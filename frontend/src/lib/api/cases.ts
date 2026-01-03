import { API_CONFIG } from '../../config/api';

/**
 * Case Management API Client
 * Handles all interactions with the case management backend
 */

const API_BASE = `${API_CONFIG.BASE_URL}/api/v1/cases`;

export interface LegalCase {
  id: string;
  case_number: string;
  case_name: string;
  case_type: string;
  status: string;
  court_name?: string;
  jurisdiction?: string;
  judge_name?: string;
  court_division?: string;
  filing_date?: string;
  status_date?: string;
  close_date?: string;
  description?: string;
  current_phase?: string;
  estimated_completion_date?: string;
  created_at: string;
  updated_at: string;
  notes?: string;
  tags?: string[];
}

export interface CaseParty {
  id: string;
  case_id: string;
  party_type?: string;
  role: string;
  name: string;
  legal_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  represented_by?: string;
  attorney_firm?: string;
  interest_amount?: number;
  authorization_level?: string;
  can_receive_notices?: boolean;
  preferred_contact_method?: string;
  created_at: string;
  notes?: string;
}

export interface TimelineEvent {
  id: string;
  case_id: string;
  event_type: string;
  title: string;
  description?: string;
  event_date: string;
  end_date?: string;
  location?: string;
  status: string;
  is_critical_path?: boolean;
  priority_level?: number;
  required_actions?: any[];
  outcome?: string;
  created_at: string;
}

export interface FinancialTransaction {
  id: string;
  case_id: string;
  transaction_type: string;
  transaction_date: string;
  amount: number;
  currency?: string;
  description?: string;
  payment_status?: string;
  approval_status?: string;
  created_at: string;
}

export interface CaseCreateData {
  case_number: string;
  case_name: string;
  case_type: string;
  court_name?: string;
  jurisdiction?: string;
  judge_name?: string;
  filing_date?: string;
  description?: string;
}

export interface CaseUpdateData {
  case_name?: string;
  status?: string;
  current_phase?: string;
  description?: string;
  notes?: string;
  tags?: string[];
}

// ============================================================================
// CASE CRUD OPERATIONS
// ============================================================================

export async function getCases(): Promise<LegalCase[]> {
  const response = await fetch(API_BASE);
  if (!response.ok) {
    throw new Error(`Failed to fetch cases: ${response.statusText}`);
  }
  return response.json();
}

export async function getCase(id: string): Promise<LegalCase> {
  const response = await fetch(`${API_BASE}/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch case: ${response.statusText}`);
  }
  return response.json();
}

export async function createCase(data: CaseCreateData): Promise<LegalCase> {
  const response = await fetch(API_BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to create case');
  }
  return response.json();
}

export async function updateCase(id: string, data: CaseUpdateData): Promise<LegalCase> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to update case: ${response.statusText}`);
  }
  return response.json();
}

export async function deleteCase(id: string): Promise<void> {
  const response = await fetch(`${API_BASE}/${id}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete case: ${response.statusText}`);
  }
}

// ============================================================================
// PARTIES
// ============================================================================

export async function getCaseParties(caseId: string): Promise<CaseParty[]> {
  const response = await fetch(`${API_BASE}/${caseId}/parties`);
  if (!response.ok) {
    throw new Error(`Failed to fetch parties: ${response.statusText}`);
  }
  return response.json();
}

export async function addParty(caseId: string, data: Partial<CaseParty>): Promise<CaseParty> {
  const response = await fetch(`${API_BASE}/${caseId}/parties`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to add party: ${response.statusText}`);
  }
  return response.json();
}

// ============================================================================
// TIMELINE EVENTS
// ============================================================================

export async function getTimeline(caseId: string): Promise<TimelineEvent[]> {
  const response = await fetch(`${API_BASE}/${caseId}/timeline`);
  if (!response.ok) {
    throw new Error(`Failed to fetch timeline: ${response.statusText}`);
  }
  return response.json();
}

export async function addTimelineEvent(caseId: string, data: Partial<TimelineEvent>): Promise<TimelineEvent> {
  const response = await fetch(`${API_BASE}/${caseId}/timeline`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`Failed to add timeline event: ${response.statusText}`);
  }
  return response.json();
}

// ============================================================================
// FINANCIAL TRANSACTIONS
// ============================================================================

export async function getTransactions(caseId: string): Promise<FinancialTransaction[]> {
  const response = await fetch(`${API_BASE}/${caseId}/transactions`);
  if (!response.ok) {
    throw new Error(`Failed to fetch transactions: ${response.statusText}`);
  }
  return response.json();
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

export function formatCaseType(type: string): string {
  const types: Record<string, string> = {
    'bankruptcy_ch7': 'Bankruptcy Chapter 7',
    'bankruptcy_ch11': 'Bankruptcy Chapter 11',
    'bankruptcy_ch13': 'Bankruptcy Chapter 13',
    'civil_litigation': 'Civil Litigation',
    'debt_collection': 'Debt Collection',
    'foreclosure': 'Foreclosure',
    'eviction': 'Eviction',
    'criminal': 'Criminal',
    'employment': 'Employment',
    'contract_dispute': 'Contract Dispute',
    'other': 'Other',
  };
  return types[type] || type;
}

export function formatCaseStatus(status: string): string {
  const statuses: Record<string, string> = {
    'intake': 'Intake',
    'active': 'Active',
    'pending': 'Pending',
    'stayed': 'Stayed',
    'closed': 'Closed',
    'dismissed': 'Dismissed',
    'settled': 'Settled',
    'appealed': 'Appealed',
  };
  return statuses[status] || status;
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    'intake': 'bg-blue-100 text-blue-800 border-blue-200',
    'active': 'bg-green-100 text-green-800 border-green-200',
    'pending': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    'stayed': 'bg-orange-100 text-orange-800 border-orange-200',
    'closed': 'bg-gray-100 text-gray-800 border-gray-200',
    'dismissed': 'bg-red-100 text-red-800 border-red-200',
    'settled': 'bg-emerald-100 text-emerald-800 border-emerald-200',
    'appealed': 'bg-purple-100 text-purple-800 border-purple-200',
  };
  return colors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
}
