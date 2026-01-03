import React, { useState, useEffect } from 'react';
import {
  Users, TrendingUp, AlertTriangle, CheckCircle, Clock, MessageSquare,
  BarChart3, PieChart, Activity, Target, Zap, Shield, RefreshCw
} from 'lucide-react';

interface BetaMetrics {
  user_adoption: {
    total_invited: number;
    total_active: number;
    activation_rate: number;
    completed_onboarding: number;
    onboarding_completion_rate: number;
  };
  engagement: {
    avg_sessions_per_user: number;
    avg_session_duration_minutes: number;
    avg_satisfaction_score: number;
    total_documents_processed: number;
    total_research_queries: number;
  };
  feedback_quality: {
    total_feedback_submissions: number;
    total_bug_reports: number;
    feedback_per_user: number;
  };
  issue_resolution: {
    total_issues: number;
    resolved_issues: number;
    resolution_rate: number;
  };
}

interface Alert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  message: string;
  triggered_at: string;
  acknowledged: boolean;
}

interface RealTimeMetrics {
  active_beta_users: number;
  error_rate_percentage: number;
  avg_response_time_ms: number;
  new_issues_last_hour: number;
  negative_feedback_last_hour: number;
}

export const BetaLaunchDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<BetaMetrics | null>(null);
  const [realTimeMetrics, setRealTimeMetrics] = useState<RealTimeMetrics | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  useEffect(() => {
    loadDashboardData();

    // Set up real-time updates
    const interval = setInterval(() => {
      loadRealTimeMetrics();
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);

      // Load all dashboard data in parallel
      const [metricsResponse, alertsResponse, realTimeResponse] = await Promise.all([
        fetch('/api/v1/beta/metrics', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/v1/beta/monitoring/alerts', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/v1/beta/monitoring/realtime', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setMetrics(metricsData);
      }

      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData);
      }

      if (realTimeResponse.ok) {
        const realTimeData = await realTimeResponse.json();
        setRealTimeMetrics(realTimeData.data);
      }

      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadRealTimeMetrics = async () => {
    try {
      const response = await fetch('/api/v1/beta/monitoring/realtime', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      if (response.ok) {
        const data = await response.json();
        setRealTimeMetrics(data.data);
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error('Failed to load real-time metrics:', error);
    }
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await fetch(`/api/v1/beta/monitoring/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });

      setAlerts(prev =>
        prev.map(alert =>
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      );
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const getHealthStatus = () => {
    if (!realTimeMetrics) return 'unknown';

    const criticalAlerts = alerts.filter(a => a.severity === 'critical' && !a.acknowledged);
    if (criticalAlerts.length > 0) return 'critical';

    if (realTimeMetrics.error_rate_percentage > 5) return 'warning';
    if (realTimeMetrics.avg_response_time_ms > 2000) return 'warning';

    return 'healthy';
  };

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600 bg-green-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'critical': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-lg">Loading Beta Launch Dashboard...</span>
      </div>
    );
  }

  const healthStatus = getHealthStatus();

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Beta Launch Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Real-time monitoring and success tracking for beta program
          </p>
        </div>

        <div className="text-right">
          <div className={`inline-flex items-center px-3 py-2 rounded-full text-sm font-medium ${getHealthColor(healthStatus)}`}>
            <Activity className="h-4 w-4 mr-1" />
            {healthStatus.toUpperCase()}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>
      </div>

      {/* Critical Alerts */}
      {alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-red-900 mb-3 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2" />
            Critical Alerts Requiring Immediate Attention
          </h3>
          <div className="space-y-2">
            {alerts
              .filter(a => a.severity === 'critical' && !a.acknowledged)
              .map(alert => (
                <div key={alert.id} className="bg-white rounded p-3 border border-red-200">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-red-900">{alert.title}</h4>
                      <p className="text-sm text-red-700 mt-1">{alert.message}</p>
                      <p className="text-xs text-red-600 mt-1">
                        {new Date(alert.triggered_at).toLocaleString()}
                      </p>
                    </div>
                    <button
                      onClick={() => acknowledgeAlert(alert.id)}
                      className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                    >
                      Acknowledge
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Real-Time Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Active Beta Users"
          value={realTimeMetrics?.active_beta_users?.toString() || '0'}
          icon={<Users className="h-6 w-6" />}
          color="blue"
          subtitle="Currently online"
        />

        <MetricCard
          title="Error Rate"
          value={`${realTimeMetrics?.error_rate_percentage?.toFixed(1) || '0'}%`}
          icon={<AlertTriangle className="h-6 w-6" />}
          color={realTimeMetrics && realTimeMetrics.error_rate_percentage > 5 ? "red" : "green"}
          subtitle="Last 10 minutes"
        />

        <MetricCard
          title="Response Time"
          value={`${realTimeMetrics?.avg_response_time_ms || 0}ms`}
          icon={<Zap className="h-6 w-6" />}
          color={realTimeMetrics && realTimeMetrics.avg_response_time_ms > 2000 ? "yellow" : "green"}
          subtitle="Average"
        />

        <MetricCard
          title="New Issues"
          value={realTimeMetrics?.new_issues_last_hour?.toString() || '0'}
          icon={<Shield className="h-6 w-6" />}
          color={realTimeMetrics && realTimeMetrics.new_issues_last_hour > 3 ? "red" : "green"}
          subtitle="Last hour"
        />

        <MetricCard
          title="Negative Feedback"
          value={realTimeMetrics?.negative_feedback_last_hour?.toString() || '0'}
          icon={<MessageSquare className="h-6 w-6" />}
          color={realTimeMetrics && realTimeMetrics.negative_feedback_last_hour > 2 ? "yellow" : "green"}
          subtitle="Last hour"
        />
      </div>

      {/* Key Success Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* User Adoption */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Target className="h-5 w-5 mr-2 text-blue-600" />
              User Adoption & Onboarding
            </h3>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Invited</span>
                <span className="font-semibold">{metrics.user_adoption.total_invited}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Active Users</span>
                <span className="font-semibold text-green-600">{metrics.user_adoption.total_active}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Activation Rate</span>
                <div className="text-right">
                  <span className="font-semibold">
                    {(metrics.user_adoption.activation_rate * 100).toFixed(1)}%
                  </span>
                  <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${metrics.user_adoption.activation_rate * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Completed Onboarding</span>
                <span className="font-semibold">{metrics.user_adoption.completed_onboarding}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Onboarding Completion Rate</span>
                <span className="font-semibold">
                  {(metrics.user_adoption.onboarding_completion_rate * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Engagement Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
              User Engagement
            </h3>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Avg Sessions/User</span>
                <span className="font-semibold">{metrics.engagement.avg_sessions_per_user?.toFixed(1) || '0'}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Avg Session Duration</span>
                <span className="font-semibold">{Math.round(metrics.engagement.avg_session_duration_minutes || 0)} min</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Satisfaction Score</span>
                <div className="text-right">
                  <span className="font-semibold text-green-600">
                    {metrics.engagement.avg_satisfaction_score?.toFixed(1) || '0'}/10
                  </span>
                  <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${(metrics.engagement.avg_satisfaction_score || 0) * 10}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Documents Processed</span>
                <span className="font-semibold">{metrics.engagement.total_documents_processed}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Research Queries</span>
                <span className="font-semibold">{metrics.engagement.total_research_queries}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Feedback & Issues */}
      {metrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Feedback Quality */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <MessageSquare className="h-5 w-5 mr-2 text-purple-600" />
              Feedback Quality
            </h3>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Feedback</span>
                <span className="font-semibold">{metrics.feedback_quality.total_feedback_submissions}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Bug Reports</span>
                <span className="font-semibold text-orange-600">{metrics.feedback_quality.total_bug_reports}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Feedback per User</span>
                <span className="font-semibold">{metrics.feedback_quality.feedback_per_user?.toFixed(1) || '0'}</span>
              </div>
            </div>
          </div>

          {/* Issue Resolution */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <CheckCircle className="h-5 w-5 mr-2 text-green-600" />
              Issue Resolution
            </h3>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Issues</span>
                <span className="font-semibold">{metrics.issue_resolution.total_issues}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Resolved Issues</span>
                <span className="font-semibold text-green-600">{metrics.issue_resolution.resolved_issues}</span>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">Resolution Rate</span>
                <div className="text-right">
                  <span className="font-semibold">
                    {(metrics.issue_resolution.resolution_rate * 100).toFixed(1)}%
                  </span>
                  <div className="w-24 bg-gray-200 rounded-full h-2 mt-1">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${metrics.issue_resolution.resolution_rate * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Alerts */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 text-yellow-600" />
            Recent Alerts
          </h3>

          <div className="space-y-3">
            {alerts.slice(0, 5).map(alert => (
              <div
                key={alert.id}
                className={`p-3 rounded-lg border ${
                  alert.severity === 'critical' ? 'bg-red-50 border-red-200' :
                  alert.severity === 'high' ? 'bg-orange-50 border-orange-200' :
                  alert.severity === 'medium' ? 'bg-yellow-50 border-yellow-200' :
                  'bg-blue-50 border-blue-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                        alert.severity === 'critical' ? 'bg-red-100 text-red-800' :
                        alert.severity === 'high' ? 'bg-orange-100 text-orange-800' :
                        alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span className="font-medium text-gray-900">{alert.title}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{alert.message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(alert.triggered_at).toLocaleString()}
                    </p>
                  </div>

                  {!alert.acknowledged && (
                    <button
                      onClick={() => acknowledgeAlert(alert.id)}
                      className="ml-3 px-3 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700"
                    >
                      Acknowledge
                    </button>
                  )}

                  {alert.acknowledged && (
                    <span className="ml-3 text-xs text-green-600 font-medium">
                      Acknowledged
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Auto-refresh Controls */}
      <div className="flex justify-center">
        <button
          onClick={loadRealTimeMetrics}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh Data
        </button>
      </div>
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
  subtitle: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon, color, subtitle }) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-600',
    green: 'bg-green-50 border-green-200 text-green-600',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-600',
    red: 'bg-red-50 border-red-200 text-red-600',
    purple: 'bg-purple-50 border-purple-200 text-purple-600'
  };

  return (
    <div className={`rounded-lg border p-4 ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>
        <div className="opacity-75">
          {icon}
        </div>
      </div>
    </div>
  );
};