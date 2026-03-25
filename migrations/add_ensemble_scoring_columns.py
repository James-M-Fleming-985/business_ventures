"""
Database migration: Add ensemble scoring columns to exploitation_recommendations
Adds ensemble R² and predicted change % so exploitation scoring can incorporate
full ensemble AI outputs (Granger + OLS + ARIMA) rather than just Granger p-values.
"""

from sqlalchemy import text
from database import engine


def upgrade():
    """Add ensemble scoring columns to exploitation_recommendations"""
    columns = [
        ("ensemble_r_squared", "FLOAT"),
        ("ensemble_change_pct", "FLOAT"),
    ]

    with engine.begin() as conn:
        for col_name, col_type in columns:
            conn.execute(text(f"""
                ALTER TABLE exploitation_recommendations
                ADD COLUMN IF NOT EXISTS {col_name} {col_type}
            """))
            print(f"  Added column: {col_name} ({col_type})")

    print("Migration complete: ensemble scoring columns added")


def downgrade():
    """Remove ensemble scoring columns"""
    columns = ["ensemble_r_squared", "ensemble_change_pct"]

    with engine.begin() as conn:
        for col_name in columns:
            conn.execute(text(f"""
                ALTER TABLE exploitation_recommendations
                DROP COLUMN IF EXISTS {col_name}
            """))

    print("Downgrade complete: ensemble scoring columns removed")


if __name__ == "__main__":
    print("Running migration: add_ensemble_scoring_columns")
    upgrade()
