#!/bin/sh
# Runtime configuration for the single-page app. The JavaScript bundle is built once (in the image); values that
# differ between environments come from environment variables when the container starts, so the same image runs in
# Docker Compose and Kubernetes.
set -eu
esc() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }
cat > /tmp/config.js <<EOF
window.APP_CONFIG = { ADMIN_URL: "$(esc "${ADMIN_URL:-}")", APP_ENV: "$(esc "${APP_ENV:-production}")" };
EOF
echo "40-config-js.sh: wrote /tmp/config.js (APP_ENV=${APP_ENV:-production})"
