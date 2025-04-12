#!/bin/bash

echo -e "\n👑 King's Dev Checker & Launcher v2.0 👑"
echo "----------------------------------------"

# 💀 Kill leftover Flask and Vite processes safely
echo -e "\n🧼 Killing previous processes..."
for PORT in 5050 5173 5174 5175 5176 5177 5178 5179 5180
do
    PID=$(lsof -t -i:$PORT)
    if [ ! -z "$PID" ]; then
        echo "⚠️  Killing process on port $PORT (PID $PID)"
        kill -9 $PID || { echo "❌ Failed to kill process on port $PORT"; exit 1; }
    fi
done

# 🧠 Frontend Check
echo -e "\n🔍 Checking Frontend..."

cd frontend/genealogy-frontend || { echo "❌ Frontend folder not found!"; exit 1; }

if ! command -v node &>/dev/null; then
    echo "❌ Node.js not installed!"
    exit 1
fi

if ! command -v npm &>/dev/null; then
    echo "❌ npm not installed!"
    exit 1
fi

[ -f package.json ] && echo "✅ package.json exists." || { echo "❌ Missing package.json"; exit 1; }
[ -d node_modules ] || { echo "📦 Installing frontend packages..."; npm install; }

cd ../../

# 🧠 Backend Check
echo -e "\n🔍 Checking Backend..."

cd backend || { echo "❌ Backend folder not found!"; exit 1; }

if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 not found!"
    exit 1
fi

if [ ! -d ../.venv ]; then
    echo "❌ Python virtual environment missing!"
    exit 1
fi

echo "✅ Activating venv..."
source ../.venv/bin/activate

pip install -r requirements.txt > /dev/null

cd ..

# 🧠 DB Check and Clear
echo -e "\n🔍 Checking PostgreSQL..."
if command -v pg_isready &>/dev/null; then
    pg_isready -d genealogy_db
else
    echo "⚠️ pg_isready not found."
fi

echo -e "\n🧹 Clearing the database..."
# Clear the database by running clear_db.py script
python3 backend/clear_db.py

# 🌐 Network Checks — optional
echo -e "\n🌐 Network Pre-Checks (skipped for now)..."

# 🚀 Start Backend + Frontend
echo -e "\n🚀 Launching Flask backend..."
cd backend
source ../.venv/bin/activate
python app.py &

echo -e "\n⚛️  Launching React frontend..."
cd ../frontend/genealogy-frontend
npm run dev &

echo -e "\n✅ All systems launched."
echo "Flask → http://127.0.0.1:5050"
echo "React → http://localhost:5173 (if available)"
open http://localhost:5173
open http://127.0.0.1:5050
