'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

import { API_CONFIG } from '../config/api';

// Helper to get auth token
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('accessToken');
  }
  return null;
};

// Helper to get auth headers
const getAuthHeaders = (): HeadersInit => {
  const token = getAuthToken();
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

interface DocumentData {
  id: string;
  fileName: string;
  fileType: string;
  uploadDate: Date;
  text: string;
  summary?: string;
  parties?: string[];
  importantDates?: Array<{ date: string; description: string }>;
  keyFigures?: Array<{ label: string; value: string }>;
  keywords?: string[];
  analysis?: any;
}

interface DocumentContextType {
  documents: DocumentData[];
  currentDocument: DocumentData | null;
  sessionId: string;
  addDocument: (doc: DocumentData) => void;
  setCurrentDocument: (doc: DocumentData | null) => void;
  removeDocument: (id: string) => Promise<void>;
  clearDocuments: () => void;
  isLoading: boolean;
  error: string | null;
  retryLoad: () => void;
}

const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

// Get or create session ID
function getSessionId(): string {
  if (typeof window === 'undefined') return '';

  let sessionId = localStorage.getItem('legalai_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('legalai_session_id', sessionId);
    console.log('Created new session ID:', sessionId);
  } else {
    console.log('Loaded existing session ID:', sessionId);
  }
  return sessionId;
}

export function DocumentProvider({ children }: { children: ReactNode }) {
  const [documents, setDocuments] = useState<DocumentData[]>([]);
  const [currentDocument, setCurrentDocument] = useState<DocumentData | null>(null);
  const [sessionId, setSessionId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Function to load documents - extracted for retry capability
  const loadDocuments = async (sid: string) => {
    setIsLoading(true);
    setError(null);

    try {
      console.log('Fetching documents for session:', sid);
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/session/${sid}`, {
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to load documents: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      console.log('Loaded documents from backend:', data.document_count);

      // Normalize functions will be applied below
      return data;
    } catch (err: any) {
      console.error('Error loading saved documents:', err);
      setError(err.message || 'Failed to load documents. Please try again.');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  // Retry function that can be called from components
  const retryLoad = async () => {
    if (sessionId) {
      const data = await loadDocuments(sessionId);
      if (data) {
        processLoadedData(data);
      }
    }
  };

  // Normalization helper functions
  const normalizeKeyFigures = (keyFigures: any, analysis?: any) => {
    let figures = keyFigures;
    if ((!figures || (Array.isArray(figures) && figures.length === 0)) && analysis) {
      figures = analysis.all_financial_amounts ||
               analysis.financial_amounts ||
               analysis.key_figures ||
               keyFigures;
    }

    if (!figures) return [];
    if (!Array.isArray(figures)) return [];

    return figures.map((item: any) => {
      if (typeof item === 'string') {
        return { label: 'Amount', value: item };
      }
      if (typeof item === 'object') {
        return {
          label: item.description || item.label || 'Amount',
          value: item.amount || item.value || '',
          disputed: item.disputed || false,
          dispute_reason: item.dispute_reason || ''
        };
      }
      return { label: 'Amount', value: String(item) };
    });
  };

  const normalizeDates = (dates: any, analysis?: any) => {
    let datesList = dates;
    if ((!datesList || (Array.isArray(datesList) && datesList.length === 0)) && analysis) {
      datesList = analysis.all_dates || analysis.key_dates || dates;
    }

    if (!datesList) return [];
    if (!Array.isArray(datesList)) return [];

    return datesList.map((d: any) => {
      if (typeof d === 'string') {
        return { date: d, description: '' };
      }
      return {
        date: d.date || d,
        description: d.event || d.description || '',
        why_important: d.why_important || d.significance || '',
        action_required: d.action_required || '',
        consequence: d.consequence_if_missed || d.consequence || '',
        urgency: d.urgency || 'normal'
      };
    });
  };

  const normalizeParties = (parties: any, analysis?: any) => {
    let partiesList = parties;
    if ((!partiesList || (Array.isArray(partiesList) && partiesList.length === 0)) && analysis) {
      partiesList = analysis.all_parties || analysis.parties || parties;
    }

    if (!partiesList) return [];
    if (!Array.isArray(partiesList)) return [];
    return partiesList;
  };

  // Process loaded data (normalization logic)
  const processLoadedData = (data: any) => {
    if (!data || !data.documents) {
      console.log('No documents to process');
      return;
    }

    console.log('[DocumentContext] ========== LOADING DOCUMENTS FROM BACKEND ==========');
    console.log('[DocumentContext] Raw documents from API:', data.documents.length);
    data.documents.forEach((doc: any, idx: number) => {
      console.log(`[DocumentContext] Doc ${idx} raw keyFigures:`, doc.keyFigures);
      console.log(`[DocumentContext] Doc ${idx} analysis.all_financial_amounts:`, doc.analysis?.all_financial_amounts);
    });

    const loadedDocs = data.documents.map((doc: any) => {
      const analysis = doc.analysis || {};
      return {
        ...doc,
        uploadDate: new Date(doc.uploadDate),
        keyFigures: normalizeKeyFigures(doc.keyFigures, analysis),
        parties: normalizeParties(doc.parties, analysis),
        importantDates: normalizeDates(doc.importantDates, analysis),
        keywords: Array.isArray(doc.keywords) ? doc.keywords : (analysis.key_terms || []),
        summary: doc.summary || analysis.comprehensive_summary || analysis.summary || '',
        coreDispute: doc.coreDispute || analysis.core_dispute || '',
        plainEnglishSummary: doc.plainEnglishSummary || analysis.plain_english_summary || '',
        documentType: doc.documentType || analysis.document_type || '',
        caseNumber: doc.caseNumber || analysis.case_number || '',
        court: doc.court || analysis.court || '',
        filingDate: doc.filingDate || analysis.filing_date || '',
        deadlines: doc.deadlines || analysis.all_deadlines || analysis.deadlines || [],
        keyArguments: doc.keyArguments || analysis.key_arguments || [],
        reliefRequested: doc.reliefRequested || analysis.relief_requested || [],
        citedAuthority: doc.citedAuthority || analysis.cited_authority || [],
        hearingInfo: doc.hearingInfo || analysis.hearing_info || null
      };
    });

    console.log('[DocumentContext] ========== AFTER NORMALIZATION ==========');
    loadedDocs.forEach((doc: any, idx: number) => {
      console.log(`[DocumentContext] Doc ${idx} normalized keyFigures:`, doc.keyFigures);
    });

    setDocuments(loadedDocs);
    if (loadedDocs.length > 0) {
      setCurrentDocument(loadedDocs[0]);
    }
  };

  // Initialize session and load documents on mount
  useEffect(() => {
    const initSession = async () => {
      const sid = getSessionId();
      setSessionId(sid);

      if (sid) {
        const data = await loadDocuments(sid);
        if (data) {
          processLoadedData(data);
        }
      } else {
        setIsLoading(false);
      }
    };

    initSession();
  }, []);

  const addDocument = (doc: DocumentData) => {
    setDocuments(prev => [...prev, doc]);
    setCurrentDocument(doc); // Auto-select newly uploaded document
  };

  const removeDocument = async (id: string) => {
    try {
      // Call backend DELETE endpoint to permanently remove document
      console.log('Deleting document from backend:', id);
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/document/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete document from backend');
      }

      console.log('Document deleted from backend successfully');

      // Update local state only if backend deletion succeeds
      setDocuments(prev => prev.filter(doc => doc.id !== id));
      if (currentDocument?.id === id) {
        setCurrentDocument(null);
      }
    } catch (error) {
      console.error('Error deleting document:', error);
      // Re-throw error so UI can handle it
      throw error;
    }
  };

  const clearDocuments = () => {
    setDocuments([]);
    setCurrentDocument(null);
  };

  return (
    <DocumentContext.Provider
      value={{
        documents,
        currentDocument,
        sessionId,
        addDocument,
        setCurrentDocument,
        removeDocument,
        clearDocuments,
        isLoading,
        error,
        retryLoad,
      }}
    >
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocuments() {
  const context = useContext(DocumentContext);
  if (context === undefined) {
    throw new Error('useDocuments must be used within a DocumentProvider');
  }
  return context;
}
