'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  MapPin,
  ExternalLink,
  Eye,
  EyeOff,
  Search,
  Target,
  BookOpen,
  AlertTriangle,
  Info,
  Maximize2,
  X
} from 'lucide-react';

interface SourceLocation {
  page: number;
  paragraph?: number;
  line?: number;
  startChar?: number;
  endChar?: number;
  context: string;
  confidence: number;
}

interface SourceHighlighterProps {
  sourceLocation: SourceLocation;
  extractedText: string;
  documentType: 'pdf' | 'docx' | 'txt';
  onNavigate?: (location: SourceLocation) => void;
  className?: string;
}

const SourceHighlighter: React.FC<SourceHighlighterProps> = ({
  sourceLocation,
  extractedText,
  documentType,
  onNavigate,
  className = ''
}) => {
  const [showContext, setShowContext] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [contextWindow, setContextWindow] = useState(100);
  const contextRef = useRef<HTMLDivElement>(null);

  const getLocationDescription = () => {
    const parts = [];
    parts.push(`Page ${sourceLocation.page}`);
    
    if (sourceLocation.paragraph) {
      parts.push(`¶${sourceLocation.paragraph}`);
    }
    
    if (sourceLocation.line) {
      parts.push(`Line ${sourceLocation.line}`);
    }

    if (sourceLocation.startChar && sourceLocation.endChar) {
      parts.push(`Chars ${sourceLocation.startChar}-${sourceLocation.endChar}`);
    }

    return parts.join(', ');
  };

  const getHighlightedContext = () => {
    const { context } = sourceLocation;
    const lowerExtracted = extractedText.toLowerCase();
    const lowerContext = context.toLowerCase();
    
    const matchIndex = lowerContext.indexOf(lowerExtracted);
    
    if (matchIndex === -1) {
      return {
        before: context,
        match: '',
        after: ''
      };
    }

    const startIndex = Math.max(0, matchIndex - contextWindow);
    const endIndex = Math.min(context.length, matchIndex + extractedText.length + contextWindow);

    return {
      before: context.substring(startIndex, matchIndex),
      match: context.substring(matchIndex, matchIndex + extractedText.length),
      after: context.substring(matchIndex + extractedText.length, endIndex),
      truncatedStart: startIndex > 0,
      truncatedEnd: endIndex < context.length
    };
  };

  const handleNavigateToSource = () => {
    if (onNavigate) {
      onNavigate(sourceLocation);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-success-600';
    if (confidence >= 0.6) return 'text-warning-600';
    return 'text-error-600';
  };

  const highlighted = getHighlightedContext();

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Source Location Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <MapPin className="h-4 w-4 text-gray-500" />
          <span className="text-sm font-medium text-gray-700">
            Source: {getLocationDescription()}
          </span>
          <span className={`text-xs font-medium ${getConfidenceColor(sourceLocation.confidence)}`}>
            {(sourceLocation.confidence * 100).toFixed(0)}% match
          </span>
        </div>

        <div className="flex items-center space-x-1">
          <button
            onClick={() => setShowContext(!showContext)}
            className="p-1 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
            title={showContext ? 'Hide context' : 'Show context'}
          >
            {showContext ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
          
          {onNavigate && (
            <button
              onClick={handleNavigateToSource}
              className="p-1 text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded"
              title="Navigate to source in document"
            >
              <Target className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Document Type Indicator */}
      <div className="flex items-center space-x-2 text-xs text-gray-500">
        <BookOpen className="h-3 w-3" />
        <span>Document Type: {documentType.toUpperCase()}</span>
        {documentType === 'pdf' && (
          <span className="text-green-600">(Navigable)</span>
        )}
        {documentType === 'txt' && (
          <span className="text-amber-600">(Text-based location)</span>
        )}
      </div>

      {/* Context Display */}
      {showContext && (
        <div className="relative">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-sm font-medium text-gray-900">Document Context</h5>
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1 text-xs">
                  <span className="text-gray-500">Context Window:</span>
                  <select
                    value={contextWindow}
                    onChange={(e) => setContextWindow(Number(e.target.value))}
                    className="border border-gray-300 rounded px-1 py-0.5 text-xs"
                  >
                    <option value={50}>50 chars</option>
                    <option value={100}>100 chars</option>
                    <option value={200}>200 chars</option>
                    <option value={500}>500 chars</option>
                  </select>
                </div>
                
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="p-1 text-gray-500 hover:text-gray-700"
                  title={isExpanded ? 'Collapse' : 'Expand'}
                >
                  {isExpanded ? <X className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
                </button>
              </div>
            </div>

            <div 
              ref={contextRef}
              className={`text-sm leading-relaxed font-mono ${
                isExpanded ? 'max-h-96 overflow-y-auto' : 'max-h-32 overflow-y-auto'
              }`}
            >
              <div className="whitespace-pre-wrap">
                {highlighted.truncatedStart && (
                  <span className="text-gray-400">...</span>
                )}
                <span className="text-gray-600">
                  {highlighted.before}
                </span>
                <span className="bg-yellow-200 text-gray-900 font-semibold px-1 rounded">
                  {highlighted.match}
                </span>
                <span className="text-gray-600">
                  {highlighted.after}
                </span>
                {highlighted.truncatedEnd && (
                  <span className="text-gray-400">...</span>
                )}
              </div>
            </div>

            {/* Match Quality Indicator */}
            <div className="mt-2 flex items-center space-x-4 text-xs">
              <div className="flex items-center space-x-1">
                <span className="text-gray-500">Match Quality:</span>
                <span className={`font-medium ${getConfidenceColor(sourceLocation.confidence)}`}>
                  {sourceLocation.confidence >= 0.9 ? 'Exact' :
                   sourceLocation.confidence >= 0.8 ? 'High' :
                   sourceLocation.confidence >= 0.6 ? 'Good' : 'Partial'}
                </span>
              </div>
              
              {sourceLocation.confidence < 0.8 && (
                <div className="flex items-center space-x-1 text-amber-600">
                  <AlertTriangle className="h-3 w-3" />
                  <span>Verify match accuracy</span>
                </div>
              )}
            </div>
          </div>

          {/* Verification Notice */}
          <div className="mt-2 bg-blue-50 border border-blue-200 rounded p-2">
            <div className="flex items-start space-x-2">
              <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-blue-800">
                <p className="font-medium mb-1">Source Verification Required</p>
                <p>
                  Always verify extracted text against the original document context. 
                  AI may misinterpret formatting, tables, or complex layouts.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center space-x-3">
          <button
            className="text-primary-600 hover:text-primary-700 inline-flex items-center space-x-1"
            onClick={handleNavigateToSource}
            title="Jump to source location"
          >
            <ExternalLink className="h-3 w-3" />
            <span>View in Document</span>
          </button>
          
          <button
            className="text-gray-600 hover:text-gray-700 inline-flex items-center space-x-1"
            onClick={() => navigator.clipboard.writeText(extractedText)}
            title="Copy extracted text"
          >
            <span>Copy Text</span>
          </button>
        </div>

        <div className="text-gray-500">
          Extracted: {extractedText.length} chars
        </div>
      </div>
    </div>
  );
};

export default SourceHighlighter;