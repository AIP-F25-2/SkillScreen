'use client';

import { motion } from 'framer-motion';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';
import { MessageSquare, Users, Globe, Award } from 'lucide-react';

export default function CommunityPage() {
  const discussions = [
    {
      title: 'Best practices for AI-powered technical interviews',
      author: 'Sarah Chen',
      replies: 24,
      views: 1.200,
      category: 'Best Practices',
      time: '2 hours ago'
    },
    {
      title: 'How to customize interview templates effectively',
      author: 'Michael Rodriguez',
      replies: 18,
      views: 856,
      category: 'Tutorials',
      time: '5 hours ago'
    },
    {
      title: 'Integrating IntervuAI with existing ATS systems',
      author: 'Geeneth Kulatunge',
      replies: 31,
      views: 1.500,
      category: 'Integration',
      time: '1 day ago'
    }
  ];

  const events = [
    {
      title: 'AI in Technical Hiring Webinar',
      date: 'March 25, 2024',
      time: '11:00 AM PST',
      type: 'Online',
      attendees: 234
    },
    {
      title: 'IntervuAI User Conference 2024',
      date: 'April 15-16, 2024',
      time: 'All Day',
      type: 'Hybrid',
      attendees: 500
    },
    {
      title: 'Community Meetup - San Francisco',
      date: 'March 30, 2024',
      time: '6:00 PM PST',
      type: 'In-Person',
      attendees: 75
    }
  ];

  const features = [
    {
      icon: MessageSquare,
      title: 'Discussion Forums',
      description: 'Engage with other users, share experiences, and get help from the community.'
    },
    {
      icon: Users,
      title: 'User Groups',
      description: 'Join local and virtual groups focused on specific topics and industries.'
    },
    {
      icon: Globe,
      title: 'Global Events',
      description: 'Participate in webinars, conferences, and local meetups worldwide.'
    },
    {
      icon: Award,
      title: 'Recognition Program',
      description: 'Earn badges and rewards for your contributions to the community.'
    }
  ];

  return (
    <div className="min-h-screen bg-black">
      <NavBar />
      
      <main className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
                Join Our Community
              </h1>
              <p className="text-xl text-white/70 max-w-3xl mx-auto">
                Connect with thousands of hiring professionals, share knowledge, and stay up to date with the latest in technical hiring.
              </p>
            </motion.div>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="glass-dark rounded-xl p-6 text-center"
              >
                <div className="w-12 h-12 rounded-full bg-blue-500/20 flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-white/70">{feature.description}</p>
              </motion.div>
            ))}
          </div>

          {/* Latest Discussions */}
          <div className="mb-20">
            <h2 className="text-2xl font-bold text-white mb-8">Latest Discussions</h2>
            <div className="space-y-4">
              {discussions.map((discussion, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-dark rounded-xl p-6 hover:bg-white/5 transition-all duration-300 cursor-pointer"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold text-white mb-2">{discussion.title}</h3>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-white/60">by {discussion.author}</span>
                        <span className="text-white/40">•</span>
                        <span className="text-white/60">{discussion.time}</span>
                        <span className="px-2 py-1 bg-blue-500/20 rounded-full text-blue-400 text-xs">
                          {discussion.category}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-6 text-sm text-white/60">
                      <div>{discussion.replies} replies</div>
                      <div>{discussion.views} views</div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Upcoming Events */}
          <div className="mb-20">
            <h2 className="text-2xl font-bold text-white mb-8">Upcoming Events</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {events.map((event, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-dark rounded-xl p-6"
                >
                  <div className="flex items-center justify-between mb-4">
                    <span className={`px-3 py-1 rounded-full text-sm ${
                      event.type === 'Online'
                        ? 'bg-green-500/20 text-green-400'
                        : event.type === 'Hybrid'
                        ? 'bg-purple-500/20 text-purple-400'
                        : 'bg-blue-500/20 text-blue-400'
                    }`}>
                      {event.type}
                    </span>
                    <div className="flex items-center text-white/60">
                      <Users className="w-4 h-4 mr-2" />
                      <span>{event.attendees}</span>
                    </div>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-3">{event.title}</h3>
                  <div className="text-white/70">
                    <p>{event.date}</p>
                    <p>{event.time}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Join CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="max-w-3xl mx-auto text-center"
          >
            <h2 className="text-2xl font-bold text-white mb-4">Ready to Join?</h2>
            <p className="text-white/70 mb-8">
              Become part of our growing community and help shape the future of technical hiring.
            </p>
            <div className="flex justify-center gap-4">
              <button className="px-8 py-4 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-all duration-300">
                Join Community
              </button>
              <button className="px-8 py-4 bg-white/10 text-white rounded-xl font-medium hover:bg-white/20 transition-all duration-300">
                Learn More
              </button>
            </div>
          </motion.div>
      </div>
      </main>

      <Footer />
    </div>
  );
}