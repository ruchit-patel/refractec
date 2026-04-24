#!/bin/bash
set -e

# ---------------------------------------------------------------------------
# Frappe Docker Entrypoint
# Runs as root to fix volume permissions, then drops to frappe user.
# ---------------------------------------------------------------------------

FRAPPE_SITE="${FRAPPE_SITE:-refractec.site}"
BENCH_DIR="/home/frappe/frappe-bench"

cd "$BENCH_DIR"

# Fix ownership on volume-mounted directories (created as root by Docker)
chown -R frappe:frappe "$BENCH_DIR/sites/${FRAPPE_SITE}" 2>/dev/null || true
chown -R frappe:frappe "$BENCH_DIR/logs" 2>/dev/null || true
mkdir -p /home/frappe/logs && chown frappe:frappe /home/frappe/logs

# ---------------------------------------------------------------------------
# Everything below runs as frappe
# ---------------------------------------------------------------------------

run_as_frappe() {
  gosu frappe env PATH="$BENCH_DIR/env/bin:$PATH" "$@"
}

# ---- Write common_site_config.json from env vars ----
configure_common_site() {
  # Frappe needs currentsite.txt to resolve the site
  run_as_frappe sh -c "echo '$FRAPPE_SITE' > sites/currentsite.txt"

  run_as_frappe sh -c "cat > sites/common_site_config.json" <<EOF
{
  "db_host": "${DB_HOST:-mariadb}",
  "db_port": ${DB_PORT:-3306},
  "redis_cache": "redis://${REDIS_CACHE_HOST:-redis-cache}:6379",
  "redis_queue": "redis://${REDIS_QUEUE_HOST:-redis-queue}:6379",
  "redis_socketio": "redis://${REDIS_CACHE_HOST:-redis-cache}:6379",
  "socketio_port": 9000,
  "webserver_port": 8000,
  "serve_default_site": true,
  "default_site": "${FRAPPE_SITE}",
  "background_workers": ${BACKGROUND_WORKERS:-2}
}
EOF
}

# ---- Wait for MariaDB ----
wait_for_db() {
  echo "Waiting for MariaDB at ${DB_HOST:-mariadb}:${DB_PORT:-3306}..."
  for i in $(seq 1 30); do
    if mariadb -h "${DB_HOST:-mariadb}" -P "${DB_PORT:-3306}" \
       -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT 1" &>/dev/null; then
      echo "MariaDB is ready."
      return 0
    fi
    sleep 2
  done
  echo "ERROR: MariaDB did not become ready in time."
  exit 1
}

# ---- Create site if it doesn't exist ----
maybe_create_site() {
  if [ ! -f "sites/${FRAPPE_SITE}/site_config.json" ]; then
    echo "Creating new site: ${FRAPPE_SITE}"
    run_as_frappe bench new-site "${FRAPPE_SITE}" \
      --db-host "${DB_HOST:-mariadb}" \
      --db-root-password "${MYSQL_ROOT_PASSWORD}" \
      --admin-password "${ADMIN_PASSWORD:-admin}" \
      --mariadb-root-username root \
      --mariadb-user-host-login-scope='%' \
      --force \
      --install-app refractec
    echo "Site created successfully."
  else
    echo "Site ${FRAPPE_SITE} already exists."
    # Run migrations on startup to pick up any code changes
    run_as_frappe bench --site "${FRAPPE_SITE}" migrate --skip-failing 2>/dev/null || true
  fi
}

# ---- Commands ----
case "$1" in
  web)
    configure_common_site
    wait_for_db
    maybe_create_site
    echo "Starting Gunicorn on port 8000..."
    exec gosu frappe env \
      PATH="$BENCH_DIR/env/bin:$PATH" \
      SITES_PATH="$BENCH_DIR/sites" \
      gunicorn \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-4}" \
        --timeout 120 \
        --graceful-timeout 30 \
        --worker-tmp-dir /dev/shm \
        --preload \
        --chdir "$BENCH_DIR/sites" \
        frappe.app:application
    ;;

  socketio)
    configure_common_site
    echo "Starting Socket.IO on port 9000..."
    exec gosu frappe node apps/frappe/socketio.js
    ;;

  worker-default)
    configure_common_site
    exec gosu frappe env PATH="$BENCH_DIR/env/bin:$PATH" bench worker --queue default
    ;;

  worker-short)
    configure_common_site
    exec gosu frappe env PATH="$BENCH_DIR/env/bin:$PATH" bench worker --queue short
    ;;

  worker-long)
    configure_common_site
    exec gosu frappe env PATH="$BENCH_DIR/env/bin:$PATH" bench worker --queue long
    ;;

  scheduler)
    configure_common_site
    exec gosu frappe env PATH="$BENCH_DIR/env/bin:$PATH" bench schedule
    ;;

  migrate)
    configure_common_site
    wait_for_db
    exec gosu frappe env PATH="$BENCH_DIR/env/bin:$PATH" bench --site "${FRAPPE_SITE}" migrate
    ;;

  backup)
    configure_common_site
    exec gosu frappe env PATH="$BENCH_DIR/env/bin:$PATH" bench --site "${FRAPPE_SITE}" backup --with-files
    ;;

  console)
    configure_common_site
    exec gosu frappe env PATH="$BENCH_DIR/env/bin:$PATH" bench --site "${FRAPPE_SITE}" console
    ;;

  *)
    exec "$@"
    ;;
esac
