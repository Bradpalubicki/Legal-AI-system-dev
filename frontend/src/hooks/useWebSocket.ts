import { useEffect, useState, useCallback, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { websocketClient, type RealtimeMessage } from '../lib/websocket'
import { costKeys } from './useCosts'
import { searchKeys } from './useSearch'

export interface WebSocketState {
  isConnected: boolean
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'closing'
  error: any
  lastMessage: RealtimeMessage | null
}

export function useWebSocketConnection(autoConnect: boolean = true) {
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    connectionState: 'disconnected',
    error: null,
    lastMessage: null
  })

  const queryClient = useQueryClient()
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()

  const connect = useCallback(async (token?: string) => {
    try {
      setState(prev => ({ ...prev, connectionState: 'connecting', error: null }))
      await websocketClient.connect(token)
    } catch (error) {
      setState(prev => ({ ...prev, error, connectionState: 'disconnected' }))
    }
  }, [])

  const disconnect = useCallback(() => {
    websocketClient.disconnect()
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
  }, [])

  useEffect(() => {
    const handleConnected = () => {
      setState(prev => ({ 
        ...prev, 
        isConnected: true, 
        connectionState: 'connected',
        error: null 
      }))
    }

    const handleDisconnected = () => {
      setState(prev => ({ 
        ...prev, 
        isConnected: false, 
        connectionState: 'disconnected' 
      }))
    }

    const handleError = (error: any) => {
      setState(prev => ({ ...prev, error }))
    }

    const handleMessage = (message: RealtimeMessage) => {
      setState(prev => ({ ...prev, lastMessage: message }))
      
      // Invalidate relevant queries based on message type
      switch (message.type) {
        case 'cost_update':
          queryClient.invalidateQueries({ queryKey: costKeys.dashboard('30d') })
          queryClient.invalidateQueries({ queryKey: costKeys.events() })
          queryClient.invalidateQueries({ queryKey: costKeys.usage() })
          break
          
        case 'budget_alert':
          queryClient.invalidateQueries({ queryKey: costKeys.budgets() })
          queryClient.invalidateQueries({ queryKey: costKeys.alerts() })
          break
          
        case 'search_complete':
          queryClient.invalidateQueries({ queryKey: searchKeys.queries() })
          break
          
        case 'document_processing':
          // Invalidate document queries if we had them
          break
      }
    }

    websocketClient.on('connected', handleConnected)
    websocketClient.on('disconnected', handleDisconnected)
    websocketClient.on('error', handleError)
    websocketClient.on('message', handleMessage)

    // Auto-connect if requested
    if (autoConnect && !websocketClient.isConnectionReady()) {
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
      connect(token || undefined)
    }

    return () => {
      websocketClient.off('connected', handleConnected)
      websocketClient.off('disconnected', handleDisconnected)
      websocketClient.off('error', handleError)
      websocketClient.off('message', handleMessage)
    }
  }, [autoConnect, connect, queryClient])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
    }
  }, [])

  return {
    ...state,
    connect,
    disconnect,
    send: websocketClient.send.bind(websocketClient)
  }
}

export function useRealtimeUpdates(userId?: string) {
  const { isConnected } = useWebSocketConnection()
  const [notifications, setNotifications] = useState<RealtimeMessage[]>([])

  useEffect(() => {
    if (!isConnected || !userId) return

    // Subscribe to user-specific events
    websocketClient.subscribeToUser(userId)
    websocketClient.subscribeToBudgetAlerts()
    websocketClient.subscribeToSearches(userId)

    const handleCostUpdate = (data: any) => {
      // Handle real-time cost updates
      console.log('Cost update received:', data)
    }

    const handleBudgetAlert = (data: any) => {
      // Add to notifications
      const message: RealtimeMessage = {
        type: 'budget_alert',
        data,
        timestamp: new Date().toISOString()
      }
      setNotifications(prev => [message, ...prev.slice(0, 49)]) // Keep last 50
    }

    const handleDocumentProcessing = (data: any) => {
      // Handle document processing updates
      console.log('Document processing update:', data)
    }

    const handleSearchComplete = (data: any) => {
      // Handle search completion
      console.log('Search completed:', data)
      const message: RealtimeMessage = {
        type: 'search_complete',
        data,
        timestamp: new Date().toISOString()
      }
      setNotifications(prev => [message, ...prev.slice(0, 49)])
    }

    websocketClient.on('cost_update', handleCostUpdate)
    websocketClient.on('budget_alert', handleBudgetAlert)
    websocketClient.on('document_processing', handleDocumentProcessing)
    websocketClient.on('search_complete', handleSearchComplete)

    return () => {
      websocketClient.off('cost_update', handleCostUpdate)
      websocketClient.off('budget_alert', handleBudgetAlert)
      websocketClient.off('document_processing', handleDocumentProcessing)
      websocketClient.off('search_complete', handleSearchComplete)
    }
  }, [isConnected, userId])

  const clearNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  const removeNotification = useCallback((index: number) => {
    setNotifications(prev => prev.filter((_, i) => i !== index))
  }, [])

  return {
    notifications,
    clearNotifications,
    removeNotification,
    isConnected
  }
}

export function useLiveData<T>(
  queryKey: any[],
  fetchFn: () => Promise<T>,
  refreshInterval: number = 30000 // 30 seconds default
) {
  const [data, setData] = useState<T | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<any>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  
  const intervalRef = useRef<NodeJS.Timeout>()
  const { isConnected } = useWebSocketConnection(false)

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true)
      const result = await fetchFn()
      setData(result)
      setError(null)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err)
    } finally {
      setIsLoading(false)
    }
  }, [fetchFn])

  useEffect(() => {
    // Initial fetch
    fetchData()

    // Set up polling interval
    intervalRef.current = setInterval(fetchData, refreshInterval)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [fetchData, refreshInterval])

  // Refresh when reconnected
  useEffect(() => {
    if (isConnected) {
      fetchData()
    }
  }, [isConnected, fetchData])

  const refresh = useCallback(() => {
    fetchData()
  }, [fetchData])

  return {
    data,
    isLoading,
    error,
    lastUpdated,
    refresh
  }
}