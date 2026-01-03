'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { RatingsDisplay } from './ratings';

// Icons as inline SVGs for cleaner design
const ShieldCheckIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
  </svg>
);

const LockClosedIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
  </svg>
);

const DocumentTextIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
  </svg>
);

const SparklesIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
  </svg>
);

const CalendarIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
  </svg>
);

const CurrencyDollarIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const ExclamationTriangleIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
  </svg>
);

const ChatBubbleIcon = () => (
  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
  </svg>
);

const CloudArrowUpIcon = () => (
  <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z" />
  </svg>
);

const CpuChipIcon = () => (
  <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25zm.75-12h9v9h-9v-9z" />
  </svg>
);

const DocumentCheckIcon = () => (
  <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25h.375a9 9 0 019 9v.375M10.125 2.25A3.375 3.375 0 0113.5 5.625v1.5c0 .621.504 1.125 1.125 1.125h1.5a3.375 3.375 0 013.375 3.375M9 15l2.25 2.25L15 12" />
  </svg>
);

const UserIcon = () => (
  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
  </svg>
);

const BuildingOfficeIcon = () => (
  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
  </svg>
);

const UserGroupIcon = () => (
  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
  </svg>
);

const NewspaperIcon = () => (
  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z" />
  </svg>
);

const BellAlertIcon = () => (  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>    <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0M3.124 7.5A8.969 8.969 0 015.292 3m13.416 0a8.969 8.969 0 012.168 4.5" />  </svg>);const ScaleIcon = () => (  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>    <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v17.25m0 0c-1.472 0-2.882.265-4.185.75M12 20.25c1.472 0 2.882.265 4.185.75M18.75 4.97A48.416 48.416 0 0012 4.5c-2.291 0-4.545.16-6.75.47m13.5 0c1.01.143 2.01.317 3 .52m-3-.52l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.988 5.988 0 01-2.031.352 5.988 5.988 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L18.75 4.971zm-16.5.52c.99-.203 1.99-.377 3-.52m0 0l2.62 10.726c.122.499-.106 1.028-.589 1.202a5.989 5.989 0 01-2.031.352 5.989 5.989 0 01-2.031-.352c-.483-.174-.711-.703-.59-1.202L5.25 4.971z" />  </svg>);
const ChevronDownIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
  </svg>
);

// Animation variants
const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

// FAQ Item Component
const FAQItem: React.FC<{ question: string; answer: string }> = ({ question, answer }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border-b border-gray-200">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full py-5 flex justify-between items-center text-left hover:text-navy-600 transition-colors"
      >
        <span className="font-medium text-gray-900">{question}</span>
        <span className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`}>
          <ChevronDownIcon />
        </span>
      </button>
      <div className={`overflow-hidden transition-all duration-300 ${isOpen ? 'max-h-96 pb-5' : 'max-h-0'}`}>
        <p className="text-gray-600 leading-relaxed">{answer}</p>
      </div>
    </div>
  );
};

export const LandingPage: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly');

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const features = [
    {
      icon: <DocumentTextIcon />,
      title: 'Plain English Summaries',
      description: 'Complex legal documents translated into clear, understandable language anyone can follow.'
    },
    {
      icon: <CalendarIcon />,
      title: 'Key Dates & Deadlines',
      description: 'Never miss a critical date. We extract and highlight every important deadline from your documents.'
    },
    {
      icon: <CurrencyDollarIcon />,
      title: 'Financial Amounts Extracted',
      description: 'All monetary figures, fees, and financial obligations clearly identified and summarized.'
    },
    {
      icon: <ExclamationTriangleIcon />,
      title: 'Risk Indicators',
      description: 'Potential concerns and red flags highlighted so you know what deserves attention.'
    },
    {
      icon: <ChatBubbleIcon />,
      title: 'Questions for Your Attorney',
      description: 'AI-generated questions to ask your lawyer, helping you make the most of your legal consultation.'
    },
    {
      icon: <SparklesIcon />,
      title: 'Instant Analysis',
      description: 'Get comprehensive insights in seconds, not hours. Upload and understand immediately.'
    },
    {
      icon: <BellAlertIcon />,
      title: 'Case Monitoring & Alerts',
      description: 'Follow your case and get automatic notifications when new documents are filed. Never miss a filing again.'
    },
    {
      icon: <ScaleIcon />,
      title: 'Defense Strategy Builder',
      description: 'Build a comprehensive defense overview to bring to your attorney, making consultations more productive and informed.'
    }
  ];

  const audiences = [
    {
      icon: <UserIcon />,
      title: 'Individuals',
      description: 'Understanding your own legal matters without expensive consultations for every question.'
    },
    {
      icon: <BuildingOfficeIcon />,
      title: 'Small Businesses',
      description: 'Review contracts, litigation documents, and compliance materials efficiently.'
    },
    {
      icon: <UserGroupIcon />,
      title: 'HR Professionals',
      description: 'Navigate employment law documents, settlements, and workplace legal matters.'
    },
    {
      icon: <NewspaperIcon />,
      title: 'Journalists & Researchers',
      description: 'Quickly analyze court filings and legal documents for investigative reporting.'
    }
  ];

  const faqs = [
    {
      question: 'Is this legal advice?',
      answer: 'No. This platform provides legal information and document analysis for educational purposes only. We help you understand legal documents, but we do not provide legal advice. For legal advice, please consult with a licensed attorney in your jurisdiction.'
    },
    {
      question: 'How secure is my data?',
      answer: 'We use bank-level 256-bit AES encryption for all data in transit and at rest. Your documents are processed securely and never shared with third parties. We are committed to protecting your privacy and maintaining the highest security standards.'
    },
    {
      question: 'What types of documents can I analyze?',
      answer: 'You can analyze court filings, contracts, legal briefs, motions, orders, judgments, settlement agreements, and most other legal documents. We support PDF, DOCX, and plain text formats.'
    },
    {
      question: 'How accurate is the AI analysis?',
      answer: 'Our AI is trained on extensive legal document datasets and provides highly accurate summaries and extractions. However, we always recommend having important legal matters reviewed by a qualified attorney. The AI is a tool to help you understand, not replace professional legal counsel.'
    },
    {
      question: 'Can I use this for active litigation?',
      answer: 'You can use our platform to better understand documents in your case. However, for strategic legal decisions in active litigation, you should work with a licensed attorney who can provide personalized legal advice based on your specific situation.'
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <header
        className="bg-white shadow-sm"
      >
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-navy-600 rounded-lg flex items-center justify-center">
                <ShieldCheckIcon />
              </div>
              <span className="font-semibold text-xl text-navy-800">LegalAI</span>
            </div>
            <div className="hidden md:flex items-center space-x-8">
              <a href="#features" className="text-gray-600 hover:text-navy-600 transition-colors">Features</a>
              <a href="#how-it-works" className="text-gray-600 hover:text-navy-600 transition-colors">How It Works</a>
              <a href="#pricing" className="text-gray-600 hover:text-navy-600 transition-colors">Pricing</a>
              <a href="#faq" className="text-gray-600 hover:text-navy-600 transition-colors">FAQ</a>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                href="/auth/login"
                className="text-gray-600 hover:text-navy-600 transition-colors font-medium"
              >
                Sign In
              </Link>
              <Link
                href="/pricing"
                className="bg-navy-600 text-white px-5 py-2 rounded-lg hover:bg-navy-700 transition-colors font-medium"
              >
                Get Started
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="pt-20 pb-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto">
          <motion.div
            className="text-center max-w-4xl mx-auto"
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
          >
            <motion.h1
              className="text-4xl sm:text-5xl lg:text-6xl font-bold text-navy-800 leading-tight"
              variants={fadeInUp}
            >
              Legal Intelligence for Everyone,{' '}
              <span className="text-teal-600">Not Just Lawyers</span>
            </motion.h1>
            <motion.p
              className="mt-6 text-xl text-gray-600 leading-relaxed"
              variants={fadeInUp}
            >
              AI-powered court case analysis that explains legal documents in plain English.
              Understand your legal matters without the confusion.
            </motion.p>
            <motion.div
              className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
              variants={fadeInUp}
            >
              <Link
                href="/pricing"
                className="w-full sm:w-auto bg-teal-600 text-white px-8 py-4 rounded-lg hover:bg-teal-700 transition-all font-semibold text-lg shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                Analyze Your First Document Free
              </Link>
              <a
                href="#how-it-works"
                className="w-full sm:w-auto text-navy-600 px-8 py-4 rounded-lg border-2 border-navy-200 hover:border-navy-300 transition-colors font-semibold text-lg"
              >
                See How It Works
              </a>
            </motion.div>

            {/* Trust Badges */}
            <motion.div
              className="mt-12 flex flex-wrap items-center justify-center gap-6 text-sm text-gray-500"
              variants={fadeInUp}
            >
              <div className="flex items-center gap-2">
                <LockClosedIcon />
                <span>Bank-Level Encryption</span>
              </div>
              <div className="flex items-center gap-2">
                <ShieldCheckIcon />
                <span>FCRA Compliant</span>
              </div>
              <div className="flex items-center gap-2">
                <DocumentTextIcon />
                <span>Educational Use Only</span>
              </div>
            </motion.div>
          </motion.div>

          {/* Stats */}
          <motion.div
            className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            {[
              { value: '50,000+', label: 'Documents Analyzed' },
              { value: '10,000+', label: 'Users Served' },
              { value: '99.9%', label: 'Uptime' },
              { value: '< 30s', label: 'Average Analysis Time' }
            ].map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-bold text-navy-800">{stat.value}</div>
                <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-navy-800">How It Works</h2>
            <p className="mt-4 text-xl text-gray-600">Three simple steps to understand any legal document</p>
          </div>

          <div className="grid md:grid-cols-3 gap-12">
            {[
              {
                step: '1',
                icon: <CloudArrowUpIcon />,
                title: 'Upload Your Document',
                description: 'Simply drag and drop your legal document or paste the text. We support PDF, DOCX, and plain text.'
              },
              {
                step: '2',
                icon: <CpuChipIcon />,
                title: 'AI Analyzes',
                description: 'Our advanced AI reads and processes your document, identifying key information, dates, and potential concerns.'
              },
              {
                step: '3',
                icon: <DocumentCheckIcon />,
                title: 'Get Plain English Summary',
                description: 'Receive a clear, easy-to-understand breakdown with all the important details highlighted.'
              }
            ].map((item, index) => (
              <motion.div
                key={index}
                className="relative text-center"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="inline-flex items-center justify-center w-20 h-20 bg-navy-50 text-navy-600 rounded-2xl mb-6">
                  {item.icon}
                </div>
                <div className="absolute -top-2 -right-2 md:right-auto md:left-1/2 md:ml-8 w-8 h-8 bg-teal-500 text-white rounded-full flex items-center justify-center font-bold text-sm">
                  {item.step}
                </div>
                <h3 className="text-xl font-semibold text-navy-800 mb-3">{item.title}</h3>
                <p className="text-gray-600">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-navy-800">What You Get</h2>
            <p className="mt-4 text-xl text-gray-600">Comprehensive analysis that helps you truly understand</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={index}
                className="bg-white p-8 rounded-xl shadow-sm hover:shadow-md transition-shadow border border-gray-100"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
              >
                <div className="w-12 h-12 bg-navy-50 text-navy-600 rounded-lg flex items-center justify-center mb-5">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-navy-800 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Who It's For */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-navy-800">Who It's For</h2>
            <p className="mt-4 text-xl text-gray-600">Designed for anyone who needs to understand legal documents</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {audiences.map((audience, index) => (
              <motion.div
                key={index}
                className="text-center p-6"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="inline-flex items-center justify-center w-16 h-16 bg-teal-50 text-teal-600 rounded-full mb-5">
                  {audience.icon}
                </div>
                <h3 className="text-lg font-semibold text-navy-800 mb-2">{audience.title}</h3>
                <p className="text-gray-600 text-sm">{audience.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Preview */}
      <section id="pricing" className="py-20 px-4 sm:px-6 lg:px-8 bg-navy-800">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Simple, Transparent Pricing</h2>
          <p className="text-xl text-navy-200 mb-8">Start free, upgrade when you need more</p>

          {/* Billing Period Toggle */}
          <div className="flex items-center justify-center gap-3 mb-10">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                billingPeriod === 'monthly'
                  ? 'bg-teal-500 text-white'
                  : 'bg-navy-600 text-navy-300 hover:text-white'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod('annual')}
              className={`px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${
                billingPeriod === 'annual'
                  ? 'bg-teal-500 text-white'
                  : 'bg-navy-600 text-navy-300 hover:text-white'
              }`}
            >
              Annual
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                billingPeriod === 'annual' ? 'bg-white text-teal-600' : 'bg-teal-500 text-white'
              }`}>
                Save 17%
              </span>
            </button>
          </div>

          <div className="grid md:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {[
              {
                name: 'Free',
                planId: 'free',
                priceMonthly: '$0',
                priceAnnual: '$0',
                period: 'forever',
                description: 'Get started with basic access',
                features: ['Case search', '1 case monitoring', 'Document preview'],
                cta: 'Get Started Free',
                highlighted: false
              },
              {
                name: 'Basic',
                planId: 'basic',
                priceMonthly: '$9.99',
                priceAnnual: '$8.33',
                annualTotal: '$99.99/year',
                period: '/month',
                description: 'Essential features for individuals',
                features: ['20 document credits', '5 case monitoring', 'Email notifications', 'Basic AI analysis'],
                cta: 'Start 14-Day Trial',
                highlighted: false
              },
              {
                name: 'Individual Pro',
                planId: 'individual_pro',
                priceMonthly: '$29.99',
                priceAnnual: '$25',
                annualTotal: '$299.99/year',
                period: '/month',
                description: 'Advanced features for power users',
                features: ['75 document credits', '25 case monitoring', 'Advanced AI analysis', 'Export reports', 'API access'],
                cta: 'Start 14-Day Trial',
                highlighted: true
              },
              {
                name: 'Professional',
                planId: 'professional',
                priceMonthly: '$99',
                priceAnnual: '$83.25',
                annualTotal: '$999/year',
                period: '/month',
                description: 'Complete toolkit for professionals',
                features: ['200 document credits', '100 case monitoring', 'Priority support', 'Bulk downloads', 'All features'],
                cta: 'Start 14-Day Trial',
                highlighted: false
              }
            ].map((plan, index) => (
              <motion.div
                key={index}
                className={`rounded-2xl p-8 ${
                  plan.highlighted
                    ? 'bg-white text-navy-800 shadow-2xl scale-105'
                    : 'bg-navy-700 text-white'
                }`}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
                <div className="mb-2">
                  <span className="text-4xl font-bold">
                    {billingPeriod === 'monthly' ? plan.priceMonthly : plan.priceAnnual}
                  </span>
                  <span className={plan.highlighted ? 'text-gray-500' : 'text-navy-300'}>{plan.period}</span>
                </div>
                {billingPeriod === 'annual' && plan.annualTotal && (
                  <p className={`text-sm mb-4 ${plan.highlighted ? 'text-teal-600' : 'text-teal-400'}`}>
                    Billed as {plan.annualTotal}
                  </p>
                )}
                {billingPeriod === 'monthly' && <div className="mb-4" />}
                <p className={`mb-6 ${plan.highlighted ? 'text-gray-600' : 'text-navy-300'}`}>{plan.description}</p>
                <ul className="space-y-3 mb-8 text-left">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-2">
                      <svg className={`w-5 h-5 ${plan.highlighted ? 'text-teal-500' : 'text-teal-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      <span className={plan.highlighted ? 'text-gray-600' : 'text-navy-200'}>{feature}</span>
                    </li>
                  ))}
                </ul>
                <Link
                  href={plan.planId === 'free'
                    ? '/auth/register'
                    : `/auth/register?plan=${plan.planId}&billing=${billingPeriod}`
                  }
                  className={`block w-full py-3 rounded-lg font-semibold transition-colors ${
                    plan.highlighted
                      ? 'bg-teal-600 text-white hover:bg-teal-700'
                      : 'bg-navy-600 text-white hover:bg-navy-500'
                  }`}
                >
                  {plan.cta}
                </Link>
              </motion.div>
            ))}
          </div>

          {/* Additional info */}
          <div className="mt-10 text-center">
            <p className="text-navy-200 mb-4">
              All paid plans include a 14-day free trial • Cancel anytime
            </p>
            <p className="text-navy-300 text-sm">
              Need more credits? Buy credit packs starting at $6.25 for 25 pages
            </p>
          </div>

          {/* Enterprise note */}
          <div className="mt-8 text-center">
            <p className="text-navy-200">
              Need a custom solution?{' '}
              <a href="mailto:support@courtcase-search.com" className="text-teal-400 hover:text-teal-300 underline">
                Contact us for Enterprise pricing
              </a>
            </p>
          </div>
        </div>
      </section>

      {/* Testimonial / Trust */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gray-50 rounded-2xl p-10 border border-gray-100">
            <p className="text-2xl text-navy-800 font-medium leading-relaxed mb-6">
              "We help you understand your legal documents. Your attorney helps you decide what to do about them."
            </p>
            <p className="text-gray-500">
              Our platform is designed to empower you with knowledge, not replace professional legal counsel.
            </p>
          </div>
        </div>
      </section>

      
      {/* User Ratings Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-navy-800">What Our Users Say</h2>
            <p className="mt-4 text-xl text-gray-600">Real feedback from people using LegalAI</p>
          </div>
          <RatingsDisplay showReviews={true} maxReviews={5} />
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="py-20 px-4 sm:px-6 lg:px-8 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-navy-800">Frequently Asked Questions</h2>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            {faqs.map((faq, index) => (
              <FAQItem key={index} question={faq.question} answer={faq.answer} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-navy-800">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Ready to Understand Your Legal Documents?
          </h2>
          <p className="text-xl text-navy-200 mb-8">
            Start with a free analysis and see the difference clarity makes.
          </p>
          <Link
            href="/pricing"
            className="inline-block bg-teal-500 text-white px-10 py-4 rounded-lg hover:bg-teal-600 transition-colors font-semibold text-lg shadow-lg"
          >
            Get Started Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-navy-900 text-white py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-12 mb-12">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-navy-600 rounded-lg flex items-center justify-center">
                  <ShieldCheckIcon />
                </div>
                <span className="font-semibold text-xl">LegalAI</span>
              </div>
              <p className="text-navy-300 text-sm">
                AI-powered legal document analysis for everyone.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Product</h4>
              <ul className="space-y-2 text-navy-300">
                <li><a href="#features" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#faq" className="hover:text-white transition-colors">FAQ</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Legal</h4>
              <ul className="space-y-2 text-navy-300">
                <li><Link href="/terms" className="hover:text-white transition-colors">Terms of Service</Link></li>
                <li><Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
                <li><Link href="/disclaimer" className="hover:text-white transition-colors">Disclaimer</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Contact</h4>
              <ul className="space-y-2 text-navy-300">
                <li><a href="mailto:support@courtcase-search.com" className="hover:text-white transition-colors">support@courtcase-search.com</a></li>
              </ul>
            </div>
          </div>

          {/* Compliance Footer */}
          <div className="border-t border-navy-700 pt-8">
            <div className="bg-navy-800 rounded-lg p-6 mb-8">
              <h4 className="font-semibold text-amber-400 mb-2 flex items-center gap-2">
                <ExclamationTriangleIcon />
                Important Disclaimer
              </h4>
              <p className="text-navy-300 text-sm leading-relaxed">
                This platform provides legal information for educational purposes only and does not constitute legal advice.
                No attorney-client relationship is created by using this service. The information provided should not be
                used as a substitute for competent legal advice from a licensed attorney in your jurisdiction.
                Always consult with a qualified attorney for advice regarding your specific legal situation.
              </p>
            </div>
            <div className="flex flex-col md:flex-row justify-between items-center text-navy-400 text-sm">
              <p>&copy; {new Date().getFullYear()} LegalAI. All rights reserved.</p>
              <p className="mt-2 md:mt-0">Made with care for those navigating the legal system.</p>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
