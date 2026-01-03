'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BellIcon,
  XMarkIcon,
  CheckIcon,
  ClockIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline'
import { usePushNotifications, NotificationTemplates } from '../../hooks/usePushNotifications'
import { useOfflineStorage } from '../../hooks/useOfflineStorage'

interface Notification {
  id: string
  title: string
  message: string
  type: 'info' | 'warning' | 'error' | 'success' | 'deadline' | 'collaboration'
  timestamp: number
  read: boolean
  actionUrl?: string
  data?: any
}

interface NotificationCenterProps {
  isOpen: boolean
  onClose: () => void
  onSettingsClick?: () => void
}

const notificationIcons = {
  info: InformationCircleIcon,
  warning: ExclamationTriangleIcon,
  error: ExclamationTriangleIcon,
  success: CheckIcon,
  deadline: ClockIcon,
  collaboration: DocumentTextIcon
}

const notificationColors = {
  info: 'text-blue-600 bg-blue-100',
  warning: 'text-yellow-600 bg-yellow-100',
  error: 'text-red-600 bg-red-100',
  success: 'text-green-600 bg-green-100',
  deadline: 'text-orange-600 bg-orange-100',
  collaboration: 'text-purple-600 bg-purple-100'
}

export default function NotificationCenter({
  isOpen,
  onClose,
  onSettingsClick
}: NotificationCenterProps) {
  const [filter, setFilter] = useState<'all' | 'unread'>('all')
  const [notifications, setNotifications] = useState<Notification[]>([])
  
  const { 
    isSupported, 
    permission, 
    isSubscribed, 
    subscribe, 
    unsubscribe,
    showNotification 
  } = usePushNotifications()

  // Offline storage for notifications
  const {
    data: storedNotifications,
    setItem: storeNotification,
    removeItem: removeStoredNotification,
    getAll: getAllNotifications
  } = useOfflineStorage<Notification>({
    storeName: 'notifications',
    maxItems: 200,
    ttl: 30 * 24 * 60 * 60 * 1000 // 30 days
  })

  // Initialize notifications
  useEffect(() => {
    const loadNotifications = async () => {
      const stored = await getAllNotifications()
      const mockNotifications: Notification[] = [
        {
          id: '1',
          title: 'Document Analysis Complete',
          message: 'Your contract analysis for "Service Agreement.pdf" is ready',
          type: 'success',
          timestamp: Date.now() - 300000, // 5 minutes ago
          read: false,
          actionUrl: '/documents/123'
        },
        {
          id: '2',
          title: 'Deadline Reminder',
          message: 'Motion to dismiss deadline is in 2 days',
          type: 'deadline',
          timestamp: Date.now() - 3600000, // 1 hour ago
          read: false,
          actionUrl: '/cases/456/deadlines'
        },
        {
          id: '3',
          title: 'New Collaboration Comment',
          message: 'Sarah Johnson commented on "Merger Agreement Draft"',
          type: 'collaboration',
          timestamp: Date.now() - 7200000, // 2 hours ago
          read: true,
          actionUrl: '/documents/789#comment-123'
        }
      ]
      
      const allNotifications = [...stored, ...mockNotifications]
        .sort((a, b) => b.timestamp - a.timestamp)
      
      setNotifications(allNotifications)
    }

    if (isOpen) {
      loadNotifications()
    }
  }, [isOpen, getAllNotifications])

  // Filter notifications
  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'unread') {
      return !notification.read
    }
    return true
  })

  const unreadCount = notifications.filter(n => !n.read).length

  // Mark notification as read
  const markAsRead = async (notificationId: string) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === notificationId 
          ? { ...notification, read: true }
          : notification
      )
    )

    // Update in storage
    const notification = notifications.find(n => n.id === notificationId)
    if (notification) {
      await storeNotification(notificationId, { ...notification, read: true })
    }
  }

  // Mark all as read
  const markAllAsRead = async () => {
    const unreadNotifications = notifications.filter(n => !n.read)
    
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    )

    // Update in storage
    for (const notification of unreadNotifications) {
      await storeNotification(notification.id, { ...notification, read: true })
    }
  }

  // Delete notification
  const deleteNotification = async (notificationId: string) => {
    setNotifications(prev => prev.filter(n => n.id !== notificationId))
    await removeStoredNotification(notificationId)
  }

  // Handle notification action
  const handleNotificationClick = (notification: Notification) => {
    markAsRead(notification.id)
    
    if (notification.actionUrl) {
      window.location.href = notification.actionUrl
    }
  }

  // Enable notifications
  const enableNotifications = async () => {
    try {
      await subscribe()
      
      // Show welcome notification
      setTimeout(() => {
        showNotification({
          title: 'Notifications Enabled',
          body: 'You\'ll now receive important updates about your legal work',
          tag: 'welcome'
        })
      }, 1000)
    } catch (error) {
      console.error('Failed to enable notifications:', error)
    }
  }

  // Disable notifications
  const disableNotifications = async () => {
    try {
      await unsubscribe()
    } catch (error) {
      console.error('Failed to disable notifications:', error)
    }
  }

  // Test notification
  const testNotification = async () => {
    try {
      await showNotification(
        NotificationTemplates.documentReady('Test Document.pdf')
      )
    } catch (error) {
      console.error('Test notification failed:', error)
    }
  }

  const formatTime = (timestamp: number) => {
    const now = Date.now()
    const diff = now - timestamp
    
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`
    
    return new Date(timestamp).toLocaleDateString()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black bg-opacity-50 z-50 lg:hidden"
          />

          {/* Notification Panel */}
          <motion.div
            initial={{ opacity: 0, x: '100%' }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed top-0 right-0 bottom-0 w-full max-w-md bg-white shadow-2xl z-50 lg:max-w-sm"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <BellIcon className="w-6 h-6 mr-2" />
                  Notifications
                  {unreadCount > 0 && (
                    <span className="ml-2 w-6 h-6 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </h2>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={onSettingsClick}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="Notification settings"
                >
                  <Cog6ToothIcon className="w-5 h-5" />
                </button>
                
                <button
                  onClick={onClose}
                  className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                  aria-label="Close notifications"
                >
                  <XMarkIcon className="w-6 h-6" />
                </button>
              </div>
            </div>

            {/* Push Notification Status */}
            {isSupported && (
              <div className="p-4 bg-gray-50 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm">
                    <span className="text-gray-700">Push notifications: </span>
                    <span className={`font-medium ${isSubscribed ? 'text-green-600' : 'text-red-600'}`}>
                      {isSubscribed ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                  
                  {permission === 'granted' ? (
                    <button
                      onClick={isSubscribed ? disableNotifications : enableNotifications}
                      className={`px-3 py-1 text-xs rounded-full transition-colors ${
                        isSubscribed 
                          ? 'bg-red-100 text-red-700 hover:bg-red-200'
                          : 'bg-green-100 text-green-700 hover:bg-green-200'
                      }`}
                    >
                      {isSubscribed ? 'Disable' : 'Enable'}
                    </button>
                  ) : permission === 'denied' ? (
                    <span className="text-xs text-red-600">Permission denied</span>
                  ) : (
                    <button
                      onClick={enableNotifications}
                      className="px-3 py-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-full transition-colors"
                    >
                      Enable
                    </button>
                  )}
                </div>
                
                {isSubscribed && (
                  <button
                    onClick={testNotification}
                    className="mt-2 text-xs text-gray-600 hover:text-gray-800 underline"
                  >
                    Send test notification
                  </button>
                )}
              </div>
            )}

            {/* Filter and Actions */}
            <div className="flex items-center justify-between p-4 border-b border-gray-200">
              <div className="flex space-x-2">
                <button
                  onClick={() => setFilter('all')}
                  className={`px-3 py-1 text-sm rounded-full transition-colors ${
                    filter === 'all'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  All ({notifications.length})
                </button>
                
                <button
                  onClick={() => setFilter('unread')}
                  className={`px-3 py-1 text-sm rounded-full transition-colors ${
                    filter === 'unread'
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`}
                >
                  Unread ({unreadCount})
                </button>
              </div>
              
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  Mark all read
                </button>
              )}
            </div>

            {/* Notifications List */}
            <div className="flex-1 overflow-y-auto">
              {filteredNotifications.length === 0 ? (
                <div className="text-center py-12">
                  <BellIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {filter === 'unread' ? 'No unread notifications' : 'No notifications'}
                  </h3>
                  <p className="text-gray-600">
                    {filter === 'unread' 
                      ? 'All caught up! Check back later for updates.'
                      : 'We\'ll notify you when something important happens.'
                    }
                  </p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  <AnimatePresence>
                    {filteredNotifications.map((notification) => {
                      const Icon = notificationIcons[notification.type]
                      const colorClasses = notificationColors[notification.type]
                      
                      return (
                        <motion.div
                          key={notification.id}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, x: -100 }}
                          className={`
                            relative p-4 hover:bg-gray-50 cursor-pointer transition-colors
                            ${!notification.read ? 'bg-blue-50 border-l-4 border-blue-500' : ''}
                          `}
                          onClick={() => handleNotificationClick(notification)}
                        >
                          <div className="flex items-start space-x-3">
                            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${colorClasses}`}>
                              <Icon className="w-4 h-4" />
                            </div>
                            
                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between">
                                <h4 className={`text-sm font-medium text-gray-900 ${!notification.read ? 'font-semibold' : ''}`}>
                                  {notification.title}
                                </h4>
                                
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    deleteNotification(notification.id)
                                  }}
                                  className="ml-2 p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                                  aria-label="Delete notification"
                                >
                                  <XMarkIcon className="w-4 h-4" />
                                </button>
                              </div>
                              
                              <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                                {notification.message}
                              </p>
                              
                              <p className="text-xs text-gray-500 mt-2">
                                {formatTime(notification.timestamp)}
                              </p>
                            </div>
                          </div>
                          
                          {!notification.read && (
                            <div className="absolute top-4 right-12 w-2 h-2 bg-blue-500 rounded-full" />
                          )}
                        </motion.div>
                      )
                    })}
                  </AnimatePresence>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}