'use client';

import React, { useState } from 'react';
import {
  BookOpen,
  Info,
  AlertTriangle,
  Scale,
  Clock,
  Users,
  FileText,
  HelpCircle,
  ExternalLink
} from 'lucide-react';

interface CaseTypeExplainerProps {
  caseType: string;
  className?: string;
}

interface CaseTypeInfo {
  title: string;
  description: string;
  commonSteps: string[];
  typicalDuration: string;
  keyConsiderations: string[];
  commonChallenges: string[];
  resources: Array<{
    title: string;
    description: string;
    url: string;
    isExternal: boolean;
  }>;
}

const CaseTypeExplainer: React.FC<CaseTypeExplainerProps> = ({ 
  caseType, 
  className = '' 
}) => {
  const [activeSection, setActiveSection] = useState<'overview' | 'process' | 'timeline' | 'resources'>('overview');

  const getCaseTypeInfo = (type: string): CaseTypeInfo => {
    switch (type.toLowerCase()) {
      case 'personal injury':
        return {
          title: 'Personal Injury Cases',
          description: 'Personal injury cases involve seeking compensation for injuries caused by another party\'s negligence or wrongful actions. These cases can include car accidents, slip and falls, medical malpractice, and product liability claims.',
          commonSteps: [
            'Initial consultation and case evaluation',
            'Investigation and evidence gathering',
            'Medical treatment and documentation',
            'Demand letter to insurance company',
            'Negotiation with insurance adjusters',
            'Filing lawsuit if settlement not reached',
            'Discovery phase (exchanging information)',
            'Mediation or settlement conferences',
            'Trial preparation and court proceedings',
            'Resolution through settlement or verdict'
          ],
          typicalDuration: '6 months to 3 years, depending on case complexity and settlement negotiations',
          keyConsiderations: [
            'Statute of limitations varies by state (typically 1-6 years)',
            'Medical documentation is crucial for proving damages',
            'Comparative negligence laws may reduce compensation',
            'Insurance policy limits may affect recovery amount',
            'Pre-existing conditions can complicate claims'
          ],
          commonChallenges: [
            'Proving fault and liability',
            'Documenting the full extent of injuries',
            'Dealing with insurance company tactics',
            'Calculating future medical expenses and lost wages',
            'Managing medical treatment during case'
          ],
          resources: [
            {
              title: 'American Bar Association - Personal Injury',
              description: 'General information about personal injury law',
              url: 'https://www.americanbar.org/groups/tort_trial_insurance_practice/',
              isExternal: true
            },
            {
              title: 'State Insurance Commissioner',
              description: 'Information about insurance regulations in your state',
              url: '/resources/insurance-info',
              isExternal: false
            }
          ]
        };

      case 'family law':
        return {
          title: 'Family Law Cases',
          description: 'Family law cases involve legal matters related to family relationships, including divorce, child custody, adoption, domestic violence, and property division. These cases often have both legal and emotional components.',
          commonSteps: [
            'Initial consultation and assessment',
            'Filing petition or response',
            'Temporary orders (if needed)',
            'Financial disclosure and discovery',
            'Mediation or settlement negotiations',
            'Court hearings and motions',
            'Final trial (if no settlement)',
            'Judgment and decree entry',
            'Post-judgment modifications (if applicable)'
          ],
          typicalDuration: '6 months to 2 years for divorce; varies significantly for other family matters',
          keyConsiderations: [
            'Best interests of children are primary concern',
            'State residency requirements must be met',
            'Financial disclosure is typically required',
            'Mediation may be mandatory in some jurisdictions',
            'Domestic violence can affect all aspects of case'
          ],
          commonChallenges: [
            'Emotional stress and family dynamics',
            'Complex financial asset valuation',
            'Child custody and parenting time disputes',
            'Coordinating court schedules with work and family',
            'Managing costs of extended litigation'
          ],
          resources: [
            {
              title: 'National Center for State Courts - Family',
              description: 'Self-help resources for family law matters',
              url: 'https://www.ncsc.org/topics/family-and-juvenile',
              isExternal: true
            },
            {
              title: 'Local Family Court Self-Help Center',
              description: 'Court-provided assistance for family law cases',
              url: '/resources/family-court-help',
              isExternal: false
            }
          ]
        };

      case 'criminal defense':
        return {
          title: 'Criminal Defense Cases',
          description: 'Criminal defense involves protecting the rights of individuals accused of crimes. The prosecution must prove guilt beyond a reasonable doubt, while the defense works to challenge the evidence and protect constitutional rights.',
          commonSteps: [
            'Arrest and initial appearance',
            'Bail hearing and pretrial release',
            'Arraignment and plea entry',
            'Discovery and evidence review',
            'Pretrial motions and hearings',
            'Plea negotiations with prosecutor',
            'Trial preparation and jury selection',
            'Trial proceedings and verdict',
            'Sentencing (if convicted)',
            'Appeal process (if applicable)'
          ],
          typicalDuration: '3 months to 2+ years depending on charge severity and court system',
          keyConsiderations: [
            'Constitutional rights must be protected throughout',
            'Right to remain silent and have attorney present',
            'Burden of proof is on the prosecution',
            'Plea agreements may resolve case without trial',
            'Prior criminal history can affect sentencing'
          ],
          commonChallenges: [
            'Stress and anxiety about potential consequences',
            'Understanding complex criminal procedures',
            'Coordinating with work and family obligations',
            'Financial costs of defense',
            'Media attention in high-profile cases'
          ],
          resources: [
            {
              title: 'National Association of Criminal Defense Lawyers',
              description: 'Information about criminal defense rights',
              url: 'https://www.nacdl.org/',
              isExternal: true
            },
            {
              title: 'Public Defender Information',
              description: 'Information about court-appointed attorneys',
              url: '/resources/public-defender',
              isExternal: false
            }
          ]
        };

      default:
        return {
          title: 'General Legal Case Information',
          description: 'Legal cases involve disputes or matters that require resolution through the legal system. Each case type has specific procedures, requirements, and considerations.',
          commonSteps: [
            'Initial consultation and case assessment',
            'Legal research and strategy development',
            'Document preparation and filing',
            'Discovery and information exchange',
            'Settlement negotiations',
            'Court proceedings (if necessary)',
            'Resolution and follow-up'
          ],
          typicalDuration: 'Varies significantly based on case type and complexity',
          keyConsiderations: [
            'Statute of limitations may limit time to file',
            'Legal procedures must be followed precisely',
            'Evidence gathering is crucial',
            'Costs can vary significantly',
            'Settlement may be preferable to trial'
          ],
          commonChallenges: [
            'Understanding legal procedures and requirements',
            'Managing time and costs',
            'Dealing with opposing parties',
            'Gathering necessary evidence and documentation',
            'Navigating court system complexities'
          ],
          resources: [
            {
              title: 'American Bar Association',
              description: 'General legal information and resources',
              url: 'https://www.americanbar.org/',
              isExternal: true
            }
          ]
        };
    }
  };

  const caseInfo = getCaseTypeInfo(caseType);

  const sections = [
    { key: 'overview', label: 'Overview', icon: BookOpen },
    { key: 'process', label: 'Process', icon: FileText },
    { key: 'timeline', label: 'Timeline', icon: Clock },
    { key: 'resources', label: 'Resources', icon: HelpCircle }
  ];

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <Scale className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-medium text-gray-900">Understanding Your Case Type</h3>
      </div>

      {/* Section Navigation */}
      <div className="flex space-x-1 mb-6 bg-gray-100 rounded-lg p-1">
        {sections.map((section) => (
          <button
            key={section.key}
            onClick={() => setActiveSection(section.key as any)}
            className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              activeSection === section.key
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <section.icon className="h-4 w-4" />
            <span>{section.label}</span>
          </button>
        ))}
      </div>

      {/* Content Sections */}
      <div className="space-y-4">
        {/* Overview Section */}
        {activeSection === 'overview' && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-3">{caseInfo.title}</h4>
            <p className="text-sm text-gray-700 mb-4">{caseInfo.description}</p>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-blue-900 mb-2">Key Considerations for Your Case Type</h5>
                  <ul className="text-sm text-blue-800 space-y-1">
                    {caseInfo.keyConsiderations.map((consideration, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-blue-600 mt-1">•</span>
                        <span>{consideration}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Process Section */}
        {activeSection === 'process' && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-3">Typical Case Process</h4>
            <p className="text-sm text-gray-600 mb-4">
              Here are the common steps in {caseType.toLowerCase()} cases. Your specific case may vary.
            </p>
            
            <div className="space-y-3">
              {caseInfo.commonSteps.map((step, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <span className="flex items-center justify-center w-6 h-6 bg-primary-100 text-primary-800 rounded-full text-xs font-medium">
                    {index + 1}
                  </span>
                  <p className="text-sm text-gray-700">{step}</p>
                </div>
              ))}
            </div>

            <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-amber-800 mb-1">Common Challenges</h5>
                  <ul className="text-sm text-amber-700 space-y-1">
                    {caseInfo.commonChallenges.map((challenge, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-amber-600 mt-1">•</span>
                        <span>{challenge}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Timeline Section */}
        {activeSection === 'timeline' && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-3">Typical Timeline</h4>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <Clock className="h-5 w-5 text-gray-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-gray-900 mb-1">Expected Duration</h5>
                  <p className="text-sm text-gray-700">{caseInfo.typicalDuration}</p>
                </div>
              </div>
            </div>

            <div className="mt-4 space-y-3">
              <h5 className="text-sm font-semibold text-gray-900">Factors That May Affect Timeline:</h5>
              <ul className="text-sm text-gray-700 space-y-2">
                <li className="flex items-start space-x-2">
                  <span className="text-gray-500 mt-1">•</span>
                  <span>Case complexity and number of parties involved</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-gray-500 mt-1">•</span>
                  <span>Court scheduling and availability</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-gray-500 mt-1">•</span>
                  <span>Settlement negotiations and willingness to compromise</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-gray-500 mt-1">•</span>
                  <span>Discovery process and evidence gathering</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-gray-500 mt-1">•</span>
                  <span>Appeals process (if applicable)</span>
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* Resources Section */}
        {activeSection === 'resources' && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-3">Additional Resources</h4>
            <div className="space-y-3">
              {caseInfo.resources.map((resource, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h5 className="text-sm font-semibold text-gray-900 mb-1">{resource.title}</h5>
                      <p className="text-sm text-gray-600">{resource.description}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      {resource.isExternal && (
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-gray-100 text-gray-600">
                          <ExternalLink className="h-3 w-3 mr-1" />
                          External
                        </span>
                      )}
                      <a
                        href={resource.url}
                        target={resource.isExternal ? "_blank" : undefined}
                        rel={resource.isExternal ? "noopener noreferrer" : undefined}
                        className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                      >
                        View Resource
                      </a>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <BookOpen className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h5 className="text-sm font-semibold text-blue-900 mb-1">Need More Help?</h5>
                  <p className="text-sm text-blue-800">
                    If you need legal advice specific to your situation, consult with a qualified attorney. 
                    General information cannot replace personalized legal counsel.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Important Disclaimer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-xs font-semibold text-legal-900 mb-1">Educational Information Only</h5>
              <p className="text-xs text-legal-700">
                This information is general and educational only. It does not constitute legal advice for your specific situation. 
                Every case is unique and requires individual analysis by a qualified attorney.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CaseTypeExplainer;