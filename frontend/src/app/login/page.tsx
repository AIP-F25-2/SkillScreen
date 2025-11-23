'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { ShaderAnimation } from '@/components/ui/shader-lines';
import Footer from '@/components/Footer';
import Image from 'next/image';
import Link from 'next/link';
import { GrainGradient as GrainGradient1 } from '@paper-design/shaders-react';




export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading } = useAuth();
  
  const [formData, setFormData] = useState({
    usernameOrEmail: '',
    password: ''
  });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDemo, setShowDemo] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push('/');
    }
  }, [isAuthenticated, isLoading, router]);

  const validateForm = () => {
    const newErrors: { [key: string]: string } = {};
    
    if (!formData.usernameOrEmail.trim()) {
      newErrors.usernameOrEmail = 'Username or email is required';
    }
    
    if (!formData.password.trim()) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 3) {
      newErrors.password = 'Password must be at least 3 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setIsSubmitting(true);
    const result = await login(formData.usernameOrEmail, formData.password);
    
    if (result.success) {
      router.push('/');
    } else {
      setErrors({ submit: result.error || 'Login failed' });
    }
    
    setIsSubmitting(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const fillDemoCredentials = (userType: 'recruiter' | 'candidate') => {
    const usernameOrEmail = userType === 'recruiter' ? 'admin' : 'ashish';
    setFormData({
      usernameOrEmail,
      password: userType === 'recruiter' ? 'password' : '1234'
    });
    setShowDemo(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-white"></div>
      </div>
    );
  }

  return (
   <div className="relative min-h-screen flex flex-col overflow-hidden">
      {/*<div className="absolute inset-0 -z-10">
        <GrainGradient1
          colors={['#7300ff', '#eba8ff', '#00bfff', '#2a00ff']}
          colorBack="#00000000"
          speed={1}
          scale={1}
          rotation={0}
          offsetX={0}
          offsetY={0}
          softness={0.5}
          intensity={0.5}
          noise={0.25}
          shape="corners"
          style={{ width: '100%', height: '100%' }}
        />
      </div>*/}

       <ShaderAnimation 
        currentStep={1}
        totalSteps={1}
        progress={0.5}
      /> 

      <div className="flex-1 flex items-center justify-center p-6">
        <motion.div 
          className="w-full max-w-md bg-black/40 backdrop-blur-md rounded-2xl p-8 shadow-2xl"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Logo */}
          <div className="text-center mb-8">
          <Link href="/" className="flex items-center space-x-2 justify-center">
          <div className="relative w-8 h-8">
            <Image
                src="/logo.png"
                alt="IntervuAI Logo"
                fill
                sizes="(max-width: 768px) 32px, (max-width: 1200px) 32px, 32px"
                className="object-contain"
              />
            </div>
            <span className="text-white text-xl font-bold">
              IntervuAI
            </span>
          </Link>
            <p className="text-white/70">Sign in to your account</p>
          </div>

          {/* Demo Info */}
          <div className="mb-6 p-4 bg-blue-500/20 rounded-lg border border-blue-500/30">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-300 font-medium">Demo Accounts</p>
                <p className="text-xs text-blue-200/70">Click to auto-fill credentials</p>
              </div>
              <button
                onClick={() => setShowDemo(!showDemo)}
                className="text-blue-300 hover:text-blue-200 text-sm font-medium"
              >
                {showDemo ? 'Hide' : 'Show'}
              </button>
            </div>
            
            {showDemo && (
              <motion.div 
                className="mt-3 space-y-2"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                transition={{ duration: 0.3 }}
              >
                <button
                  onClick={() => fillDemoCredentials('recruiter')}
                  className="w-full text-left p-2 bg-blue-600/30 hover:bg-blue-600/40 rounded text-sm text-blue-200 transition-colors"
                >
                  <strong>Admin:</strong> admin / password
                </button>
                <button
                  onClick={() => fillDemoCredentials('candidate')}
                  className="w-full text-left p-2 bg-blue-600/30 hover:bg-blue-600/40 rounded text-sm text-blue-200 transition-colors"
                >
                  <strong>User:</strong> ashish / 1234
                </button>
                <div className="text-xs text-blue-200/70 mt-2">
                  <p>You can also use:</p>
                  <p>• admin@intervuai.com / password</p>
                  <p>• ashish@intervuai.com / 1234</p>
                </div>
              </motion.div>
            )}
          </div>

          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="usernameOrEmail" className="block text-sm font-medium text-white mb-2">
                Username or Email
              </label>
              <input
                type="text"
                id="usernameOrEmail"
                name="usernameOrEmail"
                value={formData.usernameOrEmail}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 bg-white/10 border rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 transition-all ${
                  errors.usernameOrEmail ? 'border-red-500 focus:ring-red-500' : 'border-white/20 focus:ring-blue-500'
                }`}
                placeholder="Enter your username or email"
              />
              {errors.usernameOrEmail && (
                <p className="mt-1 text-sm text-red-400">{errors.usernameOrEmail}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className={`w-full px-4 py-3 bg-white/10 border rounded-xl text-white placeholder-white/50 focus:outline-none focus:ring-2 transition-all ${
                  errors.password ? 'border-red-500 focus:ring-red-500' : 'border-white/20 focus:ring-blue-500'
                }`}
                placeholder="Enter your password"
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-400">{errors.password}</p>
              )}
            </div>

            {errors.submit && (
              <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
                <p className="text-sm text-red-300">{errors.submit}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 px-4 bg-white text-black font-medium rounded-xl hover:bg-white/90 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-black mr-2"></div>
                  Signing in...
                </div>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          {/* Footer */}
          <div className="mt-6 text-center">
            <p className="text-sm text-white/60">
              New to IntervuAI?{' '}
              <button
                onClick={() => router.push('/onboarding')}
                className="text-blue-300 hover:text-blue-200 font-medium"
              >
                Get Started
              </button>
            </p>
          </div>
        </motion.div>
      </div>

    </div>
  );
}
