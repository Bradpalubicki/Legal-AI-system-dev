'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  XMarkIcon, 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  InformationCircleIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline'
import { useRealtimeUpdates } from '../../hooks/useWebSocket'

export interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: Date
  autoClose?: boolean
  duration?: number
  actions?: NotificationAction[]
}

export interface NotificationAction {
  label: string
  onClick: () => void
  variant?: 'primary' | 'secondary'
}

interface NotificationSystemProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center'
  maxNotifications?: number
  defaultDuration?: number
  userId?: string
}

export default function NotificationSystem({
  position = 'top-right',
  maxNotifications = 5,
  defaultDuration = 5000,
  userId
}: NotificationSystemProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const { notifications: realtimeNotifications } = useRealtimeUpdates(userId)

  // Convert WebSocket messages to notifications
  useEffect(() => {
    realtimeNotifications.forEach(wsMessage => {
      let notification: Notification

      switch (wsMessage.type) {
        case 'budget_alert':
          notification = {
            id: `alert-${Date.now()}`,
            type: 'warning',
            title: 'Budget Alert',
            message: wsMessage.data.message || 'Budget threshold exceeded',
            timestamp: new Date(wsMessage.timestamp),
            autoClose: false,
            actions: [
              {
                label: 'View Budget',
                onClick: () => {/* Navigate to budget page */},
                variant: 'primary'
              },
              {
                label: 'Dismiss',
                onClick: () => removeNotification(`alert-${Date.now()}`),
                variant: 'secondary'
              }
            ]
          }
          break

        case 'search_complete':
          notification = {
            id: `search-${Date.now()}`,
            type: 'success',
            title: 'Search Completed',
            message: `Found ${wsMessage.data.results?.length || 0} results`,
            timestamp: new Date(wsMessage.timestamp),
            autoClose: true,
            duration: 4000
          }
          break

        case 'document_processing':
          if (wsMessage.data.status === 'completed') {
            notification = {
              id: `doc-${wsMessage.data.documentId}`,
              type: 'success',
              title: 'Document Processed',
              message: 'Document analysis is complete',
              timestamp: new Date(wsMessage.timestamp),
              autoClose: true,
              actions: [
                {
                  label: 'View Results',
                  onClick: () => {/* Navigate to document */},
                  variant: 'primary'
                }
              ]
            }
          } else if (wsMessage.data.status === 'error') {
            notification = {
              id: `doc-error-${wsMessage.data.documentId}`,
              type: 'error',
              title: 'Processing Failed',
              message: 'Document processing encountered an error',
              timestamp: new Date(wsMessage.timestamp),
              autoClose: false
            }
          } else {
            return // Don't show notifications for 'processing' status
          }
          break

        default:
          return
      }

      addNotification(notification)
    })
  }, [realtimeNotifications])

  const addNotification = (notification: Notification) => {
    setNotifications(prev => {
      const newNotifications = [notification, ...prev]
      return newNotifications.slice(0, maxNotifications)
    })

    // Auto-close if specified
    if (notification.autoClose !== false) {
      const duration = notification.duration || defaultDuration
      setTimeout(() => {
        removeNotification(notification.id)
      }, duration)
    }
  }

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const clearAll = () => {
    setNotifications([])
  }

  const getPositionClasses = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4'
      case 'top-center':
        return 'top-4 left-1/2 transform -translate-x-1/2'
      case 'bottom-right':
        return 'bottom-4 right-4'
      case 'bottom-left':
        return 'bottom-4 left-4'
      default:
        return 'top-4 right-4'
    }
  }

  if (notifications.length === 0) return null

  return (
    <div className={`fixed z-50 space-y-3 ${getPositionClasses()}`} style={{ maxWidth: '400px' }}>
      {notifications.length > 2 && (
        <div className="flex justify-end mb-2">
          <button
            onClick={clearAll}
            className="text-xs text-gray-500 hover:text-gray-700 underline"
          >
            Clear all ({notifications.length})
          </button>
        </div>
      )}
      
      <AnimatePresence>
        {notifications.map((notification) => (
          <NotificationCard
            key={notification.id}
            notification={notification}
            onRemove={() => removeNotification(notification.id)}
          />
        ))}
      </AnimatePresence>
    </div>
  )
}

interface NotificationCardProps {
  notification: Notification
  onRemove: () => void
}

function NotificationCard({ notification, onRemove }: NotificationCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />
      case 'error':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
      default:
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />
    }
  }

  const getBorderColor = () => {
    switch (notification.type) {
      case 'success':
        return 'border-l-green-500'
      case 'error':
        return 'border-l-red-500'
      case 'warning':
        return 'border-l-yellow-500'
      default:
        return 'border-l-blue-500'
    }
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 300, scale: 0.8 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 300, scale: 0.8 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className={`bg-white rounded-lg shadow-lg border-l-4 ${getBorderColor()} p-4 max-w-md`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getIcon()}
        </div>
        
        <div className="ml-3 flex-1">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">
                {notification.title}
              </p>
              <p className="mt-1 text-sm text-gray-600">
                {notification.message}
              </p>
              <p className="mt-2 text-xs text-gray-400">
                {formatTimestamp(notification.timestamp)}
              </p>
            </div>
            
            <button
              onClick={onRemove}
              className={`ml-4 text-gray-400 hover:text-gray-600 transition-opacity ${
                isHovered ? 'opacity-100' : 'opacity-50'
              }`}
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          </div>
          
          {notification.actions && notification.actions.length > 0 && (
            <div className="mt-3 flex space-x-2">
              {notification.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={action.onClick}
                  className={`text-xs px-3 py-1 rounded-md font-medium transition-colors ${
                    action.variant === 'primary'
                      ? 'bg-primary-600 text-white hover:bg-primary-700'
                      : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
                  }`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}

// Hook for programmatically adding notifications
export function useNotifications() {
  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    // This would typically dispatch to a global notification context
    // For now, we'll use a simple implementation
    const fullNotification: Notification = {
      ...notification,
      id: `notif-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    }
    
    // Dispatch custom event for NotificationSystem to catch
    window.dispatchEvent(new CustomEvent('add-notification', {
      detail: fullNotification
    }))
  }

  const success = (title: string, message: string, options?: Partial<Notification>) => {
    addNotification({ ...options, type: 'success', title, message })
  }

  const error = (title: string, message: string, options?: Partial<Notification>) => {
    addNotification({ ...options, type: 'error', title, message, autoClose: false })
  }

  const warning = (title: string, message: string, options?: Partial<Notification>) => {
    addNotification({ ...options, type: 'warning', title, message })
  }

  const info = (title: string, message: string, options?: Partial<Notification>) => {
    addNotification({ ...options, type: 'info', title, message })
  }

  return {
    addNotification,
    success,
    error,
    warning,
    info
  }
}