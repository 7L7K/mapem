#!/usr/bin/env zsh

set -e  # exit on error

# ─── Timing Helpers ─────────────────────────────────────────────────────
typeset -A TIMER_STARTS
typeset -A TIMER_TOTALS

start_timer() {
  TIMER_STARTS[$1]=$(date +%s.%N)
}

end_timer() {
  local label="$1"
  local start="${TIMER_STARTS[$label]}"
  local end=$(date +%s.%N)
  TIMER_TOTALS[$label]=$(echo "$end - $start" | bc)
}

print_timer_summary() {
  echo -e "\n🕒 ${bold}Step Timing Breakdown:${reset}"
  for key in "${!TIMER_TOTALS[@]}"; do
    printf "   • %-20s %5.2fs\n" "$key" "${TIMER_TOTALS[$key]}"
  done
}

# ─── Constants & Helpers ─────────────────────────────────────────────────
bold="\033[1m"; green="\033[1;32m"; red="\033[1;31m"; reset="\033[0m"
error()   { echo -e "${red}${bold}❌ $1${reset}"; }
success() { echo -e "${green}${bold}✅ $1${reset}"; }

START_TIME=$(date +%s)
FLASK_PID=""; VITE_PID=""; CELERY_PID=""

trap 'echo -e "\n🚫 ${bold}Shutting down...${reset}"; kill $FLASK_PID $VITE_PID $CELERY_PID 2>/dev/null || true; exit' SIGINT SIGTERM EXIT

# ─── Paths ───────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
export PYTHONPATH="$PROJECT_ROOT"

echo "🧠 Shell executing script: $SHELL"
echo "📁 SCRIPT_DIR: $SCRIPT_DIR"
echo "📁 PROJECT_ROOT: $PROJECT_ROOT"
echo "📄 Looking for env file at: $PROJECT_ROOT/.env"

# ─── Kill Old Processes ──────────────────────────────────────────────────
echo -e "\n🫼 Killing old processes…"
pkill -f "flask run" || true
pkill -f "vite"      || true
pkill -f "celery"    || true
if lsof -i :5050 | grep -q LISTEN; then
  echo "🛑 Port 5050 in use. Killing old Flask..."
  lsof -ti :5050 | xargs kill -9 || true
fi
if lsof -i :5173 | grep -q LISTEN; then
  echo "🛑 Port 5173 in use. Killing old Vite..."
  lsof -ti :5173 | xargs kill -9 || true
fi

# ─── Start PostgreSQL ─────────────────────────────────────────────────────
echo -e "\n🔁 Checking PostgreSQL status…"
if pg_isready -q; then
  echo "✅ Postgres already running"
else
  echo "🛠️  Starting PostgreSQL…"
  pg_ctl -D /usr/local/var/postgres start 2>/dev/null || echo "⚠️ Postgres may already be running or failed to start"
  for i in {1..5}; do
    if pg_isready -q; then
      success "Postgres is ready"
      break
    else
      echo "🕒 Waiting for Postgres..."
      sleep 1
    fi
  done
fi

# ─── Load Environment & Verify ────────────────────────────────────────────
load_env_vars() {
  echo -e "\n📄 Loading .env…"
  [ ! -f "$PROJECT_ROOT/.env" ] && { error ".env missing"; exit 1; }
  set -o allexport; source "$PROJECT_ROOT/.env"; set +o allexport

  echo -e "\n🔍 Verifying environment variables…"
  local MISSING_ENV=0
  for var in DB_USER DB_HOST DB_NAME DB_PORT GOOGLE_MAPS_API_KEY; do
    echo "   $var=${!var}"
    [[ -z "${!var}" ]] && { error "Missing $var"; MISSING_ENV=1; }
  done
  [[ "$MISSING_ENV" == 1 ]] && exit 1
}
load_env_vars

# ─── Verify DB with Caching (runs in background) ─────────────────────────
check_db() {
  local DB_CACHE_FILE="$PROJECT_ROOT/.cache/db_check_passed"
  mkdir -p "$PROJECT_ROOT/.cache"
  if [[ -f "$DB_CACHE_FILE" ]]; then
    echo "✅ Skipping DB check (cache flag exists)"
  else
    echo -e "\n🗪 Verifying DB…"
    if ! psql -d postgres -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
      createdb -O "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" && success "Database '$DB_NAME' created" || { error "DB creation failed"; exit 1; }
    else
      success "Database '$DB_NAME' exists"
    fi
    touch "$DB_CACHE_FILE"
  fi
}
check_db & DB_PID=$!

# ─── Python Setup ─────────────────────────────────────────────────────────
echo -e "\n🐍 Activating venv & checking Python deps…"
[ ! -d "$PROJECT_ROOT/.venv" ] && python3 -m venv "$PROJECT_ROOT/.venv"
source "$PROJECT_ROOT/.venv/bin/activate"

REQ_PATH="$PROJECT_ROOT/backend/requirements.txt"
HASH_FILE="$PROJECT_ROOT/.cache/req_hash.txt"

start_timer "Python setup"
if [[ "$SKIP_INSTALL" != "1" ]]; then
  echo -e "\n📦 Checking backend Python deps…"
  NEW_HASH=$(shasum "$REQ_PATH" | awk '{print $1}')
  OLD_HASH=$(cat "$HASH_FILE" 2>/dev/null || echo "")
  if [[ "$NEW_HASH" != "$OLD_HASH" ]]; then
    pip install -r "$REQ_PATH" || { error "Python install failed"; exit 1; }
    echo "$NEW_HASH" > "$HASH_FILE"
    success "Backend Python deps installed"
  else
    echo "✅ No changes to requirements.txt"
  fi
else
  echo "🚀 Skipping Python deps (SKIP_INSTALL=1)"
fi
end_timer "Python setup"

# ─── Fallback Python Modules ──────────────────────────────────────────────
echo -e "\n🔍 Checking fallback Python modules…"
MISSING=$(python - <<EOF
import importlib.util
mods = ["ged4py", "psycopg"]
print(" ".join([m for m in mods if importlib.util.find_spec(m) is None]))
EOF
)
if [[ -n "$MISSING" ]]; then
  pip install $MISSING || { error "Fallback install failed"; exit 1; }
  success "Fallback Python modules installed"
else
  success "All required Python modules present"
fi

# ─── Clean Logs ───────────────────────────────────────────────────────────
echo -e "\n🚽 Cleaning logs…"
rm -f "$PROJECT_ROOT/flask.log" "$PROJECT_ROOT/frontend/frontend.log" "$PROJECT_ROOT/celery.log"
touch "$PROJECT_ROOT/flask.log" "$PROJECT_ROOT/frontend/frontend.log" "$PROJECT_ROOT/celery.log"

# ─── Wait for DB Check to Finish ──────────────────────────────────────────
wait $DB_PID

# ─── Launch Celery Worker ─────────────────────────────────────────────────
echo -e "\n📣 Launching Celery worker…"
celery -A backend.celery_app.celery_app worker --loglevel=info > "$PROJECT_ROOT/celery.log" 2>&1 & CELERY_PID=$!
sleep 2
if ps -p $CELERY_PID >/dev/null; then
  success "Celery worker started (PID $CELERY_PID)"
else
  error "Celery worker failed to start"
  tail -n20 "$PROJECT_ROOT/celery.log"
  exit 1
fi

# ─── Launch Functions ─────────────────────────────────────────────────────

launch_flask() {
  start_timer "Flask boot"
  echo -e "\n🚀 Starting Flask with auto-reload…"
  export PYTHONPATH="$PROJECT_ROOT"
  cd "$PROJECT_ROOT"
  export FLASK_APP="backend.main:create_app"
  export FLASK_ENV="development"
  export FLASK_RUN_PORT="5050"
  export FLASK_RUN_HOST="127.0.0.1"

  if command -v watchmedo >/dev/null 2>&1; then
    watchmedo auto-restart --directory=./backend --pattern="*.py" --recursive -- python -m flask run > "$PROJECT_ROOT/flask.log" 2>&1 &
    FLASK_PID=$!
  else
    echo "⚠️  watchmedo not installed — Flask will not auto-reload"
    python backend/run_server.py > "$PROJECT_ROOT/flask.log" 2>&1 &
    FLASK_PID=$!
  fi

  # Smarter readiness loop for Flask
  echo -e "\n⏳ Waiting for Flask to become ready..."
  for i in {1..5}; do
    if curl -s --max-time 2 "http://127.0.0.1:5050/api/ping" | grep -qi '"status"[[:space:]]*:[[:space:]]*"ok"'; then
      success "Flask is up on port 5050 (PID $FLASK_PID)"
      break
    else
      echo "💡 Flask attempt $i: not ready yet..."
      sleep 1
    fi
  done

  if ! curl -s --max-time 2 "http://127.0.0.1:5050/api/ping" | grep -qi '"status"[[:space:]]*:[[:space:]]*"ok"'; then
    error "Flask failed to start"
    tail -n20 "$PROJECT_ROOT/flask.log"
    exit 1
  fi

  end_timer "Flask boot"
}

launch_vite() {
  start_timer "Vite boot"
  echo -e "\n📦 Checking frontend…"
  FRONTEND_DIR="$PROJECT_ROOT/frontend"
  cd "$FRONTEND_DIR" || { error "Frontend folder missing at $FRONTEND_DIR"; exit 1; }

  if [ ! -f package.json ]; then
    error "No package.json in $(pwd). Check FRONTEND_DIR."
    exit 1
  fi

  if [[ "$SKIP_INSTALL" != "1" ]]; then
    echo -e "\n📦 Checking Node deps hash…"
    PKG_HASH=$(shasum package-lock.json 2>/dev/null | awk '{print $1}' || echo "")
    CACHE_PATH="$PROJECT_ROOT/.cache/pkg_hash.txt"
    OLD_PKG_HASH=$(cat "$CACHE_PATH" 2>/dev/null || echo "")
    if [[ "$PKG_HASH" != "$OLD_PKG_HASH" ]]; then
      echo -e "\n📦 Installing Node deps…"
      npm install --no-fund --no-audit || {
        echo -e "⚠️ Standard install failed. Retrying with --legacy-peer-deps…"
        npm install --legacy-peer-deps --no-fund --no-audit || {
          error "npm install (with legacy-peer-deps) failed"; exit 1;
        }
      }
      echo "$PKG_HASH" > "$CACHE_PATH"
      success "Frontend Node deps installed"
    else
      echo "✅ No changes to Node deps"
    fi
  else
    echo "🚀 Skipping Node install (SKIP_INSTALL=1)"
  fi

  echo -e "\n🔍 Verifying Vite in package.json…"
  grep -q '"vite":' package.json && grep -q '"dev": "vite' package.json || {
    error "Vite config missing in package.json"; exit 1;
  }
  if ! npm list vite >/dev/null 2>&1; then
    npm install vite --save-dev --no-audit --loglevel=error || {
      error "Vite install failed"; exit 1;
    }
  else
    echo "✅ Vite already installed"
  fi
  success "Vite ready"

  echo -e "\n⚛️ Starting Vite dev server…"
  export PATH="$PWD/node_modules/.bin:$PATH"
  npm run dev > "$PROJECT_ROOT/frontend/frontend.log" 2>&1 &
  VITE_PID=$!

  # Smarter readiness loop for Vite
  echo -e "\n⏳ Waiting for Vite to become ready..."
  for i in {1..5}; do
    if grep -q "Local:" "$PROJECT_ROOT/frontend/frontend.log"; then
      success "Vite is up on port 5173 (PID $VITE_PID)"
      break
    else
      echo "💡 Vite attempt $i: not ready yet..."
      sleep 1
    fi
  done

  if ! ps -p $VITE_PID >/dev/null; then
    error "Vite failed to start"
    tail -n20 "$PROJECT_ROOT/frontend/frontend.log"
    exit 1
  fi

  end_timer "Vite boot"
}

echo -e "\n🚀 Launching Flask and Vite concurrently…"
launch_flask & FLASK_LAUNCH_PID=$!
launch_vite  & VITE_LAUNCH_PID=$!
wait $FLASK_LAUNCH_PID $VITE_LAUNCH_PID

# ─── Final API Health Check ───────────────────────────────────────────────
API_HOST="127.0.0.1"
API_PORT="5050"
API_ENDPOINT="/api/ping"
LOG_FILE="$PROJECT_ROOT/flask.log"

echo -e "\n🔎 Testing ${API_ENDPOINT}…"
for i in {1..5}; do
  RESPONSE=$(curl -s --max-time 2 "http://${API_HOST}:${API_PORT}${API_ENDPOINT}" || echo "")
  if echo "$RESPONSE" | grep -qi '"status"[[:space:]]*:[[:space:]]*"ok"'; then
    success "API responded with OK"
    break
  else
    echo "…still warming up ($i): $RESPONSE"
    sleep 1
  fi
done

if ! echo "$RESPONSE" | grep -qi '"status"[[:space:]]*:[[:space:]]*"ok"'; then
  error "API not responding"
  [ -f "$LOG_FILE" ] && tail -n20 "$LOG_FILE" || echo "🪵 No flask.log available at $LOG_FILE"
  exit 1
fi

# ─── Wrap Up ──────────────────────────────────────────────────────────────
END_TIME=$(date +%s)
TOTAL_TIME=$(echo "$END_TIME - $START_TIME" | bc)

echo -e "\n🎉 ${green}${bold}All systems go!${reset}"
echo "   🔙 API → http://${API_HOST}:${API_PORT}"
echo "   🔜 UI  → http://localhost:5173"
echo "⏱️  Total boot time: ${TOTAL_TIME}s"
print_timer_summary

echo "✅ Startup at $(date)" >> "$PROJECT_ROOT/startup.log"
echo "📡 CTRL+C to kill both"
tail -f /dev/null
