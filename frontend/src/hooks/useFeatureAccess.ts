/**
 * useFeatureAccess Hook
 * React hook for checking feature access and getting upgrade information
 */
import { useQuery } from '@tanstack/react-query';
import { useAuth } from './useAuth';

export interface FeatureConfig {
  enabled: boolean;
  limit?: number | null;
  description?: string;
  credits_included?: number;
  [key: string]: any;
}

export interface FeatureAccessResponse {
  has_access: boolean;
  tier: string;
  config: FeatureConfig;
  reason: string;
  is_override?: boolean;
  is_promotional?: boolean;
  upgrade_info?: {
    feature: string;
    description: string;
    target_tier: string;
    tier_name: string;
    price: string;
    message: string;
    cta: string;
    upgrade_url: string;
  };
}

export interface TierInfo {
  tier: string;
  tier_name: string;
  features: Array<{
    feature: string;
    description: string;
    limit?: number | null;
  }>;
  limits: Record<string, number>;
}

export interface TierComparison {
  current_tier: string;
  tiers: Record<string, {
    name: string;
    price: string;
    price_monthly?: number;
    price_per_case?: number;
    description: string;
    features: Array<{
      feature: string;
      description: string;
      limit?: number | null;
    }>;
    popular?: boolean;
  }>;
}

/**
 * Check if user has access to a specific feature
 */
export function useFeatureAccess(feature: string) {
  const { user, isAuthenticated } = useAuth();

  return useQuery<FeatureAccessResponse>({
    queryKey: ['feature-access', feature, user?.id],
    queryFn: async () => {
      if (!isAuthenticated) {
        return {
          has_access: false,
          tier: 'free',
          config: { enabled: false },
          reason: 'Authentication required',
        };
      }

      const response = await fetch(`/api/v1/features/access/${feature}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to check feature access');
      }

      return response.json();
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });
}

/**
 * Get all feature access for current user
 */
export function useAllFeatureAccess() {
  const { user, isAuthenticated } = useAuth();

  return useQuery<Record<string, FeatureAccessResponse>>({
    queryKey: ['feature-access-all', user?.id],
    queryFn: async () => {
      if (!isAuthenticated) {
        return {};
      }

      const response = await fetch('/api/v1/features/access', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get feature access');
      }

      return response.json();
    },
    enabled: !!user,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get user's current tier information
 */
export function useUserTier() {
  const { user, isAuthenticated } = useAuth();

  return useQuery<TierInfo>({
    queryKey: ['user-tier', user?.id],
    queryFn: async () => {
      const response = await fetch('/api/v1/features/tier', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get user tier');
      }

      return response.json();
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Get tier comparison for upgrade decisions
 */
export function useTierComparison() {
  const { user, isAuthenticated } = useAuth();

  return useQuery<TierComparison>({
    queryKey: ['tier-comparison', user?.id],
    queryFn: async () => {
      const response = await fetch('/api/v1/features/tiers/compare', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get tier comparison');
      }

      return response.json();
    },
    enabled: isAuthenticated,
    staleTime: 10 * 60 * 1000, // Cache for 10 minutes
  });
}

/**
 * Track feature usage
 */
export async function trackFeatureUsage(feature: string, quantity: number = 1) {
  const response = await fetch(`/api/v1/features/usage/${feature}/track`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ quantity }),
  });

  if (!response.ok) {
    throw new Error('Failed to track feature usage');
  }

  return response.json();
}

/**
 * Get feature usage statistics
 */
export function useFeatureUsage(feature: string) {
  const { user, isAuthenticated } = useAuth();

  return useQuery({
    queryKey: ['feature-usage', feature, user?.id],
    queryFn: async () => {
      const response = await fetch(`/api/v1/features/usage/${feature}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get feature usage');
      }

      return response.json();
    },
    enabled: isAuthenticated && !!feature,
    staleTime: 60 * 1000, // Cache for 1 minute
  });
}
