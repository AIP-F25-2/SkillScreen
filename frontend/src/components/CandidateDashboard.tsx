'use client';

import { useState } from 'react';
import { Video } from 'lucide-react';

interface InterviewAnalysis {
  id: string;
  company: string;
  position: string;
  date: string;
  duration: string;
  score: number;
  improvements: string[];
  strengths: string[];
}

const mockInterviews: InterviewAnalysis[] = [
  {
    id: '1',
    company: 'TechCorp Inc.',
    position: 'Senior Software Engineer',
    date: '2024-01-15',
    duration: '45 minutes',
    score: 78,
    improvements: [
      'Maintain better eye contact with camera',
      'Reduce hand gestures while speaking',
      'Speak more slowly and clearly',
      'Prepare more specific examples for behavioral questions'
    ],
    strengths: [
      'Strong technical knowledge demonstration',
      'Good problem-solving approach',
      'Professional attire and background'
    ]
  },
  {
    id: '2',
    company: 'StartupXYZ',
    position: 'Full Stack Developer',
    date: '2024-01-10',
    duration: '60 minutes',
    score: 85,
    improvements: [
      'Better posture - sit up straighter',
      'Minimize background distractions',
      'Practice STAR method for behavioral questions'
    ],
    strengths: [
      'Excellent coding skills',
      'Clear communication',
      'Good questions for the interviewer'
    ]
  }
];
const mockPracticeInterviews: InterviewAnalysis[] = [
  {
    id: '1',
    company: 'Performance Inc.',
    position: 'Senior Software Engineer',
    date: '2024-01-15',
    duration: '45 minutes',
    score: 78,
    improvements: [
      'Maintain better eye contact with camera',
      'Reduce hand gestures while speaking',
      'Speak more slowly and clearly',
      'Prepare more specific examples for behavioral questions'
    ],
    strengths: [
      'Strong technical knowledge demonstration',
      'Good problem-solving approach',
      'Professional attire and background'
    ]
  },
  {
    id: '2',
    company: 'Onlyfans',
    position: 'Full Stack Developer',
    date: '2024-01-10',
    duration: '60 minutes',
    score: 85,
    improvements: [
      'Better posture - sit up straighter',
      'Minimize background distractions',
      'Practice STAR method for behavioral questions'
    ],
    strengths: [
      'Excellent coding skills',
      'Clear communication',
      'Good questions for the interviewer'
    ]
  }
];
export default function CandidateDashboard() {
  const [selectedInterview, setSelectedInterview] = useState<InterviewAnalysis | null>(null);

  return (
    <div className="min-h-screen bg-background p-6">
      {/* Breathing circle background */}
      <div className="breathing-circle"></div>
      
      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Your Interview Dashboard</h1>
          <p className="text-white/80">Track your interview performance and improve with AI-powered insights</p>
        </div>
        {/*Video Interview History */}
        <div className="lg:col-span-2">
            <div className="glass rounded-xl p-6">
              <h2 className="text-2xl font-semibold text-white mb-6">Practice Interview Performance</h2>
              <div className="space-y-4">
                {mockPracticeInterviews.map((practiceinterview) => (
                  <div
                    key={practiceinterview.id}
                    className="glass-dark rounded-xl p-6 cursor-pointer hover:bg-white/5 transition-all duration-300 transform hover:scale-[1.02]"
                    onClick={() => setSelectedInterview(practiceinterview)}
                  >
                    <div className="w-full h-[200px] bg-gray-700/50 rounded-lg mb-4 flex items-center justify-center">
                      <Video className="w-16 h-16 text-white/50" />
                    </div>
                    <div className="flex justify-between items-start mb-4">
                      
                      <div>
                        <h3 className="text-white font-semibold text-lg mb-2">{practiceinterview.position}</h3>
                        <p className="text-white/80 mb-1">{practiceinterview.company}</p>
                        <p className="text-white/60 text-sm">{practiceinterview.date} • {practiceinterview.duration}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold text-white mb-1">{practiceinterview.score}%</div>
                        <div className="text-sm text-white/60">Overall Score</div>
                      </div>
                    </div>
                    <div className="flex space-x-3">
                      {practiceinterview.strengths.slice(0, 2).map((strength, index) => (
                        <span key={index} className="glass px-3 py-1.5 rounded-full text-xs font-medium text-white/90">
                          {strength}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Interview History */}
          <div className="lg:col-span-2">
            <div className="glass rounded-xl p-6">
              <h2 className="text-2xl font-semibold text-white mb-6">Recent Interviews</h2>
              <div className="space-y-4">
                {mockInterviews.map((interview) => (
                  <div
                    key={interview.id}
                    className="glass-dark rounded-xl p-6 cursor-pointer hover:bg-white/5 transition-all duration-300 transform hover:scale-[1.02]"
                    onClick={() => setSelectedInterview(interview)}
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-white font-semibold text-lg mb-2">{interview.position}</h3>
                        <p className="text-white/80 mb-1">{interview.company}</p>
                        <p className="text-white/60 text-sm">{interview.date} • {interview.duration}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-bold text-white mb-1">{interview.score}%</div>
                        <div className="text-sm text-white/60">Overall Score</div>
                      </div>
                    </div>
                    <div className="flex space-x-3">
                      {interview.strengths.slice(0, 2).map((strength, index) => (
                        <span key={index} className="glass px-3 py-1.5 rounded-full text-xs font-medium text-white/90">
                          {strength}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Analysis Panel */}
          <div className="space-y-6">
            {/* Overall Stats */}
            <div className="glass rounded-xl p-6">
              <h3 className="text-xl font-semibold text-white mb-6">Your Progress</h3>
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-white mb-2">
                    <span>Average Score</span>
                    <span className="font-semibold">82%</span>
                  </div>
                  <div className="w-full glass-dark rounded-full h-3">
                    <div className="bg-gradient-to-r from-blue-500 to-blue-400 h-3 rounded-full" style={{ width: '82%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-white mb-2">
                    <span>Interviews Completed</span>
                    <span className="font-semibold">2</span>
                  </div>
                  <div className="w-full glass-dark rounded-full h-3">
                    <div className="bg-gradient-to-r from-green-500 to-green-400 h-3 rounded-full" style={{ width: '100%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-white mb-2">
                    <span>Improvement Areas</span>
                    <span className="font-semibold">4</span>
                  </div>
                  <div className="w-full glass-dark rounded-full h-3">
                    <div className="bg-gradient-to-r from-yellow-500 to-yellow-400 h-3 rounded-full" style={{ width: '80%' }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="glass rounded-xl p-6">
              <h3 className="text-xl font-semibold text-white mb-6">Quick Actions</h3>
              <div className="space-y-4">
                <a 
                  href="/interview" 
                  className="block w-full glass text-white py-4 px-6 rounded-xl font-semibold 
                           hover:bg-white/10 transition-all duration-300 transform hover:scale-[1.02]
                           text-center shadow-lg hover:shadow-xl"
                >
                  Start Interview
                </a>
                <button 
                  className="w-full glass-dark text-white py-4 px-6 rounded-xl font-semibold 
                           hover:bg-white/5 transition-all duration-300 transform hover:scale-[1.02]
                           shadow-lg hover:shadow-xl"
                >
                  Practice Interview
                </button>
                <button 
                  className="w-full glass-dark text-white py-4 px-6 rounded-xl font-semibold 
                           hover:bg-white/5 transition-all duration-300 transform hover:scale-[1.02]
                           shadow-lg hover:shadow-xl"
                >
                  View Profile
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Detailed Analysis Modal */}
        {selectedInterview && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-6 z-50">
            <div className="glass rounded-2xl p-8 max-w-3xl w-full max-h-[85vh] overflow-y-auto">
              <div className="flex justify-between items-start mb-8">
                <div>
                  <h3 className="text-3xl font-bold text-white mb-2">{selectedInterview.position}</h3>
                  <p className="text-white/80 text-lg">{selectedInterview.company}</p>
                </div>
                <button
                  onClick={() => setSelectedInterview(null)}
                  className="glass-dark p-2 rounded-lg text-white hover:bg-white/10 transition-all duration-300 transform hover:scale-105"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
                {/* Strengths */}
                <div className="glass-dark rounded-xl p-6">
                  <h4 className="text-xl font-semibold text-white mb-4 flex items-center">
                    <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                    Strengths
                  </h4>
                  <div className="space-y-3">
                    {selectedInterview.strengths.map((strength, index) => (
                      <div key={index} className="glass px-4 py-3 rounded-lg text-white/90">
                        {strength}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Areas for Improvement */}
                <div className="glass-dark rounded-xl p-6">
                  <h4 className="text-xl font-semibold text-white mb-4 flex items-center">
                    <span className="w-2 h-2 bg-yellow-400 rounded-full mr-2"></span>
                    Areas for Improvement
                  </h4>
                  <div className="space-y-3">
                    {selectedInterview.improvements.map((improvement, index) => (
                      <div key={index} className="glass px-4 py-3 rounded-lg text-white/90">
                        {improvement}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Video Analysis */}
              <div className="glass-dark rounded-xl p-6">
                <h4 className="text-xl font-semibold text-white mb-6">Video Analysis</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                  <div className="glass rounded-lg p-4 text-center transform hover:scale-105 transition-transform duration-300">
                    <div className="text-white/80 font-medium mb-2">Eye Contact</div>
                    <div className="text-2xl font-bold text-white">65%</div>
                    <div className="w-full glass-dark rounded-full h-1.5 mt-2">
                      <div className="bg-gradient-to-r from-blue-500 to-blue-400 h-1.5 rounded-full" style={{ width: '65%' }}></div>
                    </div>
                  </div>
                  <div className="glass rounded-lg p-4 text-center transform hover:scale-105 transition-transform duration-300">
                    <div className="text-white/80 font-medium mb-2">Posture</div>
                    <div className="text-2xl font-bold text-white">78%</div>
                    <div className="w-full glass-dark rounded-full h-1.5 mt-2">
                      <div className="bg-gradient-to-r from-green-500 to-green-400 h-1.5 rounded-full" style={{ width: '78%' }}></div>
                    </div>
                  </div>
                  <div className="glass rounded-lg p-4 text-center transform hover:scale-105 transition-transform duration-300">
                    <div className="text-white/80 font-medium mb-2">Speech Clarity</div>
                    <div className="text-2xl font-bold text-white">82%</div>
                    <div className="w-full glass-dark rounded-full h-1.5 mt-2">
                      <div className="bg-gradient-to-r from-purple-500 to-purple-400 h-1.5 rounded-full" style={{ width: '82%' }}></div>
                    </div>
                  </div>
                  <div className="glass rounded-lg p-4 text-center transform hover:scale-105 transition-transform duration-300">
                    <div className="text-white/80 font-medium mb-2">Engagement</div>
                    <div className="text-2xl font-bold text-white">75%</div>
                    <div className="w-full glass-dark rounded-full h-1.5 mt-2">
                      <div className="bg-gradient-to-r from-yellow-500 to-yellow-400 h-1.5 rounded-full" style={{ width: '75%' }}></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
