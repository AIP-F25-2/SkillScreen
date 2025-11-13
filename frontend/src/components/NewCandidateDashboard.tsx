'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Video, Search, Bell, RotateCw, LayoutGrid, Maximize2, ChevronDown, FileText, Clock, PlayCircle } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';

interface RecentApplication {
  company: string;
  status: 'pending' | 'accepted' | 'rejected';
}

interface ATSScore {
  category: string;
  percentage: number;
  color: string;
}

export default function CandidateDashboard() {
  const router = useRouter();
  const { user } = useAuth();
  const [interviews, setInterviews] = useState<any[]>([]);
  const [scheduledInterviews, setScheduledInterviews] = useState<any[]>([]);
  const [loadingInterviews, setLoadingInterviews] = useState(true);

  const recentApplications: RecentApplication[] = [
    { company: 'Meta', status: 'pending' },
    { company: 'Amazon', status: 'pending' },
    { company: 'Apple', status: 'pending' },
    { company: 'Morgan Stanley', status: 'pending' },
    { company: 'Tesla', status: 'pending' }
  ];

  const atsScores: ATSScore[] = [
    { category: 'Education', percentage: 47, color: 'bg-blue-500' },
    { category: 'Experience', percentage: 28, color: 'bg-red-400' },
    { category: 'Projects', percentage: 18, color: 'bg-yellow-400' }
  ];

  // Fetch all interviews and candidates
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoadingInterviews(true);
        
        // Fetch all interviews
        const interviewsResponse = await apiClient.getAllInterviews();
        if (interviewsResponse.success) {
          const allInterviews = interviewsResponse.data.interviews || [];
          const completedInterviews = allInterviews.filter(i => i.status === 'completed');
          setInterviews(completedInterviews);
        }

        // Fetch all candidates
        const candidatesResponse = await apiClient.getAllCandidates();
        if (candidatesResponse.success) {
          const allCandidates = candidatesResponse.data.candidates || [];
          const scheduledCandidates = allCandidates.filter(c => c.status === 'scheduled');
          setScheduledInterviews(scheduledCandidates);
        }
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setLoadingInterviews(false);
      }
    };

    fetchData();
  }, []);

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) {
        return 'Invalid Date';
      }
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Unknown';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500/20 text-green-400';
      case 'processing':
        return 'bg-yellow-500/20 text-yellow-400';
      case 'failed':
        return 'bg-red-500/20 text-red-400';
      default:
        return 'bg-gray-500/20 text-gray-400';
    }
  };

  return (
    <div className="min-h-screen p-6">
      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header with Search */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">User Overview</h1>
          </div>
          <div className="flex items-center space-x-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search"
                className="glass-dark pl-10 pr-4 py-2 rounded-lg text-white placeholder-white/50 w-64"
              />
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/50" />
            </div>
            <button className="glass-dark p-2 rounded-lg">
              <Bell className="w-5 h-5 text-white/70" />
            </button>
            <button className="glass-dark p-2 rounded-lg">
              <RotateCw className="w-5 h-5 text-white/70" />
            </button>
          </div>
        </div>

        {/* Quick Action - Test Interview Setup */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/interview-setup')}
            className="w-full glass-dark p-6 rounded-xl hover:bg-white/10 transition-all duration-300 group"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                  <Video className="w-6 h-6 text-white" />
                </div>
                <div className="text-left">
                  <h3 className="text-lg font-semibold text-white">Test Your Interview Setup</h3>
                  <p className="text-white/60 text-sm">Check camera & microphone before your interview</p>
                </div>
              </div>
              <svg className="w-6 h-6 text-white/40 group-hover:text-white group-hover:translate-x-2 transition-all duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>
          </button>
        </div>

        {/* My Interviews Section */}
        <div className="mb-8">
          <div className="glass-dark rounded-xl p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Video className="w-6 h-6" />
                My Interviews
              </h2>
              <span className="text-white/50 text-sm">
                {scheduledInterviews.length + interviews.length} total ({scheduledInterviews.length} scheduled, {interviews.length} completed)
              </span>
            </div>

            {loadingInterviews ? (
              <div className="flex justify-center py-12">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : scheduledInterviews.length === 0 && interviews.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-16 h-16 text-white/30 mx-auto mb-4" />
                <p className="text-white/70 mb-2">No interviews yet</p>
                <p className="text-white/50 text-sm">Complete an interview to see it here</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Scheduled Interviews */}
                {scheduledInterviews.length > 0 && (
                  <div>
                    <h3 className="text-white/80 text-sm font-medium mb-3 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Scheduled Interviews
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {scheduledInterviews.map((candidate) => (
                        <div
                          key={candidate.candidate_id}
                          className="glass p-4 rounded-xl hover:bg-white/10 transition-all cursor-pointer border-2 border-blue-500/30"
                          onClick={() => router.push(`/interview?session_id=${candidate.session_id}`)}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center animate-pulse">
                                <PlayCircle className="w-5 h-5 text-white" />
                              </div>
                              <div>
                                <p className="text-white font-medium text-sm">{candidate.candidate_name || candidate.candidate_id}</p>
                                <p className="text-white/50 text-xs">{formatDate(candidate.scheduled_at || candidate.uploaded_at || candidate.created_at)}</p>
                              </div>
                            </div>
                            <span className="px-2 py-1 rounded-lg text-xs font-medium bg-blue-500/20 text-blue-300">
                              Ready
                            </span>
                          </div>
                          
                          <div className="flex items-center gap-2 text-white/60 text-xs mb-2">
                            <span className="flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              Session: {candidate.session_id}
                            </span>
                          </div>

                          <div className="mt-3 pt-3 border-t border-white/10">
                            <button className="w-full bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2">
                              <PlayCircle className="w-4 h-4" />
                              Start Interview Now
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Completed Interviews */}
                {interviews.length > 0 && (
                  <div>
                    {scheduledInterviews.length > 0 && (
                      <h3 className="text-white/80 text-sm font-medium mb-3 flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Completed Interviews
                      </h3>
                    )}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {interviews.map((interview) => (
                        <div
                          key={interview.interview_id}
                          className="glass p-4 rounded-xl hover:bg-white/10 transition-all cursor-pointer"
                          onClick={() => router.push(`/interview-summary?id=${interview.session_id}`)}
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
                                <PlayCircle className="w-5 h-5 text-white" />
                              </div>
                              <div>
                                <p className="text-white font-medium text-sm">{interview.candidate_name || interview.candidate_id}</p>
                                <p className="text-white/50 text-xs">{formatDate(interview.created_at || interview.scheduled_at)}</p>
                              </div>
                            </div>
                            <span className={`px-2 py-1 rounded-lg text-xs font-medium ${getStatusColor(interview.status)}`}>
                              {interview.status}
                            </span>
                          </div>
                          
                          {interview.transcript && interview.transcript.word_count && (
                            <div className="flex items-center gap-4 text-white/60 text-xs">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {Math.floor((interview.transcript.duration_seconds || 0) / 60)}m
                              </span>
                              <span className="flex items-center gap-1">
                                <FileText className="w-3 h-3" />
                                {interview.transcript.word_count} words
                              </span>
                            </div>
                          )}

                          {interview.status === 'processing' && (
                            <div className="mt-2 text-yellow-400/70 text-xs">
                              Transcription in progress...
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      
       
        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Interview Performance */}
          <div className="lg:col-span-2">
            <div className="glass-dark rounded-xl p-6 mb-8">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-white">Interview Performance</h2>
                <div className="flex space-x-2">
                  <button className="glass p-2 rounded-lg">
                    <LayoutGrid className="w-5 h-5 text-white/70" />
                  </button>
                  <button className="glass p-2 rounded-lg">
                    <Maximize2 className="w-5 h-5 text-white/70" />
                  </button>
                </div>
              </div>

              <div className="w-full h-[200px] bg-gray-700/50 rounded-lg flex items-center justify-center mb-6">
                <div className="text-center text-white/70">
                  <p className="text-lg font-semibold mb-2">Previous Interview Video</p>
                  <p className="text-sm">Click to play</p>
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-white font-semibold">Generated Interview Tips:</h3>
                <ul className="list-disc list-inside text-white/70 space-y-2">
                  <li>Maintain consistent eye contact with the camera</li>
                  <li>Speak clearly and at a moderate pace</li>
                  <li>Use specific examples to support your answers</li>
                </ul>
              </div>
            </div>

            {/* Resume Overview */}
            <div className="glass-dark rounded-xl p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-white">Resume Overview</h2>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center">
                    <div className="relative w-12 h-12">
                      <svg className="transform -rotate-90 w-12 h-12">
                        <circle
                          className="text-gray-700"
                          strokeWidth="2"
                          stroke="currentColor"
                          fill="transparent"
                          r="20"
                          cx="24"
                          cy="24"
                        />
                        <circle
                          className="text-blue-500"
                          strokeWidth="2"
                          strokeDasharray={125.6}
                          strokeDashoffset={125.6 * (1 - 0.85)}
                          strokeLinecap="round"
                          stroke="currentColor"
                          fill="transparent"
                          r="20"
                          cx="24"
                          cy="24"
                        />
                      </svg>
                      <span className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-sm font-semibold text-white">85%</span>
                    </div>
                    <span className="ml-2 text-sm text-white/70">ATS Score</span>
                  </div>
                  <button className="glass p-2 rounded-lg">
                    <ChevronDown className="w-5 h-5 text-white/70" />
                  </button>
                </div>
              </div>
              
              <div className="w-full h-[200px] bg-[#1E1E1E] rounded-lg flex flex-col items-center justify-center border border-white/10 mb-6">
                <h3 className="text-2xl font-bold text-white mb-2">RESUME</h3>
                <p className="text-2xl font-bold text-white">Overview</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="glass p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-white mb-1">92%</div>
                  <div className="text-sm text-white/70">Keyword Match</div>
                </div>
                <div className="glass p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-white mb-1">78%</div>
                  <div className="text-sm text-white/70">Format Score</div>
                </div>
                <div className="glass p-4 rounded-lg text-center">
                  <div className="text-2xl font-bold text-white mb-1">88%</div>
                  <div className="text-sm text-white/70">Content Score</div>
                </div>
              </div>

              <div className="space-y-6">
                <div>
                  <h3 className="text-white font-semibold mb-3">ATS Optimization Suggestions:</h3>
                  <ul className="space-y-2 text-white/70">
                    <li className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-white/40 rounded-full mr-2"></span>
                      Enhance keyword density for target role
                    </li>
                    <li className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-white/40 rounded-full mr-2"></span>
                      Add measurable achievements with metrics
                    </li>
                    <li className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-white/40 rounded-full mr-2"></span>
                      Optimize technical skills section
                    </li>
                  </ul>
                </div>
                
                <div>
                  <h3 className="text-white font-semibold mb-3">Format & Structure:</h3>
                  <ul className="space-y-2 text-white/70">
                    <li className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-white/40 rounded-full mr-2"></span>
                      Use ATS-friendly section headings
                    </li>
                    <li className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-white/40 rounded-full mr-2"></span>
                      Improve content hierarchy
                    </li>
                    <li className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-white/40 rounded-full mr-2"></span>
                      Remove complex formatting
                    </li>
                  </ul>
                </div>

                <div>
                  <h3 className="text-white font-semibold mb-3">Industry Alignment:</h3>
                  <ul className="space-y-2 text-white/70">
                    <li className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-white/40 rounded-full mr-2"></span>
                      Match skills with job requirements
                    </li>
                    <li className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-white/40 rounded-full mr-2"></span>
                      Update industry-specific terminology
                    </li>
                    <li className="flex items-center">
                      <span className="w-1.5 h-1.5 bg-white/40 rounded-full mr-2"></span>
                      Highlight relevant certifications
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Stats and Applications */}
          <div className="space-y-8">
            {/* ATS Score */}
            <div className="glass-dark rounded-xl p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-white">ATS Score</h2>
                <select className="glass-dark text-white/70 text-sm px-3 py-1 rounded-lg">
                  <option>Month</option>
                  <option>Quarter</option>
                  <option>Year</option>
                </select>
              </div>
              <div className="relative pt-8">
                <div className="flex flex-col space-y-4">
                  {atsScores.map((score, index) => (
                    <div key={index} className="flex items-center space-x-3">
                      <div className="w-24 text-sm text-white/70">{score.category}</div>
                      <div className="flex-1 h-2 bg-gray-700/50 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${score.color} rounded-full`}
                          style={{ width: `${score.percentage}%` }}
                        />
                      </div>
                      <div className="w-12 text-sm text-white/70 text-right">{score.percentage}%</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Recent Applications */}
            <div className="glass-dark rounded-xl p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-white">Your Recent Applications</h2>
                <button className="text-white/50 hover:text-white">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                  </svg>
                </button>
              </div>
              <div className="space-y-4">
                {recentApplications.map((app, index) => (
                  <div key={index} className="flex items-center justify-between glass p-4 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-gray-700/50 rounded-lg flex items-center justify-center">
                        <span className="text-white/70 text-sm">{app.company[0]}</span>
                      </div>
                      <span className="text-white font-medium">{app.company}</span>
                    </div>
                    <button className="glass-dark px-3 py-1 rounded-lg text-sm text-white/70">
                      View
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
