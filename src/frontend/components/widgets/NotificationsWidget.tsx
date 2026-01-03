import React, { useEffect, useState } from 'react'
import { Bell, AlertTriangle, Info, CheckCircle, X } from 'lucide-react'

interface NotificationsWidgetProps {
  filters: any
  realTimeData: any
  isSelected: boolean
}

export const NotificationsWidget: React.FC<NotificationsWidgetProps> = ({
  filters,
  realTimeData,
  isSelected
}) => {
  const [notificationData, setNotificationData] = useState({
    unread: 0,
    recent: [],
    alerts: []
  })

  useEffect(() => {
    if (realTimeData?.notifications) {
      setNotificationData(realTimeData.notifications)
    }
  }, [realTimeData])

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'error': return <X className="w-4 h-4 text-red-500" />
      case 'warning': return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'success': return <CheckCircle className="w-4 h-4 text-green-500" />
      default: return <Info className="w-4 h-4 text-blue-500" />
    }
  }

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date()
    const time = new Date(timestamp)
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }

  return (
    <div className="h-full flex flex-col">
      <div className="bg-blue-50 p-3 rounded-lg mb-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-blue-600">Unread Notifications</p>
            <p className="text-2xl font-bold text-blue-900">{notificationData.unread}</p>
          </div>
          <Bell className="w-8 h-8 text-blue-500" />
        </div>
      </div>

      <div className="flex-1 overflow-auto space-y-4">
        {notificationData.alerts.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-red-700 mb-2">Critical Alerts</h4>
            <div className="space-y-2">
              {notificationData.alerts.map((alert: any) => (
                <div key={alert.id} className="bg-red-50 border border-red-200 p-3 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h5 className="text-sm font-medium text-red-900">{alert.title}</h5>
                      <p className="text-sm text-red-700 mt-1">{alert.message}</p>
                    </div>
                    <AlertTriangle className="w-5 h-5 text-red-500 ml-2" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Notifications</h4>
          <div className="space-y-2">
            {notificationData.recent.map((notification: any) => (
              <div key={notification.id} className={`p-3 rounded-lg border ${
                notification.read ? 'bg-gray-50' : 'bg-white border-blue-200'
              }`}>
                <div className="flex items-start space-x-3">
                  {getNotificationIcon(notification.type)}
                  <div className="flex-1 min-w-0">
                    <h5 className="text-sm font-medium text-gray-900">{notification.title}</h5>
                    <p className="text-sm text-gray-600 mt-1">{notification.message}</p>
                    <p className="text-xs text-gray-500 mt-2">
                      {formatTimeAgo(notification.timestamp)}
                    </p>
                  </div>
                  {!notification.read && (
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}