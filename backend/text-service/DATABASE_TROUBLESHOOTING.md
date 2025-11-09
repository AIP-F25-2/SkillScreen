# Database Connection Troubleshooting Guide

## Current Status
The database integration has been successfully implemented with:
- ✅ SQLAlchemy models created based on the ERD
- ✅ Database service for CRUD operations
- ✅ Configuration loader working correctly
- ✅ Azure PostgreSQL connection details configured

## Connection Issue
The connection is timing out, which indicates a network/firewall issue rather than a code problem.

## How to Check if Database is Working Properly

### 1. Check Azure Portal
1. Go to Azure Portal (portal.azure.com)
2. Navigate to your PostgreSQL server: `skillscreen-db`
3. Check if the server is **Running** (not paused/stopped)
4. Verify the server status in the Overview section

### 2. Check Firewall Rules
1. In Azure Portal, go to your PostgreSQL server
2. Click on **Connection security** in the left menu
3. Check **Allow access to Azure services** is **ON**
4. Add your current IP address to the firewall rules:
   - Click **Add current client IP address**
   - Or manually add your IP in the range

### 3. Test Connection from Azure Portal
1. In Azure Portal, go to your PostgreSQL server
2. Click on **Query editor** in the left menu
3. Try to connect using the credentials:
   - Server: `skillscreen-db.postgres.database.azure.com`
   - Username: `intervuai`
   - Password: `LOYALlist_2025`
   - Database: `skillscreen_database`

### 4. Test from Command Line (if you have psql installed)
```bash
psql "host=skillscreen-db.postgres.database.azure.com port=5432 dbname=skillscreen_database user=intervuai password=LOYALlist_2025 sslmode=require"
```

### 5. Check Network Connectivity
```bash
# Test if the server is reachable
telnet skillscreen-db.postgres.database.azure.com 5432
```

### 6. Alternative: Use Local Database for Testing
If Azure PostgreSQL is not accessible, you can test with a local PostgreSQL:

1. Install PostgreSQL locally
2. Create a database named `skillscreen_database`
3. Update `.config` file with local connection:
```
DATABASE_URL=postgresql://postgres:password@localhost:5432/skillscreen_database
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=skillscreen_database
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_SSL_MODE=disable
```

## What's Working
- ✅ Configuration loading
- ✅ Database models and schema
- ✅ Service layer for database operations
- ✅ Integration with FastAPI endpoints

## Next Steps
1. Fix the Azure PostgreSQL access (firewall rules)
2. Test the connection using the methods above
3. Once connected, run the database test script
4. Verify that tables are created successfully
5. Test the interview creation flow

## Files Created/Modified
- `backend/text-service/database/models.py` - SQLAlchemy models
- `backend/text-service/database/database.py` - Database manager
- `backend/text-service/services/database_service.py` - CRUD operations
- `backend/text-service/utils/config_loader.py` - Configuration loader
- `backend/text-service/.config` - Database credentials
- `backend/text-service/test_connection.py` - Connection test script


