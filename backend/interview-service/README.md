# Interview Service

API service for managing interviews, resumes, and job positions.

## Features
- ✅ Resume upload and processing
- ✅ Job position management (CRUD)
- ✅ Email extraction from resumes
- ✅ Candidate database management
- ✅ Docker containerization
- ✅ API Gateway integration

## Quick Start

### Docker Deployment
```bash
# Build the image
docker build -t interview-service .

# Run with environment file
docker run -d --name interview-service-container -p 8003:8003 --env-file .env interview-service
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn interview:app --host 0.0.0.0 --port 8003 --reload
```

---

## API Endpoints Overview

### Base URL
All requests go through the API Gateway:
```
http://localhost:5001/interview
```

### Health Check Endpoints
- `GET /` - Service status and deployment check
- `GET /health` - Detailed health check
- `GET /resumes/health` - Resume service health check
- `GET /job-positions/health` - Job positions service health check

### Resume Endpoints
- `POST /resumes/upload` - Upload resume files for processing

### Job Position Endpoints
- `POST /job-positions` - Create a new job position
- `GET /job-positions/{id}` - Get a specific job position by ID
- `GET /job-positions` - List all job positions (with filters)
- `PUT /job-positions/{id}` - Update a job position
- `PATCH /job-positions/{id}` - Partially update a job position
- `DELETE /job-positions/{id}` - Soft delete a job position

---

## Resume Upload API

### Upload Resume Files

**Endpoint:** `POST /resumes/upload`

**Content-Type:** `multipart/form-data`

**Request Parameters:**
- `files` (required): Array of resume files (PDF, DOC, DOCX, ZIP)
- `organization_id` (required): Organization UUID (string)

**Validation Rules:**
- Maximum 10 files per upload
- Supported file types: PDF, DOC, DOCX, ZIP
- Organization ID must exist in the database

**Success Response:**
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

**Error Response:**
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

**Error Codes:**
- `400` - Missing files or organization_id
- `400` - Too many files (max 10)
- `500` - Database or processing errors

---

## Job Positions API

### Authentication
All job position endpoints require JWT authentication:
```
Authorization: Bearer {your_jwt_token}
```

---

### 1. Create Job Position

**Endpoint:** `POST /job-positions`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "organization_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Senior Software Engineer",
  "description": "We are looking for an experienced Senior Software Engineer...",
  "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "department": "Engineering",
  "is_active": true,
  "created_by": "123e4567-e89b-12d3-a456-426614174001"
}
```

**Required Fields:**
- `organization_id` (string, UUID): Organization identifier
- `title` (string): Job title

**Optional Fields:**
- `description` (string): Job description
- `required_skills` (array of strings): List of required skills
- `department` (string): Department name
- `is_active` (boolean, default: true): Whether position is active
- `created_by` (string, UUID): User ID who created the position

**Success Response:**
```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "organization_id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Senior Software Engineer",
    "description": "We are looking for...",
    "required_skills": ["Python", "FastAPI"],
    "department": "Engineering",
    "is_active": true,
    "created_by": "123e4567-e89b-12d3-a456-426614174001",
    "created_at": "2025-11-16T10:30:00.000000+00:00",
    "updated_at": "2025-11-16T10:30:00.000000+00:00",
    "deleted_at": null
  },
  "error": null,
  "meta": {
    "timestamp": "2025-11-16T10:30:00.000000Z",
    "request_id": "req_abc12345",
    "version": "v1"
  }
}
```

---

### 2. Get Job Position by ID

**Endpoint:** `GET /job-positions/{job_position_id}`

**URL Parameters:**
- `job_position_id` (required): UUID of the job position

**Example:** `GET /job-positions/a1b2c3d4-e5f6-7890-abcd-ef1234567890`

**Success Response:**
```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "organization_id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Senior Software Engineer",
    "description": "Job description",
    "required_skills": ["Python", "FastAPI"],
    "department": "Engineering",
    "is_active": true,
    "created_by": "123e4567-e89b-12d3-a456-426614174001",
    "created_at": "2025-11-16T10:30:00.000000+00:00",
    "updated_at": "2025-11-16T10:30:00.000000+00:00",
    "deleted_at": null
  },
  "error": null,
  "meta": { ... }
}
```

---

### 3. List Job Positions

**Endpoint:** `GET /job-positions`

**Query Parameters:**
- `organization_id` (required, string UUID): Organization to filter by
- `limit` (optional, number, default: 100): Maximum number of results (1-1000)
- `offset` (optional, number, default: 0): Number of results to skip for pagination
- `is_active` (optional, boolean): Filter by active/inactive status

**Example:** `GET /job-positions?organization_id=123e4567-e89b-12d3-a456-426614174000&limit=10&offset=0&is_active=true`

**Success Response:**
```json
{
  "success": true,
  "data": {
    "job_positions": [
      {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "title": "Senior Software Engineer",
        "department": "Engineering",
        "is_active": true,
        ...
      },
      {
        "id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
        "title": "Product Manager",
        "department": "Product",
        "is_active": true,
        ...
      }
    ],
    "total": 25,
    "limit": 10,
    "offset": 0
  },
  "error": null,
  "meta": { ... }
}
```

---

### 4. Update Job Position

**Endpoint:** `PUT /job-positions/{job_position_id}`

**Content-Type:** `application/json`

**URL Parameters:**
- `job_position_id` (required): UUID of the job position

**Request Body (all fields optional):**
```json
{
  "title": "Lead Software Engineer",
  "description": "Updated description",
  "required_skills": ["Python", "FastAPI", "Kubernetes"],
  "department": "Engineering - Backend",
  "is_active": false
}
```

**Example:** `PUT /job-positions/a1b2c3d4-e5f6-7890-abcd-ef1234567890`

**Success Response:**
```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "title": "Lead Software Engineer",
    "updated_at": "2025-11-16T11:00:00.000000+00:00",
    ...
  },
  "error": null,
  "meta": { ... }
}
```

---

### 5. Partial Update Job Position

**Endpoint:** `PATCH /job-positions/{job_position_id}`

**Content-Type:** `application/json`

**URL Parameters:**
- `job_position_id` (required): UUID of the job position

**Request Body (update only specific fields):**
```json
{
  "is_active": false
}
```

**Note:** PATCH works the same as PUT - both allow partial updates.

---

### 6. Delete Job Position

**Endpoint:** `DELETE /job-positions/{job_position_id}`

**URL Parameters:**
- `job_position_id` (required): UUID of the job position

**Example:** `DELETE /job-positions/a1b2c3d4-e5f6-7890-abcd-ef1234567890`

**Success Response:**
```json
{
  "success": true,
  "data": {
    "message": "Job position deleted successfully"
  },
  "error": null,
  "meta": { ... }
}
```

**Note:** This is a soft delete - the record is not removed from the database. The `deleted_at` timestamp is set, and deleted positions won't appear in list/get queries.

---

### Error Responses

**400 Bad Request - Validation Error:**
```json
{
  "success": false,
  "data": null,
  "error": "organization_id is required",
  "meta": { ... }
}
```

**404 Not Found:**
```json
{
  "success": false,
  "data": null,
  "error": "Job position not found",
  "meta": { ... }
}
```

**500 Internal Server Error:**
```json
{
  "success": false,
  "data": null,
  "error": "Database error: ...",
  "meta": { ... }
}
```

---

## Important Notes

### Authentication
- All job position endpoints require a valid JWT token in the Authorization header
- Resume upload endpoints do not require authentication

### API Gateway
- All requests must go through the API gateway at `http://localhost:5001/interview/`
- Direct service access is available at `http://localhost:8003` for testing only

### Data Requirements
- **UUID Format:** All IDs (organization_id, job_position_id, created_by) must be valid UUIDs
- **Organization ID:** Must reference an existing organization in the database
- **Soft Delete:** Deleted job positions are not permanently removed - they have a `deleted_at` timestamp
- **Pagination:** Use `limit` and `offset` query parameters for pagination in the list endpoint
- **Filtering:** Use `is_active` query parameter to filter active/inactive positions

---

## Environment Configuration

The service reads configuration from `.env` file:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file to customize settings
PORT=8003
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

## Docker Commands

```bash
# Stop and remove container
docker stop interview-service-container
docker rm interview-service-container

# Rebuild and redeploy
docker build -t interview-service .
docker run -d --name interview-service-container -p 8003:8003 --env-file .env interview-service

# View logs
docker logs -f interview-service-container
```

## Files Structure
```
interview-service/
├── interview.py           # Main FastAPI application
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
├── models/                # Database models
│   ├── candidate.py
│   └── job_position.py
├── schemas/               # Pydantic validation schemas
│   ├── resume_schemas.py
│   └── job_position_schemas.py
├── repository/            # Database operations layer
│   ├── candidate_repository.py
│   └── job_position_repository.py
├── services/              # Business logic layer
│   ├── candidate_service.py
│   ├── job_position_service.py
│   ├── resume_service.py
│   └── email_service.py
├── controllers/           # API endpoints
│   ├── resume_controller.py
│   └── job_position_controller.py
└── temp/                  # Temporary file storage
```
