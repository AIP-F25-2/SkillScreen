"""
Migration script to create interview_tokens table
Run this after updating the database schema
"""

import os
import sys
from sqlalchemy import text

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from db import DBFactory


def create_interview_tokens_table():
    """Create the interview_tokens table"""

    sql = """
    CREATE TABLE IF NOT EXISTS interview_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        token VARCHAR(255) UNIQUE NOT NULL,
        candidate_id UUID NOT NULL,
        candidate_name VARCHAR(255),
        candidate_email VARCHAR(255),
        session_id VARCHAR(255),
        interview_id UUID,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        used_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Create index on token for faster lookups
    CREATE INDEX IF NOT EXISTS idx_interview_tokens_token ON interview_tokens(token);

    -- Create index on candidate_id for finding tokens by candidate
    CREATE INDEX IF NOT EXISTS idx_interview_tokens_candidate_id ON interview_tokens(candidate_id);

    -- Create index on expires_at for cleanup queries
    CREATE INDEX IF NOT EXISTS idx_interview_tokens_expires_at ON interview_tokens(expires_at);
    """

    try:
        session = DBFactory.get_session()
        for statement in sql.split(';'):
            if statement.strip():
                session.execute(text(statement))
        session.commit()
        print("✅ Successfully created interview_tokens table and indexes")
        return True
    except Exception as e:
        print(f"❌ Failed to create interview_tokens table: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print("Creating interview_tokens table...")
    success = create_interview_tokens_table()
    sys.exit(0 if success else 1)
