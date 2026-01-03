/**
 * Executive Dashboard for Case Management
 * Shows critical deadlines, bid status, at-risk items, and required actions
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import {
  CaseDashboard,
  ActionItemsResponse,
  StrategicSummary,
  CriticalPathAnalysis,
} from '@/types/case-management';
import { caseManagementAPI } from '@/lib/api/case-management-api';

interface ExecutiveDashboardProps {
  caseId: string;
}

interface DashboardData {
  dashboard: CaseDashboard | null;
  actionItems: ActionItemsResponse | null;
  strategicSummary: StrategicSummary | null;
  criticalPath: CriticalPathAnalysis | null;
  loading: boolean;
  error: string | null;
}

export default function ExecutiveDashboard({ caseId }: ExecutiveDashboardProps) {
  const [data, setData] = useState<DashboardData>({
    dashboard: null,
    actionItems: null,
    strategicSummary: null,
    criticalPath: null,
    loading: true,
    error: null,
  });

  useEffect(() => {
    loadDashboardData();
  }, [caseId]);

  const loadDashboardData = async () => {
    try {
      setData((prev) => ({ ...prev, loading: true, error: null }));

      // Load all dashboard data in parallel
      const [dashboard, actionItems, strategicSummary, criticalPath] = await Promise.all([
        caseManagementAPI.cases.getDashboard(caseId),
        caseManagementAPI.briefing.getActionItems(caseId),
        caseManagementAPI.briefing.getStrategicSummary(caseId),
        caseManagementAPI.timeline.getCriticalPath(caseId),
      ]);

      setData({
        dashboard,
        actionItems,
        strategicSummary,
        criticalPath,
        loading: false,
        error: null,
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
      setData((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load dashboard',
      }));
    }
  };

  if (data.loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (data.error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {data.error}</p>
        <button
          onClick={loadDashboardData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  const { dashboard, actionItems, strategicSummary, criticalPath } = data;

  // Calculate at-risk items
  const atRiskItems = {
    critical: actionItems?.urgent_items || 0,
    warning: dashboard?.deadlines.at_risk_count || 0,
    normal: (actionItems?.total_action_items || 0) - (actionItems?.urgent_items || 0),
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold text-gray-900">
          {dashboard?.case_info.case_name || 'Case Dashboard'}
        </h1>
        <p className="text-gray-600 mt-1">
          Case #{dashboard?.case_info.case_number} • Status: {dashboard?.case_info.status} • Phase:{' '}
          {dashboard?.case_info.current_phase || 'N/A'}
        </p>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Days to Critical Deadlines */}
        <Card className="p-6 bg-gradient-to-br from-red-50 to-red-100 border-red-200">
          <h3 className="text-sm font-medium text-red-900 uppercase tracking-wide">
            Next Critical Deadline
          </h3>
          {dashboard?.deadlines.upcoming && dashboard.deadlines.upcoming.length > 0 ? (
            <>
              <p className="text-4xl font-bold text-red-700 mt-2">
                {dashboard.deadlines.upcoming[0].days_until}
                <span className="text-lg ml-1">days</span>
              </p>
              <p className="text-sm text-red-600 mt-2 truncate">
                {dashboard.deadlines.upcoming[0].title}
              </p>
            </>
          ) : (
            <p className="text-2xl font-bold text-red-700 mt-2">No upcoming deadlines</p>
          )}
        </Card>

        {/* Current Bid Status */}
        <Card className="p-6 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <h3 className="text-sm font-medium text-green-900 uppercase tracking-wide">
            Total Asset Value
          </h3>
          <p className="text-4xl font-bold text-green-700 mt-2">
            ${dashboard?.assets.total_value.toLocaleString() || '0'}
          </p>
          <p className="text-sm text-green-600 mt-2">{dashboard?.assets.count || 0} assets tracked</p>
        </Card>

        {/* At-Risk Items */}
        <Card className="p-6 bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
          <h3 className="text-sm font-medium text-yellow-900 uppercase tracking-wide">
            At-Risk Items
          </h3>
          <div className="mt-2 flex items-baseline space-x-2">
            <span className="text-4xl font-bold text-red-600">{atRiskItems.critical}</span>
            <span className="text-2xl font-bold text-yellow-600">{atRiskItems.warning}</span>
            <span className="text-2xl font-bold text-green-600">{atRiskItems.normal}</span>
          </div>
          <div className="flex items-center space-x-3 mt-2 text-xs">
            <span className="text-red-600">● Critical</span>
            <span className="text-yellow-600">● Warning</span>
            <span className="text-green-600">● Normal</span>
          </div>
        </Card>

        {/* Pending Objections */}
        <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <h3 className="text-sm font-medium text-purple-900 uppercase tracking-wide">
            Pending Objections
          </h3>
          <p className="text-4xl font-bold text-purple-700 mt-2">
            {dashboard?.objections.pending_count || 0}
          </p>
          <p className="text-sm text-purple-600 mt-2">Require response</p>
        </Card>
      </div>

      {/* Critical Path Summary */}
      {criticalPath && (
        <Card className="p-6 bg-blue-50 border-blue-200">
          <h2 className="text-xl font-bold text-blue-900 mb-4">Critical Path Analysis</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-blue-600 font-medium">Total Events</p>
              <p className="text-2xl font-bold text-blue-900">{criticalPath.total_events}</p>
            </div>
            <div>
              <p className="text-sm text-blue-600 font-medium">Critical Path Events</p>
              <p className="text-2xl font-bold text-blue-900">
                {criticalPath.critical_path_events.length}
              </p>
            </div>
            <div>
              <p className="text-sm text-blue-600 font-medium">Parallel Opportunities</p>
              <p className="text-2xl font-bold text-blue-900">
                {criticalPath.parallel_opportunities.length}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Required Actions This Week */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">Required Actions This Week</h2>
          <span className="bg-red-100 text-red-800 px-3 py-1 rounded-full text-sm font-medium">
            {actionItems?.urgent_items || 0} Urgent
          </span>
        </div>
        <div className="space-y-3">
          {actionItems?.action_items.slice(0, 5).map((item, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border-l-4 ${
                item.priority === 'URGENT' || item.priority === 'HIGH'
                  ? 'bg-red-50 border-red-500'
                  : item.priority === 'MEDIUM'
                  ? 'bg-yellow-50 border-yellow-500'
                  : 'bg-green-50 border-green-500'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-bold ${
                        item.priority === 'URGENT' || item.priority === 'HIGH'
                          ? 'bg-red-200 text-red-800'
                          : item.priority === 'MEDIUM'
                          ? 'bg-yellow-200 text-yellow-800'
                          : 'bg-green-200 text-green-800'
                      }`}
                    >
                      {item.priority}
                    </span>
                    <span className="text-xs text-gray-500">{item.category}</span>
                  </div>
                  <h3 className="font-semibold text-gray-900 mt-2">{item.task}</h3>
                  <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                  {item.due_date && (
                    <p className="text-xs text-gray-500 mt-2">
                      Due: {new Date(item.due_date).toLocaleDateString()}
                      {item.hours_remaining && ` (${item.hours_remaining}h remaining)`}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
        {actionItems && actionItems.action_items.length > 5 && (
          <button className="mt-4 w-full py-2 text-blue-600 hover:text-blue-700 font-medium">
            View All {actionItems.total_action_items} Action Items →
          </button>
        )}
      </Card>

      {/* Upcoming Deadlines */}
      <Card className="p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Upcoming Deadlines</h2>
        <div className="space-y-3">
          {dashboard?.deadlines.upcoming.slice(0, 5).map((deadline, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{deadline.title}</h3>
                <p className="text-sm text-gray-600 mt-1">
                  {new Date(deadline.date).toLocaleDateString('en-US', {
                    weekday: 'short',
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                  })}
                </p>
              </div>
              <div className="text-right">
                <p
                  className={`text-2xl font-bold ${
                    deadline.days_until <= 3
                      ? 'text-red-600'
                      : deadline.days_until <= 7
                      ? 'text-yellow-600'
                      : 'text-green-600'
                  }`}
                >
                  {deadline.days_until}
                </p>
                <p className="text-xs text-gray-500">days</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Risk Factors */}
      {strategicSummary?.risk_factors_and_mitigation && strategicSummary.risk_factors_and_mitigation.length > 0 && (
        <Card className="p-6 bg-orange-50 border-orange-200">
          <h2 className="text-xl font-bold text-orange-900 mb-4">Risk Factors</h2>
          <div className="space-y-3">
            {strategicSummary.risk_factors_and_mitigation.slice(0, 3).map((risk, index) => (
              <div key={index} className="p-4 bg-white rounded-lg border border-orange-200">
                <div className="flex items-center space-x-2 mb-2">
                  <span
                    className={`px-2 py-1 rounded text-xs font-bold ${
                      risk.severity === 'CRITICAL' || risk.severity === 'HIGH'
                        ? 'bg-red-200 text-red-800'
                        : 'bg-yellow-200 text-yellow-800'
                    }`}
                  >
                    {risk.severity}
                  </span>
                  <span className="text-sm font-medium text-gray-600">{risk.category}</span>
                </div>
                <h3 className="font-semibold text-gray-900">{risk.description}</h3>
                <p className="text-sm text-gray-600 mt-2">
                  <span className="font-medium">Impact:</span> {risk.impact}
                </p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
