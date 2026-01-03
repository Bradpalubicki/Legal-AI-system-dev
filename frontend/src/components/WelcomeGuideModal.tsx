'use client';

import { useState } from 'react';
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
  AlertTriangle,
  BookOpen,
  Zap,
  DollarSign,
  Lock,
  X,
  ChevronLeft,
  ChevronRight,
  CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Step {
  id: string;
  title: string;
  icon: React.ReactNode;
  content: React.ReactNode;
}

export function WelcomeGuideModal({ isOpen, onClose }: WelcomeGuideModalProps) {
  const [currentStep, setCurrentStep] = useState(0);

  if (!isOpen) return null;

  const steps: Step[] = [
    {
      id: 'welcome',
      title: 'Welcome',
      icon: <Zap className="w-6 h-6" />,
      content: (
        <div className="space-y-4">
          <div className="text-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <BookOpen className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">Welcome to Legal AI System</h3>
            <p className="text-slate-500 dark:text-slate-400 mt-2">Your comprehensive federal court research platform</p>
          </div>

          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-amber-800 dark:text-amber-200">Important Notice</h4>
                <p className="text-sm text-amber-700 dark:text-amber-300 mt-1">
                  This platform provides legal <strong>INFORMATION</strong> only, not legal advice.
                  Consult a licensed attorney for advice about your specific situation.
                </p>
              </div>
            </div>
          </div>

          <p className="text-slate-600 dark:text-slate-300">
            This quick guide will walk you through the main features of the platform. Click <strong>Next</strong> to get started!
          </p>

          <div className="grid grid-cols-2 gap-3 mt-4">
            {[
              { icon: <Search className="w-5 h-5" />, label: 'Search Cases' },
              { icon: <Download className="w-5 h-5" />, label: 'Download Documents' },
              { icon: <Bell className="w-5 h-5" />, label: 'Monitor Cases' },
              { icon: <MessageSquare className="w-5 h-5" />, label: 'AI Analysis' },
            ].map((feature, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <span className="text-teal-600 dark:text-teal-400">{feature.icon}</span>
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{feature.label}</span>
              </div>
            ))}
          </div>
        </div>
      ),
    },
    {
      id: 'documents',
      title: 'Documents Tab',
      icon: <FileText className="w-6 h-6" />,
      content: (
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-teal-100 dark:bg-teal-900/30 rounded-xl flex items-center justify-center">
              <FileText className="w-6 h-6 text-teal-600 dark:text-teal-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">Documents Tab</h3>
              <p className="text-slate-500 dark:text-slate-400">Upload & Analyze Legal Documents</p>
            </div>
          </div>

          <p className="text-slate-600 dark:text-slate-300">
            Upload your legal documents for AI-powered analysis. The system will automatically extract key information.
          </p>

          <h4 className="font-semibold text-slate-900 dark:text-white">What You'll Get:</h4>
          <div className="space-y-2">
            {[
              { title: 'Plain-English Summaries', desc: 'Complex legal filings explained simply' },
              { title: 'Key Parties Identification', desc: 'Automatic extraction of all parties' },
              { title: 'Legal Issues Analysis', desc: 'Main legal questions identified' },
              { title: 'Timeline Generation', desc: 'Visual case timeline with dates' },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-medium text-slate-900 dark:text-white">{item.title}</span>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-700 rounded-lg p-3">
            <p className="text-sm text-teal-700 dark:text-teal-300">
              <strong>Tip:</strong> Supported formats include PDF, DOCX, and TXT files.
            </p>
          </div>
        </div>
      ),
    },
    {
      id: 'qa-assistant',
      title: 'Q&A Assistant',
      icon: <MessageSquare className="w-6 h-6" />,
      content: (
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center">
              <MessageSquare className="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">Q&A Assistant</h3>
              <p className="text-slate-500 dark:text-slate-400">Ask Questions About Your Documents</p>
            </div>
          </div>

          <p className="text-slate-600 dark:text-slate-300">
            Get instant answers about your uploaded documents or general legal concepts using our AI assistant.
          </p>

          <h4 className="font-semibold text-slate-900 dark:text-white">You Can Ask About:</h4>
          <ul className="space-y-2">
            {[
              'Legal terminology and procedures',
              'Specific information from your filings',
              'Comparing different documents',
              'Questions to ask a licensed attorney',
            ].map((item, i) => (
              <li key={i} className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                <ChevronRight className="w-4 h-4 text-purple-500" />
                {item}
              </li>
            ))}
          </ul>

          <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-amber-700 dark:text-amber-300">
                <strong>Remember:</strong> AI can make errors. Always verify important information independently.
              </p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'defense-builder',
      title: 'Defense Builder',
      icon: <Shield className="w-6 h-6" />,
      content: (
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">Defense Builder</h3>
              <p className="text-slate-500 dark:text-slate-400">Organize Response Strategies</p>
            </div>
          </div>

          <p className="text-slate-600 dark:text-slate-300">
            The Defense Builder helps you organize potential response strategies based on the filings in your case.
          </p>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-blue-800 dark:text-blue-200">Requires Document Upload</h4>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Upload documents in the Documents tab first. The Defense Builder analyzes your uploaded filings to suggest strategies.
                </p>
              </div>
            </div>
          </div>

          <h4 className="font-semibold text-slate-900 dark:text-white">Features:</h4>
          <ul className="space-y-2">
            {[
              'Identify key arguments from opposing filings',
              'Organize counter-arguments',
              'Track response deadlines',
              'Generate questions for your attorney',
            ].map((item, i) => (
              <li key={i} className="flex items-center gap-2 text-slate-600 dark:text-slate-300">
                <CheckCircle className="w-4 h-4 text-green-500" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      ),
    },
    {
      id: 'case-tracking',
      title: 'Case Tracking',
      icon: <Bell className="w-6 h-6" />,
      content: (
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/30 rounded-xl flex items-center justify-center">
              <Bell className="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">Case Tracking</h3>
              <p className="text-slate-500 dark:text-slate-400">Monitor Cases & Get Alerts</p>
            </div>
          </div>

          <p className="text-slate-600 dark:text-slate-300">
            Set up automated monitoring to receive alerts when new filings are added to cases you're tracking.
          </p>

          <h4 className="font-semibold text-slate-900 dark:text-white">How to Monitor a Case:</h4>
          <ol className="space-y-2">
            {[
              'Search for your case in PACER Search',
              'Click the Monitor button (eye icon)',
              'Configure your alert preferences',
              'View all monitored cases here in Case Tracking',
            ].map((item, i) => (
              <li key={i} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 rounded-full flex items-center justify-center text-sm font-semibold">
                  {i + 1}
                </span>
                <span className="text-slate-600 dark:text-slate-300">{item}</span>
              </li>
            ))}
          </ol>

          <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-3">
            <h5 className="font-semibold text-slate-900 dark:text-white mb-2">Monitoring Limits by Plan:</h5>
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded">
                <div className="font-bold text-slate-900 dark:text-white">Free</div>
                <div className="text-slate-500">1 case</div>
              </div>
              <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded">
                <div className="font-bold text-slate-900 dark:text-white">Basic</div>
                <div className="text-slate-500">5 cases</div>
              </div>
              <div className="p-2 bg-slate-100 dark:bg-slate-700 rounded">
                <div className="font-bold text-slate-900 dark:text-white">Pro</div>
                <div className="text-slate-500">100 cases</div>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'pacer-search',
      title: 'PACER Search',
      icon: <Search className="w-6 h-6" />,
      content: (
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-indigo-100 dark:bg-indigo-900/30 rounded-xl flex items-center justify-center">
              <Search className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">PACER Search</h3>
              <p className="text-slate-500 dark:text-slate-400">Search Federal Court Records</p>
            </div>
          </div>

          <p className="text-slate-600 dark:text-slate-300">
            Access federal court records through two data sources: <span className="text-green-600 font-semibold">CourtListener (FREE)</span> and <span className="text-amber-600 font-semibold">PACER (Paid)</span>.
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-700">
                  <th className="text-left py-2 px-3 font-semibold text-slate-900 dark:text-white">Feature</th>
                  <th className="text-left py-2 px-3 font-semibold text-green-600">FREE</th>
                  <th className="text-left py-2 px-3 font-semibold text-amber-600">PACER</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                <tr>
                  <td className="py-2 px-3 text-slate-700 dark:text-slate-300">Cost</td>
                  <td className="py-2 px-3 text-green-600 font-medium">$0</td>
                  <td className="py-2 px-3 text-amber-600">$0.10-$3/doc</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 text-slate-700 dark:text-slate-300">Coverage</td>
                  <td className="py-2 px-3 text-green-600">~91%</td>
                  <td className="py-2 px-3 text-amber-600">100%</td>
                </tr>
                <tr>
                  <td className="py-2 px-3 text-slate-700 dark:text-slate-300">Best For</td>
                  <td className="py-2 px-3 text-green-600">Initial research</td>
                  <td className="py-2 px-3 text-amber-600">Recent filings</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-3">
            <div className="flex items-start gap-2">
              <DollarSign className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-green-700 dark:text-green-300">
                <strong>Save Money:</strong> Look for the <span className="font-bold text-green-600 bg-green-100 dark:bg-green-800 px-1 rounded">GREEN "FREE" badge</span> on documents!
              </p>
            </div>
          </div>
        </div>
      ),
    },
    {
      id: 'credits',
      title: 'Credits & Billing',
      icon: <CreditCard className="w-6 h-6" />,
      content: (
        <div className="space-y-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/30 rounded-xl flex items-center justify-center">
              <CreditCard className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white">Credits & Billing</h3>
              <p className="text-slate-500 dark:text-slate-400">Understanding the Credit System</p>
            </div>
          </div>

          <p className="text-slate-600 dark:text-slate-300">
            Credits are used for downloading PACER documents. Your balance is visible in the top-right of the PACER Search tab.
          </p>

          <h4 className="font-semibold text-slate-900 dark:text-white">Subscription Tiers:</h4>
          <div className="space-y-2">
            {[
              { tier: 'Free', price: '$0/mo', credits: '0 credits', color: 'bg-slate-100 dark:bg-slate-700' },
              { tier: 'Basic', price: '$9.99/mo', credits: '20 credits', color: 'bg-blue-50 dark:bg-blue-900/20' },
              { tier: 'Individual Pro', price: '$29.99/mo', credits: '75 credits', color: 'bg-purple-50 dark:bg-purple-900/20' },
              { tier: 'Professional', price: '$99/mo', credits: '200 credits', color: 'bg-emerald-50 dark:bg-emerald-900/20' },
            ].map((plan, i) => (
              <div key={i} className={`flex items-center justify-between p-3 rounded-lg ${plan.color}`}>
                <span className="font-medium text-slate-900 dark:text-white">{plan.tier}</span>
                <div className="text-right">
                  <span className="font-bold text-teal-600 dark:text-teal-400">{plan.price}</span>
                  <span className="text-slate-500 dark:text-slate-400 text-sm ml-2">({plan.credits})</span>
                </div>
              </div>
            ))}
          </div>

          <div className="bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-700 rounded-lg p-3">
            <p className="text-sm text-teal-700 dark:text-teal-300">
              <strong>Add Credits:</strong> Go to Settings → Billing → Select a package
            </p>
          </div>
        </div>
      ),
    },
    {
      id: 'complete',
      title: 'You\'re Ready!',
      icon: <CheckCircle className="w-6 h-6" />,
      content: (
        <div className="space-y-4 text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-10 h-10 text-white" />
          </div>

          <h3 className="text-2xl font-bold text-slate-900 dark:text-white">You're All Set!</h3>
          <p className="text-slate-500 dark:text-slate-400">You're now ready to start using Legal AI System</p>

          <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-xl p-4 text-white text-left mt-6">
            <div className="flex items-center gap-2 mb-2">
              <Lock className="w-5 h-5 text-teal-400" />
              <h4 className="font-bold">Security & Privacy</h4>
            </div>
            <p className="text-sm text-slate-300">
              Your data is protected with enterprise-grade encryption and audit trails. Never share your login credentials.
            </p>
          </div>

          <div className="pt-4">
            <h4 className="font-semibold text-slate-900 dark:text-white mb-3">Quick Reference:</h4>
            <div className="grid grid-cols-2 gap-2 text-sm text-left">
              {[
                { action: 'Search case', how: 'PACER Search tab' },
                { action: 'Upload doc', how: 'Documents tab' },
                { action: 'Monitor case', how: 'Eye icon in search' },
                { action: 'Get help', how: 'support@courtcase-search.com' },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-2 p-2 bg-slate-50 dark:bg-slate-800 rounded">
                  <ChevronRight className="w-4 h-4 text-teal-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-medium text-slate-900 dark:text-white">{item.action}</span>
                    <p className="text-xs text-slate-500">{item.how}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ),
    },
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onClose();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepClick = (index: number) => {
    setCurrentStep(index);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full max-w-2xl max-h-[90vh] mx-4 bg-white dark:bg-slate-900 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-lg flex items-center justify-center text-white">
              {steps[currentStep].icon}
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-white">{steps[currentStep].title}</h2>
              <p className="text-sm text-slate-500">Step {currentStep + 1} of {steps.length}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 flex items-center justify-center text-slate-500 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/50">
          <div className="flex items-center gap-1">
            {steps.map((step, index) => (
              <button
                key={step.id}
                onClick={() => handleStepClick(index)}
                className={`flex-1 h-2 rounded-full transition-colors ${
                  index <= currentStep
                    ? 'bg-teal-500'
                    : 'bg-slate-200 dark:bg-slate-700'
                }`}
                title={step.title}
              />
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {steps[currentStep].content}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="flex items-center gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </Button>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              onClick={onClose}
              className="text-slate-500"
            >
              Skip
            </Button>
            <Button
              onClick={handleNext}
              className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-2"
            >
              {currentStep === steps.length - 1 ? 'Get Started' : 'Next'}
              {currentStep < steps.length - 1 && <ChevronRight className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WelcomeGuideModal;
