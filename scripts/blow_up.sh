OLD_SRC="frontend/"
NEW_SRC="frontend/src"
BACKUP_ZIP="src_version_before_blow_up.zip"
OUTPUT_ZIP="mapem-refactored.zip"

# ─── 0. Sanity Checks ────────────────────────────────────────────────
[[ -d $OLD_SRC ]] || { echo "❌ No $OLD_SRC folder found."; exit 1; }

# ─── 1. Backup current src/ ─────────────────────────────────────────
echo "📦 Zipping existing $OLD_SRC → $BACKUP_ZIP"
zip -r "$BACKUP_ZIP" "$OLD_SRC" >/dev/null

# ─── 2. Clean any previous refactor run ─────────────────────────────
rm -rf "$NEW_SRC" "$OUTPUT_ZIP"

# ─── 3. Scaffold new folder tree (feature‑based) ────────────────────
echo "📁 Creating new folder structure…"
mkdir -p \
  "$NEW_SRC/app" \
  "$NEW_SRC/features/map/pages" \
  "$NEW_SRC/features/map/components" \
  "$NEW_SRC/features/people/pages" \
  "$NEW_SRC/features/people/components" \
  "$NEW_SRC/features/analytics/pages" \
  "$NEW_SRC/features/dashboard/pages" \
  "$NEW_SRC/shared/components/Header" \
  "$NEW_SRC/shared/components/ui" \
  "$NEW_SRC/shared/context" \
  "$NEW_SRC/shared/hooks" \
  "$NEW_SRC/shared/styles" \
  "$NEW_SRC/lib/api"

# ─── 4. Move / Rename key files  (old → new) ────────────────────────
echo "🚚 Moving files…"
mv "$OLD_SRC/index.jsx"               "$NEW_SRC/index.jsx"
mv "$OLD_SRC/Providers.jsx"           "$NEW_SRC/app/Providers.jsx"
rm -f "$OLD_SRC/App.jsx"                               # replaced by router

mv "$OLD_SRC/pages/MapPage.jsx"       "$NEW_SRC/features/map/pages/MapPage.jsx"
mv "$OLD_SRC/components/Map/"*        "$NEW_SRC/features/map/components/"
mv "$OLD_SRC/pages/People.jsx"        "$NEW_SRC/features/people/pages/PeoplePage.jsx" || true
mv "$OLD_SRC/views/Analytics.jsx"     "$NEW_SRC/features/analytics/pages/AnalyticsPage.jsx"
mv "$OLD_SRC/styles/Dashboard.css"    "$NEW_SRC/features/dashboard/pages/DashboardPage.css" || true
mv "$OLD_SRC/components/Dashboard.jsx" "$NEW_SRC/features/dashboard/pages/DashboardPage.jsx" || true

mv "$OLD_SRC/components/Header.jsx"       "$NEW_SRC/shared/components/Header/Header.jsx"
mv "$OLD_SRC/components/SegmentedNav.jsx" "$NEW_SRC/shared/components/Header/SegmentedNav.jsx"

mv "$OLD_SRC/context/SearchContext.jsx" "$NEW_SRC/shared/context/SearchContext.jsx"
mv "$OLD_SRC/context/TreeContext.jsx"   "$NEW_SRC/shared/context/TreeContext.jsx"

mv "$OLD_SRC/utils/colors.js"          "$NEW_SRC/shared/styles/tokens.css" || true
mv "$OLD_SRC/services/api.js"          "$NEW_SRC/lib/api/client.js"

# global & other css
mv "$OLD_SRC/styles/"*.css             "$NEW_SRC/shared/styles/" 2>/dev/null || true
mv "$OLD_SRC/styles/"*.postcss         "$NEW_SRC/shared/styles/" 2>/dev/null || true

# ─── 5. Generate stub files & helpers ───────────────────────────────
cat > "$NEW_SRC/shared/hooks/useDebounce.js" <<'EOF'
export default function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = React.useState(value)
  React.useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay)
    return () => clearTimeout(id)
  }, [value, delay])
  return debounced
}
EOF

cat > "$NEW_SRC/app/router.jsx" <<'EOF'
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Header from "@shared/components/Header/Header"
import { lazy, Suspense } from "react"

const Dashboard  = lazy(() => import("@features/dashboard/pages/DashboardPage"))
const MapPage    = lazy(() => import("@features/map/pages/MapPage"))
const PeoplePage = lazy(() => import("@features/people/pages/PeoplePage"))
const Analytics  = lazy(() => import("@features/analytics/pages/AnalyticsPage"))

export default function Router() {
  return (
    <BrowserRouter>
      <Header />
      <Suspense fallback={<div>Loading…</div>}>
        <Routes>
          <Route path="/"         element={<Dashboard />} />
          <Route path="/map"      element={<MapPage   />} />
          <Route path="/people"   element={<PeoplePage/>} />
          <Route path="/analytics"element={<Analytics />}/>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}
EOF

cat > "$NEW_SRC/app/main.jsx" <<'EOF'
import { createRoot } from "react-dom/client"
import Router     from "./router"
import Providers  from "./Providers"
import "@shared/styles/globals.css"

createRoot(document.getElementById("root")).render(
  <Providers><Router /></Providers>
)
EOF

cat > "$NEW_SRC/shared/styles/globals.css" <<'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
@import "./tokens.css";
EOF

# ─── 6. Clean old folders & macOS junk ──────────────────────────────
rm -rf "$OLD_SRC" __MACOSX

# ─── 7. Tooling / Config Files ──────────────────────────────────────
echo "🛠 Writing config files…"

cat > vite.config.js <<'EOF'
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@features": "/src/features",
      "@shared"  : "/src/shared",
      "@lib"     : "/src/lib",
      "@app"     : "/src/app",
    },
  },
})
EOF

cat > tailwind.config.js <<'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: { extend: {} },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
}
EOF

cat > tsconfig.json <<'EOF'
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "moduleResolution": "node",
    "baseUrl": ".",
    "paths": {
      "@features/*": ["src/features/*"],
      "@shared/*"  : ["src/shared/*"],
      "@lib/*"     : ["src/lib/*"],
      "@app/*"     : ["src/app/*"]
    }
  },
  "include": ["src"]
}
EOF

cat > .prettierrc <<'EOF'
{
  "singleQuote": true,
  "semi": false,
  "trailingComma": "all"
}
EOF

cat > .eslintrc.js <<'EOF'
module.exports = {
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:import/errors",
    "plugin:import/warnings",
    "prettier",
  ],
  plugins: ["react", "import"],
  env: { browser: true, es2021: true },
  settings: { react: { version: "detect" } },
}
EOF

cat > .gitignore <<'EOF'
/node_modules
/dist
*.env
.DS_Store
__MACOSX
/refactored_src
EOF

cat > README.md <<'EOF'
# MapEm (Refactored)

Genealogy migration mapper built with React + Vite, Tailwind, and a feature‑based folder structure.

## 🚀 Quick Start
```bash
npm install            # installs deps (incl. dev tooling)
npm run dev            # start Vite dev server
```

## 📂 Folder Map (high‑level)
- **src/app/** – providers + router
- **src/features/** – feature slices (map, people, analytics…)
- **src/shared/** – design‑system, contexts, hooks, styles
- **src/lib/** – API clients & helper libs
EOF

# ESLint + Prettier + Husky install block (commented guidance)
cat > DEV_SETUP.txt <<'EOF'
Run these once to install dev tooling:

npm i -D prettier eslint eslint-plugin-react eslint-config-prettier eslint-plugin-import husky lint-staged \
       typescript @types/react @types/react-dom \
       @tailwindcss/forms @tailwindcss/typography @tailwindcss/aspect-ratio

# then:
npx husky install
npm pkg set scripts.prepare="husky install"
npm pkg set lint-staged."*.{js,jsx,ts,tsx}"="eslint --fix && prettier --write"
EOF

# ─── 8. Clean up & commit ───────────────────────────────────────────
echo "🧹 Cleaning up & committing…"
rm -rf "$OLD_SRC"
git add .
git commit -m "📦 Refactored src to feature-based structure with Tailwind, ESLint, Prettier, TS prep"
