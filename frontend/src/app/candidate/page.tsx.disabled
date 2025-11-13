'use client';

import CandidateDashboard from '@/components/NewCandidateDashboard';
import DashboardLayout from '@/components/DashboardLayout';
import { motion } from 'framer-motion';
import { useRequireAuth } from '@/contexts/AuthContext';

export default function CandidatePage() {
  const { user, isLoading } = useRequireAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-white"></div>
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect to login
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8, ease: "easeInOut" }}
      className="min-h-screen"
    >
      <DashboardLayout>
        <CandidateDashboard />
      </DashboardLayout>
    </motion.div>
  );
}
