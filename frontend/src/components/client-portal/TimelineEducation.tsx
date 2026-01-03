'use client';

import React, { useState } from 'react';
import {
  Clock,
  Calendar,
  CheckCircle,
  Circle,
  AlertTriangle,
  Info,
  Scale,
  FileText,
  Users,
  Gavel
} from 'lucide-react';

interface TimelineEducationProps {
  caseType: string;
  className?: string;
}

interface TimelinePhase {
  id: string;
  title: string;
  description: string;
  typicalDuration: string;
  keyActivities: string[];
  whatToExpect: string[];
  yourRole: string[];
  status: 'completed' | 'current' | 'upcoming';
}

const TimelineEducation: React.FC<TimelineEducationProps> = ({
  caseType,
  className = ''
}) => {
  const [selectedPhase, setSelectedPhase] = useState<TimelinePhase | null>(null);

  const getTimelinePhases = (type: string): TimelinePhase[] => {
    switch (type.toLowerCase()) {
      case 'personal injury':
        return [
          {
            id: 'consultation',
            title: 'Initial Consultation',
            description: 'Attorney evaluates your case and explains your rights and options.',
            typicalDuration: '1-2 weeks',
            keyActivities: [
              'Case evaluation and merit assessment',
              'Explanation of legal rights and options',
              'Discussion of fee arrangements',
              'Signing of representation agreement'
            ],
            whatToExpect: [
              'Detailed discussion about your accident and injuries',
              'Review of medical records and documentation',
              'Explanation of legal process and timeline',
              'Questions about insurance coverage and benefits'
            ],
            yourRole: [
              'Provide complete and honest information',
              'Bring all relevant documents and records',
              'Ask questions about the process',
              'Follow medical treatment recommendations'
            ],
            status: 'completed'
          },
          {
            id: 'investigation',
            title: 'Investigation & Evidence Gathering',
            description: 'Comprehensive investigation to build a strong case foundation.',
            typicalDuration: '2-6 months',
            keyActivities: [
              'Accident scene investigation and documentation',
              'Medical records collection and review',
              'Witness interviews and statements',
              'Expert consultation and accident reconstruction'
            ],
            whatToExpect: [
              'Requests for medical records and bills',
              'Interviews with witnesses to the accident',
              'Consultation with medical experts',
              'Documentation of ongoing treatment and recovery'
            ],
            yourRole: [
              'Continue medical treatment as prescribed',
              'Keep detailed records of treatments and expenses',
              'Avoid discussing the case on social media',
              'Report any new symptoms or medical issues promptly'
            ],
            status: 'current'
          },
          {
            id: 'demand',
            title: 'Demand & Negotiation',
            description: 'Formal demand for compensation and initial settlement negotiations.',
            typicalDuration: '2-4 months',
            keyActivities: [
              'Preparation of demand letter with documentation',
              'Submission to insurance company',
              'Initial settlement discussions',
              'Evaluation of settlement offers'
            ],
            whatToExpect: [
              'Comprehensive demand package preparation',
              'Insurance company investigation and review',
              'Back-and-forth negotiation discussions',
              'Regular updates on negotiation progress'
            ],
            yourRole: [
              'Review and approve demand documentation',
              'Provide input on settlement considerations',
              'Continue medical treatment until maximum improvement',
              'Be patient during negotiation process'
            ],
            status: 'upcoming'
          },
          {
            id: 'litigation',
            title: 'Litigation (if needed)',
            description: 'Filing lawsuit and proceeding through formal court process.',
            typicalDuration: '12-24 months',
            keyActivities: [
              'Filing complaint and serving defendants',
              'Discovery process and depositions',
              'Motion practice and court hearings',
              'Trial preparation and proceedings'
            ],
            whatToExpect: [
              'Formal court filings and legal documents',
              'Depositions and sworn testimony',
              'Requests for additional documentation',
              'Possible mediation or settlement conferences'
            ],
            yourRole: [
              'Participate in depositions and court proceedings',
              'Provide additional information as requested',
              'Maintain communication with legal team',
              'Prepare for potential trial testimony'
            ],
            status: 'upcoming'
          }
        ];

      case 'family law':
        return [
          {
            id: 'consultation',
            title: 'Initial Consultation',
            description: 'Assessment of your family law matter and exploration of options.',
            typicalDuration: '1-2 weeks',
            keyActivities: [
              'Discussion of family situation and goals',
              'Review of relevant documents and records',
              'Explanation of applicable laws and procedures',
              'Development of initial strategy'
            ],
            whatToExpect: [
              'Detailed discussion about family dynamics',
              'Review of financial documents and assets',
              'Discussion of child custody considerations',
              'Explanation of court processes and timelines'
            ],
            yourRole: [
              'Provide complete financial disclosure',
              'Share custody preferences and concerns',
              'Bring all relevant documents',
              'Be honest about family circumstances'
            ],
            status: 'completed'
          },
          {
            id: 'filing',
            title: 'Filing & Initial Orders',
            description: 'Filing necessary court documents and obtaining temporary orders.',
            typicalDuration: '1-3 months',
            keyActivities: [
              'Preparation and filing of petitions',
              'Service of process on other parties',
              'Request for temporary orders',
              'Initial court appearances'
            ],
            whatToExpect: [
              'Court filing fees and document preparation',
              'Formal service of legal documents',
              'Temporary custody and support arrangements',
              'Initial court hearing appearances'
            ],
            yourRole: [
              'Provide accurate information for court documents',
              'Comply with temporary court orders',
              'Attend required court hearings',
              'Maintain detailed records of expenses'
            ],
            status: 'current'
          },
          {
            id: 'discovery',
            title: 'Discovery & Financial Disclosure',
            description: 'Exchange of financial information and evidence gathering.',
            typicalDuration: '3-6 months',
            keyActivities: [
              'Financial disclosure statements',
              'Asset valuation and appraisals',
              'Custody evaluation (if applicable)',
              'Depositions and document production'
            ],
            whatToExpect: [
              'Extensive financial documentation requests',
              'Property and asset valuations',
              'Child custody evaluations and interviews',
              'Meetings with financial experts'
            ],
            yourRole: [
              'Complete financial disclosure forms accurately',
              'Cooperate with custody evaluators',
              'Provide requested financial documentation',
              'Attend depositions and interviews as required'
            ],
            status: 'upcoming'
          },
          {
            id: 'resolution',
            title: 'Settlement & Resolution',
            description: 'Negotiation and finalization of all case issues.',
            typicalDuration: '2-6 months',
            keyActivities: [
              'Settlement negotiations and mediation',
              'Drafting of settlement agreements',
              'Final court hearings and judgments',
              'Implementation of court orders'
            ],
            whatToExpect: [
              'Mediation sessions and settlement conferences',
              'Final agreement negotiations',
              'Court approval of settlement terms',
              'Entry of final judgment and orders'
            ],
            yourRole: [
              'Participate in settlement discussions',
              'Review and approve final agreements',
              'Comply with final court orders',
              'Plan for post-judgment compliance'
            ],
            status: 'upcoming'
          }
        ];

      default:
        return [
          {
            id: 'initial',
            title: 'Case Initiation',
            description: 'Beginning of the legal process and case evaluation.',
            typicalDuration: '2-4 weeks',
            keyActivities: [
              'Case assessment and strategy development',
              'Document collection and review',
              'Legal research and analysis',
              'Initial client meetings and planning'
            ],
            whatToExpect: [
              'Detailed case evaluation',
              'Collection of relevant documents',
              'Discussion of legal strategy',
              'Explanation of process and timeline'
            ],
            yourRole: [
              'Provide complete information',
              'Gather relevant documents',
              'Ask questions about the process',
              'Follow attorney recommendations'
            ],
            status: 'completed'
          },
          {
            id: 'preparation',
            title: 'Case Preparation',
            description: 'Detailed preparation and evidence gathering.',
            typicalDuration: '2-6 months',
            keyActivities: [
              'Evidence collection and analysis',
              'Witness interviews and depositions',
              'Expert consultation and reports',
              'Motion practice and court filings'
            ],
            whatToExpect: [
              'Extensive document review',
              'Interviews and depositions',
              'Expert witness consultations',
              'Court filings and motions'
            ],
            yourRole: [
              'Cooperate with information requests',
              'Participate in depositions',
              'Maintain case confidentiality',
              'Stay engaged in case development'
            ],
            status: 'current'
          },
          {
            id: 'resolution',
            title: 'Case Resolution',
            description: 'Final resolution through settlement or trial.',
            typicalDuration: '1-12 months',
            keyActivities: [
              'Settlement negotiations',
              'Trial preparation',
              'Court proceedings',
              'Final resolution and implementation'
            ],
            whatToExpect: [
              'Settlement discussions',
              'Possible trial proceedings',
              'Court decisions and orders',
              'Implementation of resolution'
            ],
            yourRole: [
              'Participate in settlement discussions',
              'Prepare for potential trial',
              'Comply with court orders',
              'Plan for post-resolution matters'
            ],
            status: 'upcoming'
          }
        ];
    }
  };

  const phases = getTimelinePhases(caseType);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-success-600" />;
      case 'current':
        return <Circle className="h-5 w-5 text-primary-600 fill-current" />;
      case 'upcoming':
        return <Circle className="h-5 w-5 text-gray-400" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-success-50 border-success-200';
      case 'current':
        return 'bg-primary-50 border-primary-200';
      case 'upcoming':
        return 'bg-gray-50 border-gray-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <Clock className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-medium text-gray-900">Case Timeline Education</h3>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Understanding the typical progression of {caseType.toLowerCase()} cases can help you know what to expect. 
          Each case is unique, so actual timelines may vary.
        </p>
      </div>

      {/* Timeline Visualization */}
      <div className="space-y-4">
        {phases.map((phase, index) => (
          <div key={phase.id} className="relative">
            {/* Connecting Line */}
            {index < phases.length - 1 && (
              <div className="absolute left-6 top-12 w-px h-16 bg-gray-300"></div>
            )}
            
            <div
              className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-sm ${
                selectedPhase?.id === phase.id 
                  ? 'border-primary-300 bg-primary-50' 
                  : getStatusColor(phase.status)
              }`}
              onClick={() => setSelectedPhase(selectedPhase?.id === phase.id ? null : phase)}
            >
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 mt-1">
                  {getStatusIcon(phase.status)}
                </div>
                
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">{phase.title}</h4>
                      <p className="text-sm text-gray-600 mt-1">{phase.description}</p>
                    </div>
                    
                    <div className="text-right">
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                        <Calendar className="h-3 w-3 mr-1" />
                        {phase.typicalDuration}
                      </span>
                    </div>
                  </div>
                  
                  {selectedPhase?.id === phase.id && (
                    <div className="mt-4 space-y-4">
                      {/* Key Activities */}
                      <div>
                        <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                          <FileText className="h-4 w-4 mr-2" />
                          Key Activities
                        </h5>
                        <ul className="text-sm text-gray-700 space-y-1">
                          {phase.keyActivities.map((activity, idx) => (
                            <li key={idx} className="flex items-start space-x-2">
                              <span className="text-gray-500 mt-1">•</span>
                              <span>{activity}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* What to Expect */}
                      <div>
                        <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                          <Info className="h-4 w-4 mr-2" />
                          What to Expect
                        </h5>
                        <ul className="text-sm text-gray-700 space-y-1">
                          {phase.whatToExpect.map((expectation, idx) => (
                            <li key={idx} className="flex items-start space-x-2">
                              <span className="text-gray-500 mt-1">•</span>
                              <span>{expectation}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      {/* Your Role */}
                      <div>
                        <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                          <Users className="h-4 w-4 mr-2" />
                          Your Role
                        </h5>
                        <ul className="text-sm text-gray-700 space-y-1">
                          {phase.yourRole.map((role, idx) => (
                            <li key={idx} className="flex items-start space-x-2">
                              <span className="text-primary-500 mt-1">•</span>
                              <span>{role}</span>
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

      {/* Important Timeline Considerations */}
      <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-amber-800 mb-2">Important Timeline Considerations</h5>
            <ul className="text-sm text-amber-700 space-y-1">
              <li className="flex items-start space-x-2">
                <span className="text-amber-600 mt-1">•</span>
                <span>Actual timelines can vary significantly based on case complexity and court schedules</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-600 mt-1">•</span>
                <span>Settlement negotiations can occur at any stage and may shorten the timeline</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-600 mt-1">•</span>
                <span>Unexpected developments or complications may extend certain phases</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-600 mt-1">•</span>
                <span>Court backlogs and scheduling conflicts can affect timing</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-amber-600 mt-1">•</span>
                <span>Your cooperation and responsiveness can help keep the case on track</span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* Communication Tips */}
      <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-blue-900 mb-2">Staying Informed Throughout Your Case</h5>
            <ul className="text-sm text-blue-800 space-y-1">
              <li className="flex items-start space-x-2">
                <span className="text-blue-600 mt-1">•</span>
                <span>Ask your attorney for regular updates on case progress</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-blue-600 mt-1">•</span>
                <span>Don't hesitate to ask questions about any phase of the process</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-blue-600 mt-1">•</span>
                <span>Keep your contact information current with your attorney's office</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="text-blue-600 mt-1">•</span>
                <span>Respond promptly to requests for information or documentation</span>
              </li>
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
              <h5 className="text-xs font-semibold text-legal-900 mb-1">Timeline Information Disclaimer</h5>
              <p className="text-xs text-legal-700">
                This timeline information is general and educational only. Every case is unique and may not follow 
                these typical phases. Consult with your attorney for specific information about your case's expected timeline.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TimelineEducation;