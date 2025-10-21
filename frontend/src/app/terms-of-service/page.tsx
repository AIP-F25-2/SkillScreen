'use client';

import { motion } from 'framer-motion';
import NavBar from '@/components/NavBar';
import Footer from '@/components/Footer';

export default function TermsOfServicePage() {
  const sections = [
    {
      title: 'Agreement to Terms',
      content: `By accessing or using IntervuAI's services, you agree to be bound by these Terms of Service ("Terms"). If you disagree with any part of the terms, you may not access the service.`
    },
    {
      title: 'Description of Service',
      content: `IntervuAI provides an AI-powered technical interview platform that includes:
• Video interviewing capabilities
• Technical assessment tools
• AI-driven analysis and feedback
• Interview recording and playback
• Integration with third-party services`
    },
    {
      title: 'User Accounts',
      content: `To access certain features of the service, you must register for an account. You agree to:
• Provide accurate account information
• Maintain the security of your account
• Accept responsibility for all activities under your account
• Notify us immediately of any security breaches`
    },
    {
      title: 'Acceptable Use',
      content: `You agree not to:
• Use the service for any illegal purpose
• Violate any laws in your jurisdiction
• Infringe on others' intellectual property rights
• Share inappropriate or offensive content
• Attempt to breach our security measures
• Interfere with the proper working of the service`
    },
    {
      title: 'Intellectual Property',
      content: `The service and its original content, features, and functionality are owned by IntervuAI and are protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.`
    },
    {
      title: 'Payment Terms',
      content: `For paid services:
• Payments are processed securely through our payment providers
• Subscriptions auto-renew unless cancelled
• Refunds are provided according to our refund policy
• Prices may change with notice
• You are responsible for applicable taxes`
    },
    {
      title: 'Data Privacy',
      content: `We collect and process personal data as described in our Privacy Policy. By using our service, you consent to such processing and warrant that all data provided by you is accurate.`
    },
    {
      title: 'Termination',
      content: `We may terminate or suspend your account and access to the service immediately, without prior notice or liability, for any reason, including breach of these Terms.`
    },
    {
      title: 'Limitation of Liability',
      content: `In no event shall IntervuAI, nor its directors, employees, partners, agents, suppliers, or affiliates, be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use or inability to use the service.`
    },
    {
      title: 'Changes to Terms',
      content: 'We reserve the right to modify or replace these Terms at any time. We will provide notice of any changes by posting the new Terms on this site.'
    },
    {
      title: 'Contact Information',
      content: 'Questions about the Terms should be sent to us at legal@intervuai.com'
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
              Terms of Service
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
              Have questions about our terms?{' '}
              <a href="mailto:legal@intervuai.com" className="text-blue-400 hover:text-blue-300 transition-colors">
                Contact our Legal Team
              </a>
            </p>
          </motion.div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
