"use client";

import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { API_CONFIG } from "@/config/api";

interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: string;
  priority: string;
  status: string;
  created_at: string;
  read_at?: string;
  archived_at?: string;
  metadata: Record<string, any>;
  action_url?: string;
  action_text?: string;
  expires_at?: string;
  is_expired: boolean;
}

interface NotificationStats {
  total: number;
  unread: number;
  read: number;
  archived: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  recent: Notification[];
}

const API_BASE = "/api/notifications/in-app";

// API functions
const notificationApi = {
  async getNotifications(
    userId: string,
    params?: {
      status?: string;
      notification_type?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<{ notifications: Notification[]; total: number }> {
    const searchParams = new URLSearchParams();
    searchParams.append("user_id", userId);

    if (params?.status) searchParams.append("status", params.status);
    if (params?.notification_type) searchParams.append("notification_type", params.notification_type);
    if (params?.limit) searchParams.append("limit", params.limit.toString());
    if (params?.offset) searchParams.append("offset", params.offset.toString());

    const response = await fetch(`${API_BASE}?${searchParams}`);
    if (!response.ok) {
      throw new Error("Failed to fetch notifications");
    }
    return response.json();
  },

  async getUnreadCount(userId: string): Promise<{ unread_count: number }> {
    const response = await fetch(`${API_BASE}/unread-count?user_id=${userId}`);
    if (!response.ok) {
      throw new Error("Failed to fetch unread count");
    }
    return response.json();
  },

  async getStats(userId: string): Promise<NotificationStats> {
    const response = await fetch(`${API_BASE}/stats?user_id=${userId}`);
    if (!response.ok) {
      throw new Error("Failed to fetch notification stats");
    }
    return response.json();
  },

  async markAsRead(userId: string, notificationId: string): Promise<{ success: boolean }> {
    const response = await fetch(`${API_BASE}/${notificationId}/read`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!response.ok) {
      throw new Error("Failed to mark notification as read");
    }
    return response.json();
  },

  async markAllAsRead(userId: string): Promise<{ marked_read: number }> {
    const response = await fetch(`${API_BASE}/mark-all-read`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!response.ok) {
      throw new Error("Failed to mark all notifications as read");
    }
    return response.json();
  },

  async archiveNotification(userId: string, notificationId: string): Promise<{ success: boolean }> {
    const response = await fetch(`${API_BASE}/${notificationId}/archive`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!response.ok) {
      throw new Error("Failed to archive notification");
    }
    return response.json();
  },

  async deleteNotification(userId: string, notificationId: string): Promise<{ success: boolean }> {
    const response = await fetch(`${API_BASE}/${notificationId}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!response.ok) {
      throw new Error("Failed to delete notification");
    }
    return response.json();
  },

  async createNotification(
    userId: string,
    notificationType: string,
    variables: Record<string, any>
  ): Promise<Notification> {
    const response = await fetch(`${API_BASE}/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: userId,
        notification_type: notificationType,
        variables,
      }),
    });
    if (!response.ok) {
      throw new Error("Failed to create notification");
    }
    return response.json();
  },
};

export function useNotifications(userId: string) {
  const queryClient = useQueryClient();
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  // Fetch notifications
  const {
    data: notificationsData,
    isLoading: loading,
    error,
    refetch: refreshNotifications,
  } = useQuery({
    queryKey: ["notifications", userId],
    queryFn: () => notificationApi.getNotifications(userId),
    enabled: !!userId,
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  // Fetch unread count
  const { data: unreadData } = useQuery({
    queryKey: ["notifications", userId, "unread-count"],
    queryFn: () => notificationApi.getUnreadCount(userId),
    enabled: !!userId,
    refetchInterval: 30000,
  });

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ["notifications", userId, "stats"],
    queryFn: () => notificationApi.getStats(userId),
    enabled: !!userId,
  });

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!userId) return;

    const wsUrl = `${API_CONFIG.WS_URL}${API_BASE}/ws/${userId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("WebSocket connected for notifications");
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Received notification update:", data);

      // Invalidate and refetch queries on real-time updates
      switch (data.type) {
        case "new_notification":
        case "notification_updated":
        case "notification_archived":
        case "notification_deleted":
        case "all_notifications_read":
          queryClient.invalidateQueries({ queryKey: ["notifications", userId] });
          queryClient.invalidateQueries({ queryKey: ["notifications", userId, "unread-count"] });
          queryClient.invalidateQueries({ queryKey: ["notifications", userId, "stats"] });
          break;
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setWsConnection(null);
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [userId, queryClient]);

  // Mutations
  const markAsReadMutation = useMutation({
    mutationFn: (notificationId: string) => notificationApi.markAsRead(userId, notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications", userId] });
      queryClient.invalidateQueries({ queryKey: ["notifications", userId, "unread-count"] });
    },
  });

  const markAllAsReadMutation = useMutation({
    mutationFn: () => notificationApi.markAllAsRead(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications", userId] });
      queryClient.invalidateQueries({ queryKey: ["notifications", userId, "unread-count"] });
    },
  });

  const archiveNotificationMutation = useMutation({
    mutationFn: (notificationId: string) => notificationApi.archiveNotification(userId, notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications", userId] });
    },
  });

  const deleteNotificationMutation = useMutation({
    mutationFn: (notificationId: string) => notificationApi.deleteNotification(userId, notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications", userId] });
      queryClient.invalidateQueries({ queryKey: ["notifications", userId, "unread-count"] });
    },
  });

  const createNotificationMutation = useMutation({
    mutationFn: ({ notificationType, variables }: { notificationType: string; variables: Record<string, any> }) =>
      notificationApi.createNotification(userId, notificationType, variables),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications", userId] });
      queryClient.invalidateQueries({ queryKey: ["notifications", userId, "unread-count"] });
    },
  });

  // Helper functions
  const markAsRead = useCallback(
    (notificationId: string) => markAsReadMutation.mutate(notificationId),
    [markAsReadMutation]
  );

  const markAllAsRead = useCallback(
    () => markAllAsReadMutation.mutate(),
    [markAllAsReadMutation]
  );

  const archiveNotification = useCallback(
    (notificationId: string) => archiveNotificationMutation.mutate(notificationId),
    [archiveNotificationMutation]
  );

  const deleteNotification = useCallback(
    (notificationId: string) => deleteNotificationMutation.mutate(notificationId),
    [deleteNotificationMutation]
  );

  const createNotification = useCallback(
    (notificationType: string, variables: Record<string, any>) =>
      createNotificationMutation.mutate({ notificationType, variables }),
    [createNotificationMutation]
  );

  // Quick notification creation helpers
  const quickNotifications = {
    documentAnalysisComplete: (documentName: string, documentId: string, analysisType = "comprehensive", keyFindingsCount = 0) =>
      createNotification("document_analysis", { document_name: documentName, document_id: documentId, analysis_type: analysisType, key_findings_count: keyFindingsCount }),

    qaResponse: (questionTopic: string, questionId: string, responderName: string) =>
      createNotification("qa_response", { question_topic: questionTopic, question_id: questionId, responder_name: responderName }),

    attorneyAction: (attorneyName: string, actionType: string, caseName: string, caseId: string, actionDescription: string) =>
      createNotification("attorney_action", { attorney_name: attorneyName, action_type: actionType, case_name: caseName, case_id: caseId, action_description: actionDescription }),

    deadlineReminder: (taskName: string, taskId: string, timeRemaining: string) =>
      createNotification("deadline_reminder", { task_name: taskName, task_id: taskId, time_remaining: timeRemaining }),

    systemAlert: (alertMessage: string, alertId?: string) =>
      createNotification("system_alert", { alert_message: alertMessage, alert_id: alertId }),
  };

  return {
    // Data
    notifications: notificationsData?.notifications || [],
    unreadCount: unreadData?.unread_count || 0,
    stats: statsData,
    total: notificationsData?.total || 0,

    // State
    loading,
    error,
    wsConnection,

    // Actions
    markAsRead,
    markAllAsRead,
    archiveNotification,
    deleteNotification,
    createNotification,
    refreshNotifications,

    // Quick helpers
    ...quickNotifications,
  };
}