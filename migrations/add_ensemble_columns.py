"""
Database migration: Add ensemble model columns to exploitation_recommendations
Stores ensemble prediction confidence/direction for viability ranking (M2 Track A).
"""

from sqlalchemy import text
from database import engine


def upgrade():
    """Add ensemble enrichment columns to exploitation_recommendations"""
    columns = [
        ("ensemble_confidence", "VARCHAR(20)"),
        ("ensemble_direction", "VARCHAR(10)"),
        ("ensemble_predicted_at", "TIMESTAMP"),
    ]

    with engine.begin() as conn:
        for col_name, col_type in columns:
            conn.execute(text(f"""
                ALTER TABLE exploitation_recommendations
                ADD COLUMN IF NOT EXISTS {col_name} {col_type}
            """))
            print(f"  Added column: {col_name} ({col_type})")

    print("Migration complete: ensemble enrichment columns added")


if __name__ == "__main__":
    upgrade()
