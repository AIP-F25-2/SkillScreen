'use client';

export default function Features() {
  const features = [
    {
      title: 'Resume Parsing & Skill Extraction',
      description: 'AI-powered resume analysis that automatically extracts skills, experience timeline, and qualifications.',
      icon: '📄',
      details: [
        'Automatic skill extraction from resumes',
        'Experience timeline mapping',
        'Education and certification parsing',
        'Keyword matching for job requirements'
      ]
    },
    {
      title: 'Job Description Ingestion & Skill Mapping',
      description: 'Intelligent job description analysis that auto-generates role-weighted question sets.',
      icon: '🎯',
      details: [
        'Automatic job requirement analysis',
        'Skill-to-question mapping',
        'Role-specific question generation',
        'Difficulty level assessment'
      ]
    },
    {
      title: 'Interview Templates',
      description: 'Comprehensive interview templates for different roles and assessment types.',
      icon: '📋',
      details: [
        'Behavioral interview questions',
        'Technical assessment templates',
        'System design interviews',
        'Live coding sessions',
        'Case study frameworks'
      ]
    },
    {
      title: 'Candidate Onboarding Checks',
      description: 'Automated pre-interview setup verification for optimal interview experience.',
      icon: '✅',
      details: [
        'Device compatibility testing',
        'Microphone and camera checks',
        'Network speed validation',
        'Room privacy consent verification',
        'Background environment assessment'
      ]
    },
    {
      title: 'Timezone-Aware Scheduling',
      description: 'Smart scheduling with calendar integration and timezone management.',
      icon: '📅',
      details: [
        'Google Calendar integration',
        'Outlook calendar sync',
        'Automatic timezone conversion',
        'Availability conflict detection',
        'Reminder notifications'
      ]
    },
    {
      title: 'AI Interview Analysis',
      description: 'Comprehensive post-interview analysis with detailed feedback and improvement suggestions.',
      icon: '🤖',
      details: [
        'Video analysis (posture, eye contact)',
        'Speech pattern evaluation',
        'Content relevance scoring',
        'Behavioral assessment',
        'Improvement recommendations'
      ]
    }
  ];

  return (
    <section className="py-24 px-6">
      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">Powerful Features</h2>
          <p className="text-lg md:text-xl text-white/80 max-w-3xl mx-auto">
            Our comprehensive AI-powered interview platform revolutionizes the hiring process 
            with intelligent automation and detailed analytics.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          {features.map((feature, index) => (
            <div 
              key={index} 
              className="glass-dark rounded-xl p-8 hover:bg-white/5 transition-all duration-300 transform hover:scale-[1.02]"
            >
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-semibold text-white mb-4">{feature.title}</h3>
              <p className="text-white/70 mb-6">{feature.description}</p>
              
              <div className="space-y-2">
                {feature.details.map((detail, detailIndex) => (
                  <div key={detailIndex} className="flex items-center space-x-2">
                    <div className="w-1.5 h-1.5 bg-white/40 rounded-full"></div>
                    <span className="text-white/60 text-sm">{detail}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        
      </div>
    </section>
  );
}
