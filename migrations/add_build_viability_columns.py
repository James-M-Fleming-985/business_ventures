"""
Database migration: Add BUILD viability columns to exploitation_recommendations
Adds BUILD-specific scoring fields: viability score, demand estimates, 
trend direction, revenue/competition sizing, market category.
"""

from sqlalchemy import text
from database import engine


def upgrade():
    """Add BUILD viability columns to exploitation_recommendations"""
    columns = [
        ("build_viability_score", "FLOAT"),
        ("estimated_monthly_searches", "INTEGER"),
        ("search_trend_direction", "VARCHAR(10)"),
        ("search_growth_pct", "FLOAT"),
        ("opportunity_duration_months", "INTEGER"),
        ("revenue_potential", "VARCHAR(10)"),
        ("competition_level", "VARCHAR(10)"),
        ("market_category", "VARCHAR(100)"),
    ]
    
    with engine.begin() as conn:
        for col_name, col_type in columns:
            conn.execute(text(f"""
                ALTER TABLE exploitation_recommendations
                ADD COLUMN IF NOT EXISTS {col_name} {col_type}
            """))
            print(f"  Added column: {col_name} ({col_type})")
    
    print("Migration complete: BUILD viability columns added")


def downgrade():
    """Remove BUILD viability columns"""
    columns = [
        "build_viability_score", "estimated_monthly_searches",
        "search_trend_direction", "search_growth_pct",
        "opportunity_duration_months", "revenue_potential",
        "competition_level", "market_category",
    ]
    
    with engine.begin() as conn:
        for col_name in columns:
            conn.execute(text(f"""
                ALTER TABLE exploitation_recommendations
                DROP COLUMN IF EXISTS {col_name}
            """))
    
    print("Downgrade complete: BUILD viability columns removed")


if __name__ == "__main__":
    print("Running migration: add_build_viability_columns")
    upgrade()
