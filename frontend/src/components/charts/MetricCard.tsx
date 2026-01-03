'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardBody } from '../ui'
import { RealtimeMetric, ExportConfig } from '../../types/analytics'
import {
  ArrowTrendingUpIcon as TrendingUpIcon,
  ArrowTrendingDownIcon as TrendingDownIcon,
  MinusIcon,
  InformationCircleIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline'

interface MetricCardProps {
  metric: RealtimeMetric
  showTrend?: boolean
  showTimestamp?: boolean
  size?: 'sm' | 'md' | 'lg'
  className?: string
  onExport?: (config: ExportConfig) => void
  onClick?: () => void
}

export default function MetricCard({
  metric,
  showTrend = true,
  showTimestamp = false,
  size = 'md',
  className = '',
  onExport,
  onClick
}: MetricCardProps) {
  const [showExportMenu, setShowExportMenu] = useState(false)

  const formatValue = (value: number, format?: string, unit?: string) => {
    let formattedValue: string

    switch (format) {
      case 'currency':
        formattedValue = new Intl.NumberFormat('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 0,
          maximumFractionDigits: 2
        }).format(value)
        break
      
      case 'percentage':
        formattedValue = `${(value * 100).toFixed(1)}%`
        break
      
      case 'time':
        if (value < 60) {
          formattedValue = `${value.toFixed(1)}s`
        } else if (value < 3600) {
          formattedValue = `${(value / 60).toFixed(1)}m`
        } else {
          formattedValue = `${(value / 3600).toFixed(1)}h`
        }
        break
      
      default:
        if (value >= 1000000) {
          formattedValue = `${(value / 1000000).toFixed(1)}M`
        } else if (value >= 1000) {
          formattedValue = `${(value / 1000).toFixed(1)}K`
        } else {
          formattedValue = value.toLocaleString()
        }
    }

    return unit ? `${formattedValue} ${unit}` : formattedValue
  }

  const getTrendIcon = (changeType: string) => {
    switch (changeType) {
      case 'increase':
        return TrendingUpIcon
      case 'decrease':
        return TrendingDownIcon
      default:
        return MinusIcon
    }
  }

  const getTrendColor = (changeType: string) => {
    switch (changeType) {
      case 'increase':
        return 'text-green-600'
      case 'decrease':
        return 'text-red-600'
      default:
        return 'text-gray-500'
    }
  }

  const getSizeClasses = () => {
    switch (size) {
      case 'sm':
        return {
          card: 'p-4',
          title: 'text-xs',
          value: 'text-lg',
          trend: 'text-xs',
          icon: 'w-3 h-3'
        }
      case 'lg':
        return {
          card: 'p-8',
          title: 'text-lg',
          value: 'text-4xl',
          trend: 'text-base',
          icon: 'w-5 h-5'
        }
      default: // md
        return {
          card: 'p-6',
          title: 'text-sm',
          value: 'text-2xl',
          trend: 'text-sm',
          icon: 'w-4 h-4'
        }
    }
  }

  const sizeClasses = getSizeClasses()
  const TrendIcon = getTrendIcon(metric.changeType)

  return (
    <Card 
      className={`${className} ${onClick ? 'cursor-pointer hover:shadow-lg transition-shadow' : ''} relative group`}
      onClick={onClick}
    >
      <CardBody className="p-0">
        <div className={sizeClasses.card}>
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <h3 className={`font-medium text-gray-600 ${sizeClasses.title}`}>
              {metric.name}
            </h3>
            
            {onExport && (
              <div className="relative opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowExportMenu(!showExportMenu)
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded"
                  title="Export metric"
                >
                  <ArrowDownTrayIcon className="w-4 h-4" />
                </button>
                
                {showExportMenu && (
                  <div className="absolute right-0 mt-2 w-36 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50">
                    <div className="py-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onExport({ format: 'png' as any, filename: `${metric.name}_metric` })
                          setShowExportMenu(false)
                        }}
                        className="block w-full text-left px-3 py-2 text-xs text-gray-700 hover:bg-gray-100"
                      >
                        Export as PNG
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          onExport({ format: 'csv' as any, filename: `${metric.name}_data` })
                          setShowExportMenu(false)
                        }}
                        className="block w-full text-left px-3 py-2 text-xs text-gray-700 hover:bg-gray-100"
                      >
                        Export Data
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Value */}
          <motion.div
            key={metric.value}
            initial={{ scale: 1 }}
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 0.3 }}
            className={`font-bold text-gray-900 mb-2 ${sizeClasses.value}`}
          >
            {formatValue(metric.value, metric.format, metric.unit)}
          </motion.div>

          {/* Trend */}
          {showTrend && metric.change !== 0 && (
            <div className={`flex items-center space-x-1 ${getTrendColor(metric.changeType)} ${sizeClasses.trend}`}>
              <TrendIcon className={sizeClasses.icon} />
              <span className="font-medium">
                {metric.change > 0 ? '+' : ''}{formatValue(Math.abs(metric.change), metric.format, metric.unit)}
              </span>
              <span className="text-gray-500">
                vs previous
              </span>
            </div>
          )}

          {/* Timestamp */}
          {showTimestamp && (
            <div className="mt-3 text-xs text-gray-500">
              Updated: {new Date(metric.timestamp).toLocaleTimeString()}
            </div>
          )}
        </div>
      </CardBody>

      {/* Export menu overlay */}
      {showExportMenu && (
        <div 
          className="fixed inset-0 z-40"
          onClick={(e) => {
            e.stopPropagation()
            setShowExportMenu(false)
          }}
        />
      )}
    </Card>
  )
}

// Specialized metric cards
export function CostMetricCard({ value, change, changeType, ...props }: Omit<MetricCardProps, 'metric'> & {
  value: number
  change: number
  changeType: 'increase' | 'decrease' | 'neutral'
}) {
  const metric: RealtimeMetric = {
    id: 'cost',
    name: 'Total Cost',
    value,
    change,
    changeType,
    timestamp: new Date().toISOString(),
    format: 'currency'
  }

  return <MetricCard metric={metric} {...props} />
}

export function SearchMetricCard({ value, change, changeType, ...props }: Omit<MetricCardProps, 'metric'> & {
  value: number
  change: number
  changeType: 'increase' | 'decrease' | 'neutral'
}) {
  const metric: RealtimeMetric = {
    id: 'searches',
    name: 'Total Searches',
    value,
    change,
    changeType,
    timestamp: new Date().toISOString(),
    format: 'number'
  }

  return <MetricCard metric={metric} {...props} />
}

export function ResponseTimeMetricCard({ value, change, changeType, ...props }: Omit<MetricCardProps, 'metric'> & {
  value: number
  change: number
  changeType: 'increase' | 'decrease' | 'neutral'
}) {
  const metric: RealtimeMetric = {
    id: 'response_time',
    name: 'Avg Response Time',
    value,
    change,
    changeType,
    timestamp: new Date().toISOString(),
    format: 'time'
  }

  return <MetricCard metric={metric} {...props} />
}

export function SuccessRateMetricCard({ value, change, changeType, ...props }: Omit<MetricCardProps, 'metric'> & {
  value: number
  change: number
  changeType: 'increase' | 'decrease' | 'neutral'
}) {
  const metric: RealtimeMetric = {
    id: 'success_rate',
    name: 'Success Rate',
    value,
    change,
    changeType,
    timestamp: new Date().toISOString(),
    format: 'percentage'
  }

  return <MetricCard metric={metric} {...props} />
}