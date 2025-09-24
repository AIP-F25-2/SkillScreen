'use client';

import { useState } from 'react';
import VideoCall from './VideoCall';
import CodingChallenge from './CodingChallenge';

interface InterviewCallProps {
  userType: 'candidate' | 'recruiter';
  participantName: string;
  interviewId: string;
}

export default function InterviewCall({ userType, participantName, interviewId }: InterviewCallProps) {
  const [currentView, setCurrentView] = useState<'call' | 'coding'>('call');
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);

  const toggleMute = () => setIsMuted(!isMuted);
  const toggleVideo = () => setIsVideoOn(!isVideoOn);
  const toggleScreenShare = () => setIsScreenSharing(!isScreenSharing);
  const toggleRecording = () => setIsRecording(!isRecording);

  return (
    <div className="h-screen flex flex-col bg-[#1E1E1E]">
      {/* Main Content Area */}
      <div className="flex-1 flex relative">
        {currentView === 'call' ? (
          <VideoCall 
            userType={userType}
            participantName={participantName}
            isMuted={isMuted}
            isVideoOn={isVideoOn}
            isScreenSharing={isScreenSharing}
            isRecording={isRecording}
            onToggleMute={toggleMute}
            onToggleVideo={toggleVideo}
            onToggleScreenShare={toggleScreenShare}
            onToggleRecording={toggleRecording}
          />
        ) : (
          <CodingChallenge 
            userType={userType}
            participantName={participantName}
          />
        )}
      </div>

      {/* Bottom Controls */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 glass-dark px-4 py-3 rounded-2xl flex items-center space-x-4 shadow-lg z-50">
        <div className="flex items-center space-x-4 mr-4">
          <div className="glass-dark px-3 py-1.5 rounded-full flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-white/80 text-sm">Connected</span>
          </div>
        </div>

        {/* Core Controls */}
        <div className="flex items-center space-x-3">
          {/* Mute Button */}
          <button
            onClick={toggleMute}
            className={`p-4 rounded-xl transition-all ${
              isMuted ? 'bg-red-500/20 hover:bg-red-500/30' : 'hover:bg-white/10'
            }`}
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isMuted ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              )}
            </svg>
          </button>

          {/* Video Button */}
          <button
            onClick={toggleVideo}
            className={`p-4 rounded-xl transition-all ${
              !isVideoOn ? 'bg-red-500/20 hover:bg-red-500/30' : 'hover:bg-white/10'
            }`}
          >
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>

          {/* Screen Share Button */}
          {userType === 'recruiter' && (
            <button
              onClick={toggleScreenShare}
              className={`p-4 rounded-xl transition-all ${
                isScreenSharing ? 'bg-blue-500/20 hover:bg-blue-500/30' : 'hover:bg-white/10'
              }`}
            >
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </button>
          )}

          {/* Recording Button */}
          {userType === 'recruiter' && (
            <button
              onClick={toggleRecording}
              className={`p-4 rounded-xl transition-all ${
                isRecording ? 'bg-red-500/20 hover:bg-red-500/30' : 'hover:bg-white/10'
              }`}
            >
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="4" fill="currentColor" />
              </svg>
            </button>
          )}
        </div>

        <div className="h-8 w-px bg-white/20 mx-2" />

        {/* View Toggle */}
        <div className="glass-dark rounded-xl p-1">
          <button
            onClick={() => setCurrentView('call')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              currentView === 'call'
                ? 'bg-white/10 text-white'
                : 'text-white/80 hover:text-white hover:bg-white/5'
            }`}
          >
            Video Call
          </button>
          <button
            onClick={() => setCurrentView('coding')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              currentView === 'coding'
                ? 'bg-white/10 text-white'
                : 'text-white/80 hover:text-white hover:bg-white/5'
            }`}
          >
            Coding Challenge
          </button>
        </div>

        {/* End Call Button */}
        <button className="p-4 rounded-xl bg-red-500/20 hover:bg-red-500/30 transition-all ml-2">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M3 3l18 18" />
          </svg>
        </button>
      </div>
    </div>
  );
}
