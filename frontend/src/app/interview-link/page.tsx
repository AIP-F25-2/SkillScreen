'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Loader, Mail } from 'lucide-react';
import { validateInterviewToken, storeInterviewToken } from '@/lib/interviewToken';

export default function InterviewLinkPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'valid' | 'invalid' | 'expired'>('loading');
  const [candidateName, setCandidateName] = useState('');
  const [error, setError] = useState('');
  const hasValidated = useRef(false); // Prevent multiple validations

  useEffect(() => {
    const verifyToken = async () => {
      // Prevent multiple validations
      if (hasValidated.current) {
        console.log('🔄 Token validation already completed, skipping...');
        return;
      }

      const token = searchParams?.get('token');

      if (!token) {
        setStatus('invalid');
        setError('No interview token provided. Please check your email link.');
        return;
      }

      hasValidated.current = true;
      console.log('🔍 Starting token validation for:', token.substring(0, 10) + '...');

      try {
        // Validate token with backend
        const validation = await validateInterviewToken(token);

        if (!validation.valid) {
          setStatus('expired');
          setError(validation.error || 'This interview link is no longer valid.');
          return;
        }

        // Store token data
        if (validation.data) {
          console.log('✅ Token validation successful, storing data:', validation.data);
          storeInterviewToken(validation.data);
          setCandidateName(validation.data.candidateName);
          setStatus('valid');

          // Auto-redirect to interview setup after 2 seconds
          setTimeout(() => {
            router.push('/interview-setup?fromToken=true');
          }, 2000);
        }
      } catch (error) {
        console.error('❌ Token validation failed:', error);
        setStatus('expired');
        setError('Failed to validate interview link. Please try again.');
      }
    };

    verifyToken();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0A0A0A] via-[#1E1E1E] to-[#0A0A0A] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="bg-black/40 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/10 overflow-hidden p-8">
          {status === 'loading' && (
            <div className="text-center">
              <Loader className="w-16 h-16 text-blue-400 mx-auto mb-4 animate-spin" />
              <h1 className="text-2xl font-bold text-white mb-2">Verifying Your Interview Link</h1>
              <p className="text-white/60">Please wait while we validate your access...</p>
            </div>
          )}

          {status === 'valid' && (
            <div className="text-center">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-white mb-2">Welcome, {candidateName}!</h1>
              <p className="text-white/60 mb-4">Your interview link has been verified.</p>
              <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4 mb-6">
                <p className="text-green-300 text-sm">
                  Redirecting you to the interview setup...
                </p>
              </div>
              <div className="flex items-center justify-center gap-2 text-white/40 text-sm">
                <Loader className="w-4 h-4 animate-spin" />
                <span>Please wait...</span>
              </div>
            </div>
          )}

          {(status === 'invalid' || status === 'expired') && (
            <div className="text-center">
              <XCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-white mb-2">
                {status === 'expired' ? 'Link Expired' : 'Invalid Link'}
              </h1>
              <p className="text-white/60 mb-4">{error}</p>
              
              <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
                <p className="text-red-300 text-sm mb-2">
                  {status === 'expired' 
                    ? 'This interview link has expired or has already been used.' 
                    : 'The link you used is not valid.'}
                </p>
                <p className="text-red-200/70 text-xs">
                  Please contact the recruiter for a new interview link.
                </p>
              </div>

              <div className="flex items-center justify-center gap-2 text-white/60 text-sm">
                <Mail className="w-4 h-4" />
                <span>Check your email for the correct link</span>
              </div>
            </div>
          )}
        </div>

        {/* Security Notice */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-6 text-center"
        >
          <p className="text-white/40 text-xs">
            🔒 This is a secure, one-time interview link
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}

