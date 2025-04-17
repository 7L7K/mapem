#$HOME/mapem/scripts/run_all.sh
#!/usr/bin/env bash

set -e  # exit on error

# ─── Timing Helpers ─────────────────────────────────────────────────────
declare -A TIMER_STARTS
declare -A TIMER_TOTALS

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
FLASK_PID=""; VITE_PID=""

# Ensure proper shutdown on signals and exit
trap 'echo -e "\n🚫 ${bold}Shutting down...${reset}"; kill $FLASK_PID $VITE_PID 2>/dev/null || true; exit' SIGINT SIGTERM EXIT

# ─── Paths ───────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ─── Kill Old Processes ──────────────────────────────────────────────────
echo -e "\n🫼 Killing old processes…"
pkill -f "flask run" || true
pkill -f "vite"      || true
if lsof -i :5050 | grep -q LISTEN; then
  echo "🛑 Port 5050 in use. Killing old Flask..."
  lsof -ti :5050 | xargs kill -9
fi

# ─── Start PostgreSQL ─────────────────────────────────────────────────────
echo -e "\n🔁 Starting PostgreSQL…"
pg_ctl -D /usr/local/var/postgres start 2>/dev/null || echo "⚠️ Postgres may already be running"
for i in {1..5}; do
  if pg_isready -q; then
    break
  else
    echo "🕒 Waiting for Postgres..."
    sleep 1
  fi
done

# ─── Python Setup ─────────────────────────────────────────────────────────
echo -e "\n🐍 Activating venv & deps…"
[ ! -d "$PROJECT_ROOT/.venv" ] && python3 -m venv "$PROJECT_ROOT/.venv"
source "$PROJECT_ROOT/.venv/bin/activate"

REQ_PATH="$PROJECT_ROOT/backend/requirements.txt"
HASH_FILE="$PROJECT_ROOT/.cache/req_hash.txt"
mkdir -p "$PROJECT_ROOT/.cache"

start_timer "Python setup"
if [[ "$SKIP_INSTALL" != "1" ]]; then
  echo -e "\n📦 Checking Python deps…"
  NEW_HASH=$(shasum "$REQ_PATH" | awk '{print $1}')
  OLD_HASH=$(cat "$HASH_FILE" 2>/dev/null || echo "")
  if [[ "$NEW_HASH" != "$OLD_HASH" ]]; then
    pip install -r "$REQ_PATH" || { error "Python install failed"; exit 1; }
    echo "$NEW_HASH" > "$HASH_FILE"
    success "Python deps installed"
  else
    echo "✅ No changes to requirements.txt"
  fi
else
  echo "🚀 Skipping Python deps (SKIP_INSTALL=1)"
fi
end_timer "Python setup"

# ─── Fallback Modules ─────────────────────────────────────────────────────
echo -e "\n🔍 Checking fallback modules…"
MISSING=()
python -c "import ged4py" 2>/dev/null || MISSING+=("ged4py")
python -c "import psycopg" 2>/dev/null || MISSING+=("psycopg")
if [ ${#MISSING[@]} -gt 0 ]; then
  pip install "${MISSING[@]}" || { error "Fallback install failed"; exit 1; }
  success "Fallback modules installed"
else
  success "All backend modules present"
fi

# ─── Env Vars ─────────────────────────────────────────────────────────────
echo -e "\n📄 Loading .env…"
[ ! -f "$PROJECT_ROOT/.env" ] && { error ".env missing"; exit 1; }
set -o allexport; source "$PROJECT_ROOT/.env"; set +o allexport

echo -e "\n🔍 Checking env vars…"
MISSING_ENV=0
for var in DB_USER DB_HOST DB_NAME DB_PORT GOOGLE_MAPS_API_KEY; do
  echo "   $var=${!var}"
  [[ -z "${!var}" ]] && { error "Missing $var"; MISSING_ENV=1; }
done
[[ "$MISSING_ENV" == 1 ]] && exit 1

# ─── Verify DB with Caching ─────────────────────────────────────────────────
DB_CACHE_FILE="$PROJECT_ROOT/.cache/db_check_passed"
if [[ -f "$DB_CACHE_FILE" ]]; then
  echo "✅ Skipping DB check (cache flag exists)"
else
  echo -e "\n🗪 Verifying DB…"
  if ! psql -d postgres -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
    createdb -O "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" || { error "DB creation failed"; exit 1; }
    success "Database '$DB_NAME' created"
  else
    success "Database '$DB_NAME' exists"
  fi
  touch "$DB_CACHE_FILE"
fi

# ─── Clean Logs ─────────────────────────────────────────────────────────────
echo -e "\n🚽 Cleaning logs…"
rm -f "$PROJECT_ROOT/flask.log" "$PROJECT_ROOT/frontend/frontend.log"
touch "$PROJECT_ROOT/flask.log"

# ─── Launch Functions (Parallel) ───────────────────────────────────────────

launch_flask() {
  start_timer "Flask boot"
  echo -e "\n🚀 Starting Flask with watchdog…"
  export PYTHONPATH="$PROJECT_ROOT"
  cd "$PROJECT_ROOT"
  export FLASK_APP="backend.main:create_app"
  export FLASK_ENV=development
  export FLASK_RUN_PORT=5050
  export FLASK_RUN_HOST="127.0.0.1"
  # If watchmedo is available, use it for auto-reload on changes in the backend
  if command -v watchmedo >/dev/null 2>&1; then
    watchmedo auto-restart --directory=./backend --pattern="*.py" --recursive -- python -m flask run > flask.log 2>&1 &
    FLASK_PID=$!
  else
    python backend/run_server.py > flask.log 2>&1 &
    FLASK_PID=$!
  fi

  echo -e "\n⏳ Waiting for Flask to boot..."
  for i in {1..5}; do
    if curl -s --max-time 2 "http://127.0.0.1:5050/api/ping" | grep -q "ok"; then
      success "Flask on 5050 (PID $FLASK_PID)"
      break
    else
      echo "💡 Flask attempt $i: not ready yet..."
      sleep 1
    fi
  done
  if ! curl -s --max-time 2 "http://127.0.0.1:5050/api/ping" | grep -q "ok"; then
    error "Flask failed to start"
    tail -n20 flask.log
    exit 1
  fi
  end_timer "Flask boot"
}

launch_vite() {
  start_timer "Vite boot"
  echo -e "\n📦 Checking frontend…"
  # Adjust FRONTEND_DIR if needed; here it’s set to the root of your frontend
  FRONTEND_DIR="$PROJECT_ROOT/frontend"
  cd "$FRONTEND_DIR" || { error "frontend folder missing at $FRONTEND_DIR"; exit 1; }
  if [ ! -f package.json ]; then
    error "No package.json in $(pwd). Check FRONTEND_DIR."
    exit 1
  fi

  [[ "$CLEAN_NODE" == "1" ]] && { rm -rf node_modules package-lock.json; echo "🧹 Cleaned node_modules"; }
  
  if [[ "$SKIP_INSTALL" != "1" ]]; then
    start_timer "Node deps"
    echo -e "\n📦 Checking Node deps hash…"
    PKG_HASH=$(shasum package-lock.json | awk '{print $1}')
    CACHE_PATH="$PROJECT_ROOT/.cache/pkg_hash.txt"
    OLD_PKG_HASH=$(cat "$CACHE_PATH" 2>/dev/null || echo "")
    if [[ "$PKG_HASH" != "$OLD_PKG_HASH" ]]; then
      echo -e "\n📦 Installing Node deps…"
      npm install --no-fund --no-audit || { error "npm install failed"; exit 1; }
      echo "$PKG_HASH" > "$CACHE_PATH"
      success "Node deps installed"
    else
      echo "✅ No changes to Node deps"
    fi
    end_timer "Node deps"
  else
    echo "🚀 Skipping Node install"
  fi

  # Only check critical frontend packages if Node deps were reinstalled
  if [[ "$PKG_HASH" != "$OLD_PKG_HASH" ]]; then
    for pkg in react-router-dom axios cytoscape cytoscape-dagre react-leaflet leaflet; do
      npm list "$pkg" >/dev/null 2>&1 || { npm install "$pkg" || { error "Failed $pkg"; exit 1; }; }
      echo "✅ $pkg OK"
    done
  else
    echo "📦 Skipping individual package checks (deps unchanged)"
  fi

  # Vite config check
  echo -e "\n🔍 Vite config check…"
  grep -q '"vite":' package.json && grep -q '"dev": "vite' package.json || { error "Vite config missing in package.json"; exit 1; }
  if ! npm list vite >/dev/null 2>&1; then
    npm install vite --save-dev --no-audit --loglevel=error || { error "Vite install failed"; exit 1; }
  else
    echo "✅ Vite already installed"
  fi
  success "Vite ready"
  
  echo -e "\n⚛️ Starting Vite…"
  export PATH="$PWD/node_modules/.bin:$PATH"
  npm run dev > frontend.log 2>&1 &
  VITE_PID=$!
  sleep 3
  if ps -p $VITE_PID >/dev/null && grep -q "Local:" frontend.log; then
    success "Vite on 5173 (PID $VITE_PID)"
  else
    error "Vite failed"
    tail -n20 frontend.log
    exit 1
  fi
  end_timer "Vite boot"
}

echo -e "\n🚀 Launching Flask and Vite concurrently…"
launch_flask & FLASK_LAUNCH_PID=$!
launch_vite & VITE_LAUNCH_PID=$!
wait $FLASK_LAUNCH_PID $VITE_LAUNCH_PID

# ─── Overall Health Check ─────────────────────────────────────────────────
API_HOST="127.0.0.1"
API_PORT="5050"
API_ENDPOINT="/api/ping"
LOG_FILE="$PROJECT_ROOT/flask.log"

echo -e "\n🔎 Testing ${API_ENDPOINT}…"
if curl -s --max-time 5 "http://${API_HOST}:${API_PORT}${API_ENDPOINT}" | grep -q "ok"; then
  success "API responding"
else
  error "API not responding"
  [ -f "$LOG_FILE" ] && tail -n20 "$LOG_FILE" || echo "🪵 No flask.log available at $LOG_FILE"
  exit 1
fi

END_TIME=$(date +%s)
TOTAL_TIME=$(echo "$END_TIME - $START_TIME" | bc)
echo -e "\n🎉 ${green}${bold}All systems go!${reset}"
echo "   🔙 API → http://${API_HOST}:${API_PORT}"
echo "   🔜 UI  → http://localhost:5173"
echo "⏱️  Total boot time: ${TOTAL_TIME}s"
print_timer_summary
echo "📡 CTRL+C to kill both"
echo "✅ Startup at $(date)" >> "$PROJECT_ROOT/startup.log"
echo "📡 CTRL+C to kill both"
tail -f /dev/null
