"""Check users in the database."""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
print(f"Connecting to database...")

# Try direct psycopg2 connection
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    # Parse connection URL
    url = DATABASE_URL.replace("postgres://", "postgresql://")
    if "sslmode=" not in url:
        url += "?sslmode=require"

    conn = psycopg2.connect(url)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Check if users table exists and list users
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name LIKE '%user%'
    """)
    tables = cur.fetchall()
    print(f"User-related tables: {[t['table_name'] for t in tables]}")

    # Check users table structure first
    cur.execute("""
        SELECT column_name, data_type FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'users'
        ORDER BY ordinal_position
    """)
    columns = cur.fetchall()
    print(f"\n=== 'users' table columns ===")
    for col in columns:
        print(f"  {col['column_name']}: {col['data_type']}")

    # Try common table names
    for table_name in ['users', 'user', 'hs_user', 'app_user']:
        try:
            # Get actual columns for this table
            cur.execute(f"""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = '{table_name}'
            """)
            cols = [c['column_name'] for c in cur.fetchall()]
            if cols:
                cur.execute(f"SELECT {', '.join(cols)} FROM {table_name} LIMIT 10")
                rows = cur.fetchall()
                if rows:
                    print(f"\n=== {len(rows)} users from '{table_name}' ===")
                    for r in rows:
                        print(f"  {dict(r)}")
                else:
                    print(f"\nTable '{table_name}' exists but is empty")
        except Exception as e:
            print(f"Error querying '{table_name}': {e}")

    cur.close()
    conn.close()

except ImportError:
    print("psycopg2 not installed. Install with: pip install psycopg2-binary")
except Exception as e:
    print(f"Database connection error: {e}")
