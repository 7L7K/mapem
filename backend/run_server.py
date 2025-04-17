#!/usr/bin/env python3
import os
import sys

# ─── Make sure project root is on the path ────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.main import create_app

app = create_app()

if __name__ == "__main__":
    # Disable the reloader so the process PID remains stable
    app.run(host="127.0.0.1", port=5050, debug=True, use_reloader=False)
