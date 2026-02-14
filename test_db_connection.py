from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import sys

# URL from the running container environment
db_url = "postgresql://intervuai:LOYALlist_2025@skillscreen-postgres.postgres.database.azure.com:5432/skillscreen_database?sslmode=require"

print(f"Attempting to connect to: {db_url}")

try:
    engine = create_engine(db_url)
    connection = engine.connect()
    print("Successfully connected to the database!")
    
    # Optional: Run a simple query
    result = connection.execute("SELECT 1").fetchone()
    print(f"Query result: {result}")
    
    connection.close()
except Exception as e:
    print(f"Failed to connect: {e}")
    sys.exit(1)
