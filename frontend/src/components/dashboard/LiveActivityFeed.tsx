'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardHeader, CardBody } from '../ui'
import { useWebSocketConnection } from '../../hooks/useWebSocket'
import { 
  MagnifyingGlassIcon,
  DocumentTextIcon,
  BanknotesIcon,
  UserIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline'

export interface ActivityItem {
  id: string
  type: 'search' | 'document' | 'cost' | 'user' | 'system'
  title: string
  description: string
  user?: {
    id: string
    name: string
    avatar?: string
  }
  metadata?: Record<string, any>
  timestamp: Date
  status?: 'pending' | 'completed' | 'error'
}

interface LiveActivityFeedProps {
  maxItems?: number
  autoScroll?: boolean
  showUserAvatars?: boolean
  refreshInterval?: number
  userId?: string
}

export default function LiveActivityFeed({
  maxItems = 50,
  autoScroll = true,
  showUserAvatars = true,
  refreshInterval = 5000,
  userId
}: LiveActivityFeedProps) {
  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [isVisible, setIsVisible] = useState(true)
  const [newItemsCount, setNewItemsCount] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)
  const { isConnected } = useWebSocketConnection()

  // Generate mock activities for demonstration
  const generateMockActivity = (): ActivityItem => {
    const types: ActivityItem['type'][] = ['search', 'document', 'cost', 'user']
    const type = types[Math.floor(Math.random() * types.length)]
    const users = [
      { id: '1', name: 'John Doe' },
      { id: '2', name: 'Jane Smith' },
      { id: '3', name: 'Mike Johnson' },
      { id: '4', name: 'Sarah Wilson' }
    ]
    const user = users[Math.floor(Math.random() * users.length)]

    const activities = {
      search: [
        'Searched for "contract breach liability"',
        'Found 12 relevant cases',
        'Accessed Supreme Court decision',
        'Downloaded case documents'
      ],
      document: [
        'Uploaded new contract for analysis',
        'Document processing completed',
        'AI analysis generated insights',
        'Shared document with team'
      ],
      cost: [
        'Incurred $25.50 research cost',
        'Budget threshold reached (80%)',
        'Monthly spending updated',
        'Cost optimization suggestion available'
      ],
      user: [
        'Logged into the system',
        'Updated profile settings',
        'Created new saved search',
        'Joined collaborative session'
      ]
    }

    const typeActivities = activities[type]
    const description = typeActivities[Math.floor(Math.random() * typeActivities.length)]

    return {
      id: `activity-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type,
      title: `${user.name}`,
      description,
      user,
      timestamp: new Date(),
      status: Math.random() > 0.8 ? 'pending' : 'completed'
    }
  }

  // Add new activity
  const addActivity = (activity: ActivityItem) => {
    setActivities(prev => {
      const newActivities = [activity, ...prev].slice(0, maxItems)
      return newActivities
    })

    // Update new items count if user is not viewing
    if (!isVisible) {
      setNewItemsCount(prev => prev + 1)
    }
  }

  // Simulate real-time activities
  useEffect(() => {
    const interval = setInterval(() => {
      if (isConnected) {
        addActivity(generateMockActivity())
      }
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [isConnected, refreshInterval])

  // Handle visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        setIsVisible(true)
        setNewItemsCount(0)
      } else {
        setIsVisible(false)
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [])

  // Auto-scroll to top when new items are added
  useEffect(() => {
    if (autoScroll && isVisible && containerRef.current) {
      containerRef.current.scrollTop = 0
    }
  }, [activities.length, autoScroll, isVisible])

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'search':
        return MagnifyingGlassIcon
      case 'document':
        return DocumentTextIcon
      case 'cost':
        return BanknotesIcon
      case 'user':
        return UserIcon
      default:
        return ClockIcon
    }
  }

  const getActivityColor = (type: ActivityItem['type']) => {
    switch (type) {
      case 'search':
        return 'text-blue-500'
      case 'document':
        return 'text-green-500'
      case 'cost':
        return 'text-yellow-500'
      case 'user':
        return 'text-purple-500'
      default:
        return 'text-gray-500'
    }
  }

  const getStatusIcon = (status?: ActivityItem['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-3 h-3 text-green-500" />
      case 'error':
        return <ExclamationCircleIcon className="w-3 h-3 text-red-500" />
      case 'pending':
        return (
          <div className="w-3 h-3 border border-gray-300 border-t-blue-500 rounded-full animate-spin" />
        )
      default:
        return null
    }
  }

  const formatTimeAgo = (date: Date) => {
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diffInSeconds < 60) {
      return `${diffInSeconds}s ago`
    } else if (diffInSeconds < 3600) {
      return `${Math.floor(diffInSeconds / 60)}m ago`
    } else if (diffInSeconds < 86400) {
      return `${Math.floor(diffInSeconds / 3600)}h ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Live Activity</h3>
          <div className="flex items-center space-x-3">
            <div className={`flex items-center space-x-1 text-xs ${
              isConnected ? 'text-green-600' : 'text-red-600'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-red-500'
              } ${isConnected ? 'animate-pulse' : ''}`} />
              <span>{isConnected ? 'Live' : 'Offline'}</span>
            </div>
            {newItemsCount > 0 && (
              <div className="bg-primary-500 text-white text-xs px-2 py-1 rounded-full">
                {newItemsCount} new
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardBody padding="none" className="flex-1 overflow-hidden">
        <div 
          ref={containerRef}
          className="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100"
        >
          <AnimatePresence initial={false}>
            {activities.map((activity, index) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, y: -20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 20, scale: 0.95 }}
                transition={{ 
                  type: 'spring',
                  stiffness: 500,
                  damping: 30,
                  delay: index * 0.05
                }}
                className={`border-b border-gray-100 p-4 hover:bg-gray-50 transition-colors ${
                  index === 0 ? 'bg-blue-50 border-blue-200' : ''
                }`}
              >
                <ActivityItemComponent
                  activity={activity}
                  showUserAvatar={showUserAvatars}
                  icon={getActivityIcon(activity.type)}
                  iconColor={getActivityColor(activity.type)}
                  statusIcon={getStatusIcon(activity.status)}
                  timeAgo={formatTimeAgo(activity.timestamp)}
                />
              </motion.div>
            ))}
          </AnimatePresence>
          
          {activities.length === 0 && (
            <div className="flex items-center justify-center h-32 text-gray-500">
              <div className="text-center">
                <ClockIcon className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                <p className="text-sm">No recent activity</p>
              </div>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  )
}

interface ActivityItemComponentProps {
  activity: ActivityItem
  showUserAvatar: boolean
  icon: React.ComponentType<{ className?: string }>
  iconColor: string
  statusIcon?: React.ReactNode
  timeAgo: string
}

function ActivityItemComponent({
  activity,
  showUserAvatar,
  icon: Icon,
  iconColor,
  statusIcon,
  timeAgo
}: ActivityItemComponentProps) {
  return (
    <div className="flex items-start space-x-3">
      {/* Activity icon */}
      <div className={`flex-shrink-0 p-1 rounded-full bg-gray-100`}>
        <Icon className={`w-4 h-4 ${iconColor}`} />
      </div>
      
      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              {showUserAvatar && activity.user && (
                <div className="flex-shrink-0">
                  {activity.user.avatar ? (
                    <img
                      src={activity.user.avatar}
                      alt={activity.user.name}
                      className="w-5 h-5 rounded-full"
                    />
                  ) : (
                    <div className="w-5 h-5 rounded-full bg-gray-300 flex items-center justify-center">
                      <span className="text-xs font-medium text-gray-600">
                        {activity.user.name.charAt(0)}
                      </span>
                    </div>
                  )}
                </div>
              )}
              <p className="text-sm font-medium text-gray-900 truncate">
                {activity.title}
              </p>
              {statusIcon && (
                <div className="flex-shrink-0">
                  {statusIcon}
                </div>
              )}
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {activity.description}
            </p>
          </div>
          
          <div className="flex-shrink-0 ml-2">
            <span className="text-xs text-gray-400">
              {timeAgo}
            </span>
          </div>
        </div>
        
        {/* Metadata */}
        {activity.metadata && Object.keys(activity.metadata).length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {Object.entries(activity.metadata).slice(0, 2).map(([key, value]) => (
              <span
                key={key}
                className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded"
              >
                {key}: {String(value)}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}