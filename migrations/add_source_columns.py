"""
Database Migration: Add source1 and source2 columns to correlation_results table

Run this script to update the production database schema.
"""

from database import engine
from sqlalchemy import text

def migrate():
    """Add source1 and source2 columns to correlation_results"""
    
    with engine.connect() as conn:
        # Check if columns already exist
        check_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'correlation_results' 
            AND column_name IN ('source1', 'source2')
        """)
        existing = conn.execute(check_query).fetchall()
        existing_cols = [row[0] for row in existing]
        
        # Add source1 if not exists
        if 'source1' not in existing_cols:
            print("Adding source1 column...")
            conn.execute(text("""
                ALTER TABLE correlation_results 
                ADD COLUMN source1 VARCHAR(100)
            """))
            conn.commit()
            print("✓ source1 column added")
        else:
            print("source1 column already exists")
        
        # Add source2 if not exists
        if 'source2' not in existing_cols:
            print("Adding source2 column...")
            conn.execute(text("""
                ALTER TABLE correlation_results 
                ADD COLUMN source2 VARCHAR(100)
            """))
            conn.commit()
            print("✓ source2 column added")
        else:
            print("source2 column already exists")
        
        print("\nMigration complete!")
        print("Next step: Re-run correlation calculation to populate source tags")

if __name__ == "__main__":
    migrate()
