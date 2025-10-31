"""
Test database connection using common-service imports
Run inside Docker: docker exec -it audio-ai-service python test_db_connection.py
"""

import sys
sys.path.append('/common-service')

import os
from repository.base_repository import BaseRepository
from db import DBFactory, UnitOfWork
from sqlalchemy import text

def test_connection():
    print("Testing database connection...")
    print(f"DATABASE_URL set: {bool(os.getenv('DATABASE_URL'))}")
    
    try:
        # Initialize database
        DBFactory.init()
        print("✅ Database factory initialized (from common-service)")
        
        # Test query
        with UnitOfWork() as uow:
            result = uow.session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Test query successful: {row}")
        
        # Test table existence
        with UnitOfWork() as uow:
            result = uow.session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('media_files', 'ai_analysis', 'transcripts', 'candidates')
            """))
            tables = result.fetchall()
            print(f"✅ Found tables: {[t[0] for t in tables]}")
        
        print("\n🎉 Database connection test PASSED!")
        print("✅ Successfully importing from common-service!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database connection test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_connection()