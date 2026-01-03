'use client';

import React, { useState, useEffect } from 'react';
import {
  MessageSquare,
  Send,
  Brain,
  Lightbulb,
  AlertTriangle,
  Clock,
  User,
  Bot,
  Scale,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Target,
  HelpCircle
} from 'lucide-react';

interface SmartQASystemProps {
  documentAnalysis: any;
  documentText?: string;
  className?: string;
}

interface QAMessage {
  id: string;
  question: string;
  answer: string;
  timestamp: string;
  confidence: number;
  sources?: string[];
  followUpQuestions?: string[];
  suggestedQuestions?: string[];
}

interface StrategicQuestion {
  question: string;
  category: string;
  importance: 'high' | 'medium' | 'low';
  explanation?: string;
}

const SmartQASystem: React.FC<SmartQASystemProps> = ({
  documentAnalysis,
  documentText = '',
  className = ''
}) => {
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [conversation, setConversation] = useState<QAMessage[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [strategicQuestions, setStrategicQuestions] = useState<StrategicQuestion[]>([]);
  const [currentSuggestions, setCurrentSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingStrategic, setLoadingStrategic] = useState(false);
  const [expandedStrategic, setExpandedStrategic] = useState(false);

  useEffect(() => {
    // Generate session ID
    setSessionId(`session_${Date.now()}`);

    // Fetch strategic questions
    fetchStrategicQuestions();

    // Set initial quick-start questions based on document type
    if (documentAnalysis) {
      const initialQuestions = generateInitialQuestions(documentAnalysis);
      setCurrentSuggestions(initialQuestions);
    }
  }, [documentAnalysis]);

  const generateInitialQuestions = (analysis: any): string[] => {
    const docType = analysis.document_type?.toLowerCase() || '';
    const baseQuestions = [
      "What are the key deadlines in this document?",
      "What are my defense options?",
      "What evidence do I need to gather?",
      "What should I do immediately?",
      "What are the strongest arguments against this?"
    ];

    // Document-specific initial questions
    if (docType.includes('motion')) {
      return [
        "What is being requested in this motion?",
        "What is the deadline to respond to this motion?",
        "What evidence supports their motion?",
        "What defenses can I raise against this motion?",
        "What happens if I don't respond?"
      ];
    } else if (docType.includes('complaint') || docType.includes('petition')) {
      return [
        "What claims are being made against me?",
        "What damages are they seeking?",
        "When is my response due?",
        "What defenses might apply to my case?",
        "What evidence do they have?"
      ];
    } else if (docType.includes('summons')) {
      return [
        "How many days do I have to respond?",
        "What happens if I miss the deadline?",
        "What should my response include?",
        "Do I need to appear in court?",
        "Can I challenge the service of process?"
      ];
    } else if (docType.includes('order')) {
      return [
        "What does this order require me to do?",
        "By when must I comply?",
        "What happens if I don't comply?",
        "Can this order be appealed or modified?",
        "Do I need to respond to this order?"
      ];
    } else if (docType.includes('contract') || docType.includes('agreement')) {
      return [
        "What are my main obligations under this contract?",
        "What are the termination conditions?",
        "What are the penalties for breach?",
        "Can this agreement be modified?",
        "What notice requirements exist?"
      ];
    }

    return baseQuestions;
  };

  const fetchStrategicQuestions = async () => {
    if (!documentAnalysis) return;

    try {
      setLoadingStrategic(true);
      const response = await fetch('/api/v1/qa/strategic-questions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_analysis: documentAnalysis
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setStrategicQuestions(data.strategic_questions || []);
      }
    } catch (err) {
      console.warn('Error fetching strategic questions:', err);
    } finally {
      setLoadingStrategic(false);
    }
  };

  const askQuestion = async (question: string) => {
    if (!question.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('/api/v1/qa/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_text: documentText,
          document_analysis: documentAnalysis,
          question: question,
          session_id: sessionId
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const newMessage: QAMessage = {
          id: `qa_${Date.now()}`,
          question: question,
          answer: data.answer,
          timestamp: new Date().toISOString(),
          confidence: data.confidence,
          sources: data.sources,
          followUpQuestions: data.follow_up_questions,
          suggestedQuestions: data.suggested_questions
        };

        setConversation(prev => [...prev, newMessage]);
        setCurrentQuestion('');

        // ALWAYS update current suggestions with the latest from API
        // If no suggestions returned, keep showing previous ones
        if (data.suggested_questions && data.suggested_questions.length > 0) {
          setCurrentSuggestions(data.suggested_questions);
        } else if (currentSuggestions.length === 0 && documentAnalysis) {
          // Fallback: regenerate initial questions if none exist
          const fallbackQuestions = generateInitialQuestions(documentAnalysis);
          setCurrentSuggestions(fallbackQuestions);
        }
      } else {
        throw new Error('Failed to get answer');
      }
    } catch (err) {
      console.error('Error asking question:', err);
      // Add error message to conversation
      const errorMessage: QAMessage = {
        id: `error_${Date.now()}`,
        question: question,
        answer: "Sorry, I couldn't process your question at the moment. Please try again or contact support if the problem persists.",
        timestamp: new Date().toISOString(),
        confidence: 0,
      };
      setConversation(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    askQuestion(currentQuestion);
  };

  const handleStrategicQuestionClick = (question: string) => {
    setCurrentQuestion(question);
    askQuestion(question);
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const groupedStrategicQuestions = strategicQuestions.reduce((acc, question) => {
    const category = question.category || 'general';
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(question);
    return acc;
  }, {} as Record<string, StrategicQuestion[]>);

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <Brain className="h-5 w-5 text-blue-600" />
          <h3 className="text-lg font-medium text-gray-900">Smart Q&A System</h3>
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <Sparkles className="h-3 w-3 mr-1" />
            Harvard-Level Analysis
          </span>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50 border-b border-amber-200 p-3">
        <div className="flex items-start space-x-2">
          <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm text-amber-800">
              <strong>Educational Analysis:</strong> Responses provide information to help you understand
              legal documents but do not constitute legal advice. Consult with a qualified attorney for legal guidance.
            </p>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Strategic Questions Section */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg">
          <button
            onClick={() => setExpandedStrategic(!expandedStrategic)}
            className="w-full flex items-center justify-between p-3 hover:bg-blue-100 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <Target className="h-4 w-4 text-blue-600" />
              <span className="text-sm font-medium text-blue-900">
                Strategic Questions ({strategicQuestions.length})
              </span>
              {loadingStrategic && (
                <div className="animate-spin rounded-full h-3 w-3 border-b border-blue-600"></div>
              )}
            </div>
            {expandedStrategic ? (
              <ChevronUp className="h-4 w-4 text-blue-600" />
            ) : (
              <ChevronDown className="h-4 w-4 text-blue-600" />
            )}
          </button>

          {expandedStrategic && (
            <div className="px-3 pb-3 space-y-3">
              <p className="text-xs text-blue-700">
                These questions are generated using Harvard-level legal analysis to identify gaps and opportunities:
              </p>

              {Object.entries(groupedStrategicQuestions).map(([category, questions]) => (
                <div key={category} className="space-y-2">
                  <h4 className="text-xs font-semibold text-blue-800 uppercase tracking-wide">
                    {category.replace('_', ' ')}
                  </h4>
                  <div className="space-y-1">
                    {questions.map((q, index) => (
                      <button
                        key={index}
                        onClick={() => handleStrategicQuestionClick(q.question)}
                        className="w-full text-left p-2 bg-white border border-blue-200 rounded hover:bg-blue-50 transition-colors"
                        disabled={loading}
                      >
                        <div className="flex items-start space-x-2">
                          <div className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                            q.importance === 'high' ? 'bg-red-500' :
                            q.importance === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                          }`} />
                          <div className="flex-1">
                            <p className="text-sm text-blue-800">{q.question}</p>
                            {q.explanation && (
                              <p className="text-xs text-blue-600 mt-1">{q.explanation}</p>
                            )}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Conversation History */}
        {conversation.length > 0 && (
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {conversation.map((message) => (
              <div key={message.id} className="space-y-3">
                {/* Question */}
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1 bg-blue-50 rounded-lg p-3">
                    <p className="text-sm text-blue-900 font-medium">{message.question}</p>
                    <p className="text-xs text-blue-600 mt-1">{formatTimestamp(message.timestamp)}</p>
                  </div>
                </div>

                {/* Answer */}
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <Bot className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="flex-1 bg-gray-50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-gray-500">Harvard Lawyer Analysis</span>
                      <span className={`text-xs font-medium ${getConfidenceColor(message.confidence)}`}>
                        {Math.round(message.confidence * 100)}% confidence
                      </span>
                    </div>
                    <p className="text-sm text-gray-800">{message.answer}</p>

                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <p className="text-xs text-gray-500 mb-1">Sources:</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {message.sources.map((source, index) => (
                            <li key={index}>• {source}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {message.followUpQuestions && message.followUpQuestions.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-gray-200">
                        <p className="text-xs text-gray-500 mb-2">Suggested follow-up questions:</p>
                        <div className="space-y-1">
                          {message.followUpQuestions.map((followUp, index) => (
                            <button
                              key={index}
                              onClick={() => handleStrategicQuestionClick(followUp)}
                              className="block text-xs text-blue-600 hover:text-blue-800 hover:underline"
                              disabled={loading}
                            >
                              {followUp}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Persistent Quick-Start Questions - ALWAYS VISIBLE */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-lg p-4 shadow-md">
          <div className="flex items-center space-x-2 mb-3">
            <Lightbulb className="h-5 w-5 text-blue-600 animate-pulse" />
            <h4 className="text-sm font-semibold text-blue-900">
              Quick-Start Questions
              <span className="ml-2 text-xs font-normal text-blue-700">
                (Click to ask instantly)
              </span>
            </h4>
          </div>
          <div className="grid grid-cols-1 gap-2">
            {currentSuggestions.length > 0 ? (
              currentSuggestions.map((suggestion, index) => (
                <button
                  key={`suggestion-${index}`}
                  onClick={() => {
                    setCurrentQuestion(suggestion);
                    askQuestion(suggestion);
                  }}
                  disabled={loading}
                  className="text-left p-3 bg-white border border-blue-200 rounded-lg hover:bg-blue-50 hover:border-blue-500 hover:shadow-md transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm group"
                >
                  <div className="flex items-start space-x-2">
                    <HelpCircle className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0 group-hover:text-blue-700" />
                    <span className="text-sm text-blue-800 font-medium group-hover:text-blue-900">{suggestion}</span>
                  </div>
                </button>
              ))
            ) : (
              <div className="text-center py-4 text-sm text-blue-600">
                Loading questions...
              </div>
            )}
          </div>
          <div className="mt-3 pt-3 border-t border-blue-200">
            <p className="text-xs text-blue-700 font-medium">
              💡 <strong>These questions update automatically</strong> as you ask more questions,
              ensuring you always have relevant follow-up options specific to your document and conversation.
            </p>
          </div>
        </div>

        {/* Question Input */}
        <form onSubmit={handleQuestionSubmit} className="space-y-3">
          <div className="flex space-x-2">
            <input
              type="text"
              value={currentQuestion}
              onChange={(e) => setCurrentQuestion(e.target.value)}
              placeholder="Ask a question about this document..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !currentQuestion.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b border-white"></div>
              ) : (
                <Send className="h-4 w-4" />
              )}
              <span>Ask</span>
            </button>
          </div>

          {/* Loading indicator */}
          {loading && (
            <div className="flex items-center space-x-2 text-blue-600">
              <Clock className="h-4 w-4" />
              <span className="text-sm">Harvard lawyer is analyzing your question...</span>
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-legal-700">
                <strong>Important:</strong> This AI analysis uses Harvard-level legal reasoning but is for educational purposes only.
                Responses help you understand documents but do not constitute legal advice. Always consult with a qualified attorney.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SmartQASystem;