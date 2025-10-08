'use client';

import { motion } from 'framer-motion';
import { useState } from 'react';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';
import { Search, ChevronRight } from 'lucide-react';

export default function DocumentationPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const sections = [
    {
      title: 'API Reference',
      description: 'Complete API documentation for integrating with IntervuAI.',
      links: [
        'Authentication',
        'Interview API',
        'Analysis API',
        'Webhooks',
        'Rate Limits'
      ]
    },
    {
      title: 'SDKs & Libraries',
      description: 'Official client libraries and SDKs for popular languages.',
      links: [
        'JavaScript/TypeScript',
        'Python',
        'Java',
        'Go',
        'Ruby'
      ]
    },
    {
      title: 'Integration Guides',
      description: 'Step-by-step guides for common integration scenarios.',
      links: [
        'ATS Integration',
        'SSO Setup',
        'Custom Templates',
        'Webhook Events'
      ]
    },
    {
      title: 'Examples',
      description: 'Sample code and example implementations.',
      links: [
        'React Components',
        'API Examples',
        'Custom UI',
        'Analytics Integration'
      ]
    }
  ];

  const guides = [
    {
      title: 'Getting Started',
      description: 'Learn the basics of integrating IntervuAI into your application.',
      time: '10 min read'
    },
    {
      title: 'Authentication',
      description: 'Secure your API requests with proper authentication.',
      time: '5 min read'
    },
    {
      title: 'Webhooks',
      description: 'Set up and handle webhook events from IntervuAI.',
      time: '8 min read'
    }
  ];

  return (
    <div className="min-h-screen bg-black">
      <NavBar />
      
      <main className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Header & Search */}
          <div className="text-center mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
                Documentation
              </h1>
              <p className="text-xl text-white/70 max-w-3xl mx-auto mb-8">
                Everything you need to integrate and customize IntervuAI for your organization.
              </p>
              <div className="max-w-2xl mx-auto relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-6 h-6 text-white/40" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search documentation..."
                  className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </motion.div>
          </div>

          {/* Quick Start Guides */}
          <div className="mb-20">
            <h2 className="text-2xl font-bold text-white mb-8">Quick Start Guides</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {guides.map((guide, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-dark rounded-xl p-6 hover:bg-white/5 transition-all duration-300 cursor-pointer group"
                >
                  <h3 className="text-xl font-bold text-white mb-3 group-hover:text-blue-400 transition-colors">
                    {guide.title}
                  </h3>
                  <p className="text-white/70 mb-4">{guide.description}</p>
                  <div className="flex items-center justify-between">
                    <span className="text-white/60 text-sm">{guide.time}</span>
                    <ChevronRight className="w-5 h-5 text-white/40 group-hover:text-blue-400 transform group-hover:translate-x-1 transition-all" />
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Documentation Sections */}
          <div className="grid md:grid-cols-2 gap-8">
            {sections.map((section, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="glass-dark rounded-xl p-8"
              >
                <h2 className="text-2xl font-bold text-white mb-4">{section.title}</h2>
                <p className="text-white/70 mb-6">{section.description}</p>
                <ul className="space-y-3">
                  {section.links.map((link, linkIndex) => (
                    <li key={linkIndex}>
                      <a
                        href="#"
                        className="flex items-center text-white/70 hover:text-white transition-colors duration-200"
                      >
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-3" />
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>

          {/* API Reference Preview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-20 glass-dark rounded-xl p-8 overflow-hidden"
          >
            <div className="flex items-start justify-between gap-8">
              <div>
                <h2 className="text-2xl font-bold text-white mb-4">API Reference</h2>
                <p className="text-white/70 mb-6">
                  Comprehensive API documentation with examples in multiple languages.
                </p>
                <button className="px-6 py-3 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-all duration-300">
                  View API Docs
                </button>
              </div>
              <div className="hidden md:block glass p-4 rounded-xl overflow-x-auto flex-shrink-0" style={{ minWidth: '400px' }}>
                <pre className="text-sm">
                  <code className="text-white/80">
{`const interview = await intervuai.interviews.create({
  candidate: {
    email: "candidate@example.com",
    name: "John Doe"
  },
  template: "frontend-engineer",
  scheduledFor: "2024-03-20T10:00:00Z"
});`}
                  </code>
                </pre>
              </div>
            </div>
          </motion.div>

          {/* Support Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-20 max-w-3xl mx-auto text-center"
          >
            <h2 className="text-2xl font-bold text-white mb-4">Need Help?</h2>
            <p className="text-white/70 mb-8">
              Can't find what you're looking for? Our developer support team is here to help.
            </p>
            <div className="flex justify-center gap-4">
              <button className="px-8 py-4 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-all duration-300">
                Contact Support
              </button>
              <button className="px-8 py-4 bg-white/10 text-white rounded-xl font-medium hover:bg-white/20 transition-all duration-300">
                Join Discord
              </button>
            </div>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
