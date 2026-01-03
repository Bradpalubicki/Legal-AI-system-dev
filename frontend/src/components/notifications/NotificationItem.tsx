"use client";

import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  FileText,
  MessageCircle,
  Users,
  AlertTriangle,
  Clock,
  CheckCircle,
  CreditCard,
  Shield,
  Bell,
  MoreVertical,
  ExternalLink,
  Archive,
  Trash2,
  Eye,
} from "lucide-react";
import { cn } from "@/lib/utils";

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

interface NotificationItemProps {
  notification: Notification;
  onMarkAsRead: () => void;
  onArchive: () => void;
  onDelete: () => void;
  onClose?: () => void;
}

const notificationIcons: Record<string, any> = {
  document_analysis: FileText,
  qa_response: MessageCircle,
  attorney_action: Users,
  case_update: FileText,
  system_alert: AlertTriangle,
  deadline_reminder: Clock,
  message: MessageCircle,
  payment: CreditCard,
  security: Shield,
};

const priorityColors: Record<string, string> = {
  low: "bg-gray-100 text-gray-700 border-gray-200",
  medium: "bg-blue-100 text-blue-700 border-blue-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  urgent: "bg-red-100 text-red-700 border-red-200",
};

const typeColors: Record<string, string> = {
  document_analysis: "text-blue-600",
  qa_response: "text-green-600",
  attorney_action: "text-purple-600",
  case_update: "text-indigo-600",
  system_alert: "text-red-600",
  deadline_reminder: "text-orange-600",
  message: "text-teal-600",
  payment: "text-emerald-600",
  security: "text-red-600",
};

export function NotificationItem({
  notification,
  onMarkAsRead,
  onArchive,
  onDelete,
  onClose,
}: NotificationItemProps) {
  const [isHovered, setIsHovered] = useState(false);

  const Icon = notificationIcons[notification.type] || Bell;
  const isUnread = notification.status === "unread";
  const isArchived = notification.status === "archived";

  const handleClick = () => {
    if (isUnread) {
      onMarkAsRead();
    }

    if (notification.action_url) {
      window.open(notification.action_url, "_blank");
      onClose?.();
    }
  };

  const handleAction = (action: string, event: React.MouseEvent) => {
    event.stopPropagation();
    switch (action) {
      case "read":
        onMarkAsRead();
        break;
      case "archive":
        onArchive();
        break;
      case "delete":
        onDelete();
        break;
    }
  };

  const formatTime = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true });
    } catch {
      return "Unknown time";
    }
  };

  return (
    <div
      className={cn(
        "relative p-4 hover:bg-gray-50 transition-colors cursor-pointer group",
        isUnread && "bg-blue-50/50 border-l-2 border-l-blue-500",
        isArchived && "opacity-60"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={handleClick}
    >
      <div className="flex items-start space-x-3">
        {/* Icon */}
        <div
          className={cn(
            "flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center",
            typeColors[notification.type]
          )}
        >
          <Icon className="w-4 h-4" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h4
                  className={cn(
                    "text-sm font-medium text-gray-900 truncate",
                    isUnread && "font-semibold"
                  )}
                >
                  {notification.title}
                </h4>
                {isUnread && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" />
                )}
              </div>

              <div className="flex items-center gap-2 mb-2">
                <Badge
                  variant="outline"
                  className={cn(
                    "text-xs px-2 py-0",
                    priorityColors[notification.priority]
                  )}
                >
                  {notification.priority}
                </Badge>
                <span className="text-xs text-gray-500 capitalize">
                  {notification.type.replace("_", " ")}
                </span>
              </div>

              <p className="text-sm text-gray-600 line-clamp-2 mb-2">
                {notification.message}
              </p>

              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  {formatTime(notification.created_at)}
                </span>

                {notification.action_url && (
                  <div className="flex items-center gap-1 text-xs text-blue-600">
                    <ExternalLink className="w-3 h-3" />
                    {notification.action_text || "View"}
                  </div>
                )}
              </div>
            </div>

            {/* Actions dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "h-8 w-8 p-0 transition-opacity",
                    !isHovered && "opacity-0 group-hover:opacity-100"
                  )}
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="h-4 w-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                {isUnread && (
                  <DropdownMenuItem
                    onClick={(e) => handleAction("read", e)}
                    className="text-sm"
                  >
                    <Eye className="w-4 h-4 mr-2" />
                    Mark as read
                  </DropdownMenuItem>
                )}
                {!isArchived && (
                  <DropdownMenuItem
                    onClick={(e) => handleAction("archive", e)}
                    className="text-sm"
                  >
                    <Archive className="w-4 h-4 mr-2" />
                    Archive
                  </DropdownMenuItem>
                )}
                <DropdownMenuItem
                  onClick={(e) => handleAction("delete", e)}
                  className="text-sm text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Expired indicator */}
      {notification.is_expired && (
        <div className="absolute top-2 right-2">
          <Badge variant="destructive" className="text-xs">
            Expired
          </Badge>
        </div>
      )}
    </div>
  );
}