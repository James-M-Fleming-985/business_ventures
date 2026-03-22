"""
Database migration: Add target_growth_actual columns to exploitation_recommendations
Tracks actual % change in target variable over the opportunity window (M1 Track C).
"""

from sqlalchemy import text
from database import engine


def upgrade():
    """Add outcome-tracking columns to exploitation_recommendations"""
    columns = [
        ("target_growth_actual", "FLOAT"),
        ("target_growth_measured_at", "TIMESTAMP"),
    ]

    with engine.begin() as conn:
        for col_name, col_type in columns:
            conn.execute(text(f"""
                ALTER TABLE exploitation_recommendations
                ADD COLUMN IF NOT EXISTS {col_name} {col_type}
            """))
            print(f"  Added column: {col_name} ({col_type})")

    print("Migration complete: target_growth_actual columns added")


if __name__ == "__main__":
    upgrade()
