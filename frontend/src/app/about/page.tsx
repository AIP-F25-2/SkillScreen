'use client';

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';
import { Video, Brain, BarChart3, Shield, Zap, Users, Target, Sparkles } from 'lucide-react';

export default function AboutPage() {
  const router = useRouter();

  const values = [
    {
      icon: Target,
      title: 'Mission-Driven',
      description: 'Revolutionizing the hiring process with AI-powered interviews that are fair, efficient, and insightful.'
    },
    {
      icon: Brain,
      title: 'AI-Powered',
      description: 'Leveraging cutting-edge artificial intelligence to analyze candidates beyond traditional resumes.'
    },
    {
      icon: Shield,
      title: 'Fair & Unbiased',
      description: 'Eliminating unconscious bias through objective, data-driven candidate evaluation.'
    },
    {
      icon: Zap,
      title: 'Fast & Efficient',
      description: 'Streamline your hiring process and make better decisions in a fraction of the time.'
    }
  ];

  const features = [
    {
      icon: Video,
      title: 'Video Interviews',
      description: 'AI-powered video analysis detects communication skills, confidence, and engagement levels.'
    },
    {
      icon: Brain,
      title: 'Smart Coding Challenges',
      description: 'Real-time code evaluation with intelligent feedback and performance metrics.'
    },
    {
      icon: BarChart3,
      title: 'Advanced Analytics',
      description: 'Comprehensive dashboards showing candidate performance, trends, and insights.'
    },
    {
      icon: Users,
      title: 'Collaborative Tools',
      description: 'Team-based evaluation features for collaborative hiring decisions.'
    }
  ];

  const stats = [
    { value: '10K+', label: 'Interviews Conducted' },
    { value: '95%', label: 'Customer Satisfaction' },
    { value: '60%', label: 'Time Saved' },
    { value: '500+', label: 'Companies Trust Us' }
  ];

  return (
    <div className="min-h-screen bg-black">
      <NavBar />

      <div className="relative">
        {/* Hero Section */}
        <section className="pt-32 pb-20 px-6">
          <div className="max-w-6xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
                Transforming Hiring with
                <span className="block mt-2 text-white">
                  Artificial Intelligence
                </span>
              </h1>
              <p className="text-xl md:text-2xl text-white/70 max-w-3xl mx-auto leading-relaxed">
                IntervuAI is revolutionizing the recruitment process by combining AI-powered video interviews, 
                intelligent coding assessments, and advanced analytics to help companies find the perfect candidates.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-16 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="grid grid-cols-2 md:grid-cols-4 gap-6"
            >
              {stats.map((stat, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-dark p-6 rounded-2xl text-center"
                >
                  <div className="text-4xl md:text-5xl font-bold text-white mb-2">{stat.value}</div>
                  <div className="text-white/60">{stat.label}</div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Mission Section */}
        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="glass-dark p-12 rounded-3xl"
            >
              <div className="flex items-center justify-center mb-6">
                <Sparkles className="w-12 h-12 text-white" />
              </div>
              <h2 className="text-4xl font-bold text-white text-center mb-6">Our Mission</h2>
              <p className="text-xl text-white/70 text-center max-w-4xl mx-auto leading-relaxed">
                We believe that hiring should be a seamless, unbiased, and data-driven process. 
                IntervuAI empowers recruiters with intelligent tools to assess candidates fairly, 
                saving time while ensuring the best talent rises to the top. Our platform combines 
                the human touch of traditional interviews with the precision and scalability of AI.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Values Section */}
        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">Our Core Values</h2>
              <p className="text-xl text-white/60">What drives us every day</p>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8">
              {values.map((value, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-dark p-8 rounded-2xl hover:bg-white/10 transition-all duration-300 group"
                >
                  <div className="w-14 h-14 rounded-xl bg-primary-200 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                    <value.icon className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">{value.title}</h3>
                  <p className="text-white/70 leading-relaxed">{value.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">Platform Features</h2>
              <p className="text-xl text-white/60">Everything you need for modern hiring</p>
            </motion.div>

            <div className="grid md:grid-cols-2 gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="glass-dark p-8 rounded-2xl hover:bg-white/10 transition-all duration-300"
                >
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-white/10 flex items-center justify-center flex-shrink-0">
                      <feature.icon className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white mb-2">{feature.title}</h3>
                      <p className="text-white/70">{feature.description}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Technology Stack */}
        <section className="py-20 px-6">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="glass-dark p-12 rounded-3xl text-center"
            >
              <h2 className="text-4xl font-bold text-white mb-6">Built with Cutting-Edge Technology</h2>
              <p className="text-xl text-white/70 mb-12 max-w-3xl mx-auto">
                Our platform leverages the latest in AI, machine learning, and cloud infrastructure 
                to deliver a seamless, reliable, and scalable interviewing experience.
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {['AI/ML', 'WebRTC', 'Cloud Native', 'Real-time Analytics'].map((tech, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.8 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: index * 0.1 }}
                    className="glass p-6 rounded-xl"
                  >
                    <div className="text-lg font-semibold text-white">{tech}</div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 px-6">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="glass-dark p-12 rounded-3xl text-center"
            >
              <h2 className="text-4xl font-bold text-white mb-6">Ready to Transform Your Hiring?</h2>
              <p className="text-xl text-white/70 mb-8">
                Join hundreds of companies already using IntervuAI to find their next great hire.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <button
                  onClick={() => router.push('/onboarding')}
                  className="px-8 py-4 bg-white text-primary-300 rounded-xl font-semibold hover:bg-primary-100 hover:text-white transition-all duration-300 transform hover:scale-105"
                >
                  Get Started Free
                </button>
                <button
                  onClick={() => router.push('/')}
                  className="px-8 py-4 bg-white/10 border border-white/20 text-white rounded-xl font-semibold hover:bg-white/20 transition-all duration-300"
                >
                  Learn More
                </button>
              </div>
            </motion.div>
          </div>
        </section>

      </div>

      <Footer />
    </div>
  );
}

