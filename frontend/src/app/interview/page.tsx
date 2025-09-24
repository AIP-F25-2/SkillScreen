'use client';

import { useState } from 'react';
import NavBar from '@/components/NavBar';
import ModernInterviewScreen from '@/components/ModernInterviewScreen';

export default function InterviewPage() {
  const [userType, setUserType] = useState<'candidate' | 'recruiter'>('candidate');
  const [interviewId] = useState('interview-123');
  const [participantName] = useState(userType === 'candidate' ? 'John Doe' : 'Sarah Johnson');

  return (
    <div className="fixed inset-0 bg-[#1E1E1E] overflow-hidden">
      <ModernInterviewScreen
        userType={userType}
        participantName={participantName}
      />
    </div>
  );
}
