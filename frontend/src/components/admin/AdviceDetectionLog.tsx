'use client';

import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  Flag,
  Eye,
  EyeOff,
  Search,
  Filter,
  Download,
  Brain,
  User,
  Clock,
  MapPin,
  Scale,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Shield,
  FileText,
  MessageSquare
} from 'lucide-react';

interface AdviceDetection {
  id: string;
  timestamp: string;
  userId: string;
  userType: 'attorney' | 'staff' | 'client';
  sessionId: string;
  query: string;
  aiResponse: string;
  detectedAdvice: string[];
  confidenceScore: number;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  keywords: string[];
  context: 'document_analysis' | 'legal_research' | 'general_query' | 'deadline_calculation';
  jurisdiction: string;
  reviewStatus: 'pending' | 'reviewed' | 'approved' | 'flagged' | 'corrected';
  reviewerNotes?: string;
  actionTaken?: string;
  falsePositive?: boolean;
}

interface DetectionPattern {
  pattern: string;
  description: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  occurrences: number;
  lastDetected: string;
}

interface AdviceDetectionLogProps {
  timeRange?: '24h' | '7d' | '30d';
  jurisdiction?: string;
  riskLevel?: string;
  onDetectionReview?: (detectionId: string, action: string) => void;
  className?: string;
}

const AdviceDetectionLog: React.FC<AdviceDetectionLogProps> = ({
  timeRange = '7d',
  jurisdiction = 'all',
  riskLevel = 'all',
  onDetectionReview,
  className = ''
}) => {
  const [detections, setDetections] = useState<AdviceDetection[]>([]);
  const [patterns, setPatterns] = useState<DetectionPattern[]>([]);
  const [expandedDetections, setExpandedDetections] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilters, setSelectedFilters] = useState({
    showResolved: false,
    showFalsePositives: false,
    contextFilter: 'all'
  });
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadDetectionData();
  }, [timeRange, jurisdiction, riskLevel]);

  const loadDetectionData = async () => {
    setIsLoading(true);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Mock detection data
    setDetections([
      {
        id: 'det_001',
        timestamp: '2024-01-16T14:30:00Z',
        userId: 'user_***789',
        userType: 'staff',
        sessionId: 'sess_abc123',
        query: 'Should we file this motion immediately?',
        aiResponse: 'Based on the deadlines in your case, I recommend filing the motion as soon as possible to avoid missing the court deadline. You should also consider including additional evidence to strengthen your argument.',
        detectedAdvice: [
          'I recommend filing the motion as soon as possible',
          'You should also consider including additional evidence'
        ],
        confidenceScore: 0.92,
        riskLevel: 'critical',
        keywords: ['recommend', 'should', 'file', 'motion', 'deadline'],
        context: 'deadline_calculation',
        jurisdiction: 'CA',
        reviewStatus: 'pending',
        falsePositive: false
      },
      {
        id: 'det_002',
        timestamp: '2024-01-16T13:45:00Z',
        userId: 'user_***456',
        userType: 'client',
        sessionId: 'sess_def456',
        query: 'What should I do about my contract dispute?',
        aiResponse: 'For contract disputes in California, you may want to review the contract terms carefully and consider whether mediation might be appropriate. I suggest consulting with your attorney about the specific circumstances.',
        detectedAdvice: [
          'you may want to review the contract terms',
          'I suggest consulting with your attorney'
        ],
        confidenceScore: 0.76,
        riskLevel: 'high',
        keywords: ['should', 'suggest', 'review', 'consider'],
        context: 'legal_research',
        jurisdiction: 'CA',
        reviewStatus: 'reviewed',
        reviewerNotes: 'Contains soft advice language - approved with disclaimer',
        actionTaken: 'Additional disclaimer shown',
        falsePositive: false
      },
      {
        id: 'det_003',
        timestamp: '2024-01-16T12:15:00Z',
        userId: 'user_***123',
        userType: 'attorney',
        sessionId: 'sess_ghi789',
        query: 'How do I calculate statute of limitations?',
        aiResponse: 'The statute of limitations calculation depends on several factors including the type of claim and jurisdiction. In California, breach of contract claims generally have a 4-year limitation period for written contracts.',
        detectedAdvice: [],
        confidenceScore: 0.23,
        riskLevel: 'low',
        keywords: ['calculate', 'limitation', 'period'],
        context: 'legal_research',
        jurisdiction: 'CA',
        reviewStatus: 'approved',
        falsePositive: true
      }
    ]);

    // Mock pattern data
    setPatterns([
      {
        pattern: 'I recommend/suggest [action]',
        description: 'Direct recommendations for specific actions',
        riskLevel: 'critical',
        occurrences: 12,
        lastDetected: '2024-01-16T14:30:00Z'
      },
      {
        pattern: 'You should [verb]',
        description: 'Imperative advice statements',
        riskLevel: 'high',
        occurrences: 8,
        lastDetected: '2024-01-16T13:45:00Z'
      },
      {
        pattern: 'You may want to consider',
        description: 'Soft advice suggestions',
        riskLevel: 'medium',
        occurrences: 15,
        lastDetected: '2024-01-16T12:30:00Z'
      },
      {
        pattern: 'It would be advisable to',
        description: 'Advisory language patterns',
        riskLevel: 'high',
        occurrences: 6,
        lastDetected: '2024-01-15T16:20:00Z'
      }
    ]);

    setIsLoading(false);
  };

  const toggleExpansion = (detectionId: string) => {
    setExpandedDetections(prev => {
      const next = new Set(prev);
      if (next.has(detectionId)) {
        next.delete(detectionId);
      } else {
        next.add(detectionId);
      }
      return next;
    });
  };

  const handleReviewAction = (detectionId: string, action: 'approve' | 'flag' | 'correct') => {
    setDetections(prev => 
      prev.map(detection => 
        detection.id === detectionId 
          ? { 
              ...detection, 
              reviewStatus: action === 'approve' ? 'approved' : action === 'flag' ? 'flagged' : 'corrected'
            }
          : detection
      )
    );
    
    onDetectionReview?.(detectionId, action);
  };

  const markFalsePositive = (detectionId: string) => {
    setDetections(prev => 
      prev.map(detection => 
        detection.id === detectionId 
          ? { ...detection, falsePositive: true, reviewStatus: 'approved' }
          : detection
      )
    );
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'critical': return 'text-red-700 bg-red-100 border-red-300';
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-amber-700 bg-amber-100 border-amber-300';
      case 'low': return 'text-green-700 bg-green-100 border-green-300';
      default: return 'text-gray-700 bg-gray-100 border-gray-300';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'flagged': return 'text-red-700 bg-red-100';
      case 'pending': return 'text-amber-700 bg-amber-100';
      case 'approved': return 'text-green-700 bg-green-100';
      case 'corrected': return 'text-blue-700 bg-blue-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  const getContextIcon = (context: string) => {
    switch (context) {
      case 'document_analysis': return <FileText className="h-4 w-4" />;
      case 'legal_research': return <Search className="h-4 w-4" />;
      case 'deadline_calculation': return <Clock className="h-4 w-4" />;
      default: return <MessageSquare className="h-4 w-4" />;
    }
  };

  const highlightAdvice = (text: string, advice: string[]) => {
    let highlightedText = text;
    advice.forEach(phrase => {
      const regex = new RegExp(`(${phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-200 px-1 rounded">$1</mark>');
    });
    return highlightedText;
  };

  const filteredDetections = detections.filter(detection => {
    if (!selectedFilters.showResolved && detection.reviewStatus !== 'pending') return false;
    if (!selectedFilters.showFalsePositives && detection.falsePositive) return false;
    if (selectedFilters.contextFilter !== 'all' && detection.context !== selectedFilters.contextFilter) return false;
    if (searchTerm && !detection.query.toLowerCase().includes(searchTerm.toLowerCase()) && 
        !detection.aiResponse.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  const exportDetectionData = () => {
    const exportData = {
      type: 'Advice Detection Log',
      exported: new Date().toISOString(),
      timeRange,
      jurisdiction,
      riskLevel,
      totalDetections: filteredDetections.length,
      data: filteredDetections.map(detection => ({
        ...detection,
        userId: '[REDACTED]',
        sessionId: '[REDACTED]'
      })),
      patterns
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `advice-detection-log-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Flag className="h-6 w-6 text-red-600" />
          <h2 className="text-xl font-semibold text-gray-900">Advice Detection Log</h2>
          <span className="px-2 py-1 bg-red-100 text-red-800 text-sm rounded-full">
            {filteredDetections.length} flagged
          </span>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Search className="h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search detections..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-legal-500"
            />
          </div>

          <button
            onClick={loadDetectionData}
            disabled={isLoading}
            className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={exportDetectionData}
            className="flex items-center space-x-1 px-3 py-2 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <Download className="h-4 w-4" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Critical Detections</p>
              <p className="text-2xl font-bold text-red-600">
                {detections.filter(d => d.riskLevel === 'critical').length}
              </p>
            </div>
            <AlertTriangle className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Pending Review</p>
              <p className="text-2xl font-bold text-amber-600">
                {detections.filter(d => d.reviewStatus === 'pending').length}
              </p>
            </div>
            <Clock className="h-8 w-8 text-amber-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Confidence</p>
              <p className="text-2xl font-bold text-blue-600">
                {(detections.reduce((sum, d) => sum + d.confidenceScore, 0) / detections.length * 100).toFixed(0)}%
              </p>
            </div>
            <Brain className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">False Positives</p>
              <p className="text-2xl font-bold text-green-600">
                {detections.filter(d => d.falsePositive).length}
              </p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-500" />
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Filter Options</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedFilters.showResolved}
                onChange={(e) => setSelectedFilters(prev => ({ ...prev, showResolved: e.target.checked }))}
                className="rounded border-gray-300 text-legal-600 focus:ring-legal-500"
              />
              <span className="text-sm text-gray-700">Show resolved detections</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedFilters.showFalsePositives}
                onChange={(e) => setSelectedFilters(prev => ({ ...prev, showFalsePositives: e.target.checked }))}
                className="rounded border-gray-300 text-legal-600 focus:ring-legal-500"
              />
              <span className="text-sm text-gray-700">Show false positives</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Context Filter
            </label>
            <select
              value={selectedFilters.contextFilter}
              onChange={(e) => setSelectedFilters(prev => ({ ...prev, contextFilter: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-legal-500"
            >
              <option value="all">All Contexts</option>
              <option value="document_analysis">Document Analysis</option>
              <option value="legal_research">Legal Research</option>
              <option value="deadline_calculation">Deadline Calculation</option>
              <option value="general_query">General Query</option>
            </select>
          </div>

          <div className="text-sm text-gray-500">
            Showing {filteredDetections.length} of {detections.length} detections
          </div>
        </div>
      </div>

      {/* Detection Patterns */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Common Advice Patterns</h3>
        
        <div className="space-y-3">
          {patterns.map((pattern, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex-1">
                <div className="flex items-center space-x-3">
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getRiskColor(pattern.riskLevel)}`}>
                    {pattern.riskLevel.toUpperCase()}
                  </span>
                  <code className="text-sm font-mono bg-gray-200 px-2 py-1 rounded">
                    {pattern.pattern}
                  </code>
                </div>
                <p className="text-sm text-gray-600 mt-1">{pattern.description}</p>
              </div>
              
              <div className="text-right text-sm text-gray-500">
                <div>{pattern.occurrences} occurrences</div>
                <div>Last: {new Date(pattern.lastDetected).toLocaleDateString()}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detection List */}
      <div className="space-y-4">
        {filteredDetections.map((detection) => (
          <div key={detection.id} className="bg-white rounded-lg shadow border">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getRiskColor(detection.riskLevel)}`}>
                      <Flag className="h-3 w-3 mr-1" />
                      {detection.riskLevel.toUpperCase()} RISK
                    </span>
                    
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(detection.reviewStatus)}`}>
                      {detection.reviewStatus.toUpperCase()}
                    </span>

                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      {getContextIcon(detection.context)}
                      <span className="ml-1">{detection.context.replace('_', ' ').toUpperCase()}</span>
                    </span>

                    {detection.falsePositive && (
                      <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-green-100 text-green-800">
                        False Positive
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                    <div>
                      <span className="font-medium">User:</span> {detection.userId}
                    </div>
                    <div>
                      <span className="font-medium">Type:</span> {detection.userType}
                    </div>
                    <div>
                      <span className="font-medium">Confidence:</span> {(detection.confidenceScore * 100).toFixed(0)}%
                    </div>
                    <div>
                      <span className="font-medium">Time:</span> {new Date(detection.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {detection.reviewStatus === 'pending' && (
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => handleReviewAction(detection.id, 'approve')}
                        className="p-1 text-green-600 hover:bg-green-100 rounded"
                        title="Approve"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => handleReviewAction(detection.id, 'flag')}
                        className="p-1 text-red-600 hover:bg-red-100 rounded"
                        title="Flag for Review"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                      
                      <button
                        onClick={() => markFalsePositive(detection.id)}
                        className="p-1 text-gray-600 hover:bg-gray-100 rounded"
                        title="Mark as False Positive"
                      >
                        <Shield className="h-4 w-4" />
                      </button>
                    </div>
                  )}

                  <button
                    onClick={() => toggleExpansion(detection.id)}
                    className="flex items-center space-x-1 text-sm text-gray-500 hover:text-gray-700"
                  >
                    {expandedDetections.has(detection.id) ? (
                      <>
                        <ChevronDown className="h-4 w-4" />
                        <span>Hide</span>
                      </>
                    ) : (
                      <>
                        <ChevronRight className="h-4 w-4" />
                        <span>Details</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {expandedDetections.has(detection.id) && (
              <div className="px-6 py-4 space-y-4">
                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">User Query</h4>
                  <div className="bg-gray-50 border rounded p-3 text-sm">
                    {detection.query}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-900 mb-2">AI Response with Detected Advice</h4>
                  <div 
                    className="bg-red-50 border border-red-200 rounded p-3 text-sm"
                    dangerouslySetInnerHTML={{ 
                      __html: highlightAdvice(detection.aiResponse, detection.detectedAdvice) 
                    }}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Detected Advice Phrases</h4>
                    <div className="space-y-1">
                      {detection.detectedAdvice.map((phrase, index) => (
                        <div key={index} className="bg-yellow-100 border border-yellow-300 rounded px-2 py-1 text-sm">
                          "{phrase}"
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Trigger Keywords</h4>
                    <div className="flex flex-wrap gap-1">
                      {detection.keywords.map((keyword, index) => (
                        <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-800">
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {detection.reviewerNotes && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Reviewer Notes</h4>
                    <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm">
                      {detection.reviewerNotes}
                    </div>
                  </div>
                )}

                {detection.actionTaken && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 mb-2">Action Taken</h4>
                    <div className="bg-green-50 border border-green-200 rounded p-3 text-sm">
                      {detection.actionTaken}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between pt-3 border-t border-gray-200">
                  <div className="text-xs text-gray-500 space-x-4">
                    <span>Session ID: {detection.sessionId}</span>
                    <span>Jurisdiction: {detection.jurisdiction}</span>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button className="px-3 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-700">
                      View Full Session
                    </button>
                    <button className="px-3 py-1 bg-legal-600 text-white text-xs rounded hover:bg-legal-700">
                      Add Training Data
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}

        {filteredDetections.length === 0 && (
          <div className="bg-white rounded-lg shadow p-8 text-center">
            <Flag className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Advice Detections Found</h3>
            <p className="text-gray-600">
              {detections.length === 0 
                ? "No advice has been detected in AI responses during the selected time period."
                : "All detections have been filtered out based on your current filter settings."
              }
            </p>
          </div>
        )}
      </div>

      {/* Professional Responsibility Notice */}
      <div className="bg-legal-50 border border-legal-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <Scale className="h-6 w-6 text-legal-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-semibold text-legal-900 mb-2">Advice Detection & UPL Compliance</h3>
            <p className="text-legal-800 mb-3">
              This log tracks AI responses that may contain legal advice or recommendations. All flagged content 
              requires immediate review to ensure compliance with unauthorized practice of law (UPL) regulations.
            </p>
            <div className="text-sm text-legal-700 space-y-1">
              <p>• <strong>Critical Risk:</strong> Direct recommendations requiring immediate intervention</p>
              <p>• <strong>High Risk:</strong> Advice-like language requiring attorney review within 24 hours</p>
              <p>• <strong>Medium Risk:</strong> Suggestive language requiring monitoring and disclaimers</p>
              <p>• <strong>Low Risk:</strong> Educational content with minimal advice indicators</p>
              <p>• <strong>False Positives:</strong> Legitimate educational content incorrectly flagged</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdviceDetectionLog;