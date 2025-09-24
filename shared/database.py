"""
Shared database connection utility for all services
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Get database URL from environment or use default
            database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@postgres:5432/ai_interview_platform_dev')
            
            self.connection = psycopg2.connect(database_url)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            logger.info("Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database disconnected")
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        try:
            if not self.connection or self.connection.closed:
                self.connect()
            
            self.cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                self.connection.commit()
                return self.cursor.rowcount
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            if self.connection:
                self.connection.rollback()
            raise e
    
    def health_check(self):
        """Check if database is accessible"""
        try:
            result = self.execute_query("SELECT 1 as health_check")
            return len(result) > 0
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False

# Global database instance
db = DatabaseConnection()

def init_database():
    """Initialize database with basic tables"""
    try:
        if not db.connect():
            return False
            
        # Create users table if it doesn't exist
        create_users_table = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        db.execute_query(create_users_table)
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return False
