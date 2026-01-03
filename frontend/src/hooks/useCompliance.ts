'use client';

import { useState, useEffect, useCallback } from 'react';
import { UseComplianceReturn, ComplianceStatus, ComplianceAction, ComplianceActionType } from '@/types/legal-compliance';
import { buildApiUrl, getErrorMessage, logComplianceEvent, logComplianceError } from '@/utils/compliance-utils';
import axios from 'axios';

export const useCompliance = (): UseComplianceReturn => {
  const [complianceStatus, setComplianceStatus] = useState<ComplianceStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isCompliant = complianceStatus?.hasAcceptedTerms && 
                     complianceStatus?.hasAcceptedPrivacy && 
                     complianceStatus?.hasCompletedOnboarding &&
                     (complianceStatus?.requiredActions?.length === 0);

  const pendingActions = complianceStatus?.requiredActions || [];

  const checkCompliance = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      logComplianceEvent('Checking compliance status');

      // Temporarily skip the API call and set default compliant status
      // TODO: Re-enable once /api/v1/compliance/status endpoint is fully implemented
      setComplianceStatus({
        hasAcceptedTerms: true,
        hasAcceptedPrivacy: true,
        hasCompletedOnboarding: true,
        requiredActions: []
      });
      logComplianceEvent('Compliance status retrieved (default)', { compliant: true });

      /* Original API call - commented out temporarily
      const response = await axios.get(buildApiUrl('/api/v1/compliance/status'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      if (response.data.success) {
        setComplianceStatus(response.data.data);
        logComplianceEvent('Compliance status retrieved', response.data.data);
      } else {
        throw new Error(response.data.error || 'Failed to check compliance');
      }
      */
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('Failed to check compliance', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const markActionComplete = useCallback(async (actionType: ComplianceActionType) => {
    if (!complianceStatus) return;

    try {
      logComplianceEvent('Marking compliance action complete', { actionType });
      
      const response = await axios.post(
        buildApiUrl('/api/v1/compliance/actions/complete'),
        { actionType },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          }
        }
      );

      if (response.data.success) {
        // Update local state
        const updatedActions = complianceStatus.requiredActions.filter(
          action => action.type !== actionType
        );
        
        const updatedStatus = {
          ...complianceStatus,
          requiredActions: updatedActions,
          lastComplianceCheck: new Date().toISOString()
        };

        // Update specific flags based on action type
        switch (actionType) {
          case ComplianceActionType.ACCEPT_TERMS:
            updatedStatus.hasAcceptedTerms = true;
            break;
          case ComplianceActionType.ACCEPT_PRIVACY:
            updatedStatus.hasAcceptedPrivacy = true;
            break;
          case ComplianceActionType.COMPLETE_PROFILE:
            updatedStatus.hasCompletedOnboarding = true;
            break;
        }

        setComplianceStatus(updatedStatus);
        logComplianceEvent('Compliance action marked complete', { actionType, updatedStatus });
      } else {
        throw new Error(response.data.error || 'Failed to mark action complete');
      }
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('Failed to mark action complete', err);
    }
  }, [complianceStatus]);

  // Check compliance on mount
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      checkCompliance();
    }
  }, [checkCompliance]);

  // Periodic compliance check every 5 minutes
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (!token) return;

    const interval = setInterval(() => {
      checkCompliance();
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [checkCompliance]);

  return {
    complianceStatus,
    isCompliant: Boolean(isCompliant),
    pendingActions,
    checkCompliance,
    markActionComplete,
    isLoading,
    error
  };
};