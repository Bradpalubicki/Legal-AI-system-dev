'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { UseDisclaimersReturn, DisclaimerConfig, UserRole } from '@/types/legal-compliance';
import { 
  buildApiUrl, 
  getErrorMessage, 
  logComplianceEvent, 
  logComplianceError,
  getDisclaimersForRole,
  getDisclaimersForContext,
  sortDisclaimersByPriority,
  setComplianceCache,
  getComplianceCache
} from '@/utils/compliance-utils';
import axios from 'axios';

export const useDisclaimers = (userRole?: UserRole) => {
  const [allDisclaimers, setAllDisclaimers] = useState<DisclaimerConfig[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filter disclaimers based on user role
  const disclaimers = useMemo(() => {
    let filtered = allDisclaimers;
    
    if (userRole) {
      filtered = getDisclaimersForRole(filtered, userRole);
    }
    
    return sortDisclaimersByPriority(filtered);
  }, [allDisclaimers, userRole]);

  const loadDisclaimers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Check cache first
      const cached = getComplianceCache('disclaimers');
      if (cached) {
        setAllDisclaimers(cached);
        setIsLoading(false);
        return;
      }

      logComplianceEvent('Loading disclaimers');
      
      const response = await axios.get(buildApiUrl('/api/compliance/disclaimers'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      if (response.data.success) {
        const disclaimerData = response.data.data || [];
        setAllDisclaimers(disclaimerData);
        setComplianceCache('disclaimers', disclaimerData);
        logComplianceEvent('Disclaimers loaded', { count: disclaimerData.length });
      } else {
        throw new Error(response.data.error || 'Failed to load disclaimers');
      }
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('Failed to load disclaimers', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const acknowledgeDisclaimer = useCallback(async (disclaimerId: string, context?: string) => {
    try {
      logComplianceEvent('Acknowledging disclaimer', { disclaimerId, context });
      
      const response = await axios.post(
        buildApiUrl('/api/compliance/disclaimers/acknowledge'),
        { disclaimerId, context },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          }
        }
      );

      if (response.data.success) {
        // Update local state to mark disclaimer as acknowledged
        setAllDisclaimers(prev => prev.map(disclaimer => 
          disclaimer.id === disclaimerId 
            ? { ...disclaimer, isAcknowledged: true }
            : disclaimer
        ));
        
        logComplianceEvent('Disclaimer acknowledged successfully', { disclaimerId });
      } else {
        throw new Error(response.data.error || 'Failed to acknowledge disclaimer');
      }
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('Failed to acknowledge disclaimer', err);
      throw err; // Re-throw so component can handle it
    }
  }, []);

  const getDisclaimersForContext = useCallback((context: string): DisclaimerConfig[] => {
    return getDisclaimersForContext(disclaimers, context);
  }, [disclaimers]);

  // Load disclaimers on mount
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      loadDisclaimers();
    }
  }, [loadDisclaimers]);

  return {
    disclaimers,
    acknowledgeDisclaimer,
    getDisclaimersForContext,
    isLoading,
    error
  };
};