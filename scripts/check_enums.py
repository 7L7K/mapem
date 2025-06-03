from sqlalchemy import create_engine, text

engine = create_engine("postgresql://kingal@localhost/genealogy_db")
with engine.connect() as conn:
    query = text("SELECT unnest(enum_range(NULL::location_status_enum));")
    result = conn.execute(query)
    values = [row[0] for row in result]
    print("🧭 location_status_enum =", values)
