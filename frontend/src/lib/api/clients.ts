/**
 * Client Management API Client
 *
 * Provides methods for managing clients, cases, and document sharing.
 */

import apiClient from '../api'
import type {
  Client,
  ClientCreateRequest,
  ClientUpdateRequest,
  ClientListResponse,
  Case,
  CaseCreateRequest,
  SharedDocument,
  DocumentShareRequest,
  DocumentShareResponse,
  ClientCommunication
} from '@/types/client'

const BASE_PATH = '/api/v1/clients'

export class ClientsApiClient {
  /**
   * Create a new client
   */
  async createClient(request: ClientCreateRequest): Promise<Client> {
    const response = await apiClient.post<Client>(BASE_PATH, request)
    return response.data!
  }

  /**
   * Get list of clients with optional search/filter
   */
  async listClients(params?: {
    search?: string
    status?: string
    client_type?: string
    skip?: number
    limit?: number
  }): Promise<ClientListResponse> {
    const response = await apiClient.get<ClientListResponse>(BASE_PATH, { params })
    return response.data!
  }

  /**
   * Get client details by ID
   */
  async getClient(clientId: number): Promise<Client> {
    const response = await apiClient.get<Client>(`${BASE_PATH}/${clientId}`)
    return response.data!
  }

  /**
   * Update client information
   */
  async updateClient(clientId: number, request: ClientUpdateRequest): Promise<Client> {
    const response = await apiClient.patch<Client>(`${BASE_PATH}/${clientId}`, request)
    return response.data!
  }

  /**
   * Archive a client (soft delete)
   */
  async archiveClient(clientId: number): Promise<void> {
    await apiClient.delete(`${BASE_PATH}/${clientId}`)
  }

  /**
   * Create a case for a client
   */
  async createCase(clientId: number, request: CaseCreateRequest): Promise<Case> {
    const response = await apiClient.post<Case>(
      `${BASE_PATH}/${clientId}/cases`,
      request
    )
    return response.data!
  }

  /**
   * Get all cases for a client
   */
  async listCases(clientId: number, params?: {
    status?: string
    skip?: number
    limit?: number
  }): Promise<{ cases: Case[]; total: number }> {
    const response = await apiClient.get<{ cases: Case[]; total: number }>(
      `${BASE_PATH}/${clientId}/cases`,
      { params }
    )
    return response.data!
  }

  /**
   * Share a document with a client
   */
  async shareDocument(clientId: number, request: DocumentShareRequest): Promise<DocumentShareResponse> {
    const response = await apiClient.post<DocumentShareResponse>(
      `${BASE_PATH}/${clientId}/documents/share`,
      request
    )
    return response.data!
  }

  /**
   * List shared documents for a client
   */
  async listSharedDocuments(clientId: number, params?: {
    status?: string
    case_id?: number
    skip?: number
    limit?: number
  }): Promise<{ documents: SharedDocument[]; total: number }> {
    const response = await apiClient.get<{ documents: SharedDocument[]; total: number }>(
      `${BASE_PATH}/${clientId}/documents`,
      { params }
    )
    return response.data!
  }

  /**
   * Get shared document details
   */
  async getSharedDocument(clientId: number, documentId: number): Promise<SharedDocument> {
    const response = await apiClient.get<SharedDocument>(
      `${BASE_PATH}/${clientId}/documents/${documentId}`
    )
    return response.data!
  }

  /**
   * Update shared document
   */
  async updateSharedDocument(
    clientId: number,
    documentId: number,
    updates: Partial<DocumentShareRequest>
  ): Promise<SharedDocument> {
    const response = await apiClient.patch<SharedDocument>(
      `${BASE_PATH}/${clientId}/documents/${documentId}`,
      updates
    )
    return response.data!
  }

  /**
   * Revoke document access
   */
  async revokeDocument(clientId: number, documentId: number): Promise<void> {
    await apiClient.delete(`${BASE_PATH}/${clientId}/documents/${documentId}`)
  }

  /**
   * Log communication with client
   */
  async logCommunication(
    clientId: number,
    communication: {
      communication_type: string
      direction: string
      subject?: string
      summary?: string
      case_id?: number
      duration_minutes?: number
      billable?: boolean
    }
  ): Promise<ClientCommunication> {
    const response = await apiClient.post<ClientCommunication>(
      `${BASE_PATH}/${clientId}/communications`,
      communication
    )
    return response.data!
  }

  /**
   * Get communication history for client
   */
  async listCommunications(clientId: number, params?: {
    case_id?: number
    communication_type?: string
    skip?: number
    limit?: number
  }): Promise<{ communications: ClientCommunication[]; total: number }> {
    const response = await apiClient.get<{ communications: ClientCommunication[]; total: number }>(
      `${BASE_PATH}/${clientId}/communications`,
      { params }
    )
    return response.data!
  }
}

// Singleton instance
export const clientsApi = new ClientsApiClient()
export default clientsApi
