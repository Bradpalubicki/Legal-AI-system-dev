'use client';

import React, { useState } from 'react';
import {
  FileText,
  Info,
  Clock,
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff,
  Copy,
  Volume2,
  VolumeX
} from 'lucide-react';

interface DocumentSummaryCardProps {
  summary: string;
  documentType: string;
  wordCount?: number;
  readingTime?: number;
  confidenceScore?: number;
  keyPoints?: string[];
  onSpeakSummary?: () => void;
}

const DocumentSummaryCard: React.FC<DocumentSummaryCardProps> = ({
  summary,
  documentType,
  wordCount,
  readingTime,
  confidenceScore,
  keyPoints = [],
  onSpeakSummary
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [showFullText, setShowFullText] = useState(false);

  const handleCopySummary = async () => {
    try {
      await navigator.clipboard.writeText(summary);
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to copy summary:', error);
    }
  };

  const handleSpeak = () => {
    if ('speechSynthesis' in window) {
      if (isSpeaking) {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
      } else {
        const utterance = new SpeechSynthesisUtterance(summary);
        utterance.rate = 0.8;
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);
        window.speechSynthesis.speak(utterance);
        setIsSpeaking(true);
      }
    } else if (onSpeakSummary) {
      onSpeakSummary();
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const estimatedReadingTime = readingTime || Math.ceil(summary.split(' ').length / 200);
  const summaryWordCount = wordCount || summary.split(' ').length;

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-white border-b border-blue-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                Document Summary
              </h2>
              <p className="text-sm text-gray-600">
                {documentType} • {summaryWordCount} words • ~{estimatedReadingTime} min read
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {confidenceScore && (
              <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getConfidenceColor(confidenceScore)}`}>
                <CheckCircle className="h-3 w-3 mr-1" />
                {Math.round(confidenceScore * 100)}% confidence
              </div>
            )}

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 text-gray-400 hover:text-gray-600"
              title={isExpanded ? "Collapse" : "Expand"}
            >
              {isExpanded ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-6">
          {/* Summary Text */}
          <div className="mb-6">
            <div className="prose prose-blue max-w-none">
              <div className="relative">
                <p className="text-gray-800 leading-relaxed text-base">
                  {showFullText ? summary : `${summary.substring(0, 300)}${summary.length > 300 ? '...' : ''}`}
                </p>

                {summary.length > 300 && (
                  <button
                    onClick={() => setShowFullText(!showFullText)}
                    className="mt-2 text-sm text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {showFullText ? 'Show less' : 'Read full summary'}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Key Points */}
          {keyPoints.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center">
                <Info className="h-4 w-4 mr-2 text-blue-600" />
                Key Points
              </h3>
              <ul className="space-y-2">
                {keyPoints.map((point, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-4 border-t border-blue-200">
            <div className="flex items-center space-x-3">
              <button
                onClick={handleSpeak}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-blue-600 bg-blue-100 rounded-md hover:bg-blue-200 transition-colors"
                disabled={!('speechSynthesis' in window) && !onSpeakSummary}
              >
                {isSpeaking ? (
                  <>
                    <VolumeX className="h-4 w-4 mr-2" />
                    Stop Reading
                  </>
                ) : (
                  <>
                    <Volume2 className="h-4 w-4 mr-2" />
                    Read Aloud
                  </>
                )}
              </button>

              <button
                onClick={handleCopySummary}
                className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                <Copy className="h-4 w-4 mr-2" />
                Copy Summary
              </button>
            </div>

            <div className="flex items-center space-x-2 text-xs text-gray-500">
              <Clock className="h-3 w-3" />
              <span>Generated by AI • For educational purposes only</span>
            </div>
          </div>

          {/* Warning Notice */}
          <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
            <div className="flex items-start space-x-2">
              <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="text-amber-800 font-medium mb-1">Important Notice</p>
                <p className="text-amber-700">
                  This summary is AI-generated and for educational purposes only.
                  It may not capture all nuances of the legal document.
                  Always consult with a qualified attorney for legal advice.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentSummaryCard;