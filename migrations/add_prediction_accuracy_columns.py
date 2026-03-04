"""
Database migration: Add accuracy tracking columns to prediction_tracking table.
Adds: actual_change_pct, actual_lag_days, lag_error_days, granger_p_value, target_source
"""

from sqlalchemy import text
from database import engine


def upgrade():
    """Add new accuracy tracking columns to prediction_tracking"""
    with engine.begin() as conn:
        columns = [
            ("actual_change_pct", "FLOAT"),
            ("actual_lag_days", "INTEGER"),
            ("lag_error_days", "INTEGER"),
            ("granger_p_value", "FLOAT"),
            ("target_source", "VARCHAR(100)"),
        ]
        for col_name, col_type in columns:
            try:
                conn.execute(text(
                    f"ALTER TABLE prediction_tracking ADD COLUMN {col_name} {col_type}"
                ))
                print(f"  ✅ Added column {col_name}")
            except Exception as e:
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"  ⏭️  Column {col_name} already exists")
                else:
                    print(f"  ⚠️  Column {col_name}: {e}")

    print("✅ prediction_tracking accuracy columns migration complete")
