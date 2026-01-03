'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import {
  FileText,
  Search,
  Bell,
  MessageSquare,
  Shield,
  CreditCard,
  Download,
  Eye,
  HelpCircle,
  CheckCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  BookOpen,
  Zap,
  DollarSign,
  Clock,
  Lock,
  ArrowRight,
  Home,
  X
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Section {
  id: string;
  title: string;
  icon: React.ReactNode;
}

const sections: Section[] = [
  { id: 'getting-started', title: 'Getting Started', icon: <Zap className="w-5 h-5" /> },
  { id: 'navigation', title: 'Platform Navigation', icon: <BookOpen className="w-5 h-5" /> },
  { id: 'credits', title: 'Credits & Billing', icon: <CreditCard className="w-5 h-5" /> },
  { id: 'searching', title: 'Searching Court Records', icon: <Search className="w-5 h-5" /> },
  { id: 'downloading', title: 'Downloading Documents', icon: <Download className="w-5 h-5" /> },
  { id: 'monitoring', title: 'Case Monitoring', icon: <Bell className="w-5 h-5" /> },
  { id: 'ai-features', title: 'AI-Powered Features', icon: <MessageSquare className="w-5 h-5" /> },
  { id: 'troubleshooting', title: 'Troubleshooting & FAQ', icon: <HelpCircle className="w-5 h-5" /> },
  { id: 'quick-reference', title: 'Quick Reference', icon: <FileText className="w-5 h-5" /> },
];

export default function WelcomePage() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const [activeSection, setActiveSection] = useState('getting-started');
  const [expandedFaq, setExpandedFaq] = useState<string | null>(null);

  const scrollToSection = (sectionId: string) => {
    setActiveSection(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleGetStarted = () => {
    // Mark onboarding as seen
    if (typeof window !== 'undefined') {
      localStorage.setItem('onboardingSeen', 'true');
    }
    router.push('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-lg flex items-center justify-center">
                <BookOpen className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                  Welcome Guide
                </h1>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Legal AI System Tutorial
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                onClick={() => router.push('/')}
                className="hidden sm:flex"
              >
                <Home className="w-4 h-4 mr-2" />
                Go to Dashboard
              </Button>
              <Button
                onClick={handleGetStarted}
                className="bg-teal-600 hover:bg-teal-700 text-white"
              >
                Get Started
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Important Notice Banner */}
        <div className="mb-8 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-800 dark:text-amber-200">Important Notice</h3>
              <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                This platform provides legal <strong>INFORMATION</strong> only, not legal advice.
                All AI analysis is for educational purposes. Consult a licensed attorney for advice
                about your specific situation.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar Navigation */}
          <aside className="lg:w-64 flex-shrink-0">
            <nav className="sticky top-24 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-4">
              <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4">
                Contents
              </h3>
              <ul className="space-y-1">
                {sections.map((section) => (
                  <li key={section.id}>
                    <button
                      onClick={() => scrollToSection(section.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        activeSection === section.id
                          ? 'bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300'
                          : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
                      }`}
                    >
                      {section.icon}
                      {section.title}
                    </button>
                  </li>
                ))}
              </ul>
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1 space-y-12">
            {/* Getting Started */}
            <section id="getting-started" className="scroll-mt-24">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 lg:p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-teal-100 dark:bg-teal-900/30 rounded-lg flex items-center justify-center">
                    <Zap className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Getting Started</h2>
                </div>

                <p className="text-slate-600 dark:text-slate-300 mb-6">
                  Welcome to the Legal AI System. This guide will walk you through everything you need
                  to know to effectively use the platform for federal court research, document analysis,
                  and case monitoring.
                </p>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Account Creation</h3>
                <p className="text-slate-600 dark:text-slate-300 mb-4">
                  Creating your account is quick and straightforward. Follow these steps to get started:
                </p>

                <ol className="space-y-3 mb-6">
                  {[
                    { step: 'Navigate to the Platform', desc: 'Visit the login page' },
                    { step: 'Click "Create Account"', desc: 'Located below the Sign In button' },
                    { step: 'Enter Your Information', desc: 'Provide email and create a secure password' },
                    { step: 'Accept Terms & Conditions', desc: 'Review the "No Legal Advice" disclaimer' },
                    { step: 'Verify Your Email', desc: 'Check your inbox for verification link' },
                    { step: 'Complete Profile Setup', desc: 'Add optional profile information' },
                  ].map((item, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <span className="flex-shrink-0 w-6 h-6 bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400 rounded-full flex items-center justify-center text-sm font-semibold">
                        {index + 1}
                      </span>
                      <div>
                        <span className="font-medium text-slate-900 dark:text-white">{item.step}</span>
                        <span className="text-slate-500 dark:text-slate-400"> - {item.desc}</span>
                      </div>
                    </li>
                  ))}
                </ol>

                <div className="bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-700 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <Lock className="w-5 h-5 text-teal-600 dark:text-teal-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-teal-800 dark:text-teal-200">Pro Tip</h4>
                      <p className="text-sm text-teal-700 dark:text-teal-300 mt-1">
                        Keep your login credentials secure. The platform implements enterprise-grade
                        encryption and audit trails to protect your data.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Platform Navigation */}
            <section id="navigation" className="scroll-mt-24">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 lg:p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                    <BookOpen className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Platform Navigation</h2>
                </div>

                <p className="text-slate-600 dark:text-slate-300 mb-6">
                  Once logged in, you'll see the main navigation tabs at the top of the screen.
                  Here's what each section does:
                </p>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-700">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Tab</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Description</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                      {[
                        { tab: 'Documents', desc: 'Upload and analyze legal documents with AI-powered summaries', icon: <FileText className="w-4 h-4" /> },
                        { tab: 'Q&A Assistant', desc: 'Ask questions about your documents or legal concepts', icon: <MessageSquare className="w-4 h-4" /> },
                        { tab: 'Defense Builder', desc: 'Organize response strategies (requires document upload)', icon: <Shield className="w-4 h-4" /> },
                        { tab: 'Case Tracking', desc: 'View and manage your monitored cases', icon: <Bell className="w-4 h-4" /> },
                        { tab: 'PACER Search', desc: 'Search federal court records and download filings', icon: <Search className="w-4 h-4" /> },
                      ].map((row, index) => (
                        <tr key={index}>
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2 text-slate-900 dark:text-white font-medium">
                              <span className="text-teal-600 dark:text-teal-400">{row.icon}</span>
                              {row.tab}
                            </div>
                          </td>
                          <td className="py-3 px-4 text-slate-600 dark:text-slate-300">{row.desc}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>

            {/* Credits & Billing */}
            <section id="credits" className="scroll-mt-24">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 lg:p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-emerald-100 dark:bg-emerald-900/30 rounded-lg flex items-center justify-center">
                    <CreditCard className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Understanding Credits & Adding Funds</h2>
                </div>

                <p className="text-slate-600 dark:text-slate-300 mb-6">
                  The Legal AI System uses a credit-based system for accessing PACER documents.
                  Understanding how credits work will help you manage your research budget effectively.
                </p>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Credit System Overview</h3>
                <p className="text-slate-600 dark:text-slate-300 mb-4">
                  Your account has two key metrics visible in the PACER Search tab:
                </p>
                <ul className="list-disc list-inside space-y-2 text-slate-600 dark:text-slate-300 mb-6 ml-4">
                  <li><strong>Credits Balance:</strong> Your current available credits (displayed as a dollar amount)</li>
                  <li><strong>Monthly Spending:</strong> Track your usage with the spending meter and remaining allowance</li>
                </ul>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Subscription Tiers</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-700">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Tier</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Price</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Credits</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Best For</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                      {[
                        { tier: 'Free', price: '$0', credits: '0 credits', best: 'Getting started' },
                        { tier: 'Basic', price: '$9.99/mo', credits: '20 credits', best: 'Occasional users' },
                        { tier: 'Individual Pro', price: '$29.99/mo', credits: '75 credits', best: 'Regular research' },
                        { tier: 'Professional', price: '$99/mo', credits: '200 credits', best: 'Heavy users' },
                      ].map((row, index) => (
                        <tr key={index}>
                          <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">{row.tier}</td>
                          <td className="py-3 px-4 text-teal-600 dark:text-teal-400 font-semibold">{row.price}</td>
                          <td className="py-3 px-4 text-slate-600 dark:text-slate-300">{row.credits}</td>
                          <td className="py-3 px-4 text-slate-600 dark:text-slate-300">{row.best}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-6">
                  <Link
                    href="/pricing"
                    className="inline-flex items-center gap-2 text-teal-600 dark:text-teal-400 hover:text-teal-700 dark:hover:text-teal-300 font-medium"
                  >
                    View all pricing options
                    <ExternalLink className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </section>

            {/* Searching Court Records */}
            <section id="searching" className="scroll-mt-24">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 lg:p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                    <Search className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Searching Federal Court Records</h2>
                </div>

                <p className="text-slate-600 dark:text-slate-300 mb-6">
                  The platform provides access to federal court records through two data sources:
                  CourtListener (free) and PACER (paid). Understanding the difference is key to
                  optimizing your research costs.
                </p>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">CourtListener vs. PACER Documents</h3>
                <p className="text-slate-600 dark:text-slate-300 mb-4">
                  This is one of the most important concepts to understand for cost-effective research:
                </p>

                <div className="overflow-x-auto mb-6">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-700">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-slate-900 dark:text-white">Feature</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-green-600 dark:text-green-400">CourtListener (FREE)</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-amber-600 dark:text-amber-400">PACER (Paid)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                      {[
                        { feature: 'Cost', free: 'FREE', paid: '~$0.10-$3.00 per document' },
                        { feature: 'Source', free: 'RECAP Archive (crowdsourced)', paid: 'Official federal courts' },
                        { feature: 'Coverage', free: '~91% of federal filings', paid: '100% of federal filings' },
                        { feature: 'Update Speed', free: 'Variable (community uploads)', paid: 'Real-time' },
                        { feature: 'Best For', free: 'Initial research, common docs', paid: 'Recent filings, complete records' },
                      ].map((row, index) => (
                        <tr key={index}>
                          <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">{row.feature}</td>
                          <td className="py-3 px-4 text-green-600 dark:text-green-400">{row.free}</td>
                          <td className="py-3 px-4 text-amber-600 dark:text-amber-400">{row.paid}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4 mb-6">
                  <div className="flex items-start gap-3">
                    <DollarSign className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-green-800 dark:text-green-200">Cost-Saving Strategy</h4>
                      <p className="text-sm text-green-700 dark:text-green-300 mt-1">
                        Always look for the <span className="font-bold text-green-600">GREEN "FREE" badge</span> on documents.
                        These CourtListener documents are available at no cost and contain the same official
                        court information. Only use credits for documents not available in the free archive.
                      </p>
                    </div>
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">How to Perform a Case Search</h3>
                <ol className="space-y-3">
                  {[
                    { step: 'Navigate to PACER Search Tab', desc: 'Click on "PACER Search" in the main navigation' },
                    { step: 'Verify Credentials Status', desc: 'Ensure your credentials show "Verified" with a green checkmark' },
                    { step: 'Choose Your Search Method', desc: 'Search by party name, case number, keywords, or CourtListener Docket ID' },
                    { step: 'Apply Filters (Optional)', desc: 'Filter by court type, date range, or case status' },
                    { step: 'Review Results', desc: 'Browse matching cases with case numbers, party names, court, and filing dates' },
                    { step: 'Select a Case', desc: 'Click to expand and view all available documents' },
                  ].map((item, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <span className="flex-shrink-0 w-6 h-6 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-full flex items-center justify-center text-sm font-semibold">
                        {index + 1}
                      </span>
                      <div>
                        <span className="font-medium text-slate-900 dark:text-white">{item.step}</span>
                        <span className="text-slate-500 dark:text-slate-400"> - {item.desc}</span>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            </section>

            {/* Downloading Documents */}
            <section id="downloading" className="scroll-mt-24">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 lg:p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
                    <Download className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Downloading Documents</h2>
                </div>

                <p className="text-slate-600 dark:text-slate-300 mb-6">
                  Once you've found a case, you'll see a document list showing all available filings.
                  Each document displays important information to help you decide what to download.
                </p>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Document Information</h3>
                <ul className="list-disc list-inside space-y-2 text-slate-600 dark:text-slate-300 mb-6 ml-4">
                  <li><strong>Document Number:</strong> The docket entry number (e.g., #883, #882)</li>
                  <li><strong>Document Type:</strong> Filing type such as Objection, Motion, Notice, etc.</li>
                  <li><strong>Filing Date:</strong> When the document was filed with the court</li>
                  <li><strong>Page Count:</strong> Number of pages (affects PACER cost)</li>
                  <li><strong>Cost Indicator:</strong> FREE badge or estimated PACER cost</li>
                </ul>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Download Options</h3>
                <div className="grid sm:grid-cols-3 gap-4">
                  {[
                    {
                      button: 'Download to App',
                      desc: 'Saves the document to your platform library for AI analysis (FREE docs only)',
                      color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                    },
                    {
                      button: 'View Online',
                      desc: 'Opens the document in a new browser tab for reading',
                      color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                    },
                    {
                      button: 'Purchase with Credits',
                      desc: 'Downloads PACER document using your credit balance',
                      color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                    },
                  ].map((item, index) => (
                    <div key={index} className={`rounded-lg p-4 ${item.color}`}>
                      <h4 className="font-semibold mb-2">{item.button}</h4>
                      <p className="text-sm opacity-90">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Case Monitoring */}
            <section id="monitoring" className="scroll-mt-24">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 lg:p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                    <Bell className="w-5 h-5 text-orange-600 dark:text-orange-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Case Monitoring</h2>
                </div>

                <p className="text-slate-600 dark:text-slate-300 mb-6">
                  Set up automated monitoring to receive alerts when new filings are added to cases
                  you're tracking. This is essential for staying current on active litigation.
                </p>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Setting Up Case Monitoring</h3>
                <ol className="space-y-3 mb-6">
                  {[
                    { step: 'Find Your Case', desc: 'Search for and locate the case you want to monitor' },
                    { step: 'Click the Monitor Button', desc: 'Look for the eye icon with "Monitor" next to each case' },
                    { step: 'Configure Alert Preferences', desc: 'Choose notification frequency and document types to track' },
                    { step: 'Confirm Monitoring', desc: 'The case will appear in your "Case Tracking" tab' },
                  ].map((item, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <span className="flex-shrink-0 w-6 h-6 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-full flex items-center justify-center text-sm font-semibold">
                        {index + 1}
                      </span>
                      <div>
                        <span className="font-medium text-slate-900 dark:text-white">{item.step}</span>
                        <span className="text-slate-500 dark:text-slate-400"> - {item.desc}</span>
                      </div>
                    </li>
                  ))}
                </ol>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Managing Monitored Cases</h3>
                <p className="text-slate-600 dark:text-slate-300 mb-4">
                  Access the "Case Tracking" tab to view and manage all your monitored cases. From here you can:
                </p>
                <ul className="list-disc list-inside space-y-2 text-slate-600 dark:text-slate-300 mb-6 ml-4">
                  <li>View all actively monitored cases in one dashboard</li>
                  <li>See recent filings and activity updates</li>
                  <li>Adjust notification settings per case</li>
                  <li>Remove cases you no longer need to track</li>
                  <li>Export monitoring history and reports</li>
                </ul>

                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <Eye className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-blue-800 dark:text-blue-200">Monitoring Limits</h4>
                      <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                        Monitoring capacity varies by subscription tier. Free plans include 1 case,
                        Basic plans include 5 cases, and Professional plans allow up to 100 monitored cases.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* AI-Powered Features */}
            <section id="ai-features" className="scroll-mt-24">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 lg:p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-pink-100 dark:bg-pink-900/30 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-pink-600 dark:text-pink-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">AI-Powered Features</h2>
                </div>

                <p className="text-slate-600 dark:text-slate-300 mb-6">
                  The platform includes several AI-enhanced capabilities designed to make legal research
                  more accessible and efficient.
                </p>

                <div className="space-y-6">
                  {/* Documents Tab */}
                  <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <FileText className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Documents Tab</h3>
                    </div>
                    <p className="text-slate-600 dark:text-slate-300 mb-3">
                      Upload legal documents for AI analysis. The system will provide:
                    </p>
                    <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 ml-4">
                      <li><strong>Plain-English Summaries:</strong> Complex legal filings explained accessibly</li>
                      <li><strong>Key Parties Identification:</strong> Automatic extraction of all parties</li>
                      <li><strong>Legal Issues Analysis:</strong> Main legal questions identified</li>
                      <li><strong>Timeline Generation:</strong> Visual case timeline with major dates</li>
                    </ul>
                  </div>

                  {/* Q&A Assistant */}
                  <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <MessageSquare className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Q&A Assistant</h3>
                    </div>
                    <p className="text-slate-600 dark:text-slate-300 mb-3">
                      Ask questions about uploaded documents or general legal concepts. The AI can help you:
                    </p>
                    <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-300 ml-4">
                      <li>Understand legal terminology and procedures</li>
                      <li>Extract specific information from lengthy filings</li>
                      <li>Compare different documents or case elements</li>
                      <li>Generate questions to ask a licensed attorney</li>
                    </ul>
                  </div>

                  {/* Defense Builder */}
                  <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Shield className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Defense Builder</h3>
                    </div>
                    <p className="text-slate-600 dark:text-slate-300">
                      <strong>Note:</strong> This feature requires document upload first. The Defense Builder
                      helps organize potential response strategies based on the filings in your case.
                    </p>
                  </div>
                </div>

                <div className="mt-6 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-amber-800 dark:text-amber-200">AI Disclaimer</h4>
                      <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                        AI analysis is provided for informational purposes only. AI systems can make errors
                        including 'hallucinations' (generating plausible but incorrect information).
                        Always verify important information independently and consult a licensed attorney
                        for legal advice.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Troubleshooting */}
            <section id="troubleshooting" className="scroll-mt-24">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 lg:p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-lg flex items-center justify-center">
                    <HelpCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Troubleshooting & FAQ</h2>
                </div>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Common Issues</h3>

                <div className="space-y-3">
                  {[
                    {
                      question: '"Failed to start monitoring" Error',
                      answer: 'This typically occurs when your PACER credentials need re-verification, there\'s a temporary connection issue, or the case has restrictions. Solution: Check credentials status, wait a few minutes, and try again.'
                    },
                    {
                      question: 'Credits Not Showing After Purchase',
                      answer: 'Allow 1-2 minutes for credits to reflect. If still not showing: refresh your browser, log out and back in, check email for payment confirmation, or contact support with your transaction ID.'
                    },
                    {
                      question: 'Document Download Failing',
                      answer: 'Ensure you have sufficient credits for PACER documents. For FREE documents, try "View Online" first. Large documents may take longer. Some sealed or restricted documents may not be available.'
                    },
                  ].map((faq, index) => (
                    <div
                      key={index}
                      className="border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => setExpandedFaq(expandedFaq === `faq-${index}` ? null : `faq-${index}`)}
                        className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                      >
                        <span className="font-medium text-slate-900 dark:text-white">{faq.question}</span>
                        {expandedFaq === `faq-${index}` ? (
                          <ChevronDown className="w-5 h-5 text-slate-400" />
                        ) : (
                          <ChevronRight className="w-5 h-5 text-slate-400" />
                        )}
                      </button>
                      {expandedFaq === `faq-${index}` && (
                        <div className="px-4 pb-4 text-slate-600 dark:text-slate-300">
                          {faq.answer}
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                <h3 className="text-lg font-semibold text-slate-900 dark:text-white mt-6 mb-4">Getting Help</h3>
                <p className="text-slate-600 dark:text-slate-300 mb-4">
                  If you encounter issues not covered here:
                </p>
                <ul className="list-disc list-inside space-y-2 text-slate-600 dark:text-slate-300 ml-4">
                  <li><strong>Email Support:</strong> support@courtcase-search.com</li>
                  <li><strong>Documentation:</strong> Check our help center for detailed guides</li>
                  <li><strong>Feedback:</strong> Use the feedback button to report bugs or suggest improvements</li>
                </ul>
              </div>
            </section>

            {/* Quick Reference */}
            <section id="quick-reference" className="scroll-mt-24">
              <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6 lg:p-8">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 bg-slate-100 dark:bg-slate-700 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">Quick Reference Card</h2>
                </div>

                <p className="text-slate-600 dark:text-slate-300 mb-6">
                  Keep this handy for a quick overview of key actions:
                </p>

                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-slate-700">
                        <th className="text-left py-3 px-4 font-semibold text-slate-900 dark:text-white">Action</th>
                        <th className="text-left py-3 px-4 font-semibold text-slate-900 dark:text-white">How To</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                      {[
                        { action: 'Search for a case', how: 'PACER Search → Enter name/number → Click Search' },
                        { action: 'Download FREE document', how: 'Find case → Look for green FREE badge → Click Download' },
                        { action: 'Download PACER document', how: 'Find case → Click Purchase with Credits → Confirm' },
                        { action: 'Monitor a case', how: 'Search results → Click Monitor (eye icon) → Confirm' },
                        { action: 'Add credits', how: 'Settings → Billing → Select package → Complete payment' },
                        { action: 'Analyze a document', how: 'Documents tab → Upload file → Wait for AI analysis' },
                        { action: 'Ask about a document', how: 'Q&A Assistant → Type question → Press Enter' },
                        { action: 'View monitored cases', how: 'Case Tracking tab → Browse your watched cases' },
                        { action: 'Check credit balance', how: 'Look at top-right "Credits Balance" indicator' },
                        { action: 'Log out', how: 'Click Logout button in header' },
                      ].map((row, index) => (
                        <tr key={index}>
                          <td className="py-3 px-4 font-medium text-slate-900 dark:text-white">{row.action}</td>
                          <td className="py-3 px-4 text-slate-600 dark:text-slate-300">{row.how}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>

            {/* Security & Privacy Footer */}
            <section className="scroll-mt-24">
              <div className="bg-gradient-to-r from-slate-800 to-slate-900 dark:from-slate-900 dark:to-black rounded-xl p-6 lg:p-8 text-white">
                <div className="flex items-center gap-3 mb-4">
                  <Lock className="w-6 h-6 text-teal-400" />
                  <h2 className="text-xl font-bold">Security & Privacy</h2>
                </div>
                <p className="text-slate-300 mb-6">
                  This system implements enterprise-grade security measures including encryption,
                  audit trails, and compliance monitoring. Your data is protected according to
                  legal industry standards. Never share your login credentials with others.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Button
                    onClick={handleGetStarted}
                    className="bg-teal-500 hover:bg-teal-600 text-white"
                  >
                    Start Using the Platform
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => router.push('/')}
                    className="border-slate-600 text-white hover:bg-slate-700"
                  >
                    <Home className="w-4 h-4 mr-2" />
                    Go to Dashboard
                  </Button>
                </div>
              </div>
            </section>

            {/* Thank You */}
            <div className="text-center py-8">
              <p className="text-slate-500 dark:text-slate-400">
                Thank you for choosing <span className="font-semibold text-slate-700 dark:text-slate-300">Legal AI System</span>
              </p>
              <p className="text-sm text-slate-400 dark:text-slate-500 mt-2">
                For the latest updates, visit{' '}
                <a
                  href="https://courtcase-search.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-teal-600 dark:text-teal-400 hover:underline"
                >
                  courtcase-search.com
                </a>
              </p>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
