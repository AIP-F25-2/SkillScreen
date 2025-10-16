# Resume Upload Feature

## Overview
This feature allows users to upload resume files (PDF, DOC, DOCX, ZIP) and automatically extract email addresses and candidate names from the documents.

## API Endpoint

### POST `/interview/resumes/upload`

**Description**: Upload single or multiple resume files for processing

**Request**:
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: `files` (array of files)

**Supported File Types**:
- PDF files (`.pdf`)
- Word documents (`.doc`, `.docx`)
- ZIP archives containing multiple resumes

**File Limits**:
- Maximum file size: 10MB per file
- Maximum ZIP size: 50MB
- Maximum files per upload: 10

**Response**:
```json
{
  "success": true,
  "data": {
    "upload_id": "upload_20241201_143022",
    "status": "completed",
    "files_received": 3,
    "files_processed": 3,
    "files": [
      {
        "filename": "john_doe_resume.pdf",
        "url": "/temp/resumes/upload_20241201_143022/john_doe_resume.pdf",
        "size": 245760,
        "status": "processed",
        "extracted_emails": ["john.doe@email.com"],
        "extracted_name": "John Doe",
        "email_count": 1
      }
    ],
    "timestamp": "2024-12-01T14:30:22.123456"
  },
  "meta": {
    "timestamp": "2024-12-01T14:30:22Z",
    "request_id": "req_abc12345",
    "version": "v1"
  }
}
```

## Features

### File Processing
- **PDF Text Extraction**: Extracts text from PDF files using PyPDF2
- **Word Document Processing**: Handles both .doc and .docx files
- **ZIP Archive Support**: Automatically extracts and processes files from ZIP archives
- **File Validation**: Validates file types, sizes, and security

### Email Extraction
- **Email Detection**: Uses regex patterns to find email addresses
- **Email Validation**: Validates email formats using email-validator
- **Duplicate Removal**: Removes duplicate emails while preserving order

### Name Extraction
- **Pattern Matching**: Uses multiple regex patterns to identify candidate names
- **Name Cleaning**: Removes titles (Mr., Ms., Dr.) and normalizes formatting
- **Validation**: Ensures extracted names have at least first and last name

### File Storage
- **Temporary Storage**: Files saved to `temp/resumes/{upload_id}/`
- **URL Generation**: Provides accessible URLs for uploaded files
- **Cleanup**: Automatic cleanup of temporary files

## Database Integration

Currently uses stub functions that log data instead of saving to database:

```python
# Example log output
DB STUB - Would save resume upload:
Upload ID: upload_20241201_143022
Files received: 3
Files data:
  File 1:
    Filename: john_doe_resume.pdf
    URL: /temp/resumes/upload_20241201_143022/john_doe_resume.pdf
    Size: 245760 bytes
    Emails: ['john.doe@email.com']
    Name: John Doe
```

## Error Handling

The service handles various error scenarios:
- Invalid file types
- File size limits exceeded
- Corrupted or encrypted files
- ZIP extraction errors
- Text extraction failures

## Testing

Run the test script to verify functionality:

```bash
# Start the service
uvicorn interview:app --host 0.0.0.0 --port 8080

# In another terminal, run tests
python test_resume_upload.py
```

## Dependencies

The following packages are required:
- `python-multipart`: For file upload handling
- `aiofiles`: For async file operations
- `PyPDF2`: For PDF text extraction
- `python-docx`: For Word document processing
- `email-validator`: For email validation
- `pydantic`: For data validation

## Future Enhancements

When ready to add database persistence:
1. Replace `db_stub.py` functions with actual database operations
2. Add SQLAlchemy models for resume and candidate entities
3. Update service layer to use real repositories
4. The API structure and file processing will remain unchanged

## Security Considerations

- File type validation using magic numbers
- File size limits to prevent abuse
- Path sanitization for uploaded files
- Input validation for extracted data
- Temporary file cleanup
