"""
Database migration: Create model_changelog table.

Tracks every change to MODEL_VERSION_CONFIGS so the dashboard user can
answer: what changed, when, and what impact did it have.
"""

from sqlalchemy import text
from database import engine


def upgrade():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS model_changelog (
                id SERIAL PRIMARY KEY,
                version VARCHAR(20) NOT NULL,
                changed_at TIMESTAMP NOT NULL DEFAULT NOW(),
                change_type VARCHAR(50) NOT NULL,
                description TEXT NOT NULL,
                config_snapshot JSONB NOT NULL,
                previous_config JSONB,
                metrics_before JSONB,
                metrics_after JSONB,
                impact_assessed BOOLEAN DEFAULT FALSE
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_mcl_version ON model_changelog(version)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_mcl_changed_at ON model_changelog(changed_at)"))
    print("Migration complete: model_changelog table created")


if __name__ == "__main__":
    upgrade()
