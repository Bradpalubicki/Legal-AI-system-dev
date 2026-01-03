import React, { useEffect, useState } from 'react'
import { CheckSquare, Clock, User, AlertCircle, Calendar } from 'lucide-react'

interface ActionItemsWidgetProps {
  filters: any
  realTimeData: any
  isSelected: boolean
}

export const ActionItemsWidget: React.FC<ActionItemsWidgetProps> = ({
  filters,
  realTimeData,
  isSelected
}) => {
  const [actionData, setActionData] = useState({
    pending: [],
    completed: 0,
    overdue: 0
  })

  useEffect(() => {
    if (realTimeData?.actions) {
      setActionData(realTimeData.actions)
    }
  }, [realTimeData])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'in-progress': return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'completed': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      case 'low': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const formatDueDate = (dueDate: string) => {
    const date = new Date(dueDate)
    const now = new Date()
    const diffInDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))

    if (diffInDays < 0) return 'Overdue'
    if (diffInDays === 0) return 'Due Today'
    if (diffInDays === 1) return 'Due Tomorrow'
    return `Due in ${diffInDays} days`
  }

  return (
    <div className="h-full flex flex-col">
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-blue-600">Pending</p>
              <p className="text-xl font-bold text-blue-900">{actionData.pending.length}</p>
            </div>
            <CheckSquare className="w-6 h-6 text-blue-500" />
          </div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-green-600">Completed</p>
              <p className="text-xl font-bold text-green-900">{actionData.completed}</p>
            </div>
            <CheckSquare className="w-6 h-6 text-green-500" />
          </div>
        </div>
        <div className="bg-red-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-red-600">Overdue</p>
              <p className="text-xl font-bold text-red-900">{actionData.overdue}</p>
            </div>
            <AlertCircle className="w-6 h-6 text-red-500" />
          </div>
        </div>
      </div>

      {/* Action Items List */}
      <div className="flex-1 overflow-auto">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Pending Action Items</h4>

        {actionData.pending.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckSquare className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No pending action items</p>
          </div>
        ) : (
          <div className="space-y-2">
            {actionData.pending.map((item: any) => (
              <div key={item.id} className="bg-white p-3 rounded-lg border shadow-sm">
                <div className="flex items-start justify-between mb-2">
                  <h5 className="text-sm font-medium text-gray-900 line-clamp-1">
                    {item.title}
                  </h5>
                  <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(item.priority)}`}>
                    {item.priority}
                  </span>
                </div>

                <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                  {item.description}
                </p>

                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <User className="w-3 h-3 text-gray-400" />
                    <span className="text-gray-600">{item.assignee}</span>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Calendar className="w-3 h-3 text-gray-400" />
                    <span className={`${
                      formatDueDate(item.dueDate).includes('Overdue') ? 'text-red-600' :
                      formatDueDate(item.dueDate).includes('Today') ? 'text-yellow-600' :
                      'text-gray-600'
                    }`}>
                      {formatDueDate(item.dueDate)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between mt-3 pt-2 border-t border-gray-100">
                  <span className={`px-2 py-1 text-xs rounded-full border ${getStatusColor(item.status)}`}>
                    {item.status.replace('-', ' ')}
                  </span>

                  <button className="text-xs text-blue-600 hover:text-blue-800">
                    Mark Complete
                  </button>
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
              Add Action
            </button>
            <button className="flex-1 px-3 py-2 text-xs bg-green-500 text-white rounded hover:bg-green-600">
              View All
            </button>
          </div>
        </div>
      )}
    </div>
  )
}