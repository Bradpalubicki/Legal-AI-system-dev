'use client';

import React, { useState } from 'react';
import {
  Search,
  ExternalLink,
  Scale,
  Users,
  MapPin,
  Phone,
  Info,
  AlertTriangle,
  BookOpen,
  Building
} from 'lucide-react';

interface FindAttorneyButtonProps {
  className?: string;
}

const FindAttorneyButton: React.FC<FindAttorneyButtonProps> = ({ className = '' }) => {
  const [showReferralInfo, setShowReferralInfo] = useState(false);

  // Sample bar referral services - in real app would be location-based
  const referralServices = [
    {
      name: 'American Bar Association Lawyer Referral Directory',
      description: 'National directory of state and local bar referral services',
      url: 'https://www.americanbar.org/groups/legal_services/flh-home/flh-lawyer-referral-directory/',
      type: 'national',
      features: ['Verified attorneys', 'Practice area filtering', 'Location-based search']
    },
    {
      name: 'State Bar Referral Service',
      description: 'Your state bar association\'s official attorney referral program',
      url: '#state-bar-referral',
      type: 'state',
      features: ['Licensed attorneys only', 'Disciplinary record checks', 'Reasonable fees']
    },
    {
      name: 'Local County Bar Association',
      description: 'County-level attorney referral and legal aid information',
      url: '#county-bar',
      type: 'local',
      features: ['Local attorneys', 'Community legal resources', 'Pro bono opportunities']
    }
  ];

  const legalAidResources = [
    {
      name: 'Legal Services Corporation (LSC)',
      description: 'Free legal aid for low-income individuals and families',
      url: 'https://www.lsc.gov/find-legal-aid',
      eligibilityInfo: 'Income-based eligibility requirements apply'
    },
    {
      name: 'Pro Bono Programs',
      description: 'Free legal services from volunteer attorneys',
      url: '#pro-bono-search',
      eligibilityInfo: 'Various eligibility criteria depending on program'
    },
    {
      name: 'Law School Clinics',
      description: 'Legal services provided by supervised law students',
      url: '#law-school-clinics',
      eligibilityInfo: 'Often income-based with case type restrictions'
    }
  ];

  return (
    <div className={className}>
      <button
        onClick={() => setShowReferralInfo(!showReferralInfo)}
        className="inline-flex items-center px-4 py-2 border border-primary-600 text-sm font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50 transition-colors"
      >
        <Search className="h-4 w-4 mr-2" />
        Find Attorney
      </button>

      {/* Attorney Referral Modal/Dropdown */}
      {showReferralInfo && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Find Legal Representation</h3>
              <button
                onClick={() => setShowReferralInfo(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>

            {/* Important Notice */}
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold text-blue-900 mb-2">Why Use Official Referral Services?</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Attorneys are vetted and licensed in your jurisdiction</li>
                    <li>• Disciplinary records are checked</li>
                    <li>• Many services offer reduced-fee initial consultations</li>
                    <li>• Matching based on your specific legal needs</li>
                    <li>• Consumer protection and complaint processes</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Attorney Referral Services */}
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-900 mb-3">Attorney Referral Services</h4>
              <div className="space-y-3">
                {referralServices.map((service, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <Building className="h-4 w-4 text-primary-600" />
                          <h5 className="font-medium text-gray-900">{service.name}</h5>
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            service.type === 'national' ? 'bg-blue-100 text-blue-800' :
                            service.type === 'state' ? 'bg-green-100 text-green-800' :
                            'bg-purple-100 text-purple-800'
                          }`}>
                            {service.type.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{service.description}</p>
                        <div className="flex flex-wrap gap-2">
                          {service.features.map((feature, idx) => (
                            <span key={idx} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700">
                              {feature}
                            </span>
                          ))}
                        </div>
                      </div>
                      <a
                        href={service.url}
                        target={service.url.startsWith('http') ? '_blank' : undefined}
                        rel={service.url.startsWith('http') ? 'noopener noreferrer' : undefined}
                        className="inline-flex items-center px-3 py-1.5 border border-primary-600 text-xs font-medium rounded text-primary-600 bg-white hover:bg-primary-50 ml-4"
                      >
                        Visit Service
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Legal Aid Resources */}
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-900 mb-3">Free & Low-Cost Legal Aid</h4>
              <div className="space-y-3">
                {legalAidResources.map((resource, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <Users className="h-4 w-4 text-green-600" />
                          <h5 className="font-medium text-gray-900">{resource.name}</h5>
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{resource.description}</p>
                        <div className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800">
                          <Info className="h-3 w-3 mr-1" />
                          {resource.eligibilityInfo}
                        </div>
                      </div>
                      <a
                        href={resource.url}
                        target={resource.url.startsWith('http') ? '_blank' : undefined}
                        rel={resource.url.startsWith('http') ? 'noopener noreferrer' : undefined}
                        className="inline-flex items-center px-3 py-1.5 border border-green-600 text-xs font-medium rounded text-green-600 bg-white hover:bg-green-50 ml-4"
                      >
                        Learn More
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Selection Tips */}
            <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <BookOpen className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold text-amber-800 mb-2">Tips for Choosing an Attorney</h4>
                  <ul className="text-sm text-amber-700 space-y-1">
                    <li>• Verify the attorney is licensed in your state</li>
                    <li>• Check disciplinary records through your state bar</li>
                    <li>• Ask about experience with your type of case</li>
                    <li>• Understand fee structures and payment arrangements</li>
                    <li>• Schedule consultations with multiple attorneys</li>
                    <li>• Get fee agreements and retainer terms in writing</li>
                    <li>• Trust your instincts about communication and comfort level</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Questions to Ask */}
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-900 mb-3">Questions to Ask During Consultation</h4>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h5 className="text-sm font-semibold text-gray-800 mb-2">Experience & Qualifications</h5>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• How long have you practiced this area of law?</li>
                      <li>• How many similar cases have you handled?</li>
                      <li>• What are typical outcomes for cases like mine?</li>
                      <li>• Will you personally handle my case?</li>
                    </ul>
                  </div>
                  <div>
                    <h5 className="text-sm font-semibold text-gray-800 mb-2">Fees & Process</h5>
                    <ul className="text-sm text-gray-700 space-y-1">
                      <li>• What are your fee structures and payment terms?</li>
                      <li>• What costs should I expect beyond attorney fees?</li>
                      <li>• How will you keep me informed about my case?</li>
                      <li>• What is the likely timeline for resolution?</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Warning About Non-Lawyer Services */}
            <div className="bg-error-50 border border-error-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-error-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-semibold text-error-900 mb-2">Beware of Non-Lawyer "Legal Services"</h4>
                  <p className="text-sm text-error-700 mb-2">
                    Be cautious of non-lawyer services that claim to provide legal assistance:
                  </p>
                  <ul className="text-sm text-error-700 space-y-1">
                    <li>• Document preparation services cannot give legal advice</li>
                    <li>• Paralegal services must be supervised by licensed attorneys</li>
                    <li>• Online legal forms may not comply with your state's requirements</li>
                    <li>• "Legal consultants" without bar admission cannot represent you</li>
                  </ul>
                  <p className="text-sm text-error-700 mt-2">
                    <strong>Always verify</strong> that any person providing legal services is a licensed attorney 
                    in good standing in your jurisdiction.
                  </p>
                </div>
              </div>
            </div>

            {/* Close Button */}
            <div className="mt-6 text-center">
              <button
                onClick={() => setShowReferralInfo(false)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FindAttorneyButton;