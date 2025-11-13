'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { getInterviewToken } from '@/lib/interviewToken';

export default function InterviewSetup() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const videoRef = useRef<HTMLVideoElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  const { user } = useAuth();
  const [candidateName, setCandidateName] = useState('');
  const [permissions, setPermissions] = useState({
    camera: false,
    microphone: false,
  });
  const [devices, setDevices] = useState({
    cameras: [] as MediaDeviceInfo[],
    microphones: [] as MediaDeviceInfo[],
  });
  const [selectedDevices, setSelectedDevices] = useState({
    camera: '',
    microphone: '',
  });
  const [audioLevel, setAudioLevel] = useState(0);
  const [isTestingAudio, setIsTestingAudio] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState('');
  const [fromToken, setFromToken] = useState(false);
  const [sessionId, setSessionId] = useState('');

  // Check if coming from email token
  useEffect(() => {
    const isFromToken = searchParams?.get('fromToken') === 'true';
    setFromToken(isFromToken);

    if (isFromToken) {
      // Get candidate data from token
      const tokenData = getInterviewToken();
      if (tokenData) {
        setCandidateName(tokenData.candidateName);
        setSessionId(tokenData.sessionId);
      } else {
        // No valid token, redirect to error
        router.push('/');
      }
    } else if (user) {
      // Recruiter or authenticated user
      setCandidateName(user.name || '');
    }
  }, [searchParams, user, router]);

  // Initialize media devices
  useEffect(() => {
    loadDevices();
    return () => {
      // Cleanup media streams on unmount
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  const loadDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const cameras = devices.filter(d => d.kind === 'videoinput');
      const microphones = devices.filter(d => d.kind === 'audioinput');
      
      setDevices({ cameras, microphones });
      
      if (cameras.length > 0 && !selectedDevices.camera) {
        setSelectedDevices(prev => ({ ...prev, camera: cameras[0].deviceId }));
      }
      if (microphones.length > 0 && !selectedDevices.microphone) {
        setSelectedDevices(prev => ({ ...prev, microphone: microphones[0].deviceId }));
      }
    } catch (error) {
      console.error('Error loading devices:', error);
      setError('Unable to load media devices');
    }
  };

  const requestMediaPermissions = async () => {
    try {
      setError('');
      
      // Stop any existing streams first
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      const constraints: MediaStreamConstraints = {
        video: selectedDevices.camera 
          ? { deviceId: { exact: selectedDevices.camera } } 
          : { facingMode: 'user' },
        audio: selectedDevices.microphone 
          ? { deviceId: { exact: selectedDevices.microphone } } 
          : true,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);

      streamRef.current = stream;

      // Set up video preview
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play().catch(err => console.error('Error playing video:', err));
        };
      }

      // Set up audio level monitoring
      setupAudioMonitoring(stream);

      setPermissions({
        camera: true,
        microphone: true,
      });

      // Reload devices to get labels
      await loadDevices();
    } catch (error: any) {
      console.error('Error requesting permissions:', error);
      let errorMessage = 'Please allow camera and microphone access to continue';
      
      if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
        errorMessage = 'Camera and microphone access was denied. Please allow access in your browser settings.';
      } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
        errorMessage = 'No camera or microphone found. Please connect a device and try again.';
      } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
        errorMessage = 'Camera or microphone is already in use by another application.';
      }
      
      setError(errorMessage);
      setPermissions({
        camera: false,
        microphone: false,
      });
    }
  };

  const setupAudioMonitoring = (stream: MediaStream) => {
    try {
      // Create audio context
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      const audioContext = new AudioContextClass();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);
      
      analyser.smoothingTimeConstant = 0.8;
      analyser.fftSize = 1024;
      
      microphone.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      // Start monitoring
      updateAudioLevel();
    } catch (error) {
      console.error('Error setting up audio monitoring:', error);
    }
  };

  const updateAudioLevel = () => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);
    
    const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
    const normalized = Math.min(100, (average / 255) * 200);
    
    setAudioLevel(normalized);
    animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
  };

  const changeDevice = async (type: 'camera' | 'microphone', deviceId: string) => {
    if (!permissions.camera && !permissions.microphone) {
      return; // Can't change devices without permissions
    }

    try {
      setError('');
      
      // Update selected device
      const newSelectedDevices = { ...selectedDevices, [type]: deviceId };
      setSelectedDevices(newSelectedDevices);
      
      // Stop current stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      // Request new stream with updated device
      const constraints: MediaStreamConstraints = {
        video: type === 'camera' 
          ? { deviceId: { exact: deviceId } }
          : (newSelectedDevices.camera ? { deviceId: { exact: newSelectedDevices.camera } } : true),
        audio: type === 'microphone'
          ? { deviceId: { exact: deviceId } }
          : (newSelectedDevices.microphone ? { deviceId: { exact: newSelectedDevices.microphone } } : true),
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.onloadedmetadata = () => {
          videoRef.current?.play().catch(err => console.error('Error playing video:', err));
        };
      }

      setupAudioMonitoring(stream);

      setPermissions({
        camera: true,
        microphone: true,
      });

      await loadDevices();
    } catch (error) {
      console.error('Error changing device:', error);
      setError('Failed to switch device. Please try again.');
      setPermissions({
        camera: false,
        microphone: false,
      });
    }
  };

  const testAudio = () => {
    setIsTestingAudio(true);
    setTimeout(() => setIsTestingAudio(false), 3000);
  };

  const handleJoinInterview = () => {
    if (!candidateName.trim()) {
      setError('Please enter your name');
      return;
    }

    if (!permissions.camera || !permissions.microphone) {
      setError('Please enable camera and microphone access');
      return;
    }

    // Clean up streams before navigating
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    // Navigate to interview with secure token-based flow
    if (fromToken) {
      // Token-based flow - use token data from session storage, no sensitive data in URL
      router.push('/interview?fromToken=true');
    } else {
      // Regular flow - still use ID for non-token users
      const interviewId = searchParams?.get('id') || 'interview-123';
      router.push(`/interview?id=${interviewId}&name=${encodeURIComponent(candidateName)}`);
    }
  };

  const handleCancel = () => {
    // Clean up streams before navigating back
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    // Navigate back or to home
    // Token-based users cannot go back - they must complete or exit
    if (fromToken) {
      if (confirm('Are you sure you want to exit? You will need a new link to restart the interview.')) {
        router.push('/');
      }
    } else if (window.history.length > 1) {
      router.back();
    } else {
      router.push(user ? '/recruiter' : '/');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0A0A0A] via-[#1E1E1E] to-[#0A0A0A] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-5xl"
        style={{ transform: 'scale(0.9)' }}
      >
        <div className="bg-black/40 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/10 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-white/5 to-white/10 px-8 py-6 border-b border-white/10">
            <h1 className="text-3xl font-bold text-white mb-2">Setup Your Interview</h1>
            <p className="text-white/60">Test your camera and microphone before joining</p>
          </div>

          <div className="p-8">
            <div className="grid md:grid-cols-2 gap-8">
              {/* Left Column - Video Preview */}
              <div className="space-y-6">
                {/* Video Preview */}
                <div className="relative aspect-video bg-black/60 rounded-2xl overflow-hidden border border-white/10">
                  {permissions.camera ? (
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      muted
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center">
                      <div className="w-20 h-20 rounded-full bg-white/10 flex items-center justify-center mb-4">
                        <svg className="w-10 h-10 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <p className="text-white/60 text-sm">Camera preview will appear here</p>
                    </div>
                  )}
                  
                  {/* Status Badge */}
                  {permissions.camera && (
                    <div className="absolute top-4 right-4">
                      <div className="bg-green-500/20 backdrop-blur-sm border border-green-500/30 px-3 py-1.5 rounded-full flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                        <span className="text-green-300 text-xs font-medium">Live</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Device Selection */}
                <div className="space-y-4">
                  {/* Camera Selection */}
                  <div className="space-y-2">
                    <label className="text-white/80 text-sm font-medium flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Camera
                    </label>
                    <select
                      value={selectedDevices.camera}
                      onChange={(e) => changeDevice('camera', e.target.value)}
                      disabled={!permissions.camera}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-white/30 disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ color: permissions.camera ? 'white' : 'rgba(255,255,255,0.4)' }}
                    >
                      {devices.cameras.length > 0 ? (
                        devices.cameras.map((device) => (
                          <option key={device.deviceId} value={device.deviceId} style={{ color: 'black' }}>
                            {device.label || `Camera ${devices.cameras.indexOf(device) + 1}`}
                          </option>
                        ))
                      ) : (
                        <option value="" style={{ color: 'black' }}>No cameras available</option>
                      )}
                    </select>
                  </div>

                  {/* Microphone Selection */}
                  <div className="space-y-2">
                    <label className="text-white/80 text-sm font-medium flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                      Microphone
                    </label>
                    <select
                      value={selectedDevices.microphone}
                      onChange={(e) => changeDevice('microphone', e.target.value)}
                      disabled={!permissions.microphone}
                      className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-white/30 disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ color: permissions.microphone ? 'white' : 'rgba(255,255,255,0.4)' }}
                    >
                      {devices.microphones.length > 0 ? (
                        devices.microphones.map((device) => (
                          <option key={device.deviceId} value={device.deviceId} style={{ color: 'black' }}>
                            {device.label || `Microphone ${devices.microphones.indexOf(device) + 1}`}
                          </option>
                        ))
                      ) : (
                        <option value="" style={{ color: 'black' }}>No microphones available</option>
                      )}
                    </select>
                  </div>
                </div>
              </div>

              {/* Right Column - Settings & Controls */}
              <div className="space-y-6">
                {/* Name Input - Editable for non-token users, read-only for token users */}
                <div className="space-y-2">
                  <label className="text-white/80 text-sm font-medium">Your Name</label>
                  <input
                    type="text"
                    value={candidateName}
                    onChange={(e) => setCandidateName(e.target.value)}
                    placeholder="Enter your full name"
                    disabled={fromToken}
                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-white/30 disabled:opacity-70 disabled:cursor-not-allowed"
                  />
                  {fromToken && (
                    <p className="text-white/40 text-xs">Name from your interview invitation</p>
                  )}
                </div>

                {/* Audio Level Indicator */}
                <div className="space-y-3">
                  <label className="text-white/80 text-sm font-medium flex items-center justify-between">
                    <span>Audio Level</span>
                    {permissions.microphone && (
                      <span className="text-xs text-white/40">Speak to test</span>
                    )}
                  </label>
                  <div className="h-3 bg-white/5 rounded-full overflow-hidden border border-white/10">
                    <motion.div
                      className={`h-full rounded-full transition-all duration-100 ${
                        audioLevel > 60 ? 'bg-green-500' : audioLevel > 30 ? 'bg-yellow-500' : 'bg-blue-500'
                      }`}
                      style={{ width: `${audioLevel}%` }}
                      animate={{
                        opacity: permissions.microphone ? 1 : 0.3,
                      }}
                    />
                  </div>
                </div>

                {/* Permission Status */}
                <div className="space-y-3">
                  <h3 className="text-white font-medium">Permission Status</h3>
                  
                  <div className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        permissions.camera ? 'bg-green-500/20' : 'bg-red-500/20'
                      }`}>
                        <svg className={`w-5 h-5 ${permissions.camera ? 'text-green-400' : 'text-red-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <span className="text-white">Camera</span>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      permissions.camera
                        ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                        : 'bg-red-500/20 text-red-300 border border-red-500/30'
                    }`}>
                      {permissions.camera ? 'Granted' : 'Required'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-white/5 border border-white/10 rounded-xl">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        permissions.microphone ? 'bg-green-500/20' : 'bg-red-500/20'
                      }`}>
                        <svg className={`w-5 h-5 ${permissions.microphone ? 'text-green-400' : 'text-red-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        </svg>
                      </div>
                      <span className="text-white">Microphone</span>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      permissions.microphone
                        ? 'bg-green-500/20 text-green-300 border border-green-500/30'
                        : 'bg-red-500/20 text-red-300 border border-red-500/30'
                    }`}>
                      {permissions.microphone ? 'Granted' : 'Required'}
                    </span>
                  </div>
                </div>

                {/* Error Message */}
                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl"
                    >
                      <p className="text-red-300 text-sm">{error}</p>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Action Buttons */}
                <div className="space-y-3">
                  {/* Enable Camera & Microphone Button - Always visible */}
                  <button
                    onClick={requestMediaPermissions}
                    disabled={permissions.camera && permissions.microphone}
                    className={`w-full px-6 py-4 rounded-xl font-semibold transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] ${
                      permissions.camera && permissions.microphone
                        ? 'bg-green-500/20 text-green-300 border border-green-500/30 cursor-default'
                        : 'bg-white text-black hover:bg-white/90'
                    }`}
                  >
                    {permissions.camera && permissions.microphone ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Camera & Microphone Enabled
                      </span>
                    ) : (
                      'Enable Camera & Microphone'
                    )}
                  </button>

                  {/* Join Meeting Button - Only shown when permissions granted */}
                  {permissions.camera && permissions.microphone && (
                    <motion.button
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      onClick={handleJoinInterview}
                      disabled={!candidateName.trim()}
                      className="w-full px-6 py-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-purple-600 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none flex items-center justify-center gap-2"
                    >
                      Join Meeting
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                      </svg>
                    </motion.button>
                  )}

                  <button
                    onClick={handleCancel}
                    className="w-full px-6 py-3 bg-white/5 border border-white/10 text-white rounded-xl font-medium hover:bg-white/10 transition-all duration-300"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>

            {/* Help Text */}
            <div className="mt-8 p-4 bg-blue-500/10 border border-blue-500/30 rounded-xl">
              <div className="flex gap-3">
                <svg className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-sm">
                  <p className="text-blue-300 font-medium mb-1">Setup Tips</p>
                  <ul className="text-blue-200/80 space-y-1 list-disc list-inside">
                    <li>Ensure you're in a quiet, well-lit environment</li>
                    <li>Check that your camera is at eye level</li>
                    <li>Test your microphone by speaking - watch the audio level indicator</li>
                    <li>Make sure you have a stable internet connection</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}


