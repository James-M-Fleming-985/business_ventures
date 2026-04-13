"""
Migration: Add github_url column to mvp_builds + create mvp_page_views table.

Run on production DB before deploying the updated code.
Safe to re-run — uses IF NOT EXISTS / IF NOT EXISTS guards.

Usage:
    python migrations/add_github_url_and_page_views.py
"""

import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import engine
from sqlalchemy import text


def run():
    with engine.connect() as conn:
        # 1. Add github_url column to mvp_builds (if not exists)
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='mvp_builds' AND column_name='github_url'"
        ))
        if not result.fetchone():
            conn.execute(text(
                "ALTER TABLE mvp_builds ADD COLUMN github_url VARCHAR(500)"
            ))
            print("✅ Added github_url column to mvp_builds")
        else:
            print("⏭️  github_url column already exists")

        # 2. Migrate existing GitHub URLs out of railway_url
        updated = conn.execute(text(
            "UPDATE mvp_builds SET github_url = railway_url "
            "WHERE railway_url LIKE '%github.com%' AND github_url IS NULL"
        ))
        print(f"✅ Migrated {updated.rowcount} GitHub URLs to github_url column")

        # 3. Create mvp_page_views table (if not exists)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS mvp_page_views (
                id SERIAL PRIMARY KEY,
                build_id INTEGER NOT NULL REFERENCES mvp_builds(id),
                visitor_hash VARCHAR(64) NOT NULL,
                user_agent VARCHAR(500),
                referrer VARCHAR(500),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """))
        print("✅ Created mvp_page_views table (if not existed)")

        # 4. Create index on mvp_page_views
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_mpv_build_time
            ON mvp_page_views (build_id, created_at)
        """))
        print("✅ Created index ix_mpv_build_time")

        conn.commit()
        print("\n✅ Migration complete")


if __name__ == "__main__":
    run()
