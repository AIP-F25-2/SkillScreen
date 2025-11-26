'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, Search, FileText, Clock, MessageSquare } from 'lucide-react';
import { useState } from 'react';

interface TranscriptModalProps {
    isOpen: boolean;
    onClose: () => void;
    transcript: {
        text: string;
        duration_seconds?: number;
        word_count?: number;
        language?: string;
    };
    candidateName?: string;
    date?: string;
}

export default function TranscriptModal({
    isOpen,
    onClose,
    transcript,
    candidateName,
    date
}: TranscriptModalProps) {
    const [searchQuery, setSearchQuery] = useState('');

    const downloadTranscript = () => {
        const blob = new Blob([transcript.text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transcript-${candidateName?.replace(/\s+/g, '-').toLowerCase() || 'interview'}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // Highlight search terms in text
    const getHighlightedText = (text: string, query: string) => {
        if (!query) return text;
        const parts = text.split(new RegExp(`(${query})`, 'gi'));
        return parts.map((part, i) =>
            part.toLowerCase() === query.toLowerCase() ? (
                <span key={i} className="bg-yellow-500/40 text-white px-1 rounded">{part}</span>
            ) : (
                part
            )
        );
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 20 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 pointer-events-none"
                    >
                        <div className="bg-[#1E1E1E] border border-white/10 w-full max-w-4xl max-h-[85vh] rounded-2xl shadow-2xl flex flex-col pointer-events-auto overflow-hidden">
                            {/* Header */}
                            <div className="p-6 border-b border-white/10 flex items-center justify-between bg-white/5">
                                <div className="flex items-center gap-4">
                                    <div className="p-3 bg-blue-500/20 rounded-lg">
                                        <FileText className="w-6 h-6 text-blue-400" />
                                    </div>
                                    <div>
                                        <h2 className="text-xl font-bold text-white">Interview Transcript</h2>
                                        <div className="flex items-center gap-3 text-sm text-white/50 mt-1">
                                            <span>{candidateName || 'Unknown Candidate'}</span>
                                            <span>•</span>
                                            <span>{date ? new Date(date).toLocaleDateString() : 'Unknown Date'}</span>
                                        </div>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <button
                                        onClick={downloadTranscript}
                                        className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg transition-colors border border-white/10 text-sm font-medium"
                                    >
                                        <Download className="w-4 h-4" />
                                        Export
                                    </button>
                                    <button
                                        onClick={onClose}
                                        className="p-2 hover:bg-white/10 rounded-lg text-white/50 hover:text-white transition-colors"
                                    >
                                        <X className="w-6 h-6" />
                                    </button>
                                </div>
                            </div>

                            {/* Stats Bar */}
                            <div className="grid grid-cols-3 border-b border-white/10 bg-black/20 divide-x divide-white/10">
                                <div className="p-4 flex items-center justify-center gap-3">
                                    <Clock className="w-5 h-5 text-white/40" />
                                    <div className="text-center">
                                        <div className="text-xs text-white/40 uppercase tracking-wider font-medium">Duration</div>
                                        <div className="text-white font-semibold">
                                            {transcript.duration_seconds
                                                ? `${Math.floor(transcript.duration_seconds / 60)}m ${Math.floor(transcript.duration_seconds % 60)}s`
                                                : 'N/A'}
                                        </div>
                                    </div>
                                </div>
                                <div className="p-4 flex items-center justify-center gap-3">
                                    <MessageSquare className="w-5 h-5 text-white/40" />
                                    <div className="text-center">
                                        <div className="text-xs text-white/40 uppercase tracking-wider font-medium">Word Count</div>
                                        <div className="text-white font-semibold">{transcript.word_count || 0}</div>
                                    </div>
                                </div>
                                <div className="p-4 flex items-center justify-center gap-3">
                                    <div className="text-xs font-bold bg-white/10 px-2 py-1 rounded text-white/60">EN</div>
                                    <div className="text-center">
                                        <div className="text-xs text-white/40 uppercase tracking-wider font-medium">Language</div>
                                        <div className="text-white font-semibold">{transcript.language || 'English'}</div>
                                    </div>
                                </div>
                            </div>

                            {/* Search Bar */}
                            <div className="p-4 border-b border-white/10 bg-white/5">
                                <div className="relative">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                                    <input
                                        type="text"
                                        placeholder="Search in transcript..."
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                        className="w-full bg-black/20 border border-white/10 rounded-lg pl-10 pr-4 py-2.5 text-white placeholder-white/30 focus:outline-none focus:border-blue-500/50 transition-colors"
                                    />
                                </div>
                            </div>

                            {/* Content */}
                            <div className="flex-1 overflow-y-auto p-6 bg-[#111111]">
                                <div className="prose prose-invert max-w-none">
                                    <p className="text-white/80 leading-relaxed whitespace-pre-wrap font-light text-lg">
                                        {getHighlightedText(transcript.text, searchQuery)}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
