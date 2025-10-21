// Use environment variable for API base URL, fallback to localhost for development
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001';

export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  meta: {
    timestamp: string;
    request_id: string;
    version: string;
  };
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  role: string;
  expires_in: number;
}

export interface User {
  id: number;
  name: string;
  email: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Add Authorization header if token exists
    const token = this.getToken();
    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    try {
      const stored = window.localStorage.getItem('intervuai_auth_token');
      if (!stored) return null;
      const parsed = JSON.parse(stored);
      return parsed.token || null;
    } catch {
      return null;
    }
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    return this.request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async getAuthHealth(): Promise<ApiResponse> {
    return this.request('/auth/health');
  }

  // User endpoints
  async getUsers(): Promise<ApiResponse<{ users: User[] }>> {
    return this.request<{ users: User[] }>('/user/users');
  }

  async getUserById(id: number): Promise<ApiResponse<{ user: User }>> {
    return this.request<{ user: User }>(`/user/users/${id}`);
  }

  async getUserHealth(): Promise<ApiResponse> {
    return this.request('/user/health');
  }

  // Assessment endpoints
  async getQuestions(): Promise<ApiResponse<{ questions: string[] }>> {
    return this.request<{ questions: string[] }>('/assessment/questions');
  }

  async submitAssessment(answer: any): Promise<ApiResponse<{ status: string; answer: any }>> {
    return this.request<{ status: string; answer: any }>('/assessment/submit', {
      method: 'POST',
      body: JSON.stringify(answer),
    });
  }

  // Coding endpoints
  async getProblems(): Promise<ApiResponse<{ problems: string[] }>> {
    return this.request<{ problems: string[] }>('/coding/problems');
  }

  async submitSolution(solution: any): Promise<ApiResponse<{ status: string; solution: any }>> {
    return this.request<{ status: string; solution: any }>('/coding/submit', {
      method: 'POST',
      body: JSON.stringify(solution),
    });
  }

  // Audio-AI endpoints (via gateway -> audio-ai-service)
  async audioProcess(payload: {
    media_url: string;
    session_id?: string;
    candidate_id?: string;
  }): Promise<ApiResponse<any>> {
    // Create abort controller with 10 minute timeout for audio processing
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minutes

    try {
      const result = await this.request<any>('/audio-ai/api/v1/audio/process', {
        method: 'POST',
        body: JSON.stringify({
          media_url: payload.media_url,
          session_id: payload.session_id ?? 'test-session',
          candidate_id: payload.candidate_id ?? 'test-candidate',
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return result;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  async audioTranscribe(payload: {
    media_url: string;
    session_id?: string;
    candidate_id?: string;
  }): Promise<ApiResponse<any>> {
    // Create abort controller with 10 minute timeout for transcription
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 600000); // 10 minutes

    try {
      const result = await this.request<any>('/audio-ai/api/audio/transcribe', {
        method: 'POST',
        body: JSON.stringify({
          media_url: payload.media_url,
          session_id: payload.session_id ?? 'test-session',
          candidate_id: payload.candidate_id ?? 'test-candidate',
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return result;
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  }

  // =========================================
  // Interview Management Methods
  // =========================================

  async getUserInterviews(userId: string): Promise<ApiResponse<{ interviews: any[]; count: number }>> {
    return this.request<{ interviews: any[]; count: number }>(`/media/api/interviews`);
  }

  async getAllInterviews(): Promise<ApiResponse<{ interviews: any[]; count: number }>> {
    return this.request<{ interviews: any[]; count: number }>('/media/api/interviews');
  }

  async getInterviewDetails(interviewId: string): Promise<ApiResponse<any>> {
    if (!interviewId) return Promise.reject(new Error('Interview ID is required'));
    return this.request<any>(`/media/api/interviews/${interviewId}`);
  }

  async updateInterviewTranscript(interviewId: string, transcript: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/media/api/interviews/${interviewId}/transcript`, {
      method: 'POST',
      body: JSON.stringify(transcript),
    });
  }

  async updateInterviewStatus(interviewId: string, status: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/interview/api/session/${interviewId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  // =========================================
  // Candidate/Resume Management Methods
  // =========================================

  async uploadResume(file: File, candidateName?: string): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);
    if (candidateName) {
      formData.append('candidate_name', candidateName);
    }

    const url = `${this.baseUrl}/media/api/resumes/upload`;
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    return response.json();
  }

  async getAllCandidates(): Promise<ApiResponse<{ candidates: any[]; count: number }>> {
    return this.request<{ candidates: any[]; count: number }>('/media/api/candidates');
  }

  async getUserCandidates(userId: string): Promise<ApiResponse<{ candidates: any[]; count: number }>> {
    return this.request<{ candidates: any[]; count: number }>(`/media/api/candidates`);
  }

  async getCandidate(candidateId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/media/api/candidates/${candidateId}`);
  }

  async scheduleCandidate(candidateId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/media/api/candidates/${candidateId}/schedule`, {
      method: 'POST',
      body: JSON.stringify({}),
    });
  }

  async updateCandidateStatus(candidateId: string, status: string, interviewId?: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/media/api/candidates/${candidateId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, interview_id: interviewId }),
    });
  }

  // =========================================
  // Interview Session Management Methods
  // =========================================

  async createInterviewSession(userId: string, candidateId?: string): Promise<ApiResponse<any>> {
    return this.request<any>('/interview/api/session/create', {
      method: 'POST',
      body: JSON.stringify({
        user_id: userId,
        candidate_id: candidateId,
      }),
    });
  }

  async getInterviewSession(sessionId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/interview/api/session/${sessionId}`);
  }

  async updateSessionStatus(sessionId: string, status: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/interview/api/session/${sessionId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    });
  }

  async saveSessionTranscript(sessionId: string, transcript: any): Promise<ApiResponse<any>> {
    return this.request<any>(`/interview/api/session/${sessionId}/transcript`, {
      method: 'POST',
      body: JSON.stringify(transcript),
    });
  }

  async getTranscriptionResult(sessionId: string): Promise<ApiResponse<any>> {
    return this.request<any>(`/audio-ai/api/v1/audio/results/${sessionId}`);
  }

  // =========================================
  // AI Logic Service Methods (Question Generation, Resume Parsing)
  // =========================================

  async parseResumeWithAI(file: File): Promise<ApiResponse<any>> {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${this.baseUrl}/ai-logic/resumes/parse`;
    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    return response.json();
  }

  async createAICandidate(candidateData: {
    name: string;
    email: string;
    phone?: string;
    resume_text: string;
    skills: string[];
    experience_years: number;
    education?: any[];
  }): Promise<ApiResponse<any>> {
    const url = `${this.baseUrl}/ai-logic/candidates`;
    const token = this.getToken();
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: JSON.stringify(candidateData),
    });

    return response.json();
  }

  async createAIJob(jobData: {
    title: string;
    company: string;
    description: string;
    required_skills: string[];
    experience_level: string;
  }): Promise<ApiResponse<any>> {
    const url = `${this.baseUrl}/ai-logic/jobs`;
    const token = this.getToken();
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: JSON.stringify(jobData),
    });

    return response.json();
  }

  async startAIInterview(data: {
    candidate_id: string;
    job_id: string;
    interview_type?: string;
    difficulty?: string;
    max_questions?: number;
  }): Promise<ApiResponse<any>> {
    const url = `${this.baseUrl}/ai-logic/interviews/start`;
    const token = this.getToken();
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
      body: JSON.stringify({
        candidate_id: data.candidate_id,
        job_id: data.job_id,
        interview_type: data.interview_type || 'standard',
        difficulty: data.difficulty || 'medium',
        max_questions: data.max_questions || 9,
        target_duration_minutes: 30
      }),
    });

    return response.json();
  }

  async getInterviewQuestions(sessionId: string): Promise<ApiResponse<any>> {
    const url = `${this.baseUrl}/ai-logic/interviews/${sessionId}/questions`;
    const token = this.getToken();
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      },
    });

    return response.json();
  }
}

export const apiClient = new ApiClient();
export default apiClient;
