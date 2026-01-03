'use client';

import React, { useState } from 'react';
import {
  Phone,
  AlertTriangle,
  Shield,
  Clock,
  Info,
  Scale,
  Heart,
  Home,
  Gavel,
  Users,
  ExternalLink,
  X
} from 'lucide-react';

interface EmergencyResource {
  name: string;
  phone: string;
  description: string;
  availability: string;
  category: 'safety' | 'legal' | 'crisis' | 'health';
  isNational: boolean;
  website?: string;
}

interface EmergencyContactProps {
  className?: string;
}

const EmergencyContact: React.FC<EmergencyContactProps> = ({ className = '' }) => {
  const [showEmergencyInfo, setShowEmergencyInfo] = useState(false);

  const emergencyResources: EmergencyResource[] = [
    {
      name: '911 Emergency Services',
      phone: '911',
      description: 'Police, fire, and medical emergencies requiring immediate response',
      availability: '24/7',
      category: 'safety',
      isNational: true
    },
    {
      name: 'National Domestic Violence Hotline',
      phone: '1-800-799-7233',
      description: 'Confidential support for domestic violence survivors and their families',
      availability: '24/7',
      category: 'safety',
      isNational: true,
      website: 'https://www.thehotline.org/'
    },
    {
      name: 'National Suicide Prevention Lifeline',
      phone: '988',
      description: 'Crisis counseling and mental health support',
      availability: '24/7',
      category: 'crisis',
      isNational: true,
      website: 'https://suicidepreventionlifeline.org/'
    },
    {
      name: 'National Child Abuse Hotline',
      phone: '1-800-4-A-CHILD (1-800-422-4453)',
      description: 'Child abuse reporting and crisis counseling',
      availability: '24/7',
      category: 'safety',
      isNational: true,
      website: 'https://www.childhelp.org/'
    },
    {
      name: 'Legal Aid Emergency Line',
      phone: 'Contact your local legal aid organization',
      description: 'Emergency legal assistance for urgent matters (evictions, restraining orders)',
      availability: 'Varies by location',
      category: 'legal',
      isNational: false
    },
    {
      name: 'Immigration Emergency',
      phone: '1-800-351-4024 (ICE Detention)',
      description: 'Immigration detention and emergency situations',
      availability: '24/7',
      category: 'legal',
      isNational: true
    }
  ];

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'safety':
        return <Shield className="h-4 w-4 text-error-600" />;
      case 'legal':
        return <Scale className="h-4 w-4 text-blue-600" />;
      case 'crisis':
        return <Heart className="h-4 w-4 text-purple-600" />;
      case 'health':
        return <Users className="h-4 w-4 text-green-600" />;
      default:
        return <Phone className="h-4 w-4 text-gray-600" />;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'safety':
        return 'bg-error-50 border-error-200';
      case 'legal':
        return 'bg-blue-50 border-blue-200';
      case 'crisis':
        return 'bg-purple-50 border-purple-200';
      case 'health':
        return 'bg-green-50 border-green-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={className}>
      <button
        onClick={() => setShowEmergencyInfo(!showEmergencyInfo)}
        className="inline-flex items-center px-4 py-2 border border-error-600 text-sm font-medium rounded-md text-error-600 bg-white hover:bg-error-50 transition-colors"
      >
        <AlertTriangle className="h-4 w-4 mr-2" />
        Emergency Help
      </button>

      {/* Emergency Information Modal */}
      {showEmergencyInfo && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-10 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-2/3 shadow-lg rounded-md bg-white">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Emergency Legal & Crisis Resources</h3>
              <button
                onClick={() => setShowEmergencyInfo(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Immediate Danger Warning */}
            <div className="mb-6 bg-error-50 border border-error-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-6 w-6 text-error-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-md font-semibold text-error-900 mb-2">
                    If You Are in Immediate Danger
                  </h4>
                  <div className="text-error-800 space-y-2">
                    <p className="font-medium text-lg">Call 911 immediately</p>
                    <p className="text-sm">
                      For immediate threats to your safety or the safety of others, contact emergency services. 
                      Do not delay seeking help for emergency situations.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Emergency Resources */}
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-900 mb-4">Emergency Contact Numbers</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {emergencyResources.map((resource, index) => (
                  <div key={index} className={`border rounded-lg p-4 ${getCategoryColor(resource.category)}`}>
                    <div className="flex items-start space-x-3">
                      <div className="mt-1">
                        {getCategoryIcon(resource.category)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <h5 className="font-medium text-gray-900">{resource.name}</h5>
                          {resource.isNational && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              National
                            </span>
                          )}
                        </div>
                        
                        <div className="text-lg font-semibold text-gray-900 mb-2">
                          <a href={`tel:${resource.phone.replace(/[^\d]/g, '')}`} className="hover:text-primary-600">
                            {resource.phone}
                          </a>
                        </div>
                        
                        <p className="text-sm text-gray-700 mb-2">{resource.description}</p>
                        
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-1 text-xs text-gray-600">
                            <Clock className="h-3 w-3" />
                            <span>{resource.availability}</span>
                          </div>
                          {resource.website && (
                            <a
                              href={resource.website}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-primary-600 hover:text-primary-700 flex items-center"
                            >
                              Website <ExternalLink className="h-3 w-3 ml-1" />
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Specific Emergency Situations */}
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-900 mb-4">Specific Emergency Situations</h4>
              <div className="space-y-4">
                
                {/* Legal Emergencies */}
                <div className="border border-blue-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <Gavel className="h-5 w-5 text-blue-600" />
                    <h5 className="font-medium text-blue-900">Legal Emergencies</h5>
                  </div>
                  <div className="space-y-2 text-sm text-blue-800">
                    <div>
                      <strong>Eviction Notice:</strong> Contact local legal aid immediately - you may have very limited time to respond
                    </div>
                    <div>
                      <strong>Restraining Order Violation:</strong> Call 911 if there's immediate danger, then contact your attorney
                    </div>
                    <div>
                      <strong>Immigration Detention:</strong> Contact an immigration attorney immediately - time is critical
                    </div>
                    <div>
                      <strong>Child Custody Emergency:</strong> Call police if child safety is at risk, then contact family court
                    </div>
                  </div>
                </div>

                {/* Safety Emergencies */}
                <div className="border border-error-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <Shield className="h-5 w-5 text-error-600" />
                    <h5 className="font-medium text-error-900">Personal Safety Emergencies</h5>
                  </div>
                  <div className="space-y-2 text-sm text-error-800">
                    <div>
                      <strong>Domestic Violence:</strong> Call 911 for immediate danger, National Hotline: 1-800-799-7233
                    </div>
                    <div>
                      <strong>Stalking/Harassment:</strong> Document incidents, call police, consider restraining order
                    </div>
                    <div>
                      <strong>Child Abuse:</strong> Call 911 or Child Abuse Hotline: 1-800-4-A-CHILD (1-800-422-4453)
                    </div>
                    <div>
                      <strong>Elder Abuse:</strong> Contact Adult Protective Services in your county
                    </div>
                  </div>
                </div>

                {/* Crisis Support */}
                <div className="border border-purple-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <Heart className="h-5 w-5 text-purple-600" />
                    <h5 className="font-medium text-purple-900">Mental Health Crisis</h5>
                  </div>
                  <div className="space-y-2 text-sm text-purple-800">
                    <div>
                      <strong>Suicide Risk:</strong> Call 988 (Suicide & Crisis Lifeline) or 911
                    </div>
                    <div>
                      <strong>Mental Health Emergency:</strong> Call 911 or go to nearest emergency room
                    </div>
                    <div>
                      <strong>Crisis Text Line:</strong> Text HOME to 741741 for crisis support
                    </div>
                    <div>
                      <strong>LGBTQ+ Crisis:</strong> Trevor Project: 1-866-488-7386
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* After-Hours Legal Emergencies */}
            <div className="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <Info className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-amber-800 mb-2">After-Hours Legal Emergencies</h5>
                  <div className="text-sm text-amber-700 space-y-1">
                    <p>If you have a legal emergency outside of business hours:</p>
                    <ul className="space-y-1 ml-4 mt-2">
                      <li>• For immediate safety issues: Call 911</li>
                      <li>• For urgent legal matters: Many law firms have emergency contact procedures</li>
                      <li>• Check if your local court has emergency filing procedures</li>
                      <li>• Some legal aid organizations have emergency hotlines</li>
                      <li>• Document everything while waiting for legal assistance</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Important Reminders */}
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <Clock className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-blue-900 mb-2">Important Reminders</h5>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Keep important phone numbers easily accessible</li>
                    <li>• Save your attorney's emergency contact information</li>
                    <li>• Know your local court's emergency procedures</li>
                    <li>• Have important documents in a safe, accessible place</li>
                    <li>• If in doubt about urgency, err on the side of calling for help</li>
                    <li>• Document any incidents with dates, times, and details</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Privacy Notice */}
            <div className="bg-legal-50 border border-legal-200 rounded-lg p-4 mb-4">
              <div className="flex items-start space-x-3">
                <Scale className="h-5 w-5 text-legal-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-legal-900 mb-2">Privacy and Confidentiality</h5>
                  <div className="text-sm text-legal-700 space-y-1">
                    <p>
                      <strong>Crisis Hotlines:</strong> Most crisis hotlines maintain confidentiality, but may report 
                      if there's immediate danger to you or others.
                    </p>
                    <p>
                      <strong>Legal Communications:</strong> Emergency communications with attorneys may be privileged, 
                      but communications with non-lawyer staff may not be protected.
                    </p>
                    <p>
                      <strong>911 Calls:</strong> All 911 calls are recorded and may be used as evidence in legal proceedings.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Close Button */}
            <div className="text-center">
              <button
                onClick={() => setShowEmergencyInfo(false)}
                className="inline-flex items-center px-6 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
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

export default EmergencyContact;