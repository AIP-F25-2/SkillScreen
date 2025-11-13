# How to Start the Server

## Issue with --reload flag

When using `--reload`, uvicorn spawns a subprocess that might use a different Python environment. If you see `ModuleNotFoundError`, try these solutions:

## Solution 1: Run without --reload (Recommended for testing)

```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

This will start the server without auto-reload. You'll need to restart manually when you make changes.

## Solution 2: Activate virtual environment properly

Make sure your virtual environment is activated:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Then start server
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

## Solution 3: Use python -m uvicorn

```bash
python -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

This ensures it uses the correct Python interpreter.

## Solution 4: Install dependencies in virtual environment

If packages are missing in the subprocess:

```bash
# Activate venv first
.venv\Scripts\Activate.ps1

# Install all dependencies
pip install aiofiles fastapi uvicorn[standard] sqlalchemy psycopg[binary]
```

## Quick Start (No Reload)

For testing the interview session, use:

```bash
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
```

Then in another terminal, run:
```bash
python test_interview_quick.py
```

## Expected Output

When the server starts successfully, you should see:

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

You may see Unicode warnings (from emoji in logs) - these are harmless and won't affect functionality.

