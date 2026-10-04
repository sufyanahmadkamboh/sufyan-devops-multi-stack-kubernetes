# syntax=docker/dockerfile:1
# ---- build stage: the full Go toolchain compiles one static binary ----
FROM golang:1.27-alpine AS build
ARG APP_VERSION=1.0.0
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY *.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -trimpath -ldflags "-s -w -X main.version=${APP_VERSION}" -o /out/go-status .

# ---- final stage: only the binary (plus CA certificates and a non-root user from distroless) ----
FROM gcr.io/distroless/static-debian12:nonroot
ARG APP_VERSION=1.0.0
ENV APP_VERSION=${APP_VERSION} PORT=8080
COPY --from=build /out/go-status /go-status
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/go-status"]
