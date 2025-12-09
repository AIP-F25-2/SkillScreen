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

      if (interviewId === '550e8400-e29b-41d4-a716-446655440000') {
        setInterview({
          interview_id: '550e8400-e29b-41d4-a716-446655440000',
          candidate_id: 'Dimantha Goonewardena',
          created_at: '2025-12-08T23:59:00',
          status: 'completed',
          video_url: 'https://drive.google.com/uc?export=download&id=1o6wXBqzNep6rQwcEWxBnXesxchrhUQPm',
          transcript: {
            duration_seconds: 1845,
            text: "Interviewer: Welcome, Dimantha. Let's start with your experience in React.\n\nCandidate: Sure. I've been working with React for about 5 years now, focusing on performance optimization and scalable architecture. I'm particularly interested in server-side rendering with Next.js.\n\nInterviewer: That's great. Can you explain how you handle state management in complex applications?\n\nCandidate: For complex state, I typically prefer using a combination of React Context for global UI state and a library like Redux Toolkit or Zustand for more complex data flows. I also use React Query for server state management to handle caching and synchronization efficiently."
          },
          analysis: {
            overall_score: 92,
            categories: [
              { name: 'Technical Proficiency', score: 95, feedback: 'Exceptional understanding of React internals and modern frontend patterns.' },
              { name: 'Communication', score: 88, feedback: 'Articulate and clear, though could be slightly more concise in technical explanations.' },
              { name: 'Problem Solving', score: 90, feedback: 'Demonstrated strong analytical skills when breaking down the system design problem.' },
              { name: 'Cultural Fit', score: 94, feedback: 'Showed great enthusiasm for mentorship and team collaboration.' }
            ],
            key_strengths: [
              'Deep expertise in React ecosystem and performance optimization',
              'Strong architectural thinking',
              'Proactive approach to testing and quality assurance'
            ],
            areas_for_improvement: [
              'Could provide more concrete examples of conflict resolution',
              'Slight tendency to over-engineer simple solutions initially'
            ],
            executive_summary: "Dimantha is a highly skilled Senior Frontend Engineer with a deep understanding of modern web technologies. He demonstrated exceptional technical proficiency and a strong problem-solving mindset. His communication was clear, and he showed a great cultural fit for a collaborative team environment. Highly recommended for the role."
          },
          cheating_detection: [
            { timestamp: "05:23", description: "Tab switch detected for 15 seconds", severity: "medium" },
            { timestamp: "12:45", description: "Multiple faces detected in frame", severity: "high" }
          ]
        });
        setLoading(false);
        return;
      }

      if (interviewId === '661f9511-f3ac-52e5-b827-557766551111') {
        setInterview({
          interview_id: '661f9511-f3ac-52e5-b827-557766551111',
          candidate_id: 'Dimantha Goonewardena',
          created_at: '2025-12-07T14:30:00',
          status: 'completed',
          video_url: 'https://drive.google.com/uc?export=download&id=1o6wXBqzNep6rQwcEWxBnXesxchrhUQPm',
          transcript: {
            duration_seconds: 1200,
            text: "Interviewer: Can you explain the difference between a process and a thread?\n\nCandidate: Um, I think a process is like a program running, and a thread is... part of it? I'm not entirely sure about the details.\n\nInterviewer: Okay. How about database indexing? When would you use it?\n\nCandidate: Indexing makes searches faster. I use it on all columns usually."
          },
          analysis: {
            overall_score: 45,
            categories: [
              { name: 'Technical Proficiency', score: 40, feedback: 'Lacks fundamental knowledge of OS concepts and database optimization.' },
              { name: 'Communication', score: 55, feedback: 'Answers were brief and lacked confidence.' },
              { name: 'Problem Solving', score: 42, feedback: 'Struggled to apply theoretical concepts to practical scenarios.' },
              { name: 'Cultural Fit', score: 60, feedback: 'Polite but seemed disengaged during the technical deep dive.' }
            ],
            key_strengths: [
              'Basic understanding of web development terminology',
              'Polite and respectful demeanor'
            ],
            areas_for_improvement: [
              'Deepen understanding of core computer science concepts',
              'Avoid "indexing everything" - learn about trade-offs',
              'Improve confidence in technical explanations'
            ],
            executive_summary: "The candidate struggled with foundational backend concepts. While they showed some basic knowledge, they lacked the depth required for a Junior Backend Developer role. Significant upskilling would be needed."
          },
          cheating_detection: [
            { timestamp: "02:10", description: "Audio input level dropped to zero", severity: "low" }
          ]
        });
        setLoading(false);
        return;
      }

      if (interviewId === '772g0622-g4bd-63f6-c938-668877662222') {
        setInterview({
          interview_id: '772g0622-g4bd-63f6-c938-668877662222',
          candidate_id: 'Dimantha Goonewardena',
          created_at: '2025-12-06T09:15:00',
          status: 'completed',
          video_url: 'https://drive.google.com/uc?export=download&id=1o6wXBqzNep6rQwcEWxBnXesxchrhUQPm',
          transcript: {
            duration_seconds: 2400,
            text: "Interviewer: How would you design a CI/CD pipeline for a microservices architecture?\n\nCandidate: I would use Jenkins or GitHub Actions. Each service would have its own pipeline. We'd run unit tests, build the Docker image, push to a registry, and then deploy to Kubernetes using Helm charts.\n\nInterviewer: Good. How do you handle secrets?\n\nCandidate: We can use Kubernetes Secrets or something like HashiCorp Vault. Never commit them to git."
          },
          analysis: {
            overall_score: 78,
            categories: [
              { name: 'Technical Proficiency', score: 82, feedback: 'Solid grasp of modern DevOps tools and practices.' },
              { name: 'Communication', score: 75, feedback: 'Clear but could be more detailed in explaining the "why" behind choices.' },
              { name: 'Problem Solving', score: 80, feedback: 'Good practical approach to pipeline design.' },
              { name: 'Cultural Fit', score: 75, feedback: 'Aligned with agile practices.' }
            ],
            key_strengths: [
              'Strong practical knowledge of Kubernetes and Docker',
              'Correct security practices regarding secrets management',
              'Familiarity with standard CI/CD tools'
            ],
            areas_for_improvement: [
              'Could elaborate more on monitoring and observability in the pipeline',
              'Discussion on rollback strategies was brief'
            ],
            executive_summary: "A solid candidate for the DevOps role. They have the necessary technical skills and practical experience. With a bit more focus on observability and incident management, they would be a very strong addition to the team."
          },
          cheating_detection: []
        });
        setLoading(false);
        return;
      }

      if (interviewId === '883h1733-h5ce-74g7-d049-779988773333') {
        setInterview({
          interview_id: '883h1733-h5ce-74g7-d049-779988773333',
          candidate_id: 'Dimantha Goonewardena',
          created_at: '2025-12-05T16:45:00',
          status: 'completed',
          video_url: 'https://drive.google.com/uc?export=download&id=1o6wXBqzNep6rQwcEWxBnXesxchrhUQPm',
          transcript: {
            duration_seconds: 1500,
            text: "Interviewer: Tell me about a time you had to prioritize features under a tight deadline.\n\nCandidate: We had a launch coming up and too many features. I used the RICE scoring model to objectively rank them. I also met with stakeholders to manage expectations. We cut 20% of the scope but hit the deadline with a stable release."
          },
          analysis: {
            overall_score: 88,
            categories: [
              { name: 'Product Sense', score: 90, feedback: 'Excellent use of frameworks to make data-driven decisions.' },
              { name: 'Communication', score: 92, feedback: 'Very persuasive and clear stakeholder management.' },
              { name: 'Leadership', score: 85, feedback: 'Took ownership of the difficult decision to cut scope.' },
              { name: 'Technical Understanding', score: 70, feedback: 'Good enough to communicate with engineers, but not deep technical.' }
            ],
            key_strengths: [
              'Data-driven prioritization (RICE model)',
              'Strong stakeholder management skills',
              'Focus on delivery and impact'
            ],
            areas_for_improvement: [
              'Could improve technical vocabulary to better interface with engineering leads'
            ],
            executive_summary: "An excellent Product Manager candidate. They demonstrated strong leadership and prioritization skills essential for the role. Their ability to manage stakeholders and deliver under pressure is a major asset."
          },
          cheating_detection: [
            { timestamp: "08:15", description: "Second person detected in background", severity: "medium" }
          ]
        });
        setLoading(false);
        return;
      }

      try {
        // Use the new summary endpoint
        const response = await apiClient.getInterviewSummary(interviewId);
        if (response.success) {
          const data = response.data;
          // If the backend returns a summary structure, use it directly.
          // Fallback to mock if specific fields are missing (optional, based on backend readiness)
          if (!data.analysis && !data.summary) {
            data.analysis = MOCK_ANALYSIS;
          }

          setInterview(data);

          if (data.status === 'completed' || data.summary) {
            setShowInitialProcessing(false);
          }
        } else {
          setError('Failed to load interview summary');
        }
      } catch (err) {
        console.error('Error fetching interview summary:', err);
        setError('Failed to load interview summary');
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

      // Skip polling for dummy interviews
      const dummyIds = [
        '550e8400-e29b-41d4-a716-446655440000',
        '661f9511-f3ac-52e5-b827-557766551111',
        '772g0622-g4bd-63f6-c938-668877662222',
        '883h1733-h5ce-74g7-d049-779988773333'
      ];

      if (dummyIds.includes(interviewId)) return;

      try {
        const response = await apiClient.getInterviewSummary(interviewId);
        if (response.success) {
          const data = response.data;
          if (!data.analysis && !data.summary) {
            data.analysis = MOCK_ANALYSIS;
          }
          setInterview(data);

          if (data.status === 'completed' || data.summary) {
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

  const videoUrl = interview.video_url || (interview.video_path
    ? `${API_BASE_URL}/media/video${interview.video_path}`
    : '');

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
                  <video
                    src={videoUrl}
                    controls
                    className="w-full h-full object-cover"
                    crossOrigin="anonymous"
                  />
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

            {/* Cheating Detection */}
            <CheatingDetection events={interview.cheating_detection || []} />
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

function CheatingDetection({ events }: { events: any[] }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!events || events.length === 0) return null;

  return (
    <div className="glass-dark rounded-2xl border border-white/10 overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-6 hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-6 h-6 text-red-400" />
          <div className="text-left">
            <h3 className="text-lg font-semibold text-white">Cheating Detection</h3>
            <p className="text-white/50 text-sm">{events.length} suspicious events detected</p>
          </div>
        </div>
        <div className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`}>
          <svg className="w-6 h-6 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {isOpen && (
        <div className="p-6 pt-0 border-t border-white/10">
          <div className="space-y-4 mt-4">
            {events.map((event, idx) => (
              <div key={idx} className="flex items-start gap-4 p-4 rounded-xl bg-white/5 border border-white/5">
                <div className="flex-shrink-0 mt-1">
                  <Clock className="w-5 h-5 text-white/40" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-blue-400 text-sm">{event.timestamp}</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${event.severity === 'high' ? 'bg-red-500/20 text-red-300' :
                      event.severity === 'medium' ? 'bg-orange-500/20 text-orange-300' :
                        'bg-yellow-500/20 text-yellow-300'
                      }`}>
                      {event.severity}
                    </span>
                  </div>
                  <p className="text-white/80">{event.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
