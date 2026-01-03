import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useWebSocketConnection } from './useWebSocket'

interface AutoRefreshOptions {
  interval?: number
  enabled?: boolean
  onlyWhenVisible?: boolean
  onlyWhenConnected?: boolean
}

export function useAutoRefresh(
  queryKeys: string[][],
  options: AutoRefreshOptions = {}
) {
  const {
    interval = 30000, // 30 seconds default
    enabled = true,
    onlyWhenVisible = true,
    onlyWhenConnected = true
  } = options

  const queryClient = useQueryClient()
  const { isConnected } = useWebSocketConnection(false)
  const intervalRef = useRef<NodeJS.Timeout>()
  const isVisible = useRef(true)

  const refresh = useCallback(() => {
    if (!enabled) return
    if (onlyWhenVisible && !isVisible.current) return
    if (onlyWhenConnected && !isConnected) return

    queryKeys.forEach(queryKey => {
      queryClient.invalidateQueries({ queryKey })
    })
  }, [enabled, onlyWhenVisible, onlyWhenConnected, isConnected, queryClient, queryKeys])

  // Handle visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      isVisible.current = !document.hidden
      
      // Refresh immediately when becoming visible
      if (!document.hidden && enabled) {
        refresh()
      }
    }

    if (onlyWhenVisible) {
      document.addEventListener('visibilitychange', handleVisibilityChange)
      return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [onlyWhenVisible, enabled, refresh])

  // Setup interval
  useEffect(() => {
    if (!enabled) return

    intervalRef.current = setInterval(refresh, interval)
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [enabled, interval, refresh])

  // Refresh when reconnected
  useEffect(() => {
    if (onlyWhenConnected && isConnected) {
      refresh()
    }
  }, [isConnected, onlyWhenConnected, refresh])

  return { refresh, isConnected, isVisible: isVisible.current }
}

export function useSmartRefresh() {
  const queryClient = useQueryClient()
  const { isConnected } = useWebSocketConnection(false)

  const refreshByPattern = useCallback((patterns: string[]) => {
    patterns.forEach(pattern => {
      queryClient.invalidateQueries({ 
        predicate: (query) => {
          return query.queryKey.some(key => 
            typeof key === 'string' && key.includes(pattern)
          )
        }
      })
    })
  }, [queryClient])

  const refreshCostData = useCallback(() => {
    refreshByPattern(['costs', 'budget', 'dashboard'])
  }, [refreshByPattern])

  const refreshSearchData = useCallback(() => {
    refreshByPattern(['search', 'queries'])
  }, [refreshByPattern])

  const refreshDocumentData = useCallback(() => {
    refreshByPattern(['documents', 'analysis'])
  }, [refreshByPattern])

  const refreshAll = useCallback(() => {
    queryClient.invalidateQueries()
  }, [queryClient])

  return {
    refreshByPattern,
    refreshCostData,
    refreshSearchData,
    refreshDocumentData,
    refreshAll,
    isConnected
  }
}

// Hook for time-based auto-refresh (morning, afternoon, evening)
export function useTimeBasedRefresh(queryKeys: string[][], enabled = true) {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!enabled) return

    const checkAndRefresh = () => {
      const now = new Date()
      const hour = now.getHours()
      
      // Refresh at start of business hours (9 AM), lunch (12 PM), and end of day (5 PM)
      if (hour === 9 || hour === 12 || hour === 17) {
        const minute = now.getMinutes()
        const second = now.getSeconds()
        
        // Only refresh at the exact start of these hours
        if (minute === 0 && second < 10) {
          queryKeys.forEach(queryKey => {
            queryClient.invalidateQueries({ queryKey })
          })
        }
      }
    }

    // Check every 10 seconds
    const interval = setInterval(checkAndRefresh, 10000)
    
    return () => clearInterval(interval)
  }, [enabled, queryClient, queryKeys])
}

// Hook for connection-aware caching
export function useConnectionAwareCache() {
  const queryClient = useQueryClient()
  const { isConnected } = useWebSocketConnection(false)

  useEffect(() => {
    // When offline, increase stale time to avoid unnecessary refetch attempts
    // When online, reduce stale time for fresher data
    const newDefaults = {
      staleTime: isConnected ? 2 * 60 * 1000 : 30 * 60 * 1000, // 2 min online, 30 min offline
      gcTime: isConnected ? 10 * 60 * 1000 : 60 * 60 * 1000,   // 10 min online, 1 hour offline
    }

    queryClient.setDefaultOptions({
      queries: newDefaults
    })
  }, [isConnected, queryClient])

  return { isConnected }
}

// Hook for periodic background sync
export function useBackgroundSync(
  syncFunction: () => Promise<void>,
  interval = 5 * 60 * 1000 // 5 minutes
) {
  const { isConnected } = useWebSocketConnection(false)
  const syncRef = useRef<() => Promise<void>>(syncFunction)

  // Update sync function reference
  useEffect(() => {
    syncRef.current = syncFunction
  }, [syncFunction])

  useEffect(() => {
    if (!isConnected) return

    const performSync = async () => {
      try {
        await syncRef.current()
      } catch (error) {
        console.warn('Background sync failed:', error)
      }
    }

    // Initial sync
    performSync()

    // Periodic sync
    const intervalId = setInterval(performSync, interval)

    return () => clearInterval(intervalId)
  }, [isConnected, interval])

  return { isConnected }
}