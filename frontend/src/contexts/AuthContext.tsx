'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, AuthToken, getStoredAuthToken, saveAuthToken, clearAuthToken, getCurrentJWTToken } from '@/lib/auth';
import apiClient from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (usernameOrEmail: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (userData: { firstName: string; lastName: string; email: string; password: string; userType: 'recruiter' | 'candidate'; company?: string; domain?: string; role?: string }) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  getToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedAuth = getStoredAuthToken();
        if (storedAuth) {
          setUser(storedAuth.user);
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = async (usernameOrEmail: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      const response = await apiClient.login({
        username: usernameOrEmail,
        password: password
      });

      if (!response.access_token) {
        return { success: false, error: 'Invalid credentials' };
      }

      // Map response to User object
      const user: User = {
        id: response.user.id,
        name: response.user.email.split('@')[0], // Fallback name
        email: response.user.email,
        userType: response.user.role === 'hr' || response.user.role === 'admin' ? 'recruiter' : 'candidate',
        organizationId: response.user.organization_id
      };

      console.log('AuthContext: Login successful, user object:', user);

      const authToken: AuthToken = {
        token: response.access_token,
        user,
        expiresAt: Date.now() + (24 * 60 * 60 * 1000) // Default 24h
      };

      // Save to localStorage
      saveAuthToken(authToken);
      setUser(user);

      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Login failed. Please check your credentials.' };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearAuthToken();
    setUser(null);
  };

  const register = async (userData: { firstName: string; lastName: string; email: string; password: string; userType: 'recruiter' | 'candidate'; company?: string; domain?: string; role?: string }): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);

      const response = await apiClient.onboard({
        organization: {
          name: userData.company || "Personal Workspace",
          domain: userData.domain || userData.email.split('@')[1],
          settings: "{}"
        },
        user: {
          email: userData.email,
          password: userData.password,
          first_name: userData.firstName,
          last_name: userData.lastName,
          role: userData.userType === 'recruiter' ? 'hr' : 'candidate'
        }
      });

      if (!response.success) {
        return { success: false, error: 'Registration failed' };
      }

      // Create user object from input data + response
      const user: User = {
        id: response.user_id,
        name: `${userData.firstName} ${userData.lastName}`,
        email: userData.email,
        userType: userData.userType,
        organizationId: response.organization_id
      };

      const authToken: AuthToken = {
        token: response.access_token,
        user,
        expiresAt: Date.now() + (24 * 60 * 60 * 1000)
      };

      // Save to localStorage
      saveAuthToken(authToken);
      setUser(user);

      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: 'Registration failed. Please try again.' };
    } finally {
      setIsLoading(false);
    }
  };

  const updateUser = (updates: Partial<User>) => {
    if (!user) return;

    const updatedUser = { ...user, ...updates };
    setUser(updatedUser);

    // Update stored auth token
    const storedAuth = getStoredAuthToken();
    if (storedAuth) {
      const updatedAuth: AuthToken = {
        ...storedAuth,
        user: updatedUser
      };
      saveAuthToken(updatedAuth);
    }
  };

  const getToken = () => {
    return getCurrentJWTToken();
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    updateUser,
    getToken
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Hook for protecting routes
export function useRequireAuth() {
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !user) {
      // Redirect to login if not authenticated
      window.location.href = '/login';
    }
  }, [user, isLoading]);

  return { user, isLoading };
}
