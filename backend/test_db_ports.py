import psycopg2
import sys

def test_conn(host, port, user):
    print(f"Testing connection to {host}:{port} with user {user}...")
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database="postgres",
            user=user,
            password="Poojitha12@",
            connect_timeout=10
        )
        print(f"SUCCESS: Connected to {host}:{port}!")
        conn.close()
        return True
    except Exception as e:
        print(f"FAILED: Connected to {host}:{port} failed: {e}")
        return False

# Test combinations
test_conn("db.strfrhojgtnaoalxfssi.supabase.co", 5432, "postgres")
test_conn("aws-0-us-east-1.pooler.supabase.com", 6543, "postgres.strfrhojgtnaoalxfssi")
