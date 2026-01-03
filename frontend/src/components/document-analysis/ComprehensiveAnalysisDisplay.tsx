'use client';

import React, { useState, useEffect } from 'react';
import {
  FileText,
  Users,
  Calendar,
  AlertTriangle,
  BookOpen,
  Scale,
  Clock,
  DollarSign,
  Info,
  ChevronDown,
  ChevronRight,
  Eye,
  Download,
  Save,
  HelpCircle,
  ExternalLink,
  Shield,
  CheckCircle,
  Brain,
  Target,
  TrendingUp,
  Lightbulb,
  MessageSquare,
  MapPin,
  HelpCircle as QuestionMark,
  Gavel,
  ArrowRight
} from 'lucide-react';
import { API_CONFIG } from '../../config/api';

// Helper to get auth headers
const getAuthHeaders = (): HeadersInit => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('accessToken');
    if (token) {
      return { 'Authorization': `Bearer ${token}` };
    }
  }
  return {};
};

interface ComprehensiveAnalysisProps {
  documentId: string;
  documentName?: string;
  documentType?: string;
  aiAnalysis?: any; // Will be typed more specifically based on our AI analysis structure
  onAnalysisUpdate?: (analysis: any) => void;
}

interface ExpandableSection {
  id: string;
  title: string;
  icon: React.ReactNode;
  content: React.ReactNode;
  urgent?: boolean;
  educationalContent?: string;
}

const ComprehensiveAnalysisDisplay: React.FC<ComprehensiveAnalysisProps> = ({
  documentId,
  aiAnalysis,
  onAnalysisUpdate
}) => {
  const [analysis, setAnalysis] = useState(aiAnalysis);
  const [loading, setLoading] = useState(!aiAnalysis);
  const [error, setError] = useState<string | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['summary', '5w-who', '5w-what', '5w-when', '5w-where', '5w-why']));
  const [showEducationalSidebar, setShowEducationalSidebar] = useState(false);
  const [activeEducationalTopic, setActiveEducationalTopic] = useState<string | null>(null);
  const [strategicQuestions, setStrategicQuestions] = useState<any[]>([]);
  const [loadingQuestions, setLoadingQuestions] = useState(false);

  // Fetch AI analysis if not provided
  useEffect(() => {
    if (!aiAnalysis && documentId) {
      fetchAIAnalysis();
    }
  }, [documentId, aiAnalysis]);

  // Fetch strategic questions when analysis is available
  useEffect(() => {
    if (analysis && strategicQuestions.length === 0 && !loadingQuestions) {
      fetchStrategicQuestions(analysis);
    }
  }, [analysis, strategicQuestions.length, loadingQuestions]);

  const fetchAIAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);

      // First try to get existing analysis
      let response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/document-processing/documents/${documentId}/ai-analysis`, {
        headers: getAuthHeaders()
      });

      if (response.status === 404) {
        // If no analysis exists, trigger AI analysis
        response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/document-processing/ai-analyze?doc_id=${documentId}`, {
          method: 'POST',
          headers: getAuthHeaders()
        });
      }

      if (!response.ok) {
        throw new Error('Failed to fetch AI analysis');
      }

      const data = await response.json();
      const analysisData = data.ai_powered_analysis || data.ai_analysis;
      setAnalysis(analysisData);
      onAnalysisUpdate?.(analysisData);

      // Fetch strategic questions once we have analysis
      if (analysisData) {
        fetchStrategicQuestions(analysisData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchStrategicQuestions = async (documentAnalysis: any) => {
    try {
      setLoadingQuestions(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/qa/strategic-questions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify({
          document_analysis: documentAnalysis
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setStrategicQuestions(data.strategic_questions || []);
      } else {
        console.warn('Failed to fetch strategic questions, falling back to basic questions');
        setStrategicQuestions([]);
      }
    } catch (err) {
      console.warn('Error fetching strategic questions:', err);
      setStrategicQuestions([]);
    } finally {
      setLoadingQuestions(false);
    }
  };

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId);
    } else {
      newExpanded.add(sectionId);
    }
    setExpandedSections(newExpanded);
  };

  const renderPlainEnglishSummary = () => {
    if (!analysis?.plain_english_summary) return null;

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <Brain className="h-6 w-6 text-blue-600" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-blue-900 mb-3">
              What This Document Means (In Plain English)
            </h3>
            <div className="prose prose-blue max-w-none">
              <p className="text-blue-800 leading-relaxed">
                {analysis.plain_english_summary}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderPartiesTable = () => {
    if (!analysis?.parties_analysis?.parties) return null;

    return (
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900">Who's Who in This Document</h4>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Role
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  What They Want
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analysis.parties_analysis.parties.map((party: any, index: number) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {party.name}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {party.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {party.entity_type}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700">
                    {party.what_they_want}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderTimelineVisualization = () => {
    // Get dates from multiple sources for comprehensive display
    const timelineEvents = analysis?.timeline_analysis?.timeline_events || [];
    // Support both old field names (dates, deadlines) and new (all_dates, all_deadlines)
    const dates = analysis?.all_dates || analysis?.dates || [];
    const deadlines = analysis?.all_deadlines || analysis?.deadlines || [];
    const fiveWDates = analysis?.five_w_analysis?.when?.critical_dates || [];

    // Combine all date sources, preferring the most detailed version
    const allDates = [
      ...fiveWDates.map((d: any) => ({ ...d, source: '5w' })),
      ...dates.map((d: any) => ({
        date: d.date,
        event: d.event || d.description,
        // Support both old (significance) and new (why_important) field names
        why_important: d.why_important || d.significance,
        action_required: d.action_required,
        // Support both old (consequence) and new (consequence_if_missed) field names
        consequence_if_missed: d.consequence_if_missed || d.consequence,
        significance: d.significance,
        importance: d.urgency === 'HIGH' || d.urgency === 'CRITICAL' || d.urgency === 'high' ? 'High' : 'Normal',
        source: 'dates'
      })),
      ...deadlines.map((d: any) => ({
        date: d.deadline || d.date,
        event: d.action_required,
        // Support both old and new field names
        why_important: d.why_important || `This deadline requires: ${d.action_required}`,
        action_required: d.action_required,
        consequence_if_missed: d.consequence_if_missed || d.consequence,
        importance: d.urgency === 'CRITICAL' || d.urgency === 'HIGH' || d.urgency === 'high' ? 'High' : 'Normal',
        source: 'deadlines'
      })),
      ...timelineEvents.map((e: any) => ({
        date: e.date,
        event: e.event,
        why_important: e.why_important || e.significance,
        importance: e.importance,
        source: 'timeline'
      }))
    ];

    // Deduplicate by date
    const uniqueDates = allDates.reduce((acc: any[], curr: any) => {
      const existing = acc.find(d => d.date === curr.date);
      if (!existing) {
        acc.push(curr);
      } else if (curr.why_important && !existing.why_important) {
        // Replace with more detailed version
        const idx = acc.indexOf(existing);
        acc[idx] = { ...existing, ...curr };
      }
      return acc;
    }, []);

    if (uniqueDates.length === 0) return null;

    return (
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-4">Important Dates & Timeline</h4>
        <div className="space-y-4">
          {uniqueDates.map((event: any, index: number) => (
            <div key={index} className={`rounded-lg p-4 border-l-4 ${
              event.importance === 'High' || event.consequence_if_missed
                ? 'border-l-red-500 bg-red-50'
                : 'border-l-blue-500 bg-blue-50'
            }`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg font-bold text-gray-900">{event.date}</span>
                    {(event.importance === 'High' || event.consequence_if_missed) && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        <AlertTriangle className="h-3 w-3 mr-1" />
                        Critical
                      </span>
                    )}
                  </div>
                  <p className="text-sm font-medium text-gray-900 mt-1">
                    {event.event}
                  </p>
                </div>
              </div>

              {/* WHY This Date Matters - Enhanced Display */}
              <div className="mt-3 space-y-2">
                {event.why_important && (
                  <div className="flex items-start space-x-2">
                    <span className="inline-flex items-center justify-center w-20 px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 flex-shrink-0">
                      WHY
                    </span>
                    <p className="text-sm text-gray-700 flex-1">{event.why_important}</p>
                  </div>
                )}

                {event.action_required && (
                  <div className="flex items-start space-x-2">
                    <span className="inline-flex items-center justify-center w-20 px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800 flex-shrink-0">
                      ACTION
                    </span>
                    <p className="text-sm text-gray-700 flex-1">{event.action_required}</p>
                  </div>
                )}

                {event.consequence_if_missed && (
                  <div className="flex items-start space-x-2">
                    <span className="inline-flex items-center justify-center w-20 px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 flex-shrink-0">
                      RISK
                    </span>
                    <p className="text-sm text-red-700 flex-1 font-medium">{event.consequence_if_missed}</p>
                  </div>
                )}

                {/* Fallback for old data without why_important */}
                {!event.why_important && !event.action_required && event.significance && (
                  <div className="flex items-start space-x-2">
                    <span className="inline-flex items-center justify-center w-20 px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-800 flex-shrink-0">
                      NOTE
                    </span>
                    <p className="text-sm text-gray-600 flex-1">{event.significance}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderLegalTermsGlossary = () => {
    if (!analysis?.legal_terms?.terms_explained) return null;

    return (
      <div className="bg-white rounded-lg border border-gray-200">
        <div className="px-4 py-3 border-b border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900">Legal Terms Explained</h4>
          <p className="text-xs text-gray-500 mt-1">
            Hover over terms to see definitions
          </p>
        </div>
        <div className="p-4 space-y-3">
          {Object.entries(analysis.legal_terms.terms_explained).map(([term, info]: [string, any]) => (
            <div key={term} className="group relative">
              <div className="flex items-start space-x-3 p-3 rounded-lg border border-gray-200 hover:bg-gray-50 cursor-help">
                <BookOpen className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h5 className="text-sm font-medium text-gray-900 capitalize">
                      {term}
                    </h5>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      info.importance_level === 'high' ? 'bg-red-100 text-red-800' :
                      info.importance_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {info.importance_level}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 mt-1">
                    {info.plain_english || info.definition}
                  </p>
                  {info.why_it_matters && (
                    <p className="text-xs text-gray-500 mt-1">
                      Why it matters: {info.why_it_matters}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderKeyFactsCards = () => {
    const facts = [];

    // Financial facts
    if (analysis?.financial_analysis?.payment_amounts?.length > 0) {
      facts.push({
        icon: <DollarSign className="h-5 w-5" />,
        title: "Financial Terms",
        value: analysis.financial_analysis.payment_amounts.join(", "),
        subtitle: `Frequency: ${analysis.financial_analysis.payment_frequency}`,
        color: "green"
      });
    }

    // Timeline facts
    if (analysis?.timeline_analysis?.total_dates > 0) {
      facts.push({
        icon: <Calendar className="h-5 w-5" />,
        title: "Important Dates",
        value: analysis.timeline_analysis.total_dates.toString(),
        subtitle: "Key dates identified",
        color: "blue"
      });
    }

    // Party facts
    if (analysis?.parties_analysis?.total_parties > 0) {
      facts.push({
        icon: <Users className="h-5 w-5" />,
        title: "Parties Involved",
        value: analysis.parties_analysis.total_parties.toString(),
        subtitle: analysis.parties_analysis.relationship_type || "Legal entities",
        color: "purple"
      });
    }

    // Risk level
    if (analysis?.risk_assessment?.overall_risk_level) {
      facts.push({
        icon: <Shield className="h-5 w-5" />,
        title: "Risk Level",
        value: analysis.risk_assessment.overall_risk_level,
        subtitle: `${analysis.risk_assessment.risk_count || 0} risks identified`,
        color: analysis.risk_assessment.overall_risk_level === "High" ? "red" :
               analysis.risk_assessment.overall_risk_level === "Medium" ? "yellow" : "green"
      });
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {facts.map((fact, index) => (
          <div key={index} className={`bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow`}>
            <div className="flex items-start space-x-3">
              <div className={`flex-shrink-0 p-2 rounded-lg ${
                fact.color === 'green' ? 'bg-green-100 text-green-600' :
                fact.color === 'blue' ? 'bg-blue-100 text-blue-600' :
                fact.color === 'purple' ? 'bg-purple-100 text-purple-600' :
                fact.color === 'red' ? 'bg-red-100 text-red-600' :
                fact.color === 'yellow' ? 'bg-yellow-100 text-yellow-600' :
                'bg-gray-100 text-gray-600'
              }`}>
                {fact.icon}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">{fact.title}</p>
                <p className="text-lg font-semibold text-gray-900 mt-1">{fact.value}</p>
                <p className="text-xs text-gray-500 mt-1">{fact.subtitle}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderWhatHappensNext = () => {
    if (!analysis?.next_steps) return null;

    return (
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <TrendingUp className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-amber-900 mb-2">
              What Happens Next
            </h4>
            <ul className="space-y-2">
              {analysis.next_steps.map((step: string, index: number) => (
                <li key={index} className="flex items-start space-x-2">
                  <CheckCircle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                  <span className="text-sm text-amber-800">{step}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    );
  };

  const renderQuestionsForAttorney = () => {
    // Fallback questions for basic document types
    const fallbackQuestions = [];

    if (analysis?.document_type === 'service_agreement') {
      fallbackQuestions.push(
        "Should I be concerned about the liability limitations in this contract?",
        "Are the payment terms favorable for my situation?",
        "What happens if I need to terminate this agreement early?",
        "Are there any unusual clauses I should be aware of?"
      );
    }

    if (analysis?.risk_assessment?.identified_risks?.length > 0) {
      fallbackQuestions.push("How can I mitigate the risks identified in this analysis?");
    }

    if (analysis?.timeline_analysis?.critical_deadlines?.length > 0) {
      fallbackQuestions.push("What are the consequences if I miss any of these deadlines?");
    }

    // Use strategic questions if available, otherwise fallback questions
    const questionsToShow = strategicQuestions.length > 0 ? strategicQuestions :
      fallbackQuestions.map(q => ({ question: q, category: 'general', importance: 'medium' }));

    // Group questions by category if using strategic questions
    const categorizedQuestions: Record<string, any[]> = {};
    if (strategicQuestions.length > 0) {
      questionsToShow.forEach((q: any) => {
        const category = q.category || 'general';
        if (!categorizedQuestions[category]) {
          categorizedQuestions[category] = [];
        }
        categorizedQuestions[category].push(q);
      });
    }

    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <MessageSquare className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-sm font-semibold text-blue-900">
                {strategicQuestions.length > 0 ? 'Strategic Questions for Your Attorney' : 'Questions to Ask Your Attorney'}
              </h4>
              {loadingQuestions && (
                <div className="flex items-center space-x-1">
                  <div className="animate-spin rounded-full h-3 w-3 border-b border-blue-600"></div>
                  <span className="text-xs text-blue-600">Generating...</span>
                </div>
              )}
            </div>

            {strategicQuestions.length > 0 ? (
              <div className="space-y-4">
                {Object.entries(categorizedQuestions).map(([category, questions]: [string, any[]]) => (
                  <div key={category} className="space-y-2">
                    <h5 className="text-xs font-semibold text-blue-800 uppercase tracking-wide">
                      {category.replace('_', ' ')}
                    </h5>
                    <ul className="space-y-2">
                      {questions.map((q, index) => (
                        <li key={index} className="flex items-start space-x-2">
                          <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                            q.importance === 'high' ? 'bg-red-500' :
                            q.importance === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                          }`} />
                          <div className="flex-1">
                            <p className="text-sm text-blue-800">{q.question}</p>
                            {q.explanation && (
                              <p className="text-xs text-blue-600 mt-1 italic">{q.explanation}</p>
                            )}
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
                <div className="bg-amber-50 border border-amber-200 rounded p-2 mt-3">
                  <p className="text-xs text-amber-700">
                    <strong>Harvard-level Analysis:</strong> These questions are generated using advanced legal analysis
                    to identify potential gaps and strategic opportunities in your document.
                  </p>
                </div>
              </div>
            ) : (
              <ul className="space-y-2">
                {questionsToShow.map((q, index) => (
                  <li key={index} className="text-sm text-blue-800">
                    • {q.question}
                  </li>
                ))}
              </ul>
            )}

            <p className="text-xs text-blue-600 mt-3 italic">
              Remember: This analysis is for educational purposes only. Always consult with a qualified attorney for legal advice.
            </p>
          </div>
        </div>
      </div>
    );
  };

  const renderEducationalResources = () => {
    const resources = [
      {
        title: "Understanding Legal Contracts",
        description: "Learn the basics of contract law and key terms",
        url: "#",
        category: "Contracts"
      },
      {
        title: "Your Rights and Obligations",
        description: "Know what you're agreeing to in legal documents",
        url: "#",
        category: "Legal Rights"
      },
      {
        title: "When to Consult an Attorney",
        description: "Understand when professional legal help is essential",
        url: "#",
        category: "Legal Advice"
      }
    ];

    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Lightbulb className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-green-900 mb-3">
              Educational Resources
            </h4>
            <div className="space-y-3">
              {resources.map((resource, index) => (
                <div key={index} className="flex items-start space-x-3 p-2 bg-white rounded border border-green-200">
                  <div className="flex-1">
                    <h5 className="text-sm font-medium text-green-900">
                      {resource.title}
                    </h5>
                    <p className="text-xs text-green-700 mt-1">
                      {resource.description}
                    </p>
                    <span className="inline-flex items-center px-1.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 mt-1">
                      {resource.category}
                    </span>
                  </div>
                  <ExternalLink className="h-4 w-4 text-green-600 flex-shrink-0" />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // ============================================
  // 5W ANALYSIS SECTIONS - WHO/WHAT/WHEN/WHERE/WHY
  // ============================================

  const renderFiveWOverview = () => {
    const fiveW = analysis?.five_w_analysis;
    if (!fiveW) return null;

    return (
      <div className="bg-gradient-to-br from-indigo-50 to-purple-50 border border-indigo-200 rounded-lg p-6">
        <div className="flex items-start space-x-3 mb-4">
          <Brain className="h-6 w-6 text-indigo-600" />
          <div>
            <h3 className="text-lg font-semibold text-indigo-900">
              Document Analysis: The 5 Key Questions
            </h3>
            <p className="text-sm text-indigo-700 mt-1">
              Understanding your document through the essential questions every client should know
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mt-4">
          {/* WHO */}
          <div className="bg-white rounded-lg p-4 border border-blue-200 hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                <Users className="h-4 w-4 text-blue-600" />
              </div>
              <h4 className="font-semibold text-blue-900">WHO</h4>
            </div>
            <p className="text-xs text-gray-600">
              {fiveW.who?.parties_summary || "Parties involved in this matter"}
            </p>
          </div>

          {/* WHAT */}
          <div className="bg-white rounded-lg p-4 border border-green-200 hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                <FileText className="h-4 w-4 text-green-600" />
              </div>
              <h4 className="font-semibold text-green-900">WHAT</h4>
            </div>
            <p className="text-xs text-gray-600">
              {fiveW.what?.core_issue || "The main issue or dispute"}
            </p>
          </div>

          {/* WHEN */}
          <div className="bg-white rounded-lg p-4 border border-amber-200 hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
                <Calendar className="h-4 w-4 text-amber-600" />
              </div>
              <h4 className="font-semibold text-amber-900">WHEN</h4>
            </div>
            <p className="text-xs text-gray-600">
              {fiveW.when?.critical_dates?.length ? `${fiveW.when.critical_dates.length} critical dates` : "Key dates and deadlines"}
            </p>
          </div>

          {/* WHERE */}
          <div className="bg-white rounded-lg p-4 border border-purple-200 hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                <MapPin className="h-4 w-4 text-purple-600" />
              </div>
              <h4 className="font-semibold text-purple-900">WHERE</h4>
            </div>
            <p className="text-xs text-gray-600">
              {fiveW.where?.venue || "Jurisdiction and venue"}
            </p>
          </div>

          {/* WHY */}
          <div className="bg-white rounded-lg p-4 border border-red-200 hover:shadow-md transition-shadow">
            <div className="flex items-center space-x-2 mb-2">
              <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                <QuestionMark className="h-4 w-4 text-red-600" />
              </div>
              <h4 className="font-semibold text-red-900">WHY</h4>
            </div>
            <p className="text-xs text-gray-600">
              {fiveW.why?.root_cause || "The underlying reason for this matter"}
            </p>
          </div>
        </div>
      </div>
    );
  };

  const renderWhoSection = () => {
    const who = analysis?.five_w_analysis?.who;
    if (!who) return null;

    return (
      <div className="bg-white rounded-lg border border-blue-200 overflow-hidden">
        <div className="bg-blue-50 px-4 py-3 border-b border-blue-200">
          <div className="flex items-center space-x-2">
            <Users className="h-5 w-5 text-blue-600" />
            <h4 className="font-semibold text-blue-900">WHO Is Involved</h4>
          </div>
          <p className="text-sm text-blue-700 mt-1">{who.parties_summary}</p>
        </div>

        <div className="p-4">
          {/* Key Actors Table */}
          {who.key_actors?.length > 0 && (
            <div className="mb-4">
              <h5 className="text-sm font-medium text-gray-900 mb-2">Key Parties</h5>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Interest</th>
                      <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Relationship</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {who.key_actors.map((actor: any, idx: number) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-3 py-2 text-sm font-medium text-gray-900">{actor.name}</td>
                        <td className="px-3 py-2 text-sm text-gray-700">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {actor.role}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-sm text-gray-700">{actor.interest}</td>
                        <td className="px-3 py-2 text-sm text-gray-600">{actor.relationship}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Decision Makers */}
          {who.decision_makers?.length > 0 && (
            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Gavel className="h-4 w-4 text-blue-600" />
                <h5 className="text-sm font-medium text-blue-900">Decision Makers</h5>
              </div>
              <div className="flex flex-wrap gap-2">
                {who.decision_makers.map((dm: string, idx: number) => (
                  <span key={idx} className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-200 text-blue-900">
                    {dm}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderWhatSection = () => {
    const what = analysis?.five_w_analysis?.what;
    if (!what) return null;

    return (
      <div className="bg-white rounded-lg border border-green-200 overflow-hidden">
        <div className="bg-green-50 px-4 py-3 border-b border-green-200">
          <div className="flex items-center space-x-2">
            <FileText className="h-5 w-5 text-green-600" />
            <h4 className="font-semibold text-green-900">WHAT Is This About</h4>
          </div>
        </div>

        <div className="p-4 space-y-4">
          {/* Core Issue - Most Important */}
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <h5 className="text-sm font-medium text-green-900 mb-2 flex items-center">
              <Target className="h-4 w-4 mr-2" />
              The Core Issue
            </h5>
            <p className="text-base text-green-800 font-medium">{what.core_issue}</p>
          </div>

          {/* Document Purpose */}
          <div>
            <h5 className="text-sm font-medium text-gray-900 mb-2">Document Purpose</h5>
            <p className="text-sm text-gray-700">{what.document_purpose}</p>
          </div>

          {/* Relief Sought */}
          {what.relief_sought && (
            <div className="bg-amber-50 rounded-lg p-3 border border-amber-200">
              <h5 className="text-sm font-medium text-amber-900 mb-2 flex items-center">
                <DollarSign className="h-4 w-4 mr-2" />
                What Is Being Requested
              </h5>
              <p className="text-sm text-amber-800">{what.relief_sought}</p>
            </div>
          )}

          {/* Key Arguments */}
          {what.key_arguments?.length > 0 && (
            <div>
              <h5 className="text-sm font-medium text-gray-900 mb-2">Key Arguments</h5>
              <ul className="space-y-2">
                {what.key_arguments.map((arg: string, idx: number) => (
                  <li key={idx} className="flex items-start space-x-2">
                    <ArrowRight className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-gray-700">{arg}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Disputed Facts */}
          {what.disputed_facts?.length > 0 && (
            <div className="bg-red-50 rounded-lg p-3 border border-red-200">
              <h5 className="text-sm font-medium text-red-900 mb-2 flex items-center">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Disputed Facts
              </h5>
              <ul className="space-y-1">
                {what.disputed_facts.map((fact: string, idx: number) => (
                  <li key={idx} className="text-sm text-red-800">• {fact}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderWhenSection = () => {
    const when = analysis?.five_w_analysis?.when;
    if (!when) return null;

    return (
      <div className="bg-white rounded-lg border border-amber-200 overflow-hidden">
        <div className="bg-amber-50 px-4 py-3 border-b border-amber-200">
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-amber-600" />
            <h4 className="font-semibold text-amber-900">WHEN - Critical Dates & Why They Matter</h4>
          </div>
          {when.timeline_summary && (
            <p className="text-sm text-amber-700 mt-1">{when.timeline_summary}</p>
          )}
        </div>

        <div className="p-4">
          {/* Critical Dates with Enhanced Explanations */}
          {when.critical_dates?.length > 0 && (
            <div className="space-y-4">
              {when.critical_dates.map((dateItem: any, idx: number) => (
                <div key={idx} className={`rounded-lg p-4 border-l-4 ${
                  dateItem.consequence_if_missed?.toLowerCase().includes('dismiss') ||
                  dateItem.consequence_if_missed?.toLowerCase().includes('waive') ||
                  dateItem.consequence_if_missed?.toLowerCase().includes('default')
                    ? 'border-l-red-500 bg-red-50'
                    : 'border-l-amber-500 bg-amber-50'
                }`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-lg font-bold text-gray-900">{dateItem.date}</span>
                        {dateItem.consequence_if_missed && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Critical
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-gray-900 mt-1">{dateItem.event}</p>
                    </div>
                  </div>

                  {/* WHY This Date Matters */}
                  <div className="mt-3 space-y-2">
                    {dateItem.why_important && (
                      <div className="flex items-start space-x-2">
                        <span className="inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">
                          WHY
                        </span>
                        <p className="text-sm text-gray-700 flex-1">{dateItem.why_important}</p>
                      </div>
                    )}

                    {dateItem.action_required && (
                      <div className="flex items-start space-x-2">
                        <span className="inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800">
                          ACTION
                        </span>
                        <p className="text-sm text-gray-700 flex-1">{dateItem.action_required}</p>
                      </div>
                    )}

                    {dateItem.consequence_if_missed && (
                      <div className="flex items-start space-x-2">
                        <span className="inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800">
                          RISK
                        </span>
                        <p className="text-sm text-red-700 flex-1 font-medium">{dateItem.consequence_if_missed}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Statute of Limitations */}
          {when.statute_of_limitations && (
            <div className="mt-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center space-x-2 mb-1">
                <Clock className="h-4 w-4 text-purple-600" />
                <h5 className="text-sm font-medium text-purple-900">Statute of Limitations</h5>
              </div>
              <p className="text-sm text-purple-800">{when.statute_of_limitations}</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderWhereSection = () => {
    const where = analysis?.five_w_analysis?.where;
    if (!where) return null;

    return (
      <div className="bg-white rounded-lg border border-purple-200 overflow-hidden">
        <div className="bg-purple-50 px-4 py-3 border-b border-purple-200">
          <div className="flex items-center space-x-2">
            <MapPin className="h-5 w-5 text-purple-600" />
            <h4 className="font-semibold text-purple-900">WHERE - Jurisdiction & Venue</h4>
          </div>
        </div>

        <div className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {where.venue && (
              <div className="bg-purple-50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <Gavel className="h-4 w-4 text-purple-600" />
                  <h5 className="text-sm font-medium text-purple-900">Court/Venue</h5>
                </div>
                <p className="text-sm text-purple-800">{where.venue}</p>
              </div>
            )}

            {where.jurisdiction && (
              <div className="bg-purple-50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <Scale className="h-4 w-4 text-purple-600" />
                  <h5 className="text-sm font-medium text-purple-900">Jurisdiction</h5>
                </div>
                <p className="text-sm text-purple-800">{where.jurisdiction}</p>
              </div>
            )}

            {where.applicable_law && (
              <div className="bg-purple-50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <BookOpen className="h-4 w-4 text-purple-600" />
                  <h5 className="text-sm font-medium text-purple-900">Applicable Law</h5>
                </div>
                <p className="text-sm text-purple-800">{where.applicable_law}</p>
              </div>
            )}

            {where.filing_location && (
              <div className="bg-purple-50 rounded-lg p-3">
                <div className="flex items-center space-x-2 mb-2">
                  <FileText className="h-4 w-4 text-purple-600" />
                  <h5 className="text-sm font-medium text-purple-900">Filing Location</h5>
                </div>
                <p className="text-sm text-purple-800">{where.filing_location}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderWhySection = () => {
    const why = analysis?.five_w_analysis?.why;
    if (!why) return null;

    return (
      <div className="bg-white rounded-lg border border-red-200 overflow-hidden">
        <div className="bg-red-50 px-4 py-3 border-b border-red-200">
          <div className="flex items-center space-x-2">
            <QuestionMark className="h-5 w-5 text-red-600" />
            <h4 className="font-semibold text-red-900">WHY - Understanding the Underlying Issues</h4>
          </div>
        </div>

        <div className="p-4 space-y-4">
          {/* Root Cause */}
          {why.root_cause && (
            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <h5 className="text-sm font-medium text-red-900 mb-2">Root Cause</h5>
              <p className="text-sm text-red-800">{why.root_cause}</p>
            </div>
          )}

          {/* Legal Basis */}
          {why.legal_basis && (
            <div>
              <h5 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                <Scale className="h-4 w-4 mr-2 text-gray-600" />
                Legal Basis
              </h5>
              <p className="text-sm text-gray-700">{why.legal_basis}</p>
            </div>
          )}

          {/* Motivation */}
          {why.motivation && (
            <div>
              <h5 className="text-sm font-medium text-gray-900 mb-2">Party Motivations</h5>
              <p className="text-sm text-gray-700">{why.motivation}</p>
            </div>
          )}

          {/* Strategic Implications */}
          {why.strategic_implications && (
            <div className="bg-amber-50 rounded-lg p-3 border border-amber-200">
              <h5 className="text-sm font-medium text-amber-900 mb-2 flex items-center">
                <Target className="h-4 w-4 mr-2" />
                Strategic Implications
              </h5>
              <p className="text-sm text-amber-800">{why.strategic_implications}</p>
            </div>
          )}

          {/* Client Impact - Most Important */}
          {why.client_impact && (
            <div className="bg-blue-50 rounded-lg p-4 border-2 border-blue-300">
              <h5 className="text-sm font-semibold text-blue-900 mb-2 flex items-center">
                <Brain className="h-4 w-4 mr-2" />
                What This Means For You
              </h5>
              <p className="text-base text-blue-800">{why.client_impact}</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-2 text-gray-600">Analyzing document with AI...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-red-600" />
          <span className="text-red-800">Error loading AI analysis: {error}</span>
        </div>
        <button
          onClick={fetchAIAnalysis}
          className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
        >
          Retry Analysis
        </button>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <Brain className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No AI analysis available</p>
        <button
          onClick={fetchAIAnalysis}
          className="mt-2 px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Run AI Analysis
        </button>
      </div>
    );
  }

  // 5W Sections - always show when analysis contains five_w_analysis
  const fiveWSections: ExpandableSection[] = analysis?.five_w_analysis ? [
    {
      id: '5w-who',
      title: 'WHO Is Involved',
      icon: <Users className="h-5 w-5 text-blue-600" />,
      content: renderWhoSection(),
    },
    {
      id: '5w-what',
      title: 'WHAT Is This About',
      icon: <FileText className="h-5 w-5 text-green-600" />,
      content: renderWhatSection(),
    },
    {
      id: '5w-when',
      title: 'WHEN - Critical Dates',
      icon: <Calendar className="h-5 w-5 text-amber-600" />,
      content: renderWhenSection(),
      urgent: true,
    },
    {
      id: '5w-where',
      title: 'WHERE - Jurisdiction',
      icon: <MapPin className="h-5 w-5 text-purple-600" />,
      content: renderWhereSection(),
    },
    {
      id: '5w-why',
      title: 'WHY - Root Cause',
      icon: <QuestionMark className="h-5 w-5 text-red-600" />,
      content: renderWhySection(),
    },
  ] : [];

  const expandableSections: ExpandableSection[] = [
    {
      id: 'summary',
      title: 'Document Summary',
      icon: <FileText className="h-5 w-5" />,
      content: renderPlainEnglishSummary(),
    },
    // Insert 5W sections here if available
    ...fiveWSections,
    {
      id: 'parties',
      title: 'All Parties Details',
      icon: <Users className="h-5 w-5" />,
      content: renderPartiesTable(),
    },
    {
      id: 'timeline',
      title: 'Full Timeline',
      icon: <Calendar className="h-5 w-5" />,
      content: renderTimelineVisualization(),
    },
    {
      id: 'legal-terms',
      title: 'Legal Terms Explained',
      icon: <BookOpen className="h-5 w-5" />,
      content: renderLegalTermsGlossary(),
    },
    {
      id: 'next-steps',
      title: 'What Happens Next',
      icon: <TrendingUp className="h-5 w-5" />,
      content: renderWhatHappensNext(),
    },
    {
      id: 'attorney-questions',
      title: 'Questions for Your Attorney',
      icon: <MessageSquare className="h-5 w-5" />,
      content: renderQuestionsForAttorney(),
    },
    {
      id: 'resources',
      title: 'Educational Resources',
      icon: <Lightbulb className="h-5 w-5" />,
      content: renderEducationalResources(),
    }
  ];

  return (
    <div className="space-y-6">
      {/* AI Analysis Warning */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-amber-800 mb-1">
              AI-Generated Analysis - Educational Purposes Only
            </h3>
            <p className="text-sm text-amber-700">
              This analysis is generated by AI to help you understand legal documents.
              It is for educational purposes only and does not constitute legal advice.
              Always consult with a qualified attorney for legal guidance.
            </p>
          </div>
        </div>
      </div>

      {/* Key Facts Cards */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Facts at a Glance</h2>
        {renderKeyFactsCards()}
      </div>

      {/* 5W Analysis Overview - Show prominently when available */}
      {analysis?.five_w_analysis && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Understanding Your Document: The 5 Essential Questions</h2>
          {renderFiveWOverview()}
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowEducationalSidebar(!showEducationalSidebar)}
            className="inline-flex items-center px-3 py-2 border border-blue-600 text-sm font-medium rounded-md text-blue-600 bg-white hover:bg-blue-50"
          >
            <HelpCircle className="h-4 w-4 mr-2" />
            Learn More
          </button>
          <button className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
            <Download className="h-4 w-4 mr-2" />
            Print Analysis
          </button>
        </div>
        <button className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700">
          <Save className="h-4 w-4 mr-2" />
          Save Analysis
        </button>
      </div>

      {/* Expandable Analysis Sections */}
      <div className="space-y-4">
        {expandableSections.map((section) => (
          <div key={section.id} className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center space-x-3">
                <div className="text-gray-600">
                  {section.icon}
                </div>
                <h3 className="text-sm font-semibold text-gray-900">
                  {section.title}
                </h3>
                {section.urgent && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    <AlertTriangle className="h-3 w-3 mr-1" />
                    Urgent
                  </span>
                )}
              </div>
              {expandedSections.has(section.id) ? (
                <ChevronDown className="h-5 w-5 text-gray-400" />
              ) : (
                <ChevronRight className="h-5 w-5 text-gray-400" />
              )}
            </button>

            {expandedSections.has(section.id) && (
              <div className="p-4">
                {section.content}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Educational Disclaimer */}
      <div className="bg-legal-50 border border-legal-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Scale className="h-5 w-5 text-legal-600 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold text-legal-900 mb-2">
              Important Legal Disclaimer
            </h3>
            <div className="text-sm text-legal-700 space-y-1">
              <p>• This AI analysis is for educational purposes only and does not constitute legal advice</p>
              <p>• The analysis may contain errors or omissions - always verify important information</p>
              <p>• Consult with a qualified attorney before making any legal decisions</p>
              <p>• AI-generated content should not be relied upon for legal or business decisions</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComprehensiveAnalysisDisplay;