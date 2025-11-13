# Interview Service

Simple Interview Service for deployment testing and health monitoring.

## Features
- ✅ Simple deployment check endpoint
- ✅ Environment variable configuration
- ✅ Docker containerization
- ✅ Port configuration from .env file
- ✅ Preserved directory structure with .gitkeep files

## Quick Start

### Docker Deployment
```bash
# Build the image
docker build -t interview-service .

# Run with environment file
docker run -d --name interview-service-container -p 5003:5003 --env-file .env interview-service

# Test the service
curl http://localhost:5003
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py
```

## API Endpoints

### Health Check Endpoints
- `GET /` - Service status and deployment check
- `GET /health` - Detailed health check
- `GET /resumes/health` - Resume service health check

### Resume Upload Endpoint
- `POST /resumes/upload` - Upload resume files for processing

## Resume Upload API Documentation

### Endpoint
```
POST /resumes/upload
```

### Request Format
**Content-Type:** `multipart/form-data`

**Required Fields:**
- `files`: Array of resume files (PDF, DOC, DOCX, ZIP)
- `organization_id`: Organization UUID (string)

### Frontend Implementation Examples

#### JavaScript (Fetch API)
```javascript
const formData = new FormData();

// Add files
const fileInput = document.getElementById('fileInput');
for (let file of fileInput.files) {
    formData.append('files', file);
}

// Add organization ID
formData.append('organization_id', '21cfc4a5-136f-4bd8-9ec1-5778c78cded2');

// Send request
fetch('http://localhost:5000/interview/resumes/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

#### JavaScript (Axios)
```javascript
const formData = new FormData();

// Add files
const fileInput = document.getElementById('fileInput');
for (let file of fileInput.files) {
    formData.append('files', file);
}

// Add organization ID
formData.append('organization_id', '21cfc4a5-136f-4bd8-9ec1-5778c78cded2');

axios.post('http://localhost:5000/interview/resumes/upload', formData, {
    headers: {
        'Content-Type': 'multipart/form-data'
    }
})
.then(response => console.log(response.data))
.catch(error => console.error('Error:', error));
```

#### React Example
```jsx
import React, { useState } from 'react';

function ResumeUpload() {
    const [files, setFiles] = useState([]);
    const [organizationId, setOrganizationId] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        const formData = new FormData();
        
        // Add files
        files.forEach(file => {
            formData.append('files', file);
        });
        
        // Add organization ID
        formData.append('organization_id', organizationId);
        
        try {
            const response = await fetch('http://localhost:5000/interview/resumes/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            console.log('Upload result:', result);
        } catch (error) {
            console.error('Upload error:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input 
                type="file" 
                multiple 
                onChange={(e) => setFiles(Array.from(e.target.files))}
            />
            <input 
                type="text" 
                placeholder="Organization ID"
                value={organizationId}
                onChange={(e) => setOrganizationId(e.target.value)}
            />
            <button type="submit">Upload Resumes</button>
        </form>
    );
}
```

### Postman Configuration
1. **Method:** POST
2. **URL:** `http://localhost:5000/interview/resumes/upload`
3. **Body Type:** `form-data`
4. **Fields:**
   - `files`: Select PDF/DOC/DOCX files
   - `organization_id`: Enter organization UUID

### Request Validation
- **Files:** Maximum 10 files per upload
- **File Types:** PDF, DOC, DOCX, ZIP
- **Organization ID:** Must be a valid UUID that exists in the organizations table

### Response Format
```json
{
    "success": true,
    "data": {
        "upload_id": "upload_20251024_130141",
        "status": "completed",
        "files_received": 2,
        "files_processed": 2,
        "candidates_saved": 2,
        "files": [
            {
                "filename": "resume1.pdf",
                "url": "/temp/resumes/upload_20251024_130141/resume1.pdf",
                "size": 1024,
                "status": "processed",
                "extracted_emails": ["john@example.com"],
                "extracted_name": "John Doe",
                "email_count": 1,
                "id": "candidate-uuid-here"
            }
        ],
        "timestamp": "2025-01-24T13:01:41.123456"
    },
    "error": null,
    "meta": {
        "timestamp": "2025-01-24T13:01:41.123456Z",
        "request_id": "req_abc12345",
        "version": "v1"
    }
}
```

### Error Responses
```json
{
    "success": false,
    "data": null,
    "error": "No files provided",
    "meta": {
        "timestamp": "2025-01-24T13:01:41.123456Z",
        "request_id": "req_abc12345",
        "version": "v1"
    }
}
```

### Common Error Codes
- **400 Bad Request:** Missing files or organization_id
- **400 Bad Request:** Too many files (max 10)
- **500 Internal Server Error:** Database or processing errors

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=5003
FLASK_ENV=production
```

## Docker Commands

```bash
# Stop and remove container
docker stop interview-service-container
docker rm interview-service-container

# Rebuild and redeploy
docker build -t interview-service .
docker run -d --name interview-service-container -p 5003:5003 --env-file .env interview-service

# View logs
docker logs -f interview-service-container
```

## Files Structure
```
interview-service/
├── app.py              # Main Flask application (22 lines)
├── Dockerfile          # Docker configuration
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Environment file
├── src/                # Source directories (preserved with .gitkeep)
│   ├── controllers/
│   ├── middleware/
│   ├── routes/
│   ├── services/
│   └── utils/
├── tests/              # Test directories (preserved with .gitkeep)
│   ├── integration/
│   └── unit/
└── README.md          # This file
```