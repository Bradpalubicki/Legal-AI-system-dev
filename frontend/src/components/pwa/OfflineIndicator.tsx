'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  WifiIcon,
  CloudArrowUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'
import { useBackgroundSync } from '../../hooks/useBackgroundSync'

interface OfflineIndicatorProps {
  position?: 'top' | 'bottom'
  className?: string
}

export default function OfflineIndicator({ 
  position = 'top',
  className = '' 
}: OfflineIndicatorProps) {
  const [showIndicator, setShowIndicator] = useState(false)
  const [wasOffline, setWasOffline] = useState(false)
  
  const {
    isOnline,
    isSyncing,
    pendingItems,
    syncProgress,
    forcSync,
    getPendingCount,
    getSyncStatus
  } = useBackgroundSync()

  const pendingCount = getPendingCount()
  const syncStatus = getSyncStatus()

  // Show/hide indicator based on online status
  useEffect(() => {
    if (!isOnline) {
      setShowIndicator(true)
      setWasOffline(true)
    } else {
      // If we were offline and now online, show reconnected message briefly
      if (wasOffline) {
        setShowIndicator(true)
        setTimeout(() => {
          setShowIndicator(false)
          setWasOffline(false)
        }, 3000)
      } else {
        setShowIndicator(false)
      }
    }
  }, [isOnline, wasOffline])

  // Auto-show when there are pending syncs
  useEffect(() => {
    if (pendingCount > 0 && !showIndicator) {
      setShowIndicator(true)
      
      // Auto-hide after successful sync
      if (syncStatus === 'success') {
        setTimeout(() => setShowIndicator(false), 2000)
      }
    }
  }, [pendingCount, showIndicator, syncStatus])

  const getIndicatorContent = () => {
    if (!isOnline) {
      return {
        icon: WifiIcon,
        title: 'You\'re offline',
        subtitle: 'Changes will sync when connection returns',
        bgColor: 'bg-orange-500',
        textColor: 'text-white',
        action: null
      }
    }

    if (isSyncing) {
      return {
        icon: ArrowPathIcon,
        title: 'Syncing changes...',
        subtitle: `${Math.round(syncProgress)}% complete`,
        bgColor: 'bg-blue-500',
        textColor: 'text-white',
        action: null
      }
    }

    if (pendingCount > 0) {
      return {
        icon: CloudArrowUpIcon,
        title: `${pendingCount} change${pendingCount === 1 ? '' : 's'} pending`,
        subtitle: 'Tap to sync now',
        bgColor: 'bg-yellow-500',
        textColor: 'text-white',
        action: forcSync
      }
    }

    if (syncStatus === 'failed') {
      return {
        icon: ExclamationTriangleIcon,
        title: 'Sync failed',
        subtitle: 'Some changes couldn\'t be synced',
        bgColor: 'bg-red-500',
        textColor: 'text-white',
        action: forcSync
      }
    }

    if (wasOffline && isOnline) {
      return {
        icon: CheckCircleIcon,
        title: 'Back online',
        subtitle: 'All changes synced successfully',
        bgColor: 'bg-green-500',
        textColor: 'text-white',
        action: null
      }
    }

    return null
  }

  const indicatorContent = getIndicatorContent()

  if (!indicatorContent) return null

  const Icon = indicatorContent.icon

  return (
    <AnimatePresence>
      {showIndicator && (
        <motion.div
          initial={{ opacity: 0, y: position === 'top' ? -100 : 100 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: position === 'top' ? -100 : 100 }}
          className={`
            fixed left-4 right-4 z-50 safe-area-top
            ${position === 'top' ? 'top-4' : 'bottom-4'}
            ${className}
          `}
        >
          <div
            className={`
              max-w-sm mx-auto rounded-xl shadow-lg border
              ${indicatorContent.bgColor} ${indicatorContent.textColor}
              ${indicatorContent.action ? 'cursor-pointer hover:opacity-90' : ''}
              transition-opacity
            `}
            onClick={indicatorContent.action || undefined}
          >
            <div className="flex items-center p-4">
              <div className="flex-shrink-0">
                <Icon 
                  className={`w-6 h-6 ${isSyncing ? 'animate-spin' : ''}`} 
                />
              </div>
              
              <div className="ml-3 flex-1 min-w-0">
                <p className="text-sm font-medium">
                  {indicatorContent.title}
                </p>
                <p className="text-xs opacity-90">
                  {indicatorContent.subtitle}
                </p>
                
                {/* Progress bar for syncing */}
                {isSyncing && (
                  <div className="mt-2 bg-white/20 rounded-full h-1">
                    <motion.div
                      className="bg-white rounded-full h-1"
                      initial={{ width: 0 }}
                      animate={{ width: `${syncProgress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                )}
              </div>
              
              {/* Dismiss button for persistent states */}
              {(pendingCount > 0 || syncStatus === 'failed') && (
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowIndicator(false)
                  }}
                  className="ml-2 p-1 hover:bg-white/20 rounded-full transition-colors"
                  aria-label="Dismiss"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// Compact version for mobile bottom bar
export function CompactOfflineIndicator() {
  const { isOnline, pendingItems } = useBackgroundSync()
  const pendingCount = pendingItems.length

  if (isOnline && pendingCount === 0) return null

  return (
    <div className={`
      flex items-center space-x-1 px-2 py-1 rounded-full text-xs
      ${!isOnline 
        ? 'bg-orange-100 text-orange-800' 
        : 'bg-yellow-100 text-yellow-800'
      }
    `}>
      {!isOnline ? (
        <>
          <WifiIcon className="w-3 h-3" />
          <span>Offline</span>
        </>
      ) : (
        <>
          <CloudArrowUpIcon className="w-3 h-3" />
          <span>{pendingCount}</span>
        </>
      )}
    </div>
  )
}

// Sync status widget for dashboard
export function SyncStatusWidget() {
  const {
    isOnline,
    isSyncing,
    pendingItems,
    syncProgress,
    forcSync,
    getSyncStatus
  } = useBackgroundSync()

  const syncStatus = getSyncStatus()
  const pendingCount = pendingItems.length

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-900">Sync Status</h3>
        
        <div className={`
          inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
          ${isOnline 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
          }
        `}>
          <div className={`w-2 h-2 rounded-full mr-1 ${
            isOnline ? 'bg-green-500' : 'bg-red-500'
          }`} />
          {isOnline ? 'Online' : 'Offline'}
        </div>
      </div>

      <div className="space-y-2">
        {isSyncing && (
          <div>
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-gray-600">Syncing...</span>
              <span className="text-gray-900 font-medium">{Math.round(syncProgress)}%</span>
            </div>
            <div className="bg-gray-200 rounded-full h-2">
              <motion.div
                className="bg-blue-500 rounded-full h-2"
                initial={{ width: 0 }}
                animate={{ width: `${syncProgress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        )}

        {pendingCount > 0 && (
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">
              {pendingCount} pending change{pendingCount === 1 ? '' : 's'}
            </span>
            
            <button
              onClick={forcSync}
              disabled={!isOnline || isSyncing}
              className="text-xs text-blue-600 hover:text-blue-700 disabled:text-gray-400 font-medium"
            >
              Sync now
            </button>
          </div>
        )}

        {syncStatus === 'failed' && (
          <div className="flex items-center space-x-2 text-sm text-red-600">
            <ExclamationTriangleIcon className="w-4 h-4" />
            <span>Some changes failed to sync</span>
          </div>
        )}

        {pendingCount === 0 && !isSyncing && isOnline && (
          <div className="flex items-center space-x-2 text-sm text-green-600">
            <CheckCircleIcon className="w-4 h-4" />
            <span>All changes synced</span>
          </div>
        )}
      </div>
    </div>
  )
}