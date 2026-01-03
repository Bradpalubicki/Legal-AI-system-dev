'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardHeader, CardBody } from '../ui'
import LineChart from '../charts/LineChart'
import BarChart from '../charts/BarChart'
import PieChart from '../charts/PieChart'
import HeatMap from '../charts/HeatMap'
import TreeMap from '../charts/TreeMap'
import MetricCard from '../charts/MetricCard'
import { 
  DashboardWidget, 
  WidgetType, 
  DrilldownPath, 
  BreadcrumbItem,
  CategoryData,
  TimeSeriesData,
  HeatMapData,
  TreeMapData,
  RealtimeMetric,
  ExportConfig
} from '../../types/analytics'
import {
  ChevronRightIcon,
  ArrowLeftIcon,
  Squares2X2Icon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline'

interface InteractiveDashboardProps {
  widgets: DashboardWidget[]
  onWidgetInteraction?: (widgetId: string, interaction: any) => void
  onExport?: (config: ExportConfig) => void
  className?: string
}

interface DrilldownState {
  widgetId: string
  path: DrilldownPath
  data: any[]
}

export default function InteractiveDashboard({
  widgets,
  onWidgetInteraction,
  onExport,
  className = ''
}: InteractiveDashboardProps) {
  const [drilldownState, setDrilldownState] = useState<DrilldownState | null>(null)
  const [selectedWidgets, setSelectedWidgets] = useState<string[]>([])
  const [filterMode, setFilterMode] = useState(false)

  const handleDrilldown = useCallback((widgetId: string, data: any) => {
    // Simulate drill-down navigation
    const newPath: DrilldownPath = {
      levels: [
        {
          field: data.category || data.id,
          label: data.category || data.id,
          data: generateDrilldownData(data)
        }
      ],
      breadcrumbs: [
        {
          label: 'Overview',
          value: 'root',
          level: 0
        },
        {
          label: data.category || data.id,
          value: data.category || data.id,
          level: 1
        }
      ]
    }

    setDrilldownState({
      widgetId,
      path: newPath,
      data: generateDrilldownData(data)
    })

    onWidgetInteraction?.(widgetId, { type: 'drilldown', data })
  }, [onWidgetInteraction])

  const handleBreadcrumbClick = useCallback((level: number) => {
    if (level === 0) {
      setDrilldownState(null)
    } else if (drilldownState) {
      // Navigate back to specific level
      const newPath = {
        ...drilldownState.path,
        levels: drilldownState.path.levels.slice(0, level),
        breadcrumbs: drilldownState.path.breadcrumbs.slice(0, level + 1)
      }
      setDrilldownState({
        ...drilldownState,
        path: newPath
      })
    }
  }, [drilldownState])

  const renderWidget = (widget: DashboardWidget, data: any = null) => {
    const widgetData = data || generateMockData(widget.type)
    const isSelected = selectedWidgets.includes(widget.id)

    const commonProps = {
      config: widget.config,
      onExport: (config: ExportConfig) => onExport?.(config),
      className: `transition-all duration-200 ${
        isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : ''
      } ${filterMode ? 'cursor-pointer' : ''}`
    }

    switch (widget.type) {
      case WidgetType.LINE_CHART:
        return (
          <LineChart
            data={widgetData as TimeSeriesData[]}
            {...commonProps}
          />
        )

      case WidgetType.BAR_CHART:
        return (
          <BarChart
            data={widgetData as CategoryData[]}
            onExport={commonProps.onExport}
            config={{
              ...commonProps.config,
              title: widget.title
            }}
            className={commonProps.className}
          />
        )

      case WidgetType.PIE_CHART:
        return (
          <PieChart
            data={widgetData as CategoryData[]}
            {...commonProps}
            config={{
              ...commonProps.config,
              title: widget.title
            }}
          />
        )

      case WidgetType.HEATMAP:
        return (
          <HeatMap
            data={widgetData as HeatMapData[]}
            onCellClick={(cell) => handleDrilldown(widget.id, cell)}
            {...commonProps}
            config={{
              ...commonProps.config,
              title: widget.title
            }}
          />
        )

      case WidgetType.TREEMAP:
        return (
          <TreeMap
            data={widgetData as TreeMapData}
            onNodeClick={(node) => handleDrilldown(widget.id, node)}
            {...commonProps}
            config={{
              ...commonProps.config,
              title: widget.title
            }}
          />
        )

      case WidgetType.METRIC_CARD:
        return (
          <MetricCard
            metric={widgetData as RealtimeMetric}
            onExport={commonProps.onExport}
            onClick={() => handleDrilldown(widget.id, widgetData)}
            className={commonProps.className}
          />
        )

      default:
        return (
          <Card className={commonProps.className}>
            <CardBody>
              <div className="text-center text-gray-500 p-8">
                Widget type '{widget.type}' not implemented
              </div>
            </CardBody>
          </Card>
        )
    }
  }

  const generateMockData = (type: WidgetType): any => {
    switch (type) {
      case WidgetType.LINE_CHART:
        return Array.from({ length: 12 }, (_, i) => ({
          date: `2024-${String(i + 1).padStart(2, '0')}-01`,
          value: Math.floor(Math.random() * 1000) + 500
        }))

      case WidgetType.BAR_CHART:
      case WidgetType.PIE_CHART:
        return [
          { category: 'Litigation', value: 450 },
          { category: 'Corporate', value: 320 },
          { category: 'Real Estate', value: 280 },
          { category: 'Employment', value: 190 },
          { category: 'IP', value: 150 }
        ]

      case WidgetType.HEATMAP:
        return [
          { id: 'Monday', data: { '9AM': 20, '10AM': 35, '11AM': 45, '12PM': 30, '1PM': 25 } },
          { id: 'Tuesday', data: { '9AM': 25, '10AM': 40, '11AM': 50, '12PM': 35, '1PM': 30 } },
          { id: 'Wednesday', data: { '9AM': 30, '10AM': 45, '11AM': 55, '12PM': 40, '1PM': 35 } },
          { id: 'Thursday', data: { '9AM': 35, '10AM': 50, '11AM': 60, '12PM': 45, '1PM': 40 } },
          { id: 'Friday', data: { '9AM': 28, '10AM': 42, '11AM': 52, '12PM': 38, '1PM': 32 } }
        ]

      case WidgetType.TREEMAP:
        return {
          name: 'Legal Services',
          children: [
            {
              name: 'Litigation',
              value: 450,
              children: [
                { name: 'Civil Litigation', value: 250 },
                { name: 'Criminal Defense', value: 200 }
              ]
            },
            {
              name: 'Corporate',
              value: 320,
              children: [
                { name: 'M&A', value: 180 },
                { name: 'Compliance', value: 140 }
              ]
            }
          ]
        }

      case WidgetType.METRIC_CARD:
        return {
          id: 'total_cases',
          name: 'Total Cases',
          value: 1250,
          change: 85,
          changeType: 'increase',
          timestamp: new Date().toISOString(),
          format: 'number'
        } as RealtimeMetric

      default:
        return []
    }
  }

  const generateDrilldownData = (parentData: any): CategoryData[] => {
    // Generate mock drill-down data based on parent selection
    return [
      { category: `${parentData.category || parentData.id} - Detail A`, value: Math.floor(Math.random() * 100) + 50 },
      { category: `${parentData.category || parentData.id} - Detail B`, value: Math.floor(Math.random() * 100) + 30 },
      { category: `${parentData.category || parentData.id} - Detail C`, value: Math.floor(Math.random() * 100) + 20 }
    ]
  }

  const toggleWidgetSelection = (widgetId: string) => {
    if (selectedWidgets.includes(widgetId)) {
      setSelectedWidgets(selectedWidgets.filter(id => id !== widgetId))
    } else {
      setSelectedWidgets([...selectedWidgets, widgetId])
    }
  }

  if (drilldownState) {
    return (
      <div className={`space-y-6 ${className}`}>
        {/* Drill-down Header */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setDrilldownState(null)}
                  className="flex items-center text-gray-600 hover:text-gray-800 transition-colors"
                >
                  <ArrowLeftIcon className="w-4 h-4 mr-2" />
                  Back to Dashboard
                </button>
                
                {/* Breadcrumbs */}
                <nav className="flex items-center space-x-2 text-sm">
                  {drilldownState.path.breadcrumbs.map((crumb, index) => (
                    <div key={index} className="flex items-center">
                      {index > 0 && <ChevronRightIcon className="w-4 h-4 mx-2 text-gray-400" />}
                      <button
                        onClick={() => handleBreadcrumbClick(crumb.level)}
                        className={`${
                          index === drilldownState.path.breadcrumbs.length - 1
                            ? 'text-blue-600 font-medium'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        {crumb.label}
                      </button>
                    </div>
                  ))}
                </nav>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Drill-down Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
        >
          <BarChart
            data={drilldownState.data}
            config={{
              title: `Detailed View: ${drilldownState.path.breadcrumbs[drilldownState.path.breadcrumbs.length - 1].label}`,
              animate: true
            }}
            onExport={onExport}
          />
        </motion.div>
      </div>
    )
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Dashboard Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-gray-900">Legal Analytics Dashboard</h2>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setFilterMode(!filterMode)}
                className={`p-2 rounded-lg transition-colors ${
                  filterMode
                    ? 'bg-blue-100 text-blue-600'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
                title="Filter mode"
              >
                <AdjustmentsHorizontalIcon className="w-4 h-4" />
              </button>
              
              <button
                onClick={() => setSelectedWidgets([])}
                className="p-2 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors"
                title="Reset view"
              >
                <Squares2X2Icon className="w-4 h-4" />
              </button>
            </div>
          </div>

          {selectedWidgets.length > 0 && (
            <div className="mt-2 text-sm text-gray-600">
              {selectedWidgets.length} widget{selectedWidgets.length !== 1 ? 's' : ''} selected
            </div>
          )}
        </CardHeader>
      </Card>

      {/* Widget Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        <AnimatePresence>
          {widgets.map((widget) => (
            <motion.div
              key={widget.id}
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.2 }}
              onClick={() => {
                if (filterMode) {
                  toggleWidgetSelection(widget.id)
                }
              }}
              className={`${widget.position ? `col-span-${widget.position.width} row-span-${widget.position.height}` : ''}`}
            >
              {renderWidget(widget)}
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}