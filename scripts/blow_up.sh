#!/usr/bin/env bash
###############################################################################
#  blow_up_safe_v2 – Non-destructive refactor into src2 with snapshot & logs #
###############################################################################
set -euo pipefail

# ──────────────── 1. CONFIG ────────────────────────────────────────────────
SRC_ROOT="frontend"
OLD_SRC="$SRC_ROOT/src"
NEW_SRC="$SRC_ROOT/src2"
STAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_ZIP="frontend_backup_${STAMP}.zip"
LOG="refactor_${STAMP}.log"

# Feature buckets – add more if needed
FEATURES=(map people analytics dashboard)

# ──────────────── 2. PRE-CHECK ─────────────────────────────────────────────
REQ_FILES=(
  "$OLD_SRC/index.jsx"
  "$OLD_SRC/pages/MapPage.jsx"
  "$OLD_SRC/pages/People.jsx"
  "$OLD_SRC/views/Analytics.jsx"
)

echo "🔍 Verifying source files..."
for f in "${REQ_FILES[@]}"; do
  [[ -f $f ]] || { echo "❌  Required file missing: $f" | tee -a "$LOG"; exit 1; }
done
echo "✅  Required files found." | tee -a "$LOG"

# ──────────────── 3. BACKUP ────────────────────────────────────────────────
echo "📦 Creating snapshot → $BACKUP_ZIP" | tee -a "$LOG"
zip -rq "$BACKUP_ZIP" "$OLD_SRC" -x '**/node_modules/**'
echo "   Snapshot stored." | tee -a "$LOG"

# ──────────────── 4. PREVIEW ───────────────────────────────────────────────
echo -e "\n🚧  Dry-run preview (no files touched yet):" | tee -a "$LOG"
cat <<PREVIEW | tee -a "$LOG"
  Will create: $NEW_SRC with feature-based structure
  Will copy:
    • index.jsx → src2/index.jsx
    • Providers → src2/app/Providers.jsx
    • Pages + Components → src2/features/...
    • Shared Header, UI, Context, Styles, API → src2/shared/*
PREVIEW

read -rp $'\n⚠️  Type YES to execute the refactor (anything else aborts): ' CONFIRM
[[ $CONFIRM == "YES" ]] || { echo "Aborted. No changes made."; exit 1; }

# ──────────────── 5. CREATE NEW FOLDERS ────────────────────────────────────
echo "📁 Creating folder tree in src2…" | tee -a "$LOG"
mkdir -p \
  "$NEW_SRC/app" \
  "$NEW_SRC/shared/components/Header" \
  "$NEW_SRC/shared/components/ui" \
  "$NEW_SRC/shared/context" \
  "$NEW_SRC/shared/hooks" \
  "$NEW_SRC/shared/styles" \
  "$NEW_SRC/lib/api"

for feat in "${FEATURES[@]}"; do
  mkdir -p "$NEW_SRC/features/$feat/components" "$NEW_SRC/features/$feat/pages"
done

# ──────────────── 6. MOVE FILES TO NEW TREE ────────────────────────────────
echo "🚚 Copying files to src2…" | tee -a "$LOG"
cp "$OLD_SRC/index.jsx"                       "$NEW_SRC/index.jsx"
cp "$OLD_SRC/Providers.jsx"                   "$NEW_SRC/app/Providers.jsx" || true

# Pages
cp "$OLD_SRC/pages/MapPage.jsx"              "$NEW_SRC/features/map/pages/MapPage.jsx"
cp "$OLD_SRC/pages/People.jsx"               "$NEW_SRC/features/people/pages/PeoplePage.jsx" || true
cp "$OLD_SRC/views/Analytics.jsx"            "$NEW_SRC/features/analytics/pages/AnalyticsPage.jsx" || true
cp "$OLD_SRC/components/Dashboard.jsx"       "$NEW_SRC/features/dashboard/pages/DashboardPage.jsx" || true
cp "$OLD_SRC/styles/Dashboard.css"           "$NEW_SRC/features/dashboard/pages/DashboardPage.css" || true

# Map components
cp "$OLD_SRC/components/Map/"*               "$NEW_SRC/features/map/components/" || true

# Shared UI + Header
cp "$OLD_SRC/components/Header.jsx"          "$NEW_SRC/shared/components/Header/Header.jsx" || true
cp "$OLD_SRC/components/Header/"*            "$NEW_SRC/shared/components/Header/"           || true
cp "$OLD_SRC/components/ui/"*                "$NEW_SRC/shared/components/ui/"               || true
cp "$OLD_SRC/components/SegmentedNav.jsx"    "$NEW_SRC/shared/components/Header/SegmentedNav.jsx" || true

# Context
cp "$OLD_SRC/context/"*.jsx                  "$NEW_SRC/shared/context/" || true

# Styles & API
cp "$OLD_SRC/utils/colors.js"                "$NEW_SRC/shared/styles/tokens.css" || true
cp "$OLD_SRC/services/api.js"                "$NEW_SRC/lib/api/client.js"        || true
cp "$OLD_SRC/styles/"*.css                   "$NEW_SRC/shared/styles/" 2>/dev/null || true
cp "$OLD_SRC/styles/"*.postcss               "$NEW_SRC/shared/styles/" 2>/dev/null || true

# ──────────────── 7. BOILERPLATE FILES ─────────────────────────────────────
echo "📝 Writing boilerplate files…" | tee -a "$LOG"

cat > "$NEW_SRC/app/router.jsx" <<'ROUTER'
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "@shared/components/Header/Header";
import { lazy, Suspense } from "react";

const Dashboard  = lazy(() => import("@features/dashboard/pages/DashboardPage"));
const MapPage    = lazy(() => import("@features/map/pages/MapPage"));
const PeoplePage = lazy(() => import("@features/people/pages/PeoplePage"));
const Analytics  = lazy(() => import("@features/analytics/pages/AnalyticsPage"));

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
  );
}
ROUTER

cat > "$NEW_SRC/app/main.jsx" <<'MAIN'
import { createRoot } from "react-dom/client";
import Router from "./router";
import Providers from "./Providers";
import "@shared/styles/globals.css";

createRoot(document.getElementById("root")).render(
  <Providers><Router /></Providers>
);
MAIN

cat > "$NEW_SRC/shared/styles/globals.css" <<'GLOBAL'
@tailwind base;
@tailwind components;
@tailwind utilities;
@import "./tokens.css";
GLOBAL

cat > "$NEW_SRC/shared/hooks/useDebounce.js" <<'DEBOUNCE'
import { useEffect, useState } from "react";
export default function useDebounce(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}
DEBOUNCE

# ──────────────── 8. DONE ──────────────────────────────────────────────────
echo "✅ All files moved into: $NEW_SRC"
echo "🛡 Snapshot → $BACKUP_ZIP"
echo "🧠 Review everything inside src2/. Rename to src when ready."
