'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { useDocuments } from '@/contexts/DocumentContext';
import { useAuth } from '@/hooks/useAuth';
import { API_CONFIG } from '../../config/api';
import { toast } from 'sonner';
import { UpgradePrompt } from '@/components/UpgradePrompt';
import { DocumentHeaderCompact } from '@/components/DocumentHeader';
import {
  Search,
  FileText,
  DollarSign,
  Settings,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Lock,
  TrendingUp,
  Eye,
  EyeOff,
  Download,
  Info,
  HelpCircle,
  ExternalLink,
  Bell,
  BellOff,
  RefreshCw,
  Trash2,
  Clock,
  CreditCard,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Scale,
  Users,
  Calendar,
  Tag
} from 'lucide-react';

/**
 * Safely ensure a value is an array.
 * Fixes character-by-character rendering bug when key_arguments comes as string.
 */
const ensureArray = <T,>(value: T | T[] | string | undefined | null): T[] => {
  if (!value) return [];
  if (Array.isArray(value)) return value;
  if (typeof value === 'string') {
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) return parsed;
      return [parsed as T];
    } catch {
      if (value.length > 10) return [value as unknown as T];
      return [];
    }
  }
  return [];
};

/**
 * Safely normalize key arguments from analysis data.
 */
const normalizeKeyArguments = (keyArguments: any): Array<{ argument: string; supporting_evidence?: string }> => {
  const arr = ensureArray(keyArguments);
  return arr.map((arg: any) => {
    if (typeof arg === 'string') {
      return { argument: arg, supporting_evidence: '' };
    }
    if (typeof arg === 'object' && arg !== null) {
      return {
        argument: arg.argument || arg.description || String(arg),
        supporting_evidence: arg.supporting_evidence || arg.supporting_facts || ''
      };
    }
    return { argument: String(arg), supporting_evidence: '' };
  });
};

interface PACERCredentialsStatus {
  has_credentials: boolean;
  is_verified: boolean;
  username: string | null;
  environment: string | null;
}

interface PACERStats {
  credentials: {
    username: string;
    environment: string;
    is_verified: boolean;
    last_used: string | null;
  };
  usage: {
    total_searches: number;
    total_downloads: number;
    total_cost: number;
  };
  limits: {
    daily_limit: number;
    monthly_limit: number;
    daily_spending: number;
    monthly_spending: number;
    daily_remaining: number;
    monthly_remaining: number;
  };
  recent_searches: Array<{
    id: number;
    type: string;
    criteria: any;
    results_count: number;
    court: string;
    timestamp: string;
  }>;
}

export default function PACERPage() {
  const router = useRouter();
  const { addDocument, documents, currentDocument, setCurrentDocument } = useDocuments();
  const { isAuthenticated, user } = useAuth();

  const [credentialsStatus, setCredentialsStatus] = useState<PACERCredentialsStatus | null>(null);
  const [stats, setStats] = useState<PACERStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Credentials form
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [clientCode, setClientCode] = useState('');
  const [environment, setEnvironment] = useState('production');
  const [dailyLimit, setDailyLimit] = useState('100');
  const [monthlyLimit, setMonthlyLimit] = useState('1000');
  const [saving, setSaving] = useState(false);
  const [clearing, setClearing] = useState(false);

  // Search form
  const [searchSource, setSearchSource] = useState<'pacer' | 'courtlistener'>('courtlistener');
  const [searchType, setSearchType] = useState<'case' | 'party'>('party');
  const [caseNumber, setCaseNumber] = useState('');
  const [caseTitle, setCaseTitle] = useState('');
  const [courtType, setCourtType] = useState<'bankruptcy' | 'district' | 'circuit'>('bankruptcy');
  const [court, setCourt] = useState('');
  const [partyName, setPartyName] = useState('');
  const [filedAfter, setFiledAfter] = useState('');
  const [filedBefore, setFiledBefore] = useState('');
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any>(null);

  // CourtListener monitoring
  const [monitoredCases, setMonitoredCases] = useState<Set<number>>(new Set());
  const [monitoredCasesList, setMonitoredCasesList] = useState<any[]>([]);
  const [hasUpdates, setHasUpdates] = useState(false);
  const [updateCount, setUpdateCount] = useState(0);
  const [loadingMonitored, setLoadingMonitored] = useState(false);
  const [refreshingUpdates, setRefreshingUpdates] = useState(false);

  // Direct docket ID lookup (for blocked cases)
  const [docketId, setDocketId] = useState('');

  // Document download to app storage
  const [downloadingDocs, setDownloadingDocs] = useState<Set<number>>(new Set());
  const [downloadedDocs, setDownloadedDocs] = useState<any[]>([]);

  // Track which documents have been analyzed (by document_id)
  const [analyzedDocIds, setAnalyzedDocIds] = useState<Set<string>>(new Set());
  // Track documents currently being analyzed
  const [analyzingDocs, setAnalyzingDocs] = useState<Set<string>>(new Set());

  // Track which results have loaded all documents
  const [loadedAllDocs, setLoadedAllDocs] = useState<Set<number>>(new Set());
  const [loadingAllDocs, setLoadingAllDocs] = useState<Set<number>>(new Set());

  // Document purchase with credits
  const [purchasingDocs, setPurchasingDocs] = useState<Set<number>>(new Set());
  const [userCredits, setUserCredits] = useState<number | null>(null);

  // Document sorting
  const [documentSortOrder, setDocumentSortOrder] = useState<'newest' | 'oldest'>('newest');

  // Upgrade prompt state
  const [showUpgradePrompt, setShowUpgradePrompt] = useState(false);
  const [upgradeInfo, setUpgradeInfo] = useState<any>(null);
  const [upgradeFeature, setUpgradeFeature] = useState<string>('');

  // Stop monitoring confirmation dialog
  const [confirmStopDialog, setConfirmStopDialog] = useState<{
    open: boolean;
    docketId: number | null;
    caseName: string;
  }>({ open: false, docketId: null, caseName: '' });

  // Start monitoring confirmation dialog with explanation
  const [confirmStartDialog, setConfirmStartDialog] = useState<{
    open: boolean;
    docketId: number | null;
    caseName: string;
    caseData: any;
  }>({ open: false, docketId: null, caseName: '', caseData: null });

  // Comprehensive court lists
  const bankruptcyCourts = {
    'Alabama': ['alnb', 'almb', 'alsb'],
    'Alaska': ['akb'],
    'Arizona': ['azb'],
    'Arkansas': ['areb', 'arwb'],
    'California': ['canb', 'caeb', 'cacb', 'casb'],
    'Colorado': ['cob'],
    'Connecticut': ['ctb'],
    'Delaware': ['deb'],
    'District of Columbia': ['dcb'],
    'Florida': ['flnb', 'flmb', 'flsb'],
    'Georgia': ['ganb', 'gamb', 'gasb'],
    'Hawaii': ['hib'],
    'Idaho': ['idb'],
    'Illinois': ['ilnb', 'ilcb', 'ilsb'],
    'Indiana': ['innb', 'insb'],
    'Iowa': ['ianb', 'iasb'],
    'Kansas': ['ksb'],
    'Kentucky': ['kyeb', 'kywb'],
    'Louisiana': ['laeb', 'lamb', 'lawb'],
    'Maine': ['meb'],
    'Maryland': ['mdb'],
    'Massachusetts': ['mab'],
    'Michigan': ['mieb', 'miwb'],
    'Minnesota': ['mnb'],
    'Mississippi': ['msnb', 'mssb'],
    'Missouri': ['moeb', 'mowb'],
    'Montana': ['mtb'],
    'Nebraska': ['neb'],
    'Nevada': ['nvb'],
    'New Hampshire': ['nhb'],
    'New Jersey': ['njb'],
    'New Mexico': ['nmb'],
    'New York': ['nynb', 'nyeb', 'nysb', 'nywb'],
    'North Carolina': ['nceb', 'ncmb', 'ncwb'],
    'North Dakota': ['ndb'],
    'Ohio': ['ohnb', 'ohsb'],
    'Oklahoma': ['oknb', 'okeb', 'okwb'],
    'Oregon': ['orb'],
    'Pennsylvania': ['paeb', 'pamb', 'pawb'],
    'Puerto Rico': ['prb'],
    'Rhode Island': ['rib'],
    'South Carolina': ['scb'],
    'South Dakota': ['sdb'],
    'Tennessee': ['tneb', 'tnmb', 'tnwb'],
    'Texas': ['txnb', 'txeb', 'txsb', 'txwb'],
    'Utah': ['utb'],
    'Vermont': ['vtb'],
    'Virginia': ['vaeb', 'vawb'],
    'Virgin Islands': ['vib'],
    'Washington': ['waeb', 'wawb'],
    'West Virginia': ['wvnb', 'wvsb'],
    'Wisconsin': ['wieb', 'wiwb'],
    'Wyoming': ['wyb']
  };

  const districtCourts = {
    'Alabama': ['alnd', 'almd', 'alsd'],
    'Alaska': ['akd'],
    'Arizona': ['azd'],
    'Arkansas': ['ared', 'arwd'],
    'California': ['cand', 'caed', 'cacd', 'casd'],
    'Colorado': ['cod'],
    'Connecticut': ['ctd'],
    'Delaware': ['ded'],
    'District of Columbia': ['dcd'],
    'Florida': ['flnd', 'flmd', 'flsd'],
    'Georgia': ['gand', 'gamd', 'gasd'],
    'Hawaii': ['hid'],
    'Idaho': ['idd'],
    'Illinois': ['ilnd', 'ilcd', 'ilsd'],
    'Indiana': ['innd', 'insd'],
    'Iowa': ['iand', 'iasd'],
    'Kansas': ['ksd'],
    'Kentucky': ['kyed', 'kywd'],
    'Louisiana': ['laed', 'lamd', 'lawd'],
    'Maine': ['med'],
    'Maryland': ['mdd'],
    'Massachusetts': ['mad'],
    'Michigan': ['mied', 'miwd'],
    'Minnesota': ['mnd'],
    'Mississippi': ['msnd', 'mssd'],
    'Missouri': ['moed', 'mowd'],
    'Montana': ['mtd'],
    'Nebraska': ['ned'],
    'Nevada': ['nvd'],
    'New Hampshire': ['nhd'],
    'New Jersey': ['njd'],
    'New Mexico': ['nmd'],
    'New York': ['nynd', 'nyed', 'nysd', 'nywd'],
    'North Carolina': ['nced', 'ncmd', 'ncwd'],
    'North Dakota': ['ndd'],
    'Ohio': ['ohnd', 'ohsd'],
    'Oklahoma': ['oknd', 'oked', 'okwd'],
    'Oregon': ['ord'],
    'Pennsylvania': ['paed', 'pamd', 'pawd'],
    'Puerto Rico': ['prd'],
    'Rhode Island': ['rid'],
    'South Carolina': ['scd'],
    'South Dakota': ['sdd'],
    'Tennessee': ['tned', 'tnmd', 'tnwd'],
    'Texas': ['txnd', 'txed', 'txsd', 'txwd'],
    'Utah': ['utd'],
    'Vermont': ['vtd'],
    'Virginia': ['vaed', 'vawd'],
    'Virgin Islands': ['vid'],
    'Washington': ['waed', 'wawd'],
    'West Virginia': ['wvnd', 'wvsd'],
    'Wisconsin': ['wied', 'wiwd'],
    'Wyoming': ['wyd']
  };

  const circuitCourts = [
    { code: 'ca1', name: '1st Circuit (ME, MA, NH, RI, PR)' },
    { code: 'ca2', name: '2nd Circuit (CT, NY, VT)' },
    { code: 'ca3', name: '3rd Circuit (DE, NJ, PA, VI)' },
    { code: 'ca4', name: '4th Circuit (MD, NC, SC, VA, WV)' },
    { code: 'ca5', name: '5th Circuit (LA, MS, TX)' },
    { code: 'ca6', name: '6th Circuit (KY, MI, OH, TN)' },
    { code: 'ca7', name: '7th Circuit (IL, IN, WI)' },
    { code: 'ca8', name: '8th Circuit (AR, IA, MN, MO, NE, ND, SD)' },
    { code: 'ca9', name: '9th Circuit (AK, AZ, CA, HI, ID, MT, NV, OR, WA)' },
    { code: 'ca10', name: '10th Circuit (CO, KS, NM, OK, UT, WY)' },
    { code: 'ca11', name: '11th Circuit (AL, FL, GA)' },
    { code: 'cadc', name: 'DC Circuit' },
    { code: 'cafc', name: 'Federal Circuit' }
  ];

  // Load user-specific data from localStorage when user changes
  useEffect(() => {
    if (typeof window !== 'undefined' && user?.id) {
      // Load user-specific search results
      const userSearchKey = `pacer_search_results_${user.id}`;
      const saved = localStorage.getItem(userSearchKey);
      if (saved) {
        try {
          setSearchResults(JSON.parse(saved));
        } catch (e) {
          console.error('Failed to parse saved search results:', e);
        }
      }

      // Load user-specific downloaded docs
      const userDocsKey = `pacer_downloaded_docs_${user.id}`;
      const savedDocs = localStorage.getItem(userDocsKey);
      if (savedDocs) {
        try {
          setDownloadedDocs(JSON.parse(savedDocs));
        } catch (e) {
          console.error('Failed to parse saved docs:', e);
        }
      }
    }
  }, [user?.id]);

  // Clear all PACER data when user logs out OR changes
  useEffect(() => {
    if (!user) {
      // Clear state when logged out
      setSearchResults(null);
      setDownloadedDocs([]);
      setMonitoredCasesList([]);
      setMonitoredCases(new Set());
      setLoadedAllDocs(new Set());
    }
  }, [user]);

  // Re-fetch user-specific data when user ID changes
  useEffect(() => {
    if (user?.id) {
      // Clear monitored cases state before fetching new user's data
      setMonitoredCasesList([]);
      setMonitoredCases(new Set());

      // Fetch monitored cases for the new user
      fetchMonitoredCases();
    }
  }, [user?.id]);

  useEffect(() => {
    if (isAuthenticated) {
      loadCredentialsStatus(); // Load PACER credentials only when authenticated
      fetchCreditsBalance(); // Load user credits balance only when authenticated
    } else {
      // When not authenticated, clear loading state and cached data
      setLoading(false);
      setCredentialsStatus(null);
      setSearchResults(null);
    }
  }, [isAuthenticated]);

  // Save search results to user-specific localStorage whenever they change
  useEffect(() => {
    if (searchResults && typeof window !== 'undefined' && user?.id) {
      const userSearchKey = `pacer_search_results_${user.id}`;
      localStorage.setItem(userSearchKey, JSON.stringify(searchResults));
    }
  }, [searchResults, user?.id]);

  // Save downloaded documents to user-specific localStorage whenever they change
  useEffect(() => {
    if (downloadedDocs.length > 0 && typeof window !== 'undefined' && user?.id) {
      const userDocsKey = `pacer_downloaded_docs_${user.id}`;
      localStorage.setItem(userDocsKey, JSON.stringify(downloadedDocs));
    }
  }, [downloadedDocs, user?.id]);

  // Initialize analyzed doc IDs from document context
  useEffect(() => {
    if (documents && documents.length > 0) {
      const analyzedIds = new Set<string>();
      documents.forEach((doc: any) => {
        // Track RECAP documents by their document_id
        if (doc.id?.startsWith('recap_')) {
          analyzedIds.add(doc.id);
        }
      });
      setAnalyzedDocIds(analyzedIds);
    }
  }, [documents]);

  // Helper: Check if a document has already been downloaded to app
  const isDocumentDownloaded = (docId: number): boolean => {
    return downloadedDocs.some(
      (downloaded) => downloaded.document_id === docId || downloaded.original_doc?.id === docId
    );
  };

  // Helper: Check if a document has already been analyzed
  const isDocumentAnalyzed = (docId: number | string): boolean => {
    const recapId = `recap_${docId}`;
    return analyzedDocIds.has(recapId) || documents?.some((doc: any) => doc.id === recapId);
  };

  const fetchCreditsBalance = async () => {
    try {
      if (!user?.id) {
        console.warn('Cannot fetch credits: user ID not available');
        return;
      }
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/credits/balance/${user.id}`);
      if (response.ok) {
        const data = await response.json();
        setUserCredits(data.balance);
      }
    } catch (error) {
      console.error('Error fetching credits balance:', error);
      // Don't set error state - this is non-critical
    }
  };

  const loadCredentialsStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/credentials/status`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setCredentialsStatus(data);

        // If has credentials, load stats
        if (data.has_credentials) {
          loadStats();
        }
      }
    } catch (err) {
      console.error('[PACER] Error loading credentials status:', err);
      setError('Failed to load PACER status');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/stats`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const handleSaveCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/credentials`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          pacer_username: username,
          pacer_password: password,
          client_code: clientCode || null,
          environment,
          daily_limit: parseFloat(dailyLimit),
          monthly_limit: parseFloat(monthlyLimit)
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('PACER credentials saved successfully!');
        setTimeout(() => {
          loadCredentialsStatus();
          setPassword(''); // Clear password
        }, 1500);
      } else {
        setError(data.detail || 'Failed to save credentials');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleAuthenticate = async () => {
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/authenticate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({})
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('Successfully authenticated with PACER!' + (data.test_mode ? ' (TEST MODE)' : ''));
        loadCredentialsStatus();
        loadStats();
      } else {
        const errorMsg = data.detail || `Authentication failed (${response.status})`;
        console.error('[PACER] Authentication error:', errorMsg);
        setError(errorMsg);
      }
    } catch (err: any) {
      console.error('[PACER] Network/parsing error:', err);
      setError(`Network error: ${err.message || 'Please try again'}`);
    }
  };

  const handleClearCredentials = async () => {
    if (!confirm('Are you sure you want to clear your PACER credentials? This action cannot be undone.')) {
      return;
    }

    setClearing(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/credentials`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        setSuccess('PACER credentials cleared successfully!');
        setUsername('');
        setPassword('');
        setClientCode('');
        setCredentialsStatus(null);
        setStats(null);
        setTimeout(() => {
          loadCredentialsStatus();
        }, 1500);
      } else {
        const data = await response.json();
        setError(data.detail || 'Failed to clear credentials');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setClearing(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setSearching(true);
    setError(null);
    setSearchResults(null);

    try {
      if (searchSource === 'pacer') {
        // PACER search (original logic)
        const endpoint = searchType === 'case'
          ? '/api/v1/pacer/search/cases'
          : '/api/v1/pacer/search/parties';

        const body = searchType === 'case'
          ? {
              case_number: caseNumber || undefined,
              case_title: caseTitle || undefined,
              court: court || undefined
            }
          : {
              party_name: partyName,
              court: court || undefined
            };

        const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(body)
        });

        const data = await response.json();

        if (response.ok) {
          setSearchResults(data);
          setSuccess(`Found ${data.total_count} results!`);
        } else {
          setError(data.detail || 'Search failed');
        }
      } else {
        // CourtListener search (FREE alternative)
        // Both case number and party name searches use the dockets endpoint
        const endpoint = '/api/v1/courtlistener/search/dockets';

        const body = searchType === 'case'
          ? {
              case_number: caseNumber || undefined,
              query: caseTitle || undefined,  // CourtListener uses 'query' not 'case_title'
              court_id: court || undefined,
              party_name: partyName || undefined,
              filed_after: filedAfter || undefined,
              filed_before: filedBefore || undefined
            }
          : {
              query: partyName,  // Party name search - still uses dockets endpoint
              court_id: court || undefined,
              filed_after: filedAfter || undefined,
              filed_before: filedBefore || undefined
            };

        const response = await fetch(`${API_CONFIG.BASE_URL}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(body)
        });

        const data = await response.json();

        if (response.ok) {
          // Filter results by court type if no specific court is selected
          let filteredResults = data.results || [];

          if (!court && courtType) {
            filteredResults = filteredResults.filter((result: any) => {
              const courtId = result.court_id || result.court || '';

              // Determine court type based on court ID pattern
              if (courtType === 'bankruptcy') {
                // Bankruptcy courts end with 'b' (e.g., 'alnb', 'canb', 'cacb')
                return courtId.endsWith('b');
              } else if (courtType === 'district') {
                // District courts end with 'd' (e.g., 'alnd', 'cand')
                return courtId.endsWith('d');
              } else if (courtType === 'circuit') {
                // Circuit courts: ca1-ca11, cadc, cafc
                // Must start with 'ca' but NOT end with 'b' or 'd' (to exclude cacb, canb, cand, etc.)
                return courtId.startsWith('ca') && !courtId.endsWith('b') && !courtId.endsWith('d');
              }
              return true;
            });
          }

          setSearchResults({
            ...data,
            results: filteredResults,
            count: filteredResults.length,
            total_count: filteredResults.length,
            source: 'courtlistener',
            filtered_by_type: !court && courtType ? courtType : null
          });
          setSuccess(`Found ${filteredResults.length} results! (FREE - CourtListener)`);
        } else {
          setError(data.detail || 'Search failed');
        }
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  // Direct docket ID lookup (for blocked cases that don't appear in search)
  const handleDirectDocketLookup = async () => {
    if (!docketId || !docketId.trim()) {
      setError('Please enter a docket ID');
      return;
    }

    setSearching(true);
    setError(null);
    setSearchResults(null);

    try {
      // Call the documents endpoint to get docket + all RECAP documents
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/docket/${docketId.trim()}/documents`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Add documents to the docket object so the UI can display them
        const docketWithDocs = {
          ...data.docket,
          recap_documents: data.documents || [],
          courtlistener_url: data.courtlistener_url,
          api_limitation: data.api_limitation
        };

        // Format the single docket as a search result
        setSearchResults({
          count: 1,
          total_count: 1,
          results: [docketWithDocs],
          source: 'courtlistener'
        });

        const docCount = data.documents?.length || 0;
        if (data.api_limitation) {
          setSuccess(`Found case: ${data.docket.case_name || 'Docket ' + docketId}`);
        } else {
          setSuccess(`Found case: ${data.docket.case_name || 'Docket ' + docketId} (${docCount} documents available)`);
        }
      } else {
        setError(data.detail || 'Docket not found');
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  // Monitor a CourtListener case for auto-updates
  const handleMonitorCase = async (docketId: number) => {
    try {
      const token = localStorage.getItem('accessToken');
      console.log('[Monitor] Starting to monitor docket:', docketId);
      console.log('[Monitor] Token present:', !!token);

      // Check for authentication before making request
      if (!token) {
        setError('Please log in to monitor cases. Your session may have expired.');
        return;
      }

      // Find case data from search results to bypass CourtListener API
      const caseData = searchResults?.results?.find((result: any) => {
        const resultDocketId = result.docket_id || result.id;
        return resultDocketId === docketId;
      });

      console.log('[Monitor] Found case data:', caseData);

      // Prepare request body with case metadata (allows monitoring without CourtListener API)
      const requestBody: any = { docket_id: docketId };
      if (caseData) {
        requestBody.case_name = caseData.case_name;
        requestBody.docket_number = caseData.docket_number || caseData.case_number;
        requestBody.court = caseData.court_name || caseData.court;
        requestBody.court_id = caseData.court_id || caseData.court;
        requestBody.date_filed = caseData.date_filed || caseData.filing_date;
        console.log('[Monitor] Including case metadata to bypass CourtListener API');
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/monitor/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        credentials: 'include',
        body: JSON.stringify(requestBody)
      });

      console.log('[Monitor] Response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('[Monitor] Success:', data);
        setMonitoredCases(prev => new Set(prev).add(docketId));
        setSuccess(`Started monitoring case ${docketId} for new documents`);
        // Refresh the monitored cases list
        await fetchMonitoredCases();
      } else if (response.status === 402) {
        // Payment required - show upgrade prompt
        const errorData = await response.json().catch(() => ({}));
        console.log('[Monitor] Payment required - upgrade needed:', errorData);
        setUpgradeFeature('case_monitoring');
        setUpgradeInfo(errorData.upgrade_info || {
          feature: 'case_monitoring',
          tier_name: 'Case Monitor',
          price: '$5/case or $19/month',
          message: 'Upgrade to monitor cases for new documents',
          description: 'Get automatic notifications when new documents are filed'
        });
        setShowUpgradePrompt(true);
      } else if (response.status === 401) {
        // Authentication failed - token expired or invalid
        console.log('[Monitor] Authentication failed - clearing tokens');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        setError('Your session has expired. Please log in again to monitor cases.');
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('[Monitor] Error:', errorData);
        setError(`Failed to start monitoring: ${errorData.detail || response.statusText}`);
      }
    } catch (err) {
      console.error('[Monitor] Exception:', err);
      setError('Failed to start monitoring');
    }
  };

  // Show confirmation dialog for start monitoring with explanation
  const openStartMonitoringConfirmation = (docketId: number, caseName?: string, caseData?: any) => {
    setConfirmStartDialog({
      open: true,
      docketId,
      caseName: caseName || `Case #${docketId}`,
      caseData
    });
  };

  // Actually start monitoring (called after user confirms)
  const confirmStartMonitoring = async () => {
    const docketId = confirmStartDialog.docketId;
    if (!docketId) return;

    // Close dialog and start monitoring
    setConfirmStartDialog({ open: false, docketId: null, caseName: '', caseData: null });
    await handleMonitorCase(docketId);
  };

  // Show confirmation dialog for stop monitoring
  const openStopMonitoringConfirmation = (docketId: number, caseName?: string) => {
    setConfirmStopDialog({
      open: true,
      docketId,
      caseName: caseName || `Case #${docketId}`
    });
  };

  // Actually stop monitoring a case (called after confirmation)
  const confirmStopMonitoring = async () => {
    const docketId = confirmStopDialog.docketId;
    if (!docketId) return;

    // Close the dialog first
    setConfirmStopDialog({ open: false, docketId: null, caseName: '' });

    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/monitor/stop/${docketId}`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setMonitoredCases(prev => {
          const newSet = new Set(prev);
          newSet.delete(docketId);
          return newSet;
        });
        setSuccess(`Stopped monitoring case`);
        // Refresh the list
        await fetchMonitoredCases();
      }
    } catch (err) {
      console.error('Failed to stop monitoring:', err);
      setError('Failed to stop monitoring');
    }
  };

  // Legacy function for backward compatibility - now shows confirmation
  const handleStopMonitoring = (docketId: number, caseName?: string) => {
    openStopMonitoringConfirmation(docketId, caseName);
  };

  // Auto-update polling for monitored cases
  useEffect(() => {
    if (monitoredCases.size === 0) return;

    const pollInterval = setInterval(async () => {
      try {
        const token = localStorage.getItem('accessToken');
        const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/monitor/updates`, {
          credentials: 'include',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.has_updates) {
            setHasUpdates(true);
            setUpdateCount(data.count);
          }
        }
      } catch (err) {
        console.error('Failed to check updates:', err);
      }
    }, 30000); // Poll every 30 seconds

    return () => clearInterval(pollInterval);
  }, [monitoredCases]);

  // Fetch monitored cases list
  const fetchMonitoredCases = async () => {
    setLoadingMonitored(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/monitor/list`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMonitoredCasesList(data.monitored_cases || []);
        // Update the monitored set
        const ids = new Set<number>(data.monitored_cases.map((c: any) => c.docket_id as number));
        setMonitoredCases(ids);
      }
    } catch (err) {
      console.error('Failed to fetch monitored cases:', err);
    } finally {
      setLoadingMonitored(false);
    }
  };

  // Check for updates manually
  const handleRefreshUpdates = async () => {
    setRefreshingUpdates(true);
    try {
      const token = localStorage.getItem('accessToken');
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/monitor/updates`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.has_updates) {
          setSuccess(`Found ${data.count} case(s) with new documents!`);
          setHasUpdates(true);
          setUpdateCount(data.count);
        } else {
          setSuccess('No new updates found');
        }
        // Refresh the monitored list
        await fetchMonitoredCases();
      }
    } catch (err) {
      setError('Failed to check for updates');
    } finally {
      setRefreshingUpdates(false);
    }
  };

  // Remove from monitoring (uses same confirmation dialog)
  const handleRemoveMonitoring = (docketId: number, caseName?: string) => {
    openStopMonitoringConfirmation(docketId, caseName);
  };

  // Download document directly to app storage
  // caseInfo parameter provides case-level context for PACER-standard naming
  const handleDownloadToApp = async (doc: any, caseInfo?: any) => {
    console.log('[DEBUG] handleDownloadToApp called with doc:', doc, 'caseInfo:', caseInfo);
    console.log('[DEBUG] doc.id:', doc.id, 'type:', typeof doc.id);

    if (!doc.id && doc.id !== 0) {
      console.error('[ERROR] Document ID is missing or invalid:', doc);
      setError('Document ID is missing. Please refresh and try again.');
      return;
    }

    // Ensure document_id is an integer
    const documentId = parseInt(String(doc.id), 10);
    if (isNaN(documentId)) {
      console.error('[ERROR] Document ID is not a valid number:', doc.id);
      setError('Invalid document ID. Please refresh and try again.');
      return;
    }

    // Prevent re-downloading if already downloaded
    if (isDocumentDownloaded(documentId)) {
      toast.info('Document Already Downloaded', {
        description: 'This document is already in your app. Go to the "Downloaded" tab to view it.',
        duration: 4000,
      });
      return;
    }

    try {
      // Add to downloading set
      setDownloadingDocs(prev => new Set(prev).add(documentId));
      setError(null);

      // Build request with PACER-standard naming metadata
      const requestBody = {
        document_id: documentId,
        // Document-level metadata
        document_number: doc.entry_number || doc.document_number || undefined,
        description: doc.short_description || doc.description || undefined,
        filing_date: doc.entry_date_filed || undefined,
        // Case-level metadata (from caseInfo if provided)
        case_number: caseInfo?.docketNumber || caseInfo?.caseNumber || caseInfo?.docket_number || undefined,
        court: caseInfo?.court_id || caseInfo?.court || undefined
      };
      console.log('[DEBUG] Request body with PACER metadata:', requestBody);

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/download-recap-to-app`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(requestBody)
      });

      console.log('[DEBUG] Response status:', response.status);
      const data = await response.json();
      console.log('[DEBUG] Response data:', data);

      if (response.ok && data.success) {
        setSuccess(`Downloaded: ${doc.short_description || 'Document'} (${(data.file_size / 1024).toFixed(1)} KB)`);

        // Add to downloaded docs list
        setDownloadedDocs(prev => [...prev, {
          ...data,
          original_doc: doc,
          downloaded_at: new Date().toISOString()
        }]);
      } else if (response.status === 402) {
        // Payment required - show upgrade prompt
        console.log('[Download] Payment required - upgrade needed:', data);
        setUpgradeFeature('document_download');
        setUpgradeInfo(data.upgrade_info || {
          feature: 'document_download',
          tier_name: 'Case Monitor',
          price: '$5/case or $19/month',
          message: 'Upgrade to download documents',
          description: 'Download free documents and purchase PACER documents'
        });
        setShowUpgradePrompt(true);
      } else {
        console.error('[ERROR] Download failed:', data);
        const errorMsg = data.detail || data.error || 'Failed to download document';

        // Special handling for access restricted errors
        if (errorMsg.includes('ACCESS_RESTRICTED') || errorMsg.includes('Access forbidden') || errorMsg.includes('permission')) {
          setError(
            `Unable to download automatically. Click "View Online" to access the document on CourtListener's website, ` +
            `then manually download if needed.`
          );
        } else {
          setError(`Download failed: ${errorMsg}`);
        }
      }
    } catch (err: any) {
      console.error('[ERROR] Exception during download:', err);
      setError(`Network error while downloading document: ${err.message || 'Unknown error'}`);
    } finally {
      // Remove from downloading set
      setDownloadingDocs(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
    }
  };

  // Purchase PACER document with credits
  const handlePurchaseWithCredits = async (doc: any, docket: any) => {
    console.log('[DEBUG] handlePurchaseWithCredits called with doc:', doc, 'docket:', docket);

    if (!doc.id && doc.id !== 0) {
      setError('Document ID is missing. Please refresh and try again.');
      return;
    }

    // Ensure document_id is an integer
    const documentId = parseInt(String(doc.id), 10);
    if (isNaN(documentId)) {
      setError('Invalid document ID. Please refresh and try again.');
      return;
    }

    try {
      // Add to purchasing set
      setPurchasingDocs(prev => new Set(prev).add(documentId));
      setError(null);

      // Fetch user credits first
      if (!user?.id) {
        throw new Error('User not authenticated');
      }
      const creditsResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/credits/balance/${user.id}`);
      if (!creditsResponse.ok) {
        throw new Error('Failed to fetch credit balance');
      }
      const creditsData = await creditsResponse.json();
      setUserCredits(creditsData.balance);

      // Check if user has sufficient credits (estimated)
      const estimatedCost = 3.0; // Default estimate, can be improved based on page count
      if (creditsData.balance < estimatedCost) {
        setError(
          `Insufficient credits. You have $${creditsData.balance.toFixed(2)} but need approximately $${estimatedCost.toFixed(2)}. ` +
          `Please visit the Credits page to add more credits.`
        );
        setPurchasingDocs(prev => {
          const newSet = new Set(prev);
          newSet.delete(documentId);
          return newSet;
        });
        return;
      }

      // Submit purchase request
      const purchaseRequest = {
        document_id: String(documentId),
        docket_id: String(docket.id || ''),
        court: docket.court_id || docket.court || '',
        case_number: docket.docket_number || docket.case_name || '',
        document_number: doc.document_number || 0,
        estimated_cost: estimatedCost
      };

      console.log('[DEBUG] Purchase request:', purchaseRequest);

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/credits/purchase-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          ...purchaseRequest,
          user_id: 1,  // For now, hardcoded user ID
          username: 'test_user',
          pacer_username: username || credentialsStatus?.username || '',
          pacer_password: password || ''  // This should be stored securely
        })
      });

      const data = await response.json();
      console.log('[DEBUG] Purchase response:', data);

      if (response.ok && data.success) {
        // Check if document was found to be FREE in RECAP Archive
        if (data.free_download) {
          setSuccess(
            `🎉 ${data.message} ` +
            `Downloading now from RECAP Archive...`
          );

          // Download the free document directly
          setPurchasingDocs(prev => {
            const newSet = new Set(prev);
            newSet.delete(documentId);
            return newSet;
          });

          // Open download link or trigger download
          if (data.download_url) {
            window.open(data.download_url, '_blank');
          }

          return;
        }

        // Document not free - proceed with purchase
        setSuccess(
          `Purchase initiated for document #${doc.document_number}. ` +
          `Cost: $${data.cost_credits.toFixed(2)}. Status: ${data.status}`
        );

        // Poll for purchase completion
        const purchaseId = data.purchase_id;
        let attempts = 0;
        const maxAttempts = 30; // 30 attempts x 2 seconds = 60 seconds

        const pollStatus = setInterval(async () => {
          attempts++;

          try {
            const statusResponse = await fetch(
              `${API_CONFIG.BASE_URL}/api/v1/credits/purchase-status/${purchaseId}`
            );
            const statusData = await statusResponse.json();

            if (statusData.status === 'completed') {
              clearInterval(pollStatus);
              setSuccess(
                `Document purchased and downloaded successfully! ` +
                `File: ${statusData.file_path || 'Saved to app storage'}`
              );
              setPurchasingDocs(prev => {
                const newSet = new Set(prev);
                newSet.delete(documentId);
                return newSet;
              });
              // Refresh credits
              if (user?.id) {
                const newCreditsResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/credits/balance/${user.id}`);
                const newCreditsData = await newCreditsResponse.json();
                setUserCredits(newCreditsData.balance);
              }
            } else if (statusData.status === 'failed') {
              clearInterval(pollStatus);
              setError(`Purchase failed: ${statusData.error_message || 'Unknown error'}`);
              setPurchasingDocs(prev => {
                const newSet = new Set(prev);
                newSet.delete(documentId);
                return newSet;
              });
              // Refresh credits (should be refunded)
              if (user?.id) {
                const newCreditsResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/credits/balance/${user.id}`);
                const newCreditsData = await newCreditsResponse.json();
                setUserCredits(newCreditsData.balance);
              }
            } else if (attempts >= maxAttempts) {
              clearInterval(pollStatus);
              setError('Purchase is taking longer than expected. Check the Credits page for status.');
              setPurchasingDocs(prev => {
                const newSet = new Set(prev);
                newSet.delete(documentId);
                return newSet;
              });
            }
          } catch (pollError) {
            console.error('[ERROR] Failed to poll purchase status:', pollError);
          }
        }, 2000); // Poll every 2 seconds

      } else {
        setError(`Purchase failed: ${data.detail || data.error || 'Unknown error'}`);
        setPurchasingDocs(prev => {
          const newSet = new Set(prev);
          newSet.delete(documentId);
          return newSet;
        });
      }
    } catch (err: any) {
      console.error('[ERROR] Exception during purchase:', err);
      setError(`Error purchasing document: ${err.message || 'Unknown error'}`);
      setPurchasingDocs(prev => {
        const newSet = new Set(prev);
        newSet.delete(documentId);
        return newSet;
      });
    }
  };

  // Load all documents for a docket
  const handleLoadAllDocuments = async (result: any, resultIndex: number) => {
    const docketIdToLoad = result.id || result.docket_id;

    if (!docketIdToLoad) {
      setError('Cannot load documents: invalid docket ID');
      return;
    }

    // Mark as loading
    setLoadingAllDocs(prev => new Set([...Array.from(prev), docketIdToLoad]));

    try {
      const response = await fetch(
        `${API_CONFIG.BASE_URL}/api/v1/courtlistener/docket/${docketIdToLoad}/documents`
      );

      if (!response.ok) {
        throw new Error('Failed to load documents');
      }

      const data = await response.json();

      if (data.success && data.documents) {
        // Update the search results with all documents
        setSearchResults((prev: any) => {
          if (!prev) return prev;

          const newResults = [...prev.results];
          newResults[resultIndex] = {
            ...newResults[resultIndex],
            recap_documents: data.documents,
            all_documents_loaded: true
          };

          return {
            ...prev,
            results: newResults
          };
        });

        // Mark as loaded
        setLoadedAllDocs(prev => new Set([...Array.from(prev), docketIdToLoad]));
        setSuccess(`Loaded ${data.documents.length} documents for this case`);
      }
    } catch (error: any) {
      console.error('Error loading all documents:', error);
      setError(`Failed to load all documents: ${error.message}`);
    } finally {
      // Remove from loading set
      setLoadingAllDocs(prev => {
        const newSet = new Set(prev);
        newSet.delete(docketIdToLoad);
        return newSet;
      });
    }
  };

  // Handle analyzing downloaded document
  const handleAnalyzeDocument = async (doc: any) => {
    const docKey = `recap_${doc.document_id}`;

    // Prevent re-analysis if already analyzed
    if (isDocumentAnalyzed(doc.document_id)) {
      toast.info('Document Already Analyzed', {
        description: 'This document has already been analyzed. View it in the "Analysis" tab.',
        duration: 4000,
      });
      return;
    }

    // Add to analyzing set
    setAnalyzingDocs(prev => new Set(prev).add(docKey));

    try {
      setSuccess('Processing document for analysis...');

      // First, extract text from the downloaded PDF
      const extractResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/process-recap-document`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: doc.file_path,
          document_id: doc.document_id,
          description: doc.original_doc?.short_description || doc.original_doc?.description || 'Court Document',
          page_count: doc.page_count
        })
      });

      if (!extractResponse.ok) {
        const errorData = await extractResponse.json().catch(() => ({}));
        const errorMsg = errorData.detail || errorData.error || 'Failed to process document';
        console.error('Backend error response:', errorData);
        throw new Error(errorMsg);
      }

      const extractData = await extractResponse.json();

      // Create DocumentData object for context
      const documentData = {
        id: `recap_${doc.document_id}`,
        fileName: `${doc.original_doc?.short_description || 'Court Document'}.pdf`,
        fileType: 'application/pdf',
        uploadDate: new Date(doc.downloaded_at),
        text: extractData.text || '',
        summary: extractData.summary,
        parties: extractData.parties,
        importantDates: extractData.important_dates,
        keyFigures: extractData.key_figures,
        keywords: extractData.keywords,
        analysis: extractData.analysis
      };

      // Add to document context
      addDocument(documentData);

      // Track as analyzed
      setAnalyzedDocIds(prev => new Set(prev).add(docKey));

      // Show success message - document is now in context and ready to view
      setSuccess('Document analyzed successfully! View it in the "Analysis" tab.');
      toast.success('Document Analysis Complete', {
        description: 'Switch to the Analysis tab to view the results',
        duration: 5000,
      });

    } catch (error: any) {
      console.error('Error analyzing document:', error);
      setError(`Failed to analyze document: ${error.message || 'Unknown error'}`);
    } finally {
      // Remove from analyzing set
      setAnalyzingDocs(prev => {
        const newSet = new Set(prev);
        newSet.delete(docKey);
        return newSet;
      });
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3">Loading PACER...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Federal Court Records Search</h1>
            <p className="text-gray-600 dark:text-slate-300">
              Access federal court records through CourtListener (FREE) or PACER
            </p>
          </div>
          {isAuthenticated && (
            <div className="flex items-center gap-3">
              <a href="/credits" className="flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg hover:bg-blue-100 transition-colors">
                <CreditCard className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                <div className="text-left">
                  <div className="text-xs text-gray-500 dark:text-slate-400">Credits Balance</div>
                  <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                    {userCredits !== null ? `$${userCredits.toFixed(2)}` : 'Loading...'}
                  </div>
                </div>
              </a>
            </div>
          )}
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-4 bg-green-50 text-green-800 border-green-200">
          <CheckCircle className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {/* Upgrade Prompt Modal */}
      {showUpgradePrompt && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="relative max-w-md w-full">
            <button
              onClick={() => setShowUpgradePrompt(false)}
              className="absolute -top-2 -right-2 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 z-10"
            >
              <XCircle className="h-5 w-5 text-gray-600 dark:text-slate-300" />
            </button>
            <UpgradePrompt
              feature={upgradeFeature}
              upgradeInfo={upgradeInfo}
              reason="This feature requires a paid subscription"
            />
          </div>
        </div>
      )}

      {/* Status Overview - Only visible when authenticated */}
      {isAuthenticated && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Credentials Status
                </div>
                {credentialsStatus?.has_credentials && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearCredentials}
                    disabled={clearing}
                    className="h-6 px-2 text-xs text-red-600 hover:text-red-700 hover:bg-red-50"
                    title="Clear PACER credentials"
                  >
                    {clearing ? 'Clearing...' : 'Logout'}
                  </Button>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {credentialsStatus?.has_credentials ? (
                <div className="flex items-center gap-2">
                  {credentialsStatus.is_verified ? (
                    <><CheckCircle className="h-5 w-5 text-green-500" /> <span className="text-green-600">Verified</span></>
                  ) : (
                    <><AlertTriangle className="h-5 w-5 text-yellow-500" /> <span className="text-yellow-600 dark:text-yellow-400">Not Verified</span></>
                  )}
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <XCircle className="h-5 w-5 text-red-500" />
                  <span className="text-red-600">Not Configured</span>
                </div>
              )}
            </CardContent>
          </Card>

          {stats && (
            <>
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <Search className="h-4 w-4" />
                    Total Searches
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{stats.usage.total_searches}</div>
                  <p className="text-xs text-gray-500 dark:text-slate-400">All time</p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium flex items-center gap-2">
                    <DollarSign className="h-4 w-4" />
                    Monthly Spending
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">${stats.limits.monthly_spending.toFixed(2)}</div>
                  <p className="text-xs text-gray-500 dark:text-slate-400">
                    ${stats.limits.monthly_remaining.toFixed(2)} remaining
                  </p>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}

      <Tabs defaultValue="search" className="space-y-4">
        <TabsList>
          <TabsTrigger value="setup">Setup</TabsTrigger>
          <TabsTrigger value="search">
            Search
          </TabsTrigger>
          <TabsTrigger value="monitoring" onClick={() => fetchMonitoredCases()}>
            <Bell className="h-4 w-4 mr-2" />
            Monitoring
            {isAuthenticated && monitoredCases.size > 0 && (
              <Badge variant="secondary" className="ml-2">
                {monitoredCases.size}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="downloaded">
            <Download className="h-4 w-4 mr-2" />
            Downloaded
            {downloadedDocs.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {downloadedDocs.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="analysis">
            <FileText className="h-4 w-4 mr-2" />
            Analysis
            {documents.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {documents.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="stats" disabled={!stats}>
            Statistics
          </TabsTrigger>
        </TabsList>

        {/* Setup Tab - Now shows platform-managed status */}
        <TabsContent value="setup">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                PACER Access Included
              </CardTitle>
              <CardDescription>
                Your subscription includes access to federal court records - no additional setup required.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Platform-Managed Notice */}
              <Alert className="mb-6 bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700">
                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
                <AlertDescription className="text-green-800 dark:text-green-200">
                  <strong>Good news!</strong> PACER access is managed by our platform. You don't need your own PACER account.
                  Simply use your subscription credits to search and download federal court documents.
                </AlertDescription>
              </Alert>

              <div className="space-y-6">
                {/* How It Works */}
                <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg">
                  <h4 className="font-semibold text-sm mb-3">How It Works</h4>
                  <ul className="text-sm text-gray-600 dark:text-slate-300 space-y-2">
                    <li className="flex items-start gap-2">
                      <span className="text-green-500 mt-0.5">✓</span>
                      <span><strong>Free searches:</strong> All case and party searches are free</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-500 mt-0.5">✓</span>
                      <span><strong>Document downloads:</strong> Use your subscription credits to download documents</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-green-500 mt-0.5">✓</span>
                      <span><strong>No account needed:</strong> We handle all PACER authentication for you</span>
                    </li>
                  </ul>
                </div>

                {/* Credits Info */}
                <div className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-700">
                  <h4 className="font-semibold text-sm mb-2 text-blue-800 dark:text-blue-200">Your Credits</h4>
                  <p className="text-sm text-blue-700 dark:text-blue-300">
                    Check your credit balance in your account settings. Need more credits?{' '}
                    <a href="/subscription" className="underline font-medium hover:text-blue-900 dark:hover:text-blue-100">
                      Upgrade your subscription
                    </a>
                  </p>
                </div>
              </div>

              {/* Legacy form removed - keeping structure for compatibility */}
              <form onSubmit={(e) => { e.preventDefault(); toast.info('PACER credentials are managed by the platform.'); }} className="hidden">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="username">PACER Username *</Label>
                    <Input
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="your.email@example.com"
                      required
                    />
                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">Enter your PACER account email or username</p>
                  </div>

                  <div>
                    <Label htmlFor="password">PACER Password *</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                        className="pr-10"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 dark:text-slate-400 hover:text-gray-700 focus:outline-none z-10 hover:opacity-70 transition-opacity"
                        tabIndex={-1}
                      >
                        {showPassword ? (
                          <Eye className="h-5 w-5" />
                        ) : (
                          <EyeOff className="h-5 w-5" />
                        )}
                      </button>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="clientCode">Client Code (Optional)</Label>
                    <Input
                      id="clientCode"
                      value={clientCode}
                      onChange={(e) => setClientCode(e.target.value)}
                      placeholder="CLIENT123"
                    />
                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">For law firms tracking PACER costs by client. Leave blank for personal use.</p>
                  </div>

                  <div>
                    <Label htmlFor="environment">Environment</Label>
                    <select
                      id="environment"
                      value={environment}
                      onChange={(e) => setEnvironment(e.target.value)}
                      className="w-full border-2 border-gray-300 dark:border-teal-500 rounded-md px-3 py-2 bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100"
                    >
                      <option value="production">Production (Live PACER - charges apply)</option>
                      <option value="qa">QA/Testing (Training environment - free, no real data)</option>
                    </select>
                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">Use QA/Testing for practice without charges</p>
                  </div>

                  <div>
                    <Label htmlFor="dailyLimit">Daily Limit ($)</Label>
                    <Input
                      id="dailyLimit"
                      type="number"
                      step="0.01"
                      value={dailyLimit}
                      onChange={(e) => setDailyLimit(e.target.value)}
                      placeholder="100.00"
                    />
                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">Recommended: $100 for regular use</p>
                  </div>

                  <div>
                    <Label htmlFor="monthlyLimit">Monthly Limit ($)</Label>
                    <Input
                      id="monthlyLimit"
                      type="number"
                      step="0.01"
                      value={monthlyLimit}
                      onChange={(e) => setMonthlyLimit(e.target.value)}
                      placeholder="1000.00"
                    />
                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">Recommended: $1000 for regular use</p>
                  </div>
                </div>

                <div className="flex gap-2 flex-wrap">
                  <Button type="submit" disabled={saving}>
                    {saving ? 'Saving...' : 'Save Credentials'}
                  </Button>

                  {credentialsStatus?.has_credentials && (
                    <>
                      <Button type="button" variant="outline" onClick={handleAuthenticate}>
                        {credentialsStatus.is_verified ? 'Re-authenticate' : 'Test Authentication'}
                      </Button>
                      <Button
                        type="button"
                        variant="destructive"
                        onClick={handleClearCredentials}
                        disabled={clearing}
                      >
                        {clearing ? 'Clearing...' : 'Clear Credentials'}
                      </Button>
                    </>
                  )}
                </div>

                {/* Important Next Step Notice */}
                {credentialsStatus?.has_credentials && !credentialsStatus.is_verified && (
                  <Alert className="mt-4 bg-amber-50 border-amber-300">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                    <AlertDescription>
                      <strong>Important:</strong> After saving your credentials, click the <strong>"Test Authentication"</strong> button above to verify your PACER account before searching.
                    </AlertDescription>
                  </Alert>
                )}
              </form>

              <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                <h4 className="font-semibold text-sm mb-2">PACER Pricing Information</h4>
                <ul className="text-sm text-gray-600 dark:text-slate-300 space-y-1">
                  <li>• Case searches: <strong>FREE</strong></li>
                  <li>• Party searches: <strong>FREE</strong></li>
                  <li>• Document pages: <strong>$0.10/page</strong> (capped at $3.00 per document)</li>
                  <li>• Quarterly free allowance: <strong>$30.00</strong></li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Search Tab */}
        <TabsContent value="search">
          <Card data-tour="pacer-search-form">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Search Federal Court Records</span>
                {hasUpdates && (
                  <Badge variant="default" className="bg-green-500">
                    {updateCount} New Update{updateCount !== 1 ? 's' : ''}
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                Search federal court records - Choose your source below
              </CardDescription>
            </CardHeader>
            <CardContent>
              {/* Source Selector */}
              <div data-tour="pacer-source-selector" className="mb-6 p-4 bg-gray-50 dark:bg-slate-800 rounded-lg border dark:border-slate-700">
                <Label className="text-sm font-semibold mb-2 block">Search Source</Label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setSearchSource('courtlistener')}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      searchSource === 'courtlistener'
                        ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/30 dark:border-teal-400'
                        : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500 dark:bg-slate-700'
                    }`}
                  >
                    <div className="font-semibold text-sm text-gray-900 dark:text-slate-100">CourtListener</div>
                    <div className="text-xs text-gray-600 dark:text-slate-300 dark:text-slate-400 mt-1">FREE - No account needed</div>
                    <Badge variant="outline" className="mt-2 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-600">
                      Recommended
                    </Badge>
                  </button>
                  <button
                    type="button"
                    onClick={() => setSearchSource('pacer')}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      searchSource === 'pacer'
                        ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/30 dark:border-teal-400'
                        : 'border-gray-200 dark:border-slate-600 hover:border-gray-300 dark:hover:border-slate-500 dark:bg-slate-700'
                    }`}
                  >
                    <div className="font-semibold text-sm text-gray-900 dark:text-slate-100">PACER</div>
                    <div className="text-xs text-gray-600 dark:text-slate-300 dark:text-slate-400 mt-1">Uses subscription credits</div>
                    <Badge variant="outline" className="mt-2 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 border-green-200 dark:border-green-600">
                      Included
                    </Badge>
                  </button>
                </div>
              </div>

              <Tabs value={searchType} onValueChange={(v) => setSearchType(v as 'case' | 'party')}>
                <TabsList className="mb-4">
                  <TabsTrigger value="party">Party / Company Name</TabsTrigger>
                  <TabsTrigger value="case">Case Number</TabsTrigger>
                </TabsList>

                <TabsContent value="case">
                  <form onSubmit={handleSearch} className="space-y-4">
                    <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-3 rounded-lg border-2 border-gray-300 dark:border-slate-500 bg-white dark:bg-slate-700">
                        <Label htmlFor="caseNumber">Case Number</Label>
                        <Input
                          id="caseNumber"
                          value={caseNumber}
                          onChange={(e) => setCaseNumber(e.target.value)}
                          placeholder="1:24-cv-00123"
                        />
                      </div>

                      <div className="p-3 rounded-lg border-2 border-gray-300 dark:border-slate-500 bg-white dark:bg-slate-700">
                        <Label htmlFor="courtType">Court Type</Label>
                        <select
                          id="courtType"
                          value={courtType}
                          onChange={(e) => {
                            setCourtType(e.target.value as 'bankruptcy' | 'district' | 'circuit');
                            setCourt('');
                          }}
                          className="w-full border-2 border-gray-300 dark:border-teal-500 rounded-md px-3 py-2 bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-teal-400"
                        >
                          <option value="bankruptcy">Bankruptcy Courts</option>
                          <option value="district">District Courts</option>
                          <option value="circuit">Circuit Courts</option>
                        </select>
                      </div>

                      <div className="md:col-span-2 p-3 rounded-lg border-2 border-gray-300 dark:border-slate-500 bg-white dark:bg-slate-700">
                        <Label htmlFor="court">
                          Select Specific Court {searchSource === 'pacer' ? '*' : '(Optional)'}
                        </Label>
                        <select
                          id="court"
                          value={court}
                          onChange={(e) => setCourt(e.target.value)}
                          className="w-full border-2 border-gray-300 dark:border-teal-500 rounded-md px-3 py-2 bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-teal-400"
                          required={searchSource === 'pacer'}
                        >
                          <option value="">-- {searchSource === 'courtlistener' ? 'All Courts' : 'Select a Court'} --</option>
                          {courtType === 'bankruptcy' && Object.entries(bankruptcyCourts).map(([state, courts]) => (
                            <optgroup key={state} label={`${state} Bankruptcy`}>
                              {courts.map(courtCode => (
                                <option key={courtCode} value={courtCode}>
                                  {state} - {courtCode.toUpperCase()}
                                  {courtCode.includes('nb') && ' (Northern)'}
                                  {courtCode.includes('eb') && ' (Eastern)'}
                                  {courtCode.includes('sb') && ' (Southern)'}
                                  {courtCode.includes('wb') && ' (Western)'}
                                  {courtCode.includes('mb') && ' (Middle)'}
                                  {courtCode.includes('cb') && ' (Central)'}
                                  {!courtCode.match(/[neswmc]b$/) && ' (Main)'}
                                </option>
                              ))}
                            </optgroup>
                          ))}
                          {courtType === 'district' && Object.entries(districtCourts).map(([state, courts]) => (
                            <optgroup key={state} label={`${state} District`}>
                              {courts.map(courtCode => (
                                <option key={courtCode} value={courtCode}>
                                  {state} - {courtCode.toUpperCase()}
                                  {courtCode.includes('nd') && ' (Northern)'}
                                  {courtCode.includes('ed') && ' (Eastern)'}
                                  {courtCode.includes('sd') && ' (Southern)'}
                                  {courtCode.includes('wd') && ' (Western)'}
                                  {courtCode.includes('md') && ' (Middle)'}
                                  {courtCode.includes('cd') && ' (Central)'}
                                  {!courtCode.match(/[neswmc]d$/) && ' (Main)'}
                                </option>
                              ))}
                            </optgroup>
                          ))}
                          {courtType === 'circuit' && circuitCourts.map(circuit => (
                            <option key={circuit.code} value={circuit.code}>
                              {circuit.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="md:col-span-2 p-3 rounded-lg border-2 border-gray-300 dark:border-slate-500 bg-white dark:bg-slate-700">
                        <Label htmlFor="caseTitle">Case Title (Optional)</Label>
                        <Input
                          id="caseTitle"
                          value={caseTitle}
                          onChange={(e) => setCaseTitle(e.target.value)}
                          placeholder="Enter case title keywords"
                        />
                      </div>

                      {searchSource === 'courtlistener' && (
                        <>
                          <div className="md:col-span-2">
                            <Alert className="mb-0">
                              <HelpCircle className="h-4 w-4" />
                              <AlertDescription>
                                <strong>Date Filter:</strong> Search for cases filed within a specific date range. Leave blank to search all dates.
                                <br />
                                <strong>Examples:</strong> Recent cases (set "Filed After" to 30 days ago) • Specific year (set both dates to year boundaries) • Historical research (set exact range)
                              </AlertDescription>
                            </Alert>
                          </div>
                          <div className="p-3 rounded-lg border-2 border-gray-300 dark:border-slate-500 bg-white dark:bg-slate-700">
                            <Label htmlFor="filedAfter">Filed After (Optional)</Label>
                            <Input
                              id="filedAfter"
                              type="date"
                              value={filedAfter}
                              onChange={(e) => setFiledAfter(e.target.value)}
                              placeholder="YYYY-MM-DD"
                            />
                            <p className="text-xs text-gray-500 dark:text-slate-400 dark:text-slate-400 mt-1">Earliest date to include in results</p>
                          </div>
                          <div className="p-3 rounded-lg border-2 border-gray-300 dark:border-slate-500 bg-white dark:bg-slate-700">
                            <Label htmlFor="filedBefore">Filed Before (Optional)</Label>
                            <Input
                              id="filedBefore"
                              type="date"
                              value={filedBefore}
                              onChange={(e) => setFiledBefore(e.target.value)}
                              placeholder="YYYY-MM-DD"
                            />
                            <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">Latest date to include in results</p>
                          </div>
                        </>
                      )}
                    </div>
                    </div>

                    <Button type="submit" disabled={searching || (searchSource === 'pacer' && !court)}>
                      {searching ? 'Searching...' : 'Search Cases'}
                    </Button>
                  </form>
                </TabsContent>

                <TabsContent value="party">
                  <form onSubmit={handleSearch} className="space-y-4">
                    <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="md:col-span-2 p-3 rounded-lg border-2 border-teal-400 dark:border-teal-500 bg-teal-50 dark:bg-teal-900/20">
                        <Label htmlFor="partyName" className="text-teal-800 dark:text-teal-300 font-semibold">Party / Company Name *</Label>
                        <Input
                          id="partyName"
                          value={partyName}
                          onChange={(e) => setPartyName(e.target.value)}
                          placeholder="e.g., Acme Corporation, Smith, Bank of America"
                          required
                          className="mt-1 border-teal-300 dark:border-teal-600"
                        />
                        <p className="text-xs text-teal-600 dark:text-teal-400 mt-1">Enter a person's name, company name, or organization</p>
                      </div>

                      <div className="p-3 rounded-lg border-2 border-gray-300 dark:border-slate-500 bg-white dark:bg-slate-700">
                        <Label htmlFor="partyCourtType">Court Type</Label>
                        <select
                          id="partyCourtType"
                          value={courtType}
                          onChange={(e) => {
                            setCourtType(e.target.value as 'bankruptcy' | 'district' | 'circuit');
                            setCourt('');
                          }}
                          className="w-full border-2 border-gray-300 dark:border-teal-500 rounded-md px-3 py-2 bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-teal-400"
                        >
                          <option value="bankruptcy">Bankruptcy Courts</option>
                          <option value="district">District Courts</option>
                          <option value="circuit">Circuit Courts</option>
                        </select>
                      </div>

                      <div className="md:col-span-2 p-3 rounded-lg border-2 border-gray-300 dark:border-slate-500 bg-white dark:bg-slate-700">
                        <Label htmlFor="partyCourt">Select Specific Court (Optional)</Label>
                        <select
                          id="partyCourt"
                          value={court}
                          onChange={(e) => setCourt(e.target.value)}
                          className="w-full border-2 border-gray-300 dark:border-teal-500 rounded-md px-3 py-2 bg-white dark:bg-slate-700 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-teal-400"
                        >
                          <option value="">-- All Courts (Search All) --</option>
                          {courtType === 'bankruptcy' && Object.entries(bankruptcyCourts).map(([state, courts]) => (
                            <optgroup key={state} label={`${state} Bankruptcy`}>
                              {courts.map(courtCode => (
                                <option key={courtCode} value={courtCode}>
                                  {state} - {courtCode.toUpperCase()}
                                  {courtCode.includes('nb') && ' (Northern)'}
                                  {courtCode.includes('eb') && ' (Eastern)'}
                                  {courtCode.includes('sb') && ' (Southern)'}
                                  {courtCode.includes('wb') && ' (Western)'}
                                  {courtCode.includes('mb') && ' (Middle)'}
                                  {courtCode.includes('cb') && ' (Central)'}
                                  {!courtCode.match(/[neswmc]b$/) && ' (Main)'}
                                </option>
                              ))}
                            </optgroup>
                          ))}
                          {courtType === 'district' && Object.entries(districtCourts).map(([state, courts]) => (
                            <optgroup key={state} label={`${state} District`}>
                              {courts.map(courtCode => (
                                <option key={courtCode} value={courtCode}>
                                  {state} - {courtCode.toUpperCase()}
                                  {courtCode.includes('nd') && ' (Northern)'}
                                  {courtCode.includes('ed') && ' (Eastern)'}
                                  {courtCode.includes('sd') && ' (Southern)'}
                                  {courtCode.includes('wd') && ' (Western)'}
                                  {courtCode.includes('md') && ' (Middle)'}
                                  {courtCode.includes('cd') && ' (Central)'}
                                  {!courtCode.match(/[neswmc]d$/) && ' (Main)'}
                                </option>
                              ))}
                            </optgroup>
                          ))}
                          {courtType === 'circuit' && circuitCourts.map(circuit => (
                            <option key={circuit.code} value={circuit.code}>
                              {circuit.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      {searchSource === 'courtlistener' && (
                        <>
                          <div>
                            <Label htmlFor="partyFiledAfter">Filed After (Optional)</Label>
                            <Input
                              id="partyFiledAfter"
                              type="date"
                              value={filedAfter}
                              onChange={(e) => setFiledAfter(e.target.value)}
                              placeholder="YYYY-MM-DD"
                            />
                          </div>
                          <div>
                            <Label htmlFor="partyFiledBefore">Filed Before (Optional)</Label>
                            <Input
                              id="partyFiledBefore"
                              type="date"
                              value={filedBefore}
                              onChange={(e) => setFiledBefore(e.target.value)}
                              placeholder="YYYY-MM-DD"
                            />
                          </div>
                        </>
                      )}
                    </div>
                    </div>

                    <Button type="submit" disabled={searching}>
                      {searching ? 'Searching...' : 'Search Parties'}
                    </Button>
                  </form>
                </TabsContent>
              </Tabs>

              {/* Direct Docket ID Lookup (for blocked cases) */}
              {searchSource === 'courtlistener' && (
                <div className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg">
                  <div className="flex items-start gap-2 mb-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
                    <div>
                      <h4 className="font-semibold text-sm text-yellow-900 dark:text-yellow-100">
                        Can't find your case? Access Blocked Cases Directly
                      </h4>
                      <p className="text-xs text-yellow-700 dark:text-yellow-300 mt-2 leading-relaxed">
                        <strong>How to find your case's Docket ID:</strong><br />
                        1️⃣ Go to <a href="https://www.courtlistener.com" target="_blank" rel="noopener noreferrer" className="underline">courtlistener.com</a> and search for your case<br />
                        2️⃣ Click on the case to open its page<br />
                        3️⃣ Look at the URL in your browser (Example: https://www.courtlistener.com/docket/<strong>69566281</strong>/...)<br />
                        4️⃣ Copy the number after "/docket/" (e.g., <strong>69566281</strong>)<br />
                        5️⃣ Paste it below and click "Lookup Docket"
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-2 items-end">
                    <div className="flex-1">
                      <Label htmlFor="docketId" className="text-sm">
                        Docket ID (from CourtListener URL)
                      </Label>
                      <Input
                        id="docketId"
                        value={docketId}
                        onChange={(e) => setDocketId(e.target.value)}
                        placeholder="e.g., 69566281"
                        className="mt-1"
                      />
                      <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
                        Example: https://www.courtlistener.com/docket/<strong>69566281</strong>/...
                      </p>
                    </div>
                    <Button
                      onClick={handleDirectDocketLookup}
                      disabled={searching}
                      className="bg-yellow-600 hover:bg-yellow-700"
                    >
                      {searching ? 'Loading...' : 'Lookup Docket'}
                    </Button>
                  </div>
                </div>
              )}

              {/* Search Results */}
              {searchResults && (
                <div data-tour="pacer-results" className="mt-6">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold">
                      Search Results ({searchResults.total_count} found)
                    </h3>
                    <div className="flex items-center gap-2">
                      {searchResults.source === 'courtlistener' && (
                        <Badge variant="outline" className="bg-blue-50">
                          CourtListener
                        </Badge>
                      )}
                      {searchResults.filtered_by_type && (
                        <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-300">
                          Filtered: {searchResults.filtered_by_type === 'bankruptcy' ? 'Bankruptcy' : searchResults.filtered_by_type === 'district' ? 'District' : 'Circuit'} Courts Only
                        </Badge>
                      )}
                    </div>
                  </div>
                  <div className="space-y-2">
                    {searchResults.results.map((result: any, index: number) => {
                      const docketId = result.id || result.docket_id;
                      const isMonitored = docketId && monitoredCases.has(docketId);

                      return (
                        <Card key={index}>
                          <CardContent className="p-4">
                            <div className="flex justify-between items-start">
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <p className="font-semibold">
                                    {result.docketNumber || result.caseNumber || result.partyName || result.caseName}
                                  </p>
                                  {isMonitored && (
                                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
                                      <Eye className="h-3 w-3 mr-1" />
                                      Monitoring
                                    </Badge>
                                  )}
                                </div>
                                <p className="text-sm text-gray-600 dark:text-slate-300 mt-1">
                                  {result.caseTitle || result.caseName || result.caseNumber}
                                </p>
                                <div className="flex items-center gap-2 mt-2">
                                  {result.court && (
                                    <Badge variant="outline">{result.court}</Badge>
                                  )}
                                  {result.dateFiled && (
                                    <span className="text-xs text-gray-500 dark:text-slate-400">
                                      Filed: {new Date(result.dateFiled).toLocaleDateString()}
                                    </span>
                                  )}
                                </div>

                                {/* API Limitation Message - Show link to CourtListener */}
                                {result.api_limitation && result.courtlistener_url && (
                                  <div className="mt-4 pt-4 border-t border-gray-200">
                                    <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                                      <div className="flex items-start gap-3">
                                        <FileText className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                                        <div className="flex-1">
                                          <p className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                                            View Documents on CourtListener
                                          </p>
                                          <p className="text-xs text-blue-700 dark:text-blue-300 mb-3">
                                            API access to RECAP documents requires a paid subscription. However, you can view all documents for free on CourtListener's website.
                                          </p>
                                          <a
                                            href={result.courtlistener_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-md transition-colors"
                                          >
                                            <ExternalLink className="h-4 w-4" />
                                            View Case & Documents on CourtListener
                                          </a>
                                        </div>
                                      </div>
                                    </div>
                                  </div>
                                )}

                                {/* RECAP Documents Display */}
                                {!result.api_limitation && result.recap_documents && result.recap_documents.length > 0 && (
                                  <div className="mt-4 pt-4 border-t border-gray-200">
                                    <div className="flex items-center justify-between gap-2 mb-2">
                                      <div className="flex items-center gap-2">
                                        <FileText className="h-4 w-4 text-gray-600 dark:text-slate-300" />
                                        <span className="text-sm font-semibold text-gray-700">
                                          Available Documents ({result.recap_documents.length})
                                        </span>
                                        {/* Sort Toggle */}
                                        <Button
                                          size="sm"
                                          variant="ghost"
                                          onClick={() => setDocumentSortOrder(prev => prev === 'newest' ? 'oldest' : 'newest')}
                                          className="text-gray-600 dark:text-slate-300 hover:text-gray-800 h-7 px-2"
                                          title={`Sort by ${documentSortOrder === 'newest' ? 'oldest' : 'newest'} first`}
                                        >
                                          {documentSortOrder === 'newest' ? (
                                            <>
                                              <ArrowDown className="h-3 w-3 mr-1" />
                                              <span className="text-xs">Newest</span>
                                            </>
                                          ) : (
                                            <>
                                              <ArrowUp className="h-3 w-3 mr-1" />
                                              <span className="text-xs">Oldest</span>
                                            </>
                                          )}
                                        </Button>
                                      </div>

                                      {/* Always show button - changes label based on state */}
                                      <div className="flex items-center gap-2">
                                        {(result.all_documents_loaded || loadedAllDocs.has(docketId)) && (
                                          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
                                            <CheckCircle className="h-3 w-3 mr-1" />
                                            All Loaded
                                          </Badge>
                                        )}
                                        <Button
                                          size="sm"
                                          variant="outline"
                                          onClick={() => handleLoadAllDocuments(result, index)}
                                          disabled={loadingAllDocs.has(docketId)}
                                          className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:text-blue-300"
                                        >
                                          {loadingAllDocs.has(docketId) ? (
                                            <>
                                              <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                                              Loading...
                                            </>
                                          ) : (result.all_documents_loaded || loadedAllDocs.has(docketId)) ? (
                                            <>
                                              <RefreshCw className="h-3 w-3 mr-1" />
                                              Refresh Documents
                                            </>
                                          ) : (
                                            <>
                                              <Eye className="h-3 w-3 mr-1" />
                                              View All Documents
                                            </>
                                          )}
                                        </Button>
                                      </div>
                                    </div>
                                    <div className="mb-3 p-2 bg-green-50 border border-green-300 rounded text-xs text-green-800">
                                      <Info className="h-3 w-3 inline mr-1" />
                                      <strong>📄 FREE Document Downloads:</strong> Click "Download to App" to automatically download documents directly into your app for AI analysis.
                                      All documents are completely free - no PACER fees!
                                    </div>
                                    <div className="space-y-2 max-h-96 overflow-y-auto">
                                      {[...result.recap_documents]
                                        .sort((a: any, b: any) => {
                                          // Sort by entry_date_filed (newest first when documentSortOrder is 'newest')
                                          const dateA = a.entry_date_filed ? new Date(a.entry_date_filed).getTime() : 0;
                                          const dateB = b.entry_date_filed ? new Date(b.entry_date_filed).getTime() : 0;
                                          if (dateA !== dateB) {
                                            return documentSortOrder === 'newest' ? dateB - dateA : dateA - dateB;
                                          }
                                          // If dates are equal, sort by entry_number descending (higher number = more recent)
                                          const numA = a.entry_number || a.document_number || 0;
                                          const numB = b.entry_number || b.document_number || 0;
                                          return documentSortOrder === 'newest' ? numB - numA : numA - numB;
                                        })
                                        .map((doc: any, docIdx: number) => (
                                        <div key={`${doc.id}-${docIdx}`} className="flex items-start justify-between gap-2 p-2 bg-gray-50 rounded border border-gray-200">
                                          <div className="flex-1 min-w-0">
                                            <div className="flex items-start gap-2 flex-wrap">
                                              <p className="text-sm font-medium text-gray-900 break-words line-clamp-2">
                                                {(doc.entry_number || doc.document_number) && <span className="text-blue-600 dark:text-blue-400 font-semibold mr-1">#{doc.entry_number || doc.document_number}</span>}
                                                {doc.short_description || doc.description || 'Court Document'}
                                              </p>
                                              {doc.is_available && doc.filepath_local ? (
                                                <Badge className="bg-green-500 text-white text-xs">FREE</Badge>
                                              ) : (
                                                <Badge variant="outline" className="text-xs text-amber-700 border-amber-300">
                                                  ~${((doc.page_count || 10) * 0.10).toFixed(2)} on PACER
                                                </Badge>
                                              )}
                                              {/* Status badges for downloaded/analyzed */}
                                              {isDocumentDownloaded(doc.id) && (
                                                <Badge className="bg-teal-500 text-white text-xs">In App</Badge>
                                              )}
                                              {isDocumentAnalyzed(doc.id) && (
                                                <Badge className="bg-purple-500 text-white text-xs">Analyzed</Badge>
                                              )}
                                            </div>
                                            {doc.entry_date_filed && (
                                              <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
                                                Filed: {new Date(doc.entry_date_filed).toLocaleDateString()}
                                                {doc.page_count && ` • ${doc.page_count} pages`}
                                              </p>
                                            )}
                                          </div>
                                          {doc.is_available && doc.filepath_local ? (
                                            <div className="flex gap-2 flex-shrink-0">
                                              {isDocumentDownloaded(doc.id) ? (
                                                // Already downloaded - show success state
                                                <Button
                                                  size="sm"
                                                  disabled
                                                  className="bg-gray-100 text-green-700 border border-green-300 cursor-default"
                                                >
                                                  <CheckCircle className="h-3 w-3 mr-1" />
                                                  Downloaded
                                                </Button>
                                              ) : (
                                                // Not yet downloaded - show download button
                                                <Button
                                                  size="sm"
                                                  onClick={() => handleDownloadToApp(doc, result)}
                                                  disabled={downloadingDocs.has(doc.id)}
                                                  className="bg-green-600 hover:bg-green-700 text-white"
                                                >
                                                  {downloadingDocs.has(doc.id) ? (
                                                    <>
                                                      <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                                                      Downloading...
                                                    </>
                                                  ) : (
                                                    <>
                                                      <Download className="h-3 w-3 mr-1" />
                                                      Download to App
                                                    </>
                                                  )}
                                                </Button>
                                              )}
                                              <a
                                                href={`https://www.courtlistener.com${doc.filepath_local.startsWith('/') ? doc.filepath_local : '/' + doc.filepath_local}`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                              >
                                                <Button
                                                  size="sm"
                                                  variant="outline"
                                                  className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:text-blue-300"
                                                >
                                                  <ExternalLink className="h-3 w-3 mr-1" />
                                                  View Online
                                                </Button>
                                              </a>
                                            </div>
                                          ) : isAuthenticated ? (
                                            <Button
                                              size="sm"
                                              onClick={() => handlePurchaseWithCredits(doc, result)}
                                              disabled={purchasingDocs.has(doc.id)}
                                              className="bg-blue-600 hover:bg-blue-700 text-white flex-shrink-0"
                                            >
                                              {purchasingDocs.has(doc.id) ? (
                                                <>
                                                  <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                                                  Purchasing...
                                                </>
                                              ) : (
                                                <>
                                                  <CreditCard className="h-3 w-3 mr-1" />
                                                  Purchase with Credits
                                                </>
                                              )}
                                            </Button>
                                          ) : (
                                            <Button
                                              size="sm"
                                              onClick={() => router.push('/login')}
                                              variant="outline"
                                              className="flex-shrink-0"
                                            >
                                              <Lock className="h-3 w-3 mr-1" />
                                              Login to Purchase
                                            </Button>
                                          )}
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>

                              {/* CourtListener Auto-Monitor Controls */}
                              {isAuthenticated && searchResults.source === 'courtlistener' && docketId && (
                                <div className="ml-4">
                                  {isMonitored ? (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleStopMonitoring(docketId, result.caseName || result.caseTitle || result.docketNumber || `Case ${docketId}`)}
                                      className="text-red-600 hover:text-red-700 border-red-300 hover:border-red-400"
                                    >
                                      <EyeOff className="h-4 w-4 mr-1" />
                                      Stop
                                    </Button>
                                  ) : (
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => openStartMonitoringConfirmation(
                                        docketId,
                                        result.caseName || result.caseTitle || result.case_name || result.docketNumber || `Case ${docketId}`,
                                        result
                                      )}
                                      className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:text-blue-300"
                                    >
                                      <Eye className="h-4 w-4 mr-1" />
                                      Monitor
                                    </Button>
                                  )}
                                </div>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>

                  {/* Monitored Cases Summary */}
                  {isAuthenticated && monitoredCases.size > 0 && (
                    <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Eye className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                          <span className="text-sm font-medium text-blue-900 dark:text-blue-100">
                            Monitoring {monitoredCases.size} case{monitoredCases.size !== 1 ? 's' : ''} for new documents
                          </span>
                        </div>
                        <span className="text-xs text-blue-700 dark:text-blue-300">Auto-checking every 30s</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Monitoring Tab */}
        {isAuthenticated ? (
          <TabsContent value="monitoring">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Case Monitoring Dashboard</CardTitle>
                    <CardDescription>
                      Track cases for automatic updates when new documents are filed
                    </CardDescription>
                  </div>
                  <Button
                    onClick={handleRefreshUpdates}
                    disabled={refreshingUpdates || monitoredCasesList.length === 0}
                    variant="outline"
                    size="sm"
                  >
                    <RefreshCw className={`h-4 w-4 mr-2 ${refreshingUpdates ? 'animate-spin' : ''}`} />
                    Check for Updates
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {loadingMonitored ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-3">Loading monitored cases...</span>
                  </div>
                ) : monitoredCasesList.length === 0 ? (
                  <div className="text-center py-12">
                    <BellOff className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-gray-700 mb-2">
                      No Cases Being Monitored
                    </h3>
                    <p className="text-gray-500 dark:text-slate-400 mb-4">
                      Start monitoring cases to receive automatic updates when new documents are filed
                    </p>
                    <p className="text-sm text-gray-400">
                      Search for a case and click the "Start Monitoring" button to begin tracking
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Summary Stats */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      <div className="bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-blue-600 dark:text-blue-400 font-medium">Active Monitors</p>
                            <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">{monitoredCasesList.length}</p>
                          </div>
                          <Bell className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                        </div>
                      </div>
                      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-green-600 font-medium">Auto-Check</p>
                            <p className="text-2xl font-bold text-green-900">Every 30s</p>
                          </div>
                          <Clock className="h-8 w-8 text-green-600" />
                        </div>
                      </div>
                      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-purple-600 font-medium">Status</p>
                            <p className="text-2xl font-bold text-purple-900">Active</p>
                          </div>
                          <CheckCircle className="h-8 w-8 text-purple-600" />
                        </div>
                      </div>
                    </div>

                    {/* Monitored Cases List */}
                    <div className="space-y-3">
                      {monitoredCasesList.map((caseInfo) => (
                        <div
                          key={caseInfo.docket_id}
                          className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <Bell className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />
                                <h3 className="font-semibold text-gray-900">
                                  {caseInfo.case_name || `Case ${caseInfo.docket_id}`}
                                </h3>
                              </div>

                              <div className="grid grid-cols-2 gap-3 text-sm ml-8">
                                <div>
                                  <span className="text-gray-500 dark:text-slate-400">Docket Number:</span>
                                  <span className="ml-2 font-medium">{caseInfo.docket_number || 'N/A'}</span>
                                </div>
                                <div>
                                  <span className="text-gray-500 dark:text-slate-400">Court:</span>
                                  <span className="ml-2 font-medium uppercase">{caseInfo.court || 'N/A'}</span>
                                </div>
                                {caseInfo.date_filed && (
                                  <div>
                                    <span className="text-gray-500 dark:text-slate-400">Filed:</span>
                                    <span className="ml-2 font-medium">
                                      {new Date(caseInfo.date_filed).toLocaleDateString()}
                                    </span>
                                  </div>
                                )}
                                <div>
                                  <span className="text-gray-500 dark:text-slate-400">Monitoring since:</span>
                                  <span className="ml-2 font-medium">
                                    {caseInfo.started_monitoring
                                      ? new Date(caseInfo.started_monitoring).toLocaleDateString()
                                      : 'N/A'}
                                  </span>
                                </div>
                              </div>

                              {caseInfo.absolute_url && (
                                <div className="mt-3 ml-8">
                                  <a
                                    href={`https://www.courtlistener.com${caseInfo.absolute_url}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
                                  >
                                    <ExternalLink className="h-3 w-3" />
                                    View on CourtListener
                                  </a>
                                </div>
                              )}
                            </div>

                            <div className="flex flex-col gap-2">
                              <Badge variant="secondary" className="whitespace-nowrap">
                                <Clock className="h-3 w-3 mr-1" />
                                {caseInfo.monitoring_duration_hours}h
                              </Badge>
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleRemoveMonitoring(caseInfo.docket_id, caseInfo.case_name || `Case ${caseInfo.docket_id}`)}
                                className="whitespace-nowrap"
                              >
                                <Trash2 className="h-4 w-4 mr-1" />
                                Stop
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        ) : (
          <TabsContent value="monitoring">
            <Card>
              <CardContent className="pt-12 pb-12 text-center">
                <Lock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Login Required</h3>
                <p className="text-gray-600 dark:text-slate-300 mb-6">
                  Please log in to view and manage your monitored cases.
                </p>
                <Button onClick={() => router.push('/login')}>
                  Log In
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Downloaded Documents Tab */}
        <TabsContent value="downloaded">
          <Card>
            <CardHeader>
              <CardTitle>Downloaded Documents</CardTitle>
              <CardDescription>
                Documents downloaded directly to app storage and ready for analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              {downloadedDocs.length === 0 ? (
                <div className="text-center py-12">
                  <Download className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-700 mb-2">
                    No Documents Downloaded Yet
                  </h3>
                  <p className="text-gray-500 dark:text-slate-400 mb-4">
                    Downloaded documents will appear here and be stored in app storage
                  </p>
                  <p className="text-sm text-gray-400">
                    Search for cases and click "Download to App" on FREE documents
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {downloadedDocs.map((doc, idx) => (
                    <div
                      key={idx}
                      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                    >
                      {/* Document Header with PACER-standard info */}
                      <DocumentHeaderCompact
                        caseNumber={doc.original_doc?.case_number || doc.case_number}
                        court={doc.original_doc?.court || doc.court}
                        documentType={doc.original_doc?.short_description || doc.original_doc?.description || 'Court Document'}
                        documentNumber={doc.original_doc?.entry_number || doc.original_doc?.document_number}
                        filingDate={doc.original_doc?.entry_date_filed}
                        source={doc.source || 'CourtListener'}
                        sourceUrl={doc.original_doc?.filepath_local ? `https://www.courtlistener.com${doc.original_doc.filepath_local}` : undefined}
                        className="mb-3"
                      />

                      {/* Status Badges */}
                      <div className="flex items-center gap-2 mb-3 flex-wrap">
                        <Badge className="bg-green-500 text-white">Downloaded</Badge>
                        {isDocumentAnalyzed(doc.document_id) ? (
                          <Badge className="bg-purple-500 text-white">Analyzed</Badge>
                        ) : analyzingDocs.has(`recap_${doc.document_id}`) ? (
                          <Badge className="bg-blue-500 text-white animate-pulse">Analyzing...</Badge>
                        ) : (
                          <Badge variant="outline" className="text-gray-500 border-gray-300">Not Analyzed</Badge>
                        )}
                      </div>

                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="grid grid-cols-2 gap-3 text-sm">
                            <div>
                              <span className="text-gray-500 dark:text-slate-400">File Size:</span>
                              <span className="ml-2 font-medium">{(doc.file_size / 1024).toFixed(1)} KB</span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-slate-400">Pages:</span>
                              <span className="ml-2 font-medium">{doc.page_count || 'N/A'}</span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-slate-400">Downloaded:</span>
                              <span className="ml-2 font-medium">
                                {new Date(doc.downloaded_at).toLocaleString()}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-500 dark:text-slate-400">Filename:</span>
                              <span className="ml-2 font-medium text-xs font-mono">{doc.standardized_filename || 'document.pdf'}</span>
                            </div>
                          </div>

                          <div className="mt-3 ml-8 flex gap-2">
                            {isDocumentAnalyzed(doc.document_id) ? (
                              // Already analyzed - show success state
                              <Button
                                size="sm"
                                disabled
                                className="bg-purple-50 text-purple-700 border border-purple-300 cursor-default"
                              >
                                <CheckCircle className="h-3 w-3 mr-1" />
                                Already Analyzed
                              </Button>
                            ) : analyzingDocs.has(`recap_${doc.document_id}`) ? (
                              // Currently analyzing
                              <Button
                                size="sm"
                                disabled
                                className="bg-blue-50 text-blue-700 border border-blue-300"
                              >
                                <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                                Analyzing...
                              </Button>
                            ) : (
                              // Not yet analyzed - show analyze button
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:text-blue-300"
                                onClick={() => handleAnalyzeDocument(doc)}
                              >
                                <FileText className="h-3 w-3 mr-1" />
                                Analyze Document
                              </Button>
                            )}
                            {isDocumentAnalyzed(doc.document_id) && (
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-purple-600 hover:text-purple-700"
                                onClick={() => {
                                  // Switch to analysis tab
                                  const analysisTab = document.querySelector('[data-value="analysis"]') as HTMLElement;
                                  if (analysisTab) analysisTab.click();
                                }}
                              >
                                <Scale className="h-3 w-3 mr-1" />
                                View Analysis
                              </Button>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* Summary */}
                  <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        <span className="text-sm font-medium text-green-900">
                          {downloadedDocs.length} document{downloadedDocs.length !== 1 ? 's' : ''} downloaded to app storage
                        </span>
                      </div>
                      <span className="text-sm text-green-700">
                        Total saved: ${downloadedDocs.reduce((sum, doc) => sum + (doc.cost || 0), 0).toFixed(2)} (All FREE)
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Stats Tab */}
        <TabsContent value="stats">
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader>
                  <CardTitle>Usage Statistics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-slate-300">Total Searches:</span>
                    <span className="font-semibold">{stats.usage.total_searches}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-slate-300">Total Downloads:</span>
                    <span className="font-semibold">{stats.usage.total_downloads}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-slate-300">Total Cost:</span>
                    <span className="font-semibold">${stats.usage.total_cost.toFixed(2)}</span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Cost Limits</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600 dark:text-slate-300">Daily Spending:</span>
                      <span className="text-sm font-semibold">
                        ${stats.limits.daily_spending.toFixed(2)} / ${stats.limits.daily_limit.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{width: `${(stats.limits.daily_spending / stats.limits.daily_limit) * 100}%`}}
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between mb-1">
                      <span className="text-sm text-gray-600 dark:text-slate-300">Monthly Spending:</span>
                      <span className="text-sm font-semibold">
                        ${stats.limits.monthly_spending.toFixed(2)} / ${stats.limits.monthly_limit.toFixed(2)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{width: `${(stats.limits.monthly_spending / stats.limits.monthly_limit) * 100}%`}}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle>Recent Searches</CardTitle>
                </CardHeader>
                <CardContent>
                  {stats.recent_searches.length > 0 ? (
                    <div className="space-y-2">
                      {stats.recent_searches.map((search) => (
                        <div key={search.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                          <div>
                            <Badge variant="outline">{search.type}</Badge>
                            <span className="ml-2 text-sm">{search.court || 'All courts'}</span>
                            <span className="ml-2 text-sm text-gray-500 dark:text-slate-400">
                              {search.results_count} results
                            </span>
                          </div>
                          <span className="text-xs text-gray-500 dark:text-slate-400">
                            {new Date(search.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 dark:text-slate-400 text-center py-4">No recent searches</p>
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis">
          {documents.length > 0 ? (
            <div className="space-y-4">
              {/* Document List */}
              <Card>
                <CardHeader>
                  <CardTitle>Analyzed Documents ({documents.length})</CardTitle>
                  <CardDescription>Click on a document to view its analysis</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                          currentDocument?.id === doc.id
                            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30 dark:border-blue-400'
                            : 'border-gray-200 dark:border-slate-600 hover:border-blue-300 dark:hover:border-blue-500 dark:bg-slate-700'
                        }`}
                        onClick={() => setCurrentDocument(doc)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                            <div>
                              <p className="font-semibold text-gray-900 dark:text-slate-100">{doc.fileName}</p>
                              <p className="text-sm text-gray-600 dark:text-slate-300">
                                {doc.uploadDate.toLocaleString()}
                              </p>
                            </div>
                          </div>
                          {currentDocument?.id === doc.id && (
                            <CheckCircle className="w-5 h-5 text-green-600" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Current Document Analysis */}
              {currentDocument && (
                <Card>
                  <CardHeader>
                    <CardTitle>Document Analysis: {currentDocument.fileName}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Comprehensive Summary */}
                    {currentDocument.summary && (
                      <div>
                        <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                          <FileText className="w-6 h-6 text-teal-600 dark:text-teal-400" />
                          Comprehensive Summary
                        </h3>
                        <div className="text-slate-800 dark:text-slate-200 bg-teal-50 dark:bg-teal-900/30 p-5 rounded-lg border-l-4 border-teal-500 border dark:border-teal-600 leading-relaxed">
                          <p className="text-base whitespace-pre-line">
                            {currentDocument.summary}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Plain English Summary */}
                    {(currentDocument as any).plainEnglishSummary && (
                      <div>
                        <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                          <Scale className="w-6 h-6 text-green-600 dark:text-green-400" />
                          In Plain English
                        </h3>
                        <div className="text-slate-800 dark:text-slate-200 bg-green-50 dark:bg-green-900/30 p-5 rounded-lg border-l-4 border-green-500 border dark:border-green-600 leading-relaxed">
                          <p className="text-base">{(currentDocument as any).plainEnglishSummary}</p>
                        </div>
                      </div>
                    )}

                    {/* Factual Background */}
                    {(currentDocument as any).factual_background && (
                      <div>
                        <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                          <FileText className="w-6 h-6 text-slate-600 dark:text-teal-400" />
                          Factual Background
                        </h3>
                        <div className="text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-slate-700 p-5 rounded-lg border-l-4 border-slate-500 dark:border-teal-500 border dark:border-slate-600">
                          <p className="text-base whitespace-pre-line">
                            {(currentDocument as any).factual_background}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Immediate Actions Required */}
                    {(currentDocument as any).immediate_actions && (currentDocument as any).immediate_actions.length > 0 && (
                      <div>
                        <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                          <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
                          Immediate Actions Required
                        </h3>
                        <div className="bg-red-50 dark:bg-red-900/30 p-5 rounded-lg border-l-4 border-red-500 border dark:border-red-600">
                          <ul className="space-y-3">
                            {(currentDocument as any).immediate_actions.map((action: string, index: number) => (
                              <li key={index} className="text-slate-800 dark:text-slate-200 flex items-start gap-3">
                                <span className="flex-shrink-0 w-6 h-6 bg-red-600 dark:bg-red-500 text-white rounded-full flex items-center justify-center font-bold text-sm mt-0.5">
                                  {index + 1}
                                </span>
                                <span className="flex-1 text-base">{action}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}

                    {/* Relief Requested */}
                    {(currentDocument as any).relief_requested && (
                      <div>
                        <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                          <Scale className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                          Relief/Remedies Requested
                        </h3>
                        <div className="text-slate-800 dark:text-slate-200 bg-purple-50 dark:bg-purple-900/30 p-5 rounded-lg border-l-4 border-purple-500 border dark:border-purple-600">
                          <p className="text-base whitespace-pre-line">
                            {(currentDocument as any).relief_requested}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Potential Risks */}
                    {(currentDocument as any).potential_risks && (currentDocument as any).potential_risks.length > 0 && (
                      <div>
                        <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                          <AlertTriangle className="w-6 h-6 text-orange-600 dark:text-orange-400" />
                          Potential Legal Risks
                        </h3>
                        <div className="bg-orange-50 dark:bg-orange-900/30 p-5 rounded-lg border-l-4 border-orange-500 border dark:border-orange-600">
                          <ul className="space-y-2">
                            {(currentDocument as any).potential_risks.map((risk: string, index: number) => (
                              <li key={index} className="text-slate-800 dark:text-slate-200 flex items-start gap-2">
                                <span className="w-2 h-2 bg-orange-600 dark:bg-orange-400 rounded-full mt-2 flex-shrink-0"></span>
                                <span className="flex-1 text-base">{risk}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    )}

                    {/* Procedural Status */}
                    {(currentDocument as any).procedural_status && (
                      <div>
                        <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                          <FileText className="w-6 h-6 text-teal-600 dark:text-teal-400" />
                          Procedural Status
                        </h3>
                        <div className="text-slate-800 dark:text-slate-200 bg-teal-50 dark:bg-teal-900/30 p-5 rounded-lg border-l-4 border-teal-500 border dark:border-teal-600">
                          <p className="text-base whitespace-pre-line">
                            {(currentDocument as any).procedural_status}
                          </p>
                        </div>
                      </div>
                    )}

                    {/* Parties */}
                    {currentDocument.parties && currentDocument.parties.length > 0 && (
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <Users className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                          Parties Involved
                        </h3>
                        <div className="bg-purple-50 dark:bg-purple-900/30 p-4 rounded-lg border-l-4 border-purple-500 border dark:border-purple-600">
                          <ul className="space-y-1">
                            {currentDocument.parties.map((party, index) => {
                              const partyName = typeof party === 'string'
                                ? party
                                : (party as any)?.name || String(party);
                              const partyRole = typeof party === 'object' && (party as any)?.role
                                ? ` (${(party as any).role})`
                                : '';
                              return (
                                <li key={index} className="text-slate-700 dark:text-slate-200 flex items-center gap-2">
                                  <span className="w-2 h-2 bg-purple-600 dark:bg-purple-400 rounded-full"></span>
                                  {partyName}{partyRole}
                                </li>
                              );
                            })}
                          </ul>
                        </div>
                      </div>
                    )}

                    {/* Important Dates - Enhanced with WHY explanations */}
                    {currentDocument.importantDates && currentDocument.importantDates.length > 0 && (
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <Calendar className="w-5 h-5 text-green-600 dark:text-green-400" />
                          Important Dates & Why They Matter
                        </h3>
                        <div className="bg-green-50 dark:bg-green-900/30 p-4 rounded-lg border-l-4 border-green-500 border dark:border-green-600 space-y-4">
                          {currentDocument.importantDates.map((dateInfo: any, index: number) => {
                            const isUrgent = dateInfo.urgency === 'high' || dateInfo.urgency === 'HIGH' || dateInfo.urgency === 'CRITICAL' || dateInfo.consequence;
                            return (
                              <div key={index} className="border-b border-green-300 dark:border-green-700 pb-4 last:border-0 last:pb-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className={`font-bold text-lg ${isUrgent ? 'text-red-900 dark:text-red-200' : 'text-green-900 dark:text-green-200'}`}>
                                    {dateInfo.date}
                                  </span>
                                  {isUrgent && (
                                    <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded-full flex items-center gap-1">
                                      <AlertTriangle className="w-3 h-3" />
                                      CRITICAL
                                    </span>
                                  )}
                                </div>
                                <p className="text-slate-800 dark:text-slate-200 font-medium">{dateInfo.description}</p>
                                {dateInfo.why_important && (
                                  <div className="mt-2 flex items-start gap-2">
                                    <span className="px-2 py-0.5 bg-blue-200 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 text-xs font-bold rounded">WHY</span>
                                    <p className="text-sm text-slate-700 dark:text-slate-300">{dateInfo.why_important}</p>
                                  </div>
                                )}
                                {dateInfo.action_required && (
                                  <div className="mt-2 flex items-start gap-2">
                                    <span className="px-2 py-0.5 bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200 text-xs font-bold rounded">ACTION</span>
                                    <p className="text-sm text-slate-700 dark:text-slate-300">{dateInfo.action_required}</p>
                                  </div>
                                )}
                                {dateInfo.consequence && (
                                  <div className="mt-2 flex items-start gap-2">
                                    <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded">RISK</span>
                                    <p className="text-sm text-red-700 dark:text-red-300 font-medium">{dateInfo.consequence}</p>
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Key Figures - Enhanced with disputed amounts */}
                    {currentDocument.keyFigures && currentDocument.keyFigures.length > 0 && (
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <DollarSign className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                          Financial Amounts
                        </h3>
                        <div className="bg-amber-50 dark:bg-amber-900/30 p-4 rounded-lg border-l-4 border-amber-500 border dark:border-amber-600 space-y-4">
                          {currentDocument.keyFigures.map((figure: any, index: number) => (
                            <div key={index} className={`border-b border-amber-300 dark:border-amber-700 pb-4 last:border-0 last:pb-0 ${figure.disputed ? 'bg-red-50/50 dark:bg-red-900/20 -mx-4 px-4 py-2 first:rounded-t-lg last:rounded-b-lg' : ''}`}>
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className="text-slate-700 dark:text-slate-300">{figure.label}:</span>
                                  {figure.disputed && (
                                    <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded-full flex items-center gap-1">
                                      <AlertTriangle className="w-3 h-3" />
                                      DISPUTED
                                    </span>
                                  )}
                                </div>
                                <span className={`font-bold text-lg ${figure.disputed ? 'text-red-900 dark:text-red-200' : 'text-amber-900 dark:text-amber-200'}`}>
                                  {figure.value}
                                </span>
                              </div>
                              {figure.dispute_reason && (
                                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                                  <span className="font-semibold">Dispute reason:</span> {figure.dispute_reason}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Key Legal Arguments */}
                    {/* Key Legal Arguments - with safe array handling */}
                    {Array.isArray((currentDocument as any).keyArguments) && (currentDocument as any).keyArguments.length > 0 && (
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <Scale className="w-5 h-5 text-slate-600 dark:text-teal-400" />
                          Key Legal Arguments
                        </h3>
                        <div className="bg-slate-100 dark:bg-slate-700 p-4 rounded-lg border-l-4 border-slate-500 dark:border-teal-500 border dark:border-slate-500 space-y-3">
                          {(currentDocument as any).keyArguments.map((arg: any, index: number) => (
                            <div key={index} className="border-b border-slate-300 dark:border-slate-600 pb-3 last:border-0 last:pb-0">
                              <div className="flex items-start gap-2">
                                <span className="bg-slate-600 dark:bg-teal-600 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                                  {index + 1}
                                </span>
                                <div className="flex-1">
                                  <p className="text-slate-800 dark:text-slate-200 font-medium">
                                    {typeof arg === 'object' ? (arg.argument || arg.description || JSON.stringify(arg)) : String(arg)}
                                  </p>
                                  {arg?.supporting_evidence && (
                                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                                      <span className="font-semibold">Evidence:</span> {arg.supporting_evidence}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Critical Deadlines */}
                    {(currentDocument as any).deadlines && (currentDocument as any).deadlines.length > 0 && (
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                          Critical Deadlines
                        </h3>
                        <div className="space-y-2">
                          {(currentDocument as any).deadlines.map((deadline: any, index: number) => (
                            <div key={index} className="p-4 rounded-lg border-l-4 border-red-500 bg-red-50 dark:bg-red-900/30 border dark:border-red-600">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="font-bold text-lg text-red-900 dark:text-red-200">{deadline.deadline || deadline.date}</span>
                                {(deadline.urgency === 'high' || deadline.urgency === 'HIGH' || deadline.urgency === 'CRITICAL') && (
                                  <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded-full">URGENT</span>
                                )}
                              </div>
                              <p className="text-slate-800 dark:text-slate-200 font-medium">{deadline.action_required || deadline.description}</p>
                              {(deadline.consequence_if_missed || deadline.consequence) && (
                                <div className="mt-2 flex items-start gap-2">
                                  <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded">IF MISSED</span>
                                  <p className="text-sm text-red-700 dark:text-red-300 font-medium">{deadline.consequence_if_missed || deadline.consequence}</p>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Keywords */}
                    {currentDocument.keywords && currentDocument.keywords.length > 0 && (
                      <div>
                        <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                          <Tag className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                          Keywords & Terms
                        </h3>
                        <div className="bg-indigo-50 dark:bg-indigo-900/30 p-4 rounded-lg border-l-4 border-indigo-500 border dark:border-indigo-600">
                          <div className="flex flex-wrap gap-2">
                            {currentDocument.keywords.map((keyword: any, index: number) => (
                              <span
                                key={index}
                                className="px-3 py-1 bg-indigo-200 dark:bg-indigo-800 text-indigo-900 dark:text-indigo-200 rounded-full text-sm font-medium"
                                title={typeof keyword === 'object' && keyword?.explanation ? keyword.explanation : undefined}
                              >
                                {typeof keyword === 'object' ? (keyword?.term || keyword?.name || JSON.stringify(keyword)) : keyword}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card>
              <CardContent className="py-16 text-center">
                <FileText className="w-20 h-20 text-gray-400 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-700 dark:text-slate-200 mb-2">No Analyzed Documents</h3>
                <p className="text-gray-600 dark:text-slate-300 mb-6">
                  Download and analyze documents from the "Downloaded" tab to see them here
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Stop Monitoring Confirmation Dialog */}
      <Dialog
        open={confirmStopDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setConfirmStopDialog({ open: false, docketId: null, caseName: '' });
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <BellOff className="w-5 h-5" />
              Stop Monitoring Case?
            </DialogTitle>
            <DialogDescription className="pt-2">
              Are you sure you want to stop monitoring{' '}
              <span className="font-semibold text-gray-900">{confirmStopDialog.caseName}</span>?
            </DialogDescription>
          </DialogHeader>
          <div className="mt-4 p-4 bg-amber-50 border border-amber-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-amber-800">
                <p className="font-medium mb-1">You will no longer receive:</p>
                <ul className="list-disc list-inside space-y-1">
                  <li>Email notifications for new filings</li>
                  <li>Real-time alerts about case updates</li>
                  <li>Automatic document downloads (if enabled)</li>
                </ul>
              </div>
            </div>
          </div>
          <div className="mt-6 flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => setConfirmStopDialog({ open: false, docketId: null, caseName: '' })}
            >
              Cancel
            </Button>
            <Button
              className="bg-red-600 hover:bg-red-700 text-white"
              onClick={confirmStopMonitoring}
            >
              <BellOff className="w-4 h-4 mr-2" />
              Stop Monitoring
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Start Monitoring Confirmation Dialog with Explanation */}
      <Dialog
        open={confirmStartDialog.open}
        onOpenChange={(open) => {
          if (!open) {
            setConfirmStartDialog({ open: false, docketId: null, caseName: '', caseData: null });
          }
        }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-blue-600">
              <Eye className="w-5 h-5" />
              Start Monitoring Case?
            </DialogTitle>
            <DialogDescription className="pt-2">
              Monitor{' '}
              <span className="font-semibold text-gray-900 dark:text-gray-100">{confirmStartDialog.caseName}</span>{' '}
              for new filings and updates.
            </DialogDescription>
          </DialogHeader>

          {/* How it works explanation */}
          <div className="mt-4 space-y-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg">
              <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-2 flex items-center gap-2">
                <Bell className="w-4 h-4" />
                How Case Monitoring Works
              </h4>
              <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">1.</span>
                  <span>We check for new documents every 15 minutes</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">2.</span>
                  <span>You receive email notifications when new filings appear</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 font-bold">3.</span>
                  <span>Real-time alerts show up in your dashboard</span>
                </li>
              </ul>
            </div>

            <div className="p-4 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg">
              <h4 className="font-medium text-amber-900 dark:text-amber-100 mb-2 flex items-center gap-2">
                <Download className="w-4 h-4" />
                Auto-Download Documents
              </h4>
              <ul className="text-sm text-amber-800 dark:text-amber-200 space-y-2">
                <li className="flex items-start gap-2">
                  <span className="text-green-600">&#10003;</span>
                  <span><strong>Free documents</strong> from RECAP/Internet Archive are always downloaded at no cost</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-amber-600">$</span>
                  <span><strong>Paid PACER documents</strong> will download automatically within your monthly budget (default $10/month)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600">&#9881;</span>
                  <span>You can adjust budget or enable &quot;free only&quot; mode in Settings after monitoring starts</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="mt-6 flex justify-end gap-3">
            <Button
              variant="outline"
              onClick={() => setConfirmStartDialog({ open: false, docketId: null, caseName: '', caseData: null })}
            >
              Cancel
            </Button>
            <Button
              className="bg-blue-600 hover:bg-blue-700 text-white"
              onClick={confirmStartMonitoring}
            >
              <Eye className="w-4 h-4 mr-2" />
              Start Monitoring
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
