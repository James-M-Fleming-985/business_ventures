"""
Database migration: Create prediction_tracking table
Feature CA-002-10: Prediction Accuracy Tracking
"""

from sqlalchemy import text
from database import engine


def upgrade():
    """Create prediction_tracking table for storing predictions and actuals"""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS prediction_tracking (
                id SERIAL PRIMARY KEY,

                -- Identification
                prediction_id VARCHAR(50) UNIQUE NOT NULL,

                -- Variables involved (match deep-analysis response field names)
                signal_name VARCHAR(255) NOT NULL,
                target_name VARCHAR(255) NOT NULL,

                -- Timing
                predicted_at TIMESTAMP NOT NULL DEFAULT NOW(),
                target_date TIMESTAMP,
                optimal_lag_days INT,

                -- The prediction
                predicted_direction VARCHAR(10),
                predicted_value FLOAT,
                predicted_change_pct FLOAT,
                current_target_value FLOAT,
                current_signal_value FLOAT,

                -- Regression coefficients
                r_squared FLOAT,

                -- Model metadata
                model_version VARCHAR(50) NOT NULL DEFAULT 'granger_v1',
                confidence VARCHAR(20) DEFAULT 'medium',
                signal_momentum FLOAT,

                -- Actual outcome (NULL until data available)
                actual_value FLOAT,
                actual_direction VARCHAR(10),

                -- Accuracy metrics (calculated after actual known)
                direction_correct BOOLEAN,
                value_error_pct FLOAT,

                -- Status: 'pending' | 'validated' | 'expired'
                status VARCHAR(20) DEFAULT 'pending',

                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pred_track_target_date
            ON prediction_tracking(target_date);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pred_track_status
            ON prediction_tracking(status);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pred_track_model
            ON prediction_tracking(model_version);
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_pred_track_variables
            ON prediction_tracking(signal_name, target_name);
        """))

    print("✅ prediction_tracking table created (CA-002-10)")


def downgrade():
    """Drop prediction_tracking table"""
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS prediction_tracking CASCADE"))
    print("🗑️  prediction_tracking table dropped")


if __name__ == "__main__":
    upgrade()
