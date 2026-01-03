import React, { useState, useEffect } from 'react';
import {
  PlayCircle, StopCircle, AlertTriangle, CheckCircle, Clock, Shield,
  TrendingUp, Users, DollarSign, Activity, RefreshCw, Eye, Phone,
  FileText, Settings, BarChart3, Target, Zap
} from 'lucide-react';

interface LaunchStatus {
  launch_plan_id: string | null;
  current_phase: string | null;
  overall_status: string | null;
  progress_percentage: number;
  contingency_activated: boolean;
  monitoring_active: boolean;
  last_updated: string;
}

interface ExecutiveMetrics {
  business_metrics: {
    total_users: number;
    active_users_24h: number;
    revenue_today: number;
    conversion_rate: number;
  };
  system_performance: {
    uptime_percentage: number;
    avg_response_time_ms: number;
    error_rate_percentage: number;
    system_health: string;
  };
  risk_indicators: {
    security_alerts: number;
    compliance_issues: number;
    critical_bugs: number;
    risk_level: string;
  };
  support_metrics: {
    open_tickets: number;
    avg_resolution_time_hours: number;
    customer_satisfaction: number;
    escalations: number;
  };
}

interface ReadinessCheck {
  overall_status: string;
  ready_for_launch: boolean;
  total_checks: number;
  checks_passed: number;
  warnings: number;
  blocking_issues: number;
  next_steps: string[];
  recommendation: string;
}

export const ExecutiveLaunchDashboard: React.FC = () => {
  const [launchStatus, setLaunchStatus] = useState<LaunchStatus | null>(null);
  const [executiveMetrics, setExecutiveMetrics] = useState<ExecutiveMetrics | null>(null);
  const [readinessCheck, setReadinessCheck] = useState<ReadinessCheck | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Launch control state
  const [showLaunchConfirm, setShowLaunchConfirm] = useState(false);
  const [showEmergencyStop, setShowEmergencyStop] = useState(false);
  const [executiveSignature, setExecutiveSignature] = useState('');

  useEffect(() => {
    loadDashboardData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);

      const [statusResponse, metricsResponse] = await Promise.all([
        fetch('/api/v1/launch/status', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        }),
        fetch('/api/v1/launch/metrics/executive-summary', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        })
      ]);

      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        setLaunchStatus(statusData);
      }

      if (metricsResponse.ok) {
        const metricsData = await metricsResponse.json();
        setExecutiveMetrics(metricsData.summary);
      }

      setLastUpdated(new Date());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const executeReadinessCheck = async () => {
    try {
      const response = await fetch('/api/v1/launch/readiness-check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          triple_check: true,
          notify_stakeholders: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        setReadinessCheck(data.executive_summary);
      }
    } catch (error) {
      console.error('Readiness check failed:', error);
    }
  };

  const executeLaunch = async () => {
    if (!executiveSignature) {
      alert('Executive signature required');
      return;
    }

    try {
      const response = await fetch('/api/v1/launch/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          target_phase: 'post_launch',
          start_immediately: false,
          executive_approval: executiveSignature
        })
      });

      if (response.ok) {
        setShowLaunchConfirm(false);
        setExecutiveSignature('');
        await loadDashboardData();
      }
    } catch (error) {
      console.error('Launch execution failed:', error);
    }
  };

  const emergencyStop = async () => {
    if (!executiveSignature) {
      alert('Executive authorization required');
      return;
    }

    try {
      const response = await fetch('/api/v1/launch/emergency-stop', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          reason: 'Executive emergency stop',
          triggered_by: 'Executive Dashboard',
          executive_authorization: executiveSignature
        })
      });

      if (response.ok) {
        setShowEmergencyStop(false);
        setExecutiveSignature('');
        await loadDashboardData();
      }
    } catch (error) {
      console.error('Emergency stop failed:', error);
    }
  };

  const getStatusColor = (status: string | null) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'executing': return 'text-blue-600 bg-blue-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'low': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  if (isLoading && !launchStatus) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-2 text-lg">Loading Executive Dashboard...</span>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Executive Launch Command Center</h1>
          <p className="text-gray-600 mt-1">
            Real-time launch control and executive oversight
          </p>
        </div>

        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-sm text-gray-500">Last Updated</p>
            <p className="font-medium">{lastUpdated.toLocaleTimeString()}</p>
          </div>

          <button
            onClick={loadDashboardData}
            className="p-2 border border-gray-300 rounded-md hover:bg-gray-50"
            title="Refresh Data"
          >
            <RefreshCw className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Critical Actions Bar */}
      <div className="bg-white rounded-lg shadow-lg border-2 border-blue-200 p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
          <Shield className="h-6 w-6 mr-2 text-blue-600" />
          Executive Launch Controls
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Readiness Check */}
          <button
            onClick={executeReadinessCheck}
            className="flex flex-col items-center p-4 border-2 border-blue-300 rounded-lg hover:bg-blue-50 transition-colors"
          >
            <CheckCircle className="h-8 w-8 text-blue-600 mb-2" />
            <span className="font-medium text-blue-900">Triple-Check Readiness</span>
            <span className="text-sm text-blue-700">Final validation</span>
          </button>

          {/* Launch Execution */}
          <button
            onClick={() => setShowLaunchConfirm(true)}
            disabled={launchStatus?.overall_status === 'executing'}
            className="flex flex-col items-center p-4 border-2 border-green-300 rounded-lg hover:bg-green-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PlayCircle className="h-8 w-8 text-green-600 mb-2" />
            <span className="font-medium text-green-900">Execute Launch</span>
            <span className="text-sm text-green-700">Start phased rollout</span>
          </button>

          {/* Emergency Stop */}
          <button
            onClick={() => setShowEmergencyStop(true)}
            className="flex flex-col items-center p-4 border-2 border-red-300 rounded-lg hover:bg-red-50 transition-colors"
          >
            <StopCircle className="h-8 w-8 text-red-600 mb-2" />
            <span className="font-medium text-red-900">Emergency Stop</span>
            <span className="text-sm text-red-700">Immediate halt</span>
          </button>
        </div>
      </div>

      {/* Launch Status */}
      {launchStatus && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Activity className="h-5 w-5 mr-2 text-blue-600" />
            Current Launch Status
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-600">Launch Phase</p>
              <p className="font-semibold text-lg capitalize">
                {launchStatus.current_phase?.replace('_', ' ') || 'Not Started'}
              </p>
            </div>

            <div>
              <p className="text-sm text-gray-600">Overall Status</p>
              <span className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(launchStatus.overall_status)}`}>
                {launchStatus.overall_status?.toUpperCase() || 'UNKNOWN'}
              </span>
            </div>

            <div>
              <p className="text-sm text-gray-600">Progress</p>
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${launchStatus.progress_percentage}%` }}
                  />
                </div>
                <span className="text-sm font-medium">{Math.round(launchStatus.progress_percentage)}%</span>
              </div>
            </div>

            <div>
              <p className="text-sm text-gray-600">System Status</p>
              <div className="flex items-center space-x-2">
                {launchStatus.contingency_activated ? (
                  <span className="text-red-600 font-medium">CONTINGENCY ACTIVE</span>
                ) : (
                  <span className="text-green-600 font-medium">NORMAL OPERATIONS</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Readiness Check Results */}
      {readinessCheck && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Target className="h-5 w-5 mr-2 text-purple-600" />
            Launch Readiness Assessment
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center justify-between mb-4">
                <span className="text-lg font-medium">Overall Assessment</span>
                <span className={`px-4 py-2 rounded-full font-bold text-lg ${
                  readinessCheck.recommendation === 'GO'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {readinessCheck.recommendation}
                </span>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span>Checks Passed</span>
                  <span className="font-semibold">{readinessCheck.checks_passed}/{readinessCheck.total_checks}</span>
                </div>
                <div className="flex justify-between">
                  <span>Warnings</span>
                  <span className={`font-semibold ${readinessCheck.warnings > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                    {readinessCheck.warnings}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Blocking Issues</span>
                  <span className={`font-semibold ${readinessCheck.blocking_issues > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {readinessCheck.blocking_issues}
                  </span>
                </div>
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-3">Next Steps</h4>
              <ul className="space-y-2">
                {readinessCheck.next_steps.map((step, index) => (
                  <li key={index} className="flex items-start space-x-2">
                    <span className="text-blue-600 mt-1">•</span>
                    <span className="text-sm">{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Executive Metrics */}
      {executiveMetrics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Business Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <TrendingUp className="h-5 w-5 mr-2 text-green-600" />
              Business Performance
            </h3>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Users</span>
                <span className="font-semibold text-lg">{executiveMetrics.business_metrics.total_users.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Active Users (24h)</span>
                <span className="font-semibold text-lg text-green-600">{executiveMetrics.business_metrics.active_users_24h.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Revenue Today</span>
                <span className="font-semibold text-lg">${executiveMetrics.business_metrics.revenue_today.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Conversion Rate</span>
                <span className="font-semibold text-lg">{executiveMetrics.business_metrics.conversion_rate}%</span>
              </div>
            </div>
          </div>

          {/* System Performance */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Zap className="h-5 w-5 mr-2 text-blue-600" />
              System Performance
            </h3>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Uptime</span>
                <span className="font-semibold text-lg text-green-600">{executiveMetrics.system_performance.uptime_percentage}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Response Time</span>
                <span className="font-semibold text-lg">{executiveMetrics.system_performance.avg_response_time_ms}ms</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Error Rate</span>
                <span className="font-semibold text-lg text-green-600">{executiveMetrics.system_performance.error_rate_percentage}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">System Health</span>
                <span className="font-semibold text-lg capitalize text-green-600">{executiveMetrics.system_performance.system_health}</span>
              </div>
            </div>
          </div>

          {/* Risk Indicators */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2 text-yellow-600" />
              Risk Indicators
            </h3>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Security Alerts</span>
                <span className={`font-semibold text-lg ${executiveMetrics.risk_indicators.security_alerts === 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {executiveMetrics.risk_indicators.security_alerts}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Compliance Issues</span>
                <span className={`font-semibold text-lg ${executiveMetrics.risk_indicators.compliance_issues === 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {executiveMetrics.risk_indicators.compliance_issues}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Critical Bugs</span>
                <span className={`font-semibold text-lg ${executiveMetrics.risk_indicators.critical_bugs === 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {executiveMetrics.risk_indicators.critical_bugs}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Overall Risk Level</span>
                <span className={`font-semibold text-lg capitalize ${getRiskColor(executiveMetrics.risk_indicators.risk_level)}`}>
                  {executiveMetrics.risk_indicators.risk_level}
                </span>
              </div>
            </div>
          </div>

          {/* Support Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Users className="h-5 w-5 mr-2 text-purple-600" />
              Support Performance
            </h3>

            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Open Tickets</span>
                <span className="font-semibold text-lg">{executiveMetrics.support_metrics.open_tickets}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Avg Resolution Time</span>
                <span className="font-semibold text-lg">{executiveMetrics.support_metrics.avg_resolution_time_hours}h</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Customer Satisfaction</span>
                <span className="font-semibold text-lg text-green-600">{executiveMetrics.support_metrics.customer_satisfaction}/10</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Escalations</span>
                <span className={`font-semibold text-lg ${executiveMetrics.support_metrics.escalations === 0 ? 'text-green-600' : 'text-yellow-600'}`}>
                  {executiveMetrics.support_metrics.escalations}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Launch Confirmation Modal */}
      {showLaunchConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">Confirm Launch Execution</h3>
            <p className="text-gray-600 mb-4">
              This will initiate the automated launch sequence. Are you sure you want to proceed?
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Executive Signature (Required)
              </label>
              <input
                type="text"
                value={executiveSignature}
                onChange={(e) => setExecutiveSignature(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter your full name"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowLaunchConfirm(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={executeLaunch}
                disabled={!executiveSignature}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                Execute Launch
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Emergency Stop Modal */}
      {showEmergencyStop && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-red-900 mb-4">Emergency Stop Confirmation</h3>
            <p className="text-gray-600 mb-4">
              This will immediately halt all launch activities and activate emergency procedures.
            </p>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Executive Authorization (Required)
              </label>
              <input
                type="text"
                value={executiveSignature}
                onChange={(e) => setExecutiveSignature(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                placeholder="Enter your full name"
              />
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setShowEmergencyStop(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={emergencyStop}
                disabled={!executiveSignature}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                Emergency Stop
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};