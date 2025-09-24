'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, MicOff, Video, VideoOff, Monitor, Record, X, Maximize2, MessageSquare } from 'lucide-react';
import CodingChallenge from './CodingChallenge';

interface ModernInterviewScreenProps {
  userType: 'candidate' | 'recruiter';
  participantName: string;
}

export default function ModernInterviewScreen({ userType, participantName }: ModernInterviewScreenProps) {
  const [isCodeEditorOpen, setIsCodeEditorOpen] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);

  const toggleCodeEditor = () => setIsCodeEditorOpen(!isCodeEditorOpen);
  const toggleMute = () => setIsMuted(!isMuted);
  const toggleVideo = () => setIsVideoOn(!isVideoOn);
  const toggleScreenShare = () => setIsScreenSharing(!isScreenSharing);
  const toggleRecording = () => setIsRecording(!isRecording);

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
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-white/80 text-sm font-medium">Interview in Progress</span>
          </div>
          <button 
            className="px-4 py-2 text-white/90 text-sm font-medium hover:bg-red-500/20 transition-all rounded-r-xl"
            onClick={() => alert('End Interview?')}
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
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800/50 to-gray-900/50">
                      <div className="w-32 h-32 rounded-full bg-gray-700/50 flex items-center justify-center">
                        <svg className="w-16 h-16 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                    </div>
                    <div className="absolute bottom-4 left-4 glass-dark px-4 py-2 rounded-xl text-white/90 text-sm font-medium shadow-lg">
                      {userType === 'candidate' ? 'Recruiter' : 'Candidate'}
                      <div className="flex items-center mt-1 space-x-2">
                        <div className={`w-2 h-2 rounded-full ${isMuted ? 'bg-red-400' : 'bg-green-400'} animate-pulse`}></div>
                        <span className="text-white/60 text-xs">
                          {isMuted ? 'Muted' : 'Speaking'}
                        </span>
                      </div>
                    </div>
                  </motion.div>

                  {/* Floating PiP Video */}
                  <motion.div 
                    className="fixed top-4 right-4 w-72 aspect-video bg-gray-800/90 rounded-2xl overflow-hidden shadow-2xl border border-white/10"
                    layoutId="pipVideo"
                    drag
                    dragMomentum={false}
                    dragConstraints={{
                      top: 20,
                      left: -window.innerWidth + 300, // Allow movement to the left edge
                      right: window.innerWidth - 300, // Allow movement to the right edge
                      bottom: window.innerHeight - 180 // Keep some space from bottom
                    }}
                    dragElastic={0.1}
                    dragTransition={{ 
                      bounceStiffness: 500,
                      bounceDamping: 50
                    }}
                    whileDrag={{ scale: 1.02 }}
                    whileHover={{ scale: 1.02 }}
                    transition={{ 
                      type: "spring",
                      stiffness: 120,
                      damping: 25,
                      mass: 1.5,
                      duration: 1.2,
                      layout: {
                        type: "spring",
                        stiffness: 120,
                        damping: 25
                      }
                    }}
                  >
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800/50 to-gray-900/50">
                      <div className="w-20 h-20 rounded-full bg-gray-700/50 flex items-center justify-center">
                        <svg className="w-10 h-10 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                    </div>
                    
                    {/* Video Controls Overlay */}
                    <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-black/50 to-transparent" />
                    <div className="absolute bottom-3 left-3 flex items-center space-x-2">
                      <div className="glass-dark px-3 py-1.5 rounded-lg text-white/90 text-xs font-medium flex items-center space-x-2">
                        <span>You</span>
                        {isMuted && (
                          <span className="text-red-400">
                            <MicOff className="w-3 h-3" />
                          </span>
                        )}
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
              {/* Video Thumbnails */}
              <div className="flex gap-4 px-6 py-4">
                {/* Main participant video - animate from main view */}
                <motion.div 
                  className="w-48 h-32 glass-dark rounded-xl overflow-hidden relative shadow-lg"
                  layoutId="mainVideo"
                  transition={{
                    type: "spring",
                    stiffness: 120,
                    damping: 25,
                    mass: 1.5,
                    duration: 1.2,
                    layout: {
                      type: "spring",
                      stiffness: 120,
                      damping: 25
                    }
                  }}
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
                    {userType === 'candidate' ? 'Recruiter' : 'Candidate'}
                  </div>
                </motion.div>

                {/* Self video - animate from PiP */}
                <motion.div 
                  className="w-48 h-32 glass-dark rounded-xl overflow-hidden relative shadow-lg"
                  layoutId="pipVideo"
                  transition={{
                    type: "spring",
                    stiffness: 120,
                    damping: 25,
                    mass: 1.5,
                    duration: 1.2,
                    layout: {
                      type: "spring",
                      stiffness: 120,
                      damping: 25
                    }
                  }}
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
                    You
                  </div>
                </motion.div>
              </div>

              {/* Coding Challenge - animate in from bottom */}
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
                <CodingChallenge userType={userType} participantName={participantName} />
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

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

          {userType === 'recruiter' && (
            <>
              <button
                onClick={toggleScreenShare}
                className={`p-4 rounded-xl transition-all ${
                  isScreenSharing ? 'bg-blue-500/20 hover:bg-blue-500/30' : 'hover:bg-white/10'
                }`}
              >
                <Monitor className="w-6 h-6 text-white" />
              </button>

              <button
                onClick={toggleRecording}
                className={`p-4 rounded-xl transition-all ${
                  isRecording ? 'bg-red-500/20 hover:bg-red-500/30' : 'hover:bg-white/10'
                }`}
              >
                <Record className="w-6 h-6 text-white" />
              </button>
            </>
          )}

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
            onClick={() => setIsChatOpen(!isChatOpen)}
            className={`p-4 rounded-xl transition-all ${
              isChatOpen ? 'bg-primary-200/20 hover:bg-primary-200/30' : 'hover:bg-white/10'
            }`}
          >
            <MessageSquare className="w-6 h-6 text-white" />
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
                onClick={() => setIsChatOpen(false)}
                className="p-2 hover:bg-white/10 rounded-lg transition-all"
              >
                <X className="w-5 h-5 text-white" />
              </button>
            </div>
            {/* Chat content here */}
          </motion.div>
        )}
      </AnimatePresence>
    
    </div>
    </div>
  );
}
