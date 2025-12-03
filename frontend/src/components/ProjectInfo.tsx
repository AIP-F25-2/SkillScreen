"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import Image from "next/image";

export default function ProjectInfo() {
    const [selectedId, setSelectedId] = useState<number | null>(null);

    const cards = [
        {
            title: "AI Analysis",
            description: "Automated code review and behavioral analysis using state-of-the-art LLMs.",
            details: "Our system utilizes advanced Large Language Models to analyze candidate code for efficiency, readability, and best practices. It also evaluates behavioral responses, providing a comprehensive report on soft skills and cultural fit, ensuring a holistic view of every candidate. The dashboard provides a detailed breakdown of scores across various metrics.",
            image: "/screenshots/ai-analysis.png",
            delay: 0.1
        },
        {
            title: "Real-time",
            description: "Live coding environment with collaborative features and instant feedback.",
            details: "Experience a seamless collaborative coding environment. The platform supports multiple languages, syntax highlighting, and real-time execution, allowing interviewers and candidates to code together without latency, mimicking real-world pair programming. See changes instantly as they happen.",
            image: "/screenshots/realtime.png",
            delay: 0.2
        },
        {
            title: "Secure",
            description: "Enterprise-grade security with proctoring and cheat detection mechanisms.",
            details: "We prioritize data integrity and fairness. Our proctoring suite includes gaze tracking, tab-switch monitoring, and identity verification to ensure the authenticity of every assessment. The interview setup process ensures all security checks are passed before the session begins.",
            image: "/screenshots/secure.png",
            delay: 0.3
        },
        {
            title: "Scalable",
            description: "Microservices architecture ensuring high availability and easy scaling.",
            details: "Designed for growth. Our microservices architecture allows individual components to scale independently, ensuring reliability and performance even during peak usage periods. Whether you're interviewing 10 or 10,000 candidates, SkillScreen handles the load effortlessly.",
            image: "/screenshots/scalable.png",
            delay: 0.4
        }
    ];

    return (
        <section className="py-24 relative overflow-hidden">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <div className="text-center mb-16">
                    <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
                        About The Project
                    </h2>
                    <p className="text-xl text-indigo-200/80 max-w-3xl mx-auto font-light">
                        SkillScreen is a cutting-edge platform designed to streamline technical recruitment using advanced Artificial Intelligence.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center mb-20">
                    <div className="space-y-6">
                        <h3 className="text-3xl font-bold text-white">
                            Modern Tech Stack
                        </h3>
                        <p className="text-lg text-gray-300 leading-relaxed">
                            Built with performance and scalability in mind, SkillScreen leverages the latest web technologies to deliver a seamless user experience.
                        </p>
                        <ul className="space-y-4">
                            <li className="flex items-center text-indigo-200">
                                <span className="w-2 h-2 bg-indigo-500 rounded-full mr-3" />
                                <span className="font-semibold text-white mr-2">Frontend:</span> Next.js 14, React, Tailwind CSS, Framer Motion
                            </li>
                            <li className="flex items-center text-indigo-200">
                                <span className="w-2 h-2 bg-indigo-500 rounded-full mr-3" />
                                <span className="font-semibold text-white mr-2">Backend:</span> Python, FastAPI, Microservices Architecture
                            </li>
                            <li className="flex items-center text-indigo-200">
                                <span className="w-2 h-2 bg-indigo-500 rounded-full mr-3" />
                                <span className="font-semibold text-white mr-2">AI/ML:</span> OpenAI GPT-4, Whisper, Custom Evaluation Models
                            </li>
                            <li className="flex items-center text-indigo-200">
                                <span className="w-2 h-2 bg-indigo-500 rounded-full mr-3" />
                                <span className="font-semibold text-white mr-2">Infrastructure:</span> Docker, Kubernetes, Cloud Deployment
                            </li>
                        </ul>
                    </div>
                    <div className="relative">
                        <div className="absolute inset-0 bg-indigo-500/20 blur-3xl rounded-full" />
                        <div className="relative grid grid-cols-2 gap-4">
                            {cards.map((card, index) => (
                                <motion.div
                                    key={index}
                                    layoutId={`card-${index}`}
                                    onClick={() => setSelectedId(index)}
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ duration: 0.5, delay: card.delay }}
                                    whileHover={{ scale: 1.02 }}
                                    className={`cursor-pointer ${index % 2 === 1 ? 'mt-8' : ''}`}
                                >
                                    <Card className="bg-[#1a1a1a] border-white/10 p-6 h-[280px] flex flex-col justify-center hover:border-indigo-500/50 transition-colors duration-300">
                                        <CardHeader className="p-0 mb-4">
                                            <CardTitle className="text-indigo-400 text-xl">{card.title}</CardTitle>
                                        </CardHeader>
                                        <CardContent className="p-0 text-gray-400">
                                            {card.description}
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <AnimatePresence>
                {selectedId !== null && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setSelectedId(null)}
                            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                        />
                        <motion.div
                            layoutId={`card-${selectedId}`}
                            className="w-full max-w-2xl bg-indigo-500/20 border border-white/10 rounded-xl overflow-hidden relative z-10 shadow-2xl max-h-[90vh] flex flex-col backdrop-blur-xl"
                        >
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    setSelectedId(null);
                                }}
                                className="absolute top-4 right-4 p-2 rounded-full bg-black/50 hover:bg-black/70 text-white transition-colors z-20 backdrop-blur-md"
                            >
                                <X className="w-5 h-5" />
                            </button>

                            <div className="relative h-64 w-full shrink-0 bg-indigo-500/20">
                                <Image
                                    src={cards[selectedId].image}
                                    alt={cards[selectedId].title}
                                    fill
                                    className="object-cover"
                                    onError={(e) => {
                                        // Fallback if image fails
                                        e.currentTarget.style.display = 'none';
                                    }}
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-indigo-900/50 to-transparent" />
                            </div>

                            <div className="p-8 overflow-y-auto bg-transparent">
                                <motion.h3 className="text-3xl font-bold text-indigo-400 mb-4">
                                    {cards[selectedId].title}
                                </motion.h3>
                                <motion.p className="text-gray-100 text-lg leading-relaxed">
                                    {cards[selectedId].details}
                                </motion.p>
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </section>
    );
}
