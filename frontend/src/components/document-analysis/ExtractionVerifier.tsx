'use client';

import React, { useState } from 'react';
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Scale,
  Brain,
  Eye,
  Edit,
  Save,
  Undo,
  Info,
  Download,
  FileText,
  Clock
} from 'lucide-react';

interface AnalysisResults {
  summary: {
    content: string;
    confidence: number;
    keyPoints: string[];
  };
  parties: {
    identified: Array<{
      name: string;
      role: string;
      confidence: number;
      sourceLocation: string;
    }>;
    confidence: number;
  };
  dates: {
    extracted: Array<{
      date: string;
      description: string;
      confidence: number;
      sourceLocation: string;
      type: 'deadline' | 'event' | 'reference';
    }>;
    confidence: number;
  };
  citations: {
    found: Array<{
      citation: string;
      type: 'case' | 'statute' | 'regulation';
      confidence: number;
      sourceLocation: string;
      verified: boolean;
    }>;
    confidence: number;
  };
}

interface ExtractionVerifierProps {
  analysisResults: AnalysisResults;
  documentId: string;
  onVerificationComplete: (verificationData: any) => void;
  className?: string;
}

interface VerificationState {
  summary: 'pending' | 'approved' | 'needs_correction' | 'corrected';
  parties: Record<number, 'pending' | 'approved' | 'needs_correction' | 'corrected'>;
  dates: Record<number, 'pending' | 'approved' | 'needs_correction' | 'corrected'>;
  citations: Record<number, 'pending' | 'approved' | 'needs_correction' | 'corrected'>;
  overallStatus: 'in_review' | 'approved' | 'requires_changes' | 'completed';
}

const ExtractionVerifier: React.FC<ExtractionVerifierProps> = ({
  analysisResults,
  documentId,
  onVerificationComplete,
  className = ''
}) => {
  const [verificationState, setVerificationState] = useState<VerificationState>({
    summary: 'pending',
    parties: {},
    dates: {},
    citations: {},
    overallStatus: 'in_review'
  });

  const [corrections, setCorrections] = useState<Record<string, any>>({});
  const [showCorrectionForm, setShowCorrectionForm] = useState<string | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');

  const updateVerificationState = (
    section: keyof Omit<VerificationState, 'overallStatus'>,
    index: number | 'all',
    status: 'approved' | 'needs_correction' | 'corrected'
  ) => {
    setVerificationState(prev => {
      const newState = { ...prev };
      
      if (section === 'summary') {
        newState.summary = status;
      } else if (index === 'all') {
        // Handle bulk updates for sections with arrays
        const sectionData = analysisResults[section as keyof AnalysisResults];
        if ('identified' in sectionData) {
          // Parties
          sectionData.identified.forEach((_, i) => {
            newState[section][i] = status;
          });
        } else if ('extracted' in sectionData) {
          // Dates
          sectionData.extracted.forEach((_, i) => {
            newState[section][i] = status;
          });
        } else if ('found' in sectionData) {
          // Citations
          sectionData.found.forEach((_, i) => {
            newState[section][i] = status;
          });
        }
      } else {
        newState[section][index as number] = status;
      }

      // Update overall status
      newState.overallStatus = calculateOverallStatus(newState);
      
      return newState;
    });
  };

  const calculateOverallStatus = (state: VerificationState): VerificationState['overallStatus'] => {
    const allSections = [
      state.summary,
      ...Object.values(state.parties),
      ...Object.values(state.dates),
      ...Object.values(state.citations)
    ];

    if (allSections.every(status => status === 'approved' || status === 'corrected')) {
      return 'completed';
    } else if (allSections.some(status => status === 'needs_correction')) {
      return 'requires_changes';
    } else if (allSections.some(status => status === 'approved' || status === 'corrected')) {
      return 'in_review';
    } else {
      return 'in_review';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-success-600" />;
      case 'needs_correction':
        return <XCircle className="h-4 w-4 text-error-600" />;
      case 'corrected':
        return <Edit className="h-4 w-4 text-blue-600" />;
      case 'pending':
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-success-100 text-success-800';
      case 'needs_correction':
        return 'bg-error-100 text-error-800';
      case 'corrected':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConfidenceThreshold = (confidence: number) => {
    if (confidence >= 0.8) return { color: 'text-success-600', label: 'High' };
    if (confidence >= 0.6) return { color: 'text-warning-600', label: 'Medium' };
    return { color: 'text-error-600', label: 'Low' };
  };

  const handleExportVerification = () => {
    const verificationReport = {
      documentId,
      verificationTimestamp: new Date().toISOString(),
      verificationState,
      corrections,
      reviewNotes,
      analysisResults,
      verifiedBy: 'Current Attorney' // Would come from auth
    };
    
    console.log('Exporting verification report:', verificationReport);
    onVerificationComplete(verificationReport);
  };

  const getProgressStats = () => {
    const totalItems = 1 + // summary
      analysisResults.parties.identified.length +
      analysisResults.dates.extracted.length +
      analysisResults.citations.found.length;
    
    const verifiedItems = [
      verificationState.summary,
      ...Object.values(verificationState.parties),
      ...Object.values(verificationState.dates),
      ...Object.values(verificationState.citations)
    ].filter(status => status === 'approved' || status === 'corrected').length;

    return { totalItems, verifiedItems };
  };

  const { totalItems, verifiedItems } = getProgressStats();

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Attorney Verification Interface</h2>
          <p className="text-sm text-gray-600">Review and verify all AI-extracted information</p>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-600">
            Progress: {verifiedItems}/{totalItems} verified
          </div>
          <div className="w-24 bg-gray-200 rounded-full h-2">
            <div 
              className="bg-primary-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${(verifiedItems / totalItems) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Professional Responsibility Notice */}
      <div className="mb-6 bg-legal-50 border border-legal-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Scale className="h-5 w-5 text-legal-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-legal-900 mb-1">Professional Review Responsibility</h3>
            <p className="text-sm text-legal-700">
              As the reviewing attorney, you are professionally responsible for the accuracy of all 
              verified information. Independent verification against source documents is required 
              before approving any AI extractions for use in legal proceedings or client advice.
            </p>
          </div>
        </div>
      </div>

      {/* Overall Status */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-md font-semibold text-gray-900">Overall Verification Status</h3>
            <p className="text-sm text-gray-600">Document ID: {documentId}</p>
          </div>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(verificationState.overallStatus)}`}>
            {getStatusIcon(verificationState.overallStatus)}
            <span className="ml-2 capitalize">{verificationState.overallStatus.replace('_', ' ')}</span>
          </span>
        </div>
      </div>

      {/* Verification Sections */}
      <div className="space-y-6">
        {/* Summary Verification */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-gray-600" />
              <h3 className="text-md font-semibold text-gray-900">Document Summary</h3>
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                getConfidenceThreshold(analysisResults.summary.confidence).color
              }`}>
                {(analysisResults.summary.confidence * 100).toFixed(0)}% confidence
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(verificationState.summary)}`}>
                {getStatusIcon(verificationState.summary)}
                <span className="ml-1 capitalize">{verificationState.summary.replace('_', ' ')}</span>
              </span>
              
              <div className="flex space-x-1">
                <button
                  onClick={() => updateVerificationState('summary', 'all', 'approved')}
                  className="p-1 text-success-600 hover:bg-success-100 rounded"
                  title="Approve summary"
                >
                  <CheckCircle className="h-4 w-4" />
                </button>
                <button
                  onClick={() => updateVerificationState('summary', 'all', 'needs_correction')}
                  className="p-1 text-error-600 hover:bg-error-100 rounded"
                  title="Mark for correction"
                >
                  <XCircle className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setShowCorrectionForm('summary')}
                  className="p-1 text-blue-600 hover:bg-blue-100 rounded"
                  title="Edit summary"
                >
                  <Edit className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded p-3 mb-3">
            <p className="text-sm text-gray-700">{analysisResults.summary.content}</p>
          </div>

          {verificationState.summary === 'needs_correction' && (
            <div className="bg-amber-50 border border-amber-200 rounded p-3">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <p className="text-sm text-amber-800">
                  This summary requires correction. Please review against the source document 
                  and make necessary adjustments before approval.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Parties Verification */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Eye className="h-5 w-5 text-gray-600" />
              <h3 className="text-md font-semibold text-gray-900">Identified Parties</h3>
              <span className="text-sm text-gray-500">({analysisResults.parties.identified.length} found)</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => updateVerificationState('parties', 'all', 'approved')}
                className="text-xs px-2 py-1 bg-success-100 text-success-800 rounded hover:bg-success-200"
              >
                Approve All
              </button>
              <button
                onClick={() => updateVerificationState('parties', 'all', 'needs_correction')}
                className="text-xs px-2 py-1 bg-error-100 text-error-800 rounded hover:bg-error-200"
              >
                Flag All
              </button>
            </div>
          </div>

          <div className="space-y-2">
            {analysisResults.parties.identified.map((party, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">{party.name}</span>
                    <span className="text-sm text-gray-600">({party.role})</span>
                    <span className={`text-xs px-2 py-1 rounded ${getConfidenceThreshold(party.confidence).color}`}>
                      {(party.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">{party.sourceLocation}</div>
                </div>
                
                <div className="flex items-center space-x-1">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs ${getStatusColor(verificationState.parties[index] || 'pending')}`}>
                    {getStatusIcon(verificationState.parties[index] || 'pending')}
                  </span>
                  
                  <div className="flex space-x-1">
                    <button
                      onClick={() => updateVerificationState('parties', index, 'approved')}
                      className="p-1 text-success-600 hover:bg-success-100 rounded"
                    >
                      <CheckCircle className="h-3 w-3" />
                    </button>
                    <button
                      onClick={() => updateVerificationState('parties', index, 'needs_correction')}
                      className="p-1 text-error-600 hover:bg-error-100 rounded"
                    >
                      <XCircle className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Dates Verification */}
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-gray-600" />
              <h3 className="text-md font-semibold text-gray-900">Extracted Dates</h3>
              <span className="text-sm text-gray-500">({analysisResults.dates.extracted.length} found)</span>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => updateVerificationState('dates', 'all', 'approved')}
                className="text-xs px-2 py-1 bg-success-100 text-success-800 rounded hover:bg-success-200"
              >
                Approve All
              </button>
              <button
                onClick={() => updateVerificationState('dates', 'all', 'needs_correction')}
                className="text-xs px-2 py-1 bg-error-100 text-error-800 rounded hover:bg-error-200"
              >
                Flag All
              </button>
            </div>
          </div>

          <div className="space-y-2">
            {analysisResults.dates.extracted.map((date, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">
                      {new Date(date.date).toLocaleDateString()}
                    </span>
                    <span className="text-sm text-gray-600">{date.description}</span>
                    <span className={`text-xs px-2 py-1 rounded ${
                      date.type === 'deadline' ? 'bg-error-100 text-error-800' : 'bg-blue-100 text-blue-800'
                    }`}>
                      {date.type}
                    </span>
                  </div>
                  <div className="text-xs text-gray-500">{date.sourceLocation}</div>
                </div>
                
                <div className="flex items-center space-x-1">
                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs ${getStatusColor(verificationState.dates[index] || 'pending')}`}>
                    {getStatusIcon(verificationState.dates[index] || 'pending')}
                  </span>
                  
                  <div className="flex space-x-1">
                    <button
                      onClick={() => updateVerificationState('dates', index, 'approved')}
                      className="p-1 text-success-600 hover:bg-success-100 rounded"
                    >
                      <CheckCircle className="h-3 w-3" />
                    </button>
                    <button
                      onClick={() => updateVerificationState('dates', index, 'needs_correction')}
                      className="p-1 text-error-600 hover:bg-error-100 rounded"
                    >
                      <XCircle className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Review Notes */}
      <div className="mt-6 border border-gray-200 rounded-lg p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Attorney Review Notes
        </label>
        <textarea
          value={reviewNotes}
          onChange={(e) => setReviewNotes(e.target.value)}
          placeholder="Document any specific findings, concerns, or corrections made during review..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
          rows={4}
        />
      </div>

      {/* Actions */}
      <div className="mt-6 flex items-center justify-between">
        <div className="text-sm text-gray-600">
          Last saved: {new Date().toLocaleString()}
        </div>
        
        <div className="flex items-center space-x-3">
          <button className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
            <Save className="h-4 w-4 mr-2" />
            Save Progress
          </button>
          
          <button
            onClick={handleExportVerification}
            disabled={verificationState.overallStatus !== 'completed'}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4 mr-2" />
            Export Verification Report
          </button>
        </div>
      </div>

      {/* Completion Notice */}
      {verificationState.overallStatus === 'completed' && (
        <div className="mt-4 bg-success-50 border border-success-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <CheckCircle className="h-5 w-5 text-success-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-success-900 mb-1">Verification Complete</h3>
              <p className="text-sm text-success-800">
                All extractions have been reviewed and verified. The document analysis is ready for use 
                in legal proceedings, subject to any noted corrections or limitations.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExtractionVerifier;