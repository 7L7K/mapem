import psycopg
import os

dsn = os.getenv("DATABASE_URL") or "postgresql://postgres@localhost:5432/genealogy_db"

with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT pid FROM pg_stat_activity
            WHERE state = 'idle' AND pid <> pg_backend_pid();
        """)
        pids = cur.fetchall()

        print(f"Found {len(pids)} idle connections to terminate.")
        for (pid,) in pids:
            print(f"🔪 Killing PID {pid}")
            cur.execute(f"SELECT pg_terminate_backend({pid});")

    conn.commit()
