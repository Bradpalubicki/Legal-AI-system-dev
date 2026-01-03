/**
 * Legal Research Type Definitions
 *
 * Types for case law search, citation extraction, and legal research features.
 */

export interface CaseSearchRequest {
  query: string
  court?: string
  date_filed_after?: string
  date_filed_before?: string
  jurisdiction?: string
  case_name?: string
  citation?: string
  limit?: number
  providers?: string[]
}

export interface CaseSearchResult {
  case_id: string
  case_name: string
  citation: string
  court: string
  date_filed: string
  snippet: string
  url?: string
  provider: string
  docket_number?: string
  judges?: string[]
  relevance_score?: number
}

export interface CaseSearchResponse {
  total_results: number
  query: string
  results: CaseSearchResult[]
  providers_used: string[]
}

export interface CaseDetailsRequest {
  case_id: string
  provider?: string
}

export interface SimilarCasesRequest {
  case_text: string
  jurisdiction?: string
  limit?: number
}

export interface CitationExtractionRequest {
  text: string
  validate?: boolean
  citation_types?: string[]
}

export interface ExtractedCitation {
  text: string
  type: CitationType
  status: CitationStatus
  span: [number, number]
  confidence: number

  // Case fields
  case_name?: string
  reporter?: string
  volume?: number
  page?: number
  year?: number
  court?: string

  // Statute fields
  title?: string
  section?: string
  jurisdiction?: string

  // Enrichment
  url?: string
  bluebook?: string
  full_case_name?: string
}

export enum CitationType {
  CASE = 'case',
  STATUTE = 'statute',
  REGULATION = 'regulation',
  CONSTITUTIONAL = 'constitutional',
  UNKNOWN = 'unknown'
}

export enum CitationStatus {
  VALID = 'valid',
  INVALID = 'invalid',
  UNVALIDATED = 'unvalidated',
  AMBIGUOUS = 'ambiguous'
}

export interface CitationExtractionResponse {
  total_citations: number
  by_type: Record<string, number>
  by_status: Record<string, number>
  validation_rate: number
  citations: ExtractedCitation[]
}

export interface ResearchProvider {
  name: string
  id: string
  type: 'free' | 'paid'
  capabilities: string[]
  configured: boolean
  setup_url?: string
  contact?: string
}

export interface ProvidersResponse {
  providers: ResearchProvider[]
  total: number
  configured: number
}

export interface Court {
  code: string
  name: string
  level: 'supreme' | 'appellate' | 'district' | 'state'
}

export interface CourtsResponse {
  courts: Court[]
  total: number
}

export interface CitationValidationResponse {
  citation: string
  is_valid: boolean
  status: CitationStatus
  confidence: number
  bluebook?: string
  case_name?: string
  url?: string
  type: CitationType
}
