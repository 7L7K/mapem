# check_imports.py
import os
import sys
import pkgutil
import importlib

# Add project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

modules_to_scan = ['backend']  # nothing else needed

errors = []

def scan_package(package_name):
    try:
        pkg = importlib.import_module(package_name)
    except Exception as e:
        print(f"❌ {package_name} (root package) -> {e}")
        errors.append((package_name, e))
        return

    for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, prefix=package_name + '.'):
        try:
            importlib.import_module(name)
            print(f"✅ {name}")
        except Exception as e:
            print(f"❌ {name} -> {e}")
            errors.append((name, e))

print("🔍 Scanning for broken imports...\n")
for mod in modules_to_scan:
    scan_package(mod)

print("\n🎯 Import Check Complete")

if errors:
    print(f"💥 {len(errors)} modules failed to import.")
    for name, err in errors:
        print(f" - {name}: {err}")
    sys.exit(1)
else:
    print("✅ All modules imported cleanly!")
    sys.exit(0)
