import psycopg2
import psycopg2.extras
from config import settings

# ================================================================
# DATABASE CONNECTION & SETUP — PostgreSQL
# ================================================================

def get_db() -> psycopg2.extensions.connection:
    """
    Returns a new Postgres connection.
    Always use in a try/finally block to ensure it gets closed.

    Example:
        conn = get_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT ...")
            conn.commit()
        finally:
            conn.close()
    """
    conn = psycopg2.connect(
        settings.database_url,
        cursor_factory=psycopg2.extras.RealDictCursor,  # rows as dicts
    )
    return conn


def init_db():
    """
    Creates all tables if they don't exist.
    Called once on app startup from main.py.
    Add new CREATE TABLE statements here as your app grows.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscribers (
                    id          SERIAL PRIMARY KEY,
                    email       TEXT NOT NULL UNIQUE,
                    name        TEXT,
                    source      TEXT DEFAULT 'website',
                    subscribed  BOOLEAN DEFAULT TRUE,
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS orders (
                    id                  SERIAL PRIMARY KEY,
                    stripe_payment_id   TEXT NOT NULL UNIQUE,
                    product_id          TEXT NOT NULL,
                    product_name        TEXT NOT NULL,
                    amount              INTEGER NOT NULL,
                    currency            TEXT NOT NULL,
                    status              TEXT NOT NULL DEFAULT 'pending',
                    customer_email      TEXT,
                    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
        conn.commit()
    finally:
        conn.close()

