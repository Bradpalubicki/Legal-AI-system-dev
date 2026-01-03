'use client';

import React, { useState, useRef } from 'react';
import { 
  FileText,
  Search,
  ZoomIn,
  ZoomOut,
  Download,
  Share,
  Shield,
  AlertTriangle,
  Info,
  Scale,
  BookOpen,
  ExternalLink,
  Eye,
  Lock,
  Highlight
} from 'lucide-react';
import InfoTooltip from './InfoTooltip';

interface Citation {
  id: string;
  text: string;
  type: 'case_law' | 'statute' | 'regulation' | 'rule';
  startIndex: number;
  endIndex: number;
  verified: boolean;
  current: boolean;
  citation: string;
  relevance: 'high' | 'medium' | 'low';
}

interface DocumentViewerProps {
  documentId: string;
  documentName: string;
  privilegeLevel: 'public' | 'confidential' | 'attorney_client' | 'work_product';
  content: string;
  citations?: Citation[];
  showComplianceFeatures?: boolean;
  className?: string;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({
  documentId,
  documentName,
  privilegeLevel,
  content,
  citations = [],
  showComplianceFeatures = true,
  className = ''
}) => {
  const [zoomLevel, setZoomLevel] = useState(100);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCitations, setShowCitations] = useState(true);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [showPrivilegeWarning, setShowPrivilegeWarning] = useState(true);
  const contentRef = useRef<HTMLDivElement>(null);

  const getPrivilegeBadge = (level: string) => {
    switch (level) {
      case 'attorney_client':
        return {
          icon: <Shield className="h-3 w-3" />,
          text: 'Attorney-Client Privileged',
          color: 'bg-error-100 text-error-800 border-error-200',
          description: 'This document contains attorney-client privileged communications. Unauthorized disclosure may waive privilege.'
        };
      case 'work_product':
        return {
          icon: <Shield className="h-3 w-3" />,
          text: 'Work Product',
          color: 'bg-warning-100 text-warning-800 border-warning-200',
          description: 'This document contains attorney work product. Protection may be waived by disclosure to opposing parties.'
        };
      case 'confidential':
        return {
          icon: <Eye className="h-3 w-3" />,
          text: 'Confidential',
          color: 'bg-blue-100 text-blue-800 border-blue-200',
          description: 'This document contains confidential information. Handle according to confidentiality agreements.'
        };
      case 'public':
        return {
          icon: <Info className="h-3 w-3" />,
          text: 'Public Information',
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          description: 'This document contains public information with no confidentiality restrictions.'
        };
      default:
        return {
          icon: <Info className="h-3 w-3" />,
          text: 'Unspecified',
          color: 'bg-gray-100 text-gray-800 border-gray-200',
          description: 'Document privilege level not specified. Exercise caution when handling.'
        };
    }
  };

  const getCitationColor = (citation: Citation) => {
    if (!citation.verified) return 'bg-gray-200 text-gray-800';
    if (!citation.current) return 'bg-red-200 text-red-800';
    
    switch (citation.relevance) {
      case 'high':
        return 'bg-green-200 text-green-800';
      case 'medium':
        return 'bg-yellow-200 text-yellow-800';
      case 'low':
        return 'bg-blue-200 text-blue-800';
      default:
        return 'bg-gray-200 text-gray-800';
    }
  };

  const highlightCitations = (text: string) => {
    if (!showCitations || citations.length === 0) {
      return <span>{text}</span>;
    }

    const sortedCitations = [...citations].sort((a, b) => a.startIndex - b.startIndex);
    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    sortedCitations.forEach((citation, index) => {
      if (citation.startIndex > lastIndex) {
        elements.push(text.slice(lastIndex, citation.startIndex));
      }

      elements.push(
        <span
          key={`citation-${citation.id}`}
          className={`cursor-pointer rounded px-1 transition-colors hover:opacity-80 ${getCitationColor(citation)}`}
          onClick={() => setSelectedCitation(citation)}
          title={citation.citation}
        >
          {text.slice(citation.startIndex, citation.endIndex)}
        </span>
      );

      lastIndex = citation.endIndex;
    });

    if (lastIndex < text.length) {
      elements.push(text.slice(lastIndex));
    }

    return <>{elements}</>;
  };

  const highlightSearchTerm = (text: string) => {
    if (!searchTerm) return text;

    const regex = new RegExp(`(${searchTerm})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) => 
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-300 rounded px-1">
          {part}
        </mark>
      ) : part
    );
  };

  const privilegeBadge = getPrivilegeBadge(privilegeLevel);
  const isProtectedDocument = privilegeLevel === 'attorney_client' || privilegeLevel === 'work_product';

  return (
    <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
      {/* Header with Controls */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <FileText className="h-5 w-5 text-gray-400" />
          <div>
            <h3 className="font-medium text-gray-900">{documentName}</h3>
            <div className="flex items-center space-x-2 mt-1">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${privilegeBadge.color}`}>
                {privilegeBadge.icon}
                <span className="ml-1">{privilegeBadge.text}</span>
              </span>
              
              {showComplianceFeatures && (
                <InfoTooltip
                  content={privilegeBadge.description}
                  type="legal"
                  title="Privilege Information"
                />
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search document..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Zoom Controls */}
          <div className="flex items-center space-x-1">
            <button
              onClick={() => setZoomLevel(Math.max(50, zoomLevel - 25))}
              className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
              disabled={zoomLevel <= 50}
            >
              <ZoomOut className="h-4 w-4" />
            </button>
            <span className="text-sm text-gray-500 min-w-[3rem] text-center">
              {zoomLevel}%
            </span>
            <button
              onClick={() => setZoomLevel(Math.min(200, zoomLevel + 25))}
              className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors"
              disabled={zoomLevel >= 200}
            >
              <ZoomIn className="h-4 w-4" />
            </button>
          </div>

          {/* Citation Toggle */}
          <button
            onClick={() => setShowCitations(!showCitations)}
            className={`inline-flex items-center px-2 py-1.5 rounded text-xs font-medium transition-colors ${
              showCitations 
                ? 'bg-primary-100 text-primary-800' 
                : 'bg-gray-100 text-gray-600'
            }`}
          >
            <Highlight className="h-3 w-3 mr-1" />
            Citations
          </button>

          {/* Actions */}
          <div className="flex items-center space-x-1">
            <button className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors">
              <Download className="h-4 w-4" />
            </button>
            <button className="p-1.5 text-gray-400 hover:text-gray-600 transition-colors">
              <Share className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Privilege Warning */}
      {showComplianceFeatures && isProtectedDocument && showPrivilegeWarning && (
        <div className="p-4 bg-error-50 border-b border-error-200">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-error-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-error-900 mb-1">
                Privileged Document Warning
              </h4>
              <p className="text-sm text-error-700 mb-2">
                This document contains privileged information. Unauthorized disclosure may waive attorney-client privilege or work product protection.
              </p>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setShowPrivilegeWarning(false)}
                  className="text-xs text-error-600 hover:text-error-700 font-medium"
                >
                  I understand - Continue viewing
                </button>
                <InfoTooltip
                  content="Privileged documents require special handling. Access should be limited to authorized personnel and sharing should follow firm policies to maintain privilege protection."
                  type="legal"
                  title="Privilege Protection Guidelines"
                />
              </div>
            </div>
            <button
              onClick={() => setShowPrivilegeWarning(false)}
              className="text-error-400 hover:text-error-600"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex">
        {/* Document Content */}
        <div className="flex-1 p-6 overflow-auto">
          <div
            ref={contentRef}
            className="prose prose-sm max-w-none"
            style={{ 
              fontSize: `${zoomLevel}%`,
              lineHeight: '1.6'
            }}
          >
            <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
              {highlightSearchTerm(content) && highlightCitations(content)}
            </div>
          </div>
        </div>

        {/* Citation Sidebar */}
        {showCitations && citations.length > 0 && (
          <div className="w-80 border-l border-gray-200 p-4 bg-gray-50">
            <div className="flex items-center space-x-2 mb-4">
              <BookOpen className="h-4 w-4 text-gray-600" />
              <h4 className="font-medium text-gray-900">Citations Found</h4>
              <InfoTooltip
                content="Citations are automatically identified but require verification through authoritative legal databases for accuracy and current validity."
                type="warning"
                title="Citation Verification Required"
              />
            </div>

            <div className="space-y-3">
              {citations.map((citation) => (
                <div
                  key={citation.id}
                  className={`border rounded-lg p-3 cursor-pointer transition-all ${
                    selectedCitation?.id === citation.id 
                      ? 'border-primary-300 bg-primary-50' 
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                  onClick={() => setSelectedCitation(citation)}
                >
                  <div className="flex items-start space-x-2">
                    <div className="flex-1">
                      <h5 className="text-sm font-medium text-gray-900 mb-1">
                        {citation.citation}
                      </h5>
                      <div className="flex items-center space-x-2 mb-2">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getCitationColor(citation)}`}>
                          {citation.relevance.toUpperCase()}
                        </span>
                        <span className="text-xs text-gray-500 capitalize">
                          {citation.type.replace('_', ' ')}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-3 text-xs">
                        {citation.verified ? (
                          <span className="text-success-600 flex items-center">
                            <Info className="h-3 w-3 mr-1" />
                            Verified
                          </span>
                        ) : (
                          <span className="text-warning-600 flex items-center">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            Unverified
                          </span>
                        )}
                        
                        {!citation.current && (
                          <span className="text-error-600 flex items-center">
                            <AlertTriangle className="h-3 w-3 mr-1" />
                            May be outdated
                          </span>
                        )}
                      </div>
                    </div>
                    
                    <button className="p-1 text-gray-400 hover:text-gray-600">
                      <ExternalLink className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {/* Citation Verification Notice */}
            {showComplianceFeatures && (
              <div className="mt-4 bg-legal-50 border border-legal-200 rounded-lg p-3">
                <div className="flex items-start space-x-2">
                  <Scale className="h-3 w-3 text-legal-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h5 className="text-xs font-semibold text-legal-900 mb-1">
                      Professional Responsibility
                    </h5>
                    <p className="text-xs text-legal-700">
                      All citations must be independently verified through authoritative legal databases. 
                      Check for subsequent history, current validity, and jurisdiction-specific applicability.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selected Citation Details */}
      {selectedCitation && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          <div className="flex items-start justify-between mb-2">
            <h4 className="font-medium text-gray-900">Citation Details</h4>
            <button
              onClick={() => setSelectedCitation(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          
          <div className="text-sm text-gray-700 mb-3">
            <strong>Full Citation:</strong> {selectedCitation.citation}
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-gray-500">Type:</span>
              <div className="font-medium capitalize">
                {selectedCitation.type.replace('_', ' ')}
              </div>
            </div>
            <div>
              <span className="text-gray-500">Relevance:</span>
              <div className="font-medium capitalize">
                {selectedCitation.relevance}
              </div>
            </div>
            <div>
              <span className="text-gray-500">Verified:</span>
              <div className="font-medium">
                {selectedCitation.verified ? 'Yes' : 'No'}
              </div>
            </div>
            <div>
              <span className="text-gray-500">Current:</span>
              <div className="font-medium">
                {selectedCitation.current ? 'Yes' : 'May be outdated'}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between mt-3">
            <div className="flex items-center space-x-2">
              <button className="inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                <Search className="h-3 w-3 mr-1" />
                Verify Citation
              </button>
              <button className="inline-flex items-center px-2 py-1 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50">
                <BookOpen className="h-3 w-3 mr-1" />
                View Source
              </button>
            </div>

            <InfoTooltip
              content="Use legal databases like Westlaw, Lexis, or Bloomberg Law to verify citation accuracy, check for subsequent history, and confirm current validity."
              type="educational"
              title="Citation Verification Best Practices"
            />
          </div>
        </div>
      )}

      {/* Educational Footer */}
      {showComplianceFeatures && (
        <div className="border-t border-gray-200 p-4 bg-blue-50">
          <div className="flex items-start space-x-2">
            <BookOpen className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-sm font-semibold text-blue-900 mb-1">
                Document Review Best Practices
              </h5>
              <p className="text-sm text-blue-800 mb-2">
                When reviewing legal documents, attorneys commonly:
              </p>
              <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
                <li>Verify all legal citations through primary sources</li>
                <li>Check privilege levels and handling requirements</li>
                <li>Note potential conflicts of interest or ethical issues</li>
                <li>Maintain confidentiality and privilege protections</li>
                <li>Document review findings and recommendations</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentViewer;