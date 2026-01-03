import { useState, useEffect, useRef, useCallback } from 'react'

export interface WebSocketMessage {
  data: string
  timestamp: number
  type: string
}

export interface WebSocketHookReturn {
  isConnected: boolean
  isConnecting: boolean
  lastMessage: WebSocketMessage | null
  error: string | null
  sendMessage: (message: string) => void
  reconnect: () => void
  disconnect: () => void
}

export const useWebSocket = (url: string, options?: {
  reconnectInterval?: number
  maxReconnectAttempts?: number
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
}): WebSocketHookReturn => {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttempts = useRef(0)
  const shouldReconnect = useRef(true)

  const {
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onOpen,
    onClose,
    onError
  } = options || {}

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setIsConnecting(true)
    setError(null)

    try {
      wsRef.current = new WebSocket(url)

      wsRef.current.onopen = () => {
        console.log('WebSocket connected:', url)
        setIsConnected(true)
        setIsConnecting(false)
        setError(null)
        reconnectAttempts.current = 0
        onOpen?.()
      }

      wsRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason)
        setIsConnected(false)
        setIsConnecting(false)
        onClose?.()

        // Attempt to reconnect if not manually disconnected
        if (shouldReconnect.current && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++
          console.log(`Reconnecting... Attempt ${reconnectAttempts.current}/${maxReconnectAttempts}`)

          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectInterval)
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setError('Max reconnection attempts reached')
        }
      }

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event)
        setError('WebSocket connection error')
        setIsConnecting(false)
        onError?.(event)
      }

      wsRef.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = {
            data: event.data,
            timestamp: Date.now(),
            type: 'message'
          }
          setLastMessage(message)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
          setError('Failed to parse message')
        }
      }
    } catch (err) {
      console.error('Failed to create WebSocket connection:', err)
      setError('Failed to create connection')
      setIsConnecting(false)
    }
  }, [url, onOpen, onClose, onError, reconnectInterval, maxReconnectAttempts])

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(message)
      } catch (err) {
        console.error('Failed to send WebSocket message:', err)
        setError('Failed to send message')
      }
    } else {
      console.warn('WebSocket is not connected. Cannot send message:', message)
      setError('WebSocket not connected')
    }
  }, [])

  const disconnect = useCallback(() => {
    shouldReconnect.current = false

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }

    setIsConnected(false)
    setIsConnecting(false)
  }, [])

  const reconnect = useCallback(() => {
    shouldReconnect.current = true
    reconnectAttempts.current = 0
    disconnect()
    setTimeout(connect, 100)
  }, [connect, disconnect])

  // Initial connection
  useEffect(() => {
    connect()

    // Cleanup on unmount
    return () => {
      shouldReconnect.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  // Handle page visibility changes for reconnection
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && !isConnected && shouldReconnect.current) {
        console.log('Page became visible, attempting to reconnect WebSocket')
        reconnect()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [isConnected, reconnect])

  return {
    isConnected,
    isConnecting,
    lastMessage,
    error,
    sendMessage,
    reconnect,
    disconnect
  }
}