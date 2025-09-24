#!/bin/bash

# Create logs directory if it doesn't exist
mkdir -p logs

# Generate a timestamp (format: YYYYMMDD_HHMMSS)
timestamp=$(date +%Y%m%d_%H%M%S)

# Run TTS server and save output
echo "Starting TTS server..."
nohup python Local_TTS_Code/app.py > logs/tts_$timestamp.log 2>&1 &

# Run STT server and save output
echo "Starting STT server..."
nohup python Offline_STT_Code_With_Live_Streaming/app.py > logs/stt_$timestamp.log 2>&1 &

echo "Both servers are running. Check logs/tts_$timestamp.log and logs/stt_$timestamp.log for output."


# To list all the running Python processes, you can use:
# ps aux | grep python

#To kill the processes, you can use:
# kill -9 <PID>

# Usage:
# Make the script executable:
# chmod +x run_all.sh

# Run it:
# ./run_all.sh

# TTS output → logs/tts.log
# STT output → logs/stt.log

# Windows Batch File (run_all.bat)
# @echo off
# mkdir logs 2>nul

# echo Starting TTS server...
# start "" cmd /k "python path\to\tts_app\app.py > logs\tts.log 2>&1"

# echo Starting STT server...
# start "" cmd /k "python path\to\stt_app\app.py > logs\stt.log 2>&1"

# echo Both servers started. Check logs\tts.log and logs\stt.log
# Save as run_all.bat and double-click or run from command prompt.
# Each server runs in its own terminal window, output saved to respective log file.
# This way, you only run one command (./run_all.sh or double-click run_all.bat) and both services start simultaneously, with all terminal output saved for later inspection.
# I can also modify the script to tail both logs live in the terminal if you want real-time monitoring.