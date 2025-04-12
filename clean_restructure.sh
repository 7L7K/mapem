#!/bin/bash
set -e

echo "👑 Starting MapEm Restructure..."

# STEP 1: CREATE NEW FOLDER STRUCTURE
mkdir -p backend/app/{routes,models,services,utils,data,logs}
mkdir -p backend/scripts/{gedcom,geo}
mkdir -p frontend/genealogy-frontend/src/{context,pages,services,styles,components/{map,upload,people,events,tree,ui}}
mkdir -p tests
mkdir -p docs

# STEP 2: MOVE BACKEND FILES
mv backend/app.py backend/app/main.py
mv backend/config.py backend/app/
mv backend/db.py backend/app/
mv backend/models.py backend/app/models/__init__.py
mv backend/gedcom_core.py backend/app/services/
mv backend/gedcom_normalizer.py backend/app/services/
mv backend/parser.py backend/app/services/
mv backend/geocode.py backend/app/services/geocode_service.py
mv backend/log_utils.py backend/app/utils/
mv backend/setup_path.py backend/app/utils/
mv backend/utils.py backend/app/utils/helpers.py
mv backend/versioning.py backend/app/utils/

mv backend/data/* backend/app/data/
mv backend/logs/* backend/app/logs/

# STEP 3: MOVE SCRIPTS
mv backend/scripts/load_gedcom.py backend/scripts/gedcom/
mv backend/scripts/{fix_missing_coords.py,show_residences_map.py,print_all_locations.py} backend/scripts/gedcom/
mv backend/scripts/{geocode_*.py,export_residences_geojson.py} backend/scripts/geo/

# STEP 4: MOVE TESTS + DOCS
mv test/* tests/
mv components_*.txt backend_code_dump.txt all_code_dump.txt docs/ 2>/dev/null || true

# STEP 5: INIT FILES
touch backend/__init__.py
touch backend/app/{routes,models,services,utils}/__init__.py

# STEP 6: CLEAN UP (OPTIONAL)
rm -rf backend/data backend/logs backend/scripts
rm -f backend/app.py backend/config.py backend/db.py backend/gedcom_*.py backend/parser.py backend/utils.py

echo "✅ File restructure complete."

# STEP 7: ADD TODOs FOR FIXING IMPORTS
echo "⚠️ You'll need to update imports manually. Examples:"
echo ""
echo "🔁 BEFORE:"
echo "from models import Individual"
echo "🛠️ AFTER:"
echo "from app.models import Individual"
echo ""
echo "Run a global find & replace to fix imports in VS Code or use 'sed'."

echo ""
echo "🚀 You're ready to modularize Flask into blueprints next."

