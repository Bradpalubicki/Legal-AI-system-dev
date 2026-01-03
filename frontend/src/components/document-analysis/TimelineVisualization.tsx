'use client';

import React, { useState } from 'react';
import {
  Calendar,
  Clock,
  AlertTriangle,
  CheckCircle,
  Info,
  Bell,
  ArrowRight,
  MapPin,
  Filter,
  Download,
  Eye
} from 'lucide-react';

interface TimelineEvent {
  date: string;
  event: string;
  significance: string;
  importance: 'High' | 'Medium' | 'Low';
  type: 'deadline' | 'event' | 'general';
  consequences?: string;
  parties_affected?: string[];
  context?: string;
  why_important?: string;
  action_required?: string;
  consequence_if_missed?: string;
}

interface TimelineVisualizationProps {
  events: TimelineEvent[];
  title?: string;
  showFilters?: boolean;
  showDetails?: boolean;
  onEventClick?: (event: TimelineEvent) => void;
}

const TimelineVisualization: React.FC<TimelineVisualizationProps> = ({
  events,
  title = "Document Timeline",
  showFilters = true,
  showDetails = true,
  onEventClick
}) => {
  const [filter, setFilter] = useState<'all' | 'deadline' | 'event' | 'general'>('all');
  const [importanceFilter, setImportanceFilter] = useState<'all' | 'High' | 'Medium' | 'Low'>('all');
  const [selectedEvent, setSelectedEvent] = useState<TimelineEvent | null>(null);
  const [viewMode, setViewMode] = useState<'timeline' | 'list'>('timeline');

  const parseDate = (dateStr: string): Date => {
    try {
      return new Date(dateStr);
    } catch {
      return new Date();
    }
  };

  const formatDate = (dateStr: string): string => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const getDaysFromNow = (dateStr: string): number => {
    try {
      const date = new Date(dateStr);
      const now = new Date();
      const diffTime = date.getTime() - now.getTime();
      return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    } catch {
      return 0;
    }
  };

  const getEventColor = (event: TimelineEvent) => {
    const daysFromNow = getDaysFromNow(event.date);

    if (event.type === 'deadline' && daysFromNow < 30 && daysFromNow > 0) {
      return 'border-red-500 bg-red-50';
    }

    switch (event.importance) {
      case 'High':
        return 'border-red-400 bg-red-50';
      case 'Medium':
        return 'border-yellow-400 bg-yellow-50';
      case 'Low':
        return 'border-blue-400 bg-blue-50';
      default:
        return 'border-gray-400 bg-gray-50';
    }
  };

  const getEventIcon = (event: TimelineEvent) => {
    const daysFromNow = getDaysFromNow(event.date);

    if (event.type === 'deadline') {
      if (daysFromNow < 0) {
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      } else if (daysFromNow < 30) {
        return <Bell className="h-4 w-4 text-orange-600" />;
      } else {
        return <Clock className="h-4 w-4 text-blue-600" />;
      }
    }

    switch (event.importance) {
      case 'High':
        return <AlertTriangle className="h-4 w-4 text-red-600" />;
      case 'Medium':
        return <Info className="h-4 w-4 text-yellow-600" />;
      case 'Low':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      default:
        return <Calendar className="h-4 w-4 text-gray-600" />;
    }
  };

  const getTimelinePosition = (event: TimelineEvent, index: number, totalEvents: number) => {
    // Sort events by date to position them correctly
    const sortedEvents = [...events].sort((a, b) =>
      parseDate(a.date).getTime() - parseDate(b.date).getTime()
    );
    const eventIndex = sortedEvents.findIndex(e => e.date === event.date && e.event === event.event);
    return (eventIndex / Math.max(totalEvents - 1, 1)) * 100;
  };

  const filteredEvents = events.filter(event => {
    const typeMatch = filter === 'all' || event.type === filter;
    const importanceMatch = importanceFilter === 'all' || event.importance === importanceFilter;
    return typeMatch && importanceMatch;
  });

  const sortedEvents = [...filteredEvents].sort((a, b) =>
    parseDate(a.date).getTime() - parseDate(b.date).getTime()
  );

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Calendar className="h-5 w-5 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {filteredEvents.length} events
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode(viewMode === 'timeline' ? 'list' : 'timeline')}
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
              title={`Switch to ${viewMode === 'timeline' ? 'list' : 'timeline'} view`}
            >
              {viewMode === 'timeline' ? <Eye className="h-4 w-4" /> : <MapPin className="h-4 w-4" />}
            </button>
            <button
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
              title="Download timeline"
            >
              <Download className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-3 flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-500" />
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value as any)}
                className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Types</option>
                <option value="deadline">Deadlines</option>
                <option value="event">Events</option>
                <option value="general">General</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <select
                value={importanceFilter}
                onChange={(e) => setImportanceFilter(e.target.value as any)}
                className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Importance</option>
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {sortedEvents.length === 0 ? (
          <div className="text-center py-8">
            <Calendar className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No timeline events found</p>
          </div>
        ) : viewMode === 'timeline' ? (
          /* Timeline View */
          <div className="relative">
            {/* Timeline Line */}
            <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-300"></div>

            {/* Timeline Events */}
            <div className="space-y-6">
              {sortedEvents.map((event, index) => {
                const daysFromNow = getDaysFromNow(event.date);
                const isUpcoming = daysFromNow > 0 && daysFromNow <= 30;
                const isPast = daysFromNow < 0;

                return (
                  <div
                    key={index}
                    className={`relative flex items-start space-x-4 p-4 rounded-lg border ${getEventColor(event)} ${
                      onEventClick ? 'cursor-pointer hover:shadow-md' : ''
                    } transition-all`}
                    onClick={() => {
                      setSelectedEvent(event);
                      onEventClick?.(event);
                    }}
                  >
                    {/* Timeline Node */}
                    <div className="absolute -left-2 top-6 w-4 h-4 bg-white border-2 border-gray-300 rounded-full flex items-center justify-center">
                      <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
                    </div>

                    {/* Event Icon */}
                    <div className="flex-shrink-0 p-2 bg-white rounded-lg border">
                      {getEventIcon(event)}
                    </div>

                    {/* Event Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-sm font-semibold text-gray-900 mb-1">
                            {formatDate(event.date)}
                          </h4>
                          <p className="text-sm text-gray-800 mb-2">
                            {event.event}
                          </p>

                          {showDetails && (
                            <div className="space-y-2 mt-2">
                              {/* WHY This Date Matters */}
                              {event.why_important && (
                                <div className="flex items-start space-x-2">
                                  <span className="inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800 flex-shrink-0">
                                    WHY
                                  </span>
                                  <p className="text-sm text-gray-700">{event.why_important}</p>
                                </div>
                              )}

                              {/* ACTION Required */}
                              {event.action_required && (
                                <div className="flex items-start space-x-2">
                                  <span className="inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-xs font-semibold bg-green-100 text-green-800 flex-shrink-0">
                                    ACTION
                                  </span>
                                  <p className="text-sm text-gray-700">{event.action_required}</p>
                                </div>
                              )}

                              {/* RISK if missed */}
                              {(event.consequence_if_missed || event.consequences) && (
                                <div className="flex items-start space-x-2">
                                  <span className="inline-flex items-center justify-center w-16 px-2 py-0.5 rounded text-xs font-semibold bg-red-100 text-red-800 flex-shrink-0">
                                    RISK
                                  </span>
                                  <p className="text-sm text-red-700 font-medium">
                                    {event.consequence_if_missed || event.consequences}
                                  </p>
                                </div>
                              )}

                              {/* Fallback to significance for old data */}
                              {!event.why_important && !event.action_required && event.significance && (
                                <p className="text-xs text-gray-600">
                                  <strong>Significance:</strong> {event.significance}
                                </p>
                              )}

                              {event.parties_affected && event.parties_affected.length > 0 && (
                                <p className="text-xs text-gray-600">
                                  <strong>Affects:</strong> {event.parties_affected.join(', ')}
                                </p>
                              )}
                            </div>
                          )}
                        </div>

                        <div className="flex flex-col items-end space-y-2 ml-4">
                          {/* Importance Badge */}
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            event.importance === 'High' ? 'bg-red-100 text-red-800' :
                            event.importance === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          }`}>
                            {event.importance}
                          </span>

                          {/* Time Indicator */}
                          {event.type === 'deadline' && (
                            <div className="text-right">
                              <p className={`text-xs font-medium ${
                                isPast ? 'text-red-600' :
                                isUpcoming ? 'text-orange-600' :
                                'text-gray-600'
                              }`}>
                                {isPast ? `${Math.abs(daysFromNow)} days ago` :
                                 daysFromNow === 0 ? 'Today' :
                                 daysFromNow === 1 ? 'Tomorrow' :
                                 `${daysFromNow} days away`}
                              </p>
                              {isUpcoming && (
                                <p className="text-xs text-orange-600 font-medium">
                                  <Bell className="h-3 w-3 inline mr-1" />
                                  Upcoming deadline
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          /* List View */
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Event
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Importance
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {sortedEvents.map((event, index) => {
                  const daysFromNow = getDaysFromNow(event.date);
                  const isPast = daysFromNow < 0;
                  const isUpcoming = daysFromNow > 0 && daysFromNow <= 30;

                  return (
                    <tr
                      key={index}
                      className={`hover:bg-gray-50 ${onEventClick ? 'cursor-pointer' : ''}`}
                      onClick={() => onEventClick?.(event)}
                    >
                      <td className="px-4 py-3 text-sm text-gray-900">
                        {formatDate(event.date)}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-900">
                        <div>
                          <p className="font-medium">{event.event}</p>
                          <p className="text-xs text-gray-500">{event.significance}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 capitalize">
                          {event.type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          event.importance === 'High' ? 'bg-red-100 text-red-800' :
                          event.importance === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {event.importance}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {event.type === 'deadline' ? (
                          <div className="flex items-center space-x-1">
                            {isPast ? (
                              <>
                                <AlertTriangle className="h-4 w-4 text-red-500" />
                                <span className="text-red-600 font-medium">Overdue</span>
                              </>
                            ) : isUpcoming ? (
                              <>
                                <Bell className="h-4 w-4 text-orange-500" />
                                <span className="text-orange-600 font-medium">
                                  {daysFromNow} days
                                </span>
                              </>
                            ) : (
                              <>
                                <CheckCircle className="h-4 w-4 text-green-500" />
                                <span className="text-green-600">Future</span>
                              </>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-500">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-1">
              <AlertTriangle className="h-3 w-3 text-red-500" />
              <span>High Priority / Overdue</span>
            </div>
            <div className="flex items-center space-x-1">
              <Bell className="h-3 w-3 text-orange-500" />
              <span>Upcoming Deadline</span>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircle className="h-3 w-3 text-green-500" />
              <span>Completed / Future</span>
            </div>
          </div>
          <div className="text-gray-500">
            Click events for more details
          </div>
        </div>
      </div>

      {/* Event Details Modal */}
      {selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-lg w-full max-h-96 overflow-y-auto">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Event Details</h3>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
            </div>
            <div className="p-4 space-y-3">
              <div>
                <label className="text-sm font-medium text-gray-700">Date</label>
                <p className="text-sm text-gray-900">{formatDate(selectedEvent.date)}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Event</label>
                <p className="text-sm text-gray-900">{selectedEvent.event}</p>
              </div>

              {/* WHY This Date Matters */}
              {selectedEvent.why_important && (
                <div className="bg-blue-50 p-3 rounded-lg">
                  <label className="text-sm font-semibold text-blue-900 flex items-center">
                    <span className="inline-flex items-center justify-center w-12 px-2 py-0.5 rounded text-xs font-semibold bg-blue-200 text-blue-800 mr-2">WHY</span>
                    Why This Matters
                  </label>
                  <p className="text-sm text-blue-800 mt-1">{selectedEvent.why_important}</p>
                </div>
              )}

              {/* ACTION Required */}
              {selectedEvent.action_required && (
                <div className="bg-green-50 p-3 rounded-lg">
                  <label className="text-sm font-semibold text-green-900 flex items-center">
                    <span className="inline-flex items-center justify-center w-12 px-2 py-0.5 rounded text-xs font-semibold bg-green-200 text-green-800 mr-2">ACTION</span>
                    What To Do
                  </label>
                  <p className="text-sm text-green-800 mt-1">{selectedEvent.action_required}</p>
                </div>
              )}

              {/* RISK if missed */}
              {(selectedEvent.consequence_if_missed || selectedEvent.consequences) && (
                <div className="bg-red-50 p-3 rounded-lg">
                  <label className="text-sm font-semibold text-red-900 flex items-center">
                    <span className="inline-flex items-center justify-center w-12 px-2 py-0.5 rounded text-xs font-semibold bg-red-200 text-red-800 mr-2">RISK</span>
                    If Missed
                  </label>
                  <p className="text-sm text-red-800 mt-1 font-medium">
                    {selectedEvent.consequence_if_missed || selectedEvent.consequences}
                  </p>
                </div>
              )}

              {/* Fallback for old data */}
              {!selectedEvent.why_important && selectedEvent.significance && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Significance</label>
                  <p className="text-sm text-gray-900">{selectedEvent.significance}</p>
                </div>
              )}

              {selectedEvent.context && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Context</label>
                  <p className="text-sm text-gray-900">{selectedEvent.context}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TimelineVisualization;