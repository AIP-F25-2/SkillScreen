// Interview token management for email-based candidate access
import { API_BASE_URL } from './config';

// Use direct interview service URL for token validation
const INTERVIEW_SERVICE_URL = 'http://localhost:8003';

export interface InterviewToken {
  token: string;
  candidateId: string;
  candidateName: string;
  candidateEmail: string;
  sessionId: string;
  interviewId: string;  // Add interview ID for proper integration
  expiresAt: string;
  usedAt?: string;
}

const TOKEN_STORAGE_KEY = 'interview_token_data';

/**
 * Store interview token data in sessionStorage (not localStorage to prevent reuse)
 */
export function storeInterviewToken(tokenData: InterviewToken): void {
  if (typeof window === 'undefined') return;
  
  try {
    sessionStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokenData));
  } catch (error) {
    console.error('Failed to store interview token:', error);
  }
}

/**
 * Get stored interview token data
 */
export function getInterviewToken(): InterviewToken | null {
  if (typeof window === 'undefined') return null;
  
  try {
    const stored = sessionStorage.getItem(TOKEN_STORAGE_KEY);
    if (!stored) return null;
    
    const tokenData = JSON.parse(stored) as InterviewToken;
    
    // Check if token is expired
    if (new Date(tokenData.expiresAt) < new Date()) {
      clearInterviewToken();
      return null;
    }
    
    return tokenData;
  } catch (error) {
    console.error('Failed to get interview token:', error);
    return null;
  }
}

/**
 * Clear interview token data
 */
export function clearInterviewToken(): void {
  if (typeof window === 'undefined') return;
  
  try {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear interview token:', error);
  }
}

/**
 * Mark token as used
 */
export function markTokenAsUsed(): void {
  const tokenData = getInterviewToken();
  if (!tokenData) return;
  
  tokenData.usedAt = new Date().toISOString();
  storeInterviewToken(tokenData);
}

/**
 * Validate interview token with backend
 */
export async function validateInterviewToken(token: string): Promise<{
  valid: boolean;
  data?: InterviewToken;
  error?: string;
}> {
  try {
    const response = await fetch(`${INTERVIEW_SERVICE_URL}/api/token/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token }),
    });

    const result = await response.json();

    if (!response.ok) {
      return {
        valid: false,
        error: result.error || 'Invalid or expired token',
      };
    }

    return {
      valid: true,
      data: result.data,
    };
  } catch (error) {
    console.error('Token validation failed:', error);
    return {
      valid: false,
      error: 'Failed to validate token. Please check your connection.',
    };
  }
}

