#$HOME/mapem/scripts/stop_all.sh
#!/usr/bin/env bash
echo "🛑 Killing Flask + Vite + watchmedo..."
pkill -f flask || true
pkill -f watchmedo || true
pkill -f vite || true
lsof -ti :5050 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true
echo "✅ Everything shut down."
