# Environment Variable Configuration Guide

## Overview

This document outlines all environment variables used across the SkillScreen platform. All API calls now use centralized configuration to make deployment easier.

## Frontend Environment Variables

### Location: `frontend/.env.local`

```bash
# API Gateway URL (Main Backend)
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001

# Frontend URL (for email links)
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000

# Optional: Media Service URL (if separate from gateway)
# NEXT_PUBLIC_MEDIA_SERVICE_URL=http://localhost:8080
```

### Usage

All API calls in the frontend now import from `@/lib/config`:

```typescript
import { API_BASE_URL } from '@/lib/config';

// Use in fetch calls
const response = await fetch(`${API_BASE_URL}/api/endpoint`);
```

### Files Updated

- ✅ `frontend/src/lib/config.ts` - Centralized configuration
- ✅ `frontend/src/lib/api.ts` - API client
- ✅ `frontend/src/lib/interviewToken.ts` - Token validation
- ✅ `frontend/src/components/ModernInterviewScreen.tsx` - Interview recording
- ✅ `frontend/src/app/interview-summary/page.tsx` - Video playback

## Backend Environment Variables

### Interview Service: `backend/interview-service/.env`

```bash
# Resend Email Configuration
RESEND_API_KEY=re_your_api_key_here
FROM_EMAIL=interviews@skillscreen.io

# URLs
FRONTEND_URL=http://localhost:3000
API_BASE_URL=http://localhost:5001
```

### Other Services

Each service should have its own `.env` file with service-specific configuration.

## Environment Profiles

### Development

```bash
# Frontend
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000

# Backend
FRONTEND_URL=http://localhost:3000
API_BASE_URL=http://localhost:5001
```

### Staging

```bash
# Frontend
NEXT_PUBLIC_API_BASE_URL=https://api-staging.yourdomain.com
NEXT_PUBLIC_FRONTEND_URL=https://staging.yourdomain.com

# Backend
FRONTEND_URL=https://staging.yourdomain.com
API_BASE_URL=https://api-staging.yourdomain.com
```

### Production

```bash
# Frontend
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
NEXT_PUBLIC_FRONTEND_URL=https://yourdomain.com

# Backend
FRONTEND_URL=https://yourdomain.com
API_BASE_URL=https://api.yourdomain.com
```

## Docker Configuration

When using Docker Compose, environment variables are passed through the compose file:

```yaml
frontend:
  environment:
    - NEXT_PUBLIC_API_BASE_URL=http://api-gateway:5001
    - NEXT_PUBLIC_FRONTEND_URL=http://localhost:3000

interview-service:
  environment:
    - FRONTEND_URL=http://frontend:3000
    - API_BASE_URL=http://api-gateway:5001
    - RESEND_API_KEY=${RESEND_API_KEY}
```

## Security Best Practices

### 1. Never Commit `.env` Files

`.env` and `.env.local` are in `.gitignore`. Always use `.env.example` for documentation.

### 2. Use Different Keys per Environment

```bash
# Development
RESEND_API_KEY=re_dev_key_here

# Production
RESEND_API_KEY=re_prod_key_here
```

### 3. Prefix Frontend Variables

Next.js requires `NEXT_PUBLIC_` prefix for browser-accessible variables:

```bash
# ✅ Accessible in browser
NEXT_PUBLIC_API_BASE_URL=http://localhost:5001

# ❌ Not accessible in browser (server-side only)
API_SECRET_KEY=secret123
```

### 4. Validate on Startup

The config file exports constants that fail fast if not set:

```typescript
// config.ts validates required variables
export const API_BASE_URL = 
  process.env.NEXT_PUBLIC_API_BASE_URL || 
  'http://localhost:5001';
```

## Troubleshooting

### Frontend not connecting to backend

1. Check `NEXT_PUBLIC_API_BASE_URL` is set correctly
2. Verify backend is running on the specified port
3. Check for CORS issues if on different domains

### Email links pointing to wrong URL

1. Verify `FRONTEND_URL` in backend `.env`
2. Ensure it matches where your frontend is deployed
3. Check email templates use the correct variable

### Changes not taking effect

1. Restart the development server after changing `.env.local`
2. Clear Next.js cache: `rm -rf .next`
3. For Docker: rebuild with `docker-compose build`

## Quick Setup

### Development Setup

```bash
# Frontend
cd frontend
cp .env.example .env.local
# Edit .env.local with your values
npm run dev

# Backend (Interview Service)
cd backend/interview-service
cp .env.example .env
# Add your Resend API key
pip install -r requirements.txt
uvicorn interview:app --reload --port 8003
```

### Production Deployment

1. Set environment variables in your hosting platform:
   - Vercel: Project Settings → Environment Variables
   - Docker: Use `docker-compose.prod.yml` with env files
   - Traditional: Export variables in server startup script

2. Update URLs to production domains:
   ```bash
   NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
   NEXT_PUBLIC_FRONTEND_URL=https://yourdomain.com
   ```

3. Test all endpoints after deployment

## API Endpoints Reference

All endpoints are defined in `frontend/src/lib/config.ts`:

```typescript
export const API_ENDPOINTS = {
  // Auth
  AUTH_LOGIN: '/auth/login',
  
  // Media
  MEDIA_UPLOAD_CHUNK: '/media/upload_chunk',
  MEDIA_FINALIZE_UPLOAD: '/media/finalize_upload',
  
  // Interview
  INTERVIEW_SESSION_CREATE: '/interview/api/session/create',
  INTERVIEW_TOKEN_VALIDATE: '/interview/api/token/validate',
  INTERVIEW_EMAIL_SEND_INVITATION: '/interview/api/email/send-invitation',
  
  // ... and more
}
```

## Migration from Hardcoded URLs

All hardcoded URLs have been replaced with environment variables:

**Before:**
```typescript
const response = await fetch('http://localhost:5001/api/endpoint');
```

**After:**
```typescript
import { API_BASE_URL } from '@/lib/config';
const response = await fetch(`${API_BASE_URL}/api/endpoint`);
```

## Additional Resources

- Next.js Environment Variables: https://nextjs.org/docs/basic-features/environment-variables
- Docker Environment Variables: https://docs.docker.com/compose/environment-variables/
- Resend API Keys: https://resend.com/api-keys

