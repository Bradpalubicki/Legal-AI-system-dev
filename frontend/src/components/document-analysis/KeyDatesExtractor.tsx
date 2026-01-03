'use client';

import React, { useState } from 'react';
import {
  Calendar,
  Clock,
  AlertTriangle,
  Info,
  Scale,
  CheckCircle,
  XCircle,
  ExternalLink,
  MapPin,
  Brain
} from 'lucide-react';

interface DateData {
  date: string;
  description: string;
  confidence: number;
  sourceLocation: string;
  type: 'deadline' | 'event' | 'reference';
  why_important?: string;
  action_required?: string;
  consequence_if_missed?: string;
}

interface DatesData {
  extracted: DateData[];
  confidence: number;
}

interface KeyDatesExtractorProps {
  dates: DatesData;
  documentName: string;
  className?: string;
}

const KeyDatesExtractor: React.FC<KeyDatesExtractorProps> = ({
  dates,
  documentName,
  className = ''
}) => {
  const [verifiedDates, setVerifiedDates] = useState<Record<string, boolean | null>>({});
  const [showVerificationWarning, setShowVerificationWarning] = useState(true);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-success-600 bg-success-100';
    if (confidence >= 0.6) return 'text-warning-600 bg-warning-100';
    return 'text-error-600 bg-error-100';
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'deadline':
        return 'bg-error-100 text-error-800 border-error-200';
      case 'event':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'reference':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'deadline':
        return <AlertTriangle className="h-4 w-4" />;
      case 'event':
        return <Calendar className="h-4 w-4" />;
      case 'reference':
        return <Info className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const getDaysUntil = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffTime = date.getTime() - now.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays < 0) {
        return `${Math.abs(diffDays)} days ago`;
      } else if (diffDays === 0) {
        return 'Today';
      } else if (diffDays === 1) {
        return 'Tomorrow';
      } else {
        return `${diffDays} days from now`;
      }
    } catch {
      return 'Invalid date';
    }
  };

  const handleDateVerification = (dateIndex: number, verified: boolean | null) => {
    setVerifiedDates(prev => ({
      ...prev,
      [dateIndex]: verified
    }));
  };

  const isUrgent = (dateStr: string, type: string) => {
    if (type !== 'deadline') return false;
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      return diffDays <= 7 && diffDays >= 0;
    } catch {
      return false;
    }
  };

  // Sort dates chronologically
  const sortedDates = [...dates.extracted].sort((a, b) => 
    new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const upcomingDeadlines = sortedDates.filter(d => 
    d.type === 'deadline' && new Date(d.date) > new Date()
  );

  return (
    <div className={`space-y-4 ${className}`}>
      {/* AI Generation Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <Brain className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-blue-900 mb-1">AI-Extracted Dates</h4>
            <p className="text-sm text-blue-800">
              These dates were automatically identified by AI from "{documentName}". 
              Professional verification is required before relying on any date information.
            </p>
          </div>
        </div>
      </div>

      {/* Verification Warning */}
      {showVerificationWarning && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-2">
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <h4 className="text-sm font-semibold text-amber-800 mb-2">Critical Verification Required</h4>
                <ul className="text-sm text-amber-700 space-y-1">
                  <li>• Always verify dates against original document</li>
                  <li>• Check court rules for actual deadline calculation methods</li>
                  <li>• Consider holidays, weekends, and court closures</li>
                  <li>• Confirm jurisdiction-specific timing requirements</li>
                  <li>• Verify service requirements and methods</li>
                </ul>
              </div>
            </div>
            <button
              onClick={() => setShowVerificationWarning(false)}
              className="text-amber-400 hover:text-amber-600"
            >
              <XCircle className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Overall Confidence */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Extracted Dates & Deadlines</h3>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">Overall Confidence:</span>
          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(dates.confidence)}`}>
            {(dates.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Upcoming Deadlines Alert */}
      {upcomingDeadlines.length > 0 && (
        <div className="bg-error-50 border border-error-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <AlertTriangle className="h-5 w-5 text-error-600 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-semibold text-error-900 mb-2">
                Upcoming Deadlines Detected
              </h4>
              <div className="space-y-1">
                {upcomingDeadlines.slice(0, 3).map((date, index) => (
                  <p key={index} className="text-sm text-error-800">
                    <strong>{formatDate(date.date)}</strong> ({getDaysUntil(date.date)}) - {date.description}
                  </p>
                ))}
              </div>
              <p className="text-xs text-error-700 mt-2">
                ⚠️ Verify all deadlines immediately through court records and applicable rules
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Dates List */}
      {sortedDates.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No dates identified in this document</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sortedDates.map((dateData, index) => (
            <div 
              key={index} 
              className={`border rounded-lg p-4 ${
                isUrgent(dateData.date, dateData.type) 
                  ? 'border-error-300 bg-error-50' 
                  : 'border-gray-200 bg-white'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getTypeColor(dateData.type)}`}>
                      {getTypeIcon(dateData.type)}
                      <span className="ml-1 capitalize">{dateData.type}</span>
                    </span>
                    
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(dateData.confidence)}`}>
                      {(dateData.confidence * 100).toFixed(0)}% confidence
                    </span>

                    {isUrgent(dateData.date, dateData.type) && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-error-100 text-error-800">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Urgent
                      </span>
                    )}
                  </div>

                  <div className="mb-2">
                    <div className="text-lg font-semibold text-gray-900">
                      {formatDate(dateData.date)}
                    </div>
                    <div className="text-sm text-gray-600">
                      {getDaysUntil(dateData.date)}
                    </div>
                  </div>

                  <p className="text-sm text-gray-700 mb-2">{dateData.description}</p>

                  {/* WHY / ACTION / RISK Section */}
                  <div className="space-y-2 mb-3">
                    {dateData.why_important && (
                      <div className="flex items-start space-x-2">
                        <span className="inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 flex-shrink-0">
                          WHY
                        </span>
                        <p className="text-sm text-gray-700">{dateData.why_important}</p>
                      </div>
                    )}

                    {dateData.action_required && (
                      <div className="flex items-start space-x-2">
                        <span className="inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800 flex-shrink-0">
                          ACTION
                        </span>
                        <p className="text-sm text-gray-700">{dateData.action_required}</p>
                      </div>
                    )}

                    {dateData.consequence_if_missed && (
                      <div className="flex items-start space-x-2">
                        <span className="inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 flex-shrink-0">
                          RISK
                        </span>
                        <p className="text-sm text-red-700 font-medium">{dateData.consequence_if_missed}</p>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <MapPin className="h-3 w-3" />
                    <span>Found in: {dateData.sourceLocation}</span>
                    <button className="text-primary-600 hover:text-primary-700 inline-flex items-center">
                      <ExternalLink className="h-3 w-3 mr-1" />
                      View Source
                    </button>
                  </div>
                </div>

                {/* Verification Controls */}
                <div className="flex flex-col items-end space-y-2">
                  <div className="text-xs text-gray-500">Verification Status:</div>
                  {verifiedDates[index] === null || verifiedDates[index] === undefined ? (
                    <div className="flex space-x-1">
                      <button
                        onClick={() => handleDateVerification(index, true)}
                        className="p-1 text-success-600 hover:bg-success-100 rounded"
                        title="Verify as accurate"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDateVerification(index, false)}
                        className="p-1 text-error-600 hover:bg-error-100 rounded"
                        title="Mark as incorrect"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                      verifiedDates[index] 
                        ? 'bg-success-100 text-success-800' 
                        : 'bg-error-100 text-error-800'
                    }`}>
                      {verifiedDates[index] ? 'Verified' : 'Incorrect'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Verification Guidelines */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-blue-900 mb-2">Date Verification Best Practices</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
              <div>
                <h5 className="font-semibold mb-1">For Deadlines:</h5>
                <ul className="space-y-1">
                  <li>• Check applicable court rules for calculation methods</li>
                  <li>• Consider service requirements and methods</li>
                  <li>• Account for holidays and court closures</li>
                  <li>• Verify jurisdiction-specific timing rules</li>
                </ul>
              </div>
              <div>
                <h5 className="font-semibold mb-1">For Events:</h5>
                <ul className="space-y-1">
                  <li>• Cross-reference with court calendars</li>
                  <li>• Confirm with opposing counsel if necessary</li>
                  <li>• Check for scheduling conflicts</li>
                  <li>• Verify location and time details</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Court Verification Notice */}
      <div className="bg-legal-50 border border-legal-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-legal-900 mb-1">Verify with Court Records</h4>
            <p className="text-sm text-legal-700">
              <strong>Professional Responsibility:</strong> All dates, especially deadlines, must be independently 
              verified through official court records, applicable rules, and case-specific orders. AI extraction 
              is a starting point for review, not a substitute for proper deadline calculation and verification.
            </p>
            <div className="mt-2 flex items-center space-x-4 text-xs">
              <button className="text-legal-600 hover:text-legal-700 font-medium inline-flex items-center">
                <ExternalLink className="h-3 w-3 mr-1" />
                Court Records Portal
              </button>
              <button className="text-legal-600 hover:text-legal-700 font-medium inline-flex items-center">
                <ExternalLink className="h-3 w-3 mr-1" />
                Local Court Rules
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Extraction Summary</h4>
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-lg font-semibold text-gray-900">
              {dates.extracted.filter(d => d.type === 'deadline').length}
            </div>
            <div className="text-xs text-gray-600">Deadlines Found</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-900">
              {dates.extracted.filter(d => d.type === 'event').length}
            </div>
            <div className="text-xs text-gray-600">Events Found</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-900">
              {Object.values(verifiedDates).filter(v => v === true).length}
            </div>
            <div className="text-xs text-gray-600">Verified</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KeyDatesExtractor;