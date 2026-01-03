/**
 * Party Management Component
 * Manages all parties in a case with contact details, roles, claims, and communication
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Party, PartyRole, CreatePartyRequest } from '@/types/case-management';
import { caseManagementAPI } from '@/lib/api/case-management-api';

interface PartyManagementProps {
  caseId: string;
}

export default function PartyManagement({ caseId }: PartyManagementProps) {
  const [parties, setParties] = useState<Party[]>([]);
  const [filteredParties, setFilteredParties] = useState<Party[]>([]);
  const [selectedParty, setSelectedParty] = useState<Party | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterRole, setFilterRole] = useState<PartyRole | 'all'>('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [newParty, setNewParty] = useState<Partial<CreatePartyRequest>>({
    case_id: caseId,
    name: '',
    role: PartyRole.OTHER,
    email: '',
    phone: '',
    address: '',
  });

  useEffect(() => {
    loadParties();
  }, [caseId]);

  useEffect(() => {
    if (filterRole === 'all') {
      setFilteredParties(parties);
    } else {
      setFilteredParties(parties.filter((p) => p.role === filterRole));
    }
  }, [filterRole, parties]);

  const loadParties = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await caseManagementAPI.parties.list(caseId);
      setParties(data);
      setFilteredParties(data);
      setLoading(false);
    } catch (err) {
      console.error('Error loading parties:', err);
      setError(err instanceof Error ? err.message : 'Failed to load parties');
      setLoading(false);
    }
  };

  const handleAddParty = async () => {
    try {
      if (!newParty.name || !newParty.role) {
        alert('Please provide at least name and role');
        return;
      }

      await caseManagementAPI.parties.create(caseId, newParty as CreatePartyRequest);
      await loadParties();
      setShowAddModal(false);
      setNewParty({
        case_id: caseId,
        name: '',
        role: PartyRole.OTHER,
        email: '',
        phone: '',
        address: '',
      });
    } catch (err) {
      console.error('Error adding party:', err);
      alert('Failed to add party: ' + (err instanceof Error ? err.message : 'Unknown error'));
    }
  };

  const getRoleIcon = (role: PartyRole): string => {
    const icons: Record<PartyRole, string> = {
      [PartyRole.PLAINTIFF]: '👤',
      [PartyRole.DEFENDANT]: '🛡️',
      [PartyRole.DEBTOR]: '💳',
      [PartyRole.CREDITOR]: '💰',
      [PartyRole.TRUSTEE]: '⚖️',
      [PartyRole.ATTORNEY]: '👔',
      [PartyRole.JUDGE]: '⚖️',
      [PartyRole.WITNESS]: '👁️',
      [PartyRole.EXPERT]: '🎓',
      [PartyRole.MEDIATOR]: '🤝',
      [PartyRole.BIDDER]: '🔨',
      [PartyRole.OTHER]: '👥',
    };
    return icons[role] || '👥';
  };

  const getRoleColor = (role: PartyRole): string => {
    const colors: Record<PartyRole, string> = {
      [PartyRole.PLAINTIFF]: 'bg-blue-100 text-blue-800',
      [PartyRole.DEFENDANT]: 'bg-red-100 text-red-800',
      [PartyRole.DEBTOR]: 'bg-orange-100 text-orange-800',
      [PartyRole.CREDITOR]: 'bg-green-100 text-green-800',
      [PartyRole.TRUSTEE]: 'bg-purple-100 text-purple-800',
      [PartyRole.ATTORNEY]: 'bg-indigo-100 text-indigo-800',
      [PartyRole.JUDGE]: 'bg-gray-100 text-gray-800',
      [PartyRole.WITNESS]: 'bg-yellow-100 text-yellow-800',
      [PartyRole.EXPERT]: 'bg-cyan-100 text-cyan-800',
      [PartyRole.MEDIATOR]: 'bg-teal-100 text-teal-800',
      [PartyRole.BIDDER]: 'bg-pink-100 text-pink-800',
      [PartyRole.OTHER]: 'bg-gray-100 text-gray-800',
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={loadParties}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Party Management</h1>
            <p className="text-gray-600 mt-1">
              {filteredParties.length} {filterRole === 'all' ? 'total' : filterRole} parties
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            {/* Role Filter */}
            <select
              value={filterRole}
              onChange={(e) => setFilterRole(e.target.value as PartyRole | 'all')}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Roles</option>
              <option value={PartyRole.PLAINTIFF}>Plaintiff</option>
              <option value={PartyRole.DEFENDANT}>Defendant</option>
              <option value={PartyRole.DEBTOR}>Debtor</option>
              <option value={PartyRole.CREDITOR}>Creditor</option>
              <option value={PartyRole.TRUSTEE}>Trustee</option>
              <option value={PartyRole.ATTORNEY}>Attorney</option>
              <option value={PartyRole.BIDDER}>Bidder</option>
            </select>

            {/* Add Party Button */}
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              + Add Party
            </button>
          </div>
        </div>
      </Card>

      {/* Party Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredParties.map((party) => (
          <Card
            key={party.id}
            onClick={() => setSelectedParty(party)}
            className="p-6 cursor-pointer hover:shadow-lg transition-shadow"
          >
            {/* Party Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{getRoleIcon(party.role)}</span>
                <div>
                  <h3 className="font-bold text-gray-900">{party.name}</h3>
                  {party.legal_name && party.legal_name !== party.name && (
                    <p className="text-xs text-gray-500">{party.legal_name}</p>
                  )}
                </div>
              </div>
              <span className={`px-2 py-1 rounded text-xs font-medium ${getRoleColor(party.role)}`}>
                {party.role.replace('_', ' ').toUpperCase()}
              </span>
            </div>

            {/* Contact Info */}
            <div className="space-y-2 text-sm">
              {party.email && (
                <div className="flex items-center text-gray-600">
                  <span className="mr-2">✉️</span>
                  <span className="truncate">{party.email}</span>
                </div>
              )}
              {party.phone && (
                <div className="flex items-center text-gray-600">
                  <span className="mr-2">📞</span>
                  <span>{party.phone}</span>
                </div>
              )}
              {party.address && (
                <div className="flex items-center text-gray-600">
                  <span className="mr-2">📍</span>
                  <span className="truncate">{party.address.split('\n')[0]}</span>
                </div>
              )}
            </div>

            {/* Authorization & Claims */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between text-xs">
                <div className="space-y-1">
                  {party.can_file_documents && (
                    <span className="flex items-center text-green-600">
                      ✓ Can file documents
                    </span>
                  )}
                  {party.can_bid && (
                    <span className="flex items-center text-green-600">✓ Qualified bidder</span>
                  )}
                  {party.interest_amount && (
                    <span className="flex items-center text-blue-600">
                      💰 ${party.interest_amount.toLocaleString()}
                    </span>
                  )}
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedParty(party);
                  }}
                  className="text-blue-600 hover:text-blue-700 font-medium"
                >
                  Details →
                </button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {filteredParties.length === 0 && (
        <Card className="p-12 text-center">
          <p className="text-gray-500 text-lg">No parties found</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add First Party
          </button>
        </Card>
      )}

      {/* Party Detail Modal */}
      {selectedParty && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedParty(null)}
        >
          <Card
            className="max-w-3xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-6">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    <span className="text-3xl">{getRoleIcon(selectedParty.role)}</span>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">{selectedParty.name}</h2>
                      {selectedParty.legal_name && selectedParty.legal_name !== selectedParty.name && (
                        <p className="text-gray-600">{selectedParty.legal_name}</p>
                      )}
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded text-sm font-medium ${getRoleColor(selectedParty.role)}`}>
                    {selectedParty.role.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedParty(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Contact Information */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Contact Information</h3>
                  <div className="space-y-3 text-sm">
                    {selectedParty.email && (
                      <div>
                        <p className="text-gray-600 font-medium">Email</p>
                        <p className="text-gray-900">{selectedParty.email}</p>
                      </div>
                    )}
                    {selectedParty.phone && (
                      <div>
                        <p className="text-gray-600 font-medium">Phone</p>
                        <p className="text-gray-900">{selectedParty.phone}</p>
                      </div>
                    )}
                    {selectedParty.address && (
                      <div>
                        <p className="text-gray-600 font-medium">Address</p>
                        <p className="text-gray-900 whitespace-pre-line">{selectedParty.address}</p>
                      </div>
                    )}
                    {selectedParty.preferred_contact_method && (
                      <div>
                        <p className="text-gray-600 font-medium">Preferred Contact</p>
                        <p className="text-gray-900 capitalize">
                          {selectedParty.preferred_contact_method.replace('_', ' ')}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Legal Representation */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Representation</h3>
                  <div className="space-y-3 text-sm">
                    {selectedParty.attorney_firm && (
                      <div>
                        <p className="text-gray-600 font-medium">Law Firm</p>
                        <p className="text-gray-900">{selectedParty.attorney_firm}</p>
                      </div>
                    )}
                    {selectedParty.bar_number && (
                      <div>
                        <p className="text-gray-600 font-medium">Bar Number</p>
                        <p className="text-gray-900">{selectedParty.bar_number}</p>
                      </div>
                    )}
                    {selectedParty.represented_by && (
                      <div>
                        <p className="text-gray-600 font-medium">Represented By</p>
                        <p className="text-gray-900">{selectedParty.represented_by}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Claims and Interests */}
                {(selectedParty.interest_amount || selectedParty.interest_description || selectedParty.claims_held) && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Claims & Interests</h3>
                    <div className="space-y-3 text-sm">
                      {selectedParty.interest_amount && (
                        <div>
                          <p className="text-gray-600 font-medium">Interest Amount</p>
                          <p className="text-gray-900 text-lg font-bold">
                            ${selectedParty.interest_amount.toLocaleString()}
                          </p>
                        </div>
                      )}
                      {selectedParty.priority_level !== undefined && (
                        <div>
                          <p className="text-gray-600 font-medium">Priority Level</p>
                          <p className="text-gray-900">Level {selectedParty.priority_level}</p>
                        </div>
                      )}
                      {selectedParty.interest_description && (
                        <div>
                          <p className="text-gray-600 font-medium">Description</p>
                          <p className="text-gray-900">{selectedParty.interest_description}</p>
                        </div>
                      )}
                      {selectedParty.claims_held && selectedParty.claims_held.length > 0 && (
                        <div>
                          <p className="text-gray-600 font-medium">Claims</p>
                          <ul className="list-disc list-inside text-gray-900">
                            {selectedParty.claims_held.map((claim, idx) => (
                              <li key={idx}>{typeof claim === 'string' ? claim : JSON.stringify(claim)}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Authorization & Access Rights */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Document Access Rights</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
                      <span className="text-gray-700">Authorization Level</span>
                      <span className="font-medium text-gray-900 capitalize">
                        {selectedParty.authorization_level || 'Not Set'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
                      <span className="text-gray-700">Can Receive Notices</span>
                      <span className={selectedParty.can_receive_notices ? 'text-green-600' : 'text-red-600'}>
                        {selectedParty.can_receive_notices ? '✓ Yes' : '✗ No'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
                      <span className="text-gray-700">Can File Documents</span>
                      <span className={selectedParty.can_file_documents ? 'text-green-600' : 'text-red-600'}>
                        {selectedParty.can_file_documents ? '✓ Yes' : '✗ No'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between py-2 px-3 bg-gray-50 rounded">
                      <span className="text-gray-700">Can Bid on Assets</span>
                      <span className={selectedParty.can_bid ? 'text-green-600' : 'text-red-600'}>
                        {selectedParty.can_bid ? '✓ Yes' : '✗ No'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Notes */}
              {(selectedParty.notes || selectedParty.communication_notes) && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Communication Log & Notes</h3>
                  {selectedParty.communication_notes && (
                    <div className="mb-3">
                      <p className="text-sm text-gray-600 font-medium">Communication Notes</p>
                      <p className="text-sm text-gray-900 mt-1">{selectedParty.communication_notes}</p>
                    </div>
                  )}
                  {selectedParty.notes && (
                    <div>
                      <p className="text-sm text-gray-600 font-medium">General Notes</p>
                      <p className="text-sm text-gray-900 mt-1">{selectedParty.notes}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Close Button */}
              <button
                onClick={() => setSelectedParty(null)}
                className="mt-6 w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Close
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* Add Party Modal */}
      {showAddModal && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowAddModal(false)}
        >
          <Card
            className="max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Add New Party</h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name <span className="text-red-600">*</span>
                  </label>
                  <input
                    type="text"
                    value={newParty.name}
                    onChange={(e) => setNewParty({ ...newParty, name: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Role <span className="text-red-600">*</span>
                  </label>
                  <select
                    value={newParty.role}
                    onChange={(e) => setNewParty({ ...newParty, role: e.target.value as PartyRole })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value={PartyRole.PLAINTIFF}>Plaintiff</option>
                    <option value={PartyRole.DEFENDANT}>Defendant</option>
                    <option value={PartyRole.DEBTOR}>Debtor</option>
                    <option value={PartyRole.CREDITOR}>Creditor</option>
                    <option value={PartyRole.TRUSTEE}>Trustee</option>
                    <option value={PartyRole.ATTORNEY}>Attorney</option>
                    <option value={PartyRole.WITNESS}>Witness</option>
                    <option value={PartyRole.EXPERT}>Expert</option>
                    <option value={PartyRole.BIDDER}>Bidder</option>
                    <option value={PartyRole.OTHER}>Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                  <input
                    type="email"
                    value={newParty.email}
                    onChange={(e) => setNewParty({ ...newParty, email: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="email@example.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                  <input
                    type="tel"
                    value={newParty.phone}
                    onChange={(e) => setNewParty({ ...newParty, phone: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="(555) 123-4567"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Address</label>
                  <textarea
                    value={newParty.address}
                    onChange={(e) => setNewParty({ ...newParty, address: e.target.value })}
                    className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    rows={3}
                    placeholder="Street address, city, state, zip"
                  />
                </div>
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddParty}
                  className="flex-1 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                >
                  Add Party
                </button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
