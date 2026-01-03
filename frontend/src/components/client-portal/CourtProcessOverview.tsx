'use client';

import React, { useState } from 'react';
import {
  Building,
  Users,
  Gavel,
  Scale,
  Clock,
  FileText,
  Info,
  AlertTriangle,
  BookOpen,
  Shield,
  CheckCircle,
  ArrowRight,
  HelpCircle
} from 'lucide-react';

interface CourtProcessStep {
  id: string;
  title: string;
  description: string;
  whoIsInvolved: string[];
  whatHappens: string[];
  clientRole: string[];
  duration: string;
  canSkip: boolean;
  commonOutcomes: string[];
}

interface CourtRole {
  title: string;
  description: string;
  responsibilities: string[];
  icon: React.ReactNode;
}

interface CourtProcessOverviewProps {
  processType?: 'civil' | 'family' | 'criminal' | 'general';
  className?: string;
}

const CourtProcessOverview: React.FC<CourtProcessOverviewProps> = ({
  processType = 'general',
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'process' | 'roles' | 'expectations'>('overview');
  const [selectedStep, setSelectedStep] = useState<string | null>(null);

  const courtRoles: CourtRole[] = [
    {
      title: 'Judge',
      description: 'Neutral decision-maker who presides over court proceedings',
      responsibilities: [
        'Ensures fair and orderly proceedings',
        'Rules on legal motions and objections',
        'Makes decisions on matters of law',
        'In bench trials, decides the outcome',
        'Sentences in criminal cases if applicable'
      ],
      icon: <Gavel className="h-5 w-5" />
    },
    {
      title: 'Attorneys',
      description: 'Legal representatives who advocate for their clients',
      responsibilities: [
        'Present legal arguments and evidence',
        'Cross-examine witnesses',
        'File motions and legal documents',
        'Negotiate settlements',
        'Advise clients on legal strategy'
      ],
      icon: <Users className="h-5 w-5" />
    },
    {
      title: 'Court Clerk',
      description: 'Administrative officer who manages court records and procedures',
      responsibilities: [
        'Maintains court records and files',
        'Schedules hearings and trials',
        'Administers oaths to witnesses',
        'Collects filing fees',
        'Assists with procedural questions'
      ],
      icon: <FileText className="h-5 w-5" />
    },
    {
      title: 'Court Reporter',
      description: 'Records verbatim transcript of court proceedings',
      responsibilities: [
        'Creates official record of proceedings',
        'Transcribes testimony and arguments',
        'Provides copies of transcripts',
        'May read back testimony during trial',
        'Ensures accuracy of legal record'
      ],
      icon: <BookOpen className="h-5 w-5" />
    },
    {
      title: 'Bailiff/Court Security',
      description: 'Maintains order and security in the courtroom',
      responsibilities: [
        'Ensures courtroom safety and order',
        'Escorts parties and witnesses',
        'Manages courtroom during proceedings',
        'Assists with logistics',
        'Handles disruptions if they occur'
      ],
      icon: <Shield className="h-5 w-5" />
    }
  ];

  const getProcessSteps = (type: string): CourtProcessStep[] => {
    const commonSteps: CourtProcessStep[] = [
      {
        id: 'filing',
        title: 'Case Filing & Service',
        description: 'Initial legal documents are filed with the court and served on all parties',
        whoIsInvolved: ['Plaintiff/Petitioner', 'Court Clerk', 'Process Server'],
        whatHappens: [
          'Complaint or petition is filed with court',
          'Filing fees are paid',
          'Case number is assigned',
          'Documents are served on defendants',
          'Proof of service is filed'
        ],
        clientRole: [
          'Provide accurate information for documents',
          'Pay required filing fees',
          'Ensure proper service of documents',
          'Keep copies of all filed documents'
        ],
        duration: '1-2 weeks',
        canSkip: false,
        commonOutcomes: [
          'Case officially begins',
          'Defendants must respond within deadline',
          'Court scheduling begins'
        ]
      },
      {
        id: 'response',
        title: 'Response Period',
        description: 'Defendants respond to the initial filing',
        whoIsInvolved: ['Defendants', 'Their attorneys', 'Court'],
        whatHappens: [
          'Defendants file answer or other response',
          'May include counterclaims or cross-claims',
          'Court reviews filings for completeness',
          'Case management begins'
        ],
        clientRole: [
          'If defendant: File timely response',
          'If plaintiff: Review response for accuracy',
          'Prepare for next phase of litigation',
          'Communicate with attorney about strategy'
        ],
        duration: '20-30 days typically',
        canSkip: false,
        commonOutcomes: [
          'Issues are defined and narrowed',
          'Discovery phase can begin',
          'Settlement discussions may start'
        ]
      },
      {
        id: 'discovery',
        title: 'Discovery Phase',
        description: 'Both sides exchange information and gather evidence',
        whoIsInvolved: ['All parties', 'Attorneys', 'Witnesses', 'Experts'],
        whatHappens: [
          'Document requests and production',
          'Written questions (interrogatories)',
          'Depositions of parties and witnesses',
          'Expert witness preparation',
          'Evidence compilation'
        ],
        clientRole: [
          'Respond to discovery requests truthfully',
          'Produce requested documents',
          'Participate in depositions',
          'Help locate witnesses and evidence'
        ],
        duration: '3-12 months',
        canSkip: false,
        commonOutcomes: [
          'Each side learns about the other\'s case',
          'Evidence is preserved and organized',
          'Settlement negotiations may intensify'
        ]
      },
      {
        id: 'pre-trial',
        title: 'Pre-Trial Motions & Conferences',
        description: 'Court addresses procedural issues and prepares for trial',
        whoIsInvolved: ['Judge', 'All attorneys', 'Parties as needed'],
        whatHappens: [
          'Motions to exclude evidence or dismiss claims',
          'Settlement conferences',
          'Pre-trial scheduling and logistics',
          'Witness and exhibit lists finalized'
        ],
        clientRole: [
          'Attend required conferences',
          'Participate in settlement discussions',
          'Review trial preparation with attorney',
          'Prepare for potential testimony'
        ],
        duration: '1-3 months',
        canSkip: true,
        commonOutcomes: [
          'Some issues may be resolved without trial',
          'Trial procedures are established',
          'Many cases settle during this phase'
        ]
      },
      {
        id: 'trial',
        title: 'Trial',
        description: 'Formal court proceeding where evidence is presented',
        whoIsInvolved: ['Judge', 'Jury (if applicable)', 'All parties', 'Attorneys', 'Witnesses'],
        whatHappens: [
          'Opening statements by each side',
          'Presentation of evidence and testimony',
          'Cross-examination of witnesses',
          'Closing arguments',
          'Judge or jury deliberation and verdict'
        ],
        clientRole: [
          'Attend all proceedings',
          'Testify if called as witness',
          'Assist attorney with case presentation',
          'Maintain courtroom decorum'
        ],
        duration: '1 day to several weeks',
        canSkip: true,
        commonOutcomes: [
          'Binding decision on disputed issues',
          'Monetary judgment or other relief',
          'Case resolution (subject to appeals)'
        ]
      },
      {
        id: 'post-trial',
        title: 'Post-Trial & Enforcement',
        description: 'Implementation of court decisions and potential appeals',
        whoIsInvolved: ['Winning party', 'Losing party', 'Court', 'Collection agencies if needed'],
        whatHappens: [
          'Judgment entry and finalization',
          'Appeal deadlines and procedures',
          'Collection or enforcement efforts',
          'Compliance with court orders'
        ],
        clientRole: [
          'Comply with all court orders',
          'Pursue collection if owed money',
          'Consider appeal options with attorney',
          'Maintain records of compliance'
        ],
        duration: 'Ongoing as needed',
        canSkip: false,
        commonOutcomes: [
          'Final resolution of legal dispute',
          'Collection of awarded damages',
          'Compliance with court orders'
        ]
      }
    ];

    return commonSteps;
  };

  const processSteps = getProcessSteps(processType);

  const tabs = [
    { key: 'overview', label: 'Court Overview', icon: Building },
    { key: 'process', label: 'Process Steps', icon: ArrowRight },
    { key: 'roles', label: 'Court Roles', icon: Users },
    { key: 'expectations', label: 'What to Expect', icon: HelpCircle }
  ];

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <Building className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-medium text-gray-900">How Courts Work</h3>
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <Info className="h-3 w-3 mr-1" />
          Educational Guide
        </span>
      </div>

      {/* Tab Navigation */}
      <div className="mb-6">
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="space-y-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-4">Understanding the Court System</h4>
            
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <Scale className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h5 className="text-sm font-semibold text-blue-900 mb-2">What Courts Do</h5>
                    <p className="text-sm text-blue-800 mb-2">
                      Courts are neutral forums where legal disputes are resolved according to law. They provide 
                      a structured process for parties to present their cases and receive fair decisions.
                    </p>
                    <ul className="text-sm text-blue-700 space-y-1">
                      <li>• Interpret and apply laws to specific situations</li>
                      <li>• Ensure fair procedures for all parties</li>
                      <li>• Provide binding resolutions to legal disputes</li>
                      <li>• Protect constitutional rights and due process</li>
                      <li>• Enforce judgments and court orders</li>
                    </ul>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Gavel className="h-4 w-4 text-purple-600" />
                    <h5 className="text-sm font-semibold text-gray-900">Types of Court Proceedings</h5>
                  </div>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li><strong>Civil Cases:</strong> Disputes between individuals, businesses, or organizations</li>
                    <li><strong>Family Cases:</strong> Divorce, custody, adoption, and domestic relations</li>
                    <li><strong>Criminal Cases:</strong> Government prosecution of alleged crimes</li>
                    <li><strong>Small Claims:</strong> Simplified process for smaller monetary disputes</li>
                  </ul>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Clock className="h-4 w-4 text-green-600" />
                    <h5 className="text-sm font-semibold text-gray-900">Court Timelines</h5>
                  </div>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li><strong>Simple Cases:</strong> 3-6 months</li>
                    <li><strong>Complex Cases:</strong> 1-3 years</li>
                    <li><strong>Appeals:</strong> Additional 6-18 months</li>
                    <li><strong>Factors:</strong> Court backlog, case complexity, settlement negotiations</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Process Steps Tab */}
        {activeTab === 'process' && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-4">Typical Court Process</h4>
            <p className="text-sm text-gray-600 mb-6">
              Most court cases follow a similar progression. Click on each step to learn more about what happens 
              and what your role might be.
            </p>

            <div className="space-y-4">
              {processSteps.map((step, index) => (
                <div key={step.id} className="relative">
                  {/* Connecting line */}
                  {index < processSteps.length - 1 && (
                    <div className="absolute left-6 top-12 w-px h-16 bg-gray-300"></div>
                  )}
                  
                  <div
                    className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-sm ${
                      selectedStep === step.id 
                        ? 'border-primary-300 bg-primary-50' 
                        : 'border-gray-200 bg-white'
                    }`}
                    onClick={() => setSelectedStep(selectedStep === step.id ? null : step.id)}
                  >
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0 mt-1">
                        <div className="w-8 h-8 bg-primary-100 text-primary-800 rounded-full flex items-center justify-center text-sm font-medium">
                          {index + 1}
                        </div>
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <div>
                            <h5 className="font-medium text-gray-900">{step.title}</h5>
                            <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                              <span>Duration: {step.duration}</span>
                              {step.canSkip && (
                                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-yellow-100 text-yellow-800">
                                  May be skipped
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="text-gray-400">
                            {selectedStep === step.id ? '−' : '+'}
                          </div>
                        </div>

                        {/* Expanded Details */}
                        {selectedStep === step.id && (
                          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <h6 className="text-sm font-semibold text-gray-900 mb-2">What Happens</h6>
                              <ul className="text-sm text-gray-700 space-y-1">
                                {step.whatHappens.map((item, idx) => (
                                  <li key={idx} className="flex items-start space-x-2">
                                    <span className="text-blue-500 mt-1">•</span>
                                    <span>{item}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>

                            <div>
                              <h6 className="text-sm font-semibold text-gray-900 mb-2">Your Role</h6>
                              <ul className="text-sm text-gray-700 space-y-1">
                                {step.clientRole.map((role, idx) => (
                                  <li key={idx} className="flex items-start space-x-2">
                                    <span className="text-primary-500 mt-1">•</span>
                                    <span>{role}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>

                            <div className="md:col-span-2">
                              <h6 className="text-sm font-semibold text-gray-900 mb-2">Common Outcomes</h6>
                              <ul className="text-sm text-gray-700 space-y-1">
                                {step.commonOutcomes.map((outcome, idx) => (
                                  <li key={idx} className="flex items-start space-x-2">
                                    <CheckCircle className="h-3 w-3 text-green-500 mt-1 flex-shrink-0" />
                                    <span>{outcome}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Court Roles Tab */}
        {activeTab === 'roles' && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-4">People in the Courtroom</h4>
            <p className="text-sm text-gray-600 mb-6">
              Understanding who does what in court can help you feel more prepared and confident during proceedings.
            </p>

            <div className="space-y-4">
              {courtRoles.map((role, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <div className="text-blue-600 mt-1">
                      {role.icon}
                    </div>
                    <div className="flex-1">
                      <h5 className="font-medium text-gray-900 mb-1">{role.title}</h5>
                      <p className="text-sm text-gray-600 mb-3">{role.description}</p>
                      
                      <h6 className="text-sm font-semibold text-gray-900 mb-2">Key Responsibilities:</h6>
                      <ul className="text-sm text-gray-700 space-y-1">
                        {role.responsibilities.map((responsibility, idx) => (
                          <li key={idx} className="flex items-start space-x-2">
                            <span className="text-blue-500 mt-1">•</span>
                            <span>{responsibility}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* What to Expect Tab */}
        {activeTab === 'expectations' && (
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-4">What to Expect in Court</h4>

            <div className="space-y-6">
              {/* Courtroom Behavior */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <Users className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h5 className="text-sm font-semibold text-blue-900 mb-2">Courtroom Etiquette</h5>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
                      <div>
                        <h6 className="font-semibold mb-1">Do:</h6>
                        <ul className="space-y-1">
                          <li>• Dress professionally and conservatively</li>
                          <li>• Arrive early and check in with clerk</li>
                          <li>• Stand when judge enters/leaves</li>
                          <li>• Address judge as "Your Honor"</li>
                          <li>• Speak only when asked</li>
                          <li>• Turn off all electronic devices</li>
                        </ul>
                      </div>
                      <div>
                        <h6 className="font-semibold mb-1">Don't:</h6>
                        <ul className="space-y-1">
                          <li>• Interrupt or argue with judge</li>
                          <li>• Speak directly to opposing party</li>
                          <li>• Bring food or drink into courtroom</li>
                          <li>• Display emotions dramatically</li>
                          <li>• Leave without permission</li>
                          <li>• Take photos or recordings</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Common Concerns */}
              <div>
                <h5 className="text-sm font-semibold text-gray-900 mb-3">Common Client Concerns</h5>
                <div className="space-y-3">
                  <div className="border border-gray-200 rounded-lg p-3">
                    <h6 className="text-sm font-medium text-gray-900 mb-1">"Will I have to testify?"</h6>
                    <p className="text-sm text-gray-700">
                      Not always. Your attorney will advise whether testifying is beneficial to your case. 
                      If you do testify, your attorney will prepare you beforehand.
                    </p>
                  </div>

                  <div className="border border-gray-200 rounded-lg p-3">
                    <h6 className="text-sm font-medium text-gray-900 mb-1">"How long will court take?"</h6>
                    <p className="text-sm text-gray-700">
                      Court proceedings can range from 30 minutes for simple hearings to several days for complex trials. 
                      Your attorney can give you estimates based on your case.
                    </p>
                  </div>

                  <div className="border border-gray-200 rounded-lg p-3">
                    <h6 className="text-sm font-medium text-gray-900 mb-1">"What if I don't understand something?"</h6>
                    <p className="text-sm text-gray-700">
                      Ask your attorney to explain anything unclear before or after court. During proceedings, 
                      your attorney can request clarification from the judge if needed.
                    </p>
                  </div>

                  <div className="border border-gray-200 rounded-lg p-3">
                    <h6 className="text-sm font-medium text-gray-900 mb-1">"Can I bring family or friends?"</h6>
                    <p className="text-sm text-gray-700">
                      Most court proceedings are public, but check with your attorney. Some family court 
                      proceedings may be closed. Support persons usually sit in the gallery (back of courtroom).
                    </p>
                  </div>
                </div>
              </div>

              {/* Preparation Tips */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h5 className="text-sm font-semibold text-green-900 mb-2">How to Prepare</h5>
                    <ul className="text-sm text-green-800 space-y-1">
                      <li>• Meet with your attorney to review case strategy and expectations</li>
                      <li>• Organize all relevant documents in chronological order</li>
                      <li>• Practice answering potential questions honestly and clearly</li>
                      <li>• Visit the courthouse beforehand to familiarize yourself with layout</li>
                      <li>• Plan to arrive 30 minutes early to account for security and parking</li>
                      <li>• Bring water and any necessary medications</li>
                      <li>• Prepare emotionally for potentially stressful testimony</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Important Reminders */}
      <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-amber-800 mb-2">Important Reminders</h5>
            <ul className="text-sm text-amber-700 space-y-1">
              <li>• Court procedures vary by jurisdiction and case type</li>
              <li>• Always follow your attorney's specific guidance for your case</li>
              <li>• Missing court appearances can seriously harm your case</li>
              <li>• Settlement can occur at any stage and may avoid trial entirely</li>
              <li>• The court process can be lengthy - patience is important</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Educational Disclaimer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-xs font-semibold text-legal-900 mb-1">Court Process Information Disclaimer</h5>
              <p className="text-xs text-legal-700">
                This information provides general education about court processes. Actual procedures vary 
                significantly by jurisdiction, court rules, and case specifics. Always follow your attorney's 
                guidance and local court rules for your specific situation.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CourtProcessOverview;