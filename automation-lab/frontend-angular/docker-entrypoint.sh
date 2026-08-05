#!/bin/sh
set -e

# Create env-config.js for runtime configuration
cat > /usr/share/nginx/html/env-config.js <<EOF
window.__API_BASE__ = "${VITE_API_BASE_URL:-http://localhost:8000}";
EOF

exec nginx -g 'daemon off;'
