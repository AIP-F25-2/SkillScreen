'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronRight, ChevronLeft, Clock } from 'lucide-react';
import { useState, useEffect } from 'react';

interface Question {
  id: string;
  question_index: number;
  question_text: string;
  question_type: string;
  difficulty: string;
  round_number: number;
}

interface QuestionModalProps {
  isOpen: boolean;
  onClose: () => void;
  questions: Question[];
  currentQuestionIndex: number;
  onQuestionChange?: (index: number) => void;
}

export default function QuestionModal({ 
  isOpen, 
  onClose, 
  questions,
  currentQuestionIndex,
  onQuestionChange 
}: QuestionModalProps) {
  const [selectedIndex, setSelectedIndex] = useState(currentQuestionIndex);

  useEffect(() => {
    setSelectedIndex(currentQuestionIndex);
  }, [currentQuestionIndex]);

  const currentQuestion = questions[selectedIndex] || null;

  const handleNext = () => {
    if (selectedIndex < questions.length - 1) {
      const newIndex = selectedIndex + 1;
      setSelectedIndex(newIndex);
      onQuestionChange?.(newIndex);
    }
  };

  const handlePrevious = () => {
    if (selectedIndex > 0) {
      const newIndex = selectedIndex - 1;
      setSelectedIndex(newIndex);
      onQuestionChange?.(newIndex);
    }
  };

  const getRoundInfo = (roundNumber: number) => {
    switch (roundNumber) {
      case 1:
        return { title: 'Round 1: General Assessment', color: 'text-blue-400', bg: 'bg-blue-500/20' };
      case 2:
        return { title: 'Round 2: Technical Assessment', color: 'text-purple-400', bg: 'bg-purple-500/20' };
      case 3:
        return { title: 'Round 3: Theoretical Assessment', color: 'text-green-400', bg: 'bg-green-500/20' };
      default:
        return { title: 'Assessment', color: 'text-gray-400', bg: 'bg-gray-500/20' };
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return 'text-green-400';
      case 'medium':
        return 'text-yellow-400';
      case 'hard':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  if (!isOpen || !currentQuestion) return null;

  const roundInfo = getRoundInfo(currentQuestion.round_number);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
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
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 rounded-lg bg-white/10 hover:bg-white/20 transition-colors"
              >
                <X className="w-5 h-5 text-white" />
              </button>
              
              <div className="flex items-center gap-3 mb-3">
                <div className={`px-3 py-1 rounded-full ${roundInfo.bg} ${roundInfo.color} text-sm font-medium`}>
                  {roundInfo.title}
                </div>
                <div className={`px-3 py-1 rounded-full bg-white/10 ${getDifficultyColor(currentQuestion.difficulty)} text-sm font-medium`}>
                  {currentQuestion.difficulty.charAt(0).toUpperCase() + currentQuestion.difficulty.slice(1)}
                </div>
              </div>
              
              <h2 className="text-2xl font-bold text-white mb-2">
                Question {currentQuestion.question_index + 1} of {questions.length}
              </h2>
              
              {/* Progress bar */}
              <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${((selectedIndex + 1) / questions.length) * 100}%` }}
                  className="h-full bg-gradient-to-r from-purple-500 to-blue-500"
                />
              </div>
            </div>

            {/* Question Content */}
            <div className="p-8 overflow-y-auto max-h-[50vh]">
              <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                <p className="text-lg text-white leading-relaxed">
                  {currentQuestion.question_text}
                </p>
              </div>

              {/* Question Type Badge */}
              <div className="mt-4 flex items-center gap-2 text-sm text-gray-400">
                <Clock className="w-4 h-4" />
                <span>Type: {currentQuestion.question_type.charAt(0).toUpperCase() + currentQuestion.question_type.slice(1)}</span>
              </div>
            </div>

            {/* Footer Navigation */}
            <div className="p-6 border-t border-white/10 bg-black/20">
              <div className="flex items-center justify-between">
                <button
                  onClick={handlePrevious}
                  disabled={selectedIndex === 0}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-white"
                >
                  <ChevronLeft className="w-5 h-5" />
                  Previous
                </button>

                <div className="text-sm text-gray-400">
                  {selectedIndex + 1} / {questions.length}
                </div>

                <button
                  onClick={handleNext}
                  disabled={selectedIndex === questions.length - 1}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-white"
                >
                  Next
                  <ChevronRight className="w-5 h-5" />
                </button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

