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
