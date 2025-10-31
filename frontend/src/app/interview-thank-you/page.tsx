'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { CheckCircle, Clock, Mail, Home, UserCheck, FileText } from 'lucide-react';
import { getInterviewToken } from '@/lib/interviewToken';

export default function InterviewThankYouPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const interviewId = searchParams?.get('id');
  
  const [candidateName, setCandidateName] = useState('');
  const [interviewData, setInterviewData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get candidate name from stored token data
    const tokenData = getInterviewToken();
    if (tokenData) {
      setCandidateName(tokenData.candidateName);
    } else {
      // Fallback to a generic name if no token data
      setCandidateName('Candidate');
    }
    
    setLoading(false);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0A0A0A] via-[#1E1E1E] to-[#0A0A0A] flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-green-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0A0A0A] via-[#1E1E1E] to-[#0A0A0A] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-4xl px-6"
      >
        {/* Success Icon */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="mb-8"
        >
          <CheckCircle className="w-32 h-32 text-green-400 mx-auto" />
        </motion.div>

        {/* Main Thank You Message */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-12"
        >
          <h1 className="text-white text-5xl font-bold mb-6">
            Thank You, {candidateName}!
          </h1>
          <p className="text-white/70 text-xl mb-8 max-w-2xl mx-auto">
            Your interview has been completed successfully. We appreciate the time you took to participate in our interview process.
          </p>
        </motion.div>

        {/* Interview Details Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="bg-white/5 rounded-2xl p-8 border border-white/10 mb-8"
        >
          <div className="flex items-center justify-center gap-2 mb-6">
            <FileText className="w-6 h-6 text-blue-400" />
            <h2 className="text-white text-2xl font-semibold">Interview Completed</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-black/30 rounded-xl p-4">
              <div className="text-white/60 text-sm mb-2">Interview ID</div>
              <div className="text-white font-mono text-sm">{interviewId || 'N/A'}</div>
            </div>
            <div className="bg-black/30 rounded-xl p-4">
              <div className="text-white/60 text-sm mb-2">Status</div>
              <div className="text-green-400 font-semibold">Completed</div>
            </div>
            <div className="bg-black/30 rounded-xl p-4">
              <div className="text-white/60 text-sm mb-2">Date</div>
              <div className="text-white">{new Date().toLocaleDateString()}</div>
            </div>
          </div>
        </motion.div>

        {/* What Happens Next */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="bg-green-500/10 border border-green-500/30 rounded-2xl p-8 mb-8"
        >
          <div className="flex items-center justify-center gap-2 mb-6">
            <Clock className="w-6 h-6 text-green-400" />
            <h3 className="text-green-300 text-xl font-semibold">What Happens Next?</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-white text-xs font-bold">1</span>
                </div>
                <div>
                  <h4 className="text-white font-semibold mb-1">Review Process</h4>
                  <p className="text-white/70 text-sm">Our team will review your interview recording and responses</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-white text-xs font-bold">2</span>
                </div>
                <div>
                  <h4 className="text-white font-semibold mb-1">Analysis</h4>
                  <p className="text-white/70 text-sm">We'll analyze your technical skills and communication abilities</p>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-white text-xs font-bold">3</span>
                </div>
                <div>
                  <h4 className="text-white font-semibold mb-1">Decision</h4>
                  <p className="text-white/70 text-sm">You'll be contacted within 2-3 business days with our decision</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span className="text-white text-xs font-bold">4</span>
                </div>
                <div>
                  <h4 className="text-white font-semibold mb-1">Next Steps</h4>
                  <p className="text-white/70 text-sm">If selected, we'll schedule the next round of interviews</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Contact Information */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          className="bg-blue-500/10 border border-blue-500/30 rounded-2xl p-6 mb-8"
        >
          <div className="flex items-center justify-center gap-2 mb-4">
            <Mail className="w-5 h-5 text-blue-400" />
            <h3 className="text-blue-300 text-lg font-semibold">Questions?</h3>
          </div>
          <p className="text-white/70 text-sm">
            If you have any questions about the interview process or need to reschedule, 
            please contact our hiring team at{' '}
            <a href="mailto:hiring@skillscreen.com" className="text-blue-400 hover:text-blue-300 underline">
              hiring@skillscreen.com
            </a>
          </p>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2 }}
          className="flex flex-col sm:flex-row gap-4 justify-center mb-8"
        >
          <button
            onClick={() => window.close()}
            className="px-8 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <UserCheck className="w-5 h-5" />
            Close Window
          </button>
          <button
            onClick={() => router.push('/')}
            className="px-8 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <Home className="w-5 h-5" />
            Return to Home
          </button>
        </motion.div>

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.4 }}
          className="text-white/40 text-sm space-y-2"
        >
          <p>This interview session has been securely recorded and stored.</p>
          <p>Only authorized recruiters can access the full interview details.</p>
          <p className="text-xs mt-4">
            © 2024 SkillScreen. All rights reserved.
          </p>
        </motion.div>
      </motion.div>
    </div>
  );
}
