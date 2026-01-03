'use client';

import React, { useState } from 'react';
import {
  Users,
  User,
  Building,
  AlertTriangle,
  Info,
  Scale,
  CheckCircle,
  XCircle,
  ExternalLink,
  MapPin,
  Brain,
  Edit,
  Plus
} from 'lucide-react';

interface PartyData {
  name: string;
  role: string;
  confidence: number;
  sourceLocation: string;
}

interface PartiesData {
  identified: PartyData[];
  confidence: number;
}

interface PartyIdentifierProps {
  parties: PartiesData;
  documentType: string;
  className?: string;
}

const PartyIdentifier: React.FC<PartyIdentifierProps> = ({
  parties,
  documentType,
  className = ''
}) => {
  const [verifiedParties, setVerifiedParties] = useState<Record<number, boolean | null>>({});
  const [editingParty, setEditingParty] = useState<number | null>(null);
  const [showRoleGuide, setShowRoleGuide] = useState(false);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-success-600 bg-success-100';
    if (confidence >= 0.6) return 'text-warning-600 bg-warning-100';
    return 'text-error-600 bg-error-100';
  };

  const getRoleColor = (role: string) => {
    const roleKey = role.toLowerCase();
    if (roleKey.includes('plaintiff') || roleKey.includes('petitioner')) {
      return 'bg-blue-100 text-blue-800 border-blue-200';
    }
    if (roleKey.includes('defendant') || roleKey.includes('respondent')) {
      return 'bg-purple-100 text-purple-800 border-purple-200';
    }
    if (roleKey.includes('attorney') || roleKey.includes('counsel')) {
      return 'bg-green-100 text-green-800 border-green-200';
    }
    if (roleKey.includes('witness')) {
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    }
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getPartyIcon = (name: string, role: string) => {
    if (name.includes('Inc.') || name.includes('LLC') || name.includes('Corp') || role.includes('Company')) {
      return <Building className="h-4 w-4" />;
    }
    return <User className="h-4 w-4" />;
  };

  const getTypicalRoles = (docType: string) => {
    switch (docType.toLowerCase()) {
      case 'contract/agreement':
        return [
          'Service Provider',
          'Service Recipient', 
          'Contractor',
          'Client',
          'Buyer',
          'Seller',
          'Lessor',
          'Lessee',
          'Licensor',
          'Licensee'
        ];
      case 'court filing':
        return [
          'Plaintiff',
          'Defendant',
          'Petitioner',
          'Respondent',
          'Intervenor',
          'Third Party',
          'Cross-Defendant',
          'Cross-Plaintiff'
        ];
      case 'legal brief':
        return [
          'Appellant',
          'Appellee',
          'Moving Party',
          'Responding Party',
          'Amicus Curiae',
          'Interested Party'
        ];
      default:
        return [
          'Party',
          'Individual',
          'Entity',
          'Organization',
          'Government Agency',
          'Representative'
        ];
    }
  };

  const handlePartyVerification = (partyIndex: number, verified: boolean | null) => {
    setVerifiedParties(prev => ({
      ...prev,
      [partyIndex]: verified
    }));
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* AI Generation Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <Brain className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-blue-900 mb-1">AI-Identified Parties</h4>
            <p className="text-sm text-blue-800">
              These parties and roles were automatically identified by AI. Professional review 
              is required to ensure accuracy and completeness of party identification.
            </p>
          </div>
        </div>
      </div>

      {/* Header with Overall Confidence */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Identified Parties</h3>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowRoleGuide(!showRoleGuide)}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            <Info className="h-4 w-4 inline mr-1" />
            Role Guide
          </button>
          <span className="text-sm text-gray-500">Overall Confidence:</span>
          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(parties.confidence)}`}>
            {(parties.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Role Guide */}
      {showRoleGuide && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">
            Typical Roles in {documentType} Documents
          </h4>
          <div className="flex flex-wrap gap-2">
            {getTypicalRoles(documentType).map((role, index) => (
              <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                {role}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Parties List */}
      {parties.identified.length === 0 ? (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <Users className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">No parties identified in this document</p>
        </div>
      ) : (
        <div className="space-y-3">
          {parties.identified.map((party, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 bg-white hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="text-gray-600 mt-1">
                    {getPartyIcon(party.name, party.role)}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h4 className="font-medium text-gray-900">{party.name}</h4>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getRoleColor(party.role)}`}>
                        {party.role}
                      </span>
                      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(party.confidence)}`}>
                        {(party.confidence * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="flex items-center space-x-2 text-xs text-gray-500 mb-2">
                      <MapPin className="h-3 w-3" />
                      <span>Found in: {party.sourceLocation}</span>
                      <button className="text-primary-600 hover:text-primary-700 inline-flex items-center">
                        <ExternalLink className="h-3 w-3 mr-1" />
                        View Source
                      </button>
                    </div>

                    {/* Party Analysis */}
                    <div className="text-xs text-gray-600 bg-gray-50 rounded p-2">
                      <strong>AI Analysis:</strong> Identified as {party.role.toLowerCase()} based on context and document structure. 
                      {party.confidence < 0.7 && (
                        <span className="text-amber-600 ml-1">Low confidence - verify role assignment.</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Verification and Edit Controls */}
                <div className="flex flex-col items-end space-y-2">
                  <div className="flex items-center space-x-1">
                    <button
                      onClick={() => setEditingParty(editingParty === index ? null : index)}
                      className="p-1 text-gray-400 hover:text-gray-600 rounded"
                      title="Edit party information"
                    >
                      <Edit className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="text-xs text-gray-500 text-right">Verification:</div>
                  {verifiedParties[index] === null || verifiedParties[index] === undefined ? (
                    <div className="flex space-x-1">
                      <button
                        onClick={() => handlePartyVerification(index, true)}
                        className="p-1 text-success-600 hover:bg-success-100 rounded"
                        title="Verify as accurate"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handlePartyVerification(index, false)}
                        className="p-1 text-error-600 hover:bg-error-100 rounded"
                        title="Mark as incorrect"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    </div>
                  ) : (
                    <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                      verifiedParties[index] 
                        ? 'bg-success-100 text-success-800' 
                        : 'bg-error-100 text-error-800'
                    }`}>
                      {verifiedParties[index] ? 'Verified' : 'Incorrect'}
                    </span>
                  )}
                </div>
              </div>

              {/* Edit Form */}
              {editingParty === index && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Party Name</label>
                      <input
                        type="text"
                        defaultValue={party.name}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Role</label>
                      <select
                        defaultValue={party.role}
                        className="w-full px-2 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                      >
                        {getTypicalRoles(documentType).map((role) => (
                          <option key={role} value={role}>{role}</option>
                        ))}
                        <option value="Other">Other (specify)</option>
                      </select>
                    </div>
                  </div>
                  <div className="flex justify-end space-x-2 mt-3">
                    <button
                      onClick={() => setEditingParty(null)}
                      className="px-3 py-1 text-xs border border-gray-300 rounded text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => {
                        console.log('Saving party edits');
                        setEditingParty(null);
                      }}
                      className="px-3 py-1 text-xs bg-primary-600 text-white rounded hover:bg-primary-700"
                    >
                      Save Changes
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Add Missing Party */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
        <button className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900">
          <Plus className="h-4 w-4 mr-2" />
          Add Missing Party
        </button>
        <p className="text-xs text-gray-500 mt-1">
          Add parties that AI may have missed during identification
        </p>
      </div>

      {/* Verification Guidelines */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-amber-800 mb-2">Party Identification Verification</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-amber-700">
              <div>
                <h5 className="font-semibold mb-1">Name Accuracy:</h5>
                <ul className="space-y-1">
                  <li>• Verify exact legal names and spellings</li>
                  <li>• Check for complete entity names (Inc., LLC, etc.)</li>
                  <li>• Identify any aliases or d/b/a names</li>
                  <li>• Confirm individual vs. entity designation</li>
                </ul>
              </div>
              <div>
                <h5 className="font-semibold mb-1">Role Verification:</h5>
                <ul className="space-y-1">
                  <li>• Confirm roles match document context</li>
                  <li>• Check for multiple roles per party</li>
                  <li>• Identify missing parties or roles</li>
                  <li>• Verify capacity (individual, representative, etc.)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Relationship Analysis */}
      {parties.identified.length > 1 && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-gray-900 mb-3">Party Relationship Analysis</h4>
          <div className="space-y-2">
            <div className="text-sm text-gray-700">
              <strong>Identified Relationships:</strong>
            </div>
            {parties.identified.length === 2 && (
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded">
                  {parties.identified[0].name} ({parties.identified[0].role})
                </span>
                <span>↔</span>
                <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded">
                  {parties.identified[1].name} ({parties.identified[1].role})
                </span>
              </div>
            )}
            <div className="text-xs text-gray-500 mt-2">
              Verify that all relevant parties are identified and relationships are correctly characterized
            </div>
          </div>
        </div>
      )}

      {/* Professional Review Notice */}
      <div className="bg-legal-50 border border-legal-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="text-sm font-semibold text-legal-900 mb-1">Professional Review Required</h4>
            <p className="text-sm text-legal-700">
              <strong>Attorney Responsibility:</strong> Party identification affects legal strategy, 
              service requirements, and case management. Independent verification of all parties, 
              their roles, and legal capacities is essential before proceeding with legal actions.
            </p>
          </div>
        </div>
      </div>

      {/* Summary Statistics */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Identification Summary</h4>
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-lg font-semibold text-gray-900">{parties.identified.length}</div>
            <div className="text-xs text-gray-600">Parties Found</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-900">
              {parties.identified.filter(p => p.name.includes('Inc.') || p.name.includes('LLC') || p.name.includes('Corp')).length}
            </div>
            <div className="text-xs text-gray-600">Entities</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-900">
              {parties.identified.length - parties.identified.filter(p => p.name.includes('Inc.') || p.name.includes('LLC') || p.name.includes('Corp')).length}
            </div>
            <div className="text-xs text-gray-600">Individuals</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-900">
              {Object.values(verifiedParties).filter(v => v === true).length}
            </div>
            <div className="text-xs text-gray-600">Verified</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PartyIdentifier;