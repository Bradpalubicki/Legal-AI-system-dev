'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardBody } from '../ui'
import { useWebSocketConnection, useLiveData } from '../../hooks/useWebSocket'
import { costService } from '../../services'
import { 
  BanknotesIcon, 
  ClockIcon, 
  ChartBarIcon,
  SignalIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'

interface LiveMetricsProps {
  userId?: string
  refreshInterval?: number
}

interface LiveMetricCard {
  title: string
  value: string | number
  change?: number
  changeType?: 'positive' | 'negative' | 'neutral'
  icon: React.ComponentType<{ className?: string }>
  isLoading: boolean
  lastUpdated?: Date
}

export default function LiveMetrics({ userId, refreshInterval = 15000 }: LiveMetricsProps) {
  const { isConnected } = useWebSocketConnection()
  
  const { 
    data: dashboardData, 
    isLoading, 
    lastUpdated,
    refresh 
  } = useLiveData(
    ['dashboard', 'live', '1h'],
    () => costService.getDashboardData('1h'),
    refreshInterval
  )

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatTime = (date: Date | null) => {
    if (!date) return 'Never'
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const metrics: LiveMetricCard[] = [
    {
      title: 'Hourly Spend',
      value: dashboardData ? formatCurrency(dashboardData.monthlySpend / 24) : '$0',
      change: 12.5,
      changeType: 'positive',
      icon: BanknotesIcon,
      isLoading,
      lastUpdated
    },
    {
      title: 'Active Sessions',
      value: '3',
      change: 1,
      changeType: 'positive',
      icon: ChartBarIcon,
      isLoading: false,
      lastUpdated
    },
    {
      title: 'Avg Response Time',
      value: '1.2s',
      change: -0.3,
      changeType: 'negative',
      icon: ClockIcon,
      isLoading: false,
      lastUpdated
    },
    {
      title: 'Budget Alerts',
      value: '2',
      changeType: 'neutral',
      icon: ExclamationTriangleIcon,
      isLoading: false,
      lastUpdated
    }
  ]

  return (
    <div className="space-y-4">
      {/* Connection Status */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Live Metrics</h2>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm text-gray-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            Last updated: {formatTime(lastUpdated)}
          </div>
          <button
            onClick={refresh}
            className="p-1 rounded-md hover:bg-gray-100 transition-colors"
            title="Refresh data"
          >
            <SignalIcon className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <LiveMetricCard key={index} {...metric} />
        ))}
      </div>
    </div>
  )
}

function LiveMetricCard({ 
  title, 
  value, 
  change, 
  changeType, 
  icon: Icon, 
  isLoading, 
  lastUpdated 
}: LiveMetricCard) {
  const [isAnimating, setIsAnimating] = useState(false)
  const [previousValue, setPreviousValue] = useState(value)

  useEffect(() => {
    if (value !== previousValue) {
      setIsAnimating(true)
      setPreviousValue(value)
      const timer = setTimeout(() => setIsAnimating(false), 500)
      return () => clearTimeout(timer)
    }
  }, [value, previousValue])

  const getChangeColor = () => {
    switch (changeType) {
      case 'positive': return 'text-green-600'
      case 'negative': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  return (
    <Card className={`transition-all duration-300 ${
      isAnimating ? 'ring-2 ring-primary-500 ring-opacity-50' : ''
    }`}>
      <CardBody padding="md">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className="h-6 w-6 text-gray-400" />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className={`text-lg font-medium text-gray-900 transition-all duration-300 ${
                  isLoading ? 'animate-pulse' : ''
                } ${isAnimating ? 'scale-105' : ''}`}>
                  {isLoading ? '...' : value}
                </div>
                {change !== undefined && (
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${getChangeColor()}`}>
                    {change > 0 ? '+' : ''}{change}%
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
        
        {/* Activity indicator */}
        <div className="mt-2 flex justify-end">
          <div className={`w-1 h-1 rounded-full transition-colors duration-300 ${
            isAnimating ? 'bg-primary-500' : 'bg-gray-300'
          }`} />
        </div>
      </CardBody>
    </Card>
  )
}