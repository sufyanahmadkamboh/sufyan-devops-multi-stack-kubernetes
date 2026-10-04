// go-status: the Bookshop's service status board (Go, standard library only).
//
// GET /api/status calls the /health endpoint of every target in TARGETS ("name=url,name=url") at the same time,
// with a 2-second timeout each, and reports which services are up.
package main

import (
	"context"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"runtime"
	"sort"
	"strings"
	"sync"
	"syscall"
	"time"
)

const service = "go-status"

// version is set at build time: -ldflags "-X main.version=1.0.0"
var version = "dev"

type target struct{ name, url string }

type result struct {
	Name       string `json:"name"`
	URL        string `json:"url"`
	Status     string `json:"status"`
	HTTPStatus int    `json:"http_status"`
	LatencyMS  int64  `json:"latency_ms"`
	Error      string `json:"error,omitempty"`
}

func parseTargets(s string) []target {
	var ts []target
	for _, part := range strings.Split(s, ",") {
		name, url, ok := strings.Cut(strings.TrimSpace(part), "=")
		if ok && name != "" && url != "" {
			ts = append(ts, target{strings.TrimSpace(name), strings.TrimSpace(url)})
		}
	}
	return ts
}

func check(ctx context.Context, client *http.Client, t target) result {
	r := result{Name: t.name, URL: t.url, Status: "down"}
	start := time.Now()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, t.url, nil)
	if err == nil {
		var resp *http.Response
		resp, err = client.Do(req)
		if err == nil {
			resp.Body.Close()
			r.HTTPStatus = resp.StatusCode
			if resp.StatusCode == http.StatusOK {
				r.Status = "up"
			}
		}
	}
	r.LatencyMS = time.Since(start).Milliseconds()
	if err != nil {
		r.Error = err.Error()
	}
	return r
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

// logged writes one log line per request to stdout.
func logged(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		rec := &statusRecorder{ResponseWriter: w, code: http.StatusOK}
		next.ServeHTTP(rec, r)
		log.Printf("%s %s %d", r.Method, r.URL.Path, rec.code)
	})
}

type statusRecorder struct {
	http.ResponseWriter
	code int
}

func (s *statusRecorder) WriteHeader(code int) { s.code = code; s.ResponseWriter.WriteHeader(code) }

func main() {
	log.SetOutput(os.Stdout)
	log.SetFlags(log.LstdFlags | log.LUTC)
	log.SetPrefix(service + " ")

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	targets := parseTargets(os.Getenv("TARGETS"))
	client := &http.Client{Timeout: 2 * time.Second}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /{$}", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{
			"service": service, "version": version, "language": "Go", "runtime": runtime.Version(),
			"description": "Service status board: checks the /health endpoint of every Bookshop service",
		})
	})
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok", "service": service, "version": version})
	})
	mux.HandleFunc("GET /api/status", func(w http.ResponseWriter, r *http.Request) {
		results := make([]result, len(targets))
		var wg sync.WaitGroup
		for i, t := range targets {
			wg.Add(1)
			go func() { defer wg.Done(); results[i] = check(r.Context(), client, t) }()
		}
		wg.Wait()
		sort.SliceStable(results, func(a, b int) bool { return results[a].Name < results[b].Name })
		up := 0
		for _, res := range results {
			if res.Status == "up" {
				up++
			}
		}
		writeJSON(w, http.StatusOK, map[string]any{"services": results, "up": up, "total": len(results)})
	})

	srv := &http.Server{Addr: "0.0.0.0:" + port, Handler: logged(mux), ReadHeaderTimeout: 5 * time.Second}
	go func() {
		log.Printf("listening on :%s, version %s, %d targets", port, version, len(targets))
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			log.Fatalf("server error: %v", err)
		}
	}()

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGTERM, syscall.SIGINT)
	<-stop
	log.Printf("shutting down")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
}
