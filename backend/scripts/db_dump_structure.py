# scripts/db_dump_structure.py
import psycopg2

conn = psycopg2.connect(
    dbname='genealogy_db',
    user='kingal',
    password='',  # update if needed
    host='localhost',
    port=5432
)

cursor = conn.cursor()

print("📋 Listing all tables...")
cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema='public'
""")
tables = cursor.fetchall()

for (table,) in tables:
    print(f"\n🧱 Table: {table}")
    cursor.execute(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = '{table}'
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]} ({row[1]})")

    print("🧪 Sample rows:")
    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
    for row in cursor.fetchall():
        print(f"  {row}")

cursor.close()
conn.close()
