"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { motion } from "framer-motion";

export default function ProjectInfo() {
    const cards = [
        {
            title: "AI Analysis",
            content: "Automated code review and behavioral analysis using state-of-the-art LLMs.",
            delay: 0.1
        },
        {
            title: "Real-time",
            content: "Live coding environment with collaborative features and instant feedback.",
            delay: 0.2
        },
        {
            title: "Secure",
            content: "Enterprise-grade security with proctoring and cheat detection mechanisms.",
            delay: 0.3
        },
        {
            title: "Scalable",
            content: "Microservices architecture ensuring high availability and easy scaling.",
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
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ duration: 0.5, delay: card.delay }}
                                    whileHover={{ scale: 1.05, zIndex: 10 }}
                                    className={`${index % 2 === 1 ? 'mt-8' : ''}`}
                                >
                                    <Card className="bg-[#1a1a1a] border-white/10 p-6 h-[280px] flex flex-col justify-center hover:border-indigo-500/50 transition-colors duration-300">
                                        <CardHeader className="p-0 mb-4">
                                            <CardTitle className="text-indigo-400 text-xl">{card.title}</CardTitle>
                                        </CardHeader>
                                        <CardContent className="p-0 text-gray-400">
                                            {card.content}
                                        </CardContent>
                                    </Card>
                                </motion.div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
