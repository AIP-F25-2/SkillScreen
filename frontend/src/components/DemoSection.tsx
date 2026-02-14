"use client";

import React from "react";

export default function DemoSection() {
    return (
        <section id="demo" className="py-24 relative overflow-hidden">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <div className="text-center mb-16">
                    <h2 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
                        See It In Action
                    </h2>
                    <p className="text-xl text-white-200/80 max-w-2xl mx-auto font-light">
                        Watch how SkillScreen transforms the technical interview process with AI-driven insights.
                    </p>
                </div>

                <div className="relative max-w-5xl mx-auto aspect-video rounded-2xl overflow-hidden shadow-2xl border border-white/10 bg-[#1a1a1a]">
                    <iframe
                        width="100%"
                        height="100%"
                        src="https://www.youtube.com/embed/OECWCv-QiJo"
                        title="SkillScreen Demo"
                        frameBorder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowFullScreen
                        className="absolute inset-0 w-full h-full"
                    ></iframe>
                </div>
            </div>

            {/* Background Glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full blur-[120px] pointer-events-none" />
        </section>
    );
}
