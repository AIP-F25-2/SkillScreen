'use client';

import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import ModernInterviewScreen from '@/components/ModernInterviewScreen';
import { useAuth } from '@/contexts/AuthContext';

export default function InterviewPage() {
  const searchParams = useSearchParams();
  const { user } = useAuth();
  const [participantName, setParticipantName] = useState('');

  useEffect(() => {
    // Get participant name from URL or user data
    const name = searchParams?.get('name');
    if (name) {
      setParticipantName(decodeURIComponent(name));
    } else if (user) {
      // Try to construct participant name from user object
      if ('firstName' in user && 'lastName' in user && user.firstName && user.lastName) {
        setParticipantName(`${user.firstName} ${user.lastName}`);
      } else if ('name' in user && user.name) {
        setParticipantName(user.name);
      } else {
        setParticipantName('Guest User');
      }
    }
  }, [searchParams, user]);

  return (
    <div className="fixed inset-0 bg-[#1E1E1E] overflow-hidden">
      <ModernInterviewScreen
        participantName={participantName}
      />
    </div>
  );
}
