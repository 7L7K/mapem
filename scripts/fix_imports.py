import os

REPLACEMENTS = {
    "from app.models": "from app.models",
    "from app.services": "from app.services",
    "from app.services": "from app.services",
    "from app.services": "from app.services",
    "from app.services.geocode_service": "from app.services.geocode_service",
    "from app.utils.helpers.helpers": "from app.utils.helpers.helpers",
    "from app.utils.helpers import app.utils.helpers.log_utils": "from app.utils.helpers import app.utils.helpers.log_utils",
    "from app.utils.helpers import setup_path": "from app.utils.helpers import setup_path",
    "from app.utils.helpers import app.utils.helpers.versioning": "from app.utils.helpers import app.utils.helpers.versioning",
    "import app.models": "import app.models",
    "import app.services.parser": "import app.services.parser",
    "import app.utils.helpers.helpers": "import app.utils.helpers.helpers",
    "import app.utils.helpers.log_utils": "import app.utils.helpers.log_utils",
    "import app.services.gedcom_core": "import app.services.gedcom_core",
    "import app.services.gedcom_normalizer": "import app.services.gedcom_normalizer",
    "import app.services.geocode_service": "import app.services.geocode_service",
    "import app.utils.helpers.versioning": "import app.utils.helpers.versioning",
}

TARGET_EXT = [".py"]
BASE_DIRS = ["backend", "scripts", "."]  # "." = root files

def fix_imports():
    updated = 0
    for basedir in BASE_DIRS:
        for root, _, files in os.walk(basedir):
            for fname in files:
                if any(fname.endswith(ext) for ext in TARGET_EXT):
                    path = os.path.join(root, fname)
                    if path.startswith("./.venv") or "/.venv/" in path:
                        continue
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    original = content
                    for old, new in REPLACEMENTS.items():
                        if old in content:
                            content = content.replace(old, new)
                    if content != original:
                        updated += 1
                        print(f"✅ Fixed imports in: {path}")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(content)
    if updated == 0:
        print("🤷 No import matches found to update.")
    else:
        print(f"\n🧼 Updated {updated} files.")

if __name__ == "__main__":
    fix_imports()
