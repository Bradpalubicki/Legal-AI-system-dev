/**
 * useCaseAccess Hook
 * React hook for checking and managing case access
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from './useAuth';

export interface CaseAccess {
  id: number;
  case_id: number;
  case_number: string;
  case_name: string;
  access_type: string;
  status: string;
  amount_paid?: number;
  granted_at?: string;
  expires_at?: string;
  days_remaining?: number | null;
  notifications_enabled: boolean;
  is_active: boolean;
}

export interface CaseAccessCheckResponse {
  has_access: boolean;
  access_type?: string;
  expires_at?: string;
  days_remaining?: number;
  subscription_tier?: string;
  message?: string;
  purchase_options?: Array<{
    type: string;
    price: number;
    description: string;
  }>;
}

/**
 * Check if user has access to a specific case
 */
export function useCaseAccessCheck(caseId: number | null) {
  const { user, isAuthenticated } = useAuth();

  return useQuery<CaseAccessCheckResponse>({
    queryKey: ['case-access-check', caseId, user?.id],
    queryFn: async () => {
      if (!isAuthenticated || !caseId) {
        return {
          has_access: false,
          message: 'Authentication required',
        };
      }

      const response = await fetch(`/api/v1/case-access/${caseId}/check`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to check case access');
      }

      return response.json();
    },
    enabled: !!user && !!caseId,
    staleTime: 60 * 1000, // Cache for 1 minute
  });
}

/**
 * Get all cases user has access to
 */
export function useMyCases() {
  const { user, isAuthenticated } = useAuth();

  return useQuery<CaseAccess[]>({
    queryKey: ['my-case-access', user?.id],
    queryFn: async () => {
      const response = await fetch('/api/v1/case-access/my-cases', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get case access');
      }

      return response.json();
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

/**
 * Cancel case access
 */
export function useCancelCaseAccess() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (caseAccessId: number) => {
      const response = await fetch(`/api/v1/case-access/${caseAccessId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to cancel case access');
      }

      return response.json();
    },
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['my-case-access'] });
      queryClient.invalidateQueries({ queryKey: ['case-access-check'] });
    },
  });
}

/**
 * Update notification settings for a case
 */
export function useUpdateNotifications() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ caseAccessId, enabled }: { caseAccessId: number; enabled: boolean }) => {
      const response = await fetch(
        `/api/v1/case-access/${caseAccessId}/notifications?enabled=${enabled}`,
        {
          method: 'PUT',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update notifications');
      }

      return response.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['my-case-access'] });
    },
  });
}

/**
 * Purchase case access
 */
export async function purchaseCaseAccess({
  caseId,
  accessType = 'one_time',
  successUrl,
  cancelUrl,
}: {
  caseId: number;
  accessType?: 'one_time' | 'monthly';
  successUrl: string;
  cancelUrl: string;
}) {
  const response = await fetch('/api/v1/case-access/purchase', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      case_id: caseId,
      access_type: accessType,
      success_url: successUrl,
      cancel_url: cancelUrl,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail?.message || 'Failed to create checkout session');
  }

  return response.json();
}
