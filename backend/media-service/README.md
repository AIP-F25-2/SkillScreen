# Flask Chunked Video Upload & Management API

A Flask-based server for **chunked video uploads**, **video merging**, and **user/video management**.  
Supports storing videos per user, previewing, converting `.webm` chunks to `.mp4`, and admin-level operations.

---

## Features

- Upload video chunks (`.webm`) for a specific user.
- Reset/delete uploaded chunks before finalizing.
- Merge chunks into a single `.webm` file and convert to `.mp4` using **FFmpeg**.
- Serve videos for preview/download.
- Admin endpoints for:
  - Listing all users and their videos.
  - Searching users and videos.
  - Deleting single/all videos or users.
  - Creating, renaming, or deleting users.

---

## Tech Stack

- **Backend:** Python 3, Flask
- **Video Processing:** FFmpeg
- **Environment Management:** python-dotenv
- **File Storage:** Local filesystem (per-user directories)

---

## Installation

1. **Clone the repo**
```bash
git clone <repo-url>
cd <repo-folder>
````

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Install FFmpeg**

   * Linux: `sudo apt install ffmpeg`
   * Mac: `brew install ffmpeg`
   * Windows: [Download FFmpeg](https://ffmpeg.org/download.html) and add to PATH

5. **Create a `.env` file**

```ini
UPLOAD_FOLDER=uploads
SERVER_HOST=0.0.0.0
SERVER_PORT=5004
# Optional SSL for HTTPS testing
# SSL_CERT=cert.pem
# SSL_KEY=key.pem
```

6. **Create uploads folder (optional)**

```bash
mkdir -p uploads
```

---

## Running the Server

```bash
python app.py
```

Server will run on `http://<SERVER_HOST>:<SERVER_PORT>` (default: `0.0.0.0:5004`)

> For HTTPS testing, uncomment the `ssl_context` line in `app.py` and provide `cert.pem` and `key.pem`.

---

## API Endpoints

### Video Upload

| Method | Endpoint           | Description                                                                |
| ------ | ------------------ | -------------------------------------------------------------------------- |
| POST   | `/upload_chunk`    | Upload a video chunk for a user. Requires `file` and `user_id`.            |
| POST   | `/reset_chunks`    | Delete all `.webm` chunks for a user. Requires JSON `{"user_id": "user1"}` |
| POST   | `/finalize_upload` | Merge chunks into `.webm` and convert to `.mp4`. Returns video URL.        |

### Video Serving

| Method | Endpoint                      | Description                               |
| ------ | ----------------------------- | ----------------------------------------- |
| GET    | `/video/<user_id>/<filename>` | Serve a video file for playback/download. |

### Admin Video Management

| Method | Endpoint                                    | Description                           |
| ------ | ------------------------------------------- | ------------------------------------- |
| GET    | `/admin/videos`                             | List all users and their videos.      |
| GET    | `/admin/videos/<user_id>`                   | List all videos of a specific user.   |
| DELETE | `/admin/video/<user_id>/<filename>`         | Delete a specific video.              |
| DELETE | `/admin/videos/<user_id>`                   | Delete all videos of a specific user. |
| DELETE | `/admin/videos`                             | Delete all videos of all users.       |
| GET    | `/admin/video/<user_id>/preview/<filename>` | Preview a video without downloading.  |
| GET    | `/admin/search/users?q=<query>`             | Search users by name.                 |
| GET    | `/admin/search/videos?q=<query>`            | Search videos by filename.            |

### Admin User Management

| Method | Endpoint                | Description                                      |
| ------ | ----------------------- | ------------------------------------------------ |
| POST   | `/admin/user`           | Create a new user. JSON `{"user_id": "user1"}`   |
| GET    | `/admin/users`          | List all users.                                  |
| GET    | `/admin/user/<user_id>` | Get a user and their videos.                     |
| PUT    | `/admin/user/<user_id>` | Rename a user. JSON `{"new_user_id": "newname"}` |
| DELETE | `/admin/user/<user_id>` | Delete a user and their videos.                  |
| DELETE | `/admin/users`          | Delete all users and all data.                   |

---

## Workflow Diagram

```text
User uploads chunks (.webm)
         |
         v
  /upload_chunk
         |
         v
Chunks stored in per-user folder
         |
         v
 /reset_chunks (optional)
         |
         v
 /finalize_upload
         |
         v
Chunks merged → merged.webm → converted → final .mp4
         |
         v
  Video stored in user folder
         |
         v
Admin can preview, search, or delete videos/users
```

---

## Notes

* **Video format:** Upload chunks in `.webm`. Final video is `.mp4`.
* **FFmpeg:** Required for chunk merging and conversion.
* **File cleanup:** Old chunks and merged intermediate files are deleted after finalization.
* **Self-signed SSL (for testing):**

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem -subj "/CN=localhost"
```

---

## Project Structure

```
.
├── app.py
├── services/
│   └── video_processor.py  # Optional processing logic
├── uploads/               # Stored per-user video folders
├── .env
├── requirements.txt
└── README.md
```

---

## License

MIT License

