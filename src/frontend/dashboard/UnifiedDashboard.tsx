'use client'

import React, { useState, useEffect } from 'react'
import { DndProvider, useDrag, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { Rnd } from 'react-rnd'
import {
  FileText,
  Brain,
  MessageSquare,
  Shield,
  TrendingUp,
  Clock,
  CheckSquare,
  Bell,
  Download,
  Share,
  Filter,
  Settings,
  Maximize,
  RefreshCw
} from 'lucide-react'

import { useWebSocket } from '../hooks/useWebSocket'
import { useRealTimeData } from '../hooks/useRealTimeData'
import { DocumentProcessingWidget } from '../components/widgets/DocumentProcessingWidget'
import { AIAnalysisWidget } from '../components/widgets/AIAnalysisWidget'
import { QAWidget } from '../components/widgets/QAWidget'
import { DefenseStrategyWidget } from '../components/widgets/DefenseStrategyWidget'
import { AttorneyMetricsWidget } from '../components/widgets/AttorneyMetricsWidget'
import { DeadlineWidget } from '../components/widgets/DeadlineWidget'
import { ActionItemsWidget } from '../components/widgets/ActionItemsWidget'
import { NotificationsWidget } from '../components/widgets/NotificationsWidget'

interface Widget {
  id: string
  type: string
  title: string
  icon: React.ComponentType
  component: React.ComponentType<any>
  position: { x: number; y: number }
  size: { width: number; height: number }
  minimized: boolean
}

interface DashboardLayout {
  widgets: Widget[]
  filters: {
    timeRange: string
    caseType: string
    priority: string
  }
}

const defaultWidgets: Widget[] = [
  {
    id: 'document-processing',
    type: 'document',
    title: 'Document Processing',
    icon: FileText,
    component: DocumentProcessingWidget,
    position: { x: 0, y: 0 },
    size: { width: 400, height: 300 },
    minimized: false
  },
  {
    id: 'ai-analysis',
    type: 'analysis',
    title: 'AI Analysis Progress',
    icon: Brain,
    component: AIAnalysisWidget,
    position: { x: 420, y: 0 },
    size: { width: 400, height: 300 },
    minimized: false
  },
  {
    id: 'qa-responses',
    type: 'qa',
    title: 'Q&A Responses',
    icon: MessageSquare,
    component: QAWidget,
    position: { x: 840, y: 0 },
    size: { width: 400, height: 300 },
    minimized: false
  },
  {
    id: 'defense-strategies',
    type: 'strategy',
    title: 'Defense Strategies',
    icon: Shield,
    component: DefenseStrategyWidget,
    position: { x: 0, y: 320 },
    size: { width: 400, height: 300 },
    minimized: false
  },
  {
    id: 'attorney-metrics',
    type: 'metrics',
    title: 'Attorney Performance',
    icon: TrendingUp,
    component: AttorneyMetricsWidget,
    position: { x: 420, y: 320 },
    size: { width: 400, height: 300 },
    minimized: false
  },
  {
    id: 'deadlines',
    type: 'deadline',
    title: 'Deadline Countdown',
    icon: Clock,
    component: DeadlineWidget,
    position: { x: 840, y: 320 },
    size: { width: 400, height: 300 },
    minimized: false
  },
  {
    id: 'action-items',
    type: 'actions',
    title: 'Action Items',
    icon: CheckSquare,
    component: ActionItemsWidget,
    position: { x: 0, y: 640 },
    size: { width: 620, height: 250 },
    minimized: false
  },
  {
    id: 'notifications',
    type: 'notifications',
    title: 'System Notifications',
    icon: Bell,
    component: NotificationsWidget,
    position: { x: 640, y: 640 },
    size: { width: 600, height: 250 },
    minimized: false
  }
]

export const UnifiedDashboard: React.FC = () => {
  const [dashboardLayout, setDashboardLayout] = useState<DashboardLayout>({
    widgets: defaultWidgets,
    filters: {
      timeRange: 'today',
      caseType: 'all',
      priority: 'all'
    }
  })

  const [selectedWidget, setSelectedWidget] = useState<string | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  // Real-time data connections
  const { isConnected, lastMessage } = useWebSocket('ws://localhost:8001/ws/dashboard')
  const { data: realTimeData, isLoading } = useRealTimeData()

  // Auto-refresh every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      // Trigger data refresh
      window.dispatchEvent(new CustomEvent('dashboard-refresh'))
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  // Handle WebSocket updates
  useEffect(() => {
    if (lastMessage) {
      try {
        const update = JSON.parse(lastMessage.data)
        handleRealTimeUpdate(update)
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error)
      }
    }
  }, [lastMessage])

  const handleRealTimeUpdate = (update: any) => {
    // Broadcast update to all widgets
    window.dispatchEvent(new CustomEvent('real-time-update', {
      detail: update
    }))
  }

  const updateWidgetPosition = (widgetId: string, position: { x: number; y: number }) => {
    setDashboardLayout(prev => ({
      ...prev,
      widgets: prev.widgets.map(widget =>
        widget.id === widgetId ? { ...widget, position } : widget
      )
    }))
  }

  const updateWidgetSize = (widgetId: string, size: { width: number; height: number }) => {
    setDashboardLayout(prev => ({
      ...prev,
      widgets: prev.widgets.map(widget =>
        widget.id === widgetId ? { ...widget, size } : widget
      )
    }))
  }

  const toggleWidgetMinimized = (widgetId: string) => {
    setDashboardLayout(prev => ({
      ...prev,
      widgets: prev.widgets.map(widget =>
        widget.id === widgetId ? { ...widget, minimized: !widget.minimized } : widget
      )
    }))
  }

  const exportDashboardData = async () => {
    try {
      // Collect data from all widgets
      const dashboardData = {
        timestamp: new Date().toISOString(),
        layout: dashboardLayout,
        data: realTimeData,
        filters: dashboardLayout.filters
      }

      // Create downloadable file
      const blob = new Blob([JSON.stringify(dashboardData, null, 2)], {
        type: 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `legal-dashboard-${new Date().toISOString().split('T')[0]}.json`
      link.click()
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to export dashboard data:', error)
    }
  }

  const shareDashboard = async () => {
    try {
      // Generate shareable link
      const shareData = {
        layout: dashboardLayout,
        filters: dashboardLayout.filters,
        timestamp: Date.now()
      }

      const shareUrl = `${window.location.origin}/dashboard/shared?data=${encodeURIComponent(JSON.stringify(shareData))}`

      if (navigator.share) {
        await navigator.share({
          title: 'Legal AI Dashboard',
          text: 'Check out this legal intelligence dashboard',
          url: shareUrl
        })
      } else {
        await navigator.clipboard.writeText(shareUrl)
        alert('Dashboard link copied to clipboard!')
      }
    } catch (error) {
      console.error('Failed to share dashboard:', error)
    }
  }

  const applyFilters = (filters: Partial<typeof dashboardLayout.filters>) => {
    setDashboardLayout(prev => ({
      ...prev,
      filters: { ...prev.filters, ...filters }
    }))
  }

  const DraggableWidget: React.FC<{ widget: Widget }> = ({ widget }) => {
    const [, ref] = useDrag({
      type: 'widget',
      item: { id: widget.id, type: widget.type }
    })

    const WidgetComponent = widget.component

    return (
      <Rnd
        ref={ref}
        position={widget.position}
        size={widget.size}
        onDragStop={(e, d) => updateWidgetPosition(widget.id, { x: d.x, y: d.y })}
        onResizeStop={(e, direction, ref, delta, position) => {
          updateWidgetSize(widget.id, {
            width: ref.offsetWidth,
            height: ref.offsetHeight
          })
          updateWidgetPosition(widget.id, position)
        }}
        className={`bg-white rounded-lg shadow-lg border ${
          selectedWidget === widget.id ? 'border-blue-500' : 'border-gray-200'
        } ${widget.minimized ? 'opacity-75' : ''}`}
        minWidth={300}
        minHeight={200}
        bounds="parent"
      >
        <div className="h-full flex flex-col">
          {/* Widget Header */}
          <div className="flex items-center justify-between p-3 border-b border-gray-100 bg-gray-50 rounded-t-lg cursor-move">
            <div className="flex items-center space-x-2">
              <widget.icon className="w-4 h-4 text-gray-600" />
              <h3 className="text-sm font-medium text-gray-900">{widget.title}</h3>
              {isConnected && (
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" title="Live Updates" />
              )}
            </div>
            <div className="flex items-center space-x-1">
              <button
                onClick={() => setSelectedWidget(widget.id)}
                className="p-1 hover:bg-gray-200 rounded"
                title="Focus Widget"
              >
                <Maximize className="w-3 h-3" />
              </button>
              <button
                onClick={() => toggleWidgetMinimized(widget.id)}
                className="p-1 hover:bg-gray-200 rounded"
                title={widget.minimized ? "Expand" : "Minimize"}
              >
                {widget.minimized ? "+" : "−"}
              </button>
            </div>
          </div>

          {/* Widget Content */}
          {!widget.minimized && (
            <div className="flex-1 p-3 overflow-auto">
              <WidgetComponent
                filters={dashboardLayout.filters}
                realTimeData={realTimeData}
                isSelected={selectedWidget === widget.id}
              />
            </div>
          )}
        </div>
      </Rnd>
    )
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-screen bg-gray-100 overflow-hidden">
        {/* Dashboard Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">Legal Intelligence Dashboard</h1>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              {/* Filters */}
              <select
                value={dashboardLayout.filters.timeRange}
                onChange={(e) => applyFilters({ timeRange: e.target.value })}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="today">Today</option>
                <option value="week">This Week</option>
                <option value="month">This Month</option>
                <option value="quarter">This Quarter</option>
              </select>

              <select
                value={dashboardLayout.filters.caseType}
                onChange={(e) => applyFilters({ caseType: e.target.value })}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="all">All Cases</option>
                <option value="civil">Civil</option>
                <option value="criminal">Criminal</option>
                <option value="corporate">Corporate</option>
                <option value="family">Family</option>
              </select>

              <select
                value={dashboardLayout.filters.priority}
                onChange={(e) => applyFilters({ priority: e.target.value })}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="all">All Priority</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>

              {/* Action Buttons */}
              <button
                onClick={() => window.location.reload()}
                className="flex items-center space-x-1 px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                title="Refresh Dashboard"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Refresh</span>
              </button>

              <button
                onClick={exportDashboardData}
                className="flex items-center space-x-1 px-3 py-1 text-sm bg-green-500 text-white rounded hover:bg-green-600"
                title="Export Data"
              >
                <Download className="w-3 h-3" />
                <span>Export</span>
              </button>

              <button
                onClick={shareDashboard}
                className="flex items-center space-x-1 px-3 py-1 text-sm bg-purple-500 text-white rounded hover:bg-purple-600"
                title="Share Dashboard"
              >
                <Share className="w-3 h-3" />
                <span>Share</span>
              </button>
            </div>
          </div>
        </div>

        {/* Dashboard Canvas */}
        <div className="relative h-full p-4 overflow-auto">
          {dashboardLayout.widgets.map(widget => (
            <DraggableWidget key={widget.id} widget={widget} />
          ))}
        </div>

        {/* Loading Overlay */}
        {isLoading && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center">
            <div className="flex items-center space-x-2">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
              <span className="text-lg text-gray-700">Loading real-time data...</span>
            </div>
          </div>
        )}
      </div>
    </DndProvider>
  )
}