# User Service CRUD API Endpoints

## Overview
Complete CRUD (Create, Read, Update, Delete) operations for user management with authentication, pagination, search, and filtering capabilities.

## Base URL
`http://localhost:8080`

## Authentication
All endpoints require proper JWT authentication via the API Gateway (except health checks).

## API Endpoints

### Health Check
- **GET** `/` - Service health status
- **GET** `/health` - Detailed health information

### User Management (CRUD Operations)

#### CREATE
- **POST** `/users` - Create a new user
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "is_active": true
  }
  ```

#### READ
- **GET** `/users` - Get all users (with pagination)
  - Query Parameters:
    - `page` (int, default: 1) - Page number
    - `limit` (int, default: 100, max: 1000) - Users per page
    - `is_active` (bool, optional) - Filter by active status

- **GET** `/users/{user_id}` - Get user by ID
- **GET** `/users/email/{email}` - Get user by email address

#### UPDATE
- **PUT** `/users/{user_id}` - Update user by ID
  ```json
  {
    "email": "newemail@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+0987654321",
    "is_active": false
  }
  ```

#### DELETE
- **DELETE** `/users/{user_id}` - Soft delete user (set is_active=False)
- **DELETE** `/users/{user_id}/permanent` - Hard delete user (permanent removal)

### Additional Operations

#### Search
- **GET** `/users/search` - Search users by email, first_name, or last_name
  - Query Parameters:
    - `q` (string, required) - Search term
    - `page` (int, default: 1) - Page number
    - `limit` (int, default: 100) - Results per page

#### User Status Management
- **PATCH** `/users/{user_id}/activate` - Activate user
- **PATCH** `/users/{user_id}/deactivate` - Deactivate user

#### Authentication
- **POST** `/users/authenticate` - Authenticate user with email/password
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```

## Response Format

All responses follow this standardized format:

```json
{
  "success": true,
  "data": {
    // Response data here
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00.000Z",
    "request_id": "req_abc12345",
    "version": "v1"
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "User with email user@example.com already exists"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid credentials"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to create user"
}
```

## Data Models

### User Schema
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00.000Z",
  "updated_at": "2024-01-01T00:00:00.000Z"
}
```

### Pagination Response
```json
{
  "users": [...],
  "total": 150,
  "page": 1,
  "limit": 100,
  "has_next": true,
  "has_prev": false
}
```

## Features Implemented

✅ **Complete CRUD Operations**
✅ **Pagination Support**
✅ **Search Functionality**
✅ **User Authentication**
✅ **Soft Delete (is_active flag)**
✅ **Hard Delete (permanent removal)**
✅ **User Activation/Deactivation**
✅ **Email Validation**
✅ **Password Hashing**
✅ **Comprehensive Error Handling**
✅ **Input Validation**
✅ **Standardized Response Format**

## Security Features

- Password hashing with salt
- Email uniqueness validation
- Input sanitization
- Proper error handling
- JWT token validation (via API Gateway)
