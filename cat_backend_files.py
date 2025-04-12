import os

# Base directory – update if your structure is different
BASE_DIR = os.path.abspath("backend/app")

# Files to collect
FILES = {
    "config.py": os.path.join(BASE_DIR, "config.py"),
    "db.py": os.path.join(BASE_DIR, "db.py"),
    "main.py": os.path.join(BASE_DIR, "main.py"),
    "helpers.py": os.path.join(BASE_DIR, "utils", "helpers.py"),
    "clear_db.py": os.path.abspath("backend/clear_db.py"),
    "scan_schema.py": os.path.abspath("backend/scan_schema.py"),
    "alembic/env.py": os.path.abspath("alembic/env.py"),
}

OUTPUT_FILE = "backend_snapshot.txt"

def collect_file_contents(name, path):
    if not os.path.exists(path):
        return f"\n\n===== 📄 {name} (NOT FOUND) =====\n⚠️  File not found: {path}\n"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    return f"\n\n===== 📄 {name} =====\n{content}"

if __name__ == "__main__":
    print(f"📦 Writing snapshot to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        for name, path in FILES.items():
            out.write(collect_file_contents(name, path))
    print("✅ Done. You can now upload or review backend_snapshot.txt.")
