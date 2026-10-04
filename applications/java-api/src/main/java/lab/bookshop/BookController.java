package lab.bookshop;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.dao.DataAccessException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class BookController {

    static final String SERVICE = "java-api";
    static final String VERSION = System.getenv().getOrDefault("APP_VERSION", "dev");

    public record Book(int id, String title, String author, int year) {}

    private final JdbcTemplate jdbc;
    private final SchemaInitializer schema;

    public BookController(JdbcTemplate jdbc, SchemaInitializer schema) {
        this.jdbc = jdbc;
        this.schema = schema;
    }

    @GetMapping("/")
    public Map<String, Object> info() {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("service", SERVICE);
        m.put("version", VERSION);
        m.put("language", "Java " + Runtime.version().feature());
        m.put("runtime", "Spring Boot 4 on the JVM");
        m.put("description", "Books API of the Bookshop: GET /api/books, GET /api/books/{id}");
        return m;
    }

    /** Liveness: the process can serve requests. Deliberately does not touch the database. */
    @GetMapping("/health")
    public Map<String, Object> health() {
        return json("status", "ok", "service", SERVICE, "version", VERSION);
    }

    /** Readiness: only ready for traffic when the database answers. */
    @GetMapping("/ready")
    public ResponseEntity<Map<String, Object>> ready() {
        try {
            schema.ensure();
            jdbc.queryForObject("SELECT 1", Integer.class);
            return ResponseEntity.ok(json("status", "ready", "service", SERVICE, "version", VERSION));
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(json(
                    "status", "not ready", "service", SERVICE, "reason", SchemaInitializer.rootMessage(e)));
        }
    }

    @GetMapping("/api/books")
    public List<Book> books() {
        schema.ensure();
        return jdbc.query("SELECT id, title, author, year FROM books ORDER BY id",
                (rs, n) -> new Book(rs.getInt("id"), rs.getString("title"), rs.getString("author"), rs.getInt("year")));
    }

    @GetMapping("/api/books/{id}")
    public ResponseEntity<Object> book(@PathVariable int id) {
        schema.ensure();
        List<Book> found = jdbc.query("SELECT id, title, author, year FROM books WHERE id = ?",
                (rs, n) -> new Book(rs.getInt("id"), rs.getString("title"), rs.getString("author"), rs.getInt("year")), id);
        if (found.isEmpty()) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(json("error", "book not found", "id", id));
        }
        return ResponseEntity.ok(found.getFirst());
    }

    /** A JSON object with its keys in the given order (Map.of would shuffle them). */
    static Map<String, Object> json(Object... keysAndValues) {
        Map<String, Object> m = new LinkedHashMap<>();
        for (int i = 0; i < keysAndValues.length; i += 2) {
            m.put((String) keysAndValues[i], keysAndValues[i + 1]);
        }
        return m;
    }

    /** Database down: a clear 503 in JSON instead of a stack trace. */
    @ExceptionHandler(DataAccessException.class)
    public ResponseEntity<Map<String, Object>> databaseDown(DataAccessException e) {
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE).body(json(
                "error", "database unavailable", "reason", SchemaInitializer.rootMessage(e)));
    }
}
