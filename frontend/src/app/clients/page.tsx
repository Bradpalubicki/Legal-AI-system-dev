'use client'

/**
 * Client Management Page
 *
 * Main page for managing law firm clients, cases, and document sharing.
 */

import { useState } from 'react'
import Layout from '@/components/layout/Layout'
import ClientList from '@/components/clients/ClientList'
import CreateClientForm from '@/components/clients/CreateClientForm'
import type { Client } from '@/types/client'

type ViewMode = 'list' | 'create' | 'details'

export default function ClientsPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [selectedClient, setSelectedClient] = useState<Client | null>(null)

  const handleClientSelect = (client: Client) => {
    setSelectedClient(client)
    setViewMode('details')
  }

  const handleClientCreated = (client: Client) => {
    setSelectedClient(client)
    setViewMode('details')
  }

  return (
    <Layout title="Client Management">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Client Management</h1>
              <p className="mt-1 text-sm text-gray-600">
                Manage client relationships, cases, and document sharing
              </p>
            </div>

            <div className="flex gap-3">
              {viewMode !== 'list' && (
                <button
                  onClick={() => setViewMode('list')}
                  className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Back to List
                </button>
              )}
              {viewMode !== 'create' && (
                <button
                  onClick={() => setViewMode('create')}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors inline-flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  New Client
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Content */}
        {viewMode === 'list' && (
          <ClientList onClientSelect={handleClientSelect} />
        )}

        {viewMode === 'create' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Create New Client</h2>
            <CreateClientForm
              onSuccess={handleClientCreated}
              onCancel={() => setViewMode('list')}
            />
          </div>
        )}

        {viewMode === 'details' && selectedClient && (
          <div className="space-y-6">
            {/* Client Header */}
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    {selectedClient.display_name}
                  </h2>
                  <p className="text-sm text-gray-700 mt-1">
                    Client #{selectedClient.client_number}
                  </p>
                  <div className="flex flex-wrap gap-3 mt-4">
                    <span className="px-3 py-1 bg-white rounded-full text-sm capitalize">
                      {selectedClient.client_type}
                    </span>
                    <span className={`px-3 py-1 rounded-full text-sm capitalize ${
                      selectedClient.status === 'active'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {selectedClient.status}
                    </span>
                    {selectedClient.portal_access_enabled && (
                      <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm">
                        Portal Access
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Client Details Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Contact Information */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
                <div className="space-y-3 text-sm">
                  {selectedClient.email && (
                    <div>
                      <span className="font-medium text-gray-700">Email:</span>
                      <p className="text-gray-900">{selectedClient.email}</p>
                    </div>
                  )}
                  {selectedClient.phone_primary && (
                    <div>
                      <span className="font-medium text-gray-700">Phone:</span>
                      <p className="text-gray-900">{selectedClient.phone_primary}</p>
                    </div>
                  )}
                  {selectedClient.address_line1 && (
                    <div>
                      <span className="font-medium text-gray-700">Address:</span>
                      <p className="text-gray-900">
                        {selectedClient.address_line1}
                        {selectedClient.address_line2 && `, ${selectedClient.address_line2}`}
                        <br />
                        {selectedClient.city}, {selectedClient.state} {selectedClient.postal_code}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Financial Information */}
              {(selectedClient.billing_rate_hourly || selectedClient.retainer_amount) && (
                <div className="bg-white rounded-lg shadow p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Financial Information</h3>
                  <div className="space-y-3 text-sm">
                    {selectedClient.billing_rate_hourly && (
                      <div>
                        <span className="font-medium text-gray-700">Billing Rate:</span>
                        <p className="text-gray-900">${(selectedClient.billing_rate_hourly / 100).toFixed(2)}/hour</p>
                      </div>
                    )}
                    {selectedClient.retainer_amount && (
                      <div>
                        <span className="font-medium text-gray-700">Retainer:</span>
                        <p className="text-gray-900">${(selectedClient.retainer_amount / 100).toFixed(2)}</p>
                      </div>
                    )}
                    {selectedClient.retainer_balance !== undefined && (
                      <div>
                        <span className="font-medium text-gray-700">Retainer Balance:</span>
                        <p className="text-gray-900">${(selectedClient.retainer_balance / 100).toFixed(2)}</p>
                      </div>
                    )}
                    {selectedClient.payment_terms && (
                      <div>
                        <span className="font-medium text-gray-700">Payment Terms:</span>
                        <p className="text-gray-900">{selectedClient.payment_terms}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Notes */}
              {selectedClient.notes && (
                <div className="bg-white rounded-lg shadow p-6 md:col-span-2">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Notes</h3>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{selectedClient.notes}</p>
                </div>
              )}
            </div>

            {/* Action Tabs */}
            <div className="bg-white rounded-lg shadow">
              <div className="border-b border-gray-200 px-6 py-4">
                <h3 className="text-lg font-semibold text-gray-900">Client Actions</h3>
              </div>
              <div className="p-6 text-center text-gray-500">
                <p className="mb-4">Additional client management features coming soon:</p>
                <ul className="text-sm space-y-2">
                  <li>• Case management</li>
                  <li>• Document sharing</li>
                  <li>• Communication history</li>
                  <li>• Billing and invoicing</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Help Section */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-sm font-semibold text-blue-900 mb-3">Client Management Tips</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-blue-800">
            <div>
              <h4 className="font-semibold mb-1">Create Clients:</h4>
              <p>Add new clients with contact and billing information for easy reference.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-1">Track Cases:</h4>
              <p>Associate cases with clients to maintain organized case files.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-1">Share Documents:</h4>
              <p>Securely share documents with clients through the portal.</p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
