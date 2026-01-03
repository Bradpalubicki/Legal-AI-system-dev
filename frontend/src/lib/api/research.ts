/**
 * Legal Research API Client
 *
 * Provides methods for interacting with legal research endpoints:
 * - Case law search
 * - Citation extraction and validation
 * - Provider management
 */

import apiClient from '../api'
import type {
  CaseSearchRequest,
  CaseSearchResponse,
  CaseDetailsRequest,
  SimilarCasesRequest,
  CitationExtractionRequest,
  CitationExtractionResponse,
  CitationValidationResponse,
  ProvidersResponse,
  CourtsResponse
} from '@/types/research'

const BASE_PATH = '/api/v1/research'

export class ResearchApiClient {
  /**
   * Search for case law across legal databases
   */
  async searchCases(request: CaseSearchRequest): Promise<CaseSearchResponse> {
    const response = await apiClient.post<CaseSearchResponse>(
      `${BASE_PATH}/cases/search`,
      request
    )
    return response.data!
  }

  /**
   * Get detailed information about a specific case
   */
  async getCaseDetails(request: CaseDetailsRequest): Promise<any> {
    const response = await apiClient.post<any>(
      `${BASE_PATH}/cases/details`,
      request
    )
    return response.data!
  }

  /**
   * Find cases similar to provided text
   */
  async findSimilarCases(request: SimilarCasesRequest): Promise<CaseSearchResponse> {
    const response = await apiClient.post<CaseSearchResponse>(
      `${BASE_PATH}/cases/similar`,
      request
    )
    return response.data!
  }

  /**
   * Extract and validate citations from text
   */
  async extractCitations(request: CitationExtractionRequest): Promise<CitationExtractionResponse> {
    const response = await apiClient.post<CitationExtractionResponse>(
      `${BASE_PATH}/citations/extract`,
      request
    )
    return response.data!
  }

  /**
   * Validate a single citation
   */
  async validateCitation(citation: string): Promise<CitationValidationResponse> {
    const encodedCitation = encodeURIComponent(citation)
    const response = await apiClient.get<CitationValidationResponse>(
      `${BASE_PATH}/citations/validate/${encodedCitation}`
    )
    return response.data!
  }

  /**
   * Get available research providers
   */
  async getProviders(): Promise<ProvidersResponse> {
    const response = await apiClient.get<ProvidersResponse>(
      `${BASE_PATH}/providers`
    )
    return response.data!
  }

  /**
   * Get supported courts
   */
  async getCourts(): Promise<CourtsResponse> {
    const response = await apiClient.get<CourtsResponse>(
      `${BASE_PATH}/courts`
    )
    return response.data!
  }
}

// Singleton instance
export const researchApi = new ResearchApiClient()
export default researchApi
