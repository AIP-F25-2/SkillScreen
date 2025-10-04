# Video Processing API

A Flask-based REST API for processing videos, managing user video uploads, and retrieving annotated videos. Supports listing, searching, and deleting videos by user, with detailed reports.

---

## Features

- Process videos and generate annotated versions.
- Organize videos per user.
- List, search, and delete videos.
- Serve videos for playback or download.
- Check video existence.
- Retrieve all users.

---

## Project Structure

```

.
├── app.py                     # Main Flask application
├── services/
│   └── video_processor.py     # Video processing logic
├── templates/
│   └── index.html             # Frontend template
├── processed_videos/          # Output videos (auto-created)
├── requirements.txt           # Python dependencies
├── .env                       # Configuration
└── README.md

```

---

## Setup

### 1. Clone the repository
```bash
git clone <repo-url>
cd <repo-folder>
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
SERVER_HOST=0.0.0.0
SERVER_PORT=5010
FLASK_DEBUG=True
PROCESSED_FOLDER=processed_videos
```

---

## Running the Server

```bash
python app.py
```

Access the frontend at:
`http://localhost:5010/`

---

## API Endpoints

### 1. Process Video

**POST** `/api/process_video`
Process a video and generate an annotated version.

**Request Body (JSON)**:

```json
{
  "video_url": "uploads/sample.mp4"
}
```

**Response**:

```json
{
  "annotated_video_url": "/api/videos/user1/sample_annotated.mp4",
  "report": {
      "faces_detected": 3,
      "duration": "00:00:15"
  }
}
```

---

### 2. List All Videos Grouped by User

**GET** `/api/all_videos_by_user`

**Response**:

```json
{
  "user1": ["/api/videos/user1/sample1.mp4", "/api/videos/user1/sample2.mp4"],
  "user2": ["/api/videos/user2/video1.mp4"]
}
```

---

### 3. Get Videos for a Specific User

**GET** `/api/users/<user_id>/videos`

**Example**:

```
GET /api/users/user1/videos
```

**Response**:

```json
{
  "user": "user1",
  "videos": ["/api/videos/user1/sample1.mp4", "/api/videos/user1/sample2.mp4"]
}
```

---

### 4. Delete a Specific Video

**DELETE** `/api/videos/<user_id>/<video_name>`

**Example**:

```
DELETE /api/videos/user1/sample1.mp4
```

**Response**:

```json
{
  "message": "Deleted video sample1.mp4 for user user1"
}
```

---

### 5. Delete All Videos for a User

**DELETE** `/api/users/<user_id>/videos`

**Response**:

```json
{
  "message": "Deleted 2 videos for user user1",
  "deleted_files": ["sample1.mp4", "sample2.mp4"]
}
```

---

### 6. Check if Video Exists

**GET** `/api/video_exists?video_url=/api/videos/user1/sample1.mp4`

**Response**:

```json
{
  "exists": true
}
```

---

### 7. Search Videos by Filename

**GET** `/api/search_videos?q=sample`

**Response**:

```json
{
  "user1": ["/api/videos/user1/sample1.mp4", "/api/videos/user1/sample2.mp4"]
}
```

---

### 8. List All Users

**GET** `/api/list_users`

**Response**:

```json
["user1", "user2"]
```

---

### 9. Serve Video

**GET** `/api/videos/<path:filename>`

**Example**:

```
GET /api/videos/user1/sample1.mp4
```

* Directly plays or downloads the video in browser.

---

## Notes

* Videos are organized in `processed_videos/<user_id>/`.
* Make sure the `processed_videos` folder exists and is writable.
* `video_processor.py` handles annotation and reporting logic.

---

## Dependencies

* Flask
* Flask-CORS
* python-dotenv
* OpenCV (cv2)
* Other dependencies as required by `video_processor.py`

---

## License

MIT License
