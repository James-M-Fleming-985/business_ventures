"""
Database migration: Create revenue_events table (M1 Track E)
Central log for all Stripe webhook financial events.
"""

from sqlalchemy import text
from database import engine


def upgrade():
    """Create revenue_events table"""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS revenue_events (
                id SERIAL PRIMARY KEY,
                app_id VARCHAR(100) NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                amount_cents INTEGER NOT NULL DEFAULT 0,
                currency VARCHAR(3) NOT NULL DEFAULT 'usd',
                stripe_event_id VARCHAR(255) UNIQUE,
                stripe_customer_id VARCHAR(255),
                stripe_subscription_id VARCHAR(255),
                user_id INTEGER REFERENCES users(id),
                tier VARCHAR(50),
                interval VARCHAR(20),
                metadata_json JSONB,
                event_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rev_app ON revenue_events(app_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rev_type ON revenue_events(event_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_rev_event_at ON revenue_events(event_at)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_rev_stripe_event ON revenue_events(stripe_event_id)"))

    print("Migration complete: revenue_events table created")


if __name__ == "__main__":
    upgrade()
