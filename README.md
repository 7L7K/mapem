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

Location cleanup helpers now live under `backend/scripts`. Useful commands:

```bash
python backend/scripts/retry_unresolved.py   # retry unresolved geocodes
python backend/scripts/audit_unresolved.py   # inspect unresolved entries
```
