# Anti‑Cheating Video Service (FastAPI, MVC)

A production‑ready service for one‑person exam recordings. It detects:
- Face presence & tracking, identity consistency (same person), **liveness**
- **Gaze** (eye‑contact proxy), **head pose**, **posture**
- **Anti‑cheating** signals: multiple faces, additional persons, **prohibited items** (phone/laptop/book)
- **Environment**: lighting & background motion
- **Engagement** score
- Returns **timeframes** (start/end in seconds) for each event, plus metrics & overall verdict

## Folder layout (MVC)
```
app/
  controllers/
    analyze_controller.py
  core/
    config.py
    logging.py
    segmentation.py
  services/
    models_loader.py
    detectors.py
    analysis.py
    pose_helper.py
    pipelines/
      cheating_pipeline.py
.env.example
requirements.txt
Dockerfile
docker-compose.yml
```

### Quick start
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # set model paths in ./models
uvicorn app.main:app --reload
```

### API
- `POST /analyze` -> `{ "input_path": "path/to/video.mp4" }` returns JSON with segments and summary.
- `POSTMAN Link` ->  [POSTMAN LINK](https://web.postman.co/workspace/My-Workspace~d654d325-098b-43d3-8bdc-459980921bae/collection/6664275-6add62e5-a00b-4ca0-9011-476c055919fc?action=share&source=copy-link&creator=6664275) to test all the endpoints.

### Notes
- Uses **Ultralytics YOLO** for faces/persons/objects; swap model paths in `.env`.
- Identity/liveness are efficient heuristics; you can plug real **face embeddings** later.
- Pose helper stub is ready to wire YOLO‑pose keypoints for richer head/posture analysis.
