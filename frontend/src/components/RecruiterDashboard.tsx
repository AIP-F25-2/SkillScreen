'use client';

import { useState } from 'react';

interface Candidate {
  id: string;
  name: string;
  email: string;
  position: string;
  status: 'scheduled' | 'completed' | 'pending' | 'rejected';
  score?: number;
  interviewDate?: string;
  skills: string[];
  experience: string;
}

interface JobPosting {
  id: string;
  title: string;
  department: string;
  applicants: number;
  interviews: number;
  status: 'active' | 'paused' | 'closed';
}

const mockCandidates: Candidate[] = [
  {
    id: '1',
    name: 'Sarah Johnson',
    email: 'sarah.j@email.com',
    position: 'Senior Software Engineer',
    status: 'completed',
    score: 85,
    interviewDate: '2024-01-15',
    skills: ['React', 'Node.js', 'TypeScript', 'AWS'],
    experience: '5 years'
  },
  {
    id: '2',
    name: 'Michael Chen',
    email: 'm.chen@email.com',
    position: 'Full Stack Developer',
    status: 'scheduled',
    interviewDate: '2024-01-20',
    skills: ['Python', 'Django', 'PostgreSQL', 'Docker'],
    experience: '3 years'
  },
  {
    id: '3',
    name: 'Emily Rodriguez',
    email: 'emily.r@email.com',
    position: 'Frontend Developer',
    status: 'pending',
    skills: ['Vue.js', 'JavaScript', 'CSS', 'Figma'],
    experience: '2 years'
  },
  {
    id: '4',
    name: 'David Kim',
    email: 'david.k@email.com',
    position: 'DevOps Engineer',
    status: 'completed',
    score: 92,
    interviewDate: '2024-01-12',
    skills: ['Kubernetes', 'Terraform', 'Jenkins', 'Linux'],
    experience: '6 years'
  }
];

const mockJobPostings: JobPosting[] = [
  {
    id: '1',
    title: 'Senior Software Engineer',
    department: 'Engineering',
    applicants: 45,
    interviews: 8,
    status: 'active'
  },
  {
    id: '2',
    title: 'Product Manager',
    department: 'Product',
    applicants: 32,
    interviews: 5,
    status: 'active'
  },
  {
    id: '3',
    title: 'UX Designer',
    department: 'Design',
    applicants: 28,
    interviews: 3,
    status: 'paused'
  }
];

export default function RecruiterDashboard() {
  const [activeTab, setActiveTab] = useState<'candidates' | 'jobs' | 'analytics'>('candidates');
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500/20 text-green-300';
      case 'scheduled': return 'bg-blue-500/20 text-blue-300';
      case 'pending': return 'bg-yellow-500/20 text-yellow-300';
      case 'rejected': return 'bg-red-500/20 text-red-300';
      default: return 'bg-gray-500/20 text-gray-300';
    }
  };

  return (
    <div className="min-h-screen p-6">
      {/* Breathing circle background */}
      <div className="breathing-circle"></div>
      
      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Recruiter Dashboard</h1>
          <p className="text-primary-100">Manage candidates, interviews, and hiring pipeline</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
            <div className="text-3xl font-bold text-white mb-2">24</div>
            <div className="text-primary-100">Total Candidates</div>
          </div>
          <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
            <div className="text-3xl font-bold text-white mb-2">8</div>
            <div className="text-primary-100">Interviews Today</div>
          </div>
          <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
            <div className="text-3xl font-bold text-white mb-2">12</div>
            <div className="text-primary-100">Pending Reviews</div>
          </div>
          <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
            <div className="text-3xl font-bold text-white mb-2">85%</div>
            <div className="text-primary-100">Avg. Score</div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-8 bg-primary-200/10 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('candidates')}
            className={`px-6 py-3 rounded-md font-semibold transition-colors ${
              activeTab === 'candidates'
                ? 'bg-white text-primary-300'
                : 'text-white hover:bg-primary-200/20'
            }`}
          >
            Candidates
          </button>
          <button
            onClick={() => setActiveTab('jobs')}
            className={`px-6 py-3 rounded-md font-semibold transition-colors ${
              activeTab === 'jobs'
                ? 'bg-white text-primary-300'
                : 'text-white hover:bg-primary-200/20'
            }`}
          >
            Job Postings
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-6 py-3 rounded-md font-semibold transition-colors ${
              activeTab === 'analytics'
                ? 'bg-white text-primary-300'
                : 'text-white hover:bg-primary-200/20'
            }`}
          >
            Analytics
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'candidates' && (
          <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-white">Candidate Pipeline</h2>
              <div className="flex space-x-3">
                <a href="/interview" className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors">
                  Start Interview
                </a>
                <button className="bg-white text-primary-300 px-4 py-2 rounded-lg font-semibold hover:bg-primary-100 hover:text-white transition-colors">
                  Add Candidate
                </button>
              </div>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-primary-200/30">
                    <th className="text-left text-white py-3 px-4">Candidate</th>
                    <th className="text-left text-white py-3 px-4">Position</th>
                    <th className="text-left text-white py-3 px-4">Status</th>
                    <th className="text-left text-white py-3 px-4">Score</th>
                    <th className="text-left text-white py-3 px-4">Interview Date</th>
                    <th className="text-left text-white py-3 px-4">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {mockCandidates.map((candidate) => (
                    <tr key={candidate.id} className="border-b border-primary-200/20 hover:bg-primary-200/10">
                      <td className="py-4 px-4">
                        <div>
                          <div className="text-white font-semibold">{candidate.name}</div>
                          <div className="text-primary-100 text-sm">{candidate.email}</div>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-white">{candidate.position}</td>
                      <td className="py-4 px-4">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(candidate.status)}`}>
                          {candidate.status}
                        </span>
                      </td>
                      <td className="py-4 px-4 text-white">
                        {candidate.score ? `${candidate.score}%` : '-'}
                      </td>
                      <td className="py-4 px-4 text-white">
                        {candidate.interviewDate || '-'}
                      </td>
                      <td className="py-4 px-4">
                        <button
                          onClick={() => setSelectedCandidate(candidate)}
                          className="text-primary-100 hover:text-white transition-colors"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'jobs' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {mockJobPostings.map((job) => (
              <div key={job.id} className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-semibold text-white">{job.title}</h3>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    job.status === 'active' ? 'bg-green-500/20 text-green-300' :
                    job.status === 'paused' ? 'bg-yellow-500/20 text-yellow-300' :
                    'bg-red-500/20 text-red-300'
                  }`}>
                    {job.status}
                  </span>
                </div>
                <p className="text-primary-100 mb-4">{job.department}</p>
                <div className="space-y-2 mb-6">
                  <div className="flex justify-between text-white">
                    <span>Applicants</span>
                    <span>{job.applicants}</span>
                  </div>
                  <div className="flex justify-between text-white">
                    <span>Interviews</span>
                    <span>{job.interviews}</span>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button className="flex-1 bg-white text-primary-300 py-2 px-4 rounded-lg font-semibold hover:bg-primary-100 hover:text-white transition-colors">
                    Manage
                  </button>
                  <button className="flex-1 bg-primary-200 text-white py-2 px-4 rounded-lg font-semibold hover:bg-primary-100 transition-colors">
                    Analytics
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
              <h3 className="text-xl font-semibold text-white mb-6">Interview Performance</h3>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-white mb-2">
                    <span>Technical Skills</span>
                    <span>88%</span>
                  </div>
                  <div className="w-full bg-primary-300 rounded-full h-2">
                    <div className="bg-white h-2 rounded-full" style={{ width: '88%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-white mb-2">
                    <span>Communication</span>
                    <span>82%</span>
                  </div>
                  <div className="w-full bg-primary-300 rounded-full h-2">
                    <div className="bg-white h-2 rounded-full" style={{ width: '82%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-white mb-2">
                    <span>Problem Solving</span>
                    <span>85%</span>
                  </div>
                  <div className="w-full bg-primary-300 rounded-full h-2">
                    <div className="bg-white h-2 rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
              <h3 className="text-xl font-semibold text-white mb-6">Hiring Pipeline</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-white">Applications</span>
                  <span className="text-white font-semibold">156</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white">Screening</span>
                  <span className="text-white font-semibold">45</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white">Interviews</span>
                  <span className="text-white font-semibold">24</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white">Offers</span>
                  <span className="text-white font-semibold">8</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white">Hired</span>
                  <span className="text-white font-semibold">5</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Candidate Detail Modal */}
        {selectedCandidate && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
            <div className="bg-primary-200 rounded-xl p-8 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-white">{selectedCandidate.name}</h3>
                  <p className="text-primary-100">{selectedCandidate.position}</p>
                </div>
                <button
                  onClick={() => setSelectedCandidate(null)}
                  className="text-white hover:text-primary-100"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-lg font-semibold text-white mb-3">Contact Info</h4>
                  <div className="space-y-2">
                    <div className="text-primary-100">{selectedCandidate.email}</div>
                    <div className="text-primary-100">Experience: {selectedCandidate.experience}</div>
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-semibold text-white mb-3">Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedCandidate.skills.map((skill, index) => (
                      <span key={index} className="bg-primary-100/20 text-primary-100 px-3 py-1 rounded-full text-sm">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {selectedCandidate.score && (
                <div className="mt-6">
                  <h4 className="text-lg font-semibold text-white mb-3">Interview Score</h4>
                  <div className="text-3xl font-bold text-white mb-2">{selectedCandidate.score}%</div>
                  <div className="w-full bg-primary-300 rounded-full h-3">
                    <div className="bg-white h-3 rounded-full" style={{ width: `${selectedCandidate.score}%` }}></div>
                  </div>
                </div>
              )}

              <div className="mt-6 flex space-x-4">
                <button className="flex-1 bg-white text-primary-300 py-3 px-4 rounded-lg font-semibold hover:bg-primary-100 hover:text-white transition-colors">
                  Schedule Interview
                </button>
                <button className="flex-1 bg-primary-200 text-white py-3 px-4 rounded-lg font-semibold hover:bg-primary-100 transition-colors">
                  Send Message
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
