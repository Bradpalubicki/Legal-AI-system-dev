'use client';

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  FileText,
  Calendar,
  Building2,
  Users,
  ExternalLink,
  Download,
  Share2,
  Scale,
  AlertTriangle,
  Clock,
  Hash
} from 'lucide-react';
import { toast } from 'sonner';

// Document type icons mapping
const DOCUMENT_TYPE_ICONS: Record<string, typeof FileText> = {
  'complaint': Scale,
  'petition': FileText,
  'motion': FileText,
  'order': FileText,
  'judgment': Scale,
  'notice': AlertTriangle,
  'answer': FileText,
  'brief': FileText,
  'default': FileText
};

// Document type colors mapping
const DOCUMENT_TYPE_COLORS: Record<string, string> = {
  'complaint': 'bg-red-100 text-red-800 border-red-200',
  'petition': 'bg-blue-100 text-blue-800 border-blue-200',
  'motion': 'bg-purple-100 text-purple-800 border-purple-200',
  'order': 'bg-green-100 text-green-800 border-green-200',
  'judgment': 'bg-amber-100 text-amber-800 border-amber-200',
  'notice': 'bg-orange-100 text-orange-800 border-orange-200',
  'answer': 'bg-teal-100 text-teal-800 border-teal-200',
  'brief': 'bg-indigo-100 text-indigo-800 border-indigo-200',
  'default': 'bg-gray-100 text-gray-800 border-gray-200'
};

export interface DocumentHeaderProps {
  /** Case number (e.g., "2024-bk-12345") */
  caseNumber?: string;
  /** Court name or code */
  court?: string;
  /** Document type (e.g., "Complaint", "Motion", "Order") */
  documentType?: string;
  /** Entry/document number in docket */
  documentNumber?: number | string;
  /** Filing date */
  filingDate?: string | Date;
  /** Brief description of the document */
  description?: string;
  /** List of parties involved */
  parties?: Array<string | { name: string; role?: string }>;
  /** External URL to PACER/CourtListener source */
  sourceUrl?: string;
  /** Source of the document (e.g., "CourtListener", "PACER") */
  source?: string;
  /** File path for download */
  filePath?: string;
  /** Whether there are urgent deadlines */
  hasUrgentDeadline?: boolean;
  /** Next deadline date */
  nextDeadline?: string | Date;
  /** Callback when download is requested */
  onDownload?: () => void;
  /** Callback when share is requested */
  onShare?: () => void;
  /** Additional className for custom styling */
  className?: string;
}

/**
 * Comprehensive document header component that displays all relevant
 * PACER/court document metadata in a clean, organized layout.
 */
export function DocumentHeader({
  caseNumber,
  court,
  documentType,
  documentNumber,
  filingDate,
  description,
  parties,
  sourceUrl,
  source,
  filePath,
  hasUrgentDeadline,
  nextDeadline,
  onDownload,
  onShare,
  className
}: DocumentHeaderProps) {
  // Format filing date
  const formattedDate = filingDate
    ? new Date(filingDate).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    : null;

  // Format next deadline
  const formattedDeadline = nextDeadline
    ? new Date(nextDeadline).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    : null;

  // Get document type icon and color
  const docTypeLower = documentType?.toLowerCase() || 'default';
  const typeCategory = Object.keys(DOCUMENT_TYPE_ICONS).find(key =>
    docTypeLower.includes(key)
  ) || 'default';
  const TypeIcon = DOCUMENT_TYPE_ICONS[typeCategory];
  const typeColor = DOCUMENT_TYPE_COLORS[typeCategory];

  // Format parties for display (show first 3)
  const displayParties = parties?.slice(0, 3).map(party => {
    if (typeof party === 'string') return party;
    return party.role ? `${party.name} (${party.role})` : party.name;
  }) || [];
  const remainingParties = (parties?.length || 0) - 3;

  // Handle share
  const handleShare = () => {
    if (onShare) {
      onShare();
    } else {
      // Default share behavior - copy link to clipboard
      const shareText = `${documentType || 'Document'} - Case ${caseNumber || 'Unknown'}`;
      navigator.clipboard.writeText(shareText);
      toast.success('Document info copied to clipboard');
    }
  };

  return (
    <Card className={`bg-gradient-to-r from-slate-50 to-blue-50 dark:from-slate-800 dark:to-slate-700 border-l-4 border-l-blue-500 ${className || ''}`}>
      <CardContent className="p-4 md:p-6">
        {/* Top Row: Case Number and Document Type Badge */}
        <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
          <div className="flex-1 min-w-0">
            {/* Case Number - Prominent */}
            {caseNumber && (
              <div className="flex items-center gap-2 mb-2">
                <Hash className="h-5 w-5 text-blue-600 flex-shrink-0" />
                <h2 className="text-xl md:text-2xl font-bold text-gray-900 dark:text-gray-100 truncate">
                  {caseNumber}
                </h2>
              </div>
            )}

            {/* Court */}
            {court && (
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
                <Building2 className="h-4 w-4 flex-shrink-0" />
                <span className="text-sm font-medium">{court}</span>
              </div>
            )}
          </div>

          {/* Document Type Badge */}
          {documentType && (
            <Badge className={`flex items-center gap-1.5 px-3 py-1.5 text-sm font-semibold ${typeColor}`}>
              <TypeIcon className="h-4 w-4" />
              {documentType}
            </Badge>
          )}
        </div>

        {/* Middle Row: Document Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {/* Document Number */}
          {documentNumber && (
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500 uppercase font-semibold">Doc #</p>
                <p className="font-medium text-gray-900 dark:text-gray-100">{documentNumber}</p>
              </div>
            </div>
          )}

          {/* Filing Date */}
          {formattedDate && (
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500 uppercase font-semibold">Filed</p>
                <p className="font-medium text-gray-900 dark:text-gray-100">{formattedDate}</p>
              </div>
            </div>
          )}

          {/* Next Deadline (if urgent) */}
          {hasUrgentDeadline && formattedDeadline && (
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-red-500" />
              <div>
                <p className="text-xs text-red-500 uppercase font-semibold flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  Next Deadline
                </p>
                <p className="font-medium text-red-600">{formattedDeadline}</p>
              </div>
            </div>
          )}

          {/* Source Badge */}
          {source && (
            <div className="flex items-center gap-2">
              <ExternalLink className="h-4 w-4 text-gray-500" />
              <div>
                <p className="text-xs text-gray-500 uppercase font-semibold">Source</p>
                <p className="font-medium text-gray-900 dark:text-gray-100">{source}</p>
              </div>
            </div>
          )}
        </div>

        {/* Description */}
        {description && (
          <div className="mb-4 p-3 bg-white/50 dark:bg-slate-600/50 rounded-lg border border-gray-200 dark:border-gray-600">
            <p className="text-gray-800 dark:text-gray-200">{description}</p>
          </div>
        )}

        {/* Parties Section */}
        {displayParties.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              <Users className="h-4 w-4 text-gray-500" />
              <span className="text-xs text-gray-500 uppercase font-semibold">Parties</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {displayParties.map((party, index) => (
                <Badge
                  key={index}
                  variant="outline"
                  className="bg-white dark:bg-slate-600 text-gray-700 dark:text-gray-200"
                >
                  {party}
                </Badge>
              ))}
              {remainingParties > 0 && (
                <Badge variant="outline" className="bg-gray-100 dark:bg-slate-500 text-gray-600 dark:text-gray-300">
                  +{remainingParties} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Bottom Row: Actions */}
        <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-gray-200 dark:border-gray-600">
          {/* Source Link */}
          {sourceUrl && (
            <a
              href={sourceUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
            >
              <ExternalLink className="h-4 w-4" />
              View on {source || 'Source'}
            </a>
          )}

          {/* Spacer */}
          <div className="flex-1" />

          {/* Download Button */}
          {(onDownload || filePath) && (
            <Button
              variant="outline"
              size="sm"
              onClick={onDownload}
              className="flex items-center gap-1.5"
            >
              <Download className="h-4 w-4" />
              Download
            </Button>
          )}

          {/* Share Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleShare}
            className="flex items-center gap-1.5"
          >
            <Share2 className="h-4 w-4" />
            Share
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Compact version of DocumentHeader for list views
 */
export function DocumentHeaderCompact({
  caseNumber,
  court,
  documentType,
  documentNumber,
  filingDate,
  sourceUrl,
  source,
  className
}: Omit<DocumentHeaderProps, 'parties' | 'description' | 'onDownload' | 'onShare'>) {
  const formattedDate = filingDate
    ? new Date(filingDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    : null;

  const docTypeLower = documentType?.toLowerCase() || 'default';
  const typeCategory = Object.keys(DOCUMENT_TYPE_ICONS).find(key =>
    docTypeLower.includes(key)
  ) || 'default';
  const TypeIcon = DOCUMENT_TYPE_ICONS[typeCategory];
  const typeColor = DOCUMENT_TYPE_COLORS[typeCategory];

  return (
    <div className={`flex items-center gap-3 p-3 bg-gray-50 dark:bg-slate-700 rounded-lg border border-gray-200 dark:border-slate-600 ${className || ''}`}>
      {/* Document Type Icon */}
      <div className={`p-2 rounded-lg ${typeColor}`}>
        <TypeIcon className="h-5 w-5" />
      </div>

      {/* Main Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          {caseNumber && (
            <span className="font-semibold text-gray-900 dark:text-gray-100 truncate">
              {caseNumber}
            </span>
          )}
          {documentNumber && (
            <Badge variant="outline" className="text-xs">
              Doc #{documentNumber}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
          {court && <span>{court}</span>}
          {court && formattedDate && <span>•</span>}
          {formattedDate && <span>{formattedDate}</span>}
        </div>
      </div>

      {/* Document Type Badge */}
      {documentType && (
        <Badge className={`hidden sm:flex ${typeColor}`}>
          {documentType}
        </Badge>
      )}

      {/* Source Link */}
      {sourceUrl && (
        <a
          href={sourceUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:text-blue-800 dark:text-blue-400"
        >
          <ExternalLink className="h-4 w-4" />
        </a>
      )}
    </div>
  );
}

export default DocumentHeader;
