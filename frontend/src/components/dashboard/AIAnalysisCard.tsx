'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  Brain, 
  AlertTriangle, 
  Info, 
  Eye, 
  TrendingUp,
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink,
  Scale,
  HelpCircle
} from 'lucide-react';
import { formatComplianceDate } from '@/utils/compliance-utils';

interface AISuggestion {
  id: string;
  matterId: string;
  matterTitle: string;
  type: 'research' | 'document_review' | 'strategy' | 'deadline_reminder';
  title: string;
  description: string;
  confidenceScore: number;
  requiresReview: boolean;
  createdAt: string;
}

interface AIAnalysisCardProps {
  suggestion: AISuggestion;
  showReviewWarning?: boolean;
  className?: string;
  onAccept?: (suggestionId: string) => void;
  onDismiss?: (suggestionId: string) => void;
}

const AIAnalysisCard: React.FC<AIAnalysisCardProps> = ({ 
  suggestion,
  showReviewWarning = true,
  className = '',
  onAccept,
  onDismiss
}) => {
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);

  const getTypeIcon = (type: AISuggestion['type']) => {
    switch (type) {
      case 'research':
        return <TrendingUp className="h-4 w-4" />;
      case 'document_review':
        return <Eye className="h-4 w-4" />;
      case 'strategy':
        return <Brain className="h-4 w-4" />;
      case 'deadline_reminder':
        return <Clock className="h-4 w-4" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getTypeColor = (type: AISuggestion['type']) => {
    switch (type) {
      case 'research':
        return 'bg-blue-100 text-blue-800';
      case 'document_review':
        return 'bg-green-100 text-green-800';
      case 'strategy':
        return 'bg-purple-100 text-purple-800';
      case 'deadline_reminder':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-success-600 bg-success-100';
    if (score >= 0.6) return 'text-warning-600 bg-warning-100';
    return 'text-error-600 bg-error-100';
  };

  const getConfidenceLabel = (score: number) => {
    if (score >= 0.8) return 'High Confidence';
    if (score >= 0.6) return 'Medium Confidence';
    return 'Low Confidence';
  };

  const handleAccept = async () => {
    if (onAccept && !isProcessing) {
      setIsProcessing(true);
      try {
        await onAccept(suggestion.id);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleDismiss = async () => {
    if (onDismiss && !isProcessing) {
      setIsProcessing(true);
      try {
        await onDismiss(suggestion.id);
      } finally {
        setIsProcessing(false);
      }
    }
  };

  return (
    <div className={`
      bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-all duration-200
      ${suggestion.requiresReview ? 'border-l-4 border-l-warning-500' : ''}
      ${className}
    `}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start space-x-3">
          <div className={`p-2 rounded-lg ${getTypeColor(suggestion.type)}`}>
            {getTypeIcon(suggestion.type)}
          </div>
          
          <div className="flex-1">
            <h4 className="font-medium text-gray-900 mb-1">
              {suggestion.title}
            </h4>
            <p className="text-sm text-gray-600">
              {suggestion.description}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              For matter: {suggestion.matterTitle}
            </p>
          </div>
        </div>

        {/* Review Required Badge */}
        {showReviewWarning && suggestion.requiresReview && (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-warning-100 text-warning-800 border border-warning-200">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Review Required
          </span>
        )}
      </div>

      {/* AI Confidence Score */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(suggestion.confidenceScore)}`}>
            {getConfidenceLabel(suggestion.confidenceScore)} ({(suggestion.confidenceScore * 100).toFixed(0)}%)
          </span>
          
          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getTypeColor(suggestion.type)}`}>
            {suggestion.type.replace('_', ' ').toUpperCase()}
          </span>
        </div>

        <div className="text-xs text-gray-500">
          {formatComplianceDate(suggestion.createdAt)}
        </div>
      </div>

      {/* AI Disclaimer Section */}
      {showReviewWarning && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-3">
          <div className="flex items-start space-x-2">
            <Brain className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-xs font-semibold text-amber-800 mb-1">
                AI-Generated Suggestion - For Attorney Review Only
              </h5>
              <p className="text-xs text-amber-700">
                This suggestion is generated by AI and requires independent professional review. 
                It does not constitute legal advice and should not be relied upon without attorney analysis.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {onAccept && (
            <button
              onClick={handleAccept}
              disabled={isProcessing}
              className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
            >
              <CheckCircle className="h-3 w-3 mr-1" />
              {isProcessing ? 'Processing...' : 'Review & Consider'}
            </button>
          )}
          
          {onDismiss && (
            <button
              onClick={handleDismiss}
              disabled={isProcessing}
              className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
            >
              <XCircle className="h-3 w-3 mr-1" />
              Dismiss
            </button>
          )}

          <Link
            href={`/dashboard/${suggestion.matterId}`}
            className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            View Matter
            <ExternalLink className="h-3 w-3 ml-1" />
          </Link>
        </div>

        {/* Disclaimer Toggle */}
        <button
          onClick={() => setShowDisclaimer(!showDisclaimer)}
          className="inline-flex items-center text-xs text-gray-500 hover:text-gray-700"
        >
          <HelpCircle className="h-3 w-3 mr-1" />
          AI Disclaimer
        </button>
      </div>

      {/* Expanded AI Disclaimer */}
      {showDisclaimer && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
            <div className="flex items-start space-x-2">
              <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
              <div>
                <h6 className="text-xs font-semibold text-legal-900 mb-2">
                  Professional Responsibility Notice
                </h6>
                <ul className="text-xs text-legal-700 space-y-1">
                  <li>• AI suggestions are informational tools, not legal advice</li>
                  <li>• Professional review and independent judgment are required</li>
                  <li>• Verify all information through authoritative sources</li>
                  <li>• Consider client-specific circumstances and applicable law</li>
                  <li>• Maintain confidentiality and privilege protections</li>
                </ul>
                <div className="mt-2 pt-2 border-t border-legal-200">
                  <p className="text-xs text-legal-600">
                    <strong>Why This Matters:</strong> AI tools can enhance efficiency but cannot 
                    replace attorney expertise. Professional responsibility rules require attorneys 
                    to exercise competent representation and independent judgment.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Type-specific Educational Content */}
      {suggestion.type === 'research' && showDisclaimer && (
        <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <h6 className="text-xs font-semibold text-blue-900 mb-1">
                Research Suggestions - Common Response Options
              </h6>
              <p className="text-xs text-blue-800 mb-2">
                When reviewing AI research suggestions, consider these typical approaches:
              </p>
              <ul className="text-xs text-blue-700 space-y-1">
                <li>• Verify case citations and current validity</li>
                <li>• Review jurisdiction-specific variations</li>
                <li>• Consider factual distinguishments</li>
                <li>• Analyze procedural requirements</li>
                <li>• Check for recent developments or appeals</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAnalysisCard;