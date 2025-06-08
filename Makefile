.PHONY: all env db python celery flask vite stop health

all: env db python celery flask vite

env:
	@echo "📄 Loading .env"
	@set -o allexport; test -f .env && source .env; set +o allexport

db:
	@echo "🗪 Checking/creating DB $(DB_NAME)"
	@PGPASSWORD="$(DB_PASSWORD)" \
	  psql -w -U "$(DB_USER)" -h "$(DB_HOST)" -p "$(DB_PORT)" \
	  -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$(DB_NAME)'" \
	  | grep -q 1 || \
	    PGPASSWORD="$(DB_PASSWORD)" \
	    createdb -U "$(DB_USER)" -h "$(DB_HOST)" -p "$(DB_PORT)" "$(DB_NAME)"

python:
	@echo "🐍 Setting up Python venv"
	@test -d .venv || python3 -m venv .venv
	@. .venv/bin/activate && pip install -r backend/requirements.txt

celery:
	@echo "📣 Launching Celery"
	@. .venv/bin/activate && \
	celery -A backend.celery_app.celery_app worker --concurrency=4 --loglevel=info &> celery.log &

flask:
	@echo "🚀 Launching Flask"
	@. .venv/bin/activate && \
	FLASK_APP=backend.main:create_app \
	FLASK_ENV=development \
	flask run --host=127.0.0.1 --port=5050 &> flask.log &

vite:
	@echo "⚛️ Launching Vite"
	cd frontend && npm ci && npm run dev &> vite.log &

stop:
	@echo "🛑 Killing Flask, Celery, and Vite processes"
	@pkill -f "flask run" || echo "❌ Flask not running"
	@pkill -f "celery"    || echo "❌ Celery not running"
	@pkill -f "vite"      || echo "❌ Vite not running"
	@echo "✅ Done."
	@echo "Running ports check:"
	@lsof -i :5050 -sTCP:LISTEN || echo " • Port 5050 clear"
	@lsof -i :5173 -sTCP:LISTEN || echo " • Port 5173 clear"

health:
	@echo "🔍 Checking DB connection"
	@PGPASSWORD="$(DB_PASSWORD)" \
	psql -U "$(DB_USER)" -h "$(DB_HOST)" -p "$(DB_PORT)" -d "$(DB_NAME)" -c '\conninfo'
