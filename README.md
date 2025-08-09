## Spatial (PostGIS)

- Requires PostgreSQL with PostGIS extension.
- Ensure `DB_HOST/DB_NAME/DB_USER/DB_PASSWORD` are set in `.env`.
- Run migrations: `alembic upgrade head`.
- Geometry columns added:
  - `locations.geom`: `Geometry(POINT, 4326)` with GiST index.
  - `events.geom`: `Geometry(POINT, 4326)` with GiST index.

## Background Jobs

- Celery + Redis configured in `backend/celery_app.py`.
- `jobs` table tracks job status/progress.
- GEDCOM upload over threshold enqueues `process_gedcom_task`; response returns `job_id` and `task_id`.
- Jobs API: `/api/jobs` and `/api/jobs/<job_id>`.

## Strict Versioning

- `TreeVersion` rows represent immutable snapshots.
- Reads that require a version must include `version_id` (e.g. `/api/events?version_id=...`).
- People listing by latest remains at `/api/people/<uploaded_tree_id>`; strict variant: `/api/people/by-version/<version_id>`.

## Frontend State

- React Query enabled in `src/app/Providers.jsx`.
- Replace ad-hoc fetches with `useQuery`. Example conversion in `PeopleViewer.jsx`.
- Zustand available via `src/shared/state/uiStore.ts` for pure UI state.
# MapEm (Refactored)

Genealogy migration mapper built with React + Vite, Tailwind, and a feature‑based folder structure.

## 🚀 Quick Start
```bash
npm install            # installs deps (incl. dev tooling)
npm run dev            # start Vite dev server
```

### Environment setup
Copy `.env.example` to `.env` and fill in any secrets before running the app:

```bash
cp .env.example .env
# edit .env to add your API keys
```

## 📂 Folder Map (high‑level)
- **src/app/** – providers + router
- **src/features/** – feature slices (map, people, analytics…)
- **src/shared/** – design‑system, contexts, hooks, styles
- **src/lib/** – API clients & helper libs

## Selector Usage Example

The `SearchContext` exposes `selectedFamilyId` and `compareIds` for advanced
filter modes. Pair the context with selector components to choose people,
families or comparison groups:

```jsx
import PersonSelector from '@/features/map/components/PersonSelector';
import FamilySelector from '@/features/map/components/FamilySelector';
import GroupSelector  from '@/features/map/components/GroupSelector';
import { useSearch } from '@shared/context/SearchContext';

function MapControls() {
  const { mode } = useSearch();
  return (
    <>
      {mode === 'person' && <PersonSelector />}
      {mode === 'family' && <FamilySelector />}
      {mode === 'compare' && <GroupSelector />}
    </>
  );
}
```

## Backend Utility Scripts

Location cleanup helpers now live under `backend/scripts` and `scripts/`. See the full catalog and workflows in `docs/scripts_and_utilities.md`.

Useful commands:

```bash
python backend/scripts/retry_unresolved.py   # retry unresolved geocodes
python backend/scripts/audit_unresolved.py   # inspect unresolved entries
python scripts/fix_and_retry.py              # apply manual fixes + retry with backups
python scripts/dispatch_unresolved_locations.py  # queue Celery jobs for unresolved
```
