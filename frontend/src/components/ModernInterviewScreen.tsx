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
}

export default function ModernInterviewScreen({ participantName, fromToken = false }: ModernInterviewScreenProps) {
  const router = useRouter();
  const { user, getToken } = useAuth();
  const [isCodeEditorOpen, setIsCodeEditorOpen] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isQuestionModalOpen, setIsQuestionModalOpen] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [interviewId, setInterviewId] = useState<string>('');  // Add interview ID state
  const [showProcessingModal, setShowProcessingModal] = useState(false);
  const [interviewQuestions, setInterviewQuestions] = useState<any[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  
  // Media recording refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const localVideoRef = useRef<HTMLVideoElement | null>(null);

  const toggleCodeEditor = () => setIsCodeEditorOpen(!isCodeEditorOpen);
  const toggleMute = () => setIsMuted(!isMuted);
  const toggleVideo = () => setIsVideoOn(!isVideoOn);
  const toggleScreenShare = () => setIsScreenSharing(!isScreenSharing);

  // Test MediaRecorder functionality
  const testRecording = async () => {
    try {
      console.log('Testing MediaRecorder...');
      
      // Check MediaRecorder support
      if (!window.MediaRecorder) {
        throw new Error('MediaRecorder not supported');
      }
      
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      
      console.log('Got media stream:', stream);
      
      // Check supported mimeTypes
      const supportedTypes = [
        'video/webm; codecs=vp8,opus',
        'video/webm',
        'video/mp4',
        'video/webm; codecs=vp9,opus'
      ];
      
      const supportedType = supportedTypes.find(type => MediaRecorder.isTypeSupported(type));
      console.log('Supported mimeType:', supportedType);
      
      if (!supportedType) {
        throw new Error('No supported video format found');
      }
      
      // Create MediaRecorder
      const recorder = new MediaRecorder(stream, { mimeType: supportedType });
      const testChunks: Blob[] = [];
      
      recorder.ondataavailable = (event) => {
        console.log('Test ondataavailable:', event.data.size);
        if (event.data.size > 0) {
          testChunks.push(event.data);
        }
      };
      
      recorder.onstop = () => {
        console.log('Test recording stopped, chunks:', testChunks.length);
        const result = testChunks.length > 0 ? 'SUCCESS' : 'FAILED - No chunks';
        console.log('Test result:', result);
        alert(`Recording test: ${result}`);
        
        // Cleanup
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.onerror = (event) => {
        console.error('Test recorder error:', event);
        alert('Recording test FAILED - Error occurred');
      };
      
      // Start recording for 3 seconds
      recorder.start(1000); // 1 second chunks
      setTimeout(() => {
        recorder.stop();
      }, 3000);
      
    } catch (error) {
      console.error('Recording test failed:', error);
      alert(`Recording test FAILED: ${error instanceof Error ? error.message : String(error)}`);
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

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [isRecording]);

  // Load interview questions on mount
  useEffect(() => {
    const loadQuestions = async () => {
      try {
        // For demo purposes, use local demo questions
        // In production, this would fetch from AI service
        const demoQuestions = getDemoInterviewQuestions();
        setInterviewQuestions(demoQuestions);
        console.log('Demo interview questions loaded:', demoQuestions.length);
      } catch (error) {
        console.error('Failed to load interview questions:', error);
        // Fallback to demo questions
        setInterviewQuestions(getDemoInterviewQuestions());
      }
    };

    loadQuestions();
  }, []);

  // Create interview session on mount and auto-start recording
  useEffect(() => {
    let isActive = true;
    
    const createSessionAndStart = async () => {
      // Handle token-based interviews
      if (fromToken) {
        const tokenData = getInterviewToken();
        console.log('🔍 DEBUG: Token-based interview detected');
        console.log('🔍 DEBUG: Token data retrieved:', tokenData);
        console.log('🔍 DEBUG: Session storage contents:', sessionStorage.getItem('interview_token_data'));
        
        if (tokenData && isActive) {
          console.log('✅ Using token-based session:', tokenData.sessionId, 'interview:', tokenData.interviewId);
          setSessionId(tokenData.sessionId);
          setInterviewId(tokenData.interviewId);
          
          // Auto-start recording after session is set
          setTimeout(() => {
            if (isActive) {
              console.log('🎬 Starting recording for token-based interview...');
              startRecording();
            }
          }, 500);
        } else {
          console.error('❌ No valid token data found for token-based interview');
          console.error('❌ Token data:', tokenData);
          console.error('❌ Is active:', isActive);
        }
        return;
      }
      
      // Handle regular authenticated interviews
      if (!user || !isActive) return;
      
      // Don't create a new session if we already have one
      if (sessionId) {
        console.log('Session already exists:', sessionId);
        return;
      }
      
      try {
        console.log('Creating interview session for user:', user.id, 'participant:', participantName);
        const response = await apiClient.createInterviewSession(
          user.id,
          participantName
        );
        
        console.log('Session creation response:', response);
        
        if (response.success && isActive) {
          const newSessionId = response.data?.session_id || response.data?.interview_id;
          console.log('Setting session ID to:', newSessionId);
          setSessionId(newSessionId);
          console.log('Interview session created:', newSessionId);
          
          // Auto-start recording after session is created
          setTimeout(() => {
            if (isActive) {
              startRecording();
            }
          }, 500);
        } else {
          console.error('Session creation failed or component unmounted:', response);
        }
      } catch (error) {
        console.error('Failed to create interview session:', error);
      }
    };
    
    createSessionAndStart();
    
    // Cleanup on unmount
    return () => {
      isActive = false;
      console.log('Component unmounting, cleaning up recording...');
      cleanupRecording();
    };
  }, [user, participantName, fromToken]);

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

      // Reset chunks on server and wait for confirmation
      const userId = user?.id || sessionId; // Use sessionId for token-based interviews
      console.log('🔄 Resetting chunks for user:', userId);
      
      if (userId) {
        try {
          const resetResponse = await fetch(`${API_BASE_URL}/media/reset_chunks`, {
            method: 'POST',
            headers: user ? getAuthHeaders() : { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
          });
          
          if (!resetResponse.ok) {
            console.warn('⚠️ Failed to reset chunks, continuing anyway:', resetResponse.status);
          } else {
            console.log('✅ Chunks reset successfully');
          }
          
          // Wait a bit to ensure filesystem is synced
          await new Promise(resolve => setTimeout(resolve, 100));
        } catch (resetError) {
          console.warn('⚠️ Chunk reset failed, continuing anyway:', resetError);
        }
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
      // Upload all chunks sequentially
      console.log(`Uploading ${recordedChunksRef.current.length} chunks...`);
      
      const headers: Record<string, string> = user ? { ...getAuthHeaders() } : {};
      delete headers['Content-Type'];

      for (let i = 0; i < recordedChunksRef.current.length; i++) {
        const chunk = recordedChunksRef.current[i];
        const chunkFilename = `chunk_${String(i).padStart(4, '0')}.webm`;
        
        const formData = new FormData();
        formData.append('file', new Blob([chunk], { type: 'video/webm' }), chunkFilename);
        formData.append('user_id', user?.id || sessionId); // Use sessionId for token-based interviews
        
        try {
          const response = await fetch(`${API_BASE_URL}/media/upload_chunk`, {
            method: 'POST',
            headers: headers,
            body: formData
          });
          
          if (!response.ok) {
            console.error(`Failed to upload chunk ${i}:`, await response.text());
          } else {
            console.log(`Uploaded chunk ${i + 1}/${recordedChunksRef.current.length}`);
          }
        } catch (error) {
          console.error(`Failed to upload chunk ${i}:`, error);
          // Continue with other chunks even if one fails
        }
      }

      console.log('All chunks uploaded, finalizing...');
      const userId = user?.id || sessionId; // Use sessionId for token-based interviews
      console.log('Finalize request data:', {
        user_id: userId,
        session_id: sessionId,
        candidate_id: participantName
      });

      // Finalize upload on media service
      const finalizeResponse = await fetch(`${API_BASE_URL}/media/finalize_upload`, {
        method: 'POST',
        headers: user ? getAuthHeaders() : { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          candidate_id: participantName
        })
      });

      const finalizeData = await finalizeResponse.json();
      console.log('Finalize response:', finalizeData);
      
      if (finalizeData.status === 'done') {
        // Use existing interview ID for token-based interviews, or get new one from media service
        const finalInterviewId = fromToken ? interviewId : finalizeData.interview_id;
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
                    {/* Fallback when no video stream */}
                    {!isRecording && (
                      <div className="absolute inset-0 w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800/50 to-gray-900/50">
                      <div className="w-32 h-32 rounded-full bg-gray-700/50 flex items-center justify-center">
                        <svg className="w-16 h-16 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
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
                <CodingChallenge userType="candidate" participantName={participantName} />
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
            className={`p-4 rounded-xl transition-all ${
              isMuted ? 'bg-red-500/20 hover:bg-red-500/30' : 'hover:bg-white/10'
            }`}
          >
            {isMuted ? <MicOff className="w-6 h-6 text-white" /> : <Mic className="w-6 h-6 text-white" />}
          </button>

          <button
            onClick={toggleVideo}
            className={`p-4 rounded-xl transition-all ${
              !isVideoOn ? 'bg-red-500/20 hover:bg-red-500/30' : 'hover:bg-white/10'
            }`}
          >
            {isVideoOn ? <Video className="w-6 h-6 text-white" /> : <VideoOff className="w-6 h-6 text-white" />}
          </button>

          <div className="h-8 w-px bg-white/20 mx-2" />

          <button
            onClick={toggleCodeEditor}
            className={`p-4 rounded-xl transition-all ${
              isCodeEditorOpen ? 'bg-primary-200/20 hover:bg-primary-200/30' : 'hover:bg-white/10'
            }`}
          >
            <Maximize2 className="w-6 h-6 text-white" />
          </button>

          <button
            onClick={toggleChat}
            className={`p-4 rounded-xl transition-all ${
              isChatOpen ? 'bg-primary-200/20 hover:bg-primary-200/30' : 'hover:bg-white/10'
            }`}
          >
            <MessageSquare className="w-6 h-6 text-white" />
          </button>

          <div className="h-8 w-px bg-white/20 mx-2" />

          <button
            onClick={toggleQuestionModal}
            className={`p-4 rounded-xl transition-all relative ${
              isQuestionModalOpen ? 'bg-purple-500/20 hover:bg-purple-500/30' : 'hover:bg-white/10'
            }`}
            title="View Interview Questions"
          >
            <FileText className="w-6 h-6 text-white" />
            {interviewQuestions.length > 0 && (
              <span className="absolute -top-1 -right-1 bg-purple-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {interviewQuestions.length}
              </span>
            )}
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
    
      {/* Processing Modal */}
      <AnimatePresence>
        {showProcessingModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 flex items-center justify-center z-[100]"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-dark p-8 rounded-2xl max-w-md text-center"
            >
              <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <h3 className="text-white text-xl font-semibold mb-2">Processing Your Interview</h3>
              <p className="text-white/70 mb-4">
                Your interview is being transcribed and analyzed. This may take 5-10 minutes.
              </p>
              <p className="text-white/60 text-sm">
                Check your dashboard for results. Redirecting...
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Question Modal */}
      <QuestionModal
        isOpen={isQuestionModalOpen}
        onClose={() => setIsQuestionModalOpen(false)}
        questions={interviewQuestions}
        currentQuestionIndex={currentQuestionIndex}
        onQuestionChange={setCurrentQuestionIndex}
      />
    </div>
  );
}
