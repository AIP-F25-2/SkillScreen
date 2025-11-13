'use client';

import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { ShieldAlert } from 'lucide-react';

// CANDIDATE DASHBOARD DISABLED
// Candidates now access interviews via email links only
// Original code saved in page.tsx.disabled

export default function CandidateDisabledPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0A0A0A] via-[#1E1E1E] to-[#0A0A0A] flex items-center justify-center p-6">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center max-w-md px-6"
      >
        <ShieldAlert className="w-24 h-24 text-yellow-400 mx-auto mb-6" />
        <h1 className="text-white text-3xl font-bold mb-4">Candidate Access Changed</h1>
        <p className="text-white/70 text-lg mb-6">
          Candidate dashboards are no longer accessible directly. You will receive an email invitation with a unique interview link.
        </p>
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-4 mb-6">
          <p className="text-blue-300 text-sm">
            <strong>To start your interview:</strong>
          </p>
          <p className="text-white/60 text-sm mt-2">
            Check your email for the interview invitation link sent by your recruiter.
          </p>
        </div>
        <button
          onClick={() => router.push('/')}
          className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
        >
          Go to Home
        </button>
      </motion.div>
    </div>
  );
}

