#!/bin/sh
# Entry point of the laravel-fpm image. Fail fast, with a clear message, when required configuration is missing:
# a container that exits at once with the reason in its log is far easier to debug than one that starts and then
# answers every request with "500 Server Error".
set -e

missing=""
[ -n "${APP_KEY:-}" ] || missing="$missing APP_KEY"
[ -n "${DB_PASSWORD:-}" ] || missing="$missing DB_PASSWORD"
if [ -n "$missing" ]; then
    echo "laravel-admin: missing required environment variable(s):$missing" >&2
    echo "laravel-admin: APP_KEY can be generated with: php artisan key:generate --show" >&2
    exit 1
fi

echo "laravel-admin ${APP_VERSION:-dev}: starting: $*" >&2
exec "$@"
