# Direct Video Upload Test

## Endpoint
```
POST /api/upload/video
```

## Test Flow

### Step 1: Create dummy video file
```bash
# Create a small test video file (200 bytes of garbage data)
dd if=/dev/zero bs=1 count=200 of=test_video.webm
```

On Windows (PowerShell):
```powershell
$bytes = [byte[]]::new(200)
[System.IO.File]::WriteAllBytes("test_video.webm", $bytes)
```

### Step 2: Upload video
```bash
curl -X POST http://localhost:5001/media/upload/video \
  -F "interview_id=550e8400-e29b-41d4-a716-446655440001" \
  -F "session_id=550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@test_video.webm"
```

### Step 3: Expected Response
```json
{
  "success": true,
  "data": {
    "file_id": "some-uuid",
    "interview_id": "550e8400-e29b-41d4-a716-446655440001",
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "storage_uri": "https://skillscreenstorage00.blob.core.windows.net/video-recordings/videos/550e8400-e29b-41d4-a716-446655440001/550e8400_abcdef12_response.webm",
    "file_size": 200,
    "checksum": "sha256_hash_here",
    "blob_name": "550e8400_abcdef12_response.webm",
    "status": "completed"
  }
}
```

### Step 4: Verify in Database
```sql
SELECT * FROM media_files
WHERE interview_id = '550e8400-e29b-41d4-a716-446655440001'
  AND file_type = 'video_response';
```

Should see:
- `storage_uri`: Full URL to video in Azure
- `file_size`: 200
- `checksum`: SHA256 hash
- `blob_name`: Generated filename
- `status`: completed

## Integration with Interview Flow

After candidate answers a question:

1. **Frontend records video** →
2. **Frontend calls POST /api/upload/video** with:
   - interview_id (from interview_sessions table)
   - session_id (from interview_sessions table)
   - video file
3. **Response contains storage_uri** →
4. **Frontend submits candidate_response** with storage_uri →
5. **Backend transcribes** video using storage_uri →
6. **Backend continues interview**

## What Gets Stored

In `media_files` table:
```
id:             Auto UUID
interview_id:   From request
session_id:     From metadata (in interviews, not media_files directly)
file_type:      'video_response'
blob_name:      550e8400_abcdef12_response.webm
storage_uri:    Azure blob URL
file_size:      200
checksum:       SHA256
status:         'completed'
mime_type:      'video/webm'
metadata:       {session_id, uploaded_at, filename, checksum}
created_at:     NOW()
```

## Notes

- Handles video files up to 500MB (configurable in MAX_CONTENT_LENGTH_BYTES)
- Automatically calculates checksum for integrity verification
- Stores to Azure Blob Storage using SAS token auth
- All UUIDs validated before use
- Safe filename generation prevents path traversal
