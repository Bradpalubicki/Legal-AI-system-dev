import { EventEmitter } from 'events'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp: string
}

export interface CostUpdateMessage extends WebSocketMessage {
  type: 'cost_update'
  data: {
    userId: string
    costEvent: any
    totalSpent: number
    budgetUsed: number
  }
}

export interface BudgetAlertMessage extends WebSocketMessage {
  type: 'budget_alert'
  data: {
    budgetId: string
    alertType: string
    threshold: number
    currentAmount: number
    message: string
  }
}

export interface DocumentProcessingMessage extends WebSocketMessage {
  type: 'document_processing'
  data: {
    documentId: string
    status: 'processing' | 'completed' | 'error'
    progress?: number
    results?: any
  }
}

export interface SearchCompleteMessage extends WebSocketMessage {
  type: 'search_complete'
  data: {
    searchId: string
    results: any[]
    totalCost: number
    processingTime: number
  }
}

export type RealtimeMessage = 
  | CostUpdateMessage 
  | BudgetAlertMessage 
  | DocumentProcessingMessage 
  | SearchCompleteMessage

class WebSocketClient extends EventEmitter {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectInterval = 1000
  private heartbeatInterval: NodeJS.Timeout | null = null
  private isConnected = false
  private authToken: string | null = null

  constructor(url: string = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws') {
    super()
    this.url = url
  }

  connect(token?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        if (token) {
          this.authToken = token
        }

        const wsUrl = this.authToken 
          ? `${this.url}?token=${this.authToken}`
          : this.url

        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          console.log('WebSocket connected')
          this.isConnected = true
          this.reconnectAttempts = 0
          this.startHeartbeat()
          this.emit('connected')
          resolve()
        }

        this.ws.onmessage = (event) => {
          try {
            const message: RealtimeMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason)
          this.isConnected = false
          this.stopHeartbeat()
          this.emit('disconnected', event)

          // Attempt to reconnect unless it was a clean close
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect()
          }
        }

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          this.emit('error', error)
          reject(error)
        }

      } catch (error) {
        reject(error)
      }
    })
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect')
      this.ws = null
    }
    this.stopHeartbeat()
    this.isConnected = false
  }

  private reconnect(): void {
    this.reconnectAttempts++
    const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts), 30000)
    
    console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`)
    
    setTimeout(() => {
      if (!this.isConnected) {
        this.connect(this.authToken || undefined).catch(() => {
          // Reconnection failed, will try again or give up
        })
      }
    }, delay)
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }))
      }
    }, 30000) // Send ping every 30 seconds
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  private handleMessage(message: RealtimeMessage): void {
    this.emit('message', message)
    this.emit(message.type, message.data)

    // Log important events
    if (message.type === 'budget_alert') {
      console.warn('Budget alert:', message.data)
    }
  }

  send(message: any): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
      return true
    }
    return false
  }

  getConnectionState(): string {
    if (!this.ws) return 'disconnected'
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING: return 'connecting'
      case WebSocket.OPEN: return 'connected'
      case WebSocket.CLOSING: return 'closing'
      case WebSocket.CLOSED: return 'disconnected'
      default: return 'unknown'
    }
  }

  isConnectionReady(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN
  }

  // Subscribe to specific user events
  subscribeToUser(userId: string): void {
    this.send({
      type: 'subscribe',
      channel: `user:${userId}`
    })
  }

  // Subscribe to budget alerts
  subscribeToBudgetAlerts(budgetId?: string): void {
    this.send({
      type: 'subscribe',
      channel: budgetId ? `budget:${budgetId}` : 'budget_alerts'
    })
  }

  // Subscribe to document processing updates
  subscribeToDocuments(documentId?: string): void {
    this.send({
      type: 'subscribe',
      channel: documentId ? `document:${documentId}` : 'documents'
    })
  }

  // Subscribe to search updates
  subscribeToSearches(userId: string): void {
    this.send({
      type: 'subscribe',
      channel: `search:${userId}`
    })
  }
}

// Singleton instance
export const websocketClient = new WebSocketClient()

// React hook for WebSocket connection
export function useWebSocket() {
  return websocketClient
}

export default WebSocketClient