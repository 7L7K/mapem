#!/usr/bin/env bash
###############################################################################
#  blow_up_safe.sh – King‑proof frontend refactor with confirmation & logging #
###############################################################################
set -euo pipefail

# ──────────────── 1. CONFIG ────────────────────────────────────────────────
SRC_ROOT="frontend"          
OLD_SRC="$SRC_ROOT/src"          
NEW_SRC="$SRC_ROOT/src"      
STAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_ZIP="frontend_backup_${STAMP}.zip"
LOG="refactor_${STAMP}.log"
REQ_FILES=(
  "$OLD_SRC/index.jsx"
  "$OLD_SRC/pages/MapPage.jsx"
  "$OLD_SRC/pages/People.jsx"
  "$OLD_SRC/views/Analytics.jsx"
)

FEATURES=(map people analytics dashboard)

# ──────────────── 2. PRE-FLIGHT CHECKS ─────────────────────────────────────
echo "🔍 Verifying source files..."
for f in "${REQ_FILES[@]}"; do
  [[ -f $f ]] || {
    echo "❌  Required file missing: $f" | tee -a "$LOG"
    echo "💡 Try restoring a backup: unzip frontend_backup_*.zip -d frontend/"
    exit 1
  }
done
echo "✅  Required files found." | tee -a "$LOG"

# ──────────────── 3. BACKUP BEFORE NUKE ────────────────────────────────────
echo "📦 Creating snapshot → $BACKUP_ZIP" | tee -a "$LOG"
zip -rq "$BACKUP_ZIP" "$SRC_ROOT" -x '**/node_modules/**'
echo "   Snapshot stored." | tee -a "$LOG"

# ──────────────── 4. DRY-RUN PREVIEW ───────────────────────────────────────
echo -e "\n🚧  Dry-run preview:" | tee -a "$LOG"
cat <<PREVIEW | tee -a "$LOG"
  Will delete: $NEW_SRC
  Will move files into: $NEW_SRC with feature‑based structure
  Will commit with: 💥 Safe refactor
PREVIEW

read -rp $'\n⚠️  Type YES to execute the refactor (anything else aborts): ' CONFIRM
[[ $CONFIRM == "YES" ]] || { echo "Aborted. No changes made."; exit 1; }

# ──────────────── 5. NUKE OLD STRUCTURE ────────────────────────────────────
echo "💣 Deleting old $NEW_SRC (safe – we backed up)..." | tee -a "$LOG"
rm -rf "$NEW_SRC"

echo "📁 Creating new folder tree…" | tee -a "$LOG"
mkdir -p "$NEW_SRC/app" "$NEW_SRC/lib/api" "$NEW_SRC/shared/hooks"
for feat in "${FEATURES[@]}"; do
  mkdir -p "$NEW_SRC/features/$feat/components" "$NEW_SRC/features/$feat/pages"
done
mkdir -p "$NEW_SRC/shared/components/Header" "$NEW_SRC/shared/components/ui" \
         "$NEW_SRC/shared/context" "$NEW_SRC/shared/styles"

# ──────────────── 6. MOVE FILES ────────────────────────────────────────────
echo "🚚 Moving files…" | tee -a "$LOG"
mv "$OLD_SRC/index.jsx" "$NEW_SRC/index.jsx" || true
mv "$OLD_SRC/Providers.jsx" "$NEW_SRC/app/Providers.jsx" || true
mv "$OLD_SRC/pages/MapPage.jsx" "$NEW_SRC/features/map/pages/MapPage.jsx" || true
mv "$OLD_SRC/pages/People.jsx" "$NEW_SRC/features/people/pages/PeoplePage.jsx" || true
mv "$OLD_SRC/views/Analytics.jsx" "$NEW_SRC/features/analytics/pages/AnalyticsPage.jsx" || true
mv "$OLD_SRC/components/Dashboard.jsx" "$NEW_SRC/features/dashboard/pages/DashboardPage.jsx" || true
mv "$OLD_SRC/styles/Dashboard.css" "$NEW_SRC/features/dashboard/pages/DashboardPage.css" || true
mv "$OLD_SRC/components/Map/"* "$NEW_SRC/features/map/components/" || true
mv "$OLD_SRC/components/Header.jsx" "$NEW_SRC/shared/components/Header/Header.jsx" || true
mv "$OLD_SRC/components/Header/"* "$NEW_SRC/shared/components/Header/" || true
mv "$OLD_SRC/components/ui/"* "$NEW_SRC/shared/components/ui/" || true
mv "$OLD_SRC/components/SegmentedNav.jsx" "$NEW_SRC/shared/components/Header/SegmentedNav.jsx" || true
mv "$OLD_SRC/context/"* "$NEW_SRC/shared/context/" || true
mv "$OLD_SRC/utils/colors.js" "$NEW_SRC/shared/styles/tokens.css" || true
mv "$OLD_SRC/services/api.js" "$NEW_SRC/lib/api/client.js" || true
mv "$OLD_SRC/styles/"*.css "$NEW_SRC/shared/styles/" 2>/dev/null || true
mv "$OLD_SRC/styles/"*.postcss "$NEW_SRC/shared/styles/" 2>/dev/null || true

# ──────────────── 7. CORE FILES ────────────────────────────────────────────
echo "📝 Writing boilerplate files…" | tee -a "$LOG"
cat > "$NEW_SRC/app/router.jsx" <<'EOF'
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "@shared/components/Header/Header";
import { lazy, Suspense } from "react";

const Dashboard = lazy(() => import("@features/dashboard/pages/DashboardPage"));
const MapPage   = lazy(() => import("@features/map/pages/MapPage"));
const People    = lazy(() => import("@features/people/pages/PeoplePage"));
const Analytics = lazy(() => import("@features/analytics/pages/AnalyticsPage"));

export default function Router() {
  return (
    <BrowserRouter>
      <Header />
      <Suspense fallback={<div>Loading…</div>}>
        <Routes>
          <Route path="/"         element={<Dashboard />} />
          <Route path="/map"      element={<MapPage />} />
          <Route path="/people"   element={<People />} />
          <Route path="/analytics"element={<Analytics />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
EOF

cat > "$NEW_SRC/app/main.jsx" <<'EOF'
import { createRoot } from "react-dom/client";
import Router from "./router";
import Providers from "./Providers";
import "@shared/styles/globals.css";

createRoot(document.getElementById("root")).render(
  <Providers><Router /></Providers>
);
EOF

cat > "$NEW_SRC/shared/hooks/useDebounce.js" <<'EOF'
import { useEffect, useState } from "react";
export default function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}
EOF

cat > "$NEW_SRC/shared/styles/globals.css" <<'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
@import "./tokens.css";
EOF

# ──────────────── 8. TOOLING FILES ─────────────────────────────────────────
cat > vite.config.js <<'EOF'
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@features": "/src/features",
      "@shared": "/src/shared",
      "@lib": "/src/lib",
      "@app": "/src/app"
    },
  },
});
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
};
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
      "@shared/*": ["src/shared/*"],
      "@lib/*": ["src/lib/*"],
      "@app/*": ["src/app/*"]
    }
  },
  "include": ["src"]
}
EOF

cat > .gitignore <<'EOF'
/node_modules
/dist
*.env
.DS_Store
__MACOSX
EOF

cat > .prettierrc <<'EOF'
{ "singleQuote": true, "semi": false, "trailingComma": "all" }
EOF

cat > .eslintrc.js <<'EOF'
module.exports = {
  extends: ["eslint:recommended", "plugin:react/recommended", "plugin:import/errors", "plugin:import/warnings", "prettier"],
  plugins: ["react", "import"],
  env: { browser: true, es2021: true },
  settings: { react: { version: "detect" } },
};
EOF

# ──────────────── 9. COMMIT + DONE ─────────────────────────────────────────
echo "🧹 Final git commit…" | tee -a "$LOG"
git add . && git commit -m "💥 Safe refactor: feature-based layout with config setup" | tee -a "$LOG"
echo "✅ Refactor complete! Snapshot: $BACKUP_ZIP | Log: $LOG"
