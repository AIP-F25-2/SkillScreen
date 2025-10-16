'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { motion } from 'framer-motion';
import { ArrowLeft, Download, Clock, FileText, CheckCircle } from 'lucide-react';

export default function InterviewSummaryPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const interviewId = searchParams?.get('id');
  const isProcessingParam = searchParams?.get('processing') === 'true';

  const [interview, setInterview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInitialProcessing, setShowInitialProcessing] = useState(isProcessingParam);

  useEffect(() => {
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

    fetchInterview();

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
  }, [interviewId, isProcessingParam]);

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
            onClick={() => router.push('/candidate')}
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
    ? `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'}/media/video${interview.video_path}`
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

