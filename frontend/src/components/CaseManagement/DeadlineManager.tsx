/**
 * Deadline Manager Component
 * Displays all upcoming deadlines, action items, and critical dates with responsible parties
 */

'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { TimelineEvent, ActionItem, EventStatus } from '@/types/case-management';
import { caseManagementAPI } from '@/lib/api/case-management-api';

interface DeadlineManagerProps {
  caseId: string;
}

interface CombinedDeadline {
  id: string;
  title: string;
  description?: string;
  due_date: string;
  type: 'event' | 'action_item';
  status: EventStatus | 'pending' | 'in_progress' | 'completed';
  responsible_party?: string;
  priority?: 'critical' | 'high' | 'medium' | 'low';
  is_critical_path?: boolean;
  estimated_hours?: number;
  blocked_by?: string[];
  impact_summary?: string;
  original_data: TimelineEvent | ActionItem;
}

export default function DeadlineManager({ caseId }: DeadlineManagerProps) {
  const [deadlines, setDeadlines] = useState<CombinedDeadline[]>([]);
  const [selectedDeadline, setSelectedDeadline] = useState<CombinedDeadline | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [priorityFilter, setPriorityFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [showOnlyCritical, setShowOnlyCritical] = useState(false);

  const [filteredDeadlines, setFilteredDeadlines] = useState<CombinedDeadline[]>([]);

  useEffect(() => {
    loadDeadlines();
  }, [caseId]);

  useEffect(() => {
    applyFilters();
  }, [deadlines, statusFilter, priorityFilter, typeFilter, showOnlyCritical]);

  const loadDeadlines = async () => {
    try {
      setLoading(true);
      setError(null);

      const [events, actionItems, criticalPath] = await Promise.all([
        caseManagementAPI.events.list(caseId),
        caseManagementAPI.briefing.getActionItems(caseId),
        caseManagementAPI.timeline.getCriticalPath(caseId),
      ]);

      const combinedDeadlines: CombinedDeadline[] = [];

      // Process timeline events
      events.forEach((event: TimelineEvent) => {
        combinedDeadlines.push({
          id: `event-${event.id}`,
          title: event.event_name,
          description: event.description,
          due_date: event.scheduled_date,
          type: 'event',
          status: event.status,
          responsible_party: event.responsible_party,
          priority: event.is_critical ? 'critical' : 'medium',
          is_critical_path: criticalPath.critical_path_events?.some(
            (cp: any) => cp.event_id === event.id
          ),
          blocked_by: event.dependencies,
          original_data: event,
        });
      });

      // Process action items
      actionItems.action_items?.forEach((item: ActionItem) => {
        combinedDeadlines.push({
          id: `action-${item.action_id}`,
          title: item.description,
          description: item.rationale,
          due_date: item.deadline,
          type: 'action_item',
          status: item.completed ? 'completed' : 'pending',
          responsible_party: item.responsible_party,
          priority: item.priority as 'critical' | 'high' | 'medium' | 'low',
          estimated_hours: item.estimated_hours,
          blocked_by: item.depends_on,
          original_data: item,
        });
      });

      // Sort by date (soonest first)
      combinedDeadlines.sort((a, b) =>
        new Date(a.due_date).getTime() - new Date(b.due_date).getTime()
      );

      setDeadlines(combinedDeadlines);
      setLoading(false);
    } catch (err) {
      console.error('Error loading deadlines:', err);
      setError(err instanceof Error ? err.message : 'Failed to load deadlines');
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...deadlines];

    if (statusFilter !== 'all') {
      filtered = filtered.filter((d) => d.status === statusFilter);
    }

    if (priorityFilter !== 'all') {
      filtered = filtered.filter((d) => d.priority === priorityFilter);
    }

    if (typeFilter !== 'all') {
      filtered = filtered.filter((d) => d.type === typeFilter);
    }

    if (showOnlyCritical) {
      filtered = filtered.filter((d) => d.is_critical_path || d.priority === 'critical');
    }

    setFilteredDeadlines(filtered);
  };

  const getDaysUntil = (date: string): number => {
    const now = new Date();
    const deadline = new Date(date);
    const diffTime = deadline.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getPriorityColor = (priority?: string): string => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-green-100 text-green-800 border-green-300',
    };
    return colors[priority || 'medium'] || 'bg-gray-100 text-gray-800';
  };

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      scheduled: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-gray-100 text-gray-800',
      postponed: 'bg-orange-100 text-orange-800',
      missed: 'bg-red-100 text-red-800',
      pending: 'bg-purple-100 text-purple-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getUrgencyIndicator = (daysUntil: number): { text: string; color: string } => {
    if (daysUntil < 0) return { text: 'OVERDUE', color: 'text-red-600 font-bold' };
    if (daysUntil === 0) return { text: 'TODAY', color: 'text-red-600 font-bold' };
    if (daysUntil === 1) return { text: 'TOMORROW', color: 'text-orange-600 font-bold' };
    if (daysUntil <= 3) return { text: `${daysUntil} DAYS`, color: 'text-orange-600' };
    if (daysUntil <= 7) return { text: `${daysUntil} DAYS`, color: 'text-yellow-600' };
    if (daysUntil <= 30) return { text: `${daysUntil} DAYS`, color: 'text-blue-600' };
    return { text: `${daysUntil} DAYS`, color: 'text-gray-600' };
  };

  const getUpcomingCount = (days: number): number => {
    return deadlines.filter((d) => {
      const daysUntil = getDaysUntil(d.due_date);
      return daysUntil >= 0 && daysUntil <= days;
    }).length;
  };

  const getOverdueCount = (): number => {
    return deadlines.filter((d) => getDaysUntil(d.due_date) < 0).length;
  };

  const getCriticalCount = (): number => {
    return deadlines.filter((d) => d.is_critical_path || d.priority === 'critical').length;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={loadDeadlines}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Deadline Manager</h1>
            <p className="text-gray-600 mt-1">
              Track all upcoming deadlines, events, and action items
            </p>
          </div>
        </div>
      </Card>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6 bg-gradient-to-br from-red-50 to-red-100">
          <p className="text-sm text-red-600 font-medium">Overdue</p>
          <p className="text-3xl font-bold text-red-900">{getOverdueCount()}</p>
          <p className="text-sm text-red-700 mt-1">Past deadline</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-orange-50 to-orange-100">
          <p className="text-sm text-orange-600 font-medium">Next 7 Days</p>
          <p className="text-3xl font-bold text-orange-900">{getUpcomingCount(7)}</p>
          <p className="text-sm text-orange-700 mt-1">Due soon</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-purple-50 to-purple-100">
          <p className="text-sm text-purple-600 font-medium">Critical Path</p>
          <p className="text-3xl font-bold text-purple-900">{getCriticalCount()}</p>
          <p className="text-sm text-purple-700 mt-1">High priority</p>
        </Card>

        <Card className="p-6 bg-gradient-to-br from-blue-50 to-blue-100">
          <p className="text-sm text-blue-600 font-medium">Total Deadlines</p>
          <p className="text-3xl font-bold text-blue-900">{deadlines.length}</p>
          <p className="text-sm text-blue-700 mt-1">All items</p>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
              <option value="overdue">Overdue</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Priorities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="event">Timeline Events</option>
              <option value="action_item">Action Items</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Critical Only</label>
            <button
              onClick={() => setShowOnlyCritical(!showOnlyCritical)}
              className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                showOnlyCritical
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {showOnlyCritical ? 'Showing Critical' : 'Show All'}
            </button>
          </div>
        </div>
      </Card>

      {/* Deadline List */}
      <div className="space-y-4">
        {filteredDeadlines.map((deadline) => {
          const daysUntil = getDaysUntil(deadline.due_date);
          const urgency = getUrgencyIndicator(daysUntil);

          return (
            <Card
              key={deadline.id}
              onClick={() => setSelectedDeadline(deadline)}
              className={`p-6 cursor-pointer hover:shadow-lg transition-shadow ${
                deadline.is_critical_path ? 'border-2 border-purple-300' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                {/* Deadline Info */}
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <span
                      className={`px-3 py-1 rounded text-xs font-medium ${getPriorityColor(
                        deadline.priority
                      )}`}
                    >
                      {deadline.priority?.toUpperCase() || 'MEDIUM'}
                    </span>
                    <span
                      className={`px-3 py-1 rounded text-xs font-medium ${getStatusColor(
                        deadline.status
                      )}`}
                    >
                      {deadline.status.toUpperCase()}
                    </span>
                    <span className="px-3 py-1 rounded text-xs font-medium bg-gray-100 text-gray-800">
                      {deadline.type === 'event' ? '📅 EVENT' : '✓ ACTION ITEM'}
                    </span>
                    {deadline.is_critical_path && (
                      <span className="px-3 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800">
                        ⚡ CRITICAL PATH
                      </span>
                    )}
                  </div>

                  <h3 className="font-semibold text-gray-900 text-lg">{deadline.title}</h3>

                  {deadline.description && (
                    <p className="text-gray-600 mt-2 text-sm">{deadline.description}</p>
                  )}

                  <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-gray-600">Due Date</p>
                      <p className="text-gray-900 font-medium">
                        {new Date(deadline.due_date).toLocaleDateString()}
                      </p>
                    </div>
                    {deadline.responsible_party && (
                      <div>
                        <p className="text-gray-600">Responsible Party</p>
                        <p className="text-gray-900 font-medium">{deadline.responsible_party}</p>
                      </div>
                    )}
                    {deadline.estimated_hours && (
                      <div>
                        <p className="text-gray-600">Estimated Time</p>
                        <p className="text-gray-900 font-medium">{deadline.estimated_hours}h</p>
                      </div>
                    )}
                    {deadline.blocked_by && deadline.blocked_by.length > 0 && (
                      <div>
                        <p className="text-gray-600">Dependencies</p>
                        <p className="text-gray-900 font-medium">
                          {deadline.blocked_by.length} blocker(s)
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Days Until */}
                <div className="text-right ml-4">
                  <p className="text-sm text-gray-600 mb-1">Time Remaining</p>
                  <p className={`text-2xl font-bold ${urgency.color}`}>{urgency.text}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {new Date(deadline.due_date).toLocaleDateString()}
                  </p>
                </div>
              </div>

              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedDeadline(deadline);
                }}
                className="mt-4 text-blue-600 hover:text-blue-700 font-medium text-sm"
              >
                View Full Details →
              </button>
            </Card>
          );
        })}

        {filteredDeadlines.length === 0 && (
          <Card className="p-12 text-center">
            <p className="text-gray-500 text-lg">No deadlines match your filters</p>
            <button
              onClick={() => {
                setStatusFilter('all');
                setPriorityFilter('all');
                setTypeFilter('all');
                setShowOnlyCritical(false);
              }}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Clear All Filters
            </button>
          </Card>
        )}
      </div>

      {/* Detail Modal */}
      {selectedDeadline && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedDeadline(null)}
        >
          <Card
            className="max-w-3xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-6">
                <div className="flex-1">
                  <h2 className="text-2xl font-bold text-gray-900">{selectedDeadline.title}</h2>
                  <p className="text-gray-600 mt-1">
                    {selectedDeadline.type === 'event' ? 'Timeline Event' : 'Action Item'}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedDeadline(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              <div className="space-y-6">
                {/* Status and Priority */}
                <div className="flex space-x-3">
                  <span
                    className={`px-4 py-2 rounded font-medium ${getPriorityColor(
                      selectedDeadline.priority
                    )}`}
                  >
                    {selectedDeadline.priority?.toUpperCase() || 'MEDIUM'} PRIORITY
                  </span>
                  <span
                    className={`px-4 py-2 rounded font-medium ${getStatusColor(
                      selectedDeadline.status
                    )}`}
                  >
                    {selectedDeadline.status.toUpperCase()}
                  </span>
                  {selectedDeadline.is_critical_path && (
                    <span className="px-4 py-2 rounded font-medium bg-purple-100 text-purple-800">
                      ⚡ CRITICAL PATH
                    </span>
                  )}
                </div>

                {/* Description */}
                {selectedDeadline.description && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                    <p className="text-gray-700">{selectedDeadline.description}</p>
                  </div>
                )}

                {/* Details Grid */}
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Timeline</h3>
                    <div className="space-y-3 text-sm">
                      <div>
                        <p className="text-gray-600 font-medium">Due Date</p>
                        <p className="text-gray-900">
                          {new Date(selectedDeadline.due_date).toLocaleDateString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-600 font-medium">Days Remaining</p>
                        <p className={`font-bold ${getUrgencyIndicator(getDaysUntil(selectedDeadline.due_date)).color}`}>
                          {getUrgencyIndicator(getDaysUntil(selectedDeadline.due_date)).text}
                        </p>
                      </div>
                      {selectedDeadline.estimated_hours && (
                        <div>
                          <p className="text-gray-600 font-medium">Estimated Hours</p>
                          <p className="text-gray-900">{selectedDeadline.estimated_hours} hours</p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Responsibility</h3>
                    <div className="space-y-3 text-sm">
                      {selectedDeadline.responsible_party && (
                        <div>
                          <p className="text-gray-600 font-medium">Responsible Party</p>
                          <p className="text-gray-900">{selectedDeadline.responsible_party}</p>
                        </div>
                      )}
                      <div>
                        <p className="text-gray-600 font-medium">Item Type</p>
                        <p className="text-gray-900 capitalize">
                          {selectedDeadline.type === 'event' ? 'Timeline Event' : 'Action Item'}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Dependencies */}
                {selectedDeadline.blocked_by && selectedDeadline.blocked_by.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Dependencies</h3>
                    <div className="space-y-2">
                      {selectedDeadline.blocked_by.map((dep, idx) => (
                        <div key={idx} className="p-3 bg-yellow-50 rounded border border-yellow-200">
                          <p className="text-sm text-yellow-800 font-medium">⚠ Blocked by: {dep}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Type-specific data */}
                {selectedDeadline.type === 'event' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Event Details</h3>
                    <div className="text-sm text-gray-700">
                      <p>Event Type: {(selectedDeadline.original_data as TimelineEvent).event_type}</p>
                      <p>Location: {(selectedDeadline.original_data as TimelineEvent).location || 'TBD'}</p>
                    </div>
                  </div>
                )}

                {selectedDeadline.type === 'action_item' && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">Action Item Details</h3>
                    <div className="text-sm text-gray-700">
                      {(selectedDeadline.original_data as ActionItem).rationale && (
                        <p className="mb-2">
                          <span className="font-medium">Rationale:</span>{' '}
                          {(selectedDeadline.original_data as ActionItem).rationale}
                        </p>
                      )}
                      {(selectedDeadline.original_data as ActionItem).outcome && (
                        <p>
                          <span className="font-medium">Expected Outcome:</span>{' '}
                          {(selectedDeadline.original_data as ActionItem).outcome}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <button
                onClick={() => setSelectedDeadline(null)}
                className="mt-6 w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
              >
                Close
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
