export type UserType = 'recruiter' | 'candidate';

export interface User {
  id: string;
  name: string;
  email: string;
  userType: UserType;
  organizationId?: string;
}

export interface AuthToken {
  token: string;
  user: User;
  expiresAt: number; // epoch ms
}

const LOCAL_STORAGE_KEY = 'intervuai_auth_token';

export function getStoredAuthToken(): AuthToken | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthToken;
    if (!parsed || typeof parsed !== 'object') return null;
    if (parsed.expiresAt && Date.now() > parsed.expiresAt) {
      window.localStorage.removeItem(LOCAL_STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function saveAuthToken(authToken: AuthToken): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(authToken));
}

export function clearAuthToken(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(LOCAL_STORAGE_KEY);
}

export async function mockLogin(usernameOrEmail: string, password: string): Promise<AuthToken | null> {
  try {
    const { apiClient } = await import('./api');
    const response = await apiClient.login({
      username: usernameOrEmail,
      password: password,
    });

    if (!response || !response.access_token) {
      return null;
    }

    // Extract user info from response
    const user: User = {
      id: response.user.id,
      name: response.user.email.split('@')[0], // Fallback name
      email: response.user.email,
      userType: response.user.role === 'admin' || response.user.role === 'recruiter' ? 'recruiter' : 'candidate',
      organizationId: response.user.organization_id,
    };

    return {
      token: response.access_token,
      user,
      expiresAt: Date.now() + (24 * 60 * 60 * 1000), // Default 24h expiration
    };
  } catch (error) {
    console.error('Login error:', error);
    return null;
  }
}

export async function mockRegister(userData: { fullName: string; email: string; password: string; userType: UserType }): Promise<AuthToken> {
  const user: User = {
    id: Math.random().toString(36).slice(2),
    name: userData.fullName,
    email: userData.email,
    userType: userData.userType,
  };
  return createAuthToken(user);
}

function createAuthToken(user: User): AuthToken {
  const expiresAt = Date.now() + 1000 * 60 * 60 * 24; // 24h
  const token = btoa(`${user.id}:${user.email}:${expiresAt}`);
  return { token, user, expiresAt };
}

export function getCurrentJWTToken(): string | null {
  const stored = getStoredAuthToken();
  return stored?.token ?? null;
}



