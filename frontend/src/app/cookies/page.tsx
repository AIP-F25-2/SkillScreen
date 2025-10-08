'use client';

import { motion } from 'framer-motion';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';

export default function CookiesPage() {
  const sections = [
    {
      title: 'What Are Cookies',
      content: `Cookies are small text files that are placed on your computer or mobile device when you visit our website. They are widely used to make websites work more efficiently and provide useful information to website owners.`
    },
    {
      title: 'How We Use Cookies',
      content: `We use cookies for the following purposes:
• Essential cookies: Required for the website to function properly
• Analytics cookies: Help us understand how visitors use our site
• Preference cookies: Remember your settings and preferences
• Marketing cookies: Track your activity across websites for marketing purposes`
    },
    {
      title: 'Types of Cookies We Use',
      subsections: [
        {
          title: 'Essential Cookies',
          items: [
            'Session cookies',
            'Authentication cookies',
            'Security cookies'
          ]
        },
        {
          title: 'Analytics Cookies',
          items: [
            'Google Analytics',
            'Usage patterns',
            'Performance monitoring'
          ]
        },
        {
          title: 'Preference Cookies',
          items: [
            'Language settings',
            'Theme preferences',
            'User interface customization'
          ]
        },
        {
          title: 'Marketing Cookies',
          items: [
            'Advertising tracking',
            'Social media integration',
            'Campaign effectiveness'
          ]
        }
      ]
    },
    {
      title: 'Managing Cookies',
      content: `You can control and manage cookies in various ways:
• Browser settings: You can modify your browser settings to accept or reject cookies
• Cookie consent: You can change your cookie preferences on our website
• Third-party tools: You can use various tools to manage cookies across websites

Please note that blocking certain cookies may impact your experience on our website.`
    },
    {
      title: 'Third-Party Cookies',
      content: `We use some third-party services that may set their own cookies:
• Analytics providers
• Social media platforms
• Payment processors
• Marketing services

These third parties have their own privacy and cookie policies.`
    },
    {
      title: 'Updates to Cookie Policy',
      content: 'We may update this Cookie Policy from time to time. Any changes will be posted on this page with an updated revision date.'
    },
    {
      title: 'Contact Us',
      content: 'If you have any questions about our use of cookies, please contact us at privacy@intervuai.com'
    }
  ];

  return (
    <div className="min-h-screen bg-black">
      <NavBar />
      
      <main className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
              Cookie Policy
            </h1>
            <p className="text-xl text-white/70">
              Last updated: March 1, 2024
            </p>
          </motion.div>

          {/* Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="glass-dark rounded-2xl p-8 md:p-12"
          >
            <div className="prose prose-invert max-w-none">
              {sections.map((section, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  className="mb-12 last:mb-0"
                >
                  <h2 className="text-2xl font-bold text-white mb-4">{section.title}</h2>
                  {section.content && (
                    <div className="text-white/70 whitespace-pre-line mb-6">{section.content}</div>
                  )}
                  {section.subsections && (
                    <div className="grid md:grid-cols-2 gap-6">
                      {section.subsections.map((subsection, subIndex) => (
                        <div
                          key={subIndex}
                          className="glass p-6 rounded-xl"
                        >
                          <h3 className="text-lg font-semibold text-white mb-4">{subsection.title}</h3>
                          <ul className="space-y-2">
                            {subsection.items.map((item, itemIndex) => (
                              <li key={itemIndex} className="flex items-center text-white/70">
                                <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-3" />
                                {item}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Cookie Preferences */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-12 glass-dark rounded-xl p-8 text-center"
          >
            <h2 className="text-2xl font-bold text-white mb-4">Cookie Preferences</h2>
            <p className="text-white/70 mb-6">
              You can customize your cookie preferences at any time.
            </p>
            <button className="px-8 py-4 bg-blue-500 text-white rounded-xl font-medium hover:bg-blue-600 transition-all duration-300">
              Manage Preferences
            </button>
          </motion.div>

          {/* Contact Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-12 text-center"
          >
            <p className="text-white/70">
              Questions about our cookie practices?{' '}
              <a href="mailto:privacy@intervuai.com" className="text-blue-400 hover:text-blue-300 transition-colors">
                Contact our Privacy Team
              </a>
            </p>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
}