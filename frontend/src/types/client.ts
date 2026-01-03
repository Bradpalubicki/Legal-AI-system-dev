/**
 * Client Management Type Definitions
 *
 * Types for client relationship management, document sharing, and case tracking.
 */

export interface Client {
  id: number
  client_number: string
  client_type: ClientType
  status: ClientStatus
  display_name: string

  // Individual
  first_name?: string
  last_name?: string
  full_name?: string
  date_of_birth?: string
  ssn_last_four?: string

  // Business
  company_name?: string
  business_type?: string
  ein?: string
  industry?: string

  // Contact
  email?: string
  phone_primary?: string
  phone_secondary?: string
  fax?: string

  // Address
  address_line1?: string
  address_line2?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string

  // Portal
  portal_access_enabled?: boolean
  portal_access_level?: AccessLevel
  portal_last_login?: string

  // Financial
  billing_rate_hourly?: number
  retainer_amount?: number
  retainer_balance?: number
  payment_terms?: string

  // Metadata
  tags?: string[]
  notes?: string
  created_at: string
  updated_at: string
}

export enum ClientType {
  INDIVIDUAL = 'individual',
  BUSINESS = 'business',
  GOVERNMENT = 'government',
  NONPROFIT = 'nonprofit'
}

export enum ClientStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  ARCHIVED = 'archived'
}

export enum AccessLevel {
  READ_ONLY = 'read_only',
  COMMENT = 'comment',
  DOWNLOAD = 'download',
  FULL = 'full'
}

export interface ClientCreateRequest {
  client_type: ClientType
  first_name?: string
  last_name?: string
  company_name?: string
  email?: string
  phone_primary?: string
  address_line1?: string
  city?: string
  state?: string
  postal_code?: string
}

export interface ClientUpdateRequest {
  first_name?: string
  last_name?: string
  company_name?: string
  email?: string
  phone_primary?: string
  status?: ClientStatus
  portal_access_enabled?: boolean
  notes?: string
  tags?: string[]
}

export interface ClientListResponse {
  clients: Client[]
  total: number
  page: number
  page_size: number
}

export interface Case {
  id: number
  case_number: string
  case_name: string
  case_type?: string
  practice_area?: string
  status: CaseStatus
  priority?: string

  client_id: number

  // Court info
  court_name?: string
  court_case_number?: string
  judge_name?: string
  opposing_party?: string
  opposing_counsel?: string

  // Dates
  opened_date: string
  closed_date?: string
  trial_date?: string
  statute_limitations_date?: string

  // Financial
  billing_type?: string
  estimated_value?: number

  // Description
  description?: string
  legal_issues?: string
  outcome?: string

  created_at: string
  updated_at: string
}

export enum CaseStatus {
  OPEN = 'open',
  PENDING = 'pending',
  CLOSED = 'closed',
  ARCHIVED = 'archived'
}

export interface CaseCreateRequest {
  case_name: string
  case_type?: string
  practice_area?: string
  description?: string
  opened_date?: string
  court_name?: string
}

export interface SharedDocument {
  id: number
  filename: string
  title?: string
  description?: string
  file_size?: number
  mime_type?: string

  client_id: number
  case_id?: number

  // Access
  share_token: string
  password_protected: boolean
  expires_at?: string
  access_level: AccessLevel

  // Status
  status: DocumentShareStatus
  view_count: number
  download_count: number
  first_viewed_at?: string
  last_viewed_at?: string

  // Metadata
  shared_at: string
  shared_by_user_id: number
}

export enum DocumentShareStatus {
  PENDING = 'pending',
  VIEWED = 'viewed',
  DOWNLOADED = 'downloaded',
  ACKNOWLEDGED = 'acknowledged',
  EXPIRED = 'expired'
}

export interface DocumentShareRequest {
  filename: string
  title?: string
  description?: string
  file_path: string
  case_id?: number
  password?: string
  expires_days?: number
  access_level?: AccessLevel
}

export interface DocumentShareResponse {
  document: SharedDocument
  share_url: string
}

export interface ClientCommunication {
  id: number
  client_id: number
  case_id?: number
  user_id: number

  communication_type: string  // email, phone, meeting, letter
  direction: string  // inbound, outbound
  subject?: string
  summary?: string

  duration_minutes?: number
  billable: boolean
  billable_time_minutes?: number

  is_privileged: boolean
  communication_date: string
  created_at: string
}
