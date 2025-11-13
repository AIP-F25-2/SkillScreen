# Quick Reference: Server Logs & Dummy Data

## 📋 How to Check Server Logs

### 1. **Terminal Output (Best for Real-time)**
If you started the server with:
```bash
python -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```
**Errors now print directly to the console** with full tracebacks!

### 2. **Log Files**
```powershell
# Latest error
Get-Content logs/errors.log -Tail 1

# Last 20 lines
Get-Content logs/errors.log -Tail 20

# Search for specific errors
Get-Content logs/errors.log | Select-String -Pattern "Job|Traceback" -Context 10

# Watch in real-time
Get-Content logs/errors.log -Wait -Tail 10
```

### 3. **Main Application Log**
```powershell
Get-Content logs/skillscreen.log -Tail 20
```

## 🔧 Using Dummy IDs for NOT NULL Columns

**Yes, this is a valid approach!** The interview endpoint already creates User records automatically from Candidates.

### Current Status:
- ✅ **Candidates & Jobs**: Can be inserted directly (no foreign keys)
- ✅ **Users**: Created automatically when starting an interview
- ⚠️ **Interviews**: Require User records (now handled automatically)
- ⚠️ **Interview Sessions**: Require Interview records
- ⚠️ **Responses**: Require Interview and Session records
- ⚠️ **AI Analysis**: Require Interview records

### The "Job" Error:
The error `name 'Job' is not defined` is a **code error**, not a database constraint issue. It means somewhere in the code, there's a reference to `Job` instead of `JobPosition`.

**The enhanced error logging will now show the exact line** in the console when you run the test.

## 🚀 Next Steps

1. **Run the test again** - The console will show the full traceback with the exact line causing the "Job" error
2. **Check the terminal** where uvicorn is running - errors print there now
3. **Fix the "Job" reference** once we see the exact line

## 📝 Quick Commands

```powershell
# Test interview flow
python test_interview_with_db_check.py

# Insert dummy data (candidates & jobs only)
python insert_dummy_data.py

# Check latest error
Get-Content logs/errors.log -Tail 1

# Watch errors in real-time
Get-Content logs/errors.log -Wait -Tail 10
```

