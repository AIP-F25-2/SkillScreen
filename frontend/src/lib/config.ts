/**
 * Centralized configuration for API endpoints
 * All environment variables should be accessed through this file
 */

// API Base URL - Gateway endpoint
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001';

// Media Service URL (if different from gateway)
export const MEDIA_SERVICE_URL = process.env.NEXT_PUBLIC_MEDIA_SERVICE_URL || API_BASE_URL;

// Frontend URL (for email links, etc.)
export const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || 'http://localhost:3000';

// Other configuration
export const IS_PRODUCTION = process.env.NODE_ENV === 'production';
export const IS_DEVELOPMENT = process.env.NODE_ENV === 'development';

// API Endpoints
export const API_ENDPOINTS = {
  // Auth
  AUTH_LOGIN: '/auth/login',
  AUTH_HEALTH: '/auth/health',
  
  // User
  USER_USERS: '/user/users',
  USER_HEALTH: '/user/health',
  
  // Media
  MEDIA_RESET_CHUNKS: '/media/reset_chunks',
  MEDIA_UPLOAD_CHUNK: '/media/upload_chunk',
  MEDIA_FINALIZE_UPLOAD: '/media/finalize_upload',
  MEDIA_VIDEO: '/media/video',
  MEDIA_INTERVIEWS: '/media/api/interviews',
  MEDIA_CANDIDATES: '/media/api/candidates',
  MEDIA_RESUMES_UPLOAD: '/media/api/resumes/upload',
  
  // Interview
  INTERVIEW_SESSION_CREATE: '/interview/api/session/create',
  INTERVIEW_SESSION: '/interview/api/session',
  INTERVIEW_TOKEN_VALIDATE: '/interview/api/token/validate',
  INTERVIEW_TOKEN_STORE: '/interview/api/token/store',
  INTERVIEW_EMAIL_SEND_INVITATION: '/interview/api/email/send-invitation',
  INTERVIEW_EMAIL_SEND_COMPLETION: '/interview/api/email/send-completion-notification',
  
  // Audio AI
  AUDIO_AI_PROCESS: '/audio-ai/api/v1/audio/process',
  AUDIO_AI_TRANSCRIBE: '/audio-ai/api/audio/transcribe',
  AUDIO_AI_RESULTS: '/audio-ai/api/v1/audio/results',
  
  // AI Logic
  TEXT_SERVICE_RESUMES_PARSE: '/text-service/resumes/parse',
  TEXT_SERVICE_CANDIDATES: '/text-service/candidates',
  TEXT_SERVICE_JOBS: '/text-service/jobs',
  TEXT_SERVICE_INTERVIEWS_START: '/text-service/interviews/start',
  TEXT_SERVICE_INTERVIEWS_QUESTIONS: '/text-service/interviews',
  
  // Assessment
  ASSESSMENT_QUESTIONS: '/assessment/questions',
  ASSESSMENT_SUBMIT: '/assessment/submit',
  
  // Coding
  CODING_PROBLEMS: '/coding/problems',
  CODING_SUBMIT: '/coding/submit',
} as const;

export default {
  API_BASE_URL,
  MEDIA_SERVICE_URL,
  FRONTEND_URL,
  IS_PRODUCTION,
  IS_DEVELOPMENT,
  API_ENDPOINTS,
};

