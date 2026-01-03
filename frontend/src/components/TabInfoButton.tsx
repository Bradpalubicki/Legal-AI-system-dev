'use client';

import { useState } from 'react';
import { HelpCircle, X, CreditCard, Download, FileText, Search, Shield, MessageSquare, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface TabInfo {
  title: string;
  icon: React.ReactNode;
  sections: {
    heading: string;
    content: string;
  }[];
}

const tabInfoContent: Record<string, TabInfo> = {
  pacer: {
    title: 'PACER Search Help',
    icon: <Search className="w-5 h-5" />,
    sections: [
      {
        heading: 'Search Sources',
        content: 'CourtListener (FREE, recommended) provides free access to most federal court records. PACER uses your subscription credits.'
      },
      {
        heading: 'Searching for Cases',
        content: 'Search by party name, case number, or case title. Select court type (Bankruptcy, District, or Circuit) to narrow results.'
      },
      {
        heading: 'FREE Documents',
        content: 'Look for the GREEN "FREE" badge! About 91% of federal filings are available free through CourtListener. Always check for free versions first.'
      },
      {
        heading: 'Credit Costs',
        content: 'PACER documents cost $0.25/page, maximum $7.50 per document. FREE documents cost nothing. Check your balance in Settings.'
      },
      {
        heading: 'Monitoring Cases',
        content: 'Click the eye icon next to any case to monitor it. You\'ll receive alerts when new documents are filed.'
      }
    ]
  },
  cases: {
    title: 'Case Tracking Help',
    icon: <Eye className="w-5 h-5" />,
    sections: [
      {
        heading: 'Monitored Cases',
        content: 'All cases you\'re monitoring appear here. Click any case to expand and see recent filings.'
      },
      {
        heading: 'Auto-Download',
        content: 'Enable auto-download to automatically save new filings to your Documents. FREE documents are always downloaded at no cost.'
      },
      {
        heading: 'Free Only Mode',
        content: 'Toggle "Free Only" to only auto-download FREE documents, never using your credits automatically.'
      },
      {
        heading: 'PACER Budget',
        content: 'Set a monthly budget per case for PACER downloads. The system stops auto-downloading when the budget is reached.'
      },
      {
        heading: 'Notifications',
        content: 'New filings appear as notifications when you log in. Configure email alerts in Settings.'
      }
    ]
  },
  documents: {
    title: 'Documents Help',
    icon: <FileText className="w-5 h-5" />,
    sections: [
      {
        heading: 'Uploading Documents',
        content: 'Upload PDF, DOC, DOCX, or TXT files. You can upload up to 20 documents at once.'
      },
      {
        heading: 'AI Analysis',
        content: 'Each document is automatically analyzed to extract: summaries, parties, legal issues, dates, and financial figures.'
      },
      {
        heading: 'Downloaded Documents',
        content: 'Documents downloaded from PACER Search automatically appear here, ready for AI analysis.'
      },
      {
        heading: 'Selecting Documents',
        content: 'Click any document to select it. The selected document is used for Q&A and Defense Builder features.'
      }
    ]
  },
  qa: {
    title: 'Q&A Assistant Help',
    icon: <MessageSquare className="w-5 h-5" />,
    sections: [
      {
        heading: 'Ask Questions',
        content: 'Type any legal question to get AI-powered answers. Questions can be about your uploaded documents or general legal concepts.'
      },
      {
        heading: 'Document Context',
        content: 'If you have a document selected, the AI will reference it when answering. For best results, select a relevant document first.'
      },
      {
        heading: 'What to Ask',
        content: 'Try: "Summarize this document", "What are the key deadlines?", "Who are the parties involved?", "Explain this legal term..."'
      }
    ]
  },
  defense: {
    title: 'Defense Builder Help',
    icon: <Shield className="w-5 h-5" />,
    sections: [
      {
        heading: 'Getting Started',
        content: 'First, upload and select a document in the Documents tab. The Defense Builder analyzes your document to help build a response strategy.'
      },
      {
        heading: 'Interview Process',
        content: 'The AI will ask you questions about your case. Answer honestly to get the most relevant defense strategies.'
      },
      {
        heading: 'Defense Analysis',
        content: 'After the interview, you\'ll receive: key arguments, counter-arguments, relevant case law, and suggested responses.'
      }
    ]
  }
};

interface TabInfoButtonProps {
  tabId: 'pacer' | 'cases' | 'documents' | 'qa' | 'defense';
  className?: string;
}

export function TabInfoButton({ tabId, className = '' }: TabInfoButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const info = tabInfoContent[tabId];

  if (!info) return null;

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(true)}
        className={`text-slate-500 hover:text-teal-600 hover:bg-teal-50 dark:hover:bg-teal-900/30 ${className}`}
        title={`${info.title}`}
      >
        <HelpCircle className="w-4 h-4" />
      </Button>

      {/* Modal Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setIsOpen(false)}
          />

          {/* Modal Content */}
          <div className="relative bg-white dark:bg-slate-800 rounded-xl shadow-xl max-w-lg w-full max-h-[80vh] overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700 bg-gradient-to-r from-teal-600 to-emerald-600">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center text-white">
                  {info.icon}
                </div>
                <h3 className="text-lg font-bold text-white">{info.title}</h3>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-5 overflow-y-auto max-h-[60vh]">
              <div className="space-y-4">
                {info.sections.map((section, index) => (
                  <div key={index} className="p-3 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                    <h4 className="font-semibold text-slate-900 dark:text-slate-100 mb-1 text-sm">
                      {section.heading}
                    </h4>
                    <p className="text-sm text-slate-600 dark:text-slate-300">
                      {section.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="px-5 py-3 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
              <p className="text-xs text-slate-500 dark:text-slate-400 text-center">
                Click the book icon in the toolbar for a full guided tour
              </p>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default TabInfoButton;
