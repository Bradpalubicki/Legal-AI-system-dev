'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Alert,
  StatCardSkeleton,
  CardSkeleton,
  EmptyState,
  Badge,
} from '@/components/design-system';
import { API_CONFIG } from '../../config/api';
import {
  Scale,
  Calendar,
  DollarSign,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  BarChart3,
  PieChart,
  TrendingUp,
  ArrowRight,
  Upload,
  FolderOpen,
} from 'lucide-react';
import { toast } from 'sonner';

interface CaseStats {
  total: number;
  byStatus: Record<string, number>;
  byType: Record<string, number>;
  recentCount: number;
}

interface FinancialStats {
  totalAmount: number;
  byType: Record<string, number>;
  byStatus: Record<string, number>;
  transactionCount: number;
}

interface TimelineStats {
  upcomingDeadlines: number;
  overdueItems: number;
  completedEvents: number;
  totalEvents: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [caseStats, setCaseStats] = useState<CaseStats | null>(null);
  const [financialStats, setFinancialStats] = useState<FinancialStats | null>(null);
  const [timelineStats, setTimelineStats] = useState<TimelineStats | null>(null);

  useEffect(() => {
    const abortController = new AbortController();

    const loadDashboardData = async () => {
      try {
        setLoading(true);

        // Fetch all cases with abort signal
        const casesResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/cases/`, {
          signal: abortController.signal
        });

        if (!casesResponse.ok) {
          throw new Error('Failed to fetch cases');
        }

        const cases = await casesResponse.json();

        // Calculate case statistics
        const caseStatsData: CaseStats = {
          total: cases.length,
          byStatus: {},
          byType: {},
          recentCount: 0
        };

        const now = new Date();
        const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

        cases.forEach((c: any) => {
          // Count by status
          caseStatsData.byStatus[c.status] = (caseStatsData.byStatus[c.status] || 0) + 1;

          // Count by type
          caseStatsData.byType[c.case_type] = (caseStatsData.byType[c.case_type] || 0) + 1;

          // Count recent cases (last 30 days)
          if (c.created_at && new Date(c.created_at) > thirtyDaysAgo) {
            caseStatsData.recentCount++;
          }
        });

        setCaseStats(caseStatsData);

        // Fetch financial data from all cases (in parallel) with abort signal
        const transactionPromises = cases.map(async (caseItem: any) => {
          try {
            const transResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/cases/${caseItem.id}/transactions`, {
              signal: abortController.signal
            });
            if (transResponse.ok) {
              return await transResponse.json();
            }
            return [];
          } catch (error: any) {
            if (error.name === 'AbortError') throw error; // Re-throw abort errors
            console.error(`Failed to fetch transactions for case ${caseItem.id}`);
            return [];
          }
        });

        const transactionResults = await Promise.all(transactionPromises);
        const allTransactions = transactionResults.flat();

        // Calculate financial statistics
        const finStatsData: FinancialStats = {
          totalAmount: 0,
          byType: {},
          byStatus: {},
          transactionCount: allTransactions.length
        };

        allTransactions.forEach((t: any) => {
          finStatsData.totalAmount += t.amount || 0;
          finStatsData.byType[t.transaction_type] = (finStatsData.byType[t.transaction_type] || 0) + t.amount;
          finStatsData.byStatus[t.payment_status] = (finStatsData.byStatus[t.payment_status] || 0) + 1;
        });

        setFinancialStats(finStatsData);

        // Fetch timeline data from all cases (in parallel) with abort signal
        const eventsPromises = cases.map(async (caseItem: any) => {
          try {
            const eventsResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/cases/${caseItem.id}/events`, {
              signal: abortController.signal
            });
            if (eventsResponse.ok) {
              return await eventsResponse.json();
            }
            return [];
          } catch (error: any) {
            if (error.name === 'AbortError') throw error; // Re-throw abort errors
            console.error(`Failed to fetch events for case ${caseItem.id}`);
            return [];
          }
        });

        const eventsResults = await Promise.all(eventsPromises);
        const allEvents = eventsResults.flat();

        // Calculate timeline statistics
        const timeStatsData: TimelineStats = {
          upcomingDeadlines: 0,
          overdueItems: 0,
          completedEvents: 0,
          totalEvents: allEvents.length
        };

        allEvents.forEach((e: any) => {
          const eventDate = new Date(e.event_date);

          if (e.status === 'completed') {
            timeStatsData.completedEvents++;
          } else if (e.status === 'scheduled' && eventDate < now) {
            timeStatsData.overdueItems++;
          } else if (e.status === 'scheduled' && eventDate >= now) {
            timeStatsData.upcomingDeadlines++;
          }
        });

        setTimelineStats(timeStatsData);

      } catch (error: any) {
        // Don't show error for aborted requests (user navigated away)
        if (error.name === 'AbortError') {
          console.log('Dashboard data fetch aborted');
          return;
        }
        console.error('Failed to load dashboard data:', error);
        toast.error('Failed to load dashboard data', {
          description: error.message
        });
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();

    // Cleanup: abort pending requests when component unmounts
    return () => {
      abortController.abort();
    };
  }, []);

  const getStatusBadgeVariant = (status: string): 'default' | 'success' | 'warning' | 'error' | 'info' => {
    const variants: Record<string, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
      open: 'info',
      active: 'success',
      pending: 'warning',
      closed: 'default',
      dismissed: 'error'
    };
    return variants[status] || 'default';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="max-w-content mx-auto px-6 py-8">
          {/* Header Skeleton */}
          <div className="mb-8">
            <div className="h-8 w-64 bg-slate-200 rounded animate-pulse mb-2"></div>
            <div className="h-4 w-96 bg-slate-200 rounded animate-pulse"></div>
          </div>

          {/* Stats Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
            <StatCardSkeleton />
          </div>

          {/* Cards Skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-content mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-navy-800 flex items-center gap-3">
                <div className="p-2 bg-teal-50 rounded-lg">
                  <BarChart3 className="w-6 h-6 text-teal-600" />
                </div>
                Analytics Dashboard
              </h1>
              <p className="text-slate-500 mt-2">
                Comprehensive insights into your legal case management
              </p>
            </div>
            <div className="flex gap-3">
              <Button
                variant="outline"
                onClick={() => router.push('/documents')}
                leftIcon={<Upload className="w-4 h-4" />}
              >
                Upload Document
              </Button>
              <Button
                onClick={() => router.push('/cases')}
                leftIcon={<FolderOpen className="w-4 h-4" />}
              >
                View All Cases
              </Button>
            </div>
          </div>
        </div>

        {/* Quick Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Cases */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Total Cases</p>
                  <p className="text-3xl font-bold text-navy-800 mt-2">
                    {caseStats?.total || 0}
                  </p>
                  <div className="flex items-center gap-1 mt-2">
                    <TrendingUp className="w-3 h-3 text-success-600" />
                    <span className="text-xs text-success-600 font-medium">
                      +{caseStats?.recentCount || 0} this month
                    </span>
                  </div>
                </div>
                <div className="p-3 bg-navy-50 rounded-xl">
                  <Scale className="w-7 h-7 text-navy-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Financial Overview */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Total Transactions</p>
                  <p className="text-3xl font-bold text-navy-800 mt-2">
                    ${financialStats?.totalAmount.toLocaleString() || 0}
                  </p>
                  <p className="text-xs text-slate-400 mt-2">
                    {financialStats?.transactionCount || 0} transactions
                  </p>
                </div>
                <div className="p-3 bg-teal-50 rounded-xl">
                  <DollarSign className="w-7 h-7 text-teal-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Upcoming Deadlines */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Upcoming Deadlines</p>
                  <p className="text-3xl font-bold text-navy-800 mt-2">
                    {timelineStats?.upcomingDeadlines || 0}
                  </p>
                  {timelineStats?.overdueItems ? (
                    <div className="flex items-center gap-1 mt-2">
                      <AlertTriangle className="w-3 h-3 text-error-600" />
                      <span className="text-xs text-error-600 font-medium">
                        {timelineStats.overdueItems} overdue
                      </span>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 mt-2">No overdue items</p>
                  )}
                </div>
                <div className="p-3 bg-warning-50 rounded-xl">
                  <Calendar className="w-7 h-7 text-warning-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Completion Rate */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-500">Completion Rate</p>
                  <p className="text-3xl font-bold text-navy-800 mt-2">
                    {timelineStats?.totalEvents
                      ? Math.round((timelineStats.completedEvents / timelineStats.totalEvents) * 100)
                      : 0}%
                  </p>
                  <p className="text-xs text-slate-400 mt-2">
                    {timelineStats?.completedEvents || 0} of {timelineStats?.totalEvents || 0} events
                  </p>
                </div>
                <div className="p-3 bg-success-50 rounded-xl">
                  <CheckCircle className="w-7 h-7 text-success-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Cases by Status */}
          <Card>
            <CardHeader>
              <CardTitle icon={<PieChart className="w-5 h-5" />}>
                Cases by Status
              </CardTitle>
              <CardDescription>
                Distribution of cases across different statuses
              </CardDescription>
            </CardHeader>
            <CardContent>
              {caseStats && Object.keys(caseStats.byStatus).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(caseStats.byStatus).map(([status, count]) => (
                    <div key={status} className="flex items-center gap-4">
                      <Badge variant={getStatusBadgeVariant(status)} className="w-20 justify-center capitalize">
                        {status}
                      </Badge>
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
                            <div
                              className="bg-gradient-to-r from-navy-600 to-navy-500 h-2.5 rounded-full transition-all duration-500"
                              style={{ width: `${(count / caseStats.total) * 100}%` }}
                            />
                          </div>
                          <span className="text-sm font-semibold text-navy-800 w-8 text-right">
                            {count}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon="folder"
                  title="No cases yet"
                  description="Create your first case to see status distribution"
                  action={{
                    label: "Create Case",
                    onClick: () => router.push('/cases')
                  }}
                />
              )}
            </CardContent>
          </Card>

          {/* Financial Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle icon={<DollarSign className="w-5 h-5" />}>
                Financial Breakdown
              </CardTitle>
              <CardDescription>
                Transaction amounts by type
              </CardDescription>
            </CardHeader>
            <CardContent>
              {financialStats && Object.keys(financialStats.byType).length > 0 ? (
                <div className="space-y-4">
                  {Object.entries(financialStats.byType)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 5)
                    .map(([type, amount]) => (
                      <div key={type} className="flex items-center gap-4">
                        <span className="text-sm font-medium text-slate-600 capitalize w-24 truncate">
                          {type}
                        </span>
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden">
                              <div
                                className="bg-gradient-to-r from-teal-600 to-teal-500 h-2.5 rounded-full transition-all duration-500"
                                style={{ width: `${(amount / financialStats.totalAmount) * 100}%` }}
                              />
                            </div>
                            <span className="text-sm font-semibold text-navy-800 w-24 text-right">
                              ${amount.toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              ) : (
                <EmptyState
                  icon="inbox"
                  title="No transactions yet"
                  description="Financial data will appear once transactions are recorded"
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Alerts and Case Types */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Alerts */}
          <Card>
            <CardHeader>
              <CardTitle icon={<AlertTriangle className="w-5 h-5 text-warning-600" />}>
                Attention Required
              </CardTitle>
              <CardDescription>
                Items that need your immediate attention
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {timelineStats && timelineStats.overdueItems > 0 && (
                  <Alert variant="error" title={`${timelineStats.overdueItems} Overdue Items`}>
                    You have overdue events that need immediate attention
                  </Alert>
                )}

                {timelineStats && timelineStats.upcomingDeadlines > 0 && (
                  <Alert variant="warning" title={`${timelineStats.upcomingDeadlines} Upcoming Deadlines`}>
                    Review your upcoming events and prepare accordingly
                  </Alert>
                )}

                {(!timelineStats || (timelineStats.overdueItems === 0 && timelineStats.upcomingDeadlines === 0)) && (
                  <Alert variant="success" title="All Caught Up!">
                    No urgent items requiring attention
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Case Types Distribution */}
          <Card>
            <CardHeader>
              <CardTitle icon={<Scale className="w-5 h-5" />}>
                Cases by Type
              </CardTitle>
              <CardDescription>
                Distribution of cases by legal category
              </CardDescription>
            </CardHeader>
            <CardContent>
              {caseStats && Object.keys(caseStats.byType).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(caseStats.byType).map(([type, count]) => (
                    <div
                      key={type}
                      className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
                      onClick={() => router.push(`/cases?type=${type}`)}
                    >
                      <span className="text-sm font-medium text-navy-700 capitalize">
                        {type.replace('_', ' ')}
                      </span>
                      <div className="flex items-center gap-3">
                        <div className="w-24 bg-slate-200 rounded-full h-2">
                          <div
                            className="bg-navy-600 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${(count / caseStats.total) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-semibold text-navy-800 w-8 text-right">
                          {count}
                        </span>
                        <ArrowRight className="w-4 h-4 text-slate-400" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon="folder"
                  title="No cases by type"
                  description="Case type breakdown will appear once cases are created"
                />
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="mt-8">
          <Card>
            <CardContent className="py-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-navy-800">Need to analyze a document?</h3>
                  <p className="text-slate-500 mt-1">Upload and analyze legal documents with AI-powered insights</p>
                </div>
                <Button
                  onClick={() => router.push('/documents')}
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  Go to Documents
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
