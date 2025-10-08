'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';

export default function SitemapPage() {
  const sections = [
    {
      title: 'Main Pages',
      links: [
        { name: 'Home', href: '/' },
        { name: 'About', href: '/about' },
        { name: 'Features', href: '/#features' },
        { name: 'Pricing', href: '/pricing' },
        { name: 'Demo', href: '/demo' }
      ]
    },
    {
      title: 'Product',
      links: [
        { name: 'Features', href: '/#features' },
        { name: 'Interview Setup', href: '/interview-setup' },
        { name: 'Pricing', href: '/pricing' },
        { name: 'Demo', href: '/demo' }
      ]
    },
    {
      title: 'Company',
      links: [
        { name: 'About', href: '/about' },
        { name: 'Careers', href: '/careers' },
        { name: 'Blog', href: '/blog' }
      ]
    },
    {
      title: 'Resources',
      links: [
        { name: 'Help Center', href: '/help-center' },
        { name: 'Documentation', href: '/documentation' },
        { name: 'Community', href: '/community' }
      ]
    },
    {
      title: 'Legal',
      links: [
        { name: 'Privacy Policy', href: '/privacy-policy' },
        { name: 'Terms of Service', href: '/terms-of-service' },
        { name: 'Cookies', href: '/cookies' }
      ]
    },
    {
      title: 'Account',
      links: [
        { name: 'Login', href: '/login' },
        { name: 'Sign Up', href: '/onboarding' },
        { name: 'Candidate Dashboard', href: '/candidate' },
        { name: 'Recruiter Dashboard', href: '/recruiter' }
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-black">
      <NavBar />
      
      <main className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
              Sitemap
            </h1>
            <p className="text-xl text-white/70">
              Find everything on our website
            </p>
          </motion.div>

          {/* Sitemap Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {sections.map((section, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="glass-dark rounded-xl p-8"
              >
                <h2 className="text-2xl font-bold text-white mb-6">{section.title}</h2>
                <ul className="space-y-4">
                  {section.links.map((link, linkIndex) => (
                    <li key={linkIndex}>
                      <Link
                        href={link.href}
                        className="text-white/70 hover:text-white transition-colors duration-200 flex items-center group"
                      >
                        <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-3 group-hover:scale-125 transition-transform" />
                        {link.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}