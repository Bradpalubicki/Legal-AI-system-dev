'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { 
  ArrowLeft,
  FileText,
  Shield,
  Eye,
  Calendar,
  Brain,
  AlertTriangle,
  Info,
  Scale,
  Clock,
  Users,
  ExternalLink,
  Download,
  Search,
  BookOpen,
  CheckCircle,
  XCircle,
  Star,
  Filter
} from 'lucide-react';
import InfoTooltip from '@/components/dashboard/InfoTooltip';
import AIAnalysisCard from '@/components/dashboard/AIAnalysisCard';
import DeadlineDisplay from '@/components/dashboard/DeadlineDisplay';
import { formatComplianceDate } from '@/utils/compliance-utils';

interface MatterDetailPageProps {
  params: {
    matterId: string;
  };
}

const MatterDetailPage: React.FC<MatterDetailPageProps> = ({ params }) => {
  const [activeTab, setActiveTab] = useState<'documents' | 'timeline' | 'analysis' | 'citations'>('documents');
  const [showDisclaimers, setShowDisclaimers] = useState(true);

  // Mock data - in real app, this would come from API based on params.matterId
  const matter = {
    id: params.matterId,
    title: 'Smith v. ABC Corporation Contract Dispute',
    client: 'John Smith',
    type: 'Commercial Litigation',
    status: 'active' as const,
    priority: 'high' as const,
    privilegeLevel: 'attorney_client' as const,
    description: 'Contract dispute involving breach of service agreement and damages claim',
    lastActivity: '2024-01-15T10:30:00Z',
    nextDeadline: '2024-02-01T17:00:00Z',
    assignedAttorney: 'Sarah Johnson, Esq.',
    caseNumber: 'CV-2024-001234',
    filingDate: '2023-12-01T00:00:00Z',
    jurisdiction: 'Superior Court of California, County of Los Angeles'
  };

  const documents = [
    {
      id: '1',
      name: 'Initial Complaint.pdf',
      type: 'Pleading',
      privilegeLevel: 'attorney_client' as const,
      uploadDate: '2023-12-01T10:00:00Z',
      size: '2.3 MB',
      aiAnalyzed: true,
      confidenceScore: 0.92
    },
    {
      id: '2', 
      name: 'Service Agreement Draft.docx',
      type: 'Contract',
      privilegeLevel: 'work_product' as const,
      uploadDate: '2023-12-05T14:30:00Z',
      size: '1.1 MB',
      aiAnalyzed: true,
      confidenceScore: 0.88
    },
    {
      id: '3',
      name: 'Client Interview Notes.pdf',
      type: 'Work Product',
      privilegeLevel: 'attorney_client' as const,
      uploadDate: '2023-12-10T09:15:00Z',
      size: '0.5 MB',
      aiAnalyzed: false,
      confidenceScore: 0
    }
  ];

  const timeline = [
    {
      id: '1',
      date: '2024-02-01T17:00:00Z',
      title: 'Answer Due',
      type: 'filing' as const,
      description: 'Defendant\'s answer to complaint must be filed',
      isTypical: true,
      status: 'upcoming' as const
    },
    {
      id: '2',
      date: '2024-02-15T17:00:00Z', 
      title: 'Case Management Conference',
      type: 'hearing' as const,
      description: 'Initial case management conference scheduled',
      isTypical: true,
      status: 'scheduled' as const
    },
    {
      id: '3',
      date: '2024-03-01T17:00:00Z',
      title: 'Discovery Deadline',
      type: 'discovery' as const,
      description: 'Typical deadline for initial discovery requests',
      isTypical: true,
      status: 'typical' as const
    }
  ];

  const aiSuggestions = [
    {
      id: '1',
      matterId: params.matterId,
      matterTitle: matter.title,
      type: 'research' as const,
      title: 'Review Recent Contract Interpretation Cases',
      description: 'AI identified 3 recent California cases on service agreement interpretation that may be relevant to contractual obligations analysis.',
      confidenceScore: 0.84,
      requiresReview: true,
      createdAt: '2024-01-14T15:30:00Z'
    },
    {
      id: '2',
      matterId: params.matterId,
      matterTitle: matter.title,
      type: 'strategy' as const,
      title: 'Consider Mediation Options',
      description: 'Based on case type and jurisdiction, mediation might be beneficial before proceeding with extensive discovery.',
      confidenceScore: 0.76,
      requiresReview: true,
      createdAt: '2024-01-13T11:20:00Z'
    }
  ];

  const citations = [
    {
      id: '1',
      citation: 'Smith v. Jones, 123 Cal.App.4th 456 (2019)',
      type: 'case_law',
      relevance: 'high',
      context: 'Contract interpretation standards',
      verified: true,
      shepardized: true
    },
    {
      id: '2',
      citation: 'Civil Code § 1549',
      type: 'statute',
      relevance: 'medium', 
      context: 'Contract formation requirements',
      verified: true,
      shepardized: false
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

  const getTimelineStatus = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-success-100 text-success-800';
      case 'upcoming':
        return 'bg-warning-100 text-warning-800';
      case 'scheduled':
        return 'bg-blue-100 text-blue-800';
      case 'typical':
        return 'bg-gray-100 text-gray-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link 
                href="/dashboard"
                className="inline-flex items-center text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Link>
              <div className="text-sm text-gray-500">|</div>
              <h1 className="text-lg font-semibold text-gray-900">
                Matter Details
              </h1>
            </div>

            <div className="flex items-center space-x-4">
              {showDisclaimers && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  <Info className="h-3 w-3 mr-1" />
                  Information Only
                </span>
              )}
              <button
                onClick={() => setShowDisclaimers(!showDisclaimers)}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                {showDisclaimers ? 'Hide' : 'Show'} Disclaimers
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Matter Summary */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-2">
                <h2 className="text-xl font-semibold text-gray-900">
                  {matter.title}
                </h2>
                <InfoTooltip
                  content="Case titles and information are provided for reference only. Always verify details through official court records."
                  type="legal"
                  title="Case Information Disclaimer"
                />
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Client:</span>
                  <div className="font-medium">{matter.client}</div>
                </div>
                <div>
                  <span className="text-gray-500">Case Type:</span>
                  <div className="font-medium">{matter.type}</div>
                </div>
                <div>
                  <span className="text-gray-500">Case Number:</span>
                  <div className="font-medium">{matter.caseNumber}</div>
                </div>
                <div>
                  <span className="text-gray-500">Attorney:</span>
                  <div className="font-medium">{matter.assignedAttorney}</div>
                </div>
              </div>

              <div className="mt-4 text-sm text-gray-600">
                <strong>Jurisdiction:</strong> {matter.jurisdiction}
              </div>
            </div>

            <div className="flex flex-col space-y-2">
              {getPrivilegeBadge(matter.privilegeLevel) && (
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getPrivilegeBadge(matter.privilegeLevel).color}`}>
                  {getPrivilegeBadge(matter.privilegeLevel).icon}
                  <span className="ml-1">{getPrivilegeBadge(matter.privilegeLevel).text}</span>
                </span>
              )}
              
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-100 text-success-800">
                {matter.status.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Professional Responsibility Notice */}
          {showDisclaimers && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h5 className="text-xs font-semibold text-legal-900 mb-1">
                      Professional Responsibility Notice
                    </h5>
                    <p className="text-xs text-legal-700">
                      All case information displayed is for informational purposes only. You remain 
                      responsible for verifying all details through official court records, applicable 
                      rules, and case-specific orders. This system does not provide legal advice.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
          <div className="border-b border-gray-200">
            <nav className="flex space-x-8 px-6">
              {[
                { key: 'documents', label: 'Documents', icon: FileText },
                { key: 'timeline', label: 'Timeline', icon: Calendar },
                { key: 'analysis', label: 'AI Analysis', icon: Brain },
                { key: 'citations', label: 'Citations', icon: BookOpen }
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.key
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

          {/* Tab Content */}
          <div className="p-6">
            {/* Documents Tab */}
            {activeTab === 'documents' && (
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <h3 className="text-lg font-medium text-gray-900">Documents</h3>
                    <InfoTooltip
                      content="Document privilege levels are marked for reference. Always maintain proper confidentiality protections and verify privilege status."
                      type="legal"
                      title="Document Privilege Information"
                    />
                  </div>
                  <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                    <Filter className="h-4 w-4 mr-2" />
                    Filter
                  </button>
                </div>

                <div className="space-y-4">
                  {documents.map((doc) => {
                    const privilegeBadge = getPrivilegeBadge(doc.privilegeLevel);
                    return (
                      <div key={doc.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-3">
                            <FileText className="h-5 w-5 text-gray-400 mt-1" />
                            <div>
                              <h4 className="font-medium text-gray-900">{doc.name}</h4>
                              <div className="flex items-center space-x-2 mt-1">
                                <span className="text-sm text-gray-500">{doc.type}</span>
                                <span className="text-sm text-gray-400">•</span>
                                <span className="text-sm text-gray-500">{doc.size}</span>
                                <span className="text-sm text-gray-400">•</span>
                                <span className="text-sm text-gray-500">
                                  {formatComplianceDate(doc.uploadDate)}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2">
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${privilegeBadge.color}`}>
                              {privilegeBadge.icon}
                              <span className="ml-1">{privilegeBadge.text}</span>
                            </span>

                            {doc.aiAnalyzed && (
                              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                <Brain className="h-3 w-3 mr-1" />
                                AI Analyzed ({Math.round(doc.confidenceScore * 100)}%)
                              </span>
                            )}

                            <div className="flex items-center space-x-1">
                              <button className="p-1 text-gray-400 hover:text-gray-600">
                                <Eye className="h-4 w-4" />
                              </button>
                              <button className="p-1 text-gray-400 hover:text-gray-600">
                                <Download className="h-4 w-4" />
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {showDisclaimers && (
                  <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
                    <div className="flex items-start space-x-2">
                      <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <h5 className="text-xs font-semibold text-amber-800 mb-1">
                          Document Security Reminder
                        </h5>
                        <p className="text-xs text-amber-700">
                          All documents marked as privileged require special handling. Maintain 
                          confidentiality protections and follow firm policies for document access and sharing.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Timeline Tab */}
            {activeTab === 'timeline' && (
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Typical Deadlines & Timeline</h3>
                  <InfoTooltip
                    content="Timeline deadlines are typical for this case type and jurisdiction. Always verify actual deadlines through court orders and local rules."
                    type="warning"
                    title="Deadline Information Disclaimer"
                  />
                </div>

                <div className="space-y-4">
                  {timeline.map((item) => (
                    <div key={item.id} className="relative pl-8">
                      <div className="absolute left-0 top-1 w-2 h-2 bg-primary-600 rounded-full"></div>
                      <div className="absolute left-1 top-3 w-px h-full bg-gray-200"></div>
                      
                      <div className="bg-white border border-gray-200 rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center space-x-2 mb-1">
                              <h4 className="font-medium text-gray-900">{item.title}</h4>
                              {item.isTypical && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                                  Typical Deadline
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mb-2">{item.description}</p>
                            <div className="text-sm font-medium text-gray-900">
                              {formatComplianceDate(item.date)}
                            </div>
                          </div>

                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getTimelineStatus(item.status)}`}>
                            {item.status.replace('_', ' ').toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {showDisclaimers && (
                  <div className="mt-6 bg-legal-50 border border-legal-200 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <h5 className="text-sm font-semibold text-legal-900 mb-2">
                          Timeline Disclaimer - Professional Responsibility
                        </h5>
                        <p className="text-sm text-legal-700 mb-2">
                          The deadlines shown represent typical timeframes for this case type and jurisdiction. 
                          You remain professionally responsible for:
                        </p>
                        <ul className="text-sm text-legal-700 space-y-1 list-disc list-inside">
                          <li>Verifying actual deadlines through official court orders and local rules</li>
                          <li>Calculating deadlines according to applicable procedural rules</li>
                          <li>Monitoring for any changes or extensions</li>
                          <li>Maintaining adequate calendaring and deadline management systems</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* AI Analysis Tab */}
            {activeTab === 'analysis' && (
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <h3 className="text-lg font-medium text-gray-900">AI Analysis & Suggestions</h3>
                  <InfoTooltip
                    content="AI suggestions require independent professional review and do not constitute legal advice. Use as informational tools only."
                    type="warning"
                    title="AI Analysis Disclaimer"
                  />
                </div>

                <div className="space-y-4">
                  {aiSuggestions.map((suggestion) => (
                    <AIAnalysisCard
                      key={suggestion.id}
                      suggestion={suggestion}
                      showReviewWarning={showDisclaimers}
                    />
                  ))}
                </div>

                <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="flex items-start space-x-2">
                    <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <h5 className="text-sm font-semibold text-blue-900 mb-1">
                        Common Response Options - Information Only
                      </h5>
                      <p className="text-sm text-blue-800 mb-2">
                        When reviewing AI analysis, attorneys commonly consider these approaches 
                        (for informational purposes only):
                      </p>
                      <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
                        <li>Verify AI-identified legal authorities through primary sources</li>
                        <li>Consider jurisdiction-specific variations in law and procedure</li>
                        <li>Analyze factual similarities and distinctions in cited cases</li>
                        <li>Review current validity and any subsequent history of citations</li>
                        <li>Apply independent professional judgment to case-specific circumstances</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Citations Tab */}
            {activeTab === 'citations' && (
              <div>
                <div className="flex items-center space-x-2 mb-4">
                  <h3 className="text-lg font-medium text-gray-900">Source Citations</h3>
                  <InfoTooltip
                    content="Citation verification status shown for reference only. Always independently verify legal authorities through authoritative sources."
                    type="legal"
                    title="Citation Verification Disclaimer"
                  />
                </div>

                <div className="space-y-4">
                  {citations.map((citation) => (
                    <div key={citation.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium text-gray-900">{citation.citation}</h4>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              citation.relevance === 'high' ? 'bg-success-100 text-success-800' :
                              citation.relevance === 'medium' ? 'bg-warning-100 text-warning-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {citation.relevance.toUpperCase()} RELEVANCE
                            </span>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-2">{citation.context}</p>
                          
                          <div className="flex items-center space-x-4 text-xs text-gray-500">
                            <span className="capitalize">{citation.type.replace('_', ' ')}</span>
                            
                            {citation.verified && (
                              <span className="inline-flex items-center text-success-600">
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Verified
                              </span>
                            )}
                            
                            {citation.shepardized && (
                              <span className="inline-flex items-center text-blue-600">
                                <Star className="h-3 w-3 mr-1" />
                                Shepardized
                              </span>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          <button className="p-1 text-gray-400 hover:text-gray-600">
                            <Search className="h-4 w-4" />
                          </button>
                          <button className="p-1 text-gray-400 hover:text-gray-600">
                            <ExternalLink className="h-4 w-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {showDisclaimers && (
                  <div className="mt-6 bg-legal-50 border border-legal-200 rounded-lg p-4">
                    <div className="flex items-start space-x-2">
                      <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
                      <div>
                        <h5 className="text-sm font-semibold text-legal-900 mb-2">
                          Citation Verification Requirements
                        </h5>
                        <p className="text-sm text-legal-700 mb-2">
                          Professional responsibility requires independent verification of all legal authorities:
                        </p>
                        <ul className="text-sm text-legal-700 space-y-1 list-disc list-inside">
                          <li>Verify current validity through authoritative legal databases</li>
                          <li>Check for subsequent history, appeals, or overruling decisions</li>
                          <li>Confirm jurisdiction-specific applicability</li>
                          <li>Review primary sources rather than relying on AI summaries</li>
                          <li>Shepardize or KeyCite all case law and statutory citations</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MatterDetailPage;