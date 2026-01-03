'use client';

import React, { useState } from 'react';
import {
  HelpCircle,
  Send,
  Clock,
  AlertTriangle,
  Info,
  Scale,
  CheckCircle,
  User,
  MessageSquare,
  FileText,
  Shield,
  ExternalLink,
  X
} from 'lucide-react';

interface Question {
  id: string;
  category: string;
  question: string;
  urgency: 'low' | 'medium' | 'high';
  submittedAt: string;
  status: 'submitted' | 'under-review' | 'answered' | 'follow-up-needed';
  response?: string;
  respondedBy?: string;
  respondedAt?: string;
  isPrivileged: boolean;
}

interface QuestionForm {
  category: string;
  question: string;
  urgency: 'low' | 'medium' | 'high';
  backgroundInfo: string;
  specificDeadline: string;
}

interface QuestionSubmissionProps {
  className?: string;
}

const QuestionSubmission: React.FC<QuestionSubmissionProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState<'submit' | 'history'>('submit');
  const [questionForm, setQuestionForm] = useState<QuestionForm>({
    category: '',
    question: '',
    urgency: 'medium',
    backgroundInfo: '',
    specificDeadline: ''
  });
  const [showPrivilegeWarning, setShowPrivilegeWarning] = useState(true);
  const [expandedQuestion, setExpandedQuestion] = useState<string | null>(null);

  // Mock data - would come from API
  const previousQuestions: Question[] = [
    {
      id: '1',
      category: 'Case Timeline',
      question: 'What are the next steps in my case and when can I expect updates?',
      urgency: 'medium',
      submittedAt: '2024-01-15T14:30:00Z',
      status: 'answered',
      response: 'Based on our current case timeline, the next steps include completing discovery (expected by February 15) and then moving to settlement discussions. I will provide updates bi-weekly and immediately if any significant developments occur. Please note this is general information about typical case progression.',
      respondedBy: 'Sarah Johnson, Esq.',
      respondedAt: '2024-01-16T10:15:00Z',
      isPrivileged: false
    },
    {
      id: '2',
      category: 'Document Question',
      question: 'Do I need to provide additional medical records from my previous injury?',
      urgency: 'high',
      submittedAt: '2024-01-14T09:20:00Z',
      status: 'under-review',
      isPrivileged: false
    }
  ];

  const questionCategories = [
    {
      value: 'case-status',
      label: 'Case Status & Timeline',
      description: 'Questions about case progress and next steps',
      examples: ['When will my case be resolved?', 'What stage is my case in?']
    },
    {
      value: 'documents',
      label: 'Document Questions', 
      description: 'Questions about documents you\'ve received or need to provide',
      examples: ['What does this document mean?', 'Do I need to provide additional records?']
    },
    {
      value: 'court-process',
      label: 'Court Process',
      description: 'Questions about court procedures and what to expect',
      examples: ['What happens at a deposition?', 'How should I prepare for court?']
    },
    {
      value: 'settlement',
      label: 'Settlement & Negotiations',
      description: 'Questions about settlement discussions and offers',
      examples: ['Should I accept this offer?', 'How is settlement value determined?']
    },
    {
      value: 'fees-costs',
      label: 'Fees & Costs',
      description: 'Questions about legal fees and case expenses',
      examples: ['What are my total costs?', 'When are fees due?']
    },
    {
      value: 'general',
      label: 'General Legal Questions',
      description: 'Other questions about your legal matter',
      examples: ['What are my rights?', 'What options do I have?']
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'submitted':
        return 'bg-blue-100 text-blue-800';
      case 'under-review':
        return 'bg-yellow-100 text-yellow-800';
      case 'answered':
        return 'bg-success-100 text-success-800';
      case 'follow-up-needed':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high':
        return 'bg-error-100 text-error-800 border-error-200';
      case 'medium':
        return 'bg-warning-100 text-warning-800 border-warning-200';
      case 'low':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleSubmitQuestion = () => {
    console.log('Submitting question:', questionForm);
    // Reset form
    setQuestionForm({
      category: '',
      question: '',
      urgency: 'medium',
      backgroundInfo: '',
      specificDeadline: ''
    });
    alert('Question submitted successfully for attorney review. You will receive a response within 1-2 business days.');
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center space-x-2 mb-4">
        <HelpCircle className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-medium text-gray-900">Questions for Attorney Review</h3>
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <Info className="h-3 w-3 mr-1" />
          For Review Only
        </span>
      </div>

      {/* Privilege Warning */}
      {showPrivilegeWarning && (
        <div className="mb-6 bg-error-50 border border-error-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-error-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-error-900 mb-2">
                Important: Attorney-Client Privilege Notice
              </h4>
              <div className="text-sm text-error-800 space-y-1">
                <p>
                  <strong>Questions submitted here are FOR ATTORNEY REVIEW ONLY</strong> and may not be protected 
                  by attorney-client privilege unless you have a signed representation agreement.
                </p>
                <p>
                  <strong>This is NOT legal advice:</strong> Responses provide general information and guidance, 
                  not specific legal advice for your situation.
                </p>
                <p>
                  <strong>For privileged communications:</strong> Schedule a consultation or call your attorney directly.
                </p>
              </div>
              <button
                onClick={() => setShowPrivilegeWarning(false)}
                className="mt-2 text-xs text-error-700 hover:text-error-800 font-medium underline"
              >
                I understand - Continue with question submission
              </button>
            </div>
            <button
              onClick={() => setShowPrivilegeWarning(false)}
              className="text-error-400 hover:text-error-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('submit')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'submit'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <MessageSquare className="h-4 w-4" />
            <span>Submit Question</span>
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'history'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <FileText className="h-4 w-4" />
            <span>Question History</span>
          </button>
        </div>
      </div>

      {/* Submit Question Tab */}
      {activeTab === 'submit' && (
        <div>
          <div className="mb-6">
            <p className="text-sm text-gray-600">
              Submit questions for your attorney to review. Responses typically provided within 1-2 business days.
              For urgent matters, please call the office directly.
            </p>
          </div>

          <form onSubmit={(e) => { e.preventDefault(); handleSubmitQuestion(); }} className="space-y-6">
            {/* Question Category */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Question Category
              </label>
              <div className="space-y-2">
                {questionCategories.map((category) => (
                  <label key={category.value} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="radio"
                      name="category"
                      value={category.value}
                      checked={questionForm.category === category.value}
                      onChange={(e) => setQuestionForm({...questionForm, category: e.target.value})}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{category.label}</div>
                      <div className="text-xs text-gray-600 mb-1">{category.description}</div>
                      <div className="text-xs text-gray-500">
                        Examples: {category.examples.join(', ')}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Question */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Your Question
              </label>
              <textarea
                value={questionForm.question}
                onChange={(e) => setQuestionForm({...questionForm, question: e.target.value})}
                placeholder="Please be as specific as possible in your question..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                rows={4}
                required
              />
            </div>

            {/* Background Information */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Background Information (Optional)
              </label>
              <textarea
                value={questionForm.backgroundInfo}
                onChange={(e) => setQuestionForm({...questionForm, backgroundInfo: e.target.value})}
                placeholder="Any additional context that might help your attorney provide a better response..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                rows={3}
              />
            </div>

            {/* Urgency Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Urgency Level
              </label>
              <div className="space-y-2">
                {[
                  { value: 'low', label: 'Low - General inquiry', desc: 'No immediate deadline, can wait for regular response time' },
                  { value: 'medium', label: 'Medium - Important', desc: 'Affects case progress but not time-critical' },
                  { value: 'high', label: 'High - Time-sensitive', desc: 'Related to upcoming deadline or court date' }
                ].map((urgency) => (
                  <label key={urgency.value} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="radio"
                      name="urgency"
                      value={urgency.value}
                      checked={questionForm.urgency === urgency.value}
                      onChange={(e) => setQuestionForm({...questionForm, urgency: e.target.value as any})}
                      className="mt-1"
                    />
                    <div>
                      <div className="text-sm font-medium text-gray-900">{urgency.label}</div>
                      <div className="text-xs text-gray-600">{urgency.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Specific Deadline */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Specific Deadline (Optional)
              </label>
              <input
                type="text"
                value={questionForm.specificDeadline}
                onChange={(e) => setQuestionForm({...questionForm, specificDeadline: e.target.value})}
                placeholder="If your question relates to a specific deadline, please mention it here..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={!questionForm.category || !questionForm.question}
              >
                <Send className="h-4 w-4 mr-2" />
                Submit for Review
              </button>
            </div>

            {/* Response Time Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-start space-x-2">
                <Clock className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-blue-900 mb-1">Expected Response Time</h5>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• <strong>Low urgency:</strong> 2-3 business days</li>
                    <li>• <strong>Medium urgency:</strong> 1-2 business days</li>
                    <li>• <strong>High urgency:</strong> Same day or next business day</li>
                    <li>• <strong>True emergencies:</strong> Call office directly at [phone number]</li>
                  </ul>
                </div>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Question History Tab */}
      {activeTab === 'history' && (
        <div>
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Review your previously submitted questions and attorney responses.
            </p>
          </div>

          {previousQuestions.length === 0 ? (
            <div className="text-center py-8">
              <MessageSquare className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No questions submitted yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {previousQuestions.map((q) => (
                <div key={q.id} className="border border-gray-200 rounded-lg">
                  <div
                    className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => setExpandedQuestion(expandedQuestion === q.id ? null : q.id)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-sm font-medium text-gray-900">{q.category}</span>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getUrgencyColor(q.urgency)}`}>
                            {q.urgency.toUpperCase()}
                          </span>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(q.status)}`}>
                            {q.status.replace('-', ' ').toUpperCase()}
                          </span>
                        </div>
                        
                        <p className="text-sm text-gray-700 mb-2">{q.question}</p>
                        
                        <div className="text-xs text-gray-500">
                          Submitted: {formatDate(q.submittedAt)}
                        </div>
                      </div>
                      
                      <div className="text-gray-400">
                        {expandedQuestion === q.id ? '−' : '+'}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Response */}
                  {expandedQuestion === q.id && (
                    <div className="border-t border-gray-200 p-4 bg-gray-50">
                      {q.response ? (
                        <div>
                          <div className="flex items-center space-x-2 mb-3">
                            <User className="h-4 w-4 text-green-600" />
                            <span className="text-sm font-medium text-green-900">Response from {q.respondedBy}</span>
                            <span className="text-xs text-gray-500">{formatDate(q.respondedAt!)}</span>
                          </div>
                          
                          <div className="bg-white border border-gray-200 rounded p-3 mb-3">
                            <p className="text-sm text-gray-700">{q.response}</p>
                          </div>

                          {!q.isPrivileged && (
                            <div className="bg-amber-50 border border-amber-200 rounded p-2">
                              <div className="flex items-start space-x-2">
                                <Info className="h-3 w-3 text-amber-600 mt-0.5 flex-shrink-0" />
                                <p className="text-xs text-amber-700">
                                  This response provides general information only and does not constitute legal advice 
                                  specific to your situation. For personalized legal advice, schedule a consultation.
                                </p>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="text-center py-4">
                          <Clock className="h-8 w-8 text-gray-300 mx-auto mb-2" />
                          <p className="text-sm text-gray-500">Response pending attorney review</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Important Guidelines */}
      <div className="mt-6 space-y-4">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-sm font-semibold text-amber-800 mb-2">Question Submission Guidelines</h5>
              <ul className="text-sm text-amber-700 space-y-1">
                <li>• Be as specific as possible in your questions</li>
                <li>• Include relevant context and background information</li>
                <li>• Do not include sensitive personal information unless necessary</li>
                <li>• For urgent matters requiring immediate attention, call the office</li>
                <li>• Follow up with additional questions if the response needs clarification</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="bg-legal-50 border border-legal-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Scale className="h-5 w-5 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-sm font-semibold text-legal-900 mb-2">Question Review Disclaimer</h5>
              <ul className="text-sm text-legal-700 space-y-1">
                <li>• Questions are reviewed for educational and informational purposes only</li>
                <li>• Responses do not create attorney-client relationships</li>
                <li>• Information provided is general and not specific legal advice</li>
                <li>• Confidentiality protection begins only with confirmed legal representation</li>
                <li>• For legal advice specific to your situation, schedule a consultation</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default QuestionSubmission;