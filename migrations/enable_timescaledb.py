"""
Database migration: Enable TimescaleDB and convert time_series_data to hypertable.

Track D: Data Infrastructure (M1 Foundation Scaling)

TimescaleDB converts the time_series_data table into a hypertable with
time-based chunking.  Queries that filter by timestamp (e.g. Granger
service fetching 90 days of data) only scan relevant chunks instead of
the full table — 10-100x speedup at scale.

Compression policy:  chunks older than 7 days are compressed (~90% size
reduction).  Retention policy: raw daily data kept for 2 years.

Prerequisites:
  - TimescaleDB extension must be available on the PostgreSQL instance.
    On Railway: check the PostgreSQL plugin supports it, or use a
    TimescaleDB-specific add-on.

Usage:
  python -m migrations.enable_timescaledb          # run upgrade
  python -m migrations.enable_timescaledb --check   # dry-run check only
"""

import sys
import logging
from sqlalchemy import text
from database import engine

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def check_timescaledb_available() -> bool:
    """Check if TimescaleDB extension is available (not necessarily enabled)."""
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'"
        ))
        return result.fetchone() is not None


def check_already_hypertable() -> bool:
    """Check if time_series_data is already a hypertable."""
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 1 FROM timescaledb_information.hypertables
            WHERE hypertable_name = 'time_series_data'
        """))
        return result.fetchone() is not None


def upgrade():
    """Enable TimescaleDB and convert time_series_data to a hypertable."""

    # ------------------------------------------------------------------
    # Step 1: Enable extension
    # ------------------------------------------------------------------
    with engine.begin() as conn:
        logger.info("Enabling TimescaleDB extension...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"))
        logger.info("TimescaleDB extension enabled.")

    # ------------------------------------------------------------------
    # Step 2: Check if already converted
    # ------------------------------------------------------------------
    try:
        if check_already_hypertable():
            logger.info("time_series_data is already a hypertable — skipping conversion.")
            _add_policies()
            return
    except Exception:
        pass  # timescaledb_information may not exist yet if extension just created

    # ------------------------------------------------------------------
    # Step 3: Convert to hypertable
    #
    # TimescaleDB requires the partitioning column (timestamp) to be
    # part of any UNIQUE / PRIMARY KEY constraint.  The current table
    # has `id SERIAL PRIMARY KEY` which conflicts.
    #
    # Strategy: drop the PK on id, add a composite PK on (id, timestamp),
    # then convert.  This is safe because no other table has a FK to
    # time_series_data.id.
    # ------------------------------------------------------------------
    with engine.begin() as conn:
        logger.info("Preparing time_series_data for hypertable conversion...")

        # Drop existing primary key constraint
        conn.execute(text("""
            ALTER TABLE time_series_data
            DROP CONSTRAINT IF EXISTS time_series_data_pkey
        """))

        # Add composite primary key that includes the time column
        conn.execute(text("""
            ALTER TABLE time_series_data
            ADD PRIMARY KEY (id, "timestamp")
        """))

        logger.info("Converting time_series_data to hypertable (chunk_interval = 1 month)...")
        conn.execute(text("""
            SELECT create_hypertable(
                'time_series_data',
                'timestamp',
                chunk_time_interval => INTERVAL '1 month',
                if_not_exists => TRUE,
                migrate_data => TRUE
            )
        """))
        logger.info("Hypertable conversion complete.")

    _add_policies()


def _add_policies():
    """Add compression and retention policies to the hypertable."""

    with engine.begin() as conn:
        # ------------------------------------------------------------------
        # Step 4: Compression policy — compress chunks older than 7 days
        # Segment by variable_id (most queries filter by variable)
        # Order by timestamp (range scans)
        # ------------------------------------------------------------------
        logger.info("Enabling compression on time_series_data...")
        conn.execute(text("""
            ALTER TABLE time_series_data SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'variable_id',
                timescaledb.compress_orderby = '"timestamp" DESC'
            )
        """))

        conn.execute(text("""
            SELECT add_compression_policy(
                'time_series_data',
                INTERVAL '7 days',
                if_not_exists => TRUE
            )
        """))
        logger.info("Compression policy added (compress after 7 days).")

        # ------------------------------------------------------------------
        # Step 5: Retention policy — drop raw chunks older than 2 years
        # Aggregated monthly data should be pre-computed and stored
        # separately before this kicks in.
        # ------------------------------------------------------------------
        conn.execute(text("""
            SELECT add_retention_policy(
                'time_series_data',
                INTERVAL '2 years',
                if_not_exists => TRUE
            )
        """))
        logger.info("Retention policy added (drop chunks older than 2 years).")


def check():
    """Dry-run: report whether TimescaleDB is available and current state."""
    available = check_timescaledb_available()
    logger.info(f"TimescaleDB extension available: {available}")

    if available:
        try:
            is_hypertable = check_already_hypertable()
            logger.info(f"time_series_data is hypertable: {is_hypertable}")
        except Exception as e:
            logger.info(f"Cannot check hypertable status: {e}")

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT COUNT(*) FROM time_series_data"
        ))
        count = result.scalar()
        logger.info(f"time_series_data row count: {count:,}")


if __name__ == "__main__":
    if "--check" in sys.argv:
        check()
    else:
        if not check_timescaledb_available():
            logger.error(
                "TimescaleDB extension is NOT available on this PostgreSQL instance.\n"
                "Please enable TimescaleDB on Railway or use a TimescaleDB-compatible provider."
            )
            sys.exit(1)
        upgrade()
        logger.info("Migration complete.")
