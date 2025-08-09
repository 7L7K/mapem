### Scripts and Utilities

This repository includes a rich set of scripts to bootstrap the environment, operate the backend, analyze data quality, and automate geocoding cleanup. This page catalogs the most useful commands, grouped by workflow, with examples and safety notes.

Use all commands from the repository root unless otherwise noted.

---

### Prerequisites

- **.env**: Ensure `./.env` exists with DB and API keys (see `Makefile` and `scripts/run_all.sh` for required vars: `DB_USER`, `DB_HOST`, `DB_NAME`, `DB_PORT`, `GOOGLE_MAPS_API_KEY`).
- **Python**: `python3 -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt`
- **Node**: `cd frontend && npm install`
- **PostgreSQL**: Local Postgres running and accessible by values in `.env`.

---

### Dev Orchestration

- Start backend + UI + Celery with caching and health checks:
  ```bash
  scripts/run_all.sh                  # boots Postgres (if needed), Flask, Vite, Celery
  SKIP_INSTALL=1 scripts/run_all.sh   # skip reinstalling deps
  CLEAN_NODE=1  scripts/run_all.sh    # force clean install of front-end deps
  ```
- Stop everything:
  ```bash
  scripts/stop_all.sh
  ```
- Makefile alternative:
  ```bash
  make all      # env + db + python + celery + flask + vite
  make stop     # kill processes
  make health   # verify DB connectivity
  ```

---

### Geocoding Cleanup and Analysis

Data files referenced:
- `backend/data/unresolved_locations.json`: log of unresolved place strings
- `backend/data/manual_place_fixes.json`: authoritative overrides for specific names
- `backend/data/permanent_geocodes.json`: curated cache of known-good coordinates

- Retry unresolved locations via the service (synchronous):
  ```bash
  python backend/scripts/retry_unresolved.py
  # or legacy equivalent
  python scripts/retry_unresolved.py
  ```

- Apply manual fixes and retry unresolved, with audit-friendly backup:
  ```bash
  python scripts/fix_and_retry.py \
    --manual_fixes backend/data/manual_place_fixes.json \
    --tree 3             # optional: filter to a specific tree-id
  ```

- Queue Celery jobs for all unresolved DB rows (async background processing):
  ```bash
  python scripts/dispatch_unresolved_locations.py
  # requires Celery worker: celery -A backend.celery_app.celery_app worker
  ```

- Quick stats for unresolved backlog:
  ```bash
  python scripts/unresolved_stats.py
  ```

- Geocode a single place and upsert into DB:
  ```bash
  python scripts/save_geocode_to_db.py "Compton, California, United States"
  ```

Related docs: see `docs/location_cleanup_guide.md`.

---

### GEDCOM Debugging and Pre‑flight

- Inspect a GEDCOM file before upload; counts individuals, families, place tags, and samples vague/empty places. JSON or readable output:
  ```bash
  python scripts/debug_gedcom.py /path/to/file.ged
  python scripts/debug_gedcom.py /path/to/file.ged --json
  ```

---

### Database Bootstrap and Maintenance

- Create all tables (SQLAlchemy metadata):
  ```bash
  python scripts/bootstrap_db.py
  python scripts/init_db.py          # drops and recreates all tables
  ```

- Compare model tables to live DB schema:
  ```bash
  python scripts/check_models.py
  python scripts/schema_check.py     # prints missing/extra tables vs models
  ```

- Wipe application data (dangerous — verify models referenced):
  ```bash
  python scripts/reset_db.py
  ```

- Kill idle DB connections:
  ```bash
  python scripts/db_kill_idle_clients.py
  ```

---

### Backend Introspection and Smoke Tests

- List registered Flask routes:
  ```bash
  python scripts/list_routes.py
  ```

- Quick API smoke against common endpoints (requires API running):
  ```bash
  python scripts/smoke.py 3   # optional tree id
  ```

---

### Data Backfill and Utilities

- Backfill unresolved location rows from a JSON list (insert missing rows as unresolved):
  ```bash
  python scripts/backfill_locations.py --file backend/data/unresolved_locations.json --dry_run
  ```

- Backfill missing first/last name fields on individuals (uses `split_full_name`):
  ```bash
  python scripts/backfill_individuals_name_parts.py   # DRY_RUN default True inside script
  ```

---

### Frontend Utilities

- Validate import statements and alias resolution in `frontend/src`:
  ```bash
  node scripts/check-imports.js
  ```

---

### Legacy or Path‑Specific Helpers

The following scripts contain hard‑coded paths to older layouts (e.g., `frontend/genealogy-frontend` or `$HOME/mapem`) and are preserved for reference. Review and adjust paths before using:

- `scripts/env_check.sh`, `scripts/run_all_backup.sh`, `scripts/list_files.sh`, `scripts/collect_code.sh`, `scripts/Zipit.sh`

---

### Common Workflows

- Geocode cleanup after import:
  1) `python scripts/unresolved_stats.py`
  2) `python scripts/fix_and_retry.py --manual_fixes backend/data/manual_place_fixes.json [--tree <id>]`
  3) `python scripts/dispatch_unresolved_locations.py` (async) or `python backend/scripts/retry_unresolved.py` (sync)
  4) For stubborn one-offs: `python scripts/save_geocode_to_db.py "<place>"`

- Day‑to‑day development:
  1) `scripts/run_all.sh`
  2) Develop in the frontend and backend
  3) `scripts/stop_all.sh`

---

### Safety Notes

- Prefer running retries in a staging DB first; make backups of `backend/data/*.json`.
- Some scripts support dry runs or create `.bak.<timestamp>` backups automatically — keep those defaults unless confident.
- Celery queueing requires a running worker; synchronous retries block until each geocode call returns.


