"""
Database migration: Add Granger Causality columns to CorrelationResult
Phase 2 of Causal Affect Exploitation Pathway
"""

from sqlalchemy import text
from database import engine

def upgrade():
    """Add Granger causality columns"""
    with engine.connect() as conn:
        # Add causal_direction column
        conn.execute(text("""
            ALTER TABLE correlation_results 
            ADD COLUMN IF NOT EXISTS causal_direction VARCHAR(20)
        """))
        
        # Add granger_p_value_xy column (var1 → var2)
        conn.execute(text("""
            ALTER TABLE correlation_results 
            ADD COLUMN IF NOT EXISTS granger_p_value_xy FLOAT
        """))
        
        # Add granger_p_value_yx column (var2 → var1)
        conn.execute(text("""
            ALTER TABLE correlation_results 
            ADD COLUMN IF NOT EXISTS granger_p_value_yx FLOAT
        """))
        
        # Add granger_lags column
        conn.execute(text("""
            ALTER TABLE correlation_results 
            ADD COLUMN IF NOT EXISTS granger_lags INTEGER
        """))
        
        conn.commit()
        
        print("✅ Successfully added Granger causality columns to correlation_results table")

def downgrade():
    """Remove Granger causality columns"""
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE correlation_results DROP COLUMN IF EXISTS causal_direction"))
        conn.execute(text("ALTER TABLE correlation_results DROP COLUMN IF EXISTS granger_p_value_xy"))
        conn.execute(text("ALTER TABLE correlation_results DROP COLUMN IF EXISTS granger_p_value_yx"))
        conn.execute(text("ALTER TABLE correlation_results DROP COLUMN IF EXISTS granger_lags"))
        conn.commit()
        
        print("✅ Removed Granger causality columns from correlation_results table")

if __name__ == "__main__":
    print("Running Granger Causality migration...")
    upgrade()
