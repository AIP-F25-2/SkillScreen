'use client';

import { motion } from 'framer-motion';
import { useState } from 'react';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';
import { Search } from 'lucide-react';

export default function HelpCenterPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const categories = [
    {
      title: 'Getting Started',
      icon: '🚀',
      articles: [
        'Quick Start Guide',
        'Setting Up Your Account',
        'Creating Your First Interview',
        'Understanding the Dashboard'
      ]
    },
    {
      title: 'Interview Setup',
      icon: '⚙️',
      articles: [
        'Configuring Interview Settings',
        'Custom Templates',
        'AI Analysis Settings',
        'Technical Requirements'
      ]
    },
    {
      title: 'Conducting Interviews',
      icon: '🎯',
      articles: [
        'Live Interview Best Practices',
        'Using the Code Editor',
        'Real-time Feedback',
        'Recording Sessions'
      ]
    },
    {
      title: 'Analysis & Reports',
      icon: '📊',
      articles: [
        'Understanding AI Analysis',
        'Generating Reports',
        'Performance Metrics',
        'Exporting Data'
      ]
    },
    {
      title: 'Account Management',
      icon: '👤',
      articles: [
        'User Roles & Permissions',
        'Team Management',
        'Billing & Subscriptions',
        'Security Settings'
      ]
    },
    {
      title: 'Troubleshooting',
      icon: '🔧',
      articles: [
        'Common Issues',
        'Connection Problems',
        'Audio/Video Troubleshooting',
        'Error Messages'
      ]
    }
  ];

  const popularArticles = [
    'How to Set Up Your First Technical Interview',
    'Understanding AI Analysis Metrics',
    'Best Practices for Remote Interviews',
    'Customizing Interview Templates'
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
                How can we help?
              </h1>
              <div className="max-w-2xl mx-auto relative">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-6 h-6 text-white/40" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for help articles..."
                  className="w-full pl-12 pr-4 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </motion.div>
          </div>

          {/* Popular Articles */}
          <div className="mb-20">
            <h2 className="text-2xl font-bold text-white mb-8">Popular Articles</h2>
            <div className="grid md:grid-cols-2 gap-6">
              {popularArticles.map((article, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-dark rounded-xl p-6 hover:bg-white/5 transition-all duration-300 cursor-pointer"
                >
                  <h3 className="text-lg font-medium text-white mb-2">{article}</h3>
                  <p className="text-white/60">Last updated 2 days ago</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Categories */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {categories.map((category, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="glass-dark rounded-xl p-6"
              >
                <div className="text-4xl mb-4">{category.icon}</div>
                <h2 className="text-xl font-bold text-white mb-4">{category.title}</h2>
                <ul className="space-y-3">
                  {category.articles.map((article, articleIndex) => (
                    <li key={articleIndex}>
                      <a
                        href="#"
                        className="text-white/70 hover:text-white transition-colors duration-200 flex items-center"
                      >
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-3" />
                        {article}
                      </a>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>

          {/* Contact Support */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-20 max-w-3xl mx-auto text-center"
          >
            <h2 className="text-2xl font-bold text-white mb-4">Still Need Help?</h2>
            <p className="text-white/70 mb-8">
              Our support team is available 24/7 to assist you with any questions or issues.
            </p>
            <div className="flex justify-center gap-4">
              <button className="px-8 py-4 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-all duration-300">
                Contact Support
              </button>
              <button className="px-8 py-4 bg-white/10 text-white rounded-xl font-medium hover:bg-white/20 transition-all duration-300">
                Schedule a Call
              </button>
            </div>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
}