'use client';

import { useState } from 'react';

interface VideoCallProps {
  userType: 'candidate' | 'recruiter';
  participantName: string;
  isMuted: boolean;
  isVideoOn: boolean;
  isScreenSharing: boolean;
  isRecording: boolean;
  onToggleMute: () => void;
  onToggleVideo: () => void;
  onToggleScreenShare: () => void;
  onToggleRecording: () => void;
}

export default function VideoCall({
  userType,
  participantName,
  isMuted,
  isVideoOn,
  isScreenSharing,
  isRecording,
  onToggleMute,
  onToggleVideo,
  onToggleScreenShare,
  onToggleRecording
}: VideoCallProps) {
  const [chatMessages, setChatMessages] = useState([
    { id: 1, sender: 'recruiter', message: 'Welcome to the interview! How are you feeling today?', timestamp: '10:30 AM' },
    { id: 2, sender: 'candidate', message: 'Thank you! I\'m excited and ready to discuss the role.', timestamp: '10:31 AM' },
    { id: 3, sender: 'recruiter', message: 'Great! Let\'s start with some behavioral questions.', timestamp: '10:32 AM' }
  ]);
  const [newMessage, setNewMessage] = useState('');
  const [showChat, setShowChat] = useState(false);

  const sendMessage = () => {
    if (newMessage.trim()) {
      setChatMessages([...chatMessages, {
        id: chatMessages.length + 1,
        sender: userType,
        message: newMessage,
        timestamp: new Date().toLocaleTimeString()
      }]);
      setNewMessage('');
    }
  };

  return (
    <div className="flex-1 flex bg-[#1E1E1E] relative">
      {/* Main Video Area */}
      <div className="absolute inset-0 flex items-center justify-center">
        {/* Main Video (Full Screen) */}
        <div className="w-full h-full max-w-6xl aspect-video relative mx-auto">
          <div className="absolute inset-0 glass-dark rounded-2xl overflow-hidden">
            {/* Placeholder for main video */}
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800/50 to-gray-900/50">
              <div className="w-32 h-32 rounded-full bg-gray-700/50 flex items-center justify-center">
                <svg className="w-16 h-16 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
            </div>
          </div>
          
          {/* Name Label */}
          <div className="absolute bottom-4 left-4 glass-dark px-4 py-2 rounded-xl text-white/90 text-sm font-medium shadow-lg">
            {userType === 'candidate' ? 'Sarah Johnson (Recruiter)' : 'John Doe (Candidate)'}
            <div className="flex items-center mt-1 space-x-2">
              <div className={`w-2 h-2 rounded-full ${isMuted ? 'bg-red-400' : 'bg-green-400'} animate-pulse`}></div>
              <span className="text-white/60 text-xs">
                {isMuted ? 'Muted' : 'Speaking'}
              </span>
            </div>
          </div>
        </div>

        {/* Floating PiP Video */}
        <div className="absolute top-24 right-6 w-80 aspect-video bg-gray-800/90 rounded-2xl overflow-hidden shadow-2xl border border-white/10">
          {/* Placeholder for self video */}
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800/50 to-gray-900/50">
            <div className="w-20 h-20 rounded-full bg-gray-700/50 flex items-center justify-center">
              <svg className="w-10 h-10 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
          </div>
          
          {/* Video Controls Overlay */}
          <div className="absolute inset-x-0 bottom-0 h-12 bg-gradient-to-t from-black/50 to-transparent" />
          <div className="absolute bottom-3 left-3 glass-dark px-3 py-1.5 rounded-lg text-white/90 text-xs font-medium">
            You {isMuted ? '(Muted)' : ''}
          </div>
        </div>

        {/* Status Indicators */}
        {isRecording && (
          <div className="absolute top-6 left-6 glass-dark bg-red-500/20 px-4 py-2 rounded-xl text-sm flex items-center space-x-2 shadow-lg">
            <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
            <span className="text-white">Recording</span>
          </div>
        )}

        {isScreenSharing && (
          <div className="absolute top-6 left-1/2 transform -translate-x-1/2 glass-dark bg-blue-500/20 px-4 py-2 rounded-xl text-sm flex items-center space-x-2 shadow-lg">
            <svg className="w-4 h-4 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <span className="text-white">Screen Sharing</span>
          </div>
        )}
      </div>

      {/* Chat Sidebar */}
      {showChat && (
        <div className="absolute right-0 top-0 bottom-0 w-96 glass-dark border-l border-white/10 shadow-2xl">
          <div className="p-4 border-b border-white/10 flex justify-between items-center">
            <h3 className="text-white font-medium">Chat</h3>
            <button
              onClick={() => setShowChat(false)}
              className="p-2 hover:bg-white/10 rounded-lg transition-all"
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.sender === userType ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-sm px-4 py-3 rounded-xl ${
                  msg.sender === userType 
                    ? 'bg-white/10 text-white' 
                    : 'bg-white/5 text-white'
                }`}>
                  <div className="text-sm leading-relaxed">{msg.message}</div>
                  <div className="text-xs mt-2 text-white/60">
                    {msg.timestamp}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 border-t border-white/10">
            <div className="flex space-x-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Type a message..."
                className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white placeholder-white/40 focus:outline-none focus:border-white/20"
              />
              <button
                onClick={sendMessage}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-all"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Toggle Button */}
      {!showChat && (
        <button
          onClick={() => setShowChat(true)}
          className="absolute top-1/2 right-6 transform -translate-y-1/2 glass-dark p-4 rounded-xl text-white hover:bg-white/10 transition-all shadow-lg"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </button>
      )}
    </div>
  );
}
