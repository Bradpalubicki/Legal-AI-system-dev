'use client';

import React, { useState } from 'react';
import {
  FileText,
  Info,
  AlertTriangle,
  Scale,
  Brain,
  CheckCircle,
  XCircle,
  HelpCircle
} from 'lucide-react';

interface SummaryData {
  content: string;
  confidence: number;
  keyPoints: string[];
}

interface PlainEnglishSummaryProps {
  summary: SummaryData;
  documentType: string;
  className?: string;
}

const PlainEnglishSummary: React.FC<PlainEnglishSummaryProps> = ({
  summary,
  documentType,
  className = ''
}) => {
  const [isVerified, setIsVerified] = useState<boolean | null>(null);
  const [showTypicalImplications, setShowTypicalImplications] = useState(false);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-success-600 bg-success-100';
    if (confidence >= 0.6) return 'text-warning-600 bg-warning-100';
    return 'text-error-600 bg-error-100';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High Confidence';
    if (confidence >= 0.6) return 'Medium Confidence';
    return 'Low Confidence';
  };

  const getTypicalImplications = (docType: string) => {
    switch (docType.toLowerCase()) {
      case 'contract/agreement':
        return [
          'Review performance obligations and timelines',
          'Identify termination and breach provisions',
          'Examine dispute resolution mechanisms',
          'Verify compliance requirements and penalties',
          'Consider renewal or modification procedures'
        ];
      case 'court filing':
        return [
          'Note response deadlines and procedural requirements',
          'Identify claims, defenses, and factual allegations',
          'Review requested relief and damages',
          'Check jurisdictional and venue provisions',
          'Examine discovery and motion practice implications'
        ];
      case 'legal brief':
        return [
          'Analyze legal arguments and supporting authorities',
          'Evaluate factual assertions and evidence cited',
          'Consider counterarguments and potential weaknesses',
          'Review procedural compliance and formatting',
          'Assess persuasiveness and likelihood of success'
        ];
      default:
        return [
          'Verify accuracy of AI-identified key elements',
          'Consider document context within broader case',
          'Review for privilege and confidentiality issues',
          'Assess relevance to case strategy and objectives',
          'Identify follow-up actions or document needs'
        ];
    }
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* AI Generation Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <Brain className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-blue-900 mb-1">AI-Generated Summary</h4>
            <p className="text-sm text-blue-800">
              This summary was created by AI and requires professional review. It provides general 
              information about document contents but does not constitute legal analysis or advice.
            </p>
          </div>
        </div>
      </div>

      {/* Confidence Score */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Document Summary</h3>
        <div className="flex items-center space-x-3">
          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(summary.confidence)}`}>
            {getConfidenceLabel(summary.confidence)} ({(summary.confidence * 100).toFixed(0)}%)
          </span>
          
          {isVerified === null ? (
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setIsVerified(true)}
                className="p-1 text-success-600 hover:bg-success-100 rounded"
                title="Mark as verified"
              >
                <CheckCircle className="h-4 w-4" />
              </button>
              <button
                onClick={() => setIsVerified(false)}
                className="p-1 text-error-600 hover:bg-error-100 rounded"
                title="Mark as needs correction"
              >
                <XCircle className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
              isVerified 
                ? 'bg-success-100 text-success-800' 
                : 'bg-error-100 text-error-800'
            }`}>
              {isVerified ? 'Verified' : 'Needs Review'}
            </span>
          )}
        </div>
      </div>

      {/* Summary Content */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <p className="text-gray-700 leading-relaxed">{summary.content}</p>
      </div>

      {/* Key Points */}
      <div>
        <h4 className="text-md font-semibold text-gray-900 mb-3">AI-Identified Key Points</h4>
        <div className="space-y-2">
          {summary.keyPoints.map((point, index) => (
            <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-800 rounded-full flex items-center justify-center text-xs font-medium">
                {index + 1}
              </div>
              <p className="text-sm text-gray-700">{point}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Typical Implications */}
      <div className="border border-blue-200 rounded-lg">
        <button
          onClick={() => setShowTypicalImplications(!showTypicalImplications)}
          className="w-full flex items-center justify-between p-3 text-left hover:bg-blue-50 transition-colors"
        >
          <div className="flex items-center space-x-2">
            <HelpCircle className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-semibold text-blue-900">
              Typical Implications for {documentType} Documents
            </span>
          </div>
          <span className="text-blue-600">
            {showTypicalImplications ? '−' : '+'}
          </span>
        </button>
        
        {showTypicalImplications && (
          <div className="border-t border-blue-200 p-3 bg-blue-50">
            <p className="text-sm text-blue-800 mb-3">
              Based on document type, attorneys typically consider these aspects during review:
            </p>
            <ul className="space-y-2">
              {getTypicalImplications(documentType).map((implication, index) => (
                <li key={index} className="flex items-start space-x-2 text-sm text-blue-700">
                  <span className="text-blue-600 mt-1">•</span>
                  <span>{implication}</span>
                </li>
              ))}
            </ul>
            <div className="mt-3 p-2 bg-blue-100 rounded">
              <p className="text-xs text-blue-700">
                <strong>Note:</strong> These are general considerations for this document type and 
                may not apply to your specific document or situation. Professional judgment is required.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Verification Warnings */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-amber-800 mb-2">Summary Verification Requirements</h4>
            <ul className="text-sm text-amber-700 space-y-1">
              <li>• Compare summary against original document for accuracy and completeness</li>
              <li>• Verify that key legal concepts are properly identified and explained</li>
              <li>• Ensure no critical information has been omitted or mischaracterized</li>
              <li>• Check that legal terminology is used appropriately and accurately</li>
              <li>• Confirm summary reflects document's legal significance and implications</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Professional Review Notice */}
      <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-legal-900 mb-1">Professional Review Required</h4>
            <p className="text-sm text-legal-700">
              This AI-generated summary is provided for efficiency only and does not replace 
              professional document analysis. Independent review and verification are required 
              before relying on this information for legal decisions or strategy.
            </p>
          </div>
        </div>
      </div>

      {/* Common Review Actions */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Common Attorney Review Actions</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="space-y-2">
            <h5 className="text-xs font-semibold text-gray-800">Content Verification</h5>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>• Cross-reference with original document</li>
              <li>• Verify legal terminology accuracy</li>
              <li>• Check for omitted critical details</li>
            </ul>
          </div>
          <div className="space-y-2">
            <h5 className="text-xs font-semibold text-gray-800">Strategic Assessment</h5>
            <ul className="text-xs text-gray-600 space-y-1">
              <li>• Evaluate case strategy implications</li>
              <li>• Identify follow-up actions needed</li>
              <li>• Consider discovery or research needs</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PlainEnglishSummary;