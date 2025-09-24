'use client';

import { useState } from 'react';
import Image from 'next/image';
import { Send, Paperclip, Code, SkipBack, SkipForward, Flag, Check, User, Bot, Clipboard, MoreVertical, MessageSquare } from 'lucide-react';
import NavBar from '@/components/NavBar';

interface Message {
  type: 'user' | 'assistant';
  content: string;
  isCode?: boolean;
}

export default function ChatPage() {
  const [charCount, setCharCount] = useState(0);
  const [messages] = useState<Message[]>([
    {
      type: 'assistant',
      content: 'Welcome to your IntervuAI interview! I\'ll be assessing your technical and problem-solving skills. Let\'s begin with the first question.'
    },
    {
      type: 'assistant',
      content: 'Question 1: Explain the difference between let, const, and var in JavaScript.'
    },
    {
      type: 'user',
      content: 'In JavaScript, var is function-scoped and can be redeclared and updated. let is block-scoped and can be updated but not redeclared. const is also block-scoped but cannot be updated or redeclared after initialization.'
    },
    {
      type: 'assistant',
      content: 'Question 2: Write a function that reverses a string in JavaScript.',
      isCode: true
    }
  ]);

  return (
    <div className="min-h-screen bg-[#1E1E1E]">
      <NavBar />
      <div className="flex h-screen pt-16">
        {/* Sidebar */}
        <div className="hidden md:flex w-[260px] bg-[#1E1E1E] border-r border-white/10 flex-col p-2">
          <button className="flex items-center gap-2 w-full p-3 hover:bg-white/5 rounded-lg text-white text-sm transition-colors">
            <MessageSquare className="w-4 h-4" />
            New Interview
          </button>
          <div className="mt-4 flex flex-col gap-2 flex-1">
            <div className="text-xs text-white/50 px-3 py-2">Previous Interviews</div>
            <button className="flex items-center gap-2 w-full p-3 hover:bg-white/5 rounded-lg text-white/70 text-sm transition-colors">
              Senior Software Engineer - TechCorp
            </button>
            <button className="flex items-center gap-2 w-full p-3 hover:bg-white/5 rounded-lg text-white/70 text-sm transition-colors">
              Full Stack Developer - StartupXYZ
            </button>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 flex flex-col bg-[#1E1E1E] overflow-hidden h-[calc(100vh-4rem)]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto pt-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`border-b border-white/10 ${
                  message.type === 'assistant' ? 'bg-[#1E1E1E]' : 'bg-[#27272A]'
                }`}
              >
                <div className="max-w-3xl mx-auto px-4 py-6 flex gap-4">
                  <div className="mt-1 flex-shrink-0">
                    {message.type === 'assistant' ? (
                      <div className="w-8 h-8 rounded-full bg-[#1E1E1E] relative overflow-hidden">
                        <Image
                          src="/logo.png"
                          alt="IntervuAI"
                          fill
                          className="object-contain"
                        />
                      </div>
                    ) : (
                      <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
                        <User className="w-5 h-5 text-green-500" />
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1 space-y-2">
                    <div className="text-white prose prose-invert max-w-none">
                      {message.isCode ? (
                        <div className="bg-[#27272A] rounded-lg p-4 font-mono text-sm">
                          <pre><code>{message.content}</code></pre>
                        </div>
                      ) : (
                        <p>{message.content}</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Input Area */}
          <div className="border-t border-white/10 bg-[#1E1E1E] p-4">
            <div className="max-w-3xl mx-auto">
              <div className="flex items-end gap-3">
                <div className="flex-1 bg-[#27272A] rounded-xl border border-white/10 focus-within:border-white/20 transition-colors overflow-hidden">
                  <textarea
                    rows={1}
                    className="w-full bg-transparent px-4 py-3 text-white resize-none focus:outline-none"
                    placeholder="Type your answer here..."
                    onChange={(e) => setCharCount(e.target.value.length)}
                    style={{ minHeight: '44px', maxHeight: '200px' }}
                  />
                  <div className="flex items-center justify-between px-4 py-2 border-t border-white/10">
                    <div className="flex gap-2">
                      <button className="p-1 hover:bg-white/5 rounded-md transition-colors">
                        <Paperclip className="w-5 h-5 text-white/60" />
                      </button>
                      <button className="p-1 hover:bg-white/5 rounded-md transition-colors">
                        <Code className="w-5 h-5 text-white/60" />
                      </button>
                    </div>
                    <div className="text-xs text-white/40">
                      {charCount}/1000
                    </div>
                  </div>
                </div>
                <button className="bg-blue-500 p-3 rounded-xl hover:bg-blue-600 transition-colors">
                  <Send className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>
          </div>

          {/* Interview Controls */}
          <div className="border-t border-white/10 bg-[#1E1E1E] p-4">
            <div className="max-w-3xl mx-auto flex justify-between items-center">
              <div className="flex items-center space-x-2">
                <button className="flex items-center gap-2 px-4 py-2 border border-white/10 rounded-lg text-white/90 hover:bg-white/5 transition-colors">
                  <SkipBack className="w-4 h-4" />
                  Previous
                </button>
                <button className="flex items-center gap-2 px-4 py-2 border border-white/10 rounded-lg text-white/90 hover:bg-white/5 transition-colors">
                  <SkipForward className="w-4 h-4" />
                  Next
                </button>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-sm text-white/60">
                  <span className="font-medium">Progress:</span> 2/10 questions
                </div>
                <button className="flex items-center gap-2 px-4 py-2 bg-red-500/20 text-red-500 rounded-lg hover:bg-red-500/30 transition-colors">
                  <Flag className="w-4 h-4" />
                  Flag Issue
                </button>
                <button className="flex items-center gap-2 px-4 py-2 bg-green-500/20 text-green-500 rounded-lg hover:bg-green-500/30 transition-colors">
                  <Check className="w-4 h-4" />
                  Submit
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}