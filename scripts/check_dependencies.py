import subprocess
import sys

REQUIRED_MODULES = [
    "flask", "flask_cors", "sqlalchemy", "psycopg2-binary", "python-dotenv",
    "fuzzywuzzy", "python-Levenshtein", "requests", "ged4py"
]

missing = []

for module in REQUIRED_MODULES:
    try:
        __import__(module.replace("-", "_").replace(".", "_"))
    except ImportError:
        missing.append(module)

if missing:
    print("\n⚠️  Missing modules detected:")
    for m in missing:
        print(f"   • {m}")
    print("\n📦 Installing missing modules now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

    print("\n✅ All missing packages installed.")
    print("🔁 Re-freezing requirements.txt...")
    with open("backend/requirements.txt", "w") as f:
        subprocess.call([sys.executable, "-m", "pip", "freeze"], stdout=f)
