#!/usr/bin/env bash
set -e

bold="\033[1m"
green="\033[1;32m"
red="\033[1;31m"
reset="\033[0m"

error()   { echo -e "${red}${bold}❌ $1${reset}"; }
success() { echo -e "${green}${bold}✅ $1${reset}"; }

trap 'echo -e "\n🚫 ${bold}Shutting down...${reset}"; kill $FLASK_PID $FRONT_PID 2>/dev/null || true; exit' SIGINT SIGTERM EXIT

# ─── Setup paths ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ─── Kill old processes ──────────────────────────────────────────────────────
echo -e "\n🫼 Killing old processes…"
pkill -f "flask run" || true
pkill -f "vite"      || true

# ─── Start Postgres ──────────────────────────────────────────────────────────
echo -e "\n🔁 Starting PostgreSQL…"
pg_ctl -D /usr/local/var/postgres start || echo "⚠️ Postgres may already be running"
sleep 2

# ─── Python / Backend ─────────────────────────────────────────────────────────
echo -e "\n🐍 Activating venv & deps…"
if [ ! -d "$PROJECT_ROOT/.venv" ]; then
  python3 -m venv "$PROJECT_ROOT/.venv"
fi
source "$PROJECT_ROOT/.venv/bin/activate"

echo -e "\n📆 Installing Python dependencies…"
REQ_PATH="$PROJECT_ROOT/backend/requirements.txt"
if [ -f "$REQ_PATH" ]; then
  pip install -r "$REQ_PATH" || { error "Failed to install Python packages"; exit 1; }
  success "Backend dependencies installed"
else
  error "Cannot find $REQ_PATH"; exit 1
fi

echo -e "\n🔍 Checking for known missing modules…"
MISSING=()
python - <<'PYCODE' 2>/dev/null || MISSING+=("ged4py")
import ged4py
PYCODE
python - <<'PYCODE' 2>/dev/null || MISSING+=("psycopg")
import psycopg
PYCODE
if [ ${#MISSING[@]} -gt 0 ]; then
  echo -e "📦 Installing fallback modules: ${MISSING[*]}"
  pip install "${MISSING[@]}" || { error "Failed fallback installs"; exit 1; }
  success "Fallback packages installed"
else
  success "All backend modules present"
fi

echo -e "\n🔁 Re‑freezing requirements.txt…"
pip freeze > "$REQ_PATH" || echo "⚠️ Could not freeze requirements"

echo -e "\n📄 Loading environment variables from .env..."
if [ ! -f "$PROJECT_ROOT/.env" ]; then
  error ".env file not found at $PROJECT_ROOT"; exit 1
fi
set -o allexport
source "$PROJECT_ROOT/.env"
set +o allexport

echo -e "\n🔍 Required env vars:"
for var in DB_USER DB_HOST DB_NAME DB_PORT GOOGLE_MAPS_API_KEY; do
  echo "   $var = ${!var}"
done

echo -e "\n🗪 Verifying Postgres connection & database..."
if ! psql -d postgres -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -tAc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1; then
  echo "📈 Creating database '$DB_NAME'..."
  createdb -O "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" || { error "Database creation failed"; exit 1; }
  success "Database '$DB_NAME' created"
else
  success "Database '$DB_NAME' exists"
fi

echo -e "\n🚽 Cleaning logs…"
rm -f "$PROJECT_ROOT/flask.log" "$PROJECT_ROOT/frontend/frontend.log"

echo -e "\n🚀 Launching Flask…"
export PYTHONPATH="$PROJECT_ROOT"
cd "$PROJECT_ROOT"
export FLASK_APP="backend.main:create_app"
export FLASK_ENV=development
export FLASK_RUN_PORT=5050
export FLASK_RUN_HOST=127.0.0.1

flask run --debug > flask.log 2>&1 &
FLASK_PID=$!
sleep 3
if ps -p $FLASK_PID > /dev/null; then
  success "Flask running on 5050 (PID $FLASK_PID)"
else
  error "Flask boot failed"; tail -n20 flask.log; exit 1
fi

# ─── Frontend / Vite ──────────────────────────────────────────────────────────
echo -e "\n📦 Checking frontend…"
cd "$PROJECT_ROOT/frontend" || { error "Missing frontend folder"; exit 1; }

# ensure devDependencies install even if NODE_ENV=production
unset NODE_ENV

# clean out old installs & lockfile
echo -e "\n🧹 Cleaning frontend node_modules & lockfile…"
rm -rf node_modules package-lock.json

echo -e "\n📦 Installing Node dependencies (incl. dev)…"
npm install --omit=none || { error "npm install failed"; exit 1; }

echo -e "\n🔍 Checking Vite configuration in package.json..."
if ! grep -q '"vite":' package.json && ! grep -q '"dev": "vite' package.json; then
  error "Vite not declared in dependencies or scripts."; exit 1
else
  success "Vite is configured in package.json"
fi

echo -e "\n🧹 Vite binary debug:"
ls -la node_modules/.bin/vite || echo "⚠️ vite binary missing"

# explicit install just in case
echo -e "\n📦 Ensuring Vite is installed explicitly..."
npm install vite --save-dev --no-audit --loglevel=error || { error "Vite install failed"; exit 1; }
success "Vite installed"

# key: add local bin to PATH
export PATH="$PWD/node_modules/.bin:$PATH"

echo -e "\n⚛️ Launching Vite frontend…"
echo -e "   Node: $(node -v)  NPM: $(npm -v)  Vite: $(which vite)"
npm run dev > frontend.log 2>&1 &
FRONT_PID=$!
sleep 3
if ps -p $FRONT_PID > /dev/null && grep -q "Local:" frontend.log; then
  success "Vite running on 5173 (PID $FRONT_PID)"
  
  # auto‑open browser on macOS
  if command -v open >/dev/null; then
    open http://localhost:5173
  fi
else
  error "Vite crash"; tail -n20 frontend.log; exit 1
fi

# ─── Final API check ──────────────────────────────────────────────────────────
echo -e "\n🔎 Testing Flask API connectivity…"
if curl -s --max-time 5 http://127.0.0.1:5050/api/people | grep -q name; then
  success "API responding"
else
  error "API not responding"; tail -n20 flask.log; exit 1
fi

echo -e "\n🎉 ${green}${bold}All systems go!${reset}"
echo "   🔙 API → http://127.0.0.1:5050"
echo "   🔜 UI  → http://localhost:5173"
echo -e "📡 Press CTRL+C to kill both"

echo "✅ Startup successful at $(date)" >> "$PROJECT_ROOT/startup.log"
wait
