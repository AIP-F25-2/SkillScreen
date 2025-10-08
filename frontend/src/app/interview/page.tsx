'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import ModernInterviewScreen from '@/components/ModernInterviewScreen';
import { useAuth } from '@/contexts/AuthContext';

export default function InterviewPage() {
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const [userType, setUserType] = useState<'candidate' | 'recruiter'>('candidate');
  const [interviewId, setInterviewId] = useState('interview-123');
  const [participantName, setParticipantName] = useState('');

  useEffect(() => {
    // Get interview ID from URL or default
    const id = searchParams?.get('id');
    if (id) {
      setInterviewId(id);
    }

    // Get participant name from URL or user data
    const name = searchParams?.get('name');
    if (name) {
      setParticipantName(decodeURIComponent(name));
    } else if (user) {
      setParticipantName(user.fullName);
    } else {
      setParticipantName('Guest User');
    }

    // Determine user type
    if (user) {
      setUserType(user.userType === 'recruiter' ? 'recruiter' : 'candidate');
    }
  }, [searchParams, user]);

  return (
    <div className="fixed inset-0 bg-[#1E1E1E] overflow-hidden">
      <ModernInterviewScreen
        userType={userType}
        participantName={participantName}
      />
    </div>
  );
}
