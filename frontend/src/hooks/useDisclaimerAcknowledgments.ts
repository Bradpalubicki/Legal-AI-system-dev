/**
 * Hook for managing disclaimer acknowledgments
 * Tracks when users confirm/dismiss/view liability disclaimers
 */

import { useState, useCallback } from 'react';
import { API_CONFIG } from '../config/api';

interface AcknowledgeRequest {
  disclaimer_id: string;
  disclaimer_type: string;
  page_url?: string;
  page_context?: string;
  jurisdiction?: string;
  time_to_acknowledge?: number;
  time_on_page?: number;
  session_id?: string;
  metadata?: Record<string, any>;
}

interface DismissRequest {
  disclaimer_id: string;
  disclaimer_type: string;
  reason?: string;
  page_url?: string;
  page_context?: string;
  session_id?: string;
}

interface ViewRequest {
  disclaimer_id: string;
  disclaimer_type: string;
  page_url?: string;
  page_context?: string;
  time_on_page?: number;
  session_id?: string;
}

interface DisclaimerStatus {
  acknowledged: boolean;
  acknowledged_at?: string;
  view_count: number;
  risk_level: string;
  follow_up_required: boolean;
  needs_re_acknowledgment: boolean;
}

export function useDisclaimerAcknowledgments() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  };

  const acknowledgeDisclaimer = useCallback(async (request: AcknowledgeRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/disclaimers/acknowledge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to acknowledge disclaimer' }));
        throw new Error(errorData.detail || 'Failed to acknowledge disclaimer');
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to acknowledge disclaimer';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const dismissDisclaimer = useCallback(async (request: DismissRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/disclaimers/dismiss`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to dismiss disclaimer' }));
        throw new Error(errorData.detail || 'Failed to dismiss disclaimer');
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to dismiss disclaimer';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const recordView = useCallback(async (request: ViewRequest) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/disclaimers/view`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to record view' }));
        throw new Error(errorData.detail || 'Failed to record view');
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to record view';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getDisclaimerStatus = useCallback(async (disclaimerId: string): Promise<DisclaimerStatus | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_CONFIG.BASE_URL}/api/v1/disclaimers/status/${disclaimerId}`,
        {
          method: 'GET',
          headers: getAuthHeaders()
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to get status' }));
        throw new Error(errorData.detail || 'Failed to get status');
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get disclaimer status';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    acknowledgeDisclaimer,
    dismissDisclaimer,
    recordView,
    getDisclaimerStatus,
    loading,
    error
  };
}
