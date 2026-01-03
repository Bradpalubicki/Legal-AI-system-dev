import React, { useEffect, useState } from 'react'
import { Clock, AlertTriangle, Calendar, CheckCircle } from 'lucide-react'

interface DeadlineWidgetProps {
  filters: any
  realTimeData: any
  isSelected: boolean
}

export const DeadlineWidget: React.FC<DeadlineWidgetProps> = ({
  filters,
  realTimeData,
  isSelected
}) => {
  const [deadlineData, setDeadlineData] = useState({
    upcoming: [],
    overdue: [],
    completed: 0
  })

  useEffect(() => {
    if (realTimeData?.deadlines) {
      setDeadlineData(realTimeData.deadlines)
    }
  }, [realTimeData])

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'text-red-800 bg-red-100 border-red-200'
      case 'high': return 'text-red-600 bg-red-50 border-red-200'
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low': return 'text-green-600 bg-green-50 border-green-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const formatDaysRemaining = (days: number) => {
    if (days === 0) return 'Today'
    if (days === 1) return 'Tomorrow'
    if (days < 0) return `${Math.abs(days)} days overdue`
    return `${days} days`
  }

  return (
    <div className="h-full flex flex-col">
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-yellow-50 p-2 rounded-lg">
          <div className="text-xs text-yellow-600">Upcoming</div>
          <div className="text-lg font-bold text-yellow-900">{deadlineData.upcoming.length}</div>
        </div>
        <div className="bg-red-50 p-2 rounded-lg">
          <div className="text-xs text-red-600">Overdue</div>
          <div className="text-lg font-bold text-red-900">{deadlineData.overdue.length}</div>
        </div>
        <div className="bg-green-50 p-2 rounded-lg">
          <div className="text-xs text-green-600">Completed</div>
          <div className="text-lg font-bold text-green-900">{deadlineData.completed}</div>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Upcoming Deadlines</h4>
        <div className="space-y-2">
          {deadlineData.upcoming.map((deadline: any) => (
            <div key={deadline.id} className="bg-white p-3 rounded-lg border">
              <div className="flex items-start justify-between mb-2">
                <h5 className="text-sm font-medium text-gray-900 line-clamp-1">
                  {deadline.title}
                </h5>
                <span className={`px-2 py-1 text-xs rounded-full border ${getPriorityColor(deadline.priority)}`}>
                  {deadline.priority}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-600 capitalize">{deadline.type}</span>
                <span className={`font-medium ${deadline.daysRemaining <= 1 ? 'text-red-600' : 'text-gray-600'}`}>
                  {formatDaysRemaining(deadline.daysRemaining)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}