"""
Database migration (Track I — Autonomous Loop Closure):
Hard-delete all manually-injected exploitation recommendations (source='manual').

Rationale:
    Manual idea injection has been removed from the application. The autonomous
    Discovery → Adapt → Exploit → Monitor → Learn → Optimize loop requires that
    every recommendation originate from Discovery. Existing manual rows must be
    purged so they cannot contaminate downstream learning signals (verification
    outcomes, telemetry, prompt performance).

    See:
      - Causal_Affect_Scaling_Plan.yaml#out_of_scope
      - causal_affect_outstanding_items.yaml M2-OA-15

Idempotent: safe to run multiple times. No-op if no manual rows exist.
"""

from sqlalchemy import text
from database import engine


def upgrade():
    with engine.begin() as conn:
        # Confirm the column still exists (it does — kept for granger/future provenance)
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_name = 'exploitation_recommendations'
              AND column_name = 'source'
        """)).scalar()
        if not result:
            print("  source column not present — nothing to delete")
            return

        # Count first for logging
        count = conn.execute(text("""
            SELECT COUNT(*) FROM exploitation_recommendations WHERE source = 'manual'
        """)).scalar() or 0

        if count == 0:
            print("  No source='manual' rows found — nothing to delete")
            return

        # Hard delete
        conn.execute(text("""
            DELETE FROM exploitation_recommendations WHERE source = 'manual'
        """))
        print(f"  Hard-deleted {count} source='manual' recommendation(s)")


if __name__ == "__main__":
    upgrade()
