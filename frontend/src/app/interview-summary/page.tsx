'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { motion } from 'framer-motion';
import { ArrowLeft, Download, Clock, FileText, CheckCircle, ShieldAlert, UserCheck } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { API_BASE_URL } from '@/lib/config';
import { getInterviewToken } from '@/lib/interviewToken';

export default function InterviewSummaryPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const interviewId = searchParams?.get('id');
  const isProcessingParam = searchParams?.get('processing') === 'true';

  const [interview, setInterview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInitialProcessing, setShowInitialProcessing] = useState(isProcessingParam);
  const [accessDenied, setAccessDenied] = useState(false);
  const [isCandidateCompletion, setIsCandidateCompletion] = useState(false);
  const [candidateName, setCandidateName] = useState('');

  useEffect(() => {
    // Debug authentication state
    console.log('🔍 DEBUG: Interview Summary Auth State:', {
      authLoading,
      user,
      userType: user?.userType,
      interviewId,
      isProcessingParam
    });

    // Check if this is a candidate completion flow (no user but has interview token)
    const tokenData = getInterviewToken();
    if (!authLoading && !user && tokenData && interviewId) {
      console.log('🎯 Candidate completion flow detected');
      setIsCandidateCompletion(true);
      setCandidateName(tokenData.candidateName);
      // Allow candidate to see their completion message
    } else if (!authLoading && !user) {
      // No user and no token - access denied
      console.log('❌ No user found, setting access denied');
      setAccessDenied(true);
      setLoading(false);
      return;
    } else if (!authLoading && user && user.userType !== 'recruiter') {
      // User is not a recruiter - access denied
      console.log('❌ User is not a recruiter:', user.userType);
      setAccessDenied(true);
      setLoading(false);
      return;
    } else if (!authLoading && user && user.userType === 'recruiter') {
      console.log('✅ Recruiter access granted');
    }

    const fetchInterview = async () => {
      if (!interviewId) {
        setError('No interview ID provided');
        setLoading(false);
        return;
      }

      try {
        const response = await apiClient.getInterviewDetails(interviewId);
        if (response.success) {
          setInterview(response.data);
          console.log('📊 Interview data loaded:', response.data);
          console.log('📝 Transcript data:', response.data.transcript);
          // Hide initial processing screen once we have data
          if (response.data.status === 'completed' || response.data.transcript) {
            setShowInitialProcessing(false);
          }
        } else {
          setError('Failed to load interview');
        }
      } catch (err) {
        console.error('Error fetching interview:', err);
        setError('Failed to load interview');
      } finally {
        setLoading(false);
      }
    };

    if (!authLoading && (user?.userType === 'recruiter' || isCandidateCompletion)) {
    fetchInterview();
    }

    // Poll for updates if processing
    const pollInterval = setInterval(async () => {
      if (!interviewId) return;
      
      try {
        const response = await apiClient.getInterviewDetails(interviewId);
        if (response.success) {
          setInterview(response.data);
          
          // Stop polling if completed
          if (response.data.status === 'completed') {
            clearInterval(pollInterval);
            setShowInitialProcessing(false);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(pollInterval);
  }, [interviewId, isProcessingParam, user, authLoading, isCandidateCompletion]);

  // Show candidate completion screen
  if (isCandidateCompletion && !loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0A0A0A] via-[#1E1E1E] to-[#0A0A0A] flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-2xl px-6"
        >
          <UserCheck className="w-24 h-24 text-green-400 mx-auto mb-6" />
          <h1 className="text-white text-4xl font-bold mb-4">Thank You, {candidateName}!</h1>
          <p className="text-white/70 text-xl mb-8">
            Your interview has been completed successfully.
          </p>
          
          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6 mb-8">
            <h2 className="text-green-300 text-lg font-semibold mb-3">What happens next?</h2>
            <div className="text-white/80 text-left space-y-2">
              <p>• Our team will review your interview recording and responses</p>
              <p>• We'll analyze your technical skills and communication</p>
              <p>• You'll be contacted within 2-3 business days with next steps</p>
              <p>• If selected, we'll schedule the next round of interviews</p>
            </div>
          </div>

          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6 mb-8">
            <h3 className="text-blue-300 text-lg font-semibold mb-3">Interview Details</h3>
            <div className="text-white/80 text-left space-y-2">
              <p><strong>Interview ID:</strong> {interviewId}</p>
              <p><strong>Status:</strong> Completed</p>
              <p><strong>Duration:</strong> {interview?.duration || 'Processing...'}</p>
              <p><strong>Questions Answered:</strong> {interview?.questions?.length || 'Processing...'}</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => window.close()}
              className="px-8 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              Close Window
            </button>
            <button
              onClick={() => router.push('/')}
              className="px-8 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
            >
              Return to Home
            </button>
          </div>

          <div className="mt-8 text-white/50 text-sm">
            <p>This interview session has been securely recorded and stored.</p>
            <p>Only authorized recruiters can access the full interview details.</p>
          </div>
        </motion.div>
      </div>
    );
  }

  // Show access denied screen
  if (accessDenied) {
    return (
      <div className="min-h-screen bg-[#1E1E1E] flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md px-6"
        >
          <ShieldAlert className="w-24 h-24 text-red-400 mx-auto mb-6" />
          <h1 className="text-white text-3xl font-bold mb-4">Access Denied</h1>
          <p className="text-white/70 text-lg mb-6">
            Interview summaries are only accessible to recruiters.
          </p>
          <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
            <p className="text-red-300 text-sm">
              {!user 
                ? 'Please log in as a recruiter to view this page.' 
                : 'Your account does not have permission to view interview summaries.'}
            </p>
          </div>
          <button
            onClick={() => router.push(user ? '/recruiter' : '/login')}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
          >
            {user ? 'Go to Dashboard' : 'Go to Login'}
          </button>
        </motion.div>
      </div>
    );
  }

  // Show big processing message when first redirected
  if (showInitialProcessing && loading) {
    return (
      <div className="min-h-screen bg-[#1E1E1E] flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-2xl px-6"
        >
          <div className="w-24 h-24 border-4 border-yellow-500 border-t-transparent rounded-full animate-spin mx-auto mb-6"></div>
          <h1 className="text-white text-4xl font-bold mb-4">Processing Your Interview</h1>
          <p className="text-white/70 text-lg mb-6">
            Your interview is being processed and transcribed. This may take 5-10 minutes.
          </p>
          <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6 mb-6">
            <p className="text-blue-300 text-sm mb-2">
              <strong>What's happening:</strong>
            </p>
            <ul className="text-white/60 text-sm space-y-1 text-left">
              <li>✓ Video saved successfully</li>
              <li>⏳ Extracting audio from video</li>
              <li>⏳ Transcribing with AI model</li>
              <li>⏳ Processing complete transcript</li>
            </ul>
          </div>
          <p className="text-white/50 text-sm">
            You can wait here or come back in a few minutes. This page will auto-refresh when complete.
          </p>
        </motion.div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#1E1E1E] flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (error || !interview) {
    return (
      <div className="min-h-screen bg-[#1E1E1E] flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-white text-2xl font-bold mb-4">Error</h1>
          <p className="text-white/70">{error || 'Interview not found'}</p>
          <button
            onClick={() => router.push('/recruiter')}
            className="mt-6 px-6 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Video path from backend is like: /ashish/filename.mp4
  // Use configurable API base URL for video serving
  const videoUrl = interview.video_path
    ? `${API_BASE_URL}/media/video${interview.video_path}`
    : '';
  
  console.log('Interview data:', interview);
  console.log('Video URL:', videoUrl);

  const downloadTranscript = () => {
    const text = interview.transcript?.text || 'No transcript available';
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview-${interview.interview_id}-transcript.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-[#1E1E1E] p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-white/70 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            Back
          </button>
          <h1 className="text-white text-3xl font-bold">Interview Summary</h1>
          <div className="w-20"></div>
        </div>

        {/* Status Badge */}
        <div className="mb-6">
          <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium ${
            interview.status === 'completed' 
              ? 'bg-green-500/20 text-green-400' 
              : interview.status === 'processing'
              ? 'bg-yellow-500/20 text-yellow-400'
              : 'bg-gray-500/20 text-gray-400'
          }`}>
            {interview.status === 'completed' && <CheckCircle className="w-4 h-4" />}
            {interview.status === 'processing' && <Clock className="w-4 h-4 animate-spin" />}
            {interview.status === 'completed' ? 'Completed' : 'Processing...'}
          </span>
        </div>

        {/* Video Player */}
        <div className="bg-black/50 rounded-xl overflow-hidden mb-8">
          <video
            src={videoUrl}
            controls
            className="w-full aspect-video"
          />
        </div>

        {/* Interview Info */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <div className="text-white/60 text-sm mb-1">Candidate</div>
            <div className="text-white text-lg font-semibold">{interview.candidate_id}</div>
          </div>
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <div className="text-white/60 text-sm mb-1">Date</div>
            <div className="text-white text-lg font-semibold">
              {new Date(interview.created_at).toLocaleDateString()}
            </div>
          </div>
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <div className="text-white/60 text-sm mb-1">Duration</div>
            <div className="text-white text-lg font-semibold">
              {interview.transcript?.duration_seconds 
                ? `${Math.floor(interview.transcript.duration_seconds / 60)}m ${Math.floor(interview.transcript.duration_seconds % 60)}s`
                : 'N/A'}
            </div>
          </div>
        </div>

        {/* Transcript Section */}
        {interview.transcript ? (
          <div className="bg-white/5 rounded-xl p-6 border border-white/10">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-white text-2xl font-bold flex items-center gap-2">
                <FileText className="w-6 h-6" />
                Transcript
              </h2>
              <button
                onClick={downloadTranscript}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
              >
                <Download className="w-4 h-4" />
                Download
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-white/60 text-sm mb-1">Word Count</div>
                <div className="text-white text-2xl font-semibold">{interview.transcript.word_count || 0}</div>
              </div>
              <div className="bg-black/30 rounded-lg p-4">
                <div className="text-white/60 text-sm mb-1">Language</div>
                <div className="text-white text-2xl font-semibold">{interview.transcript.language || 'N/A'}</div>
              </div>
            </div>

            <div className="bg-black/30 rounded-lg p-6">
              <p className="text-white/80 whitespace-pre-wrap leading-relaxed">
                {interview.transcript.text}
              </p>
            </div>
          </div>
        ) : interview.status === 'processing' ? (
          <div className="bg-white/5 rounded-xl p-12 border border-white/10 text-center">
            <Clock className="w-16 h-16 text-yellow-400 mx-auto mb-4 animate-spin" />
            <h3 className="text-white text-xl font-semibold mb-2">Transcription in Progress</h3>
            <p className="text-white/60">
              The AI is transcribing your interview. This usually takes 5-10 minutes.
            </p>
            <p className="text-white/40 text-sm mt-4">
              This page will automatically update when the transcript is ready.
            </p>
          </div>
        ) : (
          <div className="bg-white/5 rounded-xl p-12 border border-white/10 text-center">
            <FileText className="w-16 h-16 text-white/30 mx-auto mb-4" />
            <h3 className="text-white text-xl font-semibold mb-2">No Transcript Available</h3>
            <p className="text-white/60">
              The transcript for this interview is not available yet.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

