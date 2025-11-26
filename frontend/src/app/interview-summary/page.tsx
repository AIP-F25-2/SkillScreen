'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Download,
  Clock,
  FileText,
  CheckCircle,
  ShieldAlert,
  UserCheck,
  Play,
  BarChart3,
  BrainCircuit,
  Target,
  TrendingUp,
  AlertCircle
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { API_BASE_URL } from '@/lib/config';
import { getInterviewToken } from '@/lib/interviewToken';
import TranscriptModal from '@/components/TranscriptModal';

// Mock analysis data for visualization if not present in API
const MOCK_ANALYSIS = {
  overall_score: 85,
  categories: [
    { name: 'Technical Proficiency', score: 88, feedback: 'Strong understanding of core concepts.' },
    { name: 'Communication', score: 82, feedback: 'Clear and concise explanations.' },
    { name: 'Problem Solving', score: 85, feedback: 'Good analytical approach to challenges.' },
    { name: 'Cultural Fit', score: 90, feedback: 'Aligns well with team values.' }
  ],
  key_strengths: [
    'Deep knowledge of React and modern frontend ecosystems',
    'Excellent system design capabilities',
    'Strong advocate for code quality and testing'
  ],
  areas_for_improvement: [
    'Could provide more concrete examples for soft skill questions',
    'Slightly hesitant on database optimization topics'
  ],
  executive_summary: "The candidate demonstrates a strong technical background with a focus on frontend technologies. They communicated complex ideas effectively and showed a solid problem-solving mindset. Highly recommended for the Senior Frontend role."
};

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
  const [isTranscriptOpen, setIsTranscriptOpen] = useState(false);

  useEffect(() => {
    // Check if this is a candidate completion flow (no user but has interview token)
    const tokenData = getInterviewToken();
    if (!authLoading && !user && tokenData && interviewId) {
      setIsCandidateCompletion(true);
      setCandidateName(tokenData.candidateName);
    } else if (!authLoading && !user) {
      setAccessDenied(true);
      setLoading(false);
      return;
    } else if (!authLoading && user && user.userType !== 'recruiter') {
      setAccessDenied(true);
      setLoading(false);
      return;
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
          // Merge with mock analysis if real analysis is missing (for demo purposes)
          const data = {
            ...response.data,
            analysis: response.data.analysis || MOCK_ANALYSIS
          };
          setInterview(data);

          if (data.status === 'completed' || data.transcript) {
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
          const data = {
            ...response.data,
            analysis: response.data.analysis || MOCK_ANALYSIS
          };
          setInterview(data);

          if (data.status === 'completed') {
            clearInterval(pollInterval);
            setShowInitialProcessing(false);
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 10000);

    return () => clearInterval(pollInterval);
  }, [interviewId, isProcessingParam, user, authLoading, isCandidateCompletion]);

  // Loading State
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // Candidate Completion View
  if (isCandidateCompletion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#0A0A0A] via-[#1E1E1E] to-[#0A0A0A] flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-2xl w-full glass-dark p-8 rounded-2xl border border-white/10"
        >
          <UserCheck className="w-24 h-24 text-green-400 mx-auto mb-6" />
          <h1 className="text-white text-4xl font-bold mb-4">Thank You, {candidateName}!</h1>
          <p className="text-white/70 text-xl mb-8">
            Your interview has been completed successfully.
          </p>

          <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6 mb-8 text-left">
            <h2 className="text-green-300 text-lg font-semibold mb-3">What happens next?</h2>
            <div className="text-white/80 space-y-2">
              <p>• Our team will review your interview recording and responses</p>
              <p>• We'll analyze your technical skills and communication</p>
              <p>• You'll be contacted within 2-3 business days with next steps</p>
            </div>
          </div>

          <button
            onClick={() => router.push('/')}
            className="px-8 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors font-medium"
          >
            Return to Home
          </button>
        </motion.div>
      </div>
    );
  }

  // Access Denied View
  if (accessDenied) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center max-w-md w-full glass-dark p-8 rounded-2xl border border-white/10"
        >
          <ShieldAlert className="w-24 h-24 text-red-400 mx-auto mb-6" />
          <h1 className="text-white text-3xl font-bold mb-4">Access Denied</h1>
          <p className="text-white/70 text-lg mb-6">
            Interview summaries are only accessible to recruiters.
          </p>
          <button
            onClick={() => router.push(user ? '/recruiter' : '/login')}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors font-medium"
          >
            {user ? 'Go to Dashboard' : 'Go to Login'}
          </button>
        </motion.div>
      </div>
    );
  }

  if (error || !interview) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] flex items-center justify-center">
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

  const videoUrl = interview.video_path
    ? `${API_BASE_URL}/media/video${interview.video_path}`
    : '';

  const analysis = interview.analysis || MOCK_ANALYSIS;

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white font-sans selection:bg-blue-500/30">
      {/* Background Ambient Glow */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-blue-500/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-purple-500/10 blur-[120px] rounded-full" />
      </div>

      <div className="relative z-10 max-w-[1600px] mx-auto p-6 lg:p-10">
        {/* Header */}
        <header className="flex items-center justify-between mb-10">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.back()}
              className="p-2 rounded-full bg-white/5 hover:bg-white/10 transition-colors border border-white/10 group"
            >
              <ArrowLeft className="w-5 h-5 text-white/70 group-hover:text-white" />
            </button>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">Interview Analysis</h1>
              <div className="flex items-center gap-3 text-white/50 text-sm mt-1">
                <span>ID: {interviewId}</span>
                <span>•</span>
                <span>{new Date(interview.created_at).toLocaleDateString(undefined, { dateStyle: 'long' })}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border ${interview.status === 'completed'
                ? 'bg-green-500/10 text-green-400 border-green-500/20'
                : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'
              }`}>
              {interview.status === 'completed' ? <CheckCircle className="w-4 h-4" /> : <Clock className="w-4 h-4 animate-spin" />}
              {interview.status === 'completed' ? 'Analysis Complete' : 'Processing...'}
            </span>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Video & Key Metrics (4 cols) */}
          <div className="lg:col-span-4 space-y-6">
            {/* Video Player Card */}
            <div className="glass-dark rounded-2xl overflow-hidden border border-white/10 shadow-xl">
              <div className="relative aspect-video bg-black group">
                {videoUrl ? (
                  <video src={videoUrl} controls className="w-full h-full object-cover" />
                ) : (
                  <div className="absolute inset-0 flex items-center justify-center text-white/30">
                    <p>Video unavailable</p>
                  </div>
                )}
              </div>
              <div className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{interview.candidate_id}</h3>
                    <p className="text-white/50 text-sm">Candidate</p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-mono font-medium">
                      {interview.transcript?.duration_seconds
                        ? `${Math.floor(interview.transcript.duration_seconds / 60)}:${(interview.transcript.duration_seconds % 60).toString().padStart(2, '0')}`
                        : '--:--'}
                    </div>
                    <p className="text-white/50 text-sm">Duration</p>
                  </div>
                </div>

                <button
                  onClick={() => setIsTranscriptOpen(true)}
                  className="w-full flex items-center justify-center gap-2 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl transition-all group"
                >
                  <FileText className="w-4 h-4 text-blue-400 group-hover:text-blue-300" />
                  <span className="font-medium">View Full Transcript</span>
                </button>
              </div>
            </div>

            {/* Overall Score Card */}
            <div className="glass-dark rounded-2xl p-6 border border-white/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-32 bg-blue-500/10 blur-[60px] rounded-full pointer-events-none" />

              <h3 className="text-lg font-semibold text-white/90 mb-6 flex items-center gap-2">
                <Target className="w-5 h-5 text-blue-400" />
                Overall Score
              </h3>

              <div className="flex items-end gap-4 mb-6">
                <div className="text-6xl font-bold text-white tracking-tighter">
                  {analysis.overall_score}
                </div>
                <div className="text-xl text-white/40 font-medium mb-2">/ 100</div>
              </div>

              <div className="space-y-4">
                {analysis.categories.map((cat: any, idx: number) => (
                  <div key={idx}>
                    <div className="flex justify-between text-sm mb-1.5">
                      <span className="text-white/70">{cat.name}</span>
                      <span className="font-medium text-white">{cat.score}%</span>
                    </div>
                    <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${cat.score}%` }}
                        transition={{ duration: 1, delay: 0.2 + (idx * 0.1) }}
                        className={`h-full rounded-full ${cat.score >= 80 ? 'bg-green-500' :
                            cat.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Deep Analysis (8 cols) */}
          <div className="lg:col-span-8 space-y-6">

            {/* Executive Summary */}
            <div className="glass-dark rounded-2xl p-8 border border-white/10">
              <h3 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <BrainCircuit className="w-6 h-6 text-purple-400" />
                Executive Summary
              </h3>
              <p className="text-white/80 leading-relaxed text-lg font-light">
                {analysis.executive_summary}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Key Strengths */}
              <div className="glass-dark rounded-2xl p-6 border border-white/10 bg-green-500/5">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-green-400" />
                  Key Strengths
                </h3>
                <ul className="space-y-3">
                  {analysis.key_strengths.map((strength: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 text-white/80">
                      <CheckCircle className="w-5 h-5 text-green-500/50 shrink-0 mt-0.5" />
                      <span className="text-sm leading-relaxed">{strength}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Areas for Improvement */}
              <div className="glass-dark rounded-2xl p-6 border border-white/10 bg-orange-500/5">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-orange-400" />
                  Areas for Improvement
                </h3>
                <ul className="space-y-3">
                  {analysis.areas_for_improvement.map((area: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 text-white/80">
                      <div className="w-1.5 h-1.5 rounded-full bg-orange-500/50 mt-2 shrink-0" />
                      <span className="text-sm leading-relaxed">{area}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Detailed Category Breakdown */}
            <div className="glass-dark rounded-2xl p-8 border border-white/10">
              <h3 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                <BarChart3 className="w-6 h-6 text-blue-400" />
                Detailed Analysis
              </h3>
              <div className="grid grid-cols-1 gap-6">
                {analysis.categories.map((cat: any, idx: number) => (
                  <div key={idx} className="p-4 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-white">{cat.name}</h4>
                      <span className={`px-2 py-1 rounded text-xs font-bold ${cat.score >= 80 ? 'bg-green-500/20 text-green-300' :
                          cat.score >= 60 ? 'bg-yellow-500/20 text-yellow-300' : 'bg-red-500/20 text-red-300'
                        }`}>
                        {cat.score}/100
                      </span>
                    </div>
                    <p className="text-white/60 text-sm leading-relaxed">
                      {cat.feedback}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Transcript Modal */}
      <TranscriptModal
        isOpen={isTranscriptOpen}
        onClose={() => setIsTranscriptOpen(false)}
        transcript={interview.transcript || { text: 'No transcript available.' }}
        candidateName={interview.candidate_id}
        date={interview.created_at}
      />
    </div>
  );
}
