'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Video, VideoOff, Monitor, Circle, X, Maximize2, MessageSquare, FileText } from 'lucide-react';
import CodingChallenge from './CodingChallenge';
import QuestionModal from './QuestionModal';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { getDemoInterviewQuestions } from '@/lib/demoHelpers';
import { API_BASE_URL } from '@/lib/config';
import { getInterviewToken } from '@/lib/interviewToken';

interface ModernInterviewScreenProps {
  participantName: string;
  fromToken?: boolean;
  mode?: 'chat' | 'audio' | 'video';
}

export default function ModernInterviewScreen({ participantName, fromToken = false, mode = 'video' }: ModernInterviewScreenProps) {
  const router = useRouter();
  const { user, getToken } = useAuth();
  const [isCodeEditorOpen, setIsCodeEditorOpen] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(mode === 'video');
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isQuestionModalOpen, setIsQuestionModalOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [interviewId, setInterviewId] = useState<string>('');  // Add interview ID state
  const [showProcessingModal, setShowProcessingModal] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState<string>('');
  const [questionNumber, setQuestionNumber] = useState(1);
  const [isQuestionLoading, setIsQuestionLoading] = useState(false);
  const [isInterviewComplete, setIsInterviewComplete] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [codingChallengeData, setCodingChallengeData] = useState<any>(null);
  const recognitionRef = useRef<any>(null);

  // Initialize Speech Recognition
  useEffect(() => {
    if (typeof globalThis !== 'undefined') {
      const SpeechRecognition = (globalThis as any).SpeechRecognition || (globalThis as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event: any) => {
          let interimTranscript = '';
          let finalTranscript = '';

          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            } else {
              interimTranscript += event.results[i][0].transcript;
            }
          }

          if (finalTranscript) {
            setTranscript(prev => {
              const newTranscript = (prev + ' ' + finalTranscript).trim();
              console.log('📝 STT Update:', newTranscript);
              return newTranscript;
            });
          }
        };

        recognitionRef.current = recognition;
      }
    }
  }, []);

  // Manage Speech Recognition based on recording state
  useEffect(() => {
    if (isRecording && recognitionRef.current) {
      try {
        recognitionRef.current.start();
        console.log('🎙️ Speech Recognition started');
      } catch (e) {
        console.log('Speech recognition already active');
      }
    } else if (!isRecording && recognitionRef.current) {
      recognitionRef.current.stop();
      console.log('Example: Speech Recognition stopped');
    }
  }, [isRecording]);

  // Media recording refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const localVideoRef = useRef<HTMLVideoElement | null>(null);

  const toggleCodeEditor = () => setIsCodeEditorOpen(!isCodeEditorOpen);
  const toggleMute = () => setIsMuted(!isMuted);
  const toggleVideo = () => setIsVideoOn(!isVideoOn);
  const toggleScreenShare = () => setIsScreenSharing(!isScreenSharing);

  const speakQuestion = (text: string) => {
    if ('speechSynthesis' in globalThis) {
      // Cancel any ongoing speech
      globalThis.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);
      // Optional: Select a specific voice if desired, or let browser pick default
      // const voices = window.speechSynthesis.getVoices();
      // utterance.voice = voices.find(v => v.lang === 'en-US') || null;

      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      globalThis.speechSynthesis.speak(utterance);
    }
  };

  const toggleChat = () => setIsChatOpen(!isChatOpen);
  const toggleQuestionModal = () => setIsQuestionModalOpen(!isQuestionModalOpen);

  // Helper to get auth headers
  const getAuthHeaders = () => {
    const token = getToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  };

  // Warn user before leaving page during recording
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isRecording) {
        e.preventDefault();
        e.returnValue = 'You are currently recording an interview. Are you sure you want to leave?';
        return 'You are currently recording an interview. Are you sure you want to leave?';
      }
    };

    globalThis.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      globalThis.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isRecording]);

  // Start Interview on Mount
  useEffect(() => {
    let isActive = true;

    const initInterview = async () => {
      // 1. Get Interview ID
      let currentInterviewId = interviewId;

      if (!currentInterviewId && fromToken) {
        const tokenData = getInterviewToken();
        if (tokenData?.interviewId) {
          currentInterviewId = tokenData.interviewId;
          setInterviewId(currentInterviewId);
          setSessionId(tokenData.sessionId || currentInterviewId);
        }
      }

      // If we still don't have an ID (and not from token), we might need to create one or handle error
      // For now, assume ID is passed or retrieved from token for this flow
      if (!currentInterviewId) {
        console.error('No interview ID found');
        return;
      }

      try {
        // 2. Start Interview (Fetch first question)
        console.log('Starting interview:', currentInterviewId);
        const response = await apiClient.startInterview(currentInterviewId);

        if (response.success && response.data && isActive) {
          const { first_question, question_number, session_id } = response.data;

          setCurrentQuestion(first_question);
          setQuestionNumber(question_number || 1);
          if (session_id) setSessionId(session_id);

          // Open question modal and speak
          setIsQuestionModalOpen(true);
          speakQuestion(first_question);

          // 3. Start Recording
          setTimeout(() => {
            if (isActive) {
              startRecording();
            }
          }, 1000);

        } else {
          console.error('Failed to start interview:', response);
          alert('Failed to start interview session. Please try again.');
        }
      } catch (error) {
        console.error('Error starting interview:', error);
        alert('Error connecting to interview service.');
      }
    };

    initInterview();

    return () => {
      isActive = false;
      cleanupRecording();
      if ('speechSynthesis' in globalThis) {
        globalThis.speechSynthesis.cancel();
      }
    };
  }, [fromToken]); // Run once on mount (dependency on fromToken is stable)


  const handleNextQuestion = async (previousResponseText: string) => {
    if (!interviewId) return;

    setIsQuestionLoading(true);
    try {
      const response = await apiClient.getNextQuestion(interviewId, previousResponseText, questionNumber);

      if (response.success && response.data) {
        if (response.data.status === 'completed' || response.data.message === 'Interview completed') {
          setIsInterviewComplete(true);
          stopRecording();
        } else {
          let nextQuestionText = '';
          let nextQuestionNumber = 0;

          // Check if response is a JSON string (coding question)
          try {
            // The response.data might be the string itself or an object containing next_question
            const rawData = response.data.next_question || response.data;

            if (typeof rawData === 'string' && rawData.trim().startsWith('{')) {
              const parsedData = JSON.parse(rawData);
              if (parsedData.type === 'coding') {
                console.log('👨‍💻 Coding question detected:', parsedData);
                // Set coding challenge data
                if (parsedData.data) {
                  setCodingChallengeData(parsedData.data);
                }

                nextQuestionText = parsedData.text;
                setIsCodeEditorOpen(true);
              } else {
                nextQuestionText = rawData;
              }
            } else {
              nextQuestionText = rawData;
            }
          } catch (e) {
            // Not JSON, treat as normal text
            nextQuestionText = response.data.next_question || response.data;
          }

          // If we didn't extract a question number from the response object, increment locally
          nextQuestionNumber = response.data.question_number || questionNumber + 1;

          setCurrentQuestion(nextQuestionText);
          setQuestionNumber(nextQuestionNumber);

          // Speak new question
          speakQuestion(nextQuestionText);
        }
      }
    } catch (error) {
      console.error('Error getting next question:', error);
      alert('Failed to get next question. Please try again.');
    } finally {
      setIsQuestionLoading(false);
    }
  };

  const startRecording = async () => {
    // Prevent starting if already recording
    if (isRecording || mediaRecorderRef.current) {
      console.log('Already recording, ignoring start request');
      return;
    }

    console.log('🎬 Starting recording...');

    try {
      // Get user media
      console.log('📹 Requesting camera and microphone access...');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });

      console.log('✅ Media stream obtained:', stream);
      streamRef.current = stream;
      recordedChunksRef.current = [];

      // Attach stream to video element
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
        console.log('📺 Stream attached to video element');
      }

      // Check MediaRecorder support and find best mimeType
      console.log('🔍 Checking MediaRecorder support...');
      let mimeType = 'video/webm; codecs=vp8,opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        console.warn(`⚠️ MimeType ${mimeType} not supported, trying alternatives...`);
        if (MediaRecorder.isTypeSupported('video/webm')) {
          mimeType = 'video/webm';
          console.log('✅ Using video/webm');
        } else if (MediaRecorder.isTypeSupported('video/mp4')) {
          mimeType = 'video/mp4';
          console.log('✅ Using video/mp4');
        } else {
          console.error('❌ No supported video mimeType found!');
          throw new Error('Browser does not support video recording');
        }
      } else {
        console.log(`✅ Using mimeType: ${mimeType}`);
      }

      // Create media recorder
      console.log('🎥 Creating MediaRecorder...');
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: mimeType
      });

      console.log('✅ MediaRecorder created, state:', mediaRecorder.state);

      mediaRecorder.ondataavailable = (event) => {
        console.log(`ondataavailable fired, data size: ${event.data.size}`);
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
          console.log(`Recorded chunk ${recordedChunksRef.current.length}, size: ${event.data.size}`);
        } else {
          console.warn('Received empty chunk');
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
      };

      mediaRecorder.onstart = () => {
        console.log('MediaRecorder started');
      };

      mediaRecorder.start(5000); // Record in 5-second chunks for better quality
      mediaRecorderRef.current = mediaRecorder;
      setIsRecording(true);

      // Update session status
      if (sessionId) {
        await apiClient.updateSessionStatus(sessionId, 'recording');
      }
    } catch (error) {
      console.error('❌ Failed to start recording:', error);

      // More specific error messages
      let errorMessage = 'Failed to start recording. ';
      if (error instanceof Error) {
        if (error.message.includes('Permission denied') || error.message.includes('NotAllowedError')) {
          errorMessage += 'Please allow camera and microphone access.';
        } else if (error.message.includes('NotFoundError')) {
          errorMessage += 'No camera or microphone found.';
        } else if (error.message.includes('NotReadableError')) {
          errorMessage += 'Camera or microphone is already in use.';
        } else if (error.message.includes('MediaRecorder')) {
          errorMessage += 'Browser does not support video recording.';
        } else {
          errorMessage += `Error: ${error.message}`;
        }
      } else {
        errorMessage += 'Please check camera/microphone permissions.';
      }

      alert(errorMessage);
    }
  };

  const cleanupRecording = () => {
    console.log('Cleaning up recording...');

    // Stop media recorder if it exists
    if (mediaRecorderRef.current) {
      console.log('Stopping MediaRecorder, state:', mediaRecorderRef.current.state);

      if (mediaRecorderRef.current.state !== 'inactive') {
        try {
          mediaRecorderRef.current.stop();
        } catch (e) {
          console.error('Error stopping recorder:', e);
        }
      }

      // Remove all event handlers to prevent further events
      mediaRecorderRef.current.ondataavailable = null;
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.onerror = null;
      mediaRecorderRef.current = null;
    }

    // Stop and cleanup media stream
    if (streamRef.current) {
      console.log('Stopping media stream tracks');
      streamRef.current.getTracks().forEach(track => {
        track.stop();
        track.enabled = false;
      });
      streamRef.current = null;
    }

    // Clear local video source
    if (localVideoRef.current) {
      localVideoRef.current.srcObject = null;
    }

    setIsRecording(false);
    console.log('Recording cleanup complete');
  };

  const stopRecording = async () => {
    // For token-based interviews, we don't need user authentication
    if (!fromToken && !user) {
      alert('User not authenticated');
      return;
    }

    console.log('Stop recording called');
    console.log('MediaRecorder state:', mediaRecorderRef.current?.state);
    console.log('Current chunks count:', recordedChunksRef.current.length);

    // Create a promise that resolves when the final chunk is received
    const finalChunkPromise = new Promise<void>((resolve) => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        console.log('MediaRecorder is active, setting up final chunk capture...');

        // Keep track of whether we've received the final chunk
        let finalChunkReceived = false;

        // Set up handler to capture the final chunk
        const handleFinalData = (event: BlobEvent) => {
          console.log(`Final dataavailable event: size=${event.data.size}`);
          if (event.data.size > 0) {
            recordedChunksRef.current.push(event.data);
            console.log(`Final chunk received: ${recordedChunksRef.current.length}`);
            finalChunkReceived = true;
          } else {
            console.warn('Final chunk is empty');
          }
        };

        // Set up onstop handler
        mediaRecorderRef.current.onstop = () => {
          console.log('MediaRecorder onstop fired');
          // Wait a bit to ensure ondataavailable completes
          setTimeout(() => {
            console.log(`Final chunk count after stop: ${recordedChunksRef.current.length}, final chunk received: ${finalChunkReceived}`);
            resolve();
          }, 200);
        };

        // Add the final data handler
        mediaRecorderRef.current.addEventListener('dataavailable', handleFinalData);

        // Stop the recorder - this will trigger ondataavailable then onstop
        mediaRecorderRef.current.stop();
        console.log('MediaRecorder.stop() called');
      } else {
        console.log('MediaRecorder is not active, resolving immediately');
        resolve();
      }
    });

    // Wait for the final chunk to be captured
    await finalChunkPromise;

    console.log(`Total chunks captured: ${recordedChunksRef.current.length}`);

    // Now cleanup to prevent any more events
    cleanupRecording();

    try {
      // Get interview_id before uploading chunks
      let finalInterviewIdForChunks = interviewId;
      if (!finalInterviewIdForChunks && fromToken) {
        const tokenData = getInterviewToken();
        finalInterviewIdForChunks = tokenData?.interviewId || '';
      }

      if (!finalInterviewIdForChunks) {
        console.error('Missing interview_id for chunk upload');
        alert('Failed to upload interview: Missing interview_id');
        return;
      }

      if (!sessionId) {
        console.error('Missing session_id for chunk upload');
        alert('Failed to upload interview: Missing session_id');
        return;
      }

      // Upload all chunks sequentially
      const totalChunks = recordedChunksRef.current.length;
      console.log(`Uploading ${totalChunks} chunks for interview ${finalInterviewIdForChunks}...`);

      const headers: Record<string, string> = user ? { ...getAuthHeaders() } : {};
      delete headers['Content-Type'];

      for (let i = 0; i < recordedChunksRef.current.length; i++) {
        const chunk = recordedChunksRef.current[i];
        const chunkFilename = `chunk_${String(i).padStart(4, '0')}.webm`;

        const formData = new FormData();
        formData.append('file', new Blob([chunk], { type: 'video/webm' }), chunkFilename);
        formData.append('interview_id', finalInterviewIdForChunks);
        formData.append('session_id', sessionId);
        formData.append('chunk_index', String(i));
        formData.append('total_chunks', String(totalChunks));

        try {
          const response = await fetch(`${API_BASE_URL}/media/upload_chunk`, {
            method: 'POST',
            headers: headers,
            body: formData
          });

          if (!response.ok) {
            const errorText = await response.text();
            console.error(`Failed to upload chunk ${i}:`, errorText);
          } else {
            console.log(`Uploaded chunk ${i + 1}/${totalChunks}`);
          }
        } catch (error) {
          console.error(`Failed to upload chunk ${i}:`, error);
          // Continue with other chunks even if one fails
        }
      }

      console.log('All chunks uploaded, finalizing...');
      const userId = user?.id || sessionId; // Use sessionId for token-based interviews

      // Use the same interview_id that was used for chunk uploads
      console.log('Finalize request data:', {
        user_id: userId,
        session_id: sessionId,
        candidate_id: participantName,
        interview_id: finalInterviewIdForChunks
      });

      // Finalize upload on media service
      const finalizeResponse = await fetch(`${API_BASE_URL}/media/finalize_upload`, {
        method: 'POST',
        headers: user ? getAuthHeaders() : { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          candidate_id: participantName,
          interview_id: finalInterviewIdForChunks
        })
      });

      const finalizeData = await finalizeResponse.json();
      console.log('Finalize response:', finalizeData);

      if (finalizeData.status === 'done') {
        // Use the interview_id that was used for chunk uploads (consistent throughout)
        const finalInterviewId = finalInterviewIdForChunks || finalizeData.interview_id;
        const videoPath = finalizeData.file;
        console.log('Final Interview ID:', finalInterviewId, 'Video Path:', videoPath);

        if (!finalInterviewId) {
          console.error('No interview_id available for completion');
          alert('Failed to create interview record. Please try again.');
          return;
        }

        // Update interview status to processing (only if we have a valid sessionId)
        if (sessionId && sessionId !== '') {
          try {
            await apiClient.updateInterviewStatus(sessionId, 'processing');
            console.log('Updated session status to processing');
          } catch (error) {
            console.error('Failed to update session status:', error);
          }
        } else {
          console.warn('No valid sessionId available, skipping status update');
        }

        // Trigger transcription in background (don't await)
        // Use Docker internal network hostname for audio-ai service to access media
        // Video path format: /user_id/filename.mp4 -> http://media-service:8080/video/user_id/filename.mp4
        const videoUrl = `http://media-service:8080/video${videoPath}`;
        console.log('Transcribing video from:', videoUrl);
        apiClient.audioTranscribe({
          media_url: videoUrl,
          session_id: sessionId,
          candidate_id: participantName
        }).then(async (transcriptResponse: any) => {
          // Update interview with transcript
          if (transcriptResponse?.status === 'success' || transcriptResponse?.data) {
            const data = transcriptResponse.data || transcriptResponse;
            console.log('📝 Updating interview transcript:', {
              interviewId: finalInterviewId,
              transcriptData: {
                text: data.transcript,
                word_count: data.word_count,
                duration_seconds: data.duration_seconds,
                language: data.language
              }
            });

            await apiClient.updateInterviewTranscript(finalInterviewId, {
              text: data.transcript,
              word_count: data.word_count,
              duration_seconds: data.duration_seconds,
              language: data.language
            });

            console.log('✅ Transcript updated successfully');
            // Update status to completed after transcript is saved
            await apiClient.updateInterviewStatus(finalInterviewId, 'completed');
            console.log('✅ Interview status updated to completed');
          } else {
            console.warn('⚠️ No transcript data available:', transcriptResponse);
          }
        }).catch(err => {
          console.error('Transcription failed:', err);
        });

        await fetch(
          `${API_BASE_URL}/orchestration/interviews/trigger-analyses/${finalInterviewId}`,
          { method: 'POST', headers: getAuthHeaders() }
        );

        // Clear recorded chunks to free memory
        recordedChunksRef.current = [];

        // For token-based interviews, clear the token after completion
        if (fromToken) {
          console.log('🧹 Clearing interview token after completion');
          const { clearInterviewToken } = await import('@/lib/interviewToken');
          clearInterviewToken();

          // Redirect candidates to thank you page instead of interview summary
          console.log('Redirecting candidate to thank you page...');
          router.push(`/interview-thank-you?id=${finalInterviewId}`);
        } else {
          // Redirect recruiters to interview summary page with processing state
          console.log('Redirecting to interview summary...');
          router.push(`/interview-summary?id=${finalInterviewId}&processing=true`);
        }
      } else if (finalizeData.error) {
        // Handle error from media service
        console.error('Finalize error:', finalizeData.error);
        alert(`Failed to finalize interview: ${finalizeData.error}`);
      }
    } catch (error) {
      console.error('Failed to finalize interview:', error);
      alert('Failed to save interview. Please try again.');
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <div className="absolute inset-0 flex flex-col">
      {/* Interview Status Bar */}
      <div className="absolute top-6 left-0 right-0 flex justify-center z-10">
        <motion.div
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass-dark rounded-xl shadow-lg flex items-center"
        >
          <div className="px-4 py-2 flex items-center space-x-3 border-r border-white/10">
            <div className={`w-2 h-2 rounded-full animate-pulse ${isRecording ? 'bg-red-400' : 'bg-green-400'}`} />
            <span className="text-white/80 text-sm font-medium">
              {isRecording ? 'Recording in Progress' : 'Interview in Progress'}
            </span>
          </div>
          <button
            className="px-4 py-2 text-white/90 text-sm font-medium hover:bg-red-500/20 transition-all rounded-r-xl disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={stopRecording}
          >
            End Interview
          </button>
        </motion.div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 relative pt-24">
        <AnimatePresence>
          {!isCodeEditorOpen ? (
            /* Video Layout */
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0"
            >
              {/* Main Video (Full Screen) */}
              <div className="absolute inset-0 flex items-center justify-center p-6">
                {/* Main Video Container */}
                <div className="relative w-full max-w-[1600px] mx-auto aspect-video">
                  {/* Main Video (Participant) */}
                  <motion.div
                    className="absolute inset-0 rounded-2xl overflow-hidden bg-gray-800/90 border border-white/10"
                    layoutId="mainVideo"
                    transition={{
                      type: "spring",
                      stiffness: 120,
                      damping: 25,
                      mass: 1.5,
                      duration: 1.2
                    }}
                  >
                    {/* Video Element */}
                    <video
                      ref={localVideoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover"
                    />

                    {/* Live Transcript Overlay */}
                    {transcript && (
                      <div className="absolute bottom-20 left-0 right-0 flex justify-center px-4 pointer-events-none">
                        <div className="bg-black/60 backdrop-blur-md px-6 py-3 rounded-2xl max-w-3xl text-center border border-white/10 shadow-lg">
                          <p className="text-white/90 text-lg font-medium leading-relaxed">
                            {transcript.split(' ').slice(-15).join(' ')}
                            <span className="animate-pulse">|</span>
                          </p>
                          <p className="text-white/40 text-xs mt-1 uppercase tracking-wider font-semibold">
                            Live Transcript
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Fallback when no video stream */}
                    {!isRecording && (
                      <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800/50 to-gray-900/50">
                        <div className="flex flex-col items-center gap-4">
                          <div className="w-32 h-32 rounded-full bg-gray-700/50 flex items-center justify-center">
                            {mode === 'audio' ? (
                              <Mic className="w-16 h-16 text-white/50" />
                            ) : mode === 'chat' ? (
                              <MessageSquare className="w-16 h-16 text-white/50" />
                            ) : (
                              <svg className="w-16 h-16 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                            )}
                          </div>
                          {mode !== 'video' && (
                            <p className="text-white/60 font-medium">
                              {mode === 'audio' ? 'Audio Only Interview' : 'Chat Interview'}
                            </p>
                          )}
                        </div>
                      </div>
                    )}
                    <div className="absolute bottom-4 left-4 glass-dark px-4 py-2 rounded-xl text-white/90 text-sm font-medium shadow-lg">
                      You
                      <div className="flex items-center mt-1 space-x-2">
                        <div className={`w-2 h-2 rounded-full ${isMuted ? 'bg-red-400' : 'bg-green-400'} animate-pulse`}></div>
                        <span className="text-white/60 text-xs">
                          {isMuted ? 'Muted' : 'Speaking'}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          ) : (
            /* Code Editor Layout */
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="w-full h-full"
            >
              <div className="flex gap-4 px-6 py-4">
                <motion.div
                  className="w-48 h-32 glass-dark rounded-xl overflow-hidden relative shadow-lg"
                  layoutId="mainVideo"
                  whileHover={{ scale: 1.05 }}
                >
                  <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800/50 to-gray-900/50">
                    <div className="w-12 h-12 rounded-full bg-gray-700/50 flex items-center justify-center">
                      <svg className="w-6 h-6 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                  </div>
                  <div className="absolute bottom-2 left-2 glass-dark px-2 py-1 rounded-lg text-white/90 text-xs">
                    Candidate
                  </div>
                </motion.div>

              </div>

              <motion.div
                initial={{ y: 200, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                exit={{ y: 200, opacity: 0 }}
                transition={{
                  type: "spring",
                  stiffness: 100,
                  damping: 20,
                  mass: 1,
                  delay: 0.4,
                  duration: 1
                }}
              >
                <CodingChallenge
                  userType="candidate"
                  participantName={participantName}
                  videoStream={streamRef.current}
                  challengeData={codingChallengeData}
                  onComplete={() => {
                    setIsCodeEditorOpen(false);
                    handleNextQuestion('Code Submitted');
                  }}
                />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Control Bar */}
      <div className="fixed bottom-8 left-0 right-0 flex justify-center z-50">
        <motion.div
          initial={{ y: 50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass-dark px-3 py-3 rounded-2xl flex items-center space-x-4 shadow-lg"
        >
          <button
            onClick={toggleMute}
            className={`p-4 rounded-xl transition-all ${isMuted ? 'bg-red-500/20 hover:bg-red-500/30' : 'hover:bg-white/10'
              }`}
          >
            {isMuted ? <MicOff className="w-6 h-6 text-white" /> : <Mic className="w-6 h-6 text-white" />}
          </button>

          <button
            onClick={toggleVideo}
            disabled={mode !== 'video'}
            className={`p-4 rounded-xl transition-all ${isVideoOn ? 'hover:bg-white/10' : 'bg-red-500/20 hover:bg-red-500/30'} ${mode !== 'video' ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isVideoOn ? <Video className="w-6 h-6 text-white" /> : <VideoOff className="w-6 h-6 text-white" />}
          </button>

          <div className="h-8 w-px bg-white/20 mx-2" />

          <button
            onClick={toggleCodeEditor}
            className={`p-4 rounded-xl transition-all ${isCodeEditorOpen ? 'bg-primary-200/20 hover:bg-primary-200/30' : 'hover:bg-white/10'
              }`}
          >
            <Maximize2 className="w-6 h-6 text-white" />
          </button>

          <button
            onClick={toggleChat}
            className={`p-4 rounded-xl transition-all ${isChatOpen ? 'bg-primary-200/20 hover:bg-primary-200/30' : 'hover:bg-white/10'
              }`}
          >
            <MessageSquare className="w-6 h-6 text-white" />
          </button>

          <div className="h-8 w-px bg-white/20 mx-2" />

          <button
            onClick={toggleQuestionModal}
            className={`p-4 rounded-xl transition-all relative ${isQuestionModalOpen ? 'bg-purple-500/20 hover:bg-purple-500/30' : 'hover:bg-white/10'
              }`}
            title="View Interview Questions"
          >
            <FileText className="w-6 h-6 text-white" />
          </button>
        </motion.div>
      </div>

      {/* Chat Sidebar */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div
            initial={{ x: 400 }}
            animate={{ x: 0 }}
            exit={{ x: 400 }}
            className="absolute top-0 right-0 w-96 h-full glass-dark border-l border-white/10"
          >
            <div className="p-4 border-b border-white/10 flex justify-between items-center">
              <h3 className="text-white font-medium">Chat</h3>
              <button
                onClick={toggleChat}
                className="p-2 hover:bg-white/10 rounded-lg transition-all"
              >
                <X className="w-5 h-5 text-white" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Question Modal */}
      <QuestionModal
        isOpen={isQuestionModalOpen}
        question={currentQuestion}
        questionNumber={questionNumber}
        onNext={async () => {
          // Use the captured client-side transcript
          const responseText = transcript || "Audio response provided (STT unavailable).";
          console.log('📤 Sending response:', responseText);

          await handleNextQuestion(responseText);

          // Clear transcript for the next question
          setTranscript('');
        }}
        isLoading={isQuestionLoading}
      />

      {/* Processing Modal */}
      <AnimatePresence>
        {showProcessingModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
          >
            <div className="bg-gray-900 rounded-2xl p-8 max-w-md w-full text-center border border-white/10">
              <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-6" />
              <h3 className="text-xl font-bold text-white mb-2">Processing Interview</h3>
              <p className="text-gray-400">
                Please wait while we analyze your interview session and generate the summary...
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
