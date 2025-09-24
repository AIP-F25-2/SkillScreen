'use client';

export default function Hero() {
  return (
    <main className="relative z-10 flex flex-col items-center justify-center min-h-[90vh] px-6 md:px-12 text-center pt-24">
      {/* Welcome Banner */}
      <div className="mb-8">
        <div className="inline-block bg-primary-200 px-6 py-2 rounded-full">
          <span className="text-white text-sm font-medium tracking-wide">
            Welcome to IntervuAI
          </span>
        </div>
      </div>

      {/* Main Headline */}
      <div className="mb-8 max-w-4xl">
        <h1 className="text-5xl md:text-7xl font-bold text-white leading-tight mb-6">
          <span className="block">Revolutionize</span>
          <span className="block bg-white/10 backdrop-blur-sm px-8 py-4 rounded-2xl inline-block">
            Technical Interviews
          </span>
          <span className="block">With AI Precision</span>
        </h1>
      </div>

      {/* Description */}
      <div className="mb-12 max-w-2xl">
        <p className="text-lg md:text-xl text-white leading-relaxed">
          Elevate your technical hiring with our AI-driven platform. Conduct fair, consistent, and 
          comprehensive coding interviews that assess real-world skills and potential. Perfect for 
          tech companies seeking exceptional talent.
        </p>
      </div>

      {/* Call to Action Button */}
      <div className="mb-16">
        <button className="bg-white text-primary-300 px-8 py-4 rounded-xl font-semibold text-lg hover:bg-primary-100 hover:text-white transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl">
          Start Hiring Better Engineers Today
        </button>
      </div>

      {/* Additional Features Preview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl">
        <div className="text-center">
          <div className="w-16 h-16 bg-primary-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-white font-semibold text-lg mb-2">AI Code Analysis</h3>
          <p className="text-primary-100 text-sm">Real-time evaluation of coding skills and problem-solving approach</p>
        </div>

        <div className="text-center">
          <div className="w-16 h-16 bg-primary-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-white font-semibold text-lg mb-2">Interactive IDE</h3>
          <p className="text-primary-100 text-sm">Full-featured coding environment with real-time collaboration</p>
        </div>

        <div className="text-center">
          <div className="w-16 h-16 bg-primary-200 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-white font-semibold text-lg mb-2">Detailed Reports</h3>
          <p className="text-primary-100 text-sm">In-depth analysis of technical skills and code quality</p>
        </div>
      </div>
    </main>
  );
}
