'use client';

import { motion } from 'framer-motion';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';

export default function PrivacyPolicyPage() {
  const sections = [
    {
      title: 'Introduction',
      content: `This Privacy Policy explains how IntervuAI ("we," "us," or "our") collects, uses, and protects your personal information. By using our services, you agree to the collection and use of information in accordance with this policy.`
    },
    {
      title: 'Information We Collect',
      content: `We collect information that you provide directly to us, including:
• Account information (name, email, company details)
• Interview recordings and transcripts
• Assessment results and feedback
• Technical information about your device and usage
• Communication preferences`
    },
    {
      title: 'How We Use Your Information',
      content: `We use the collected information for:
• Providing and improving our services
• Personalizing your experience
• Analyzing usage patterns and trends
• Communicating with you about our services
• Ensuring compliance with legal obligations`
    },
    {
      title: 'Data Storage and Security',
      content: `We implement appropriate technical and organizational measures to protect your personal information. Data is encrypted in transit and at rest, and access is strictly controlled.`
    },
    {
      title: 'Data Sharing and Third Parties',
      content: `We may share your information with:
• Service providers who assist in our operations
• Business partners with your consent
• Law enforcement when required by law
We do not sell your personal information to third parties.`
    },
    {
      title: 'Your Rights and Choices',
      content: `You have the right to:
• Access your personal information
• Correct inaccurate data
• Request deletion of your data
• Opt-out of marketing communications
• Export your data
Contact us to exercise these rights.`
    },
    {
      title: 'Cookies and Tracking',
      content: `We use cookies and similar technologies to:
• Maintain your session
• Remember your preferences
• Analyze usage patterns
• Improve our services
You can control cookie settings in your browser.`
    },
    {
      title: 'Changes to This Policy',
      content: 'We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page and updating the effective date.'
    },
    {
      title: 'Contact Us',
      content: 'If you have any questions about this Privacy Policy, please contact us at privacy@intervuai.com'
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
              Privacy Policy
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
                  <div className="text-white/70 whitespace-pre-line">{section.content}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Contact Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mt-12 text-center"
          >
            <p className="text-white/70">
              Have questions about our privacy practices?{' '}
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
