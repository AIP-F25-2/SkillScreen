'use client';

import { motion } from 'framer-motion';
import Image from 'next/image';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';

type BlogPost = {
  category: string;
  title: string;
  excerpt: string;
  date: string;
  readTime: string;
};

export default function BlogPage() {
  const featuredPost = {
    title: 'The Future of Technical Interviews: AI-Driven Assessment',
    excerpt: 'Discover how artificial intelligence is revolutionizing the way companies evaluate technical talent, making the process more efficient and unbiased.',
    author: 'Sheethal Shivakumar',
    role: 'Project Lead',
    date: 'October 2, 2025',
    readTime: '8 min read',
    image: '/blog/featured.jpg' // Add this image to your public folder
  };

  const posts: BlogPost[] = [];

  const categories = [
    'All Posts',
    'AI & ML',
    'Best Practices',
    'Hiring',
    'Technology',
    'Company News'
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
                IntervuAI Blog
              </h1>
              <p className="text-xl text-white/70 max-w-3xl mx-auto">
                Insights, best practices, and the latest trends in technical hiring and AI-powered interviews.
              </p>
            </motion.div>
          </div>

          {/* Categories */}
          <div className="flex flex-wrap justify-center gap-3 mb-16">
            {categories.map((category, index) => (
              <motion.button
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className={`px-6 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
                  index === 0
                    ? 'bg-blue-500 text-white'
                    : 'bg-white/10 text-white/80 hover:bg-white/20'
                }`}
              >
                {category}
              </motion.button>
            ))}
          </div>

          {/* Featured Post */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="glass-dark rounded-2xl overflow-hidden mb-16"
          >
            <div className="relative h-96 w-full">
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10" />
              <div className="absolute inset-0 bg-black/20 z-10" />
              <div className="absolute bottom-0 left-0 right-0 p-8 z-20">
                <div className="flex items-center space-x-4 mb-4">
                  <div className="w-12 h-12 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center">
                    <span className="text-lg font-bold text-white">
                      {featuredPost.author.split(' ').map(n => n[0]).join('')}
                    </span>
                  </div>
                  <div>
                    <div className="text-white font-medium">{featuredPost.author}</div>
                    <div className="text-white/60 text-sm">{featuredPost.role}</div>
                  </div>
                </div>
                <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">{featuredPost.title}</h2>
                <p className="text-white/80 text-lg mb-4 max-w-3xl">{featuredPost.excerpt}</p>
                <div className="flex items-center space-x-4 text-white/60">
                  <span>{featuredPost.date}</span>
                  <span>•</span>
                  <span>{featuredPost.readTime}</span>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Recent Posts Grid */}
          <div className="grid md:grid-cols-3 gap-8">
            {posts.map((post: BlogPost, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="glass-dark rounded-xl overflow-hidden group cursor-pointer"
              >
                <div className="relative h-48">
                  <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-all duration-300" />
                </div>
                <div className="p-6">
                  <div className="text-blue-400 text-sm font-medium mb-3">{post.category}</div>
                  <h3 className="text-xl font-bold text-white mb-3 group-hover:text-blue-400 transition-colors">
                    {post.title}
                  </h3>
                  <p className="text-white/70 mb-4">{post.excerpt}</p>
                  <div className="flex items-center space-x-4 text-white/60 text-sm">
                    <span>{post.date}</span>
                    <span>•</span>
                    <span>{post.readTime}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Newsletter Signup */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-20 max-w-2xl mx-auto text-center"
          >
            <h2 className="text-2xl font-bold text-white mb-4">Stay Updated</h2>
            <p className="text-white/70 mb-8">
              Get the latest insights on technical hiring and AI-powered interviews delivered to your inbox.
            </p>
            <form className="flex gap-4">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-6 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                type="submit"
                className="px-8 py-4 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-all duration-300"
              >
                Subscribe
              </button>
            </form>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
}