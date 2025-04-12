#!/usr/bin/env bash
set -e

bold="\033[1m"
green="\033[1;32m"
red="\033[1;31m"
reset="\033[0m"

error() { echo -e "${red}${bold}❌ $1${reset}"; }
success() { echo -e "${green}${bold}✅ $1${reset}"; }

trap 'echo -e "\n🛑 ${bold}Shutting down...${reset}"; kill $FLASK_PID $FRONT_PID 2>/dev/null || true; exit' SIGINT SIGTERM EXIT

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "\n🧼 Killing old processes…"
pkill -f "flask run" || true
pkill -f "vite" || true

echo -e "\n🔁 Starting PostgreSQL…"
pg_ctl -D /usr/local/var/postgres start || echo "⚠️ Postgres may already be running"
sleep 2

echo -e "\n🐍 Activating venv & deps…"
if [ ! -d ".venv" ]; then python3 -m venv .venv; fi
source .venv/bin/activate

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  success ".env loaded"
fi

echo -e "\n📦 Checking Python dependencies..."
MISSING_PKGS=()
for pkg in psycopg2-binary python-dotenv python-Levenshtein; do
  python -c "import $pkg" 2>/dev/null || MISSING_PKGS+=($pkg)
done

if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
  echo -e "⚠️  Missing modules detected:"
  for pkg in "${MISSING_PKGS[@]}"; do echo "   • $pkg"; done
  echo -e "\n📦 Installing missing modules now..."
  pip install "${MISSING_PKGS[@]}"
else
  success "All Python packages installed"
fi

echo -e "\n🔁 Re-freezing requirements.txt..."
pip freeze > backend/requirements.txt

echo -e "\n🧽 Cleaning logs…"
rm -f flask.log
rm -f frontend/genealogy-frontend/frontend.log

echo -e "\n🚀 Launching Flask…"
export FLASK_APP=backend/app.py
export FLASK_ENV=development
export FLASK_RUN_PORT=5050
export FLASK_RUN_HOST=127.0.0.1
flask run --debug > flask.log 2>&1 &
FLASK_PID=$!
sleep 3

if ps -p $FLASK_PID > /dev/null; then
  success "Flask running on port 5050 (PID $FLASK_PID)"
else
  error "Flask crashed during boot"
  tail -n 20 flask.log
  exit 1
fi

echo -e "\n📦 Checking frontend deps..."
cd frontend/genealogy-frontend || { error "Missing frontend folder!"; exit 1; }

# Node version check
NODE_MIN=18
NODE_VER=$(node -v | sed 's/v//;s/\..*//')
if [ "$NODE_VER" -lt "$NODE_MIN" ]; then
  error "Node.js version too old. Please use v$NODE_MIN+"
  exit 1
fi

# Install Node deps
npm install > /dev/null || { error "npm install failed"; exit 1; }

# Ensure vite is a project dependency
if ! npm ls vite --depth=0 >/dev/null 2>&1; then
  echo -e "📦 Adding Vite to devDependencies..."
  npm install --save-dev vite
  success "Vite installed locally"
fi

# Run frontend
echo -e "\n⚛️ Launching Vite React frontend…"
export PATH="./node_modules/.bin:$PATH"
echo -e "\n🔍 Debug Info:"
echo "   Node version: $(node -v)"
echo "   NPM version: $(npm -v)"
echo "   Vite path: $(which vite || echo 'vite not found')"
echo "   node_modules/.bin exists: $(ls -ld ./node_modules/.bin || echo 'not found')"
echo "   PATH: $PATH"
npm run dev > frontend.log 2>&1 &
FRONT_PID=$!
sleep 3

if ps -p $FRONT_PID > /dev/null; then
  grep -q "VITE v" frontend.log && grep -q "Local:" frontend.log && success "Vite running on port 5173 (PID $FRONT_PID)" || {
    error "Vite started but failed to bind properly"
    tail -n 20 frontend.log
    exit 1
  }
else
  error "React/Vite crashed"
  tail -n 20 frontend.log
  exit 1
fi

echo -e "\n🔎 Checking Flask API connectivity…"
curl -s --max-time 5 http://127.0.0.1:5050/api/people | grep -q 'name' && success "Flask API responding" || {
  error "Flask API did not respond properly"
  tail -n 20 flask.log
  exit 1
}

echo -e "\n🎉 ${green}${bold}All systems go!${reset}"
echo "   🔙 API → http://127.0.0.1:5050"
echo "   🔜 UI  → http://localhost:5173"
echo -e "📡 Press CTRL+C to kill both"

wait
