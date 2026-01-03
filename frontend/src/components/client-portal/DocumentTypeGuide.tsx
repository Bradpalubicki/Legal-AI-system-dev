'use client';

import React, { useState } from 'react';
import {
  FileText,
  Search,
  BookOpen,
  Scale,
  Info,
  AlertTriangle,
  Clock,
  Gavel,
  Users,
  Shield,
  ExternalLink,
  HelpCircle
} from 'lucide-react';

interface DocumentType {
  id: string;
  name: string;
  description: string;
  purpose: string;
  typicalTimeline: string;
  whoFiles: string;
  whatItMeans: string;
  commonInCases: string[];
  clientActions: string[];
  importantNotes: string[];
  category: 'pleadings' | 'motions' | 'discovery' | 'court-orders' | 'evidence' | 'administrative';
}

interface DocumentTypeGuideProps {
  caseType?: string;
  className?: string;
}

const DocumentTypeGuide: React.FC<DocumentTypeGuideProps> = ({
  caseType = 'general',
  className = ''
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedDoc, setExpandedDoc] = useState<string | null>(null);

  const categories = [
    { key: 'all', label: 'All Documents', icon: FileText },
    { key: 'pleadings', label: 'Pleadings', icon: Scale },
    { key: 'motions', label: 'Motions', icon: Gavel },
    { key: 'discovery', label: 'Discovery', icon: Search },
    { key: 'court-orders', label: 'Court Orders', icon: Shield },
    { key: 'evidence', label: 'Evidence', icon: BookOpen },
    { key: 'administrative', label: 'Administrative', icon: Users }
  ];

  const documentTypes: DocumentType[] = [
    {
      id: 'complaint',
      name: 'Complaint/Petition',
      description: 'The initial document that starts a lawsuit',
      purpose: 'To formally notify the court and defendant(s) of the legal claims being made',
      typicalTimeline: 'Filed at the beginning of a case',
      whoFiles: 'The plaintiff (person bringing the lawsuit) or their attorney',
      whatItMeans: 'This document explains what happened, why the defendant is responsible, and what the plaintiff wants as a remedy',
      commonInCases: ['Personal Injury', 'Contract Disputes', 'Family Law', 'Employment Law'],
      clientActions: [
        'Review carefully for accuracy',
        'Provide any additional information requested',
        'Keep a copy for your records',
        'Understand the relief being sought'
      ],
      importantNotes: [
        'Sets the foundation for your entire case',
        'Must be served on all defendants',
        'Defendants have limited time to respond',
        'Cannot usually be changed without court permission'
      ],
      category: 'pleadings'
    },
    {
      id: 'answer',
      name: 'Answer/Response',
      description: 'The defendant\'s formal response to a complaint',
      purpose: 'To admit, deny, or claim insufficient knowledge about each allegation in the complaint',
      typicalTimeline: 'Usually due 20-30 days after being served with complaint',
      whoFiles: 'The defendant or their attorney',
      whatItMeans: 'This document tells the court the defendant\'s side of the story and any defenses they have',
      commonInCases: ['All civil litigation cases'],
      clientActions: [
        'If you receive one: Review with your attorney',
        'If you need to file one: Respond to every allegation',
        'Include any counterclaims or cross-claims',
        'Meet all deadlines strictly'
      ],
      importantNotes: [
        'Failure to file can result in default judgment',
        'Must respond to each numbered paragraph',
        'Can include affirmative defenses',
        'May include counterclaims against plaintiff'
      ],
      category: 'pleadings'
    },
    {
      id: 'motion-dismiss',
      name: 'Motion to Dismiss',
      description: 'A request to end the case without trial',
      purpose: 'To argue that the lawsuit should be thrown out for legal reasons',
      typicalTimeline: 'Often filed early in the case, sometimes before an answer',
      whoFiles: 'Usually the defendant, but any party can file',
      whatItMeans: 'The filing party believes the case has legal problems that prevent it from moving forward',
      commonInCases: ['All types of civil cases'],
      clientActions: [
        'If filed against you: Work with attorney on response',
        'Understand the legal arguments being made',
        'Gather any additional facts that support your case',
        'Be prepared for possible case dismissal'
      ],
      importantNotes: [
        'Does not address the merits of the case',
        'Focuses on legal and procedural issues',
        'If granted, case may be dismissed',
        'Some dismissals can be appealed'
      ],
      category: 'motions'
    },
    {
      id: 'discovery-request',
      name: 'Discovery Requests',
      description: 'Formal requests for information and documents',
      purpose: 'To gather evidence and information from other parties',
      typicalTimeline: 'During the discovery phase, after initial pleadings',
      whoFiles: 'Any party to the lawsuit',
      whatItMeans: 'These requests help each side learn about the other\'s evidence and build their case',
      commonInCases: ['Most civil litigation cases'],
      clientActions: [
        'If you receive them: Respond completely and truthfully',
        'Gather requested documents promptly',
        'Work with attorney on objections if appropriate',
        'Meet all deadlines strictly'
      ],
      importantNotes: [
        'Failure to respond can result in sanctions',
        'Must be complete and truthful',
        'Some information may be privileged',
        'Can include document requests, interrogatories, and depositions'
      ],
      category: 'discovery'
    },
    {
      id: 'subpoena',
      name: 'Subpoena',
      description: 'A court order requiring someone to appear or produce documents',
      purpose: 'To compel testimony or document production from parties or witnesses',
      typicalTimeline: 'Can be issued during discovery or before trial',
      whoFiles: 'Attorneys or parties, issued by the court',
      whatItMeans: 'This is a legal command that must be followed - ignoring it can result in contempt of court',
      commonInCases: ['Cases requiring witness testimony or third-party documents'],
      clientActions: [
        'If you receive one: Comply or seek legal advice immediately',
        'If your case involves one: Understand what information is being sought',
        'Prepare for deposition or document production',
        'Consider whether to object to overly broad requests'
      ],
      importantNotes: [
        'Has the force of a court order',
        'Failure to comply can result in contempt',
        'Can be challenged if improper',
        'May require witness fees and mileage'
      ],
      category: 'discovery'
    },
    {
      id: 'summary-judgment',
      name: 'Motion for Summary Judgment',
      description: 'A request to decide the case without a trial',
      purpose: 'To argue that there are no disputed facts and the law favors one side',
      typicalTimeline: 'After discovery is substantially complete',
      whoFiles: 'Any party, but often the defendant',
      whatItMeans: 'The filing party believes the evidence is so clear that a trial is unnecessary',
      commonInCases: ['Civil cases with clear-cut legal or factual issues'],
      clientActions: [
        'If filed against you: Work closely with attorney on response',
        'Gather evidence that shows disputed facts',
        'Understand the legal standard being applied',
        'Be prepared for possible case resolution'
      ],
      importantNotes: [
        'Can end the case without trial',
        'Requires no genuine dispute of material fact',
        'Court views evidence in light most favorable to non-moving party',
        'If denied, case usually proceeds to trial'
      ],
      category: 'motions'
    },
    {
      id: 'court-order',
      name: 'Court Order',
      description: 'A judge\'s official decision or command',
      purpose: 'To direct parties to do or not do specific things',
      typicalTimeline: 'Can be issued at any time during the case',
      whoFiles: 'Issued by the court/judge',
      whatItMeans: 'This is a binding legal command that must be followed',
      commonInCases: ['All types of cases'],
      clientActions: [
        'Read carefully and understand all requirements',
        'Comply with all deadlines and requirements',
        'Ask attorney to explain anything unclear',
        'Keep copies of all orders'
      ],
      importantNotes: [
        'Violation can result in contempt of court',
        'May include deadlines for compliance',
        'Can be appealed in some circumstances',
        'Some orders are temporary, others are permanent'
      ],
      category: 'court-orders'
    },
    {
      id: 'settlement-agreement',
      name: 'Settlement Agreement',
      description: 'A contract resolving the dispute without trial',
      purpose: 'To formally document the terms of a negotiated resolution',
      typicalTimeline: 'Can occur at any stage of the case',
      whoFiles: 'Prepared by attorneys, signed by parties',
      whatItMeans: 'This ends the lawsuit and creates binding obligations for all parties',
      commonInCases: ['Any case that resolves without trial'],
      clientActions: [
        'Review all terms carefully before signing',
        'Understand all obligations and deadlines',
        'Keep executed copies of all documents',
        'Comply with all settlement terms'
      ],
      importantNotes: [
        'Becomes binding contract once signed',
        'Usually ends the litigation',
        'Breach can result in new lawsuit',
        'May include confidentiality provisions'
      ],
      category: 'administrative'
    }
  ];

  const filteredDocs = documentTypes.filter(doc => {
    const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory;
    const matchesSearch = searchTerm === '' || 
      doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'pleadings':
        return 'bg-blue-100 text-blue-800';
      case 'motions':
        return 'bg-purple-100 text-purple-800';
      case 'discovery':
        return 'bg-green-100 text-green-800';
      case 'court-orders':
        return 'bg-red-100 text-red-800';
      case 'evidence':
        return 'bg-yellow-100 text-yellow-800';
      case 'administrative':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <FileText className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-medium text-gray-900">Legal Document Guide</h3>
        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          <Info className="h-3 w-3 mr-1" />
          Information Only
        </span>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Understanding legal documents can help you better participate in your case. This guide explains 
          common document types in plain English. Always consult with your attorney for case-specific advice.
        </p>
      </div>

      {/* Search and Filter */}
      <div className="mb-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search document types..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-3 py-2 w-full border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category.key}
              onClick={() => setSelectedCategory(category.key)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === category.key
                  ? 'bg-primary-100 text-primary-800 border border-primary-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <category.icon className="h-4 w-4" />
              <span>{category.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Document List */}
      <div className="space-y-4">
        {filteredDocs.map((doc) => (
          <div key={doc.id} className="border border-gray-200 rounded-lg">
            <div
              className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => setExpandedDoc(expandedDoc === doc.id ? null : doc.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="mt-1">
                    <FileText className="h-5 w-5 text-gray-400" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-medium text-gray-900">{doc.name}</h4>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(doc.category)}`}>
                        {doc.category.replace('-', ' ').toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{doc.description}</p>
                    <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                      <span>Timeline: {doc.typicalTimeline}</span>
                      <span>Filed by: {doc.whoFiles}</span>
                    </div>
                  </div>
                </div>
                <div className="text-gray-400">
                  {expandedDoc === doc.id ? '−' : '+'}
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedDoc === doc.id && (
              <div className="border-t border-gray-200 p-4 bg-gray-50">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* What It Means */}
                  <div>
                    <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                      <HelpCircle className="h-4 w-4 mr-2" />
                      What This Document Means
                    </h5>
                    <p className="text-sm text-gray-700 mb-3">{doc.whatItMeans}</p>
                    
                    <h6 className="text-sm font-semibold text-gray-900 mb-2">Purpose</h6>
                    <p className="text-sm text-gray-700">{doc.purpose}</p>
                  </div>

                  {/* Client Actions */}
                  <div>
                    <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                      <Users className="h-4 w-4 mr-2" />
                      What You Should Do
                    </h5>
                    <ul className="text-sm text-gray-700 space-y-1">
                      {doc.clientActions.map((action, idx) => (
                        <li key={idx} className="flex items-start space-x-2">
                          <span className="text-primary-500 mt-1">•</span>
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Common In Cases */}
                  <div>
                    <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                      <Scale className="h-4 w-4 mr-2" />
                      Common In These Case Types
                    </h5>
                    <div className="flex flex-wrap gap-1">
                      {doc.commonInCases.map((caseType, idx) => (
                        <span key={idx} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                          {caseType}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Important Notes */}
                  <div>
                    <h5 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      Important Notes
                    </h5>
                    <ul className="text-sm text-gray-700 space-y-1">
                      {doc.importantNotes.map((note, idx) => (
                        <li key={idx} className="flex items-start space-x-2">
                          <span className="text-amber-500 mt-1">•</span>
                          <span>{note}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredDocs.length === 0 && (
        <div className="text-center py-8">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No documents found matching your search criteria.</p>
        </div>
      )}

      {/* Legal Process Tips */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <BookOpen className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-blue-900 mb-2">Tips for Understanding Legal Documents</h5>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Read all documents carefully and ask questions about anything unclear</li>
              <li>• Pay attention to deadlines and respond promptly</li>
              <li>• Keep organized records of all documents received and filed</li>
              <li>• Understand the difference between filing and serving documents</li>
              <li>• Know that court rules and procedures vary by jurisdiction</li>
              <li>• Always consult with your attorney before taking any action</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Deadline Warning */}
      <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Clock className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-amber-800 mb-1">Critical Deadline Warning</h5>
            <p className="text-sm text-amber-700">
              Many legal documents have strict deadlines for response. Missing these deadlines can seriously 
              harm your case or result in default judgments against you. Always respond promptly and consult 
              with your attorney about any documents you receive.
            </p>
          </div>
        </div>
      </div>

      {/* Educational Disclaimer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-xs font-semibold text-legal-900 mb-1">Document Guide Disclaimer</h5>
              <p className="text-xs text-legal-700">
                This guide provides general educational information only. Legal documents and procedures vary 
                significantly by jurisdiction, case type, and specific circumstances. This information does not 
                constitute legal advice. Always consult with a qualified attorney for guidance on your specific case.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentTypeGuide;