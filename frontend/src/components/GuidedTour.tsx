'use client';

import { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import {
  FileText,
  Search,
  Bell,
  MessageSquare,
  Shield,
  CreditCard,
  ChevronLeft,
  ChevronRight,
  X,
  Eye,
  AlertTriangle,
  CheckCircle,
  Download,
  Zap,
  HelpCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export interface TourStep {
  id: string;
  title: string;
  description: string;
  targetSelector?: string; // CSS selector for element to highlight
  tabId?: string; // Tab to switch to
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  icon?: React.ReactNode;
  highlight?: boolean;
}

interface GuidedTourProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
  onTabChange?: (tabId: string) => void;
}

const tourSteps: TourStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to Legal AI System!',
    description: 'This quick tour will show you how to search for cases, download documents, and set up case monitoring. Let\'s get started!',
    position: 'center',
    icon: <Zap className="w-8 h-8" />,
  },
  {
    id: 'disclaimer',
    title: 'Important Notice',
    description: 'This platform provides legal INFORMATION only, not legal advice. All AI analysis is for educational purposes. Always consult a licensed attorney for advice about your specific situation.',
    position: 'center',
    icon: <AlertTriangle className="w-8 h-8 text-amber-500" />,
  },
  {
    id: 'pacer-tab',
    title: 'PACER Search Tab',
    description: 'This is where you search for federal court cases. Click this tab to access court records from all U.S. District Courts, Bankruptcy Courts, and Courts of Appeals.',
    targetSelector: '[data-tour="pacer-tab"]',
    tabId: 'pacer',
    position: 'bottom',
    icon: <Search className="w-6 h-6" />,
    highlight: true,
  },
  {
    id: 'search-how-to',
    title: 'How to Search for Cases',
    description: 'Use this search form to find cases:\n\n• Search by Party Name (e.g., "Smith")\n• Search by Case Number (e.g., "1:23-cv-00123")\n• Search by Case Title keywords\n• Filter by court type and date range\n\nResults will show matching federal court cases.',
    targetSelector: '[data-tour="pacer-search-form"]',
    tabId: 'pacer',
    position: 'center',
    icon: <Search className="w-6 h-6" />,
    highlight: true,
  },
  {
    id: 'free-docs',
    title: 'FREE vs PACER Documents',
    description: 'Look for the GREEN "FREE" badge on documents!\n\n✓ FREE docs come from CourtListener\'s archive\n✓ About 91% of federal filings are available free\n✓ PACER docs require credits to download\n\nAlways check for free versions first to save money!',
    tabId: 'pacer',
    position: 'center',
    icon: <Download className="w-6 h-6 text-green-500" />,
  },
  {
    id: 'how-to-download',
    title: 'Downloading Documents',
    description: 'After finding a case, click to expand and see all documents. You have three options:\n\n• "Download to App" - Saves FREE docs to your library for AI analysis\n• "View Online" - Opens document in browser\n• "Purchase" - Downloads PACER docs using credits\n\nDownloaded docs appear in your Documents tab for analysis!',
    tabId: 'pacer',
    position: 'center',
    icon: <Download className="w-6 h-6" />,
  },
  {
    id: 'credit-costs',
    title: 'Understanding Credit Costs',
    description: 'Document downloads use credits from your subscription:\n\n• $0.25 per page for PACER documents\n• Maximum $7.50 per document (30+ pages)\n• FREE documents: $0.00 (no credits needed!)\n\nExample: A 10-page motion costs $2.50\nExample: A 50-page brief costs $7.50 (capped)\n\nCheck your credit balance in Settings → Subscription.',
    tabId: 'pacer',
    position: 'center',
    icon: <CreditCard className="w-6 h-6" />,
  },
  {
    id: 'monitor-case',
    title: 'How to Monitor a Case',
    description: 'To get alerts when new documents are filed:\n\n1. Search for a case in PACER Search\n2. Click the eye icon (👁) next to the case\n3. Choose your notification preferences\n4. You\'ll receive alerts for new filings!\n\nThis is essential for staying current on active litigation.',
    tabId: 'pacer',
    position: 'center',
    icon: <Eye className="w-6 h-6 text-orange-500" />,
  },
  {
    id: 'auto-download',
    title: 'Auto-Download Feature',
    description: 'When monitoring a case, you can enable Auto-Download:\n\n• New filings are automatically downloaded to your library\n• FREE documents are always downloaded (no credits used)\n• PACER documents use your credits ($0.25/page)\n\n⚙️ Control options:\n• "Free Only" - Only auto-download FREE documents\n• Set a PACER budget limit per case\n• Turn off auto-download completely\n\nManage in Case Tracking or Settings → Subscription.',
    tabId: 'cases',
    position: 'center',
    icon: <Download className="w-6 h-6 text-teal-500" />,
  },
  {
    id: 'case-tracking-tab',
    title: 'Case Tracking Tab',
    description: 'All your monitored cases appear here. View new filings, manage alert settings, and track activity across all cases you\'re watching.',
    targetSelector: '[data-tour="cases-tab"]',
    tabId: 'cases',
    position: 'bottom',
    icon: <Bell className="w-6 h-6" />,
    highlight: true,
  },
  {
    id: 'cases-monitored',
    title: 'Your Monitored Cases',
    description: 'This is where all your monitored cases appear:\n\n• See case name, court, and status\n• View recent filings and updates\n• Toggle auto-download per case\n• Set PACER budget limits\n• Click to expand for more options\n\nNew filings show automatically when they are detected.',
    targetSelector: '[data-tour="cases-monitored"]',
    tabId: 'cases',
    position: 'center',
    icon: <Eye className="w-6 h-6" />,
    highlight: true,
  },
  {
    id: 'documents-tab',
    title: 'Documents Tab',
    description: 'Upload documents here OR they appear automatically when you download from PACER Search.',
    targetSelector: '[data-tour="documents-tab"]',
    tabId: 'documents',
    position: 'bottom',
    icon: <FileText className="w-6 h-6" />,
    highlight: true,
  },
  {
    id: 'documents-upload',
    title: 'Upload Your Documents',
    description: 'Click this area to upload legal documents:\n\n• Supports PDF, DOC, DOCX, and TXT files\n• Upload up to 20 documents at once\n• Documents are automatically analyzed by AI\n• Drag and drop supported\n\nDocuments downloaded from PACER Search also appear here.',
    targetSelector: '[data-tour="documents-upload"]',
    tabId: 'documents',
    position: 'center',
    icon: <FileText className="w-6 h-6" />,
    highlight: true,
  },
  {
    id: 'ai-analysis',
    title: 'AI Document Analysis',
    description: 'When you upload or download a document, our AI automatically analyzes it:\n\n• Plain-English Summary - Complex filings explained simply\n• Key Parties - All parties extracted and identified\n• Legal Issues - Main legal questions identified\n• Important Dates - Timeline of key events\n• Financial Figures - Dollar amounts and claims extracted\n\nAnalysis takes 30-60 seconds. Results appear in the document details.',
    tabId: 'documents',
    position: 'center',
    icon: <FileText className="w-6 h-6" />,
  },
  {
    id: 'qa-tab',
    title: 'Q&A Assistant',
    description: 'Ask questions about your uploaded documents or general legal concepts. The AI can help:\n\n• Explain legal terminology\n• Extract specific information\n• Compare documents\n• Generate questions for your attorney',
    targetSelector: '[data-tour="qa-tab"]',
    tabId: 'qa',
    position: 'bottom',
    icon: <MessageSquare className="w-6 h-6" />,
    highlight: true,
  },
  {
    id: 'defense-tab',
    title: 'Defense Builder',
    description: 'After uploading documents, use this tab to organize response strategies. The AI analyzes filings to help:\n\n• Identify key arguments\n• Organize counter-arguments\n• Track response deadlines\n\nNote: Requires document upload first.',
    targetSelector: '[data-tour="defense-tab"]',
    tabId: 'defense',
    position: 'bottom',
    icon: <Shield className="w-6 h-6" />,
    highlight: true,
  },
  {
    id: 'subscriptions',
    title: 'Subscription Plans',
    description: 'Choose a plan that fits your needs:\n\n• Free: $0/mo - 0 credits, 1 monitored case\n• Basic: $9.99/mo - 20 credits, 5 cases\n• Pro: $29.99/mo - 75 credits, 25 cases\n• Professional: $99/mo - 200 credits, 100 cases\n\nUpgrade anytime in Settings → Subscription.\nCredits refresh monthly with your plan.',
    position: 'center',
    icon: <CreditCard className="w-6 h-6" />,
  },
  {
    id: 'help',
    title: 'Need Help?',
    description: 'We have a Help Assistant available anytime!\n\nClick the "?" icon in the toolbar to open our AI-powered help assistant. It can answer questions about:\n\n• How to use any feature\n• Understanding court records\n• Troubleshooting issues\n• General platform questions\n\nYou can also email: support@courtcase-search.com',
    position: 'center',
    icon: <HelpCircle className="w-6 h-6" />,
  },
  {
    id: 'complete',
    title: 'You\'re All Set!',
    description: 'You now know the basics:\n\n✓ Search for cases in PACER Search\n✓ Download FREE documents (green badge)\n✓ Monitor cases for new filings\n✓ Configure auto-download for monitored cases\n✓ Upload docs for AI analysis\n✓ Check usage in Settings → Subscription\n\nClick the blue book icon anytime to replay this tour.',
    position: 'center',
    icon: <CheckCircle className="w-8 h-8 text-green-500" />,
  },
];

export function GuidedTour({ isOpen, onClose, onComplete, onTabChange }: GuidedTourProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const step = tourSteps[currentStep];

  // Find and highlight target element
  const updateTargetPosition = useCallback(() => {
    if (!step?.targetSelector) {
      setTargetRect(null);
      return;
    }

    const element = document.querySelector(step.targetSelector);
    if (element) {
      // Scroll element into view if needed (with some padding)
      const rect = element.getBoundingClientRect();
      const viewportHeight = window.innerHeight;

      // Check if element is not fully visible
      if (rect.top < 100 || rect.bottom > viewportHeight - 100) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Update rect after scroll settles
        setTimeout(() => {
          const newRect = element.getBoundingClientRect();
          setTargetRect(newRect);
        }, 300);
      } else {
        setTargetRect(rect);
      }
    } else {
      setTargetRect(null);
    }
  }, [step?.targetSelector]);

  // Update position on step change or resize
  useEffect(() => {
    if (!isOpen) return;

    // Switch tab if needed
    if (step?.tabId && onTabChange) {
      onTabChange(step.tabId);
      // Wait for tab to render before finding element
      setTimeout(updateTargetPosition, 100);
    } else {
      updateTargetPosition();
    }

    window.addEventListener('resize', updateTargetPosition);
    window.addEventListener('scroll', updateTargetPosition);

    return () => {
      window.removeEventListener('resize', updateTargetPosition);
      window.removeEventListener('scroll', updateTargetPosition);
    };
  }, [isOpen, currentStep, step?.tabId, onTabChange, updateTargetPosition]);

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
      onClose();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    onClose();
  };

  if (!isOpen || !mounted) return null;

  // Calculate tooltip position with viewport bounds checking
  const getTooltipStyle = (): React.CSSProperties => {
    const padding = 16;
    const tooltipWidth = 400;
    const tooltipHeight = 320; // Increased for content

    // Center position for non-highlighted steps or missing target
    if (!targetRect || step.position === 'center') {
      return {
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
      };
    }

    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    // Calculate horizontal position (centered on target, clamped to viewport)
    const horizontalCenter = targetRect.left + targetRect.width / 2 - tooltipWidth / 2;
    const left = Math.max(padding, Math.min(horizontalCenter, viewportWidth - tooltipWidth - padding));

    // Try preferred position first, then fallback to alternatives
    let top: number;
    let finalPosition = step.position;

    // Check if bottom position would work
    const bottomTop = targetRect.bottom + padding;
    const bottomFits = bottomTop + tooltipHeight <= viewportHeight - padding;

    // Check if top position would work
    const topTop = targetRect.top - tooltipHeight - padding;
    const topFits = topTop >= padding;

    // For 'bottom' preference
    if (step.position === 'bottom') {
      if (bottomFits) {
        top = bottomTop;
      } else if (topFits) {
        top = topTop;
        finalPosition = 'top';
      } else {
        // Neither fits - center in viewport
        top = Math.max(padding, (viewportHeight - tooltipHeight) / 2);
      }
    }
    // For 'top' preference
    else if (step.position === 'top') {
      if (topFits) {
        top = topTop;
      } else if (bottomFits) {
        top = bottomTop;
        finalPosition = 'bottom';
      } else {
        top = Math.max(padding, (viewportHeight - tooltipHeight) / 2);
      }
    }
    // For 'left' or 'right' - center vertically relative to target
    else {
      const verticalCenter = targetRect.top + targetRect.height / 2 - tooltipHeight / 2;
      top = Math.max(padding, Math.min(verticalCenter, viewportHeight - tooltipHeight - padding));
    }

    // Final bounds check
    top = Math.max(padding, Math.min(top, viewportHeight - tooltipHeight - padding));

    return {
      position: 'fixed',
      top,
      left,
    };
  };

  const overlay = (
    <div className="fixed inset-0 z-[9999]">
      {/* Dark overlay with spotlight cutout */}
      <svg className="absolute inset-0 w-full h-full" style={{ pointerEvents: 'none' }}>
        <defs>
          <mask id="spotlight-mask">
            <rect x="0" y="0" width="100%" height="100%" fill="white" />
            {targetRect && step.highlight && (
              <rect
                x={targetRect.left - 8}
                y={targetRect.top - 8}
                width={targetRect.width + 16}
                height={targetRect.height + 16}
                rx="8"
                fill="black"
              />
            )}
          </mask>
        </defs>
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="rgba(0, 0, 0, 0.75)"
          mask="url(#spotlight-mask)"
        />
      </svg>

      {/* Highlight border around target element */}
      {targetRect && step.highlight && (
        <div
          className="absolute border-2 border-teal-400 rounded-lg pointer-events-none animate-pulse"
          style={{
            left: targetRect.left - 8,
            top: targetRect.top - 8,
            width: targetRect.width + 16,
            height: targetRect.height + 16,
            boxShadow: '0 0 0 4px rgba(20, 184, 166, 0.3), 0 0 20px rgba(20, 184, 166, 0.5)',
          }}
        />
      )}

      {/* Click blocker (except for highlighted area) */}
      <div
        className="absolute inset-0"
        onClick={(e) => {
          // Allow clicks on highlighted element
          if (targetRect && step.highlight) {
            const { clientX, clientY } = e;
            if (
              clientX >= targetRect.left - 8 &&
              clientX <= targetRect.right + 8 &&
              clientY >= targetRect.top - 8 &&
              clientY <= targetRect.bottom + 8
            ) {
              return; // Allow click through
            }
          }
          e.stopPropagation();
        }}
      />

      {/* Tooltip */}
      <div
        className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl w-[400px] max-w-[calc(100vw-32px)] overflow-hidden"
        style={getTooltipStyle()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-teal-600 to-emerald-600">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center text-white">
              {step.icon}
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">{step.title}</h3>
              <p className="text-sm text-teal-100">Step {currentStep + 1} of {tourSteps.length}</p>
            </div>
          </div>
          <button
            onClick={handleSkip}
            className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-5 py-2 bg-slate-50 dark:bg-slate-800/50">
          <div className="flex items-center gap-1">
            {tourSteps.map((_, index) => (
              <div
                key={index}
                className={`flex-1 h-1.5 rounded-full transition-colors ${
                  index <= currentStep ? 'bg-teal-500' : 'bg-slate-200 dark:bg-slate-700'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="px-5 py-4">
          <p className="text-slate-600 dark:text-slate-300 whitespace-pre-line text-sm leading-relaxed">
            {step.description}
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-5 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className="flex items-center gap-1"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </Button>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleSkip}
              className="text-slate-500"
            >
              Skip Tour
            </Button>
            <Button
              size="sm"
              onClick={handleNext}
              className="bg-teal-600 hover:bg-teal-700 text-white flex items-center gap-1"
            >
              {currentStep === tourSteps.length - 1 ? 'Finish' : 'Next'}
              {currentStep < tourSteps.length - 1 && <ChevronRight className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(overlay, document.body);
}

export default GuidedTour;
