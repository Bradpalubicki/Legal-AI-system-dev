'use client';

import React from 'react';
import { Modal, ModalBody, ModalFooter } from '@/components/ui/modal';
import { Button } from '@/components/design-system';
import { FileText, Bell, ExternalLink, Calendar, Scale } from 'lucide-react';
import { useRouter } from 'next/navigation';

interface NewFiling {
  docket_id: number;
  case_name: string;
  court: string;
  new_documents: Array<{
    description?: string;
    entry_number?: number;
    date_filed?: string;
  }>;
  document_count: number;
  latest_notification: string | null;
}

interface NewFilingModalProps {
  isOpen: boolean;
  onClose: () => void;
  filings: NewFiling[];
  totalDocuments: number;
  since: string | null;
}

export function NewFilingModal({
  isOpen,
  onClose,
  filings,
  totalDocuments,
  since
}: NewFilingModalProps) {
  const router = useRouter();

  const handleViewCaseTracking = () => {
    onClose();
    // Navigate to case tracking tab
    router.push('/?tab=cases');
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Recently';
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title=""
      size="lg"
      showCloseButton={true}
      closeOnOverlayClick={false}
    >
      {/* Custom Header with Icon */}
      <div className="bg-gradient-to-r from-teal-600 to-teal-700 px-6 py-5">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white/20 rounded-full">
            <Bell className="w-8 h-8 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">
              New Court Filings Detected
            </h2>
            <p className="text-teal-100 text-sm mt-1">
              {totalDocuments} new document{totalDocuments !== 1 ? 's' : ''} in {filings.length} case{filings.length !== 1 ? 's' : ''} since your last login
            </p>
          </div>
        </div>
      </div>

      <ModalBody>
        <div className="space-y-4 max-h-[400px] overflow-y-auto">
          {filings.map((filing) => (
            <div
              key={filing.docket_id}
              className="border-2 border-slate-200 dark:border-slate-600 rounded-lg p-4 hover:border-teal-400 transition-colors"
            >
              {/* Case Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Scale className="w-4 h-4 text-teal-600 flex-shrink-0" />
                    <h3 className="font-semibold text-slate-900 dark:text-slate-100 truncate">
                      {filing.case_name}
                    </h3>
                  </div>
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    {filing.court}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-teal-100 dark:bg-teal-900/50 text-teal-800 dark:text-teal-200">
                    {filing.document_count} new
                  </span>
                </div>
              </div>

              {/* Document List (show first 3) */}
              {filing.new_documents && filing.new_documents.length > 0 && (
                <div className="mt-3 space-y-2">
                  {filing.new_documents.slice(0, 3).map((doc, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300 bg-slate-50 dark:bg-slate-700 rounded px-3 py-2"
                    >
                      <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <span className="flex-1 truncate">
                        {doc.entry_number && `#${doc.entry_number} - `}
                        {doc.description || 'Document filed'}
                      </span>
                      {doc.date_filed && (
                        <span className="text-xs text-slate-400 flex-shrink-0">
                          {formatDate(doc.date_filed)}
                        </span>
                      )}
                    </div>
                  ))}

                </div>
              )}

              {/* Latest notification time */}
              {filing.latest_notification && (
                <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
                  <Calendar className="w-3 h-3" />
                  <span>Latest filing: {formatDate(filing.latest_notification)}</span>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Info about since date */}
        {since && (
          <p className="mt-4 text-xs text-slate-500 dark:text-slate-400 text-center">
            Showing filings since {formatDate(since)}
          </p>
        )}
      </ModalBody>

      <ModalFooter>
        <Button variant="outline" onClick={onClose}>
          Dismiss
        </Button>
        <Button onClick={handleViewCaseTracking} className="gap-2">
          <ExternalLink className="w-4 h-4" />
          View Case Tracking
        </Button>
      </ModalFooter>
    </Modal>
  );
}

export default NewFilingModal;
