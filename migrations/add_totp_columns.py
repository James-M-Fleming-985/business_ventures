"""Migration: add TOTP two-factor columns to users (idempotent)."""

import logging

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

TOTP_COLUMNS = {
    "totp_secret": "VARCHAR(64)",
    "totp_enabled": "BOOLEAN DEFAULT FALSE",
    "totp_recovery_hashes": "TEXT",
    "totp_last_step": "INTEGER DEFAULT 0",
}


def upgrade(engine=None) -> list:
    """Add any missing TOTP columns. Returns the names that were added."""
    if engine is None:
        from database import engine as default_engine
        engine = default_engine

    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return []

    existing = {c["name"] for c in inspector.get_columns("users")}
    added = []
    with engine.begin() as conn:
        for name, ddl in TOTP_COLUMNS.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {ddl}"))
                added.append(name)
    if added:
        logger.info(f"Added users columns: {added}")
    return added
