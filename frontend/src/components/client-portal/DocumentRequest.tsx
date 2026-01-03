'use client';

import React, { useState } from 'react';
import {
  FileText,
  Calendar,
  AlertTriangle,
  Clock,
  Info,
  Scale,
  Send,
  Plus,
  X,
  CheckCircle,
  Upload,
  Shield,
  ExternalLink
} from 'lucide-react';

interface DocumentRequest {
  id: string;
  title: string;
  description: string;
  requestedBy: string;
  dueDate: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  documentTypes: string[];
  instructions: string[];
  status: 'pending' | 'in_progress' | 'completed' | 'overdue';
  relatedTo: string;
  legalImportance: string;
}

interface NewRequest {
  documentType: string;
  description: string;
  urgency: 'routine' | 'important' | 'urgent';
  context: string;
}

interface DocumentRequestProps {
  className?: string;
}

const DocumentRequest: React.FC<DocumentRequestProps> = ({ className = '' }) => {
  const [activeTab, setActiveTab] = useState<'requests' | 'submit'>('requests');
  const [expandedRequest, setExpandedRequest] = useState<string | null>(null);
  const [newRequest, setNewRequest] = useState<NewRequest>({
    documentType: '',
    description: '',
    urgency: 'routine',
    context: ''
  });

  // Mock data - would come from API
  const documentRequests: DocumentRequest[] = [
    {
      id: '1',
      title: 'Medical Records Request',
      description: 'We need your complete medical records related to the incident from January 2024',
      requestedBy: 'Sarah Johnson, Esq.',
      dueDate: '2024-02-01T17:00:00Z',
      priority: 'high',
      documentTypes: [
        'Emergency room records',
        'Doctor visit notes',
        'Prescription records',
        'Physical therapy reports',
        'Any specialist consultations'
      ],
      instructions: [
        'Contact your healthcare providers to request records',
        'Sign medical release forms as needed',
        'Organize records chronologically',
        'Make copies for your own records'
      ],
      status: 'pending',
      relatedTo: 'Personal injury claim documentation',
      legalImportance: 'Essential for proving the extent of your injuries and medical expenses'
    },
    {
      id: '2',
      title: 'Employment Documentation',
      description: 'Please provide employment and wage information for lost income calculation',
      requestedBy: 'Legal Assistant - Maria',
      dueDate: '2024-01-30T17:00:00Z',
      priority: 'medium',
      documentTypes: [
        'Pay stubs for last 6 months',
        'Tax returns for previous 2 years',
        'Employment contract or offer letter',
        'Any bonus or overtime documentation',
        'Benefits information'
      ],
      instructions: [
        'Gather documents from HR department',
        'Redact social security numbers on copies',
        'Include explanation for any gaps in employment',
        'Provide both paper and digital copies if available'
      ],
      status: 'in_progress',
      relatedTo: 'Lost wages and income documentation',
      legalImportance: 'Required to calculate economic damages and lost earning capacity'
    }
  ];

  const commonDocumentTypes = [
    'Medical records',
    'Employment records',
    'Financial statements',
    'Insurance documents',
    'Contracts or agreements',
    'Correspondence/emails',
    'Photos or videos',
    'Police reports',
    'Tax documents',
    'Business records',
    'Other (please specify)'
  ];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-error-100 text-error-800 border-error-200';
      case 'high':
        return 'bg-warning-100 text-warning-800 border-warning-200';
      case 'medium':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'low':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-success-100 text-success-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'overdue':
        return 'bg-error-100 text-error-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDueDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const daysUntil = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    const formatted = date.toLocaleDateString();
    
    if (daysUntil < 0) {
      return `${formatted} (${Math.abs(daysUntil)} days overdue)`;
    } else if (daysUntil === 0) {
      return `${formatted} (Due today)`;
    } else if (daysUntil === 1) {
      return `${formatted} (Due tomorrow)`;
    } else {
      return `${formatted} (${daysUntil} days remaining)`;
    }
  };

  const handleSubmitRequest = () => {
    console.log('Submitting document request:', newRequest);
    // Reset form
    setNewRequest({
      documentType: '',
      description: '',
      urgency: 'routine',
      context: ''
    });
    // Show success message
    alert('Document request submitted successfully. Your attorney will review and respond within 1-2 business days.');
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center space-x-2 mb-4">
        <FileText className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-medium text-gray-900">Document Requests</h3>
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <Info className="h-3 w-3 mr-1" />
          Case Support
        </span>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('requests')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'requests'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <FileText className="h-4 w-4" />
            <span>Active Requests</span>
          </button>
          <button
            onClick={() => setActiveTab('submit')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === 'submit'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Plus className="h-4 w-4" />
            <span>Request Documents</span>
          </button>
        </div>
      </div>

      {/* Active Requests Tab */}
      {activeTab === 'requests' && (
        <div>
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              Your attorney has requested the following documents to support your case. 
              Click on each request for detailed instructions.
            </p>
          </div>

          {documentRequests.length === 0 ? (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">No active document requests</p>
            </div>
          ) : (
            <div className="space-y-4">
              {documentRequests.map((request) => (
                <div key={request.id} className="border border-gray-200 rounded-lg">
                  <div
                    className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => setExpandedRequest(
                      expandedRequest === request.id ? null : request.id
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h4 className="font-medium text-gray-900">{request.title}</h4>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${getPriorityColor(request.priority)}`}>
                            {request.priority.toUpperCase()}
                          </span>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(request.status)}`}>
                            {request.status.replace('_', ' ').toUpperCase()}
                          </span>
                        </div>
                        
                        <p className="text-sm text-gray-600 mb-2">{request.description}</p>
                        
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>Requested by: {request.requestedBy}</span>
                          <div className="flex items-center space-x-1">
                            <Calendar className="h-3 w-3" />
                            <span className={
                              request.status === 'overdue' ? 'text-error-600 font-medium' : ''
                            }>
                              {formatDueDate(request.dueDate)}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="text-gray-400">
                        {expandedRequest === request.id ? '−' : '+'}
                      </div>
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {expandedRequest === request.id && (
                    <div className="border-t border-gray-200 p-4 bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Document Types */}
                        <div>
                          <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                            <FileText className="h-4 w-4 mr-2" />
                            Documents Needed
                          </h5>
                          <ul className="text-sm text-gray-700 space-y-1">
                            {request.documentTypes.map((type, idx) => (
                              <li key={idx} className="flex items-start space-x-2">
                                <span className="text-blue-600 mt-1">•</span>
                                <span>{type}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        {/* Instructions */}
                        <div>
                          <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Instructions
                          </h5>
                          <ol className="text-sm text-gray-700 space-y-1">
                            {request.instructions.map((instruction, idx) => (
                              <li key={idx} className="flex items-start space-x-2">
                                <span className="text-primary-600 mt-1 font-medium">{idx + 1}.</span>
                                <span>{instruction}</span>
                              </li>
                            ))}
                          </ol>
                        </div>

                        {/* Context */}
                        <div className="md:col-span-2">
                          <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                            <Info className="h-4 w-4 mr-2" />
                            Why This Is Important
                          </h5>
                          <div className="bg-blue-50 border border-blue-200 rounded p-3">
                            <p className="text-sm text-blue-800 mb-1">
                              <strong>Related to:</strong> {request.relatedTo}
                            </p>
                            <p className="text-sm text-blue-700">
                              {request.legalImportance}
                            </p>
                          </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="md:col-span-2 flex items-center space-x-3 pt-4 border-t border-gray-200">
                          <button className="inline-flex items-center px-3 py-2 border border-primary-600 text-sm font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50">
                            <Upload className="h-4 w-4 mr-2" />
                            Upload Documents
                          </button>
                          <button className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                            <Clock className="h-4 w-4 mr-2" />
                            Request Extension
                          </button>
                          <button className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                            Ask Question
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Deadline Warning */}
          <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
              <div>
                <h5 className="text-sm font-semibold text-amber-800 mb-1">Important Deadline Reminder</h5>
                <p className="text-sm text-amber-700">
                  Document deadlines are often tied to court deadlines or legal requirements. Missing these 
                  deadlines can seriously impact your case. If you're having trouble obtaining any requested 
                  documents, contact your attorney immediately to discuss alternatives or extensions.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Submit Request Tab */}
      {activeTab === 'submit' && (
        <div>
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              If you have documents that might be relevant to your case or if your attorney has asked you 
              to provide something specific, use this form to submit a document request or notify your 
              attorney about available materials.
            </p>
          </div>

          <form onSubmit={(e) => { e.preventDefault(); handleSubmitRequest(); }} className="space-y-4">
            {/* Document Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Document Type
              </label>
              <select
                value={newRequest.documentType}
                onChange={(e) => setNewRequest({...newRequest, documentType: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                required
              >
                <option value="">Select document type...</option>
                {commonDocumentTypes.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description
              </label>
              <textarea
                value={newRequest.description}
                onChange={(e) => setNewRequest({...newRequest, description: e.target.value})}
                placeholder="Please describe the documents you have or need help obtaining..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                rows={3}
                required
              />
            </div>

            {/* Context */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Context (Optional)
              </label>
              <textarea
                value={newRequest.context}
                onChange={(e) => setNewRequest({...newRequest, context: e.target.value})}
                placeholder="How do these documents relate to your case? Any special circumstances?"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                rows={2}
              />
            </div>

            {/* Urgency */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Urgency Level
              </label>
              <div className="space-y-2">
                {[
                  { value: 'routine', label: 'Routine - No rush', desc: 'General document gathering, no immediate deadline' },
                  { value: 'important', label: 'Important - Within a week', desc: 'Needed for upcoming deadlines or case development' },
                  { value: 'urgent', label: 'Urgent - ASAP', desc: 'Critical for immediate court filing or emergency situation' }
                ].map((option) => (
                  <label key={option.value} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                    <input
                      type="radio"
                      name="urgency"
                      value={option.value}
                      checked={newRequest.urgency === option.value}
                      onChange={(e) => setNewRequest({...newRequest, urgency: e.target.value as any})}
                      className="mt-1"
                    />
                    <div>
                      <div className="text-sm font-medium text-gray-900">{option.label}</div>
                      <div className="text-xs text-gray-600">{option.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <div className="pt-4">
              <button
                type="submit"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                disabled={!newRequest.documentType || !newRequest.description}
              >
                <Send className="h-4 w-4 mr-2" />
                Submit Request
              </button>
            </div>

            {/* Response Time Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-start space-x-2">
                <Clock className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-blue-900 mb-1">Response Time</h5>
                  <p className="text-sm text-blue-800">
                    Your attorney will review document requests within 1-2 business days and provide 
                    guidance on next steps. For urgent requests, consider calling the office directly.
                  </p>
                </div>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Privacy Notice */}
      <div className="mt-6 bg-legal-50 border border-legal-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Shield className="h-5 w-5 text-legal-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-legal-900 mb-2">Document Privacy & Security</h5>
            <ul className="text-sm text-legal-700 space-y-1">
              <li>• All documents shared through this portal are kept confidential</li>
              <li>• Documents may be subject to attorney-client privilege protection</li>
              <li>• Only share documents that are relevant to your case</li>
              <li>• Redact sensitive information (SSN, account numbers) unless specifically needed</li>
              <li>• Keep copies of all documents you provide</li>
              <li>• Do not share privileged communications with third parties</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Legal Disclaimer */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-xs font-semibold text-legal-900 mb-1">Document Request Disclaimer</h5>
              <p className="text-xs text-legal-700">
                Document requests are part of case preparation and do not constitute legal advice. 
                The importance and urgency of documents may vary based on case developments. 
                Always consult with your attorney about document relevance and handling procedures.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentRequest;