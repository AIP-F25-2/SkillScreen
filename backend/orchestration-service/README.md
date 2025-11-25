# Orchestration Service

Orchestrates multiple microservices for interview workflows.

## Features
- Coordinates question generation with TTS
- Orchestrates video processing and AI analysis
- Manages complete interview workflows

## Quick Start

```bash
# Run locally
uvicorn orchestration:app --host 0.0.0.0 --port 8080 --reload
```

## Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status

