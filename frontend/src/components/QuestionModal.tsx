'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronRight, Clock, Loader2 } from 'lucide-react';

interface QuestionModalProps {
  isOpen: boolean;
  question: string;
  questionNumber: number;
  onNext: () => void;
  isLoading: boolean;
}

export default function QuestionModal({
  isOpen,
  question,
  questionNumber,
  onNext,
  isLoading
}: QuestionModalProps) {

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            transition={{ type: "spring", duration: 0.5 }}
            className="relative bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden border border-white/10"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="relative p-6 border-b border-white/10 bg-gradient-to-r from-purple-900/20 to-blue-900/20">
              <div className="flex items-center gap-3 mb-3">
                <div className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-400 text-sm font-medium">
                  Live Interview
                </div>
              </div>

              <h2 className="text-2xl font-bold text-white mb-2">
                Question {questionNumber}
              </h2>
            </div>

            {/* Question Content */}
            <div className="p-8 overflow-y-auto max-h-[50vh]">
              <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                <p className="text-lg text-white leading-relaxed">
                  {question}
                </p>
              </div>

              {/* Status Badge */}
              <div className="mt-4 flex items-center gap-2 text-sm text-gray-400">
                <Clock className="w-4 h-4" />
                <span>Please answer verbally</span>
              </div>
            </div>

            {/* Footer Navigation */}
            <div className="p-6 border-t border-white/10 bg-black/20">
              <div className="flex items-center justify-end">
                <button
                  onClick={onNext}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-white font-medium shadow-lg shadow-blue-500/25"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Generating Next Question...
                    </>
                  ) : (
                    <>
                      Next Question
                      <ChevronRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

