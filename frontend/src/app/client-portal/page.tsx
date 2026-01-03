'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  User,
  FileText,
  MessageSquare,
  Calendar,
  AlertTriangle,
  Info,
  Scale,
  Shield,
  Phone,
  ExternalLink,
  Upload,
  Clock,
  BookOpen,
  HelpCircle,
  Building
} from 'lucide-react';
import CaseTypeExplainer from '@/components/client-portal/CaseTypeExplainer';
import TimelineEducation from '@/components/client-portal/TimelineEducation';
import SecureMessaging from '@/components/client-portal/SecureMessaging';
import FindAttorneyButton from '@/components/client-portal/FindAttorneyButton';
import LegalAidResources from '@/components/client-portal/LegalAidResources';
import EmergencyContact from '@/components/client-portal/EmergencyContact';

const ClientPortalPage: React.FC = () => {
  const [showLegalNotice, setShowLegalNotice] = useState(true);
  
  // Mock client data - in real app would come from auth/API
  const clientData = {
    name: 'John Smith',
    caseNumber: 'CV-2024-001234',
    caseType: 'Personal Injury',
    attorney: 'Sarah Johnson, Esq.',
    firmName: 'Johnson & Associates',
    nextAppointment: '2024-01-25T14:00:00Z',
    caseStatus: 'Discovery Phase',
    statusDescription: 'We are currently gathering information and evidence for your case. This typically involves requesting documents and conducting depositions.',
    lastUpdate: '2024-01-15T10:30:00Z'
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Legal Notice Banner */}
      {showLegalNotice && (
        <div className="bg-error-50 border-b border-error-200 p-4">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-error-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-sm font-semibold text-error-900 mb-1">
                  Important Legal Notice - Please Read Carefully
                </h3>
                <p className="text-sm text-error-800 mb-2">
                  This client portal provides general information about your case for educational purposes only. 
                  The information does not constitute legal advice, and using this portal does not create an 
                  attorney-client relationship unless you already have a signed representation agreement.
                </p>
                <div className="flex items-center space-x-4">
                  <button
                    onClick={() => setShowLegalNotice(false)}
                    className="text-xs text-error-700 hover:text-error-800 font-medium underline"
                  >
                    I understand - Continue to portal
                  </button>
                  <span className="text-xs text-error-600">
                    For legal advice, consult with your attorney directly
                  </span>
                </div>
              </div>
              <button
                onClick={() => setShowLegalNotice(false)}
                className="text-error-400 hover:text-error-600"
              >
                ×
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Building className="h-6 w-6 text-primary-600" />
              <div>
                <h1 className="text-lg font-semibold text-gray-900">Client Portal</h1>
                <p className="text-sm text-gray-500">General Case Information</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <EmergencyContact />
              <FindAttorneyButton />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Welcome Section */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Welcome, {clientData.name}
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Case Number:</span>
                  <div className="font-medium">{clientData.caseNumber}</div>
                </div>
                <div>
                  <span className="text-gray-500">Case Type:</span>
                  <div className="font-medium">{clientData.caseType}</div>
                </div>
                <div>
                  <span className="text-gray-500">Attorney:</span>
                  <div className="font-medium">{clientData.attorney}</div>
                </div>
                <div>
                  <span className="text-gray-500">Law Firm:</span>
                  <div className="font-medium">{clientData.firmName}</div>
                </div>
              </div>
            </div>
            
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              <Info className="h-3 w-3 mr-1" />
              Information Only
            </span>
          </div>

          {/* Case Status */}
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <Scale className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-semibold text-blue-900 mb-1">
                  Current Case Status: {clientData.caseStatus}
                </h3>
                <p className="text-sm text-blue-800">
                  {clientData.statusDescription}
                </p>
                <p className="text-xs text-blue-700 mt-2">
                  <strong>Last Updated:</strong> {new Date(clientData.lastUpdate).toLocaleDateString()}
                  <span className="ml-2 italic">
                    (Status information is general and for educational purposes only)
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <MessageSquare className="h-5 w-5 text-primary-600" />
              <h3 className="font-medium text-gray-900">Send Message</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Send non-urgent questions to your attorney's office.
            </p>
            <Link
              href="/client-portal/messaging"
              className="inline-flex items-center px-3 py-2 border border-primary-600 text-sm font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50"
            >
              Open Messaging
              <ExternalLink className="h-3 w-3 ml-2" />
            </Link>
            <div className="mt-2 text-xs text-amber-600">
              <AlertTriangle className="h-3 w-3 inline mr-1" />
              Does not create attorney-client privilege
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <Upload className="h-5 w-5 text-primary-600" />
              <h3 className="font-medium text-gray-900">Upload Documents</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Securely share documents with your attorney's office.
            </p>
            <Link
              href="/client-portal/documents"
              className="inline-flex items-center px-3 py-2 border border-primary-600 text-sm font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50"
            >
              Upload Files
              <ExternalLink className="h-3 w-3 ml-2" />
            </Link>
            <div className="mt-2 text-xs text-blue-600">
              <Shield className="h-3 w-3 inline mr-1" />
              Secure & confidential
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center space-x-3 mb-4">
              <Calendar className="h-5 w-5 text-primary-600" />
              <h3 className="font-medium text-gray-900">Schedule Meeting</h3>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Request an appointment with your attorney.
            </p>
            <Link
              href="/client-portal/scheduling"
              className="inline-flex items-center px-3 py-2 border border-primary-600 text-sm font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50"
            >
              Request Meeting
              <ExternalLink className="h-3 w-3 ml-2" />
            </Link>
            {clientData.nextAppointment && (
              <div className="mt-2 text-xs text-green-600">
                <Clock className="h-3 w-3 inline mr-1" />
                Next: {new Date(clientData.nextAppointment).toLocaleDateString()}
              </div>
            )}
          </div>
        </div>

        {/* Educational Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="space-y-6">
            <CaseTypeExplainer caseType={clientData.caseType} />
            <TimelineEducation caseType={clientData.caseType} />
          </div>
          
          <div className="space-y-6">
            <LegalAidResources />
            
            {/* Help & Resources */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center space-x-2 mb-4">
                <HelpCircle className="h-5 w-5 text-blue-600" />
                <h3 className="font-medium text-gray-900">Understanding Legal Processes</h3>
              </div>
              
              <div className="space-y-3">
                <Link
                  href="/client-portal/court-process"
                  className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">How Courts Work</h4>
                      <p className="text-xs text-gray-600">General information about court procedures</p>
                    </div>
                    <ExternalLink className="h-4 w-4 text-gray-400" />
                  </div>
                </Link>
                
                <Link
                  href="/client-portal/document-guide"
                  className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Document Types</h4>
                      <p className="text-xs text-gray-600">What different legal filings mean</p>
                    </div>
                    <ExternalLink className="h-4 w-4 text-gray-400" />
                  </div>
                </Link>
                
                <Link
                  href="/client-portal/legal-terms"
                  className="block p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">Legal Terms Glossary</h4>
                      <p className="text-xs text-gray-600">Common legal terms explained</p>
                    </div>
                    <ExternalLink className="h-4 w-4 text-gray-400" />
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Important Disclaimers */}
        <div className="bg-legal-50 border border-legal-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <Scale className="h-5 w-5 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-legal-900 mb-2">
                Important Client Portal Disclaimers
              </h3>
              <div className="space-y-2 text-sm text-legal-700">
                <p>
                  <strong>Not Legal Advice:</strong> This portal provides general educational information only. 
                  It does not constitute legal advice specific to your situation.
                </p>
                <p>
                  <strong>No Attorney-Client Privilege:</strong> Communications through this portal may not be 
                  protected by attorney-client privilege unless you have a signed representation agreement.
                </p>
                <p>
                  <strong>Emergency Situations:</strong> Do not use this portal for urgent legal matters. 
                  Contact your attorney directly or emergency services if immediate assistance is needed.
                </p>
                <p>
                  <strong>Case Information:</strong> Status updates and case information are general summaries. 
                  Consult with your attorney for specific legal strategy and advice.
                </p>
                <p>
                  <strong>Third-Party Resources:</strong> Links to external resources are provided for 
                  educational purposes only and do not constitute endorsements.
                </p>
              </div>
              
              <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded">
                <p className="text-sm text-amber-800">
                  <strong>Need Legal Representation?</strong> If you don't currently have an attorney, 
                  use the "Find Attorney" button to connect with your local bar association's referral service.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-xs text-gray-500">
          <p>
            This client portal is for informational purposes only. 
            For legal advice, consult with a qualified attorney.
          </p>
          <p className="mt-1">
            <Link href="/privacy" className="text-primary-600 hover:text-primary-700">Privacy Policy</Link>
            {' • '}
            <Link href="/terms" className="text-primary-600 hover:text-primary-700">Terms of Use</Link>
            {' • '}
            <Link href="/help" className="text-primary-600 hover:text-primary-700">Help Center</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ClientPortalPage;