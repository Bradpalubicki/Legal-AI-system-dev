import React, { useEffect, useState } from 'react'
import { TrendingUp, Users, Clock, Briefcase } from 'lucide-react'

interface AttorneyMetricsWidgetProps {
  filters: any
  realTimeData: any
  isSelected: boolean
}

export const AttorneyMetricsWidget: React.FC<AttorneyMetricsWidgetProps> = ({
  filters,
  realTimeData,
  isSelected
}) => {
  const [metricsData, setMetricsData] = useState({
    activeUsers: 0,
    productivityScore: 0,
    billableHours: 0,
    caseLoad: 0
  })

  useEffect(() => {
    if (realTimeData?.attorney) {
      setMetricsData(realTimeData.attorney)
    }
  }, [realTimeData])

  return (
    <div className="h-full flex flex-col">
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-green-600">Active Users</p>
              <p className="text-xl font-bold text-green-900">{metricsData.activeUsers}</p>
            </div>
            <Users className="w-6 h-6 text-green-500" />
          </div>
        </div>
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-blue-600">Productivity</p>
              <p className="text-xl font-bold text-blue-900">{metricsData.productivityScore}%</p>
            </div>
            <TrendingUp className="w-6 h-6 text-blue-500" />
          </div>
        </div>
        <div className="bg-purple-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-purple-600">Billable Hours</p>
              <p className="text-xl font-bold text-purple-900">{metricsData.billableHours}h</p>
            </div>
            <Clock className="w-6 h-6 text-purple-500" />
          </div>
        </div>
        <div className="bg-yellow-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-yellow-600">Case Load</p>
              <p className="text-xl font-bold text-yellow-900">{metricsData.caseLoad}</p>
            </div>
            <Briefcase className="w-6 h-6 text-yellow-500" />
          </div>
        </div>
      </div>

      <div className="flex-1 bg-gray-50 rounded-lg p-3">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Performance Overview</h4>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span>Productivity Score</span>
              <span>{metricsData.productivityScore}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{ width: `${metricsData.productivityScore}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}