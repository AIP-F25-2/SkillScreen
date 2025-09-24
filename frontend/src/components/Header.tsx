'use client';

import { useState } from 'react';
import Image from 'next/image';

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <header className="relative z-20 px-6 py-8 md:px-12">
      <nav className="flex items-center justify-between">
        {/* Logo */}
        <a href="/" className="flex items-center space-x-3">
          <Image src="/logo.png" alt="InterviewAI" width={40} height={40} />
          <span className="text-white text-2xl font-bold tracking-wide">
            INTERVUAI
          </span>
        </a>

        {/* Desktop Navigation */}
        <div className="hidden md:flex items-center space-x-8">
          <a 
            href="/features" 
            className="text-white hover:text-primary-100 transition-colors duration-300 font-medium"
          >
            Features
          </a>
          <a 
            href="/candidate" 
            className="text-white hover:text-primary-100 transition-colors duration-300 font-medium"
          >
            Candidate Dashboard
          </a>
          <a 
            href="/recruiter" 
            className="text-white hover:text-primary-100 transition-colors duration-300 font-medium"
          >
            Recruiter Dashboard
          </a>
          <a 
            href="#contact" 
            className="text-white hover:text-primary-100 transition-colors duration-300 font-medium"
          >
            Contact
          </a>
        </div>

        {/* Mobile Menu Button */}
        <button
          className="md:hidden text-white"
          onClick={() => setIsMenuOpen(!isMenuOpen)}
          aria-label="Toggle menu"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            {isMenuOpen ? (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            ) : (
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            )}
          </svg>
        </button>
      </nav>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden mt-4 py-4 border-t border-primary-200">
          <div className="flex flex-col space-y-4">
            <a 
              href="/features" 
              className="text-white hover:text-primary-100 transition-colors duration-300 font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              Features
            </a>
            <a 
              href="/candidate" 
              className="text-white hover:text-primary-100 transition-colors duration-300 font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              Candidate Dashboard
            </a>
            <a 
              href="/recruiter" 
              className="text-white hover:text-primary-100 transition-colors duration-300 font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              Recruiter Dashboard
            </a>
            <a 
              href="#contact" 
              className="text-white hover:text-primary-100 transition-colors duration-300 font-medium"
              onClick={() => setIsMenuOpen(false)}
            >
              Contact
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
