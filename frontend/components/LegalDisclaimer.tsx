/**
 * Legal Disclaimer Components - Frontend UPL Compliance
 * CRITICAL: Ensures all legal AI content includes proper disclaimers
 * Prevents unauthorized practice of law violations through clear user notices
 */

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Scale, ExternalLink, X, Info, Phone, MapPin } from 'lucide-react';

// Types for disclaimer configuration
interface DisclaimerConfig {
  outputType: 'research' | 'document_analysis' | 'education' | 'case_suggestion';
  hasClientData: boolean;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  practiceArea?: string;
  userState?: string;
  requiresReview: boolean;
}

interface AttorneyReferral {
  organization: string;
  phone: string;
  website: string;
  description: string;
}

interface LegalAidService {
  name: string;
  phone: string;
  website: string;
  eligibility: string;
  services: string[];
}

// Fixed bottom banner disclaimer - Always visible
export const LegalDisclaimer: React.FC<{ config: DisclaimerConfig }> = ({ config }) => {
  const [showFullDisclaimer, setShowFullDisclaimer] = useState(false);
  const [showAttorneyFinder, setShowAttorneyFinder] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);

  // Don't allow minimizing for high/critical risk content
  const canMinimize = !['high', 'critical'].includes(config.riskLevel) && !config.requiresReview;

  return (
    <>
      {/* Fixed Bottom Banner */}
      {!isMinimized && (
        <div className={`
          fixed bottom-0 left-0 right-0 z-50 
          ${config.riskLevel === 'critical' ? 'bg-red-600' : 
            config.riskLevel === 'high' ? 'bg-orange-600' :
            config.riskLevel === 'medium' ? 'bg-yellow-600' : 
            'bg-blue-600'} 
          text-white px-4 py-3 shadow-lg
        `}>
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <AlertTriangle className="h-5 w-5 flex-shrink-0" />
              <span className="font-medium">
                {config.riskLevel === 'critical' ? '🚨 ATTORNEY REVIEW REQUIRED' :
                 config.riskLevel === 'high' ? '⚠️ HIGH RISK CONTENT' :
                 config.requiresReview ? '👨‍⚖️ PROFESSIONAL REVIEW NEEDED' :
                 '⚠️ Legal Information Only - Not Legal Advice'}
              </span>
              {config.hasClientData && (
                <span className="bg-white bg-opacity-20 px-2 py-1 rounded text-xs">
                  CONFIDENTIAL
                </span>
              )}
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowFullDisclaimer(true)}
                className="text-white hover:text-gray-200 underline text-sm"
              >
                Learn More
              </button>
              <button
                onClick={() => setShowAttorneyFinder(true)}
                className="bg-white text-blue-600 px-3 py-1 rounded text-sm font-medium hover:bg-gray-100"
              >
                Find an Attorney
              </button>
              {canMinimize && (
                <button
                  onClick={() => setIsMinimized(true)}
                  className="text-white hover:text-gray-200 p-1"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Minimized Indicator */}
      {isMinimized && (
        <div className="fixed bottom-4 right-4 z-50">
          <button
            onClick={() => setIsMinimized(false)}
            className="bg-blue-600 text-white p-2 rounded-full shadow-lg hover:bg-blue-700"
          >
            <Scale className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* Full Disclaimer Modal */}
      {showFullDisclaimer && (
        <FullDisclaimerModal 
          config={config} 
          onClose={() => setShowFullDisclaimer(false)} 
        />
      )}

      {/* Attorney Finder Modal */}
      {showAttorneyFinder && (
        <AttorneyFinderModal 
          userState={config.userState} 
          practiceArea={config.practiceArea}
          onClose={() => setShowAttorneyFinder(false)} 
        />
      )}
    </>
  );
};

// Full disclaimer modal with detailed legal notices
const FullDisclaimerModal: React.FC<{
  config: DisclaimerConfig;
  onClose: () => void;
}> = ({ config, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Scale className="h-8 w-8 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">Legal Disclaimer & Important Notices</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 p-2"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="space-y-6">
            {/* Primary Disclaimer */}
            <div className={`
              p-4 rounded-lg border-l-4 
              ${config.riskLevel === 'critical' ? 'border-red-500 bg-red-50' :
                config.riskLevel === 'high' ? 'border-orange-500 bg-orange-50' :
                'border-blue-500 bg-blue-50'}
            `}>
              <h3 className="font-semibold text-lg mb-2">
                {config.riskLevel === 'critical' ? '🚨 Critical Notice' :
                 config.riskLevel === 'high' ? '⚠️ Important Warning' :
                 '📋 Legal Information Disclaimer'}
              </h3>
              <div className="text-sm space-y-2">
                <p>
                  <strong>This AI-generated content is for informational purposes only and does not constitute legal advice.</strong> 
                  It is not a substitute for professional legal counsel tailored to your specific circumstances.
                </p>
                {config.requiresReview && (
                  <p className="font-medium text-red-600">
                    ⚖️ This content requires attorney review before use or reliance.
                  </p>
                )}
                {config.hasClientData && (
                  <p className="font-medium text-purple-600">
                    🔒 This content may contain confidential client information protected by attorney-client privilege.
                  </p>
                )}
              </div>
            </div>

            {/* No Attorney-Client Relationship */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">No Attorney-Client Relationship</h4>
              <p className="text-sm text-gray-700">
                Use of this AI system does not create an attorney-client relationship. Any information you provide 
                may not be protected by attorney-client privilege unless you are working with a qualified attorney 
                who is representing you.
              </p>
            </div>

            {/* Verification Required */}
            <div className="bg-yellow-50 p-4 rounded-lg border-l-4 border-yellow-500">
              <h4 className="font-semibold mb-2">🔍 Verification Required</h4>
              <p className="text-sm text-gray-700">
                All legal authorities, citations, and procedural information should be independently verified 
                before reliance. Laws change frequently and vary by jurisdiction.
              </p>
            </div>

            {/* Jurisdiction Notice */}
            {config.userState && (
              <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
                <h4 className="font-semibold mb-2">🗺️ Jurisdiction Notice</h4>
                <p className="text-sm text-gray-700">
                  Legal requirements vary significantly by jurisdiction. Information provided may not apply 
                  to {config.userState} law. Consult local counsel familiar with {config.userState} 
                  legal requirements.
                </p>
              </div>
            )}

            {/* Practice Area Specific Notice */}
            {config.practiceArea && (
              <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                <h4 className="font-semibold mb-2">⚖️ {config.practiceArea.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Notice</h4>
                <p className="text-sm text-gray-700">
                  {getPracticeAreaNotice(config.practiceArea)}
                </p>
              </div>
            )}

            {/* AI Limitations */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">🤖 AI System Limitations</h4>
              <ul className="text-sm text-gray-700 list-disc list-inside space-y-1">
                <li>AI may not have access to the most current legal developments</li>
                <li>AI cannot assess the specific facts and circumstances of your situation</li>
                <li>AI responses may contain errors or incomplete information</li>
                <li>AI cannot provide strategic legal guidance or professional judgment</li>
              </ul>
            </div>

            {/* Professional Consultation Required */}
            <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
              <h4 className="font-semibold mb-2">👨‍⚖️ Professional Consultation Required</h4>
              <p className="text-sm text-gray-700">
                For legal advice specific to your situation, consult with a qualified attorney licensed 
                to practice in your jurisdiction. Legal professionals can provide personalized guidance 
                based on current law and your specific circumstances.
              </p>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              This disclaimer is required by professional responsibility rules to prevent unauthorized practice of law.
              Generated at {new Date().toLocaleString()} | Compliance Version 1.0
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Attorney finder modal with referral services
const AttorneyFinderModal: React.FC<{
  userState?: string;
  practiceArea?: string;
  onClose: () => void;
}> = ({ userState, practiceArea, onClose }) => {
  const [selectedState, setSelectedState] = useState(userState || 'general');

  // State bar referral services
  const stateBarServices: Record<string, AttorneyReferral> = {
    'CA': {
      organization: 'State Bar of California Lawyer Referral Service',
      phone: '1-866-442-2529',
      website: 'https://www.calbar.ca.gov/public/need-legal-help/lawyer-referral-service',
      description: 'Official California State Bar referral service with vetted attorneys'
    },
    'NY': {
      organization: 'New York State Bar Association Lawyer Referral Service',
      phone: '1-800-342-3661',
      website: 'https://www.nysba.org/attorney/find-a-lawyer/',
      description: 'New York State Bar Association certified lawyer referral program'
    },
    'TX': {
      organization: 'State Bar of Texas Lawyer Referral Service',
      phone: '1-800-252-9690',
      website: 'https://www.texasbar.com/AM/Template.cfm?Section=Lawyer_Referral_Service_LRIS_',
      description: 'Texas State Bar lawyer referral and information service'
    },
    'FL': {
      organization: 'Florida Bar Lawyer Referral Service',
      phone: '1-800-342-8011',
      website: 'https://www.floridabar.org/public/lrs/',
      description: 'Florida Bar certified lawyer referral service'
    },
    'general': {
      organization: 'American Bar Association - Find a Lawyer',
      phone: '312-988-5000',
      website: 'https://www.americanbar.org/groups/lawyer_referral/',
      description: 'National directory and state bar referral service information'
    }
  };

  // Legal aid services
  const legalAidServices: LegalAidService[] = [
    {
      name: 'Legal Services Corporation',
      phone: '202-295-1500',
      website: 'https://www.lsc.gov/find-legal-aid',
      eligibility: 'Income-based eligibility (typically 125% of federal poverty level)',
      services: ['Civil legal aid', 'Housing', 'Family law', 'Public benefits', 'Consumer protection']
    },
    {
      name: 'National Legal Aid & Defender Association',
      phone: '202-452-0620',
      website: 'https://www.nlada.org/',
      eligibility: 'Varies by local program',
      services: ['Legal aid directory', 'Defender services', 'Pro bono programs']
    },
    {
      name: 'Pro Bono Net',
      phone: '212-760-2554',
      website: 'https://www.probono.net/',
      eligibility: 'Low-income individuals and nonprofits',
      services: ['Pro bono matching', 'Self-help resources', 'Legal clinics']
    }
  ];

  const currentBarService = stateBarServices[selectedState] || stateBarServices['general'];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <Phone className="h-8 w-8 text-green-600" />
              <h2 className="text-2xl font-bold text-gray-900">Find Legal Assistance</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 p-2"
            >
              <X className="h-6 w-6" />
            </button>
          </div>

          <div className="space-y-6">
            {/* State Selection */}
            <div className="bg-blue-50 p-4 rounded-lg">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Your State for Local Bar Referral:
              </label>
              <select
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
              >
                <option value="general">National / Not Listed</option>
                <option value="CA">California</option>
                <option value="NY">New York</option>
                <option value="TX">Texas</option>
                <option value="FL">Florida</option>
              </select>
            </div>

            {/* State Bar Referral Service */}
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <Scale className="h-6 w-6 text-blue-600 mt-1" />
                <div className="flex-1">
                  <h3 className="font-semibold text-lg text-gray-900 mb-2">
                    Bar Association Lawyer Referral
                  </h3>
                  <div className="space-y-2">
                    <p className="font-medium text-gray-800">{currentBarService.organization}</p>
                    <p className="text-sm text-gray-600">{currentBarService.description}</p>
                    <div className="flex items-center space-x-4">
                      <a
                        href={`tel:${currentBarService.phone}`}
                        className="flex items-center space-x-1 text-green-600 hover:text-green-700"
                      >
                        <Phone className="h-4 w-4" />
                        <span>{currentBarService.phone}</span>
                      </a>
                      <a
                        href={currentBarService.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-1 text-blue-600 hover:text-blue-700"
                      >
                        <ExternalLink className="h-4 w-4" />
                        <span>Visit Website</span>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Practice Area Notice */}
            {practiceArea && (
              <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                <h4 className="font-semibold mb-2">
                  📋 {practiceArea.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} Specialists
                </h4>
                <p className="text-sm text-gray-700">
                  When contacting attorneys, specify that you need assistance with {practiceArea.replace('_', ' ')} matters 
                  to ensure you're connected with relevant specialists.
                </p>
              </div>
            )}

            {/* Legal Aid Services */}
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-semibold text-lg text-gray-900 mb-4 flex items-center">
                <MapPin className="h-5 w-5 mr-2 text-green-600" />
                Free & Low-Cost Legal Aid
              </h3>
              <div className="space-y-4">
                {legalAidServices.map((service, index) => (
                  <div key={index} className="bg-white p-3 rounded border">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-medium text-gray-800">{service.name}</h4>
                      <div className="flex items-center space-x-3 text-sm">
                        <a
                          href={`tel:${service.phone}`}
                          className="text-green-600 hover:text-green-700"
                        >
                          {service.phone}
                        </a>
                        <a
                          href={service.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700 flex items-center"
                        >
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      </div>
                    </div>
                    <p className="text-xs text-gray-600 mb-1">
                      <strong>Eligibility:</strong> {service.eligibility}
                    </p>
                    <div className="text-xs text-gray-600">
                      <strong>Services:</strong> {service.services.join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Emergency Resources */}
            <div className="bg-red-50 p-4 rounded-lg border-l-4 border-red-500">
              <h4 className="font-semibold mb-2 text-red-800">🚨 Emergency Legal Situations</h4>
              <p className="text-sm text-red-700 mb-2">
                If you're facing immediate legal deadlines or emergency situations:
              </p>
              <ul className="text-sm text-red-700 list-disc list-inside space-y-1">
                <li>Contact your state bar's emergency referral service immediately</li>
                <li>Many courts have self-help resources for urgent matters</li>
                <li>Legal aid organizations often have emergency assistance programs</li>
                <li>Some areas have 24/7 legal hotlines for crisis situations</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200 text-center">
            <p className="text-sm text-gray-600">
              These referral services can connect you with qualified attorneys licensed in your jurisdiction 
              who can provide personalized legal advice and representation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Content-aware disclaimer component for different AI outputs
export const ContentDisclaimer: React.FC<{
  outputType: DisclaimerConfig['outputType'];
  riskLevel: DisclaimerConfig['riskLevel'];
  hasClientData?: boolean;
  practiceArea?: string;
  className?: string;
}> = ({ outputType, riskLevel, hasClientData = false, practiceArea, className = '' }) => {
  const getDisclaimerText = () => {
    switch (outputType) {
      case 'document_analysis':
        return 'This AI document analysis is for informational purposes only. Professional legal review is recommended before making decisions based on this analysis.';
      case 'case_suggestion':
        return 'These case suggestions are for research purposes only. Discuss relevance and applicability with your attorney.';
      case 'education':
        return 'This educational content provides general legal information only. It is not specific legal advice for your situation.';
      default:
        return 'This AI-generated legal research is for informational purposes only and does not constitute legal advice.';
    }
  };

  const getBorderColor = () => {
    switch (riskLevel) {
      case 'critical': return 'border-red-500';
      case 'high': return 'border-orange-500';
      case 'medium': return 'border-yellow-500';
      default: return 'border-blue-500';
    }
  };

  const getIconColor = () => {
    switch (riskLevel) {
      case 'critical': return 'text-red-600';
      case 'high': return 'text-orange-600';
      case 'medium': return 'text-yellow-600';
      default: return 'text-blue-600';
    }
  };

  return (
    <div className={`border-l-4 ${getBorderColor()} bg-gray-50 p-3 ${className}`}>
      <div className="flex items-start space-x-2">
        <Info className={`h-4 w-4 mt-0.5 ${getIconColor()}`} />
        <div className="text-sm">
          <p className="text-gray-700">{getDisclaimerText()}</p>
          {hasClientData && (
            <p className="text-purple-600 font-medium mt-1">
              🔒 Contains confidential information - handle accordingly
            </p>
          )}
          {riskLevel === 'critical' && (
            <p className="text-red-600 font-medium mt-1">
              ⚖️ Attorney review required before use
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper function for practice area notices
function getPracticeAreaNotice(practiceArea: string): string {
  const notices: Record<string, string> = {
    'bankruptcy_law': 'Bankruptcy law involves complex federal and state regulations with strict deadlines. Missing deadlines can result in loss of rights or dismissal of cases.',
    'employment_law': 'Employment law varies significantly by state and involves federal regulations. Discrimination claims have strict filing deadlines that cannot be extended.',
    'contract_law': 'Contract interpretation depends heavily on specific terms and applicable state law. Contract disputes may involve significant financial consequences.',
    'family_law': 'Family law matters often involve urgent deadlines and court orders. Child custody and support issues require immediate professional attention.',
    'criminal_law': 'Criminal matters involve constitutional rights and potential incarceration. Immediate legal representation is essential in all criminal proceedings.',
    'personal_injury': 'Personal injury claims are subject to statutes of limitations that vary by state. Evidence preservation and timely filing are critical.'
  };
  
  return notices[practiceArea] || 'This practice area involves specialized legal requirements and procedures that require professional guidance.';
}

export default LegalDisclaimer;