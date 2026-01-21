"""
Migration: Add Users Table
Creates the users table for authentication
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from models import Base, User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        database_url = os.getenv(
            'DATABASE_URL_FALLBACK',
            'postgresql://postgres:postgres@localhost:5432/causal_affect'
        )
    
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url


def run_migration():
    """Create users table if it doesn't exist"""
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    if 'users' in existing_tables:
        logger.info("✅ Users table already exists")
        
        # Check columns
        columns = [col['name'] for col in inspector.get_columns('users')]
        logger.info(f"Existing columns: {columns}")
        return True
    
    logger.info("Creating users table...")
    
    # Create only the User table
    User.__table__.create(engine, checkfirst=True)
    
    logger.info("✅ Users table created successfully")
    
    # Verify
    inspector = inspect(engine)
    if 'users' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('users')]
        logger.info(f"Created with columns: {columns}")
        return True
    else:
        logger.error("❌ Failed to create users table")
        return False


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
