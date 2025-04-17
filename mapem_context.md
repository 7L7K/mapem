# 🧬 MapEm Project Context Overview

This document gives Codex (or any dev) full insight into the MapEm system — what each file does, how it connects, and where core logic lives.

### 🔗 Main Connections
- `UploadPanel.jsx` ⟷ `upload.py` ⟷ `parser.py` ⟷ `location_service.py`
- `MapView.jsx` ⟷ `movements.py` ⟷ `Event`, `Location`
- `TreeSelector.jsx` ⟷ `trees.py` ⟷ `UploadedTree`
- `PeopleViewer`, `EventPanel`, `SchemaViewer` ⟷ various API endpoints

## 🧠 Backend Summary


**(root)**
- `__init__.py` 
- `config.py` 
- `db.py` 
- `main.py` 
- `requirements.txt` 
- `run_server.py` 
- `scan_schema.py` 

**data/**
- `manual_place_fixes.json` 
- `residences.geojson` 
- `residences_map.html` 
- `test_map.html` 
- `unresolved_locations.json` 

**data/historical_places/**
- `sunflower_beats_1910.json` 

**logs/**
- `export_geojson.log` 
- `geocode.log` 

**models/**
- `__init__.py` 
- `location_models.py` 

**routes/**
- `__init__.py` 
- `debug.py` 
- `events.py` 
- `health.py` 
- `movements.py` 
- `people.py` 
- `schema.py` 
- `test.py` 
- `timeline.py` 
- `trees.py` 
- `upload.py` 

**services/**
- `__init__.py` 
- `gedcom_core.py` 
- `gedcom_normalizer.py` 
- `geocode.py` 
- `location_processor.py` 
- `location_service.py` 
- `parser.py` 

**utils/**
- `__init__.py` 
- `helpers.py` 
- `location_utils.py` 
- `log_utils.py` 
- `setup_path.py` 
- `versioning.py` 

## 🖼 Frontend Summary


**(root)**
- `index.html` 
- `package-lock.json` 
- `package.json` 
- `vite.config.js` 

**src/**
- `App.jsx` 
- `index.jsx` 

**src/components/**
- `Dashboard.jsx` 
- `DiffViewer.jsx` 
- `EventPanel.jsx` 
- `MapView.jsx` 
- `MigrationMap.jsx` 
- `PeopleViewer.jsx` 
- `SchemaViewer.jsx` 
- `SearchPanel.jsx` 
- `Timeline.jsx` 
- `TreeSelector.jsx` 
- `TreeViewer.jsx` 
- `UploadPanel.jsx` 
- `UploadStatusContext.jsx` 
- `UploadStatusOverlay.jsx` 
- `list_files_to_txt.py` 

**src/components/ui/**
- `ErrorBox.jsx` 
- `Loader.jsx` 

**src/context/**
- `TreeContext.jsx` 

**src/services/**
- `api.js` 

**src/styles/**
- `Dashboard.css` 
- `MapView.css` 
- `main.css` 

## 🛠 Root Scripts & Utilities


**data/historical_places/**
- `sunflower_beats_1910.json` 

**scripts/**
- `check_dependencies.py` 
- `collect_code.sh` 
- `env_check.sh` 
- `fix_imports.py` 
- `list_files.sh` 
- `list_routes.py` 
- `reset_db.py` 
- `run_all.sh` 
- `save_geocode_to_db.py` 
- `stop_all.sh` 
- `test_location_parser.py` 

**scripts/dev/**
- `cat_backend_files.py` 
- `check_imports.py` 
- `cmp_checker.py` 
- `dump_backend_files.sh` 

**test/**
- `conftest.py` 
- `test_mapem_sanity.py` 

**tests/data/**
- `EIchelberger Tree-3.ged` 