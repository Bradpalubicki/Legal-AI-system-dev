'use client'

import React, { useState, useEffect } from 'react'
import {
  FileText,
  Brain,
  MessageSquare,
  User,
  Calendar,
  Clock,
  CheckCircle,
  AlertTriangle,
  Gavel,
  Upload,
  Search,
  Filter,
  Download
} from 'lucide-react'

interface TimelineEvent {
  id: string
  type: 'document_upload' | 'analysis_complete' | 'qa_interaction' | 'attorney_action' | 'court_date' | 'deadline' | 'outcome'
  title: string
  description: string
  timestamp: string
  metadata: {
    caseId?: string
    documentName?: string
    actionBy?: string
    priority?: 'low' | 'medium' | 'high' | 'critical'
    status?: 'pending' | 'completed' | 'failed'
    outcome?: string
  }
}

interface CaseTimelineProps {
  caseId?: string
  showAllCases?: boolean
}

export const CaseTimeline: React.FC<CaseTimelineProps> = ({
  caseId,
  showAllCases = false
}) => {
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [filteredEvents, setFilteredEvents] = useState<TimelineEvent[]>([])
  const [filters, setFilters] = useState({
    type: 'all',
    dateRange: 'all',
    priority: 'all',
    search: ''
  })
  const [isLoading, setIsLoading] = useState(false)

  // Mock data generator
  const generateMockEvents = (): TimelineEvent[] => {
    const now = new Date()
    const events: TimelineEvent[] = []

    // Generate events for the past 30 days
    for (let i = 0; i < 50; i++) {
      const eventDate = new Date(now.getTime() - Math.random() * 30 * 24 * 60 * 60 * 1000)
      const eventTypes: Array<TimelineEvent['type']> = [
        'document_upload', 'analysis_complete', 'qa_interaction',
        'attorney_action', 'court_date', 'deadline', 'outcome'
      ]
      const type = eventTypes[Math.floor(Math.random() * eventTypes.length)]

      events.push({
        id: `event_${i}`,
        type,
        title: generateEventTitle(type),
        description: generateEventDescription(type),
        timestamp: eventDate.toISOString(),
        metadata: {
          caseId: `case_${Math.floor(Math.random() * 5) + 1}`,
          documentName: type === 'document_upload' ? `Document_${i}.pdf` : undefined,
          actionBy: ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Lisa Chen'][Math.floor(Math.random() * 4)],
          priority: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)] as any,
          status: ['pending', 'completed', 'failed'][Math.floor(Math.random() * 3)] as any,
          outcome: type === 'outcome' ? ['favorable', 'unfavorable', 'settled'][Math.floor(Math.random() * 3)] : undefined
        }
      })
    }

    return events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
  }

  const generateEventTitle = (type: TimelineEvent['type']): string => {
    switch (type) {
      case 'document_upload': return 'Document Uploaded'
      case 'analysis_complete': return 'AI Analysis Completed'
      case 'qa_interaction': return 'Q&A Session'
      case 'attorney_action': return 'Attorney Action Taken'
      case 'court_date': return 'Court Hearing'
      case 'deadline': return 'Deadline Reminder'
      case 'outcome': return 'Case Outcome'
      default: return 'Event'
    }
  }

  const generateEventDescription = (type: TimelineEvent['type']): string => {
    switch (type) {
      case 'document_upload': return 'New document uploaded and queued for processing'
      case 'analysis_complete': return 'AI analysis completed with risk assessment and recommendations'
      case 'qa_interaction': return 'Attorney asked questions and received AI-powered responses'
      case 'attorney_action': return 'Attorney performed case-related action or decision'
      case 'court_date': return 'Scheduled court hearing or proceeding'
      case 'deadline': return 'Important case deadline approaching or completed'
      case 'outcome': return 'Final case outcome or settlement reached'
      default: return 'Case event occurred'
    }
  }

  const getEventIcon = (type: TimelineEvent['type']) => {
    const iconClass = "w-5 h-5"
    switch (type) {
      case 'document_upload': return <Upload className={iconClass} />
      case 'analysis_complete': return <Brain className={iconClass} />
      case 'qa_interaction': return <MessageSquare className={iconClass} />
      case 'attorney_action': return <User className={iconClass} />
      case 'court_date': return <Gavel className={iconClass} />
      case 'deadline': return <Clock className={iconClass} />
      case 'outcome': return <CheckCircle className={iconClass} />
      default: return <Calendar className={iconClass} />
    }
  }

  const getEventColor = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'document_upload': return 'bg-blue-500'
      case 'analysis_complete': return 'bg-purple-500'
      case 'qa_interaction': return 'bg-green-500'
      case 'attorney_action': return 'bg-orange-500'
      case 'court_date': return 'bg-red-500'
      case 'deadline': return 'bg-yellow-500'
      case 'outcome': return 'bg-teal-500'
      default: return 'bg-gray-500'
    }
  }

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'critical': return 'text-red-800 bg-red-100 border-red-200'
      case 'high': return 'text-red-600 bg-red-50 border-red-200'
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low': return 'text-green-600 bg-green-50 border-green-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)

    if (diffInHours < 1) {
      return `${Math.floor(diffInHours * 60)} minutes ago`
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)} hours ago`
    } else if (diffInHours < 48) {
      return 'Yesterday'
    } else {
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
      })
    }
  }

  const applyFilters = () => {
    let filtered = events

    // Type filter
    if (filters.type !== 'all') {
      filtered = filtered.filter(event => event.type === filters.type)
    }

    // Priority filter
    if (filters.priority !== 'all') {
      filtered = filtered.filter(event => event.metadata.priority === filters.priority)
    }

    // Date range filter
    if (filters.dateRange !== 'all') {
      const now = new Date()
      let cutoffDate: Date

      switch (filters.dateRange) {
        case 'today':
          cutoffDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
          break
        case 'week':
          cutoffDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
          break
        case 'month':
          cutoffDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
          break
        default:
          cutoffDate = new Date(0)
      }

      filtered = filtered.filter(event => new Date(event.timestamp) >= cutoffDate)
    }

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      filtered = filtered.filter(event =>
        event.title.toLowerCase().includes(searchLower) ||
        event.description.toLowerCase().includes(searchLower) ||
        event.metadata.documentName?.toLowerCase().includes(searchLower) ||
        event.metadata.actionBy?.toLowerCase().includes(searchLower)
      )
    }

    setFilteredEvents(filtered)
  }

  const exportTimeline = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      caseId,
      events: filteredEvents,
      filters
    }

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `case-timeline-${caseId || 'all'}-${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  // Initialize data
  useEffect(() => {
    setIsLoading(true)
    // Simulate API call
    setTimeout(() => {
      const mockEvents = generateMockEvents()
      setEvents(mockEvents)
      setFilteredEvents(mockEvents)
      setIsLoading(false)
    }, 1000)
  }, [caseId])

  // Apply filters when they change
  useEffect(() => {
    applyFilters()
  }, [filters, events])

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {showAllCases ? 'All Cases Timeline' : `Case Timeline ${caseId ? `- ${caseId}` : ''}`}
            </h1>
            <p className="text-gray-600 mt-1">
              Chronological view of all case events and activities
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={exportTimeline}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <div className="flex items-center space-x-2">
            <Search className="w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search events..."
              value={filters.search}
              onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <select
            value={filters.type}
            onChange={(e) => setFilters(prev => ({ ...prev, type: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value="document_upload">Document Uploads</option>
            <option value="analysis_complete">AI Analysis</option>
            <option value="qa_interaction">Q&A Sessions</option>
            <option value="attorney_action">Attorney Actions</option>
            <option value="court_date">Court Dates</option>
            <option value="deadline">Deadlines</option>
            <option value="outcome">Outcomes</option>
          </select>

          <select
            value={filters.dateRange}
            onChange={(e) => setFilters(prev => ({ ...prev, dateRange: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Time</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>

          <select
            value={filters.priority}
            onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Priorities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <div className="text-sm text-gray-500">
            {filteredEvents.length} of {events.length} events
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="flex-1 overflow-auto p-6">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            <span className="ml-3 text-gray-600">Loading timeline...</span>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div className="text-center py-12">
            <Calendar className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No events found</h3>
            <p className="text-gray-500">Try adjusting your filters to see more events</p>
          </div>
        ) : (
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-8 top-0 bottom-0 w-px bg-gray-200"></div>

            <div className="space-y-6">
              {filteredEvents.map((event, index) => (
                <div key={event.id} className="relative flex items-start">
                  {/* Timeline dot */}
                  <div className={`relative flex items-center justify-center w-16 h-16 rounded-full ${getEventColor(event.type)} text-white shadow-lg z-10`}>
                    {getEventIcon(event.type)}
                  </div>

                  {/* Event content */}
                  <div className="ml-6 flex-1 min-w-0">
                    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-4 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <h3 className="text-lg font-medium text-gray-900">{event.title}</h3>
                            {event.metadata.priority && (
                              <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(event.metadata.priority)}`}>
                                {event.metadata.priority}
                              </span>
                            )}
                            {event.metadata.status && (
                              <span className={`px-2 py-1 text-xs rounded-full ${
                                event.metadata.status === 'completed' ? 'bg-green-100 text-green-800' :
                                event.metadata.status === 'failed' ? 'bg-red-100 text-red-800' :
                                'bg-yellow-100 text-yellow-800'
                              }`}>
                                {event.metadata.status}
                              </span>
                            )}
                          </div>

                          <p className="text-gray-600 mb-3">{event.description}</p>

                          <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
                            {event.metadata.caseId && (
                              <div>
                                <span className="font-medium">Case:</span> {event.metadata.caseId}
                              </div>
                            )}
                            {event.metadata.actionBy && (
                              <div>
                                <span className="font-medium">By:</span> {event.metadata.actionBy}
                              </div>
                            )}
                            {event.metadata.documentName && (
                              <div>
                                <span className="font-medium">Document:</span> {event.metadata.documentName}
                              </div>
                            )}
                            {event.metadata.outcome && (
                              <div>
                                <span className="font-medium">Outcome:</span>
                                <span className={`ml-1 capitalize ${
                                  event.metadata.outcome === 'favorable' ? 'text-green-600' :
                                  event.metadata.outcome === 'unfavorable' ? 'text-red-600' :
                                  'text-blue-600'
                                }`}>
                                  {event.metadata.outcome}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">
                            {formatDate(event.timestamp)}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {new Date(event.timestamp).toLocaleTimeString('en-US', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}