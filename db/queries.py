import psycopg2
from db.database import get_db

# ================================================================
# DATABASE QUERIES — PostgreSQL
# All SQL lives here — routers just call these functions.
# Uses %s placeholders (psycopg2 style, not ? like sqlite)
# ================================================================


# ── Subscribers ──────────────────────────────────────────────────

def insert_subscriber(email: str, name: str | None, source: str) -> bool:
    """
    Insert a new subscriber. Returns True if inserted, False if already exists.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO subscribers (email, name, source)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (email) DO NOTHING""",
                (email.lower().strip(), name, source)
            )
            inserted = cur.rowcount > 0
        conn.commit()
        return inserted
    finally:
        conn.close()


def get_subscribers(limit: int = 100, offset: int = 0) -> tuple[int, list[dict]]:
    """Returns (total_count, list_of_subscribers)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, email, name, source, created_at
                   FROM subscribers
                   WHERE subscribed = TRUE
                   ORDER BY created_at DESC
                   LIMIT %s OFFSET %s""",
                (limit, offset)
            )
            rows = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM subscribers WHERE subscribed = TRUE")
            total = cur.fetchone()["count"]

        return total, [dict(r) for r in rows]
    finally:
        conn.close()


def unsubscribe_email(email: str) -> bool:
    """Soft delete — marks subscriber inactive. Returns True if found."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE subscribers SET subscribed = FALSE WHERE email = %s",
                (email.lower().strip(),)
            )
            found = cur.rowcount > 0
        conn.commit()
        return found
    finally:
        conn.close()


# ── Orders ───────────────────────────────────────────────────────

def insert_order(
    stripe_payment_id: str,
    product_id: str,
    product_name: str,
    amount: int,
    currency: str,
    status: str,
    customer_email: str | None = None,
) -> bool:
    """
    Insert a new order. Returns True if inserted, False if duplicate.
    Called from the Stripe webhook after payment succeeds.
    """
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO orders
                   (stripe_payment_id, product_id, product_name, amount, currency, status, customer_email)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (stripe_payment_id) DO NOTHING""",
                (stripe_payment_id, product_id, product_name, amount, currency, status, customer_email)
            )
            inserted = cur.rowcount > 0
        conn.commit()
        return inserted
    finally:
        conn.close()


def get_orders(limit: int = 100, offset: int = 0) -> tuple[int, list[dict]]:
    """Returns (total_count, list_of_orders)."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, stripe_payment_id, product_id, product_name,
                          amount, currency, status, customer_email, created_at
                   FROM orders
                   ORDER BY created_at DESC
                   LIMIT %s OFFSET %s""",
                (limit, offset)
            )
            rows = cur.fetchall()

            cur.execute("SELECT COUNT(*) FROM orders")
            total = cur.fetchone()["count"]

        return total, [dict(r) for r in rows]
    finally:
        conn.close()


def update_order_status(stripe_payment_id: str, status: str) -> bool:
    """Update the status of an order. Returns True if found."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE orders SET status = %s WHERE stripe_payment_id = %s",
                (status, stripe_payment_id)
            )
            found = cur.rowcount > 0
        conn.commit()
        return found
    finally:
        conn.close()

