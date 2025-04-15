# 🚀 MapEm Fullstack Launcher v2.1
# King-approved, auto-installs, smart waits, no warnings

#!/usr/bin/env bash
set -e  # exit on error

# ─── Constants & Helpers ────────────────────────────────────────────────
bold="\033[1m"; green="\033[1;32m"; red="\033[1;31m"; reset="\033[0m"
error()   { echo -e "${red}${bold}❌ $1${reset}"; }
success() { echo -e "${green}${bold}✅ $1${reset}"; }

START_TIME=$(date +%s)
FLASK_PID=""; FRONT_PID=""

# Ensure proper shutdown on signals and exit
trap 'echo -e "\n🚫 ${bold}Shutting down...${reset}"; kill $FLASK_PID $FRONT_PID 2>/dev/null || true; exit' SIGINT SIGTERM EXIT

# ─── Paths ────────────────────────────────────────────────────────────────
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

# ─── PostgreSQL ─────────────────────────────────────────────────────────
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

# ─── Python Setup ────────────────────────────────────────────────────────
echo -e "\n🐍 Activating venv & deps…"
[ ! -d "$PROJECT_ROOT/.venv" ] && python3 -m venv "$PROJECT_ROOT/.venv"
source "$PROJECT_ROOT/.venv/bin/activate"

REQ_PATH="$PROJECT_ROOT/backend/requirements.txt"
HASH_FILE="$PROJECT_ROOT/.cache/req_hash.txt"
mkdir -p "$PROJECT_ROOT/.cache"

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

# ─── Fallback Modules ────────────────────────────────────────────────────
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

# ─── Env Vars ───────────────────────────────────────────────────────────
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

# ─── DB Check ───────────────────────────────────────────────────────────
echo -e "\n🗪 Verifying DB…"
if ! psql -d postgres -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -tAc \
     "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1; then
  createdb -O "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" || { error "DB creation failed"; exit 1; }
  success "Database '$DB_NAME' created"
else
  success "Database '$DB_NAME' exists"
fi

# ─── Launch Flask ────────────────────────────────────────────────────────
echo -e "\n🚽 Cleaning logs…"
rm -f "$PROJECT_ROOT/flask.log" "$PROJECT_ROOT/frontend/frontend.log"
touch "$PROJECT_ROOT/flask.log"

echo -e "\n🚀 Starting Flask…"
export PYTHONPATH="$PROJECT_ROOT"
cd "$PROJECT_ROOT"
export FLASK_APP="backend.main:create_app"
export FLASK_ENV=development
export FLASK_RUN_PORT=5050
export FLASK_RUN_HOST="127.0.0.1"

python backend/run_server.py > flask.log 2>&1 &
FLASK_PID=$!

echo -e "\n⏳ Waiting for Flask to boot..."
for i in {1..5}; do
  if curl -s --max-time 2 "http://127.0.0.1:5050/api/ping" | grep -q "ok"; then
    success "Flask on 5050 (PID $FLASK_PID)"
    break
  else
    echo "💡 Attempt $i: Flask not ready yet..."
    sleep 1
  fi
done
if ! curl -s --max-time 2 "http://127.0.0.1:5050/api/ping" | grep -q "ok"; then
  error "Flask failed to start"
  tail -n20 flask.log
  exit 1
fi

# ─── Frontend ───────────────────────────────────────────────────────────
echo -e "\n📦 Checking frontend…"
# Point to the real React app directory:
FRONTEND_DIR="$PROJECT_ROOT/frontend/"
cd "$FRONTEND_DIR" || { error "frontend folder missing at $FRONTEND_DIR"; exit 1; }

# Sanity check
if [ ! -f package.json ]; then
  error "No package.json in $(pwd). Check FRONTEND_DIR."
  exit 1
fi

[[ "$CLEAN_NODE" == "1" ]] && { rm -rf node_modules package-lock.json; echo "🧹 Cleaned node_modules"; }

if [[ "$SKIP_INSTALL" != "1" ]]; then
  echo -e "\n📦 Checking Node deps hash…"
  PKG_HASH=$(shasum package-lock.json | awk '{print $1}')
  CACHE_PATH="$PROJECT_ROOT/.cache/pkg_hash.txt"
  OLD_PKG_HASH=$(cat "$CACHE_PATH" 2>/dev/null || echo "")
  if [[ "$PKG_HASH" != "$OLD_PKG_HASH" ]]; then
    echo -e "\n📦 Installing Node deps…"
    npm install || { error "npm install failed"; exit 1; }
    echo "$PKG_HASH" > "$CACHE_PATH"
    success "Node deps installed"
  else
    echo "✅ No changes to Node deps"
  fi
else
  echo "🚀 Skipping Node install"
fi

# Critical frontend packages check
for pkg in react-router-dom axios cytoscape cytoscape-dagre react-leaflet leaflet; do
  npm list "$pkg" >/dev/null 2>&1 || { npm install "$pkg" || { error "Failed $pkg"; exit 1; }; }
  echo "✅ $pkg OK"
done

# Vite config check
echo -e "\n🔍 Vite config check…"
grep -q '"vite":' package.json && grep -q '"dev": "vite' package.json || { error "Vite config missing in package.json"; exit 1; }
npm install vite --save-dev --no-audit --loglevel=error || { error "Vite install failed"; exit 1; }
success "Vite ready"

echo -e "\n⚛️ Starting Vite…"
export PATH="$PWD/node_modules/.bin:$PATH"
npm run dev > frontend.log 2>&1 &
FRONT_PID=$!
sleep 3
if ps -p $FRONT_PID >/dev/null && grep -q "Local:" frontend.log; then
  success "Vite on 5173 (PID $FRONT_PID)"
else
  error "Vite failed"
  tail -n20 frontend.log
  exit 1
fi

# ─── Health Check ────────────────────────────────────────────────────────
API_HOST="127.0.0.1"
API_PORT="5050"
API_ENDPOINT="/api/ping"
LOG_FILE="$PROJECT_ROOT/flask.log"

echo -e "\n🔎 Testing ${API_ENDPOINT}…"
if curl -s --max-time 5 "http://${API_HOST}:${API_PORT}${API_ENDPOINT}" | grep -q "ok"; then
  success "API responding"
else
  error "API not responding"
  if [ -f "$LOG_FILE" ]; then
    tail -n20 "$LOG_FILE"
  else
    echo "🪵 No flask.log available at $LOG_FILE"
  fi
  exit 1
fi

# ─── Done ───────────────────────────────────────────────────────────────
END_TIME=$(date +%s)
echo -e "\n🎉 ${green}${bold}All systems go!${reset}"
echo "   🔙 API → http://${API_HOST}:${API_PORT}"
echo "   🔜 UI  → http://localhost:5173"
echo "⏱️  Boot time: $((END_TIME - START_TIME))s"
echo "📡 CTRL+C to kill both"

echo "✅ Startup at $(date)" >> "$PROJECT_ROOT/startup.log"
wait
