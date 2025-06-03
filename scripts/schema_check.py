# scripts/schema_check.py
from backend.models import Base
from sqlalchemy import create_engine, inspect

engine = create_engine("postgresql://kingal@localhost/genealogy_db")
inspector = inspect(engine)

model_tables = set(Base.metadata.tables)
db_tables    = set(inspector.get_table_names())

print("🧠 models →", model_tables)
print("🗄  db     →", db_tables)
print("✅ in sync:", model_tables == db_tables)
print("👻 missing in DB:", model_tables - db_tables)
print("🗑 extra in DB:  ", db_tables - model_tables)
