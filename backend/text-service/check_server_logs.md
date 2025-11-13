# How to Check Server Logs

## Method 1: Check the Terminal Running Uvicorn
If you started the server with:
```bash
python -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

The logs will appear directly in that terminal window. Look for:
- `ERROR` messages
- `Traceback` output
- Any exceptions

## Method 2: Check Log Files
The application writes logs to several files:

### Error Log
```bash
# View last 20 lines
Get-Content logs/errors.log -Tail 20

# View last 50 lines with context
Get-Content logs/errors.log -Tail 50

# Search for specific errors
Get-Content logs/errors.log | Select-String -Pattern "Job|Traceback" -Context 5
```

### Main Application Log
```bash
# View last 20 lines
Get-Content logs/skillscreen.log -Tail 20

# Search for interview-related logs
Get-Content logs/skillscreen.log | Select-String -Pattern "interview|ERROR" -Context 3
```

## Method 3: Real-time Log Monitoring
Watch logs in real-time (PowerShell):
```powershell
# Watch error log
Get-Content logs/errors.log -Wait -Tail 10

# Watch main log
Get-Content logs/skillscreen.log -Wait -Tail 10
```

## Method 4: Check Server Response Directly
The server now prints errors to console. If you're running uvicorn in a terminal, you'll see:
```
============================================================
ERROR in start_interview endpoint:
============================================================
Error: name 'Job' is not defined

Traceback:
...
```

## Method 5: Use API Testing Tools
- **Postman**: Check the response body for error details
- **curl**: 
  ```bash
  curl -X POST http://localhost:8000/api/interviews/start -H "Content-Type: application/json" -d @test_data.json
  ```

## Quick Check Command
Run this to see the latest error:
```powershell
Get-Content logs/errors.log -Tail 1
Get-Content logs/skillscreen.log -Tail 5
```

