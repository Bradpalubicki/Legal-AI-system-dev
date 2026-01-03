"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  CheckCircle2,
  Clock,
  Archive,
  Trash2,
  MarkAsUnread,
  ExternalLink,
} from "lucide-react";
import { NotificationItem } from "./NotificationItem";
import { useNotifications } from "@/hooks/useNotifications";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface NotificationCenterProps {
  userId: string;
  onClose?: () => void;
  onMarkAllRead?: () => void;
}

export function NotificationCenterNew({
  userId,
  onClose,
  onMarkAllRead,
}: NotificationCenterProps) {
  const [activeTab, setActiveTab] = useState("all");
  const {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    archiveNotification,
    deleteNotification,
    markAllAsRead,
    refreshNotifications,
  } = useNotifications(userId);

  const filteredNotifications = notifications.filter((notification) => {
    switch (activeTab) {
      case "unread":
        return notification.status === "unread";
      case "read":
        return notification.status === "read";
      case "archived":
        return notification.status === "archived";
      default:
        return notification.status !== "archived";
    }
  });

  const handleMarkAllRead = async () => {
    await markAllAsRead();
    onMarkAllRead?.();
  };

  const handleMarkAsRead = async (notificationId: string) => {
    await markAsRead(notificationId);
  };

  const handleArchive = async (notificationId: string) => {
    await archiveNotification(notificationId);
  };

  const handleDelete = async (notificationId: string) => {
    await deleteNotification(notificationId);
  };

  const getTabCount = (tab: string) => {
    switch (tab) {
      case "unread":
        return notifications.filter((n) => n.status === "unread").length;
      case "read":
        return notifications.filter((n) => n.status === "read").length;
      case "archived":
        return notifications.filter((n) => n.status === "archived").length;
      default:
        return notifications.filter((n) => n.status !== "archived").length;
    }
  };

  return (
    <div className="w-full max-w-md">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <h3 className="font-semibold text-lg">Notifications</h3>
          {unreadCount > 0 && (
            <Badge variant="secondary" className="text-xs">
              {unreadCount}
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleMarkAllRead}
              className="text-xs"
            >
              <CheckCircle2 className="h-3 w-3 mr-1" />
              Mark all read
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={refreshNotifications}
            className="text-xs"
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="px-4 pt-2">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="all" className="text-xs relative">
              All
              {getTabCount("all") > 0 && (
                <Badge
                  variant="secondary"
                  className="ml-1 text-xs h-4 w-4 p-0 flex items-center justify-center"
                >
                  {getTabCount("all")}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="unread" className="text-xs relative">
              Unread
              {getTabCount("unread") > 0 && (
                <Badge
                  variant="destructive"
                  className="ml-1 text-xs h-4 w-4 p-0 flex items-center justify-center"
                >
                  {getTabCount("unread")}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="read" className="text-xs">
              Read
            </TabsTrigger>
            <TabsTrigger value="archived" className="text-xs">
              Archived
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Content */}
        <div className="h-96">
          <ScrollArea className="h-full">
            <TabsContent value={activeTab} className="mt-0">
              {loading ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  Loading notifications...
                </div>
              ) : filteredNotifications.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  {activeTab === "unread" && "No unread notifications"}
                  {activeTab === "read" && "No read notifications"}
                  {activeTab === "archived" && "No archived notifications"}
                  {activeTab === "all" && "No notifications yet"}
                </div>
              ) : (
                <div className="divide-y">
                  {filteredNotifications.map((notification, index) => (
                    <NotificationItem
                      key={notification.id}
                      notification={notification}
                      onMarkAsRead={() => handleMarkAsRead(notification.id)}
                      onArchive={() => handleArchive(notification.id)}
                      onDelete={() => handleDelete(notification.id)}
                      onClose={onClose}
                    />
                  ))}
                </div>
              )}
            </TabsContent>
          </ScrollArea>
        </div>
      </Tabs>

      {/* Footer */}
      <div className="border-t p-3">
        <Button
          variant="outline"
          size="sm"
          className="w-full text-xs"
          onClick={onClose}
        >
          Close
        </Button>
      </div>
    </div>
  );
}