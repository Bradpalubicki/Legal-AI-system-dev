"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { toast } from "sonner";
import { API_CONFIG } from "@/config/api";

interface CaseDocument {
  id: number;
  document_number: number;
  short_description: string;
  description: string;
  is_available: boolean;
}

interface CaseMonitorNotification {
  type: "new_documents" | "connection_established" | "check_complete" | "pong";
  timestamp?: string;
  docket_id?: number;
  case_name?: string;
  document_count?: number;
  documents?: CaseDocument[];
  total_new?: number;
  message?: string;
  poll_interval?: number;
}

export function useCaseMonitorNotifications() {
  const [connected, setConnected] = useState(false);
  const [notifications, setNotifications] = useState<CaseMonitorNotification[]>([]);
  const [latestNotification, setLatestNotification] = useState<CaseMonitorNotification | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const wsUrl = `${API_CONFIG.WS_URL}/api/v1/notifications/ws`;
    console.log("[CaseMonitor] Connecting to WebSocket:", wsUrl);

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("[CaseMonitor] WebSocket connected");
      setConnected(true);
      reconnectAttempts.current = 0; // Reset on successful connection
    };

    ws.onmessage = (event) => {
      try {
        const data: CaseMonitorNotification = JSON.parse(event.data);
        console.log("[CaseMonitor] Received notification:", data);

        // Update latest notification
        setLatestNotification(data);

        // Handle different message types
        switch (data.type) {
          case "connection_established":
            console.log(`[CaseMonitor] Connected. Poll interval: ${data.poll_interval}s`);
            toast.success("Connected to case monitoring service", {
              description: `Monitoring for new court documents`
            });
            break;

          case "new_documents":
            console.log(`[CaseMonitor] New documents detected:`, data);

            // Add to notifications list
            setNotifications((prev) => [data, ...prev].slice(0, 50)); // Keep last 50

            // Show toast notification
            const caseInfo = data.case_name || `Case ${data.docket_id}`;
            const docCount = data.total_new || data.document_count || 0;

            toast.success(`${docCount} new document${docCount > 1 ? 's' : ''} available!`, {
              description: `${caseInfo} - Click to view`,
              duration: 10000, // 10 seconds
              action: data.docket_id ? {
                label: "View Case",
                onClick: () => {
                  // Navigate to case page
                  window.location.href = `/pacer?docket=${data.docket_id}`;
                }
              } : undefined
            });
            break;

          case "check_complete":
            console.log("[CaseMonitor] Manual check completed");
            break;

          case "pong":
            // Heartbeat response
            break;

          default:
            console.log("[CaseMonitor] Unknown message type:", data);
        }
      } catch (error) {
        console.error("[CaseMonitor] Failed to parse message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("[CaseMonitor] WebSocket error:", error);
      setConnected(false);
    };

    ws.onclose = (event) => {
      console.log("[CaseMonitor] WebSocket disconnected:", event.code, event.reason);
      setConnected(false);
      wsRef.current = null;

      // Attempt to reconnect with exponential backoff
      if (reconnectAttempts.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        console.log(`[CaseMonitor] Reconnecting in ${delay}ms... (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);

        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current++;
          connect();
        }, delay);
      } else {
        console.error("[CaseMonitor] Max reconnection attempts reached");
        toast.error("Lost connection to case monitoring service", {
          description: "Please refresh the page to reconnect",
          duration: Infinity
        });
      }
    };

    wsRef.current = ws;
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      console.log("[CaseMonitor] Manually disconnecting WebSocket");
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
  }, []);

  const sendMessage = useCallback((message: Record<string, any>) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn("[CaseMonitor] Cannot send message - not connected");
    return false;
  }, []);

  const requestManualCheck = useCallback(() => {
    return sendMessage({ type: "check_now" });
  }, [sendMessage]);

  const sendPing = useCallback(() => {
    return sendMessage({ type: "ping" });
  }, [sendMessage]);

  const clearNotifications = useCallback(() => {
    setNotifications([]);
    setLatestNotification(null);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Periodic ping to keep connection alive (every 30 seconds)
  useEffect(() => {
    if (!connected) return;

    const pingInterval = setInterval(() => {
      sendPing();
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [connected, sendPing]);

  return {
    // State
    connected,
    notifications,
    latestNotification,
    unreadCount: notifications.filter(n => n.type === "new_documents").length,

    // Actions
    connect,
    disconnect,
    requestManualCheck,
    sendPing,
    clearNotifications,
  };
}
