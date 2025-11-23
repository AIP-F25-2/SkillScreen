'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';

export default function TestPage() {
  const { user, isAuthenticated, login, logout } = useAuth();
  const [testResults, setTestResults] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);

  const testBackendConnection = async () => {
    setIsLoading(true);
    try {
      const results = {
        authHealth: await apiClient.getAuthHealth(),
        assessmentQuestions: await apiClient.getQuestions(),
        codingProblems: await apiClient.getProblems(),
      };
      setTestResults(results);
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      setTestResults({ error: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (usernameOrEmail: string, password: string) => {
    const result = await login(usernameOrEmail, password);
    if (result.success) {
      alert('Login successful!');
    } else {
      alert(`Login failed: ${result.error}`);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Backend Integration Test</h1>
        
        {/* Authentication Status */}
        <div className="bg-gray-800 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">Authentication Status</h2>
          <p>Authenticated: {isAuthenticated ? 'Yes' : 'No'}</p>
          {user && (
            <div className="mt-2">
              <p>User: {user.name}</p>
              <p>Email: {user.email}</p>
              <p>Type: {user.userType}</p>
            </div>
          )}
        </div>

        {/* Login Buttons */}
        <div className="bg-gray-800 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">Test Login</h2>
          <div className="space-x-4">
            <button
              onClick={() => handleLogin('admin', 'password')}
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
            >
              Login as Admin
            </button>
            <button
              onClick={() => handleLogin('ashish', '1234')}
              className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded"
            >
              Login as User
            </button>
            {isAuthenticated && (
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded"
              >
                Logout
              </button>
            )}
          </div>
        </div>

        {/* Backend Test */}
        <div className="bg-gray-800 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">Backend API Test</h2>
          <button
            onClick={testBackendConnection}
            disabled={isLoading}
            className="bg-purple-600 hover:bg-purple-700 disabled:opacity-50 px-4 py-2 rounded"
          >
            {isLoading ? 'Testing...' : 'Test Backend Connection'}
          </button>
        </div>

        {/* Results */}
        {testResults && (
          <div className="bg-gray-800 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">Test Results</h2>
            <pre className="bg-gray-900 p-4 rounded overflow-auto text-sm">
              {JSON.stringify(testResults, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
