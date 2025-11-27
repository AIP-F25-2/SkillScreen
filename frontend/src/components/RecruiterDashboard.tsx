'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { FileUploadDemo } from '@/components/ui/file-upload-demo';
import { apiClient } from '@/lib/api';
import { FileText, User } from 'lucide-react';

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

interface JobTemplate {
  id: string;
  title: string;
  department: string;
  content: string;
  required_skills?: string[];
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


export default function RecruiterDashboard() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'interviews' | 'candidates' | 'jobs' | 'analytics'>('interviews');
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [interviews, setInterviews] = useState<any[]>([]);
  const [loadingInterviews, setLoadingInterviews] = useState(true);
  const [candidates, setCandidates] = useState<any[]>([]);
  const [loadingCandidates, setLoadingCandidates] = useState(true);

  // Job Description Management state
  const [jobTemplates, setJobTemplates] = useState<JobTemplate[]>([{
    id: 'tmpl-1',
    title: 'Senior Software Engineer',
    department: 'Engineering',
    content: 'We are seeking a Senior Software Engineer with experience in React, Node.js, and cloud-native architectures. Responsibilities include building scalable features, mentoring, and collaborating across teams.',
    required_skills: ['React', 'Node.js', 'TypeScript', 'AWS', 'Docker']
  }]);
  const [templateTitle, setTemplateTitle] = useState('');
  const [templateDepartment, setTemplateDepartment] = useState('');
  const [templateContent, setTemplateContent] = useState('');
  const [templateSkills, setTemplateSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState('');
  const [editingTemplateId, setEditingTemplateId] = useState<string | null>(null);

  // Fetch all interviews and candidates
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoadingInterviews(true);
        setLoadingCandidates(true);

        // Fetch all interviews
        const interviewsResponse = await apiClient.getAllInterviews();
        if (interviewsResponse.success) {
          setInterviews(interviewsResponse.data.interviews || []);
        }

        // Fetch all candidates
        const candidatesResponse = await apiClient.getAllCandidates();
        if (candidatesResponse.success) {
          setCandidates(candidatesResponse.data.candidates || []);
        }
      } catch (error) {
        console.error('Failed to fetch data:', error);
      } finally {
        setLoadingInterviews(false);
        setLoadingCandidates(false);
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
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch {
      return 'Unknown';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500/20 text-green-300';
      case 'scheduled': return 'bg-blue-500/20 text-blue-300';
      case 'pending': return 'bg-yellow-500/20 text-yellow-300';
      case 'rejected': return 'bg-red-500/20 text-red-300';
      default: return 'bg-gray-500/20 text-gray-300';
    }
  };

  const resetTemplateForm = () => {
    setTemplateTitle('');
    setTemplateDepartment('');
    setTemplateContent('');
    setTemplateSkills([]);
    setSkillInput('');
    setEditingTemplateId(null);
  };

  const saveTemplate = () => {
    const trimmedTitle = templateTitle.trim();
    const trimmedDept = templateDepartment.trim();
    const trimmedContent = templateContent.trim();
    if (!trimmedTitle || !trimmedDept || !trimmedContent) return;

    if (editingTemplateId) {
      setJobTemplates(prev => prev.map(t => t.id === editingTemplateId ? {
        ...t,
        title: trimmedTitle,
        department: trimmedDept,
        content: trimmedContent,
        required_skills: templateSkills.length > 0 ? templateSkills : undefined,
      } : t));
    } else {
      const newTemplate: JobTemplate = {
        id: `tmpl-${Date.now()}`,
        title: trimmedTitle,
        department: trimmedDept,
        content: trimmedContent,
        required_skills: templateSkills.length > 0 ? templateSkills : undefined,
      };
      setJobTemplates(prev => [newTemplate, ...prev]);
    }
    resetTemplateForm();
  };

  const editTemplate = (template: JobTemplate) => {
    setTemplateTitle(template.title);
    setTemplateDepartment(template.department);
    setTemplateContent(template.content);
    setTemplateSkills(template.required_skills || []);
    setEditingTemplateId(template.id);
  };

  const addSkill = () => {
    const trimmedSkill = skillInput.trim();
    if (trimmedSkill && !templateSkills.includes(trimmedSkill)) {
      setTemplateSkills(prev => [...prev, trimmedSkill]);
      setSkillInput('');
    }
  };

  const removeSkill = (skillToRemove: string) => {
    setTemplateSkills(prev => prev.filter(skill => skill !== skillToRemove));
  };

  const handleSkillKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addSkill();
    }
  };

  const deleteTemplate = (id: string) => {
    setJobTemplates(prev => prev.filter(t => t.id !== id));
    if (editingTemplateId === id) resetTemplateForm();
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
            onClick={() => setActiveTab('interviews')}
            className={`px-6 py-3 rounded-md font-semibold transition-colors ${
              activeTab === 'interviews'
                ? 'bg-white text-primary-300'
                : 'text-white hover:bg-primary-200/20'
            }`}
          >
            Interviews
          </button>
         
          <button
            onClick={() => setActiveTab('jobs')}
            className={`px-6 py-3 rounded-md font-semibold transition-colors ${
              activeTab === 'jobs'
                ? 'bg-white text-primary-300'
                : 'text-white hover:bg-primary-200/20'
            }`}
          >
            Active Job Listings
          </button>
        </div>

        {/* Tab Content */}
        {/* Interviews Tab */}
        {activeTab === 'interviews' && (
          <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
            {/* Document Upload */}
            <div className="mb-8">
              <FileUploadDemo />
            </div>
            <div className="flex justify-between items-center mb-6">
              
              <h2 className="text-2xl font-semibold text-white flex items-center gap-2">
                <FileText className="w-6 h-6" />
                All Interviews
              </h2>
              <span className="text-primary-100">
                {interviews.length} total interviews
              </span>
            </div>

            {loadingInterviews ? (
              <div className="flex justify-center py-12">
                <div className="w-8 h-8 border-4 border-white border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : interviews.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-16 h-16 text-white/30 mx-auto mb-4" />
                <p className="text-white/60">No interviews yet</p>
                <p className="text-white/40 text-sm">Scheduled and completed interviews will appear here</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left py-3 px-4 text-white/80 font-medium">Candidate</th>
                      <th className="text-left py-3 px-4 text-white/80 font-medium">User</th>
                      <th className="text-left py-3 px-4 text-white/80 font-medium">Date</th>
                      <th className="text-left py-3 px-4 text-white/80 font-medium">Duration</th>
                      <th className="text-left py-3 px-4 text-white/80 font-medium">Words</th>
                      <th className="text-left py-3 px-4 text-white/80 font-medium">Status</th>
                      <th className="text-left py-3 px-4 text-white/80 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {interviews.map((interview) => (
                      <tr key={interview.interview_id} className="border-b border-white/5 hover:bg-white/5">
                        <td className="py-4 px-4">
                          <div className="flex items-center gap-3">
                            <div className="bg-blue-500/20 rounded-full p-2">
                              <User className="w-5 h-5 text-blue-300" />
                            </div>
                            <span className="text-white font-medium">{interview.candidate_name || interview.candidate_id}</span>
                          </div>
                        </td>
                        <td className="py-4 px-4 text-white/80">{interview.assigned_user || interview.user_id || '-'}</td>
                        <td className="py-4 px-4 text-white/80">{formatDate(interview.created_at || interview.scheduled_at)}</td>
                        <td className="py-4 px-4 text-white/80">
                          {interview.transcript?.duration_seconds 
                            ? `${Math.floor(interview.transcript.duration_seconds / 60)}m`
                            : '-'}
                        </td>
                        <td className="py-4 px-4 text-white/80">
                          {interview.transcript?.word_count || '-'}
                        </td>
                        <td className="py-4 px-4">
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(interview.status)}`}>
                            {interview.status}
                          </span>
                        </td>
                        <td className="py-4 px-4">
                          <button
                            onClick={() => router.push(`/interview-summary?id=${interview.interview_id}`)}
                            className="text-blue-400 hover:text-blue-300 font-medium"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Candidates Tab */}
        {activeTab === 'candidates' && (
          <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-semibold text-white">Candidate Pipeline</h2>
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
          <div className="bg-primary-200/20 backdrop-blur-sm rounded-xl p-6 border border-primary-200/30">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-white">Job Description Management</h2>
            </div>

            {/* Template Form */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1 bg-primary-200/10 rounded-xl p-5 border border-primary-200/20">
                <h3 className="text-lg font-semibold text-white mb-4">{editingTemplateId ? 'Edit Template' : 'Add New Template'}</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-primary-100 mb-1">Title</label>
                    <input
                      value={templateTitle}
                      onChange={(e) => setTemplateTitle(e.target.value)}
                      placeholder="e.g., Senior Backend Engineer"
                      className="w-full rounded-lg bg-transparent border border-primary-200/40 text-white px-3 py-2 focus:outline-none focus:border-white/60"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-primary-100 mb-1">Department</label>
                    <input
                      value={templateDepartment}
                      onChange={(e) => setTemplateDepartment(e.target.value)}
                      placeholder="e.g., Engineering"
                      className="w-full rounded-lg bg-transparent border border-primary-200/40 text-white px-3 py-2 focus:outline-none focus:border-white/60"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-primary-100 mb-1">Description</label>
                    <textarea
                      value={templateContent}
                      onChange={(e) => setTemplateContent(e.target.value)}
                      placeholder="Role summary, responsibilities, requirements, and nice-to-haves..."
                      className="w-full min-h-[140px] rounded-lg bg-transparent border border-primary-200/40 text-white px-3 py-2 focus:outline-none focus:border-white/60"
                    />
                  </div>

                  <div>
                    <label className="block text-sm text-primary-100 mb-1">Required Skills</label>
                    <div className="flex gap-2 mb-2">
                      <input
                        value={skillInput}
                        onChange={(e) => setSkillInput(e.target.value)}
                        onKeyDown={handleSkillKeyDown}
                        placeholder="e.g., React, Python, AWS"
                        className="flex-1 rounded-lg bg-transparent border border-primary-200/40 text-white px-3 py-2 focus:outline-none focus:border-white/60"
                      />
                      <button
                        type="button"
                        onClick={addSkill}
                        className="px-4 py-2 bg-primary-200/40 hover:bg-primary-200/60 text-white rounded-lg transition-colors"
                      >
                        Add
                      </button>
                    </div>
                    {templateSkills.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {templateSkills.map((skill, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center gap-1 px-3 py-1 bg-primary-200/20 border border-primary-200/40 text-white rounded-full text-sm"
                          >
                            {skill}
                            <button
                              type="button"
                              onClick={() => removeSkill(skill)}
                              className="ml-1 hover:text-red-300 transition-colors"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={saveTemplate}
                      className="flex-1 bg-white text-primary-300 py-2 px-4 rounded-lg font-semibold hover:bg-primary-100 hover:text-white transition-colors"
                    >
                      {editingTemplateId ? 'Update Template' : 'Save Template'}
                    </button>
                    {editingTemplateId && (
                      <button
                        onClick={resetTemplateForm}
                        className="px-4 py-2 rounded-lg font-semibold text-white bg-primary-200/40 hover:bg-primary-200/60 transition-colors"
                      >
                        Cancel
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Templates List */}
              <div className="lg:col-span-2">
                {jobTemplates.length === 0 ? (
                  <div className="text-center py-12 border border-primary-200/20 rounded-xl">
                    <p className="text-white/70">No templates yet. Create your first job description template on the left.</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {jobTemplates.map((t) => (
                      <div key={t.id} className="bg-primary-200/10 rounded-xl p-5 border border-primary-200/20">
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div>
                            <h4 className="text-white font-semibold">{t.title}</h4>
                            <p className="text-primary-100 text-sm">{t.department}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => editTemplate(t)}
                              className="text-white/80 hover:text-white text-sm font-medium"
                            >
                              Edit
                            </button>
                            <span className="text-white/20">|</span>
                            <button
                              onClick={() => deleteTemplate(t.id)}
                              className="text-red-300/80 hover:text-red-300 text-sm font-medium"
                            >
                              Delete
                            </button>
                          </div>
                        </div>
                        <p className="text-white/80 text-sm whitespace-pre-line mb-3">
                          {t.content}
                        </p>
                        {t.required_skills && t.required_skills.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-primary-200/20">
                            <p className="text-xs text-primary-100 mb-2">Required Skills:</p>
                            <div className="flex flex-wrap gap-1.5">
                              {t.required_skills.map((skill, idx) => (
                                <span
                                  key={idx}
                                  className="px-2 py-0.5 bg-primary-200/10 border border-primary-200/30 text-white/90 rounded text-xs"
                                >
                                  {skill}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div className="grid grid-cols-1 lg:grid-cols-1 gap-8">
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
