#!/bin/bash

# --------------------------
# Variables
# --------------------------
VENV_DIR="env"
LOG_DIR="logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/server_$TIMESTAMP.log"
APP_FILE="app.py"

# --------------------------
# Activate virtual environment
# --------------------------
if [ -d "$VENV_DIR" ]; then
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    echo "Virtual environment '$VENV_DIR' not found!"
    exit 1
fi

# --------------------------
# Create logs folder if not exists
# --------------------------
mkdir -p "$LOG_DIR"

# --------------------------
# Run Flask + SocketIO app
# --------------------------
echo "Starting TTS + STT server..."
echo "Logs will be saved to $LOG_FILE"

# Run server and save both stdout and stderr
python "$APP_FILE" &> "$LOG_FILE"
