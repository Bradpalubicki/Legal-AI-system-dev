import React, { useEffect, useState } from 'react'
import { MessageSquare, Clock, CheckCircle, AlertTriangle, User } from 'lucide-react'

interface QAWidgetProps {
  filters: any
  realTimeData: any
  isSelected: boolean
}

export const QAWidget: React.FC<QAWidgetProps> = ({
  filters,
  realTimeData,
  isSelected
}) => {
  const [qaData, setQaData] = useState({
    pendingResponses: 0,
    totalSessions: 0,
    activeUsers: 0,
    recentQuestions: []
  })

  useEffect(() => {
    if (realTimeData?.qa) {
      setQaData(realTimeData.qa)
    }
  }, [realTimeData])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="w-4 h-4 text-yellow-500" />
      case 'answered': return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'escalated': return <AlertTriangle className="w-4 h-4 text-red-500" />
      default: return <MessageSquare className="w-4 h-4 text-gray-500" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
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
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-yellow-50 p-2 rounded-lg">
          <div className="text-xs text-yellow-600">Pending</div>
          <div className="text-lg font-bold text-yellow-900">{qaData.pendingResponses}</div>
        </div>
        <div className="bg-blue-50 p-2 rounded-lg">
          <div className="text-xs text-blue-600">Active</div>
          <div className="text-lg font-bold text-blue-900">{qaData.activeUsers}</div>
        </div>
        <div className="bg-green-50 p-2 rounded-lg">
          <div className="text-xs text-green-600">Total</div>
          <div className="text-lg font-bold text-green-900">{qaData.totalSessions}</div>
        </div>
      </div>

      {/* Recent Questions */}
      <div className="flex-1 overflow-auto">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Questions</h4>

        {qaData.recentQuestions.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No recent questions</p>
          </div>
        ) : (
          <div className="space-y-2">
            {qaData.recentQuestions.map((item: any) => (
              <div key={item.id} className="bg-white p-3 rounded-lg border shadow-sm">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(item.status)}
                    <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(item.priority)}`}>
                      {item.priority}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {formatTimeAgo(item.timestamp)}
                  </span>
                </div>

                <p className="text-sm text-gray-900 line-clamp-3">
                  {item.question}
                </p>

                <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
                  <span className={`text-xs font-medium ${
                    item.status === 'pending' ? 'text-yellow-600' :
                    item.status === 'answered' ? 'text-green-600' :
                    'text-red-600'
                  }`}>
                    {item.status.toUpperCase()}
                  </span>

                  {item.status === 'pending' && (
                    <button className="text-xs text-blue-600 hover:text-blue-800">
                      Answer Now
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      {isSelected && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            <button className="flex-1 px-3 py-2 text-xs bg-blue-500 text-white rounded hover:bg-blue-600">
              Ask Question
            </button>
            <button className="flex-1 px-3 py-2 text-xs bg-green-500 text-white rounded hover:bg-green-600">
              View All Q&As
            </button>
          </div>
        </div>
      )}
    </div>
  )
}