import { API_CONFIG } from '../../config/api';

/**
 * Case Management API Client
 * All API calls for case management system
 */

import {
  LegalCase,
  Party,
  TimelineEvent,
  FinancialTransaction,
  Asset,
  BiddingProcess,
  Objection,
  CaseDashboard,
  CriticalPathAnalysis,
  EventImpact,
  StrategicSummary,
  TalkingPoints,
  ActionItemsResponse,
  CreateCaseRequest,
  UpdateCaseRequest,
  CreatePartyRequest,
  CreateEventRequest,
  CreateAssetRequest,
  CreateBiddingProcessRequest,
  SubmitBidRequest,
  CreateObjectionRequest,
  CalculationRequest,
  CalculationResponse,
  CaseStatus,
  CaseType,
  PartyRole,
  EventType,
  EventStatus,
  AssetStatus,
  ObjectionStatus,
} from '@/types/case-management';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || API_CONFIG.BASE_URL;

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  };

  const response = await fetch(url, defaultOptions);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API Error: ${response.statusText}`);
  }

  return response.json();
}

// ============================================================================
// CASE ENDPOINTS
// ============================================================================

export const caseManagementAPI = {
  // Cases
  cases: {
    list: async (params?: {
      status?: CaseStatus;
      case_type?: CaseType;
      skip?: number;
      limit?: number;
    }): Promise<LegalCase[]> => {
      const queryParams = new URLSearchParams();
      if (params?.status) queryParams.append('status_filter', params.status);
      if (params?.case_type) queryParams.append('case_type_filter', params.case_type);
      if (params?.skip !== undefined) queryParams.append('skip', params.skip.toString());
      if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());

      const query = queryParams.toString();
      return fetchAPI<LegalCase[]>(`/api/v1/cases${query ? `?${query}` : ''}`);
    },

    get: async (caseId: string): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}`);
    },

    create: async (data: CreateCaseRequest): Promise<LegalCase> => {
      return fetchAPI<LegalCase>('/api/v1/cases', {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    update: async (caseId: string, data: UpdateCaseRequest): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
    },

    delete: async (caseId: string): Promise<{ message: string }> => {
      return fetchAPI<{ message: string }>(`/api/v1/cases/${caseId}`, {
        method: 'DELETE',
      });
    },

    getDashboard: async (caseId: string): Promise<CaseDashboard> => {
      return fetchAPI<CaseDashboard>(`/api/v1/cases/${caseId}/dashboard`);
    },
  },

  // Parties
  parties: {
    list: async (caseId: string, role?: PartyRole): Promise<any[]> => {
      const query = role ? `?role_filter=${role}` : '';
      return fetchAPI<any[]>(`/api/v1/cases/${caseId}/parties${query}`);
    },

    get: async (caseId: string, partyId: string): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/parties/${partyId}`);
    },

    create: async (caseId: string, data: CreatePartyRequest): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/parties`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
  },

  // Timeline Events
  events: {
    list: async (caseId: string, params?: {
      event_type?: EventType;
      status?: EventStatus;
      start_date?: string;
      end_date?: string;
    }): Promise<any[]> => {
      const queryParams = new URLSearchParams();
      if (params?.event_type) queryParams.append('event_type_filter', params.event_type);
      if (params?.status) queryParams.append('status_filter', params.status);
      if (params?.start_date) queryParams.append('start_date', params.start_date);
      if (params?.end_date) queryParams.append('end_date', params.end_date);

      const query = queryParams.toString();
      return fetchAPI<any[]>(`/api/v1/cases/${caseId}/events${query ? `?${query}` : ''}`);
    },

    create: async (caseId: string, data: CreateEventRequest): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/events`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    update: async (caseId: string, eventId: string, data: Partial<TimelineEvent>): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/events/${eventId}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      });
    },
  },

  // Financial Transactions
  transactions: {
    list: async (caseId: string, params?: {
      transaction_type?: string;
      start_date?: string;
      end_date?: string;
    }): Promise<any[]> => {
      const queryParams = new URLSearchParams();
      if (params?.transaction_type) queryParams.append('transaction_type_filter', params.transaction_type);
      if (params?.start_date) queryParams.append('start_date', params.start_date);
      if (params?.end_date) queryParams.append('end_date', params.end_date);

      const query = queryParams.toString();
      return fetchAPI<any[]>(`/api/v1/cases/${caseId}/transactions${query ? `?${query}` : ''}`);
    },

    create: async (caseId: string, data: any): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/transactions`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
  },

  // Assets
  assets: {
    list: async (caseId: string, params?: {
      status?: AssetStatus;
      asset_type?: string;
    }): Promise<any[]> => {
      const queryParams = new URLSearchParams();
      if (params?.status) queryParams.append('status_filter', params.status);
      if (params?.asset_type) queryParams.append('asset_type', params.asset_type);

      const query = queryParams.toString();
      return fetchAPI<any[]>(`/api/v1/cases/${caseId}/assets${query ? `?${query}` : ''}`);
    },

    get: async (caseId: string, assetId: string): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/assets/${assetId}`);
    },

    create: async (caseId: string, data: CreateAssetRequest): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/assets`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
  },

  // Bidding Process
  bidding: {
    list: async (caseId: string, status?: string): Promise<any[]> => {
      const query = status ? `?status_filter=${status}` : '';
      return fetchAPI<any[]>(`/api/v1/cases/${caseId}/bidding${query}`);
    },

    get: async (caseId: string, biddingId: string): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/bidding/${biddingId}`);
    },

    create: async (caseId: string, data: CreateBiddingProcessRequest): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/bidding`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    submitBid: async (caseId: string, biddingId: string, data: SubmitBidRequest): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/bidding/${biddingId}/bids`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },

    calculate: async (
      caseId: string,
      biddingId: string,
      calculationType: 'increment' | 'deposit' | 'credit_bid',
      params?: Record<string, any>
    ): Promise<CalculationResponse> => {
      return fetchAPI<CalculationResponse>(
        `/api/v1/cases/${caseId}/bidding/${biddingId}/calculate?calculation_type=${calculationType}`,
        {
          method: 'POST',
          body: JSON.stringify(params || {}),
        }
      );
    },
  },

  // Objections
  objections: {
    list: async (caseId: string, params?: {
      status?: ObjectionStatus;
      objection_type?: string;
    }): Promise<any[]> => {
      const queryParams = new URLSearchParams();
      if (params?.status) queryParams.append('status_filter', params.status);
      if (params?.objection_type) queryParams.append('objection_type', params.objection_type);

      const query = queryParams.toString();
      return fetchAPI<any[]>(`/api/v1/cases/${caseId}/objections${query ? `?${query}` : ''}`);
    },

    get: async (caseId: string, objectionId: string): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/objections/${objectionId}`);
    },

    create: async (caseId: string, data: CreateObjectionRequest): Promise<any> => {
      return fetchAPI<any>(`/api/v1/cases/${caseId}/objections`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
  },

  // Timeline & Workflow
  timeline: {
    getCriticalPath: async (caseId: string): Promise<CriticalPathAnalysis> => {
      return fetchAPI<CriticalPathAnalysis>(`/api/v1/cases/${caseId}/timeline/critical-path`);
    },

    getEventImpact: async (caseId: string, eventId: string): Promise<EventImpact> => {
      return fetchAPI<EventImpact>(`/api/v1/cases/${caseId}/timeline/${eventId}/impact`);
    },
  },

  // Attorney Briefing
  briefing: {
    getStrategicSummary: async (caseId: string): Promise<StrategicSummary> => {
      return fetchAPI<StrategicSummary>(`/api/v1/cases/${caseId}/briefing/strategic-summary`);
    },

    getTalkingPoints: async (caseId: string, nextHearingId?: string): Promise<TalkingPoints> => {
      const query = nextHearingId ? `?next_hearing_id=${nextHearingId}` : '';
      return fetchAPI<TalkingPoints>(`/api/v1/cases/${caseId}/briefing/talking-points${query}`);
    },

    getActionItems: async (caseId: string): Promise<ActionItemsResponse> => {
      return fetchAPI<ActionItemsResponse>(`/api/v1/cases/${caseId}/briefing/action-items`);
    },
  },
};

// Export individual namespace APIs for convenience
export const {
  cases,
  parties,
  events,
  transactions,
  assets,
  bidding,
  objections,
  timeline,
  briefing,
} = caseManagementAPI;
