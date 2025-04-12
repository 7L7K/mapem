# test_connection.py
import psycopg2
from psycopg2.extras import RealDictCursor

DB_NAME = "genealogy_db"
USER = "kingal"
HOST = "localhost"
PORT = "5432"

# Connect to DB
def get_conn():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=USER,
        host=HOST,
        port=PORT
    )

def fetch_tree_people(tree_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM tree_people WHERE tree_id = %s", (tree_id,))
            return cur.fetchall()

def fetch_tree_relationships(tree_id):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM tree_relationships WHERE tree_id = %s", (tree_id,))
            return cur.fetchall()

if __name__ == "__main__":
    print("\n--- Tree People (tree_id = 1) ---")
    for row in fetch_tree_people(1):
        print(row)

    print("\n--- Tree Relationships (tree_id = 1) ---")
    for row in fetch_tree_relationships(1):
        print(row)
