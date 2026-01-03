/**
 * Timeline Gantt Chart Visualization
 * Interactive Gantt chart with dependencies, status indicators, and filtering
 */

'use client';

import React, { useEffect, useState, useRef } from 'react';
import { Card } from '@/components/ui/card';
import {
  TimelineEvent,
  CriticalPathAnalysis,
  EventType,
  EventStatus,
} from '@/types/case-management';
import { caseManagementAPI } from '@/lib/api/case-management-api';

interface TimelineGanttChartProps {
  caseId: string;
}

interface FilterOptions {
  eventType: EventType | 'all';
  status: EventStatus | 'all';
  showCriticalPathOnly: boolean;
}

export default function TimelineGanttChart({ caseId }: TimelineGanttChartProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [criticalPath, setCriticalPath] = useState<CriticalPathAnalysis | null>(null);
  const [filters, setFilters] = useState<FilterOptions>({
    eventType: 'all',
    status: 'all',
    showCriticalPathOnly: false,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);

  useEffect(() => {
    loadTimelineData();
  }, [caseId]);

  const loadTimelineData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [eventsData, criticalPathData] = await Promise.all([
        caseManagementAPI.events.list(caseId),
        caseManagementAPI.timeline.getCriticalPath(caseId),
      ]);

      setEvents(eventsData);
      setCriticalPath(criticalPathData);
      setLoading(false);
    } catch (err) {
      console.error('Error loading timeline:', err);
      setError(err instanceof Error ? err.message : 'Failed to load timeline');
      setLoading(false);
    }
  };

  const getFilteredEvents = (): TimelineEvent[] => {
    let filtered = [...events];

    if (filters.eventType !== 'all') {
      filtered = filtered.filter((e) => e.event_type === filters.eventType);
    }

    if (filters.status !== 'all') {
      filtered = filtered.filter((e) => e.status === filters.status);
    }

    if (filters.showCriticalPathOnly && criticalPath) {
      const criticalIds = new Set(criticalPath.critical_path_events.map((e) => e.id));
      filtered = filtered.filter((e) => criticalIds.has(e.id));
    }

    return filtered.sort((a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime());
  };

  const getStatusColor = (status: EventStatus): string => {
    const colors = {
      scheduled: 'bg-blue-500',
      in_progress: 'bg-yellow-500',
      completed: 'bg-green-500',
      cancelled: 'bg-gray-400',
      postponed: 'bg-orange-500',
      missed: 'bg-red-500',
    };
    return colors[status] || 'bg-gray-500';
  };

  const getEventTypeIcon = (type: EventType): string => {
    const icons = {
      filing: '📄',
      hearing: '⚖️',
      deadline: '⏰',
      meeting: '👥',
      objection: '⚠️',
      motion: '📋',
      order: '📜',
      payment: '💰',
      auction: '🔨',
      confirmation: '✓',
      discharge: '✅',
      other: '📌',
    };
    return icons[type] || '📌';
  };

  const getDaysUntil = (dateStr: string): number => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  };

  const filteredEvents = getFilteredEvents();

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
          onClick={loadTimelineData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Filters */}
      <Card className="p-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Timeline & Gantt Chart</h1>
            <p className="text-gray-600 mt-1">
              {filteredEvents.length} events {filters.showCriticalPathOnly && '(Critical Path Only)'}
            </p>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap gap-3">
            {/* Event Type Filter */}
            <select
              value={filters.eventType}
              onChange={(e) => setFilters({ ...filters, eventType: e.target.value as EventType | 'all' })}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Types</option>
              <option value="filing">Filing</option>
              <option value="hearing">Hearing</option>
              <option value="deadline">Deadline</option>
              <option value="meeting">Meeting</option>
              <option value="objection">Objection</option>
              <option value="motion">Motion</option>
              <option value="auction">Auction</option>
            </select>

            {/* Status Filter */}
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value as EventStatus | 'all' })}
              className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Status</option>
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="postponed">Postponed</option>
            </select>

            {/* Critical Path Toggle */}
            <button
              onClick={() =>
                setFilters({ ...filters, showCriticalPathOnly: !filters.showCriticalPathOnly })
              }
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filters.showCriticalPathOnly
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {filters.showCriticalPathOnly ? '🔴 Critical Path' : '⚪ Show Critical Path'}
            </button>
          </div>
        </div>
      </Card>

      {/* Critical Path Summary */}
      {criticalPath && (
        <Card className="p-6 bg-gradient-to-r from-red-50 to-orange-50 border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-red-900">Critical Path Analysis</h2>
              <p className="text-sm text-red-700 mt-1">
                {criticalPath.critical_path_events.length} events on critical path (zero slack time)
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-red-600">Estimated Completion</p>
              <p className="text-lg font-bold text-red-900">
                {criticalPath.estimated_completion
                  ? new Date(criticalPath.estimated_completion).toLocaleDateString()
                  : 'TBD'}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Gantt Chart View */}
      <Card className="p-6">
        <div className="space-y-2">
          {filteredEvents.map((event) => {
            const daysUntil = getDaysUntil(event.event_date);
            const isCritical = criticalPath?.critical_path_events.some((e) => e.id === event.id);
            const hasDependencies = (event.blocked_by_event_ids?.length || 0) > 0;
            const blocksOthers = (event.blocks_event_ids?.length || 0) > 0;

            return (
              <div
                key={event.id}
                onClick={() => setSelectedEvent(event)}
                className={`relative p-4 rounded-lg border-l-4 cursor-pointer transition-all hover:shadow-md ${
                  isCritical
                    ? 'bg-red-50 border-red-500'
                    : event.status === 'completed'
                    ? 'bg-green-50 border-green-500'
                    : 'bg-white border-blue-500'
                } ${selectedEvent?.id === event.id ? 'ring-2 ring-blue-500' : ''}`}
              >
                <div className="flex items-start justify-between">
                  {/* Event Info */}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-xl">{getEventTypeIcon(event.event_type)}</span>
                      <span className={`w-3 h-3 rounded-full ${getStatusColor(event.status)}`}></span>
                      <span className="text-xs uppercase font-medium text-gray-600">
                        {event.event_type.replace('_', ' ')}
                      </span>
                      {isCritical && (
                        <span className="bg-red-600 text-white px-2 py-0.5 rounded text-xs font-bold">
                          CRITICAL
                        </span>
                      )}
                      {event.priority_level === 1 && (
                        <span className="bg-orange-600 text-white px-2 py-0.5 rounded text-xs font-bold">
                          HIGH PRIORITY
                        </span>
                      )}
                    </div>

                    <h3 className="font-semibold text-gray-900">{event.title}</h3>
                    {event.description && (
                      <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                    )}

                    {/* Dependencies */}
                    <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                      {hasDependencies && (
                        <span className="flex items-center">
                          ⬅️ Blocked by {event.blocked_by_event_ids?.length} event(s)
                        </span>
                      )}
                      {blocksOthers && (
                        <span className="flex items-center">
                          ➡️ Blocks {event.blocks_event_ids?.length} event(s)
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Date & Status */}
                  <div className="text-right ml-4">
                    <p className="text-sm font-medium text-gray-700">
                      {new Date(event.event_date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </p>
                    <p
                      className={`text-lg font-bold mt-1 ${
                        daysUntil < 0
                          ? 'text-red-600'
                          : daysUntil <= 3
                          ? 'text-orange-600'
                          : daysUntil <= 7
                          ? 'text-yellow-600'
                          : 'text-green-600'
                      }`}
                    >
                      {daysUntil < 0
                        ? `${Math.abs(daysUntil)}d overdue`
                        : daysUntil === 0
                        ? 'Today'
                        : `${daysUntil}d`}
                    </p>
                    <p className="text-xs text-gray-500 capitalize">{event.status.replace('_', ' ')}</p>
                  </div>
                </div>

                {/* Progress Bar */}
                {event.completion_percentage !== undefined && event.completion_percentage > 0 && (
                  <div className="mt-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${event.completion_percentage}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{event.completion_percentage}% complete</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {filteredEvents.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <p className="text-lg">No events match the current filters</p>
            <button
              onClick={() => setFilters({ eventType: 'all', status: 'all', showCriticalPathOnly: false })}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Clear Filters
            </button>
          </div>
        )}
      </Card>

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedEvent(null)}
        >
          <Card
            className="max-w-2xl w-full max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedEvent.title}</h2>
                  <p className="text-gray-600 mt-1">
                    {getEventTypeIcon(selectedEvent.event_type)} {selectedEvent.event_type.replace('_', ' ')}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
                >
                  ×
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm font-medium text-gray-600">Date & Time</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {new Date(selectedEvent.event_date).toLocaleString()}
                  </p>
                </div>

                {selectedEvent.location && (
                  <div>
                    <p className="text-sm font-medium text-gray-600">Location</p>
                    <p className="text-gray-900">{selectedEvent.location}</p>
                  </div>
                )}

                {selectedEvent.description && (
                  <div>
                    <p className="text-sm font-medium text-gray-600">Description</p>
                    <p className="text-gray-900">{selectedEvent.description}</p>
                  </div>
                )}

                <div>
                  <p className="text-sm font-medium text-gray-600">Status</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`w-3 h-3 rounded-full ${getStatusColor(selectedEvent.status)}`}></span>
                    <span className="capitalize">{selectedEvent.status.replace('_', ' ')}</span>
                  </div>
                </div>

                {selectedEvent.required_actions && selectedEvent.required_actions.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-2">Required Actions</p>
                    <ul className="list-disc list-inside space-y-1">
                      {selectedEvent.required_actions.map((action, idx) => (
                        <li key={idx} className="text-gray-900">
                          {typeof action === 'string' ? action : JSON.stringify(action)}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <button
                  onClick={() => setSelectedEvent(null)}
                  className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
