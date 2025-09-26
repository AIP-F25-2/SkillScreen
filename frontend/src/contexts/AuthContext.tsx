'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User, AuthToken, getStoredAuthToken, saveAuthToken, clearAuthToken, mockLogin, mockRegister, getCurrentJWTToken } from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  register: (userData: { fullName: string; email: string; password: string; userType: 'recruiter' | 'candidate' }) => Promise<{ success: boolean; error?: string }>;
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

  const login = async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      const authToken = await mockLogin(email, password);
      
      if (!authToken) {
        return { success: false, error: 'Invalid email or password' };
      }

      // Save to localStorage
      saveAuthToken(authToken);
      setUser(authToken.user);
      
      return { success: true };
    } catch (error) {
      return { success: false, error: 'Login failed. Please try again.' };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    clearAuthToken();
    setUser(null);
  };

  const register = async (userData: { fullName: string; email: string; password: string; userType: 'recruiter' | 'candidate' }): Promise<{ success: boolean; error?: string }> => {
    try {
      setIsLoading(true);
      const authToken = await mockRegister(userData);
      
      // Save to localStorage
      saveAuthToken(authToken);
      setUser(authToken.user);
      
      return { success: true };
    } catch (error) {
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
