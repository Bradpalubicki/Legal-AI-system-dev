'use client';

import { useState, useEffect, useCallback } from 'react';
import { API_CONFIG } from '@/config/api';

export interface UserPreferences {
  show_new_filing_notifications: boolean;
  email_notifications: boolean;
  case_alerts: boolean;
  document_alerts: boolean;
  auto_download_enabled: boolean;
  auto_download_free_only: boolean;
}

const DEFAULT_PREFERENCES: UserPreferences = {
  show_new_filing_notifications: true,
  email_notifications: true,
  case_alerts: true,
  document_alerts: true,
  auto_download_enabled: false,
  auto_download_free_only: true
};

// Helper to get auth headers
const getAuthHeaders = (): HeadersInit => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('accessToken');
    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
    }
  }
  return { 'Content-Type': 'application/json' };
};

export function useUserPreferences() {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Fetch preferences from backend
  const fetchPreferences = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/auth/me/preferences`, {
        method: 'GET',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Not authenticated - use defaults
          setPreferences(DEFAULT_PREFERENCES);
          return DEFAULT_PREFERENCES;
        }
        throw new Error('Failed to fetch preferences');
      }

      const data = await response.json();
      setPreferences(data);
      return data;
    } catch (err) {
      console.error('Error fetching preferences:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch preferences');
      // Return defaults on error
      return DEFAULT_PREFERENCES;
    } finally {
      setLoading(false);
    }
  }, []);

  // Update a single preference
  const updatePreference = useCallback(async <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ): Promise<boolean> => {
    try {
      setSaving(true);
      setError(null);

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/auth/me/preferences`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ [key]: value })
      });

      if (!response.ok) {
        throw new Error('Failed to update preference');
      }

      const updatedPrefs = await response.json();
      setPreferences(updatedPrefs);
      return true;
    } catch (err) {
      console.error('Error updating preference:', err);
      setError(err instanceof Error ? err.message : 'Failed to update preference');
      return false;
    } finally {
      setSaving(false);
    }
  }, []);

  // Update multiple preferences at once
  const updatePreferences = useCallback(async (
    updates: Partial<UserPreferences>
  ): Promise<boolean> => {
    try {
      setSaving(true);
      setError(null);

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/auth/me/preferences`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        throw new Error('Failed to update preferences');
      }

      const updatedPrefs = await response.json();
      setPreferences(updatedPrefs);
      return true;
    } catch (err) {
      console.error('Error updating preferences:', err);
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
      return false;
    } finally {
      setSaving(false);
    }
  }, []);

  // Load preferences on mount
  useEffect(() => {
    fetchPreferences();
  }, [fetchPreferences]);

  return {
    preferences,
    loading,
    error,
    saving,
    fetchPreferences,
    updatePreference,
    updatePreferences
  };
}

// Separate hook to fetch new filings since last login
export function useNewFilingsSinceLogin() {
  const [filings, setFilings] = useState<any[]>([]);
  const [totalDocuments, setTotalDocuments] = useState(0);
  const [since, setSince] = useState<string | null>(null);
  const [hasNewFilings, setHasNewFilings] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNewFilings = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/monitor/new-since-login`, {
        method: 'GET',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Not authenticated
          return { hasNewFilings: false, cases: [], totalDocuments: 0, since: null };
        }
        throw new Error('Failed to fetch new filings');
      }

      const data = await response.json();
      setFilings(data.cases || []);
      setTotalDocuments(data.total_new_documents || 0);
      setSince(data.since);
      setHasNewFilings(data.has_new_filings || false);

      return data;
    } catch (err) {
      console.error('Error fetching new filings:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch new filings');
      return { hasNewFilings: false, cases: [], totalDocuments: 0, since: null };
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    filings,
    totalDocuments,
    since,
    hasNewFilings,
    loading,
    error,
    fetchNewFilings
  };
}

export default useUserPreferences;
