'use client';

import { useState, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ModernInterviewScreen from '@/components/ModernInterviewScreen';
import { useAuth } from '@/contexts/AuthContext';
import { useCheatPrevention } from '@/contexts/CheatPreventionContext';
import { getInterviewToken } from '@/lib/interviewToken';

export default function InterviewPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user } = useAuth();
  const { enableProtection } = useCheatPrevention();
  const [participantName, setParticipantName] = useState('');
  const [fromToken, setFromToken] = useState(false);

  useEffect(() => {
    // Check if coming from email token
    const isFromToken = searchParams?.get('fromToken') === 'true';
    setFromToken(isFromToken);

    // Get participant name from URL or user data
    const name = searchParams?.get('name');
    if (name) {
      setParticipantName(decodeURIComponent(name));
    } else if (isFromToken) {
      // Get from token
      const tokenData = getInterviewToken();
      if (tokenData) {
        setParticipantName(tokenData.candidateName);
      } else {
        // No valid token, redirect
        router.push('/');
        return;
      }
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

    // Enable cheat prevention for token-based interviews
    if (isFromToken) {
      enableProtection();
    }
  }, [searchParams, user, enableProtection, router]);

  return (
    <div className="fixed inset-0 bg-[#1E1E1E] overflow-hidden">
      <ModernInterviewScreen
        participantName={participantName}
        fromToken={fromToken}
      />
    </div>
  );
}
