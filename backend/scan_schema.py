# scan_schema.py
from sqlalchemy import create_engine, inspect
from app.config import settings
from app.db import get_engine

# Use our central engine created from settings
engine = get_engine()
inspector = inspect(engine)

print("🧠 Scanning your PostgreSQL DB...\n")

for table_name in inspector.get_table_names():
    print(f"📄 Table: {table_name}")
    for column in inspector.get_columns(table_name):
        name = column["name"]
        dtype = str(column["type"])
        nullable = column["nullable"]
        default = column.get("default")
        print(f"   └─ {name} ({dtype}){' NULLABLE' if nullable else ''}{f' DEFAULT={default}' if default else ''}")
    print("")
