'use client';

import { motion } from 'framer-motion';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';

type Position = {
  title: string;
  department: string;
  location: string;
  type: string;
  description: string;
  requirements: string[];
};

export default function CareersPage() {
  const openPositions: Position[] = [];

  const values = [
    {
      title: 'Innovation First',
      description: 'We push boundaries and embrace cutting-edge technology.'
    },
    {
      title: 'Remote-Native',
      description: 'Work from anywhere, focus on impact over location.'
    },
    {
      title: 'Continuous Learning',
      description: 'Regular opportunities for growth and skill development.'
    },
    {
      title: 'Work-Life Balance',
      description: 'Flexible hours and unlimited PTO policy.'
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
                Join Our Mission
              </h1>
              <p className="text-xl text-white/70 max-w-3xl mx-auto">
                Help us transform the future of technical hiring with AI. We're looking for passionate individuals to join our remote-first team.
              </p>
            </motion.div>
          </div>

          {/* Values Section */}
          <div className="mb-20">
            <h2 className="text-3xl font-bold text-white text-center mb-12">Our Values</h2>
            <div className="grid md:grid-cols-4 gap-8">
              {values.map((value, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-dark rounded-xl p-6 text-center"
                >
                  <h3 className="text-xl font-semibold text-white mb-3">{value.title}</h3>
                  <p className="text-white/70">{value.description}</p>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Open Positions */}
          <div className="mb-20">
            <h2 className="text-3xl font-bold text-white text-center mb-12">Open Positions</h2>
            <div className="space-y-6">
              {openPositions.map((position, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-dark rounded-xl p-8 border border-white/10"
                >
                  <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
                    <div>
                      <h3 className="text-2xl font-bold text-white mb-2">{position.title}</h3>
                      <div className="flex flex-wrap gap-3">
                        <span className="px-3 py-1 bg-white/10 rounded-full text-sm text-white/80">{position.department}</span>
                        <span className="px-3 py-1 bg-white/10 rounded-full text-sm text-white/80">{position.location}</span>
                        <span className="px-3 py-1 bg-white/10 rounded-full text-sm text-white/80">{position.type}</span>
                      </div>
                    </div>
                    <button className="px-6 py-3 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-all duration-300">
                      Apply Now
                    </button>
                  </div>
                  <p className="text-white/70 mb-6">{position.description}</p>
                  <h4 className="text-white font-semibold mb-3">Requirements:</h4>
                  <ul className="space-y-2">
                    {position.requirements.map((req: string, reqIndex: number) => (
                      <li key={reqIndex} className="flex items-center text-white/70">
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-3" />
                        {req}
                      </li>
                    ))}
                  </ul>
                </motion.div>
              ))}
            </div>
          </div>

          
        </div>
      </main>

      <Footer />
    </div>
  );
}