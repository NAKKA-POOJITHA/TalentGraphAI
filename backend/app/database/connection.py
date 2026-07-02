import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from app.utils.config import settings
from app.utils.logging import logger

def get_db_connection():
    """Create a direct connection to the Supabase PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL database at {settings.DB_HOST}: {e}")
        raise e

@contextmanager
def get_db_cursor():
    """Context manager to yield a dictionary cursor and auto-commit or roll back."""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error, rolled back transaction: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()

def test_db_connection() -> bool:
    """Test the database connection and return True if successful, False otherwise."""
    try:
        conn = get_db_connection()
        conn.close()
        logger.info("Successfully connected to Supabase PostgreSQL database!")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
