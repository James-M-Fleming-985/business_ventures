#!/usr/bin/env python3
"""
Test script to initialize database and verify setup
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db

if __name__ == "__main__":
    print("🚀 Initializing database...")
    init_db()
    print("✅ Database tables created successfully")
    print("📊 Tables: users, baselines, exploration_history")
    print("🎯 Ready to start FastAPI server with: python -m app.main")
