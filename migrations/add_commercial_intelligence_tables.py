"""
Database migration: Create product_deployments + product_metrics tables (M1 Track G)
Commercial intelligence foundation — tracks deployed products and their metrics.
"""

from sqlalchemy import text
from database import engine


def upgrade():
    """Create product_deployments and product_metrics tables"""
    with engine.begin() as conn:
        # ProductDeployment
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product_deployments (
                id SERIAL PRIMARY KEY,
                recommendation_id INTEGER REFERENCES exploitation_recommendations(id),
                build_id INTEGER REFERENCES mvp_builds(id),
                product_name VARCHAR(255) NOT NULL,
                app_id VARCHAR(100) NOT NULL,
                description TEXT,
                tech_stack JSONB,
                template_ids JSONB,
                pricing_model VARCHAR(50),
                market_category VARCHAR(100),
                target_demographic VARCHAR(255),
                geographic_focus VARCHAR(100),
                railway_url VARCHAR(500),
                domain VARCHAR(255),
                deployed_at TIMESTAMP,
                status VARCHAR(20) NOT NULL DEFAULT 'active',
                outcome VARCHAR(20),
                outcome_notes TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pd_app_id ON product_deployments(app_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pd_status ON product_deployments(status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pd_market ON product_deployments(market_category)"))
        print("Created: product_deployments + 3 indexes")

        # ProductMetrics
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS product_metrics (
                id SERIAL PRIMARY KEY,
                deployment_id INTEGER NOT NULL REFERENCES product_deployments(id),
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                mrr_cents INTEGER DEFAULT 0,
                subscriber_count INTEGER DEFAULT 0,
                page_views INTEGER DEFAULT 0,
                unique_visitors INTEGER DEFAULT 0,
                avg_session_seconds FLOAT,
                conversion_rate FLOAT,
                churn_rate FLOAT,
                source VARCHAR(50) DEFAULT 'manual',
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pm_deployment ON product_metrics(deployment_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_pm_period ON product_metrics(period_start, period_end)"))
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_pm_deploy_period
            ON product_metrics(deployment_id, period_start)
        """))
        print("Created: product_metrics + 3 indexes")

    print("Migration complete: commercial intelligence tables created")


if __name__ == "__main__":
    upgrade()
