"""
Database migration: Create version_comparison_cache table.

Persists the expensive ensemble replay output across Railway redeploys so
the dashboard checkboxes render on first page load instead of waiting for
the user to manually trigger a ~60s recomputation.
"""

from sqlalchemy import text
from database import engine


def upgrade():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS version_comparison_cache (
                id SERIAL PRIMARY KEY,
                data JSONB NOT NULL,
                computed_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """))
    print("Migration complete: version_comparison_cache table created")


if __name__ == "__main__":
    upgrade()
