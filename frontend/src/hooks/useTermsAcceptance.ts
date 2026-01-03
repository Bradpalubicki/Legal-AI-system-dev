'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { 
  UseTermsAcceptanceReturn, 
  LegalDocument, 
  ComplianceStatus,
  AcceptanceMethod 
} from '@/types/legal-compliance';
import { 
  buildApiUrl, 
  getErrorMessage, 
  logComplianceEvent, 
  logComplianceError,
  setComplianceCache,
  getComplianceCache
} from '@/utils/compliance-utils';
import axios from 'axios';

export const useTermsAcceptance = () => {
  const [documents, setDocuments] = useState<LegalDocument[]>([]);
  const [acceptanceStatus, setAcceptanceStatus] = useState<Map<string, boolean>>(new Map());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Check cache first
      const cached = getComplianceCache('legal_documents');
      if (cached) {
        setDocuments(cached.documents);
        setAcceptanceStatus(new Map(cached.acceptanceStatus));
        setIsLoading(false);
        return;
      }

      logComplianceEvent('Loading legal documents');
      
      const response = await axios.get(buildApiUrl('/api/compliance/documents'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      if (response.data.success) {
        const { documents: docs, acceptanceStatus: status } = response.data.data;
        setDocuments(docs || []);
        setAcceptanceStatus(new Map(Object.entries(status || {})));
        
        // Cache the results
        setComplianceCache('legal_documents', {
          documents: docs,
          acceptanceStatus: Object.entries(status || {})
        });
        
        logComplianceEvent('Legal documents loaded', { count: docs?.length || 0 });
      } else {
        throw new Error(response.data.error || 'Failed to load documents');
      }
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('Failed to load documents', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const acceptTerms = useCallback(async (documentIds: string[]) => {
    try {
      logComplianceEvent('Accepting terms', { documentIds });
      
      const response = await axios.post(
        buildApiUrl('/api/compliance/terms/accept'),
        { 
          documentIds,
          acceptanceMethod: AcceptanceMethod.CLICK_THROUGH,
          ipAddress: '', // Will be filled by server
          userAgent: navigator.userAgent
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          }
        }
      );

      if (response.data.success) {
        // Update local acceptance status
        const newStatus = new Map(acceptanceStatus);
        documentIds.forEach(id => newStatus.set(id, true));
        setAcceptanceStatus(newStatus);
        
        // Update cache
        const cacheData = {
          documents,
          acceptanceStatus: Array.from(newStatus.entries())
        };
        setComplianceCache('legal_documents', cacheData);
        
        logComplianceEvent('Terms accepted successfully', { documentIds });
      } else {
        throw new Error(response.data.error || 'Failed to accept terms');
      }
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('Failed to accept terms', err);
      throw err; // Re-throw so component can handle it
    }
  }, [acceptanceStatus, documents]);

  const checkAcceptanceStatus = useCallback((documentId: string): boolean => {
    return acceptanceStatus.get(documentId) || false;
  }, [acceptanceStatus]);

  const forceAcceptanceCheck = useCallback(async (): Promise<ComplianceStatus> => {
    try {
      logComplianceEvent('Performing forced acceptance check');
      
      const response = await axios.get(buildApiUrl('/api/compliance/force-check'), {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      if (response.data.success) {
        const complianceStatus = response.data.data;
        logComplianceEvent('Forced acceptance check completed', complianceStatus);
        return complianceStatus;
      } else {
        throw new Error(response.data.error || 'Failed to check compliance');
      }
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('Failed to perform forced acceptance check', err);
      throw err;
    }
  }, []);

  // Computed values
  const requiredDocuments = useMemo(() => 
    documents.filter(doc => doc.requiresAcceptance), 
    [documents]
  );

  const hasAcceptedAllRequired = useMemo(() =>
    requiredDocuments.every(doc => checkAcceptanceStatus(doc.id)),
    [requiredDocuments, checkAcceptanceStatus]
  );

  const pendingDocuments = useMemo(() =>
    requiredDocuments.filter(doc => !checkAcceptanceStatus(doc.id)),
    [requiredDocuments, checkAcceptanceStatus]
  );

  // Load documents on mount
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      loadDocuments();
    }
  }, [loadDocuments]);

  return {
    documents,
    acceptTerms,
    checkAcceptanceStatus,
    forceAcceptanceCheck,
    isLoading,
    error,
    // Additional computed properties
    requiredDocuments,
    hasAcceptedAllRequired,
    pendingDocuments,
    acceptanceStatus: acceptanceStatus
  } as UseTermsAcceptanceReturn & {
    requiredDocuments: LegalDocument[];
    hasAcceptedAllRequired: boolean;
    pendingDocuments: LegalDocument[];
    acceptanceStatus: Map<string, boolean>;
  };
};