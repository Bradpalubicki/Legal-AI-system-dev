'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '@/components/design-system';
import { useAuth } from '@/hooks/useAuth';
import { API_CONFIG } from '../../config/api';
import {
  FileText, Calendar, AlertCircle, CheckCircle, Link as LinkIcon,
  Download, RefreshCw, Eye, EyeOff, Bell, BellOff, ExternalLink,
  Clock, Mail, Activity, TrendingUp, Inbox, Settings, DollarSign,
  ChevronDown, ChevronUp
} from 'lucide-react';
import { toast } from 'sonner';

interface PACERDocument {
  document_number: string;
  description: string;
  filed_date: string;
  party: string;
  document_url?: string;
}

interface CaseData {
  case_number: string;
  case_name: string;
  court: string;
  filing_date: string;
  status: string;
  next_hearing?: string;
  pacer_documents?: PACERDocument[];
}

interface MonitoredCase {
  docket_id: number;
  case_name: string;
  docket_number: string;
  court: string;
  date_filed: string;
  absolute_url: string;
  last_checked: string;
  started_monitoring: string;
  monitoring_duration_hours: number;
}

interface DocumentInfo {
  entry_number?: number;
  document_number?: number;
  description?: string;
  entry_date_filed?: string;
  is_free_on_pacer?: boolean;
}

interface NotificationHistory {
  id: number;
  docket_id: number;
  case_name: string;
  notification_type: string;
  document_count: number;
  documents?: DocumentInfo[];
  created_at: string;
  sent_at: string;
  websocket_sent: boolean;
  email_sent: boolean;
  email_to?: string;
  email_error?: string;
}

interface AutoDownloadSettings {
  auto_download_enabled: boolean;
  auto_download_free_only: boolean;
  pacer_download_budget: number;
  pacer_spent_this_month: number;
}

interface DownloadHistoryItem {
  id: number;
  document_id: number;
  docket_id: number;
  description?: string;
  document_number?: number;
  source: string;
  status: string;
  page_count?: number;
  cost: number;
  file_name?: string;
  created_at: string;
  downloaded_at?: string;
  error_message?: string;
}

interface NotificationStats {
  total_notifications: number;
  websocket_success_rate: number;
  email_success_rate: number;
  total_documents_notified: number;
}

export function EnhancedCaseTracker() {
  const { isAuthenticated, user } = useAuth();
  const [cases, setCases] = useState<CaseData[]>([]);
  const [selectedCase, setSelectedCase] = useState<CaseData | null>(null);
  const [pacerConnected, setPacerConnected] = useState(false);
  const [pacerUsername, setPacerUsername] = useState('');
  const [pacerPassword, setPacerPassword] = useState('');
  const [showPacerPassword, setShowPacerPassword] = useState(false);
  const [showPacerSetup, setShowPacerSetup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // CourtListener monitoring state
  const [monitoredCases, setMonitoredCases] = useState<MonitoredCase[]>([]);
  const [notificationHistory, setNotificationHistory] = useState<NotificationHistory[]>([]);
  const [notificationStats, setNotificationStats] = useState<NotificationStats | null>(null);
  const [loadingMonitored, setLoadingMonitored] = useState(false);
  const [checkingUpdates, setCheckingUpdates] = useState(false);

  // Auto-download state
  const [expandedCaseSettings, setExpandedCaseSettings] = useState<number | null>(null);
  const [autoDownloadSettings, setAutoDownloadSettings] = useState<Record<number, AutoDownloadSettings>>({});
  const [downloadHistory, setDownloadHistory] = useState<DownloadHistoryItem[]>([]);
  const [savingAutoDownload, setSavingAutoDownload] = useState<number | null>(null);

  useEffect(() => {
    loadCases();
    checkPacerConnection();
    // Only load monitoring data if authenticated
    if (isAuthenticated) {
      loadMonitoredCases();
      loadNotifications();
      loadDownloadHistory();
    }
  }, [isAuthenticated]);

  // Re-fetch user-specific data when user ID changes
  useEffect(() => {
    if (user?.id) {
      // Clear ALL user-specific data when switching users
      setMonitoredCases([]);
      setNotificationHistory([]);
      setNotificationStats(null);
      setDownloadHistory([]);
      // Re-fetch for the new user
      loadMonitoredCases();
      loadNotifications();
      loadDownloadHistory();
    } else if (!user) {
      // Clear all data when logged out
      setMonitoredCases([]);
      setNotificationHistory([]);
      setNotificationStats(null);
      setDownloadHistory([]);
    }
  }, [user?.id]);

  const loadMonitoredCases = async (retryOnAuth = true) => {
    setLoadingMonitored(true);
    try {
      const token = localStorage.getItem('accessToken');  // Fixed: use camelCase to match login
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/monitor/list`, {
        headers,
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        console.log('[Monitored Cases] Loaded from API:', data);
        setMonitoredCases(data.monitored_cases || []);
      } else if (response.status === 401 && retryOnAuth) {
        // Token might be expired, try to refresh it
        console.log('[Monitored Cases] Token expired, attempting refresh...');
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          try {
            const refreshResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/auth/refresh`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh_token: refreshToken })
            });
            if (refreshResponse.ok) {
              const refreshData = await refreshResponse.json();
              localStorage.setItem('accessToken', refreshData.access_token);
              if (refreshData.refresh_token) {
                localStorage.setItem('refreshToken', refreshData.refresh_token);
              }
              console.log('[Monitored Cases] Token refreshed, retrying...');
              // Retry the request with new token (don't retry again on auth failure)
              return loadMonitoredCases(false);
            }
          } catch (refreshError) {
            console.error('[Monitored Cases] Token refresh failed:', refreshError);
          }
        }
        console.error('Failed to load monitored cases: Unauthorized');
        setMonitoredCases([]);
      } else {
        console.error('Failed to load monitored cases:', response.status);
        setMonitoredCases([]);
      }
    } catch (error) {
      console.error('Failed to load monitored cases:', error);
      setMonitoredCases([]);
    } finally {
      setLoadingMonitored(false);
    }
  };

  const loadNotifications = async (retryOnAuth = true) => {
    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Load notification history
      const historyResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/notifications/history?limit=10`, {
        headers
      });

      if (historyResponse.status === 401 && retryOnAuth) {
        // Token might be expired, try to refresh it
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          try {
            const refreshResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/auth/refresh`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh_token: refreshToken })
            });
            if (refreshResponse.ok) {
              const refreshData = await refreshResponse.json();
              localStorage.setItem('accessToken', refreshData.access_token);
              if (refreshData.refresh_token) {
                localStorage.setItem('refreshToken', refreshData.refresh_token);
              }
              return loadNotifications(false);
            }
          } catch (refreshError) {
            console.error('[Notifications] Token refresh failed:', refreshError);
          }
        }
        return;
      }

      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        // Deduplicate notifications by docket_id - keep only the most recent for each case
        const notifications = historyData.notifications || [];
        const seenDockets = new Set<number>();
        const deduped = notifications.filter((n: NotificationHistory) => {
          if (seenDockets.has(n.docket_id)) {
            return false; // Already have a notification for this case (more recent ones come first)
          }
          seenDockets.add(n.docket_id);
          return true;
        });
        setNotificationHistory(deduped);
      }

      // Load notification stats
      const statsResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/notifications/stats?days=30`, {
        headers
      });
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setNotificationStats(statsData);
      }
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const loadDownloadHistory = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/downloads/history?limit=20`, {
        headers
      });

      if (response.ok) {
        const data = await response.json();
        setDownloadHistory(data || []);
      }
    } catch (error) {
      console.error('Failed to load download history:', error);
    }
  };

  const loadAutoDownloadSettings = async (docketId: number) => {
    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/downloads/budget/${docketId}`, {
        headers
      });

      if (response.ok) {
        const data = await response.json();
        setAutoDownloadSettings(prev => ({
          ...prev,
          [docketId]: {
            auto_download_enabled: data.auto_download_enabled || false,
            auto_download_free_only: data.auto_download_free_only ?? true,
            pacer_download_budget: data.budget || 10,
            pacer_spent_this_month: data.spent || 0
          }
        }));
      }
    } catch (error) {
      console.error('Failed to load auto-download settings:', error);
    }
  };

  const updateAutoDownloadSettings = async (
    docketId: number,
    updates: Partial<AutoDownloadSettings>
  ) => {
    setSavingAutoDownload(docketId);
    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/downloads/monitor/${docketId}/auto-download`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({
          auto_download_enabled: updates.auto_download_enabled,
          auto_download_free_only: updates.auto_download_free_only,
          pacer_download_budget: updates.pacer_download_budget
        })
      });

      if (response.ok) {
        const data = await response.json();
        setAutoDownloadSettings(prev => ({
          ...prev,
          [docketId]: {
            auto_download_enabled: data.auto_download_enabled,
            auto_download_free_only: data.auto_download_free_only,
            pacer_download_budget: data.pacer_download_budget,
            pacer_spent_this_month: data.pacer_spent_this_month
          }
        }));
        toast.success('Auto-download settings saved');
      } else {
        toast.error('Failed to save settings');
      }
    } catch (error) {
      console.error('Failed to update auto-download settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSavingAutoDownload(null);
    }
  };

  const toggleCaseSettings = (docketId: number) => {
    if (expandedCaseSettings === docketId) {
      setExpandedCaseSettings(null);
    } else {
      setExpandedCaseSettings(docketId);
      // Load settings for this case if not already loaded
      if (!autoDownloadSettings[docketId]) {
        loadAutoDownloadSettings(docketId);
      }
    }
  };

  const checkForUpdates = async () => {
    setCheckingUpdates(true);
    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/monitor/updates`, {
        headers
      });
      if (response.ok) {
        const data = await response.json();
        if (data.has_updates) {
          alert(`Found updates for ${data.count} case(s)!`);
        } else {
          alert('No new updates found');
        }
        await loadMonitoredCases();
        await loadNotifications();
      }
    } catch (error) {
      console.error('Failed to check for updates:', error);
    } finally {
      setCheckingUpdates(false);
    }
  };

  const stopMonitoring = async (docketId: number) => {
    if (!confirm('Stop monitoring this case?')) return;

    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/courtlistener/monitor/stop/${docketId}`, {
        method: 'POST',
        headers
      });

      if (response.ok) {
        await loadMonitoredCases();
        alert('Stopped monitoring case');
      } else {
        const error = await response.json();
        alert(`Failed to stop monitoring: ${error.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to stop monitoring:', error);
      alert('Failed to stop monitoring. Please try again.');
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const loadCases = async () => {
    try {
      // Load cases from backend with authentication
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/cases/`, { headers });
      if (response.ok) {
        const data = await response.json();
        console.log('[Case Tracking] Loaded cases from API:', data);
        setCases(data.cases || data || []);
      } else {
        console.error('[Case Tracking] Failed to load cases, status:', response.status);
        setCases([]);
      }
    } catch (error) {
      console.error('[Case Tracking] Error loading cases:', error);
      setCases([]);
    }
  };

  const checkPacerConnection = async () => {
    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/credentials/status`, {
        headers
      });
      if (response.ok) {
        const data = await response.json();
        // Check if credentials exist and are verified
        setPacerConnected(data.has_credentials && data.is_verified);
      }
    } catch (error) {
      setPacerConnected(false);
    }
  };

  const connectToPacer = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      // Save credentials first
      const saveResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/credentials`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          pacer_username: pacerUsername,
          pacer_password: pacerPassword,
          environment: 'production',
          daily_limit: 100,
          monthly_limit: 1000
        })
      });

      if (!saveResponse.ok) {
        alert('Failed to save PACER credentials. Please try again.');
        return;
      }

      // Then authenticate
      const authResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/authenticate`, {
        method: 'POST',
        headers
      });

      if (authResponse.ok) {
        setPacerConnected(true);
        setShowPacerSetup(false);
        // Sync cases immediately after connection
        await syncWithPacer();
      } else {
        alert('Failed to authenticate with PACER. Please check your credentials.');
      }
    } catch (error) {
      alert('Error connecting to PACER. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const syncWithPacer = async () => {
    setSyncing(true);
    try {
      const token = localStorage.getItem('accessToken');
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };

      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/case-tracking/pacer/sync`, {
        method: 'POST',
        headers
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Synced ${data.documents_added || 0} new documents from PACER`);
        await loadCases();
      }
    } catch (error) {
      console.error('PACER sync error:', error);
    } finally {
      setSyncing(false);
    }
  };

  const downloadDocument = async (doc: PACERDocument) => {
    if (doc.document_url) {
      window.open(doc.document_url, '_blank');
    } else {
      alert('Document not yet downloaded from PACER. Click "Sync with PACER" to fetch.');
    }
  };

  return (
    <div className="enhanced-case-tracker space-y-6">
      {/* CourtListener Monitoring Dashboard */}
      <Card className="border-blue-200 dark:border-slate-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-teal-600" />
              CourtListener Case Monitoring
            </CardTitle>
            <Button
              onClick={checkForUpdates}
              disabled={checkingUpdates || monitoredCases.length === 0}
              size="sm"
              variant="outline"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${checkingUpdates ? 'animate-spin' : ''}`} />
              {checkingUpdates ? 'Checking...' : 'Check for Updates'}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Stats Overview */}
          {isAuthenticated && notificationStats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-white dark:bg-slate-700 rounded-lg p-4 shadow-sm">
                <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300 mb-1">
                  <Activity className="w-4 h-4" />
                  <span className="text-sm font-medium">Total Notifications</span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{notificationStats.total_notifications}</p>
              </div>
              <div className="bg-white dark:bg-slate-700 rounded-lg p-4 shadow-sm">
                <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300 mb-1">
                  <FileText className="w-4 h-4" />
                  <span className="text-sm font-medium">Documents Tracked</span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">{notificationStats.total_documents_notified}</p>
              </div>
              <div className="bg-white dark:bg-slate-700 rounded-lg p-4 shadow-sm">
                <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300 mb-1">
                  <Bell className="w-4 h-4" />
                  <span className="text-sm font-medium">Alert Success Rate</span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {notificationStats.total_notifications > 0
                    ? `${Math.round((notificationStats.websocket_success_rate || 0) * 100)}%`
                    : 'N/A'}
                </p>
              </div>
              <div className="bg-white dark:bg-slate-700 rounded-lg p-4 shadow-sm">
                <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300 mb-1">
                  <Mail className="w-4 h-4" />
                  <span className="text-sm font-medium">Email Success Rate</span>
                </div>
                <p className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                  {notificationStats.total_notifications > 0
                    ? `${Math.round((notificationStats.email_success_rate || 0) * 100)}%`
                    : 'N/A'}
                </p>
              </div>
            </div>
          )}

          {/* Monitored Cases */}
          {isAuthenticated && (
            <div data-tour="cases-monitored">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                <Eye className="w-4 h-4" />
                Monitored Cases ({monitoredCases.length})
              </h3>
              {loadingMonitored ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-8 h-8 text-slate-400 animate-spin mx-auto mb-2" />
                  <p className="text-slate-600 dark:text-slate-300">Loading monitored cases...</p>
                </div>
              ) : monitoredCases.length > 0 ? (
                <div className="space-y-3">
                  {monitoredCases.map((monitoredCase) => {
                    const settings = autoDownloadSettings[monitoredCase.docket_id];
                    const isExpanded = expandedCaseSettings === monitoredCase.docket_id;
                    const budgetUsedPercent = settings
                      ? (settings.pacer_spent_this_month / settings.pacer_download_budget) * 100
                      : 0;

                    return (
                      <div key={monitoredCase.docket_id} className="bg-white dark:bg-slate-700 rounded-lg shadow-sm border border-slate-200 dark:border-slate-600 overflow-hidden">
                        <div className="p-4">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <h4 className="font-bold text-slate-900 dark:text-slate-100">{monitoredCase.case_name}</h4>
                                <Badge variant="outline" className="text-xs">
                                  {monitoredCase.court.toUpperCase()}
                                </Badge>
                                {settings?.auto_download_enabled && (
                                  <Badge className="text-xs bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 border-teal-200 dark:border-teal-700">
                                    <Download className="w-3 h-3 mr-1" />
                                    Auto-Download
                                  </Badge>
                                )}
                              </div>
                              <div className="space-y-1 text-sm text-slate-600 dark:text-slate-300">
                                <p>Docket: {monitoredCase.docket_number}</p>
                                {monitoredCase.date_filed && (
                                  <p className="flex items-center gap-2">
                                    <Calendar className="w-3 h-3" />
                                    Filed: {new Date(monitoredCase.date_filed).toLocaleDateString()}
                                  </p>
                                )}
                                <p className="flex items-center gap-2">
                                  <Clock className="w-3 h-3" />
                                  Last checked: {formatTimeAgo(monitoredCase.last_checked)}
                                </p>
                                <p className="text-green-600 font-medium">
                                  ✓ Monitoring since {formatTimeAgo(monitoredCase.started_monitoring)}
                                </p>
                              </div>
                            </div>
                            <div className="flex flex-col gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => window.open(`https://www.courtlistener.com${monitoredCase.absolute_url}`, '_blank')}
                              >
                                <ExternalLink className="w-4 h-4 mr-1" />
                                View
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => toggleCaseSettings(monitoredCase.docket_id)}
                                className="text-slate-600 hover:text-slate-700 dark:text-slate-300"
                              >
                                <Settings className="w-4 h-4 mr-1" />
                                {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => stopMonitoring(monitoredCase.docket_id)}
                                className="text-red-600 hover:text-red-700"
                              >
                                <BellOff className="w-4 h-4 mr-1" />
                                Stop
                              </Button>
                            </div>
                          </div>
                        </div>

                        {/* Auto-Download Settings Panel */}
                        {isExpanded && (
                          <div className="border-t border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-800 p-4">
                            <h5 className="font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                              <Download className="w-4 h-4" />
                              Auto-Download Settings
                            </h5>

                            {!settings ? (
                              <div className="flex items-center justify-center py-4">
                                <RefreshCw className="w-5 h-5 text-slate-400 animate-spin" />
                                <span className="ml-2 text-slate-500">Loading settings...</span>
                              </div>
                            ) : (
                              <div className="space-y-4">
                                {/* Enable Auto-Download Toggle */}
                                <div className="flex items-center justify-between">
                                  <div>
                                    <label className="font-medium text-slate-900 dark:text-slate-100">
                                      Auto-download new documents
                                    </label>
                                    <p className="text-sm text-slate-500 dark:text-slate-400">
                                      Automatically download documents when filed
                                    </p>
                                  </div>
                                  <button
                                    onClick={() => updateAutoDownloadSettings(monitoredCase.docket_id, {
                                      ...settings,
                                      auto_download_enabled: !settings.auto_download_enabled
                                    })}
                                    disabled={savingAutoDownload === monitoredCase.docket_id}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                                      settings.auto_download_enabled
                                        ? 'bg-teal-600'
                                        : 'bg-slate-300 dark:bg-slate-600'
                                    } ${savingAutoDownload === monitoredCase.docket_id ? 'opacity-50' : ''}`}
                                  >
                                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                      settings.auto_download_enabled ? 'translate-x-6' : 'translate-x-1'
                                    }`} />
                                  </button>
                                </div>

                                {settings.auto_download_enabled && (
                                  <>
                                    {/* Free Only Checkbox */}
                                    <div className="flex items-center gap-3">
                                      <input
                                        type="checkbox"
                                        id={`free-only-${monitoredCase.docket_id}`}
                                        checked={settings.auto_download_free_only}
                                        onChange={(e) => updateAutoDownloadSettings(monitoredCase.docket_id, {
                                          ...settings,
                                          auto_download_free_only: e.target.checked
                                        })}
                                        disabled={savingAutoDownload === monitoredCase.docket_id}
                                        className="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-teal-600 focus:ring-teal-500"
                                      />
                                      <label
                                        htmlFor={`free-only-${monitoredCase.docket_id}`}
                                        className="text-slate-900 dark:text-slate-100"
                                      >
                                        Only download free documents (RECAP/Internet Archive)
                                      </label>
                                    </div>

                                    {/* PACER Budget (shown when not free-only) */}
                                    {!settings.auto_download_free_only && (
                                      <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg p-4">
                                        <div className="flex items-center gap-2 mb-3">
                                          <DollarSign className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                                          <span className="font-medium text-amber-800 dark:text-amber-200">
                                            PACER Budget (costs $0.10/page)
                                          </span>
                                        </div>

                                        <div className="flex items-center gap-4 mb-3">
                                          <div className="flex-1">
                                            <label className="text-sm text-slate-600 dark:text-slate-300 block mb-1">
                                              Monthly budget limit
                                            </label>
                                            <div className="flex items-center gap-2">
                                              <span className="text-slate-500">$</span>
                                              <input
                                                type="number"
                                                min="0"
                                                max="1000"
                                                step="1"
                                                value={settings.pacer_download_budget}
                                                onChange={(e) => {
                                                  const value = parseFloat(e.target.value) || 0;
                                                  setAutoDownloadSettings(prev => ({
                                                    ...prev,
                                                    [monitoredCase.docket_id]: {
                                                      ...settings,
                                                      pacer_download_budget: value
                                                    }
                                                  }));
                                                }}
                                                onBlur={() => updateAutoDownloadSettings(monitoredCase.docket_id, settings)}
                                                disabled={savingAutoDownload === monitoredCase.docket_id}
                                                className="w-24 px-2 py-1 border border-slate-300 dark:border-slate-600 rounded bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100"
                                              />
                                            </div>
                                          </div>
                                          <div className="text-right">
                                            <p className="text-sm text-slate-600 dark:text-slate-300">Spent this month</p>
                                            <p className="text-lg font-bold text-slate-900 dark:text-slate-100">
                                              ${settings.pacer_spent_this_month.toFixed(2)}
                                            </p>
                                          </div>
                                        </div>

                                        {/* Budget Progress Bar */}
                                        <div className="relative h-2 bg-slate-200 dark:bg-slate-600 rounded-full overflow-hidden">
                                          <div
                                            className={`absolute inset-y-0 left-0 rounded-full transition-all ${
                                              budgetUsedPercent >= 90 ? 'bg-red-500' :
                                              budgetUsedPercent >= 80 ? 'bg-amber-500' :
                                              'bg-teal-500'
                                            }`}
                                            style={{ width: `${Math.min(budgetUsedPercent, 100)}%` }}
                                          />
                                        </div>
                                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                          ${(settings.pacer_download_budget - settings.pacer_spent_this_month).toFixed(2)} remaining
                                        </p>

                                        {budgetUsedPercent >= 80 && (
                                          <div className={`mt-2 p-2 rounded text-sm ${
                                            budgetUsedPercent >= 90
                                              ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                                              : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                                          }`}>
                                            <AlertCircle className="w-4 h-4 inline mr-1" />
                                            {budgetUsedPercent >= 90
                                              ? 'Budget nearly exhausted! PACER downloads may be skipped.'
                                              : 'Budget is running low. Consider increasing the limit.'}
                                          </div>
                                        )}
                                      </div>
                                    )}
                                  </>
                                )}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8 bg-white dark:bg-slate-800 rounded-lg border-2 border-dashed border-slate-300 dark:border-slate-600">
                  <Bell className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                  <p className="text-slate-600 dark:text-slate-300 font-medium mb-2">No cases being monitored</p>
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                    Go to PACER Search tab to search and monitor court cases
                  </p>
                  <Button
                    onClick={() => window.location.href = '/?tab=pacer'}
                    size="sm"
                  >
                    Go to PACER Search
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Recent Notifications */}
          {isAuthenticated && notificationHistory.length > 0 && (
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                <Inbox className="w-4 h-4" />
                Recent Notifications
              </h3>
              <div className="space-y-2">
                {notificationHistory.slice(0, 5).map((notification) => (
                  <div key={notification.id} className="bg-white dark:bg-slate-700 rounded-lg p-3 shadow-sm border border-slate-200 dark:border-slate-600">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <p className="font-medium text-slate-900 dark:text-slate-100">{notification.case_name}</p>
                        <p className="text-sm text-slate-600 dark:text-slate-300 mt-1">
                          {notification.document_count} new document{notification.document_count > 1 ? 's' : ''} filed
                        </p>
                        {/* Document numbers from CourtListener */}
                        {notification.documents && notification.documents.length > 0 && (
                          <div className="mt-2 text-xs text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800 rounded p-2">
                            <span className="font-medium">Document{notification.documents.length > 1 ? 's' : ''}: </span>
                            {notification.documents.slice(0, 5).map((doc, idx) => (
                              <span key={idx}>
                                {doc.entry_number ? `#${doc.entry_number}` : doc.document_number ? `Doc ${doc.document_number}` : 'Document'}
                                {doc.description && ` - ${doc.description.slice(0, 40)}${doc.description.length > 40 ? '...' : ''}`}
                                {idx < Math.min(notification.documents!.length, 5) - 1 && '; '}
                              </span>
                            ))}
                            {notification.documents.length > 5 && (
                              <span className="text-slate-400"> +{notification.documents.length - 5} more</span>
                            )}
                          </div>
                        )}
                        <div className="flex items-center gap-3 mt-2 flex-wrap">
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            {formatTimeAgo(notification.sent_at || notification.created_at)}
                          </span>
                          {notification.websocket_sent && (
                            <Badge variant="outline" className="text-xs">
                              <Bell className="w-3 h-3 mr-1" />
                              Alert Sent
                            </Badge>
                          )}
                          {notification.email_sent && notification.email_to && (
                            <Badge variant="outline" className="text-xs bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700 text-green-700 dark:text-green-300">
                              <Mail className="w-3 h-3 mr-1" />
                              Email → {notification.email_to}
                            </Badge>
                          )}
                          {notification.email_sent && !notification.email_to && (
                            <Badge variant="outline" className="text-xs">
                              <Mail className="w-3 h-3 mr-1" />
                              Email Sent
                            </Badge>
                          )}
                          {notification.email_error && (
                            <Badge variant="outline" className="text-xs bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700 text-red-700 dark:text-red-300">
                              <AlertCircle className="w-3 h-3 mr-1" />
                              Email Failed
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Download History */}
          {isAuthenticated && downloadHistory.length > 0 && (
            <div>
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                <Download className="w-4 h-4" />
                Recent Downloads
              </h3>
              <div className="space-y-2">
                {downloadHistory.slice(0, 5).map((download) => (
                  <div key={download.id} className="bg-white dark:bg-slate-700 rounded-lg p-3 shadow-sm border border-slate-200 dark:border-slate-600">
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex-1">
                        <p className="font-medium text-slate-900 dark:text-slate-100">
                          {download.description || `Document #${download.document_number || download.document_id}`}
                        </p>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <Badge
                            variant="outline"
                            className={`text-xs ${
                              download.source === 'free'
                                ? 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700 text-green-700 dark:text-green-300'
                                : 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-700 text-amber-700 dark:text-amber-300'
                            }`}
                          >
                            {download.source === 'free' ? 'FREE' : 'PACER'}
                          </Badge>
                          {download.cost > 0 && (
                            <span className="text-xs text-slate-500 dark:text-slate-400">
                              ${download.cost.toFixed(2)}
                            </span>
                          )}
                          <Badge
                            variant="outline"
                            className={`text-xs ${
                              download.status === 'completed'
                                ? 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700 text-green-700 dark:text-green-300'
                                : download.status === 'failed'
                                ? 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700 text-red-700 dark:text-red-300'
                                : 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-700 dark:text-blue-300'
                            }`}
                          >
                            {download.status}
                          </Badge>
                          <span className="text-xs text-slate-500 dark:text-slate-400">
                            {formatTimeAgo(download.downloaded_at || download.created_at)}
                          </span>
                        </div>
                        {download.error_message && (
                          <p className="text-xs text-red-600 dark:text-red-400 mt-1">
                            {download.error_message}
                          </p>
                        )}
                      </div>
                      {download.status === 'completed' && download.file_name && (
                        <Button size="sm" variant="outline">
                          <Eye className="w-4 h-4 mr-1" />
                          View
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* PACER Connection Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <LinkIcon className="w-5 h-5" />
              PACER Integration
            </CardTitle>
            <div className="flex items-center gap-2">
              {pacerConnected ? (
                <span className="flex items-center gap-2 text-green-600 font-semibold">
                  <CheckCircle className="w-5 h-5" />
                  Connected
                </span>
              ) : (
                <span className="flex items-center gap-2 text-red-600 font-semibold">
                  <AlertCircle className="w-5 h-5" />
                  Not Connected
                </span>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {!pacerConnected && (
            <div className="space-y-4">
              <p className="text-slate-600 dark:text-slate-300">
                Connect to PACER (Public Access to Court Electronic Records) to automatically sync court documents
                and track your case progress in real-time.
              </p>

              {!showPacerSetup ? (
                <Button onClick={() => setShowPacerSetup(true)} className="w-full">
                  <LinkIcon className="w-4 h-4 mr-2" />
                  Connect to PACER
                </Button>
              ) : (
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="PACER Username"
                    value={pacerUsername}
                    onChange={(e) => setPacerUsername(e.target.value)}
                    className="w-full px-4 py-2 border-2 border-slate-300 dark:border-slate-500 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 dark:focus:ring-teal-400"
                  />
                  <div className="relative">
                    <input
                      type={showPacerPassword ? "text" : "password"}
                      placeholder="PACER Password"
                      value={pacerPassword}
                      onChange={(e) => setPacerPassword(e.target.value)}
                      className="w-full px-4 py-2 pr-10 border-2 border-slate-300 dark:border-slate-500 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 dark:focus:ring-teal-400"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPacerPassword(!showPacerPassword)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center z-10 hover:opacity-70 transition-opacity"
                      tabIndex={-1}
                    >
                      {showPacerPassword ? (
                        <Eye className="h-5 w-5 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" />
                      ) : (
                        <EyeOff className="h-5 w-5 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200" />
                      )}
                    </button>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={connectToPacer}
                      disabled={loading || !pacerUsername || !pacerPassword}
                      className="flex-1"
                    >
                      {loading ? 'Connecting...' : 'Connect'}
                    </Button>
                    <Button
                      onClick={() => setShowPacerSetup(false)}
                      variant="outline"
                    >
                      Cancel
                    </Button>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Your PACER credentials are securely encrypted and never shared.
                  </p>
                </div>
              )}
            </div>
          )}

          {pacerConnected && (
            <div className="space-y-3">
              <p className="text-green-700 dark:text-green-400">
                ✅ Successfully connected to PACER. Your case documents will automatically sync.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Cases List */}
      <div className="cases-grid grid grid-cols-1 md:grid-cols-2 gap-4">
        {cases.map((caseData, index) => (
          <Card key={index} className="cursor-pointer hover:shadow-lg transition-shadow dark:bg-slate-800 dark:border-slate-700">
            <CardHeader>
              <CardTitle className="text-lg">
                <FileText className="inline-block w-5 h-5 mr-2 text-teal-600" />
                {caseData.case_number}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <div>
                <p className="font-semibold text-slate-900 dark:text-slate-100">{caseData.case_name}</p>
                <p className="text-sm text-slate-600 dark:text-slate-300">{caseData.court}</p>
              </div>

              <div className="flex items-center gap-2 text-sm">
                <Calendar className="w-4 h-4 text-slate-500 dark:text-slate-400" />
                <span className="text-slate-600 dark:text-slate-300">Filed: {caseData.filing_date}</span>
              </div>

              <div className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                caseData.status === 'Active' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' :
                caseData.status === 'Pending' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300' :
                'bg-slate-100 dark:bg-slate-700 text-slate-800 dark:text-slate-200'
              }`}>
                {caseData.status}
              </div>

              {caseData.next_hearing && (
                <div className="bg-amber-50 dark:bg-amber-900/30 border border-amber-200 dark:border-amber-700 rounded p-2 mt-2">
                  <p className="text-sm font-semibold text-amber-900 dark:text-amber-200">
                    ⏰ Next Hearing: {caseData.next_hearing}
                  </p>
                </div>
              )}

              <div className="pt-2 border-t mt-3">
                <Button
                  onClick={() => setSelectedCase(caseData)}
                  className="w-full"
                  variant="outline"
                >
                  View Documents ({caseData.pacer_documents?.length || 0})
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Selected Case Documents */}
      {selectedCase && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                Documents for {selectedCase.case_number}
              </CardTitle>
              <Button onClick={() => setSelectedCase(null)} variant="outline">
                Close
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {selectedCase.pacer_documents && selectedCase.pacer_documents.length > 0 ? (
              <div className="space-y-2">
                {selectedCase.pacer_documents.map((doc, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-700 rounded border dark:border-slate-600">
                    <div className="flex-1">
                      <p className="font-semibold text-slate-900 dark:text-slate-100">{doc.document_number}</p>
                      <p className="text-sm text-slate-600 dark:text-slate-300">{doc.description}</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400">Filed: {doc.filed_date} by {doc.party}</p>
                    </div>
                    <Button
                      onClick={() => downloadDocument(doc)}
                      size="sm"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      View
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-600 dark:text-slate-300 mb-2">No documents available yet</p>
                {pacerConnected && (
                  <Button onClick={syncWithPacer} variant="outline">
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Sync with PACER
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Info Box */}
      <Card className="bg-teal-50 dark:bg-teal-900/30 border-blue-200 dark:border-teal-700">
        <CardContent className="p-4">
          <p className="text-sm text-navy-800 dark:text-slate-200">
            <strong>ℹ️ About PACER:</strong> PACER provides electronic access to federal court documents.
            Your credentials are used to access case information and download documents related to your cases.
            Standard PACER fees apply for document downloads ($0.10 per page, max $3.00 per document).
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
