/**
 * Hook for admin disclaimer acknowledgment management
 * Fetches analytics and acknowledgment records
 */

import { useState, useCallback } from 'react';
import { API_CONFIG } from '../config/api';

export interface AcknowledgmentRecord {
  id: string;
  user_id: string;
  user_type: 'attorney' | 'client' | 'staff' | 'user';
  disclaimer_type: string;
  action: string;
  acknowledged: boolean;
  acknowledged_at: string | null;
  dismissed_at: string | null;
  disabled_at: string | null;
  view_count: number;
  time_to_acknowledge: number | null;
  page_context: string;
  jurisdiction: string;
  session_id: string;
  ip_address: string;
  user_agent: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  follow_up_required: boolean;
  created_at: string;
}

export interface AcknowledgmentPattern {
  disclaimer_type: string;
  total_shown: number;
  acknowledged: number;
  average_time_to_acknowledge: number;
  drop_off_rate: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

interface FetchAcknowledgmentsParams {
  disclaimer_type?: string;
  user_id?: number;
  acknowledged?: boolean;
  risk_level?: string;
  jurisdiction?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export function useAdminDisclaimers() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  };

  const fetchAcknowledgments = useCallback(async (
    params: FetchAcknowledgmentsParams = {}
  ): Promise<{ total: number; acknowledgments: AcknowledgmentRecord[] }> => {
    setLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams();
      if (params.disclaimer_type) queryParams.append('disclaimer_type', params.disclaimer_type);
      if (params.user_id) queryParams.append('user_id', String(params.user_id));
      if (params.acknowledged !== undefined) queryParams.append('acknowledged', String(params.acknowledged));
      if (params.risk_level) queryParams.append('risk_level', params.risk_level);
      if (params.jurisdiction) queryParams.append('jurisdiction', params.jurisdiction);
      if (params.start_date) queryParams.append('start_date', params.start_date);
      if (params.end_date) queryParams.append('end_date', params.end_date);
      if (params.limit) queryParams.append('limit', String(params.limit));
      if (params.offset) queryParams.append('offset', String(params.offset));

      const response = await fetch(
        `${API_CONFIG.BASE_URL}/api/v1/disclaimers/admin/acknowledgments?${queryParams}`,
        {
          method: 'GET',
          headers: getAuthHeaders()
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch acknowledgments' }));
        throw new Error(errorData.detail || 'Failed to fetch acknowledgments');
      }

      const data = await response.json();
      return {
        total: data.total || 0,
        acknowledgments: data.acknowledgments || []
      };
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch acknowledgments';
      setError(errorMessage);
      return { total: 0, acknowledgments: [] };
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAnalytics = useCallback(async (): Promise<AcknowledgmentPattern[]> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_CONFIG.BASE_URL}/api/v1/disclaimers/admin/analytics`,
        {
          method: 'GET',
          headers: getAuthHeaders()
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch analytics' }));
        throw new Error(errorData.detail || 'Failed to fetch analytics');
      }

      const data = await response.json();
      return data.patterns || [];
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch analytics';
      setError(errorMessage);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchHighRiskUsers = useCallback(async (): Promise<AcknowledgmentRecord[]> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_CONFIG.BASE_URL}/api/v1/disclaimers/admin/high-risk-users`,
        {
          method: 'GET',
          headers: getAuthHeaders()
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch high-risk users' }));
        throw new Error(errorData.detail || 'Failed to fetch high-risk users');
      }

      const data = await response.json();
      return data.high_risk_acknowledgments || [];
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch high-risk users';
      setError(errorMessage);
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    fetchAcknowledgments,
    fetchAnalytics,
    fetchHighRiskUsers,
    loading,
    error
  };
}
