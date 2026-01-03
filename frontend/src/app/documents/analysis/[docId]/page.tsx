'use client';

import React, { useState } from 'react';
import {
  FileText,
  Brain,
  Scale,
  AlertTriangle,
  Info,
  CheckCircle,
  XCircle,
  Clock,
  Shield,
  Eye,
  Download,
  Share2,
  ArrowLeft,
  Maximize2,
  Minimize2,
  Users,
  MessageSquare
} from 'lucide-react';
import Link from 'next/link';
import PlainEnglishSummary from '@/components/document-analysis/PlainEnglishSummary';
import KeyDatesExtractor from '@/components/document-analysis/KeyDatesExtractor';
import PartyIdentifier from '@/components/document-analysis/PartyIdentifier';
import DeadlineCalculator from '@/components/document-analysis/DeadlineCalculator';
import ExtractionVerifier from '@/components/document-analysis/ExtractionVerifier';
import ComprehensiveAnalysisDisplay from '@/components/document-analysis/ComprehensiveAnalysisDisplay';
import SmartQASystem from '@/components/qa/SmartQASystem';

interface DocumentAnalysisPageProps {
  params: {
    docId: string;
  };
}

interface DocumentData {
  id: string;
  name: string;
  type: string;
  privilegeLevel: 'public' | 'confidential' | 'attorney_client' | 'work_product';
  uploadedBy: string;
  uploadedAt: string;
  size: string;
  pageCount: number;
  analysisStatus: 'pending' | 'processing' | 'completed' | 'review_required' | 'error';
  confidenceScore: number;
}

interface AnalysisResult {
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

const DocumentAnalysisPage: React.FC<DocumentAnalysisPageProps> = ({ params }) => {
  const [viewMode, setViewMode] = useState<'split' | 'analysis' | 'document'>('split');
  const [activeAnalysisTab, setActiveAnalysisTab] = useState<'comprehensive' | 'summary' | 'dates' | 'parties' | 'deadlines' | 'qa'>('comprehensive');
  const [showReviewChecklist, setShowReviewChecklist] = useState(false);
  const [reviewedSections, setReviewedSections] = useState<string[]>([]);

  // Mock data - would come from API
  const document: DocumentData = {
    id: params.docId,
    name: 'Service Agreement - ABC Corp.pdf',
    type: 'Contract/Agreement',
    privilegeLevel: 'attorney_client',
    uploadedBy: 'Sarah Johnson, Esq.',
    uploadedAt: '2024-01-15T10:30:00Z',
    size: '2.3 MB',
    pageCount: 15,
    analysisStatus: 'completed',
    confidenceScore: 0.87
  };

  const analysisResults: AnalysisResult = {
    summary: {
      content: 'This service agreement establishes terms between ABC Corporation and XYZ Services for ongoing consulting services. Key provisions include a 24-month term, monthly payment schedule, and standard termination clauses.',
      confidence: 0.89,
      keyPoints: [
        'Service period: 24 months from execution date',
        'Monthly compensation: $15,000 plus expenses',
        'Termination: 30-day notice required',
        'Confidentiality provisions included',
        'Dispute resolution through arbitration'
      ]
    },
    parties: {
      identified: [
        {
          name: 'ABC Corporation',
          role: 'Service Recipient',
          confidence: 0.95,
          sourceLocation: 'Page 1, Paragraph 1'
        },
        {
          name: 'XYZ Services LLC',
          role: 'Service Provider', 
          confidence: 0.92,
          sourceLocation: 'Page 1, Paragraph 1'
        }
      ],
      confidence: 0.94
    },
    dates: {
      extracted: [
        {
          date: '2024-02-01',
          description: 'Service commencement date',
          confidence: 0.91,
          sourceLocation: 'Page 2, Section 3.1',
          type: 'event'
        },
        {
          date: '2026-01-31',
          description: 'Contract expiration date',
          confidence: 0.88,
          sourceLocation: 'Page 2, Section 3.2',
          type: 'deadline'
        }
      ],
      confidence: 0.90
    },
    citations: {
      found: [
        {
          citation: 'UCC § 2-201',
          type: 'statute',
          confidence: 0.85,
          sourceLocation: 'Page 8, Section 12.3',
          verified: true
        }
      ],
      confidence: 0.85
    }
  };

  const reviewChecklist = [
    {
      id: 'privilege_check',
      title: 'Privilege Level Verification',
      description: 'Confirm document privilege designation is appropriate',
      required: true
    },
    {
      id: 'summary_accuracy',
      title: 'Summary Accuracy Review',
      description: 'Verify AI-generated summary captures key document elements',
      required: true
    },
    {
      id: 'party_identification',
      title: 'Party Identification Check',
      description: 'Confirm all parties are correctly identified with proper roles',
      required: true
    },
    {
      id: 'date_verification',
      title: 'Date and Deadline Verification',
      description: 'Verify all extracted dates and calculated deadlines',
      required: true
    },
    {
      id: 'citation_validation',
      title: 'Legal Citation Validation',
      description: 'Confirm accuracy and current validity of identified citations',
      required: false
    },
    {
      id: 'confidence_assessment',
      title: 'Confidence Score Assessment',
      description: 'Evaluate whether confidence scores align with actual accuracy',
      required: false
    }
  ];

  const getPrivilegeBadge = (level: string) => {
    switch (level) {
      case 'attorney_client':
        return {
          icon: <Shield className="h-3 w-3" />,
          text: 'Attorney-Client Privileged',
          color: 'bg-error-100 text-error-800 border-error-200'
        };
      case 'work_product':
        return {
          icon: <Shield className="h-3 w-3" />,
          text: 'Work Product',
          color: 'bg-warning-100 text-warning-800 border-warning-200'
        };
      case 'confidential':
        return {
          icon: <Eye className="h-3 w-3" />,
          text: 'Confidential',
          color: 'bg-blue-100 text-blue-800 border-blue-200'
        };
      default:
        return {
          icon: <Info className="h-3 w-3" />,
          text: 'Public',
          color: 'bg-gray-100 text-gray-800 border-gray-200'
        };
    }
  };

  const privilegeBadge = getPrivilegeBadge(document.privilegeLevel);

  const handleSectionReview = (sectionId: string) => {
    if (reviewedSections.includes(sectionId)) {
      setReviewedSections(prev => prev.filter(id => id !== sectionId));
    } else {
      setReviewedSections(prev => [...prev, sectionId]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link href="/documents" className="text-gray-600 hover:text-gray-900">
                <ArrowLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-lg font-semibold text-gray-900">{document.name}</h1>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  <span>{document.type}</span>
                  <span>•</span>
                  <span>{document.pageCount} pages</span>
                  <span>•</span>
                  <span>{document.size}</span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${privilegeBadge.color}`}>
                {privilegeBadge.icon}
                <span className="ml-1">{privilegeBadge.text}</span>
              </span>
              
              <div className="flex items-center space-x-1">
                <button
                  onClick={() => setViewMode('document')}
                  className={`p-2 rounded ${viewMode === 'document' ? 'bg-primary-100 text-primary-600' : 'text-gray-600 hover:text-gray-900'}`}
                  title="Document Only"
                >
                  <FileText className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setViewMode('split')}
                  className={`p-2 rounded ${viewMode === 'split' ? 'bg-primary-100 text-primary-600' : 'text-gray-600 hover:text-gray-900'}`}
                  title="Split View"
                >
                  <Maximize2 className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setViewMode('analysis')}
                  className={`p-2 rounded ${viewMode === 'analysis' ? 'bg-primary-100 text-primary-600' : 'text-gray-600 hover:text-gray-900'}`}
                  title="Analysis Only"
                >
                  <Brain className="h-4 w-4" />
                </button>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setShowReviewChecklist(!showReviewChecklist)}
                  className="inline-flex items-center px-3 py-2 border border-primary-600 text-sm font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50"
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Review Checklist
                </button>
                <button className="p-2 text-gray-600 hover:text-gray-900">
                  <Download className="h-4 w-4" />
                </button>
                <button className="p-2 text-gray-600 hover:text-gray-900">
                  <Share2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* AI Analysis Warning */}
        <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-amber-800 mb-1">AI-Generated Analysis - Attorney Review Required</h3>
              <p className="text-sm text-amber-700">
                This analysis was generated by AI and requires independent professional review. 
                Confidence scores indicate AI certainty but do not replace attorney judgment. 
                Always verify extractions against source documents before relying on information.
              </p>
            </div>
          </div>
        </div>

        {/* Review Checklist Modal */}
        {showReviewChecklist && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Attorney Review Checklist</h3>
                <button
                  onClick={() => setShowReviewChecklist(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>

              <div className="mb-4 bg-legal-50 border border-legal-200 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-legal-700">
                    Complete this checklist to ensure proper professional review of AI-generated document analysis. 
                    This review is essential for maintaining professional responsibility standards.
                  </p>
                </div>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {reviewChecklist.map((item) => (
                  <label key={item.id} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50">
                    <input
                      type="checkbox"
                      checked={reviewedSections.includes(item.id)}
                      onChange={() => handleSectionReview(item.id)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900">{item.title}</span>
                        {item.required && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-error-100 text-error-800">
                            Required
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600">{item.description}</p>
                    </div>
                  </label>
                ))}
              </div>

              <div className="mt-6 flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  {reviewedSections.length} of {reviewChecklist.length} items completed
                </div>
                <div className="space-x-3">
                  <button
                    onClick={() => setShowReviewChecklist(false)}
                    className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Close
                  </button>
                  <button
                    onClick={() => {
                      console.log('Review completed:', reviewedSections);
                      alert('Review status saved. Professional review documentation updated.');
                      setShowReviewChecklist(false);
                    }}
                    className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                  >
                    Save Review Status
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className={`grid gap-6 ${
          viewMode === 'split' ? 'grid-cols-2' : 
          viewMode === 'document' ? 'grid-cols-1' : 
          'grid-cols-1'
        }`}>
          
          {/* Document Viewer */}
          {(viewMode === 'document' || viewMode === 'split') && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Original Document</h2>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-500">Confidence: {(document.confidenceScore * 100).toFixed(0)}%</span>
                  <button className="p-1 text-gray-400 hover:text-gray-600">
                    <Maximize2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <div className="p-4">
                <div className="bg-gray-100 rounded-lg p-8 text-center">
                  <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">PDF Viewer would be embedded here</p>
                  <p className="text-sm text-gray-400 mt-2">
                    Interactive PDF with highlighted citations and extracted elements
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Analysis Panel */}
          {(viewMode === 'analysis' || viewMode === 'split') && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">AI Analysis Results</h2>
                <div className="flex items-center space-x-2">
                  <Brain className="h-4 w-4 text-primary-600" />
                  <span className="text-sm text-primary-600">AI Generated</span>
                </div>
              </div>

              {/* Analysis Tabs */}
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-4">
                  {[
                    { key: 'comprehensive', label: 'Comprehensive Analysis', icon: Brain },
                    { key: 'qa', label: 'Smart Q&A', icon: MessageSquare },
                    { key: 'summary', label: 'Summary', icon: FileText },
                    { key: 'dates', label: 'Key Dates', icon: Clock },
                    { key: 'parties', label: 'Parties', icon: Users },
                    { key: 'deadlines', label: 'Deadlines', icon: AlertTriangle }
                  ].map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => setActiveAnalysisTab(tab.key as any)}
                      className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                        activeAnalysisTab === tab.key
                          ? 'border-primary-500 text-primary-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <tab.icon className="h-4 w-4" />
                      <span>{tab.label}</span>
                    </button>
                  ))}
                </nav>
              </div>

              {/* Analysis Content */}
              <div className="p-4">
                {activeAnalysisTab === 'comprehensive' && (
                  <ComprehensiveAnalysisDisplay
                    documentId={document.id}
                    documentName={document.name}
                    documentType={document.type}
                  />
                )}

                {activeAnalysisTab === 'qa' && (
                  <SmartQASystem
                    documentAnalysis={analysisResults}
                    documentText="Mock document text would be provided here from the document processing API"
                  />
                )}

                {activeAnalysisTab === 'summary' && (
                  <PlainEnglishSummary
                    summary={analysisResults.summary}
                    documentType={document.type}
                  />
                )}

                {activeAnalysisTab === 'dates' && (
                  <KeyDatesExtractor
                    dates={analysisResults.dates}
                    documentName={document.name}
                  />
                )}

                {activeAnalysisTab === 'parties' && (
                  <PartyIdentifier
                    parties={analysisResults.parties}
                    documentType={document.type}
                  />
                )}

                {activeAnalysisTab === 'deadlines' && (
                  <DeadlineCalculator
                    dates={analysisResults.dates.extracted.filter(d => d.type === 'deadline')}
                    documentName={document.name}
                  />
                )}
              </div>
            </div>
          )}
        </div>

        {/* Verification Interface */}
        <div className="mt-6">
          <ExtractionVerifier 
            analysisResults={analysisResults}
            documentId={document.id}
            onVerificationComplete={() => {
              console.log('Verification completed');
            }}
          />
        </div>

        {/* Professional Responsibility Footer */}
        <div className="mt-6 bg-legal-50 border border-legal-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Scale className="h-5 w-5 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-legal-900 mb-2">Professional Responsibility Reminder</h3>
              <div className="text-sm text-legal-700 space-y-1">
                <p>
                  • AI analysis is a tool to assist professional judgment, not replace it
                </p>
                <p>
                  • Independent verification of all extractions and calculations is required
                </p>
                <p>
                  • Privilege designations and confidentiality must be maintained throughout the process
                </p>
                <p>
                  • Document retention and audit trail requirements apply to all AI-processed materials
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentAnalysisPage;