'use client'

import { useState, useEffect, useCallback } from 'react'
import { useOfflineStorage } from './useOfflineStorage'

interface SyncItem {
  id: string
  type: 'document-upload' | 'annotation-sync' | 'search-cache' | 'user-action'
  data: any
  endpoint: string
  method: 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  headers?: Record<string, string>
  retryCount: number
  maxRetries: number
  timestamp: number
  priority: 'low' | 'medium' | 'high' | 'critical'
}

interface BackgroundSyncHook {
  // State
  isOnline: boolean
  isSyncing: boolean
  pendingItems: SyncItem[]
  syncProgress: number
  
  // Actions
  queueSync: (item: Omit<SyncItem, 'id' | 'retryCount' | 'timestamp'>) => Promise<void>
  forcSync: () => Promise<void>
  clearQueue: () => Promise<void>
  retryFailedSync: (itemId: string) => Promise<void>
  
  // Utilities
  getPendingCount: () => number
  getFailedItems: () => SyncItem[]
  getSyncStatus: () => 'idle' | 'syncing' | 'failed' | 'success'
}

export function useBackgroundSync(): BackgroundSyncHook {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [isSyncing, setIsSyncing] = useState(false)
  const [syncProgress, setSyncProgress] = useState(0)
  const [serviceWorkerRegistration, setServiceWorkerRegistration] = useState<ServiceWorkerRegistration | null>(null)

  // Offline storage for sync queue
  const {
    data: pendingItems,
    setItem: queueItem,
    removeItem: removeQueueItem,
    getAll: getAllQueueItems,
    clear: clearAllItems
  } = useOfflineStorage<SyncItem>({
    storeName: 'sync-queue',
    maxItems: 1000,
    ttl: 7 * 24 * 60 * 60 * 1000 // 7 days
  })

  // Initialize service worker registration
  useEffect(() => {
    const initializeSync = async () => {
      if ('serviceWorker' in navigator) {
        try {
          const registration = await navigator.serviceWorker.ready
          setServiceWorkerRegistration(registration)
          
          // Listen for sync events from service worker
          navigator.serviceWorker.addEventListener('message', handleServiceWorkerMessage)
        } catch (error) {
          console.error('Failed to initialize background sync:', error)
        }
      }
    }

    initializeSync()

    return () => {
      navigator.serviceWorker.removeEventListener('message', handleServiceWorkerMessage)
    }
  }, [])

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      // Trigger sync when coming back online
      if (pendingItems.length > 0) {
        forcSync()
      }
    }

    const handleOffline = () => {
      setIsOnline(false)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [pendingItems.length])

  // Handle messages from service worker
  const handleServiceWorkerMessage = (event: MessageEvent) => {
    const { type, payload } = event.data

    switch (type) {
      case 'SYNC_PROGRESS':
        setSyncProgress(payload.progress)
        break
      
      case 'SYNC_COMPLETE':
        setIsSyncing(false)
        setSyncProgress(100)
        // Remove successfully synced items
        if (payload.syncedItems) {
          payload.syncedItems.forEach((itemId: string) => {
            removeQueueItem(itemId)
          })
        }
        break
      
      case 'SYNC_FAILED':
        setIsSyncing(false)
        setSyncProgress(0)
        console.error('Background sync failed:', payload.error)
        break
      
      case 'ITEM_SYNCED':
        // Remove individual synced item
        removeQueueItem(payload.itemId)
        break
    }
  }

  // Queue item for background sync
  const queueSync = useCallback(async (
    item: Omit<SyncItem, 'id' | 'retryCount' | 'timestamp'>
  ): Promise<void> => {
    const syncItem: SyncItem = {
      ...item,
      id: `sync_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      retryCount: 0,
      timestamp: Date.now()
    }

    await queueItem(syncItem.id, syncItem)

    // Try to sync immediately if online
    if (isOnline && serviceWorkerRegistration) {
      try {
        // Request background sync
        await serviceWorkerRegistration.sync.register(syncItem.type)
      } catch (error) {
        console.warn('Background sync registration failed, will retry when online:', error)
      }
    }
  }, [isOnline, serviceWorkerRegistration, queueItem])

  // Force immediate sync
  const forcSync = useCallback(async (): Promise<void> => {
    if (!isOnline || isSyncing || pendingItems.length === 0) {
      return
    }

    setIsSyncing(true)
    setSyncProgress(0)

    try {
      const itemsToSync = pendingItems
        .sort((a, b) => {
          // Sort by priority and timestamp
          const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 }
          const priorityDiff = priorityOrder[a.priority] - priorityOrder[b.priority]
          return priorityDiff !== 0 ? priorityDiff : a.timestamp - b.timestamp
        })

      let syncedCount = 0

      for (const item of itemsToSync) {
        try {
          await syncSingleItem(item)
          await removeQueueItem(item.id)
          syncedCount++
          
          setSyncProgress((syncedCount / itemsToSync.length) * 100)
        } catch (error) {
          console.error(`Failed to sync item ${item.id}:`, error)
          
          // Increment retry count
          const updatedItem = {
            ...item,
            retryCount: item.retryCount + 1
          }

          if (updatedItem.retryCount < item.maxRetries) {
            await queueItem(item.id, updatedItem)
          } else {
            console.error(`Item ${item.id} exceeded max retries, removing from queue`)
            await removeQueueItem(item.id)
          }
        }
      }

      setIsSyncing(false)
      setSyncProgress(100)
      
      // Reset progress after a short delay
      setTimeout(() => setSyncProgress(0), 2000)
    } catch (error) {
      console.error('Force sync failed:', error)
      setIsSyncing(false)
      setSyncProgress(0)
    }
  }, [isOnline, isSyncing, pendingItems, removeQueueItem, queueItem])

  // Sync single item
  const syncSingleItem = async (item: SyncItem): Promise<void> => {
    const response = await fetch(item.endpoint, {
      method: item.method,
      headers: {
        'Content-Type': 'application/json',
        ...item.headers
      },
      body: item.method !== 'GET' ? JSON.stringify(item.data) : undefined
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    return response.json()
  }

  // Clear all queued items
  const clearQueue = useCallback(async (): Promise<void> => {
    await clearAllItems()
  }, [clearAllItems])

  // Retry specific failed item
  const retryFailedSync = useCallback(async (itemId: string): Promise<void> => {
    const item = pendingItems.find(p => p.id === itemId)
    if (!item) return

    if (!isOnline) {
      console.warn('Cannot retry sync while offline')
      return
    }

    try {
      await syncSingleItem(item)
      await removeQueueItem(itemId)
    } catch (error) {
      console.error('Retry sync failed:', error)
      
      // Increment retry count
      const updatedItem = {
        ...item,
        retryCount: item.retryCount + 1
      }

      if (updatedItem.retryCount < item.maxRetries) {
        await queueItem(itemId, updatedItem)
      } else {
        await removeQueueItem(itemId)
      }
    }
  }, [isOnline, pendingItems, removeQueueItem, queueItem])

  // Get pending count
  const getPendingCount = useCallback((): number => {
    return pendingItems.length
  }, [pendingItems.length])

  // Get failed items (those that have reached max retries)
  const getFailedItems = useCallback((): SyncItem[] => {
    return pendingItems.filter(item => item.retryCount >= item.maxRetries)
  }, [pendingItems])

  // Get overall sync status
  const getSyncStatus = useCallback((): 'idle' | 'syncing' | 'failed' | 'success' => {
    if (isSyncing) return 'syncing'
    if (getFailedItems().length > 0) return 'failed'
    if (pendingItems.length === 0 && syncProgress === 100) return 'success'
    return 'idle'
  }, [isSyncing, pendingItems.length, syncProgress, getFailedItems])

  return {
    isOnline,
    isSyncing,
    pendingItems,
    syncProgress,
    queueSync,
    forcSync,
    clearQueue,
    retryFailedSync,
    getPendingCount,
    getFailedItems,
    getSyncStatus
  }
}

// Predefined sync actions for common use cases
export const SyncActions = {
  uploadDocument: (file: File, metadata: any): Omit<SyncItem, 'id' | 'retryCount' | 'timestamp'> => ({
    type: 'document-upload',
    data: { file, metadata },
    endpoint: '/api/documents/upload',
    method: 'POST',
    maxRetries: 3,
    priority: 'high'
  }),

  saveAnnotation: (documentId: string, annotation: any): Omit<SyncItem, 'id' | 'retryCount' | 'timestamp'> => ({
    type: 'annotation-sync',
    data: annotation,
    endpoint: `/api/documents/${documentId}/annotations`,
    method: 'POST',
    maxRetries: 5,
    priority: 'medium'
  }),

  updateAnnotation: (documentId: string, annotationId: string, updates: any): Omit<SyncItem, 'id' | 'retryCount' | 'timestamp'> => ({
    type: 'annotation-sync',
    data: updates,
    endpoint: `/api/documents/${documentId}/annotations/${annotationId}`,
    method: 'PATCH',
    maxRetries: 5,
    priority: 'medium'
  }),

  deleteAnnotation: (documentId: string, annotationId: string): Omit<SyncItem, 'id' | 'retryCount' | 'timestamp'> => ({
    type: 'annotation-sync',
    data: null,
    endpoint: `/api/documents/${documentId}/annotations/${annotationId}`,
    method: 'DELETE',
    maxRetries: 3,
    priority: 'low'
  }),

  saveSearch: (query: string, results: any[]): Omit<SyncItem, 'id' | 'retryCount' | 'timestamp'> => ({
    type: 'search-cache',
    data: { query, results, timestamp: Date.now() },
    endpoint: '/api/search/cache',
    method: 'POST',
    maxRetries: 2,
    priority: 'low'
  }),

  saveUserAction: (action: string, data: any): Omit<SyncItem, 'id' | 'retryCount' | 'timestamp'> => ({
    type: 'user-action',
    data: { action, data, timestamp: Date.now() },
    endpoint: '/api/analytics/actions',
    method: 'POST',
    maxRetries: 1,
    priority: 'low'
  })
}