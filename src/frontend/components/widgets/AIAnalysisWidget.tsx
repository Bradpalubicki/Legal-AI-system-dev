import React, { useEffect, useState } from 'react'
import { Brain, TrendingUp, CheckCircle, Clock } from 'lucide-react'

interface AIAnalysisWidgetProps {
  filters: any
  realTimeData: any
  isSelected: boolean
}

export const AIAnalysisWidget: React.FC<AIAnalysisWidgetProps> = ({
  filters,
  realTimeData,
  isSelected
}) => {
  const [analysisData, setAnalysisData] = useState({
    inProgress: 0,
    completed: 0,
    confidence: 0,
    insights: []
  })

  useEffect(() => {
    if (realTimeData?.analysis) {
      setAnalysisData(realTimeData.analysis)
    }
  }, [realTimeData])

  return (
    <div className="h-full flex flex-col">
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-blue-600">In Progress</p>
              <p className="text-xl font-bold text-blue-900">{analysisData.inProgress}</p>
            </div>
            <Clock className="w-6 h-6 text-blue-500" />
          </div>
        </div>
        <div className="bg-green-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-green-600">Completed</p>
              <p className="text-xl font-bold text-green-900">{analysisData.completed}</p>
            </div>
            <CheckCircle className="w-6 h-6 text-green-500" />
          </div>
        </div>
      </div>

      <div className="bg-purple-50 p-3 rounded-lg mb-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-purple-600">Average Confidence</p>
            <p className="text-2xl font-bold text-purple-900">{analysisData.confidence}%</p>
          </div>
          <Brain className="w-8 h-8 text-purple-500" />
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Recent Insights</h4>
        <div className="space-y-2">
          {analysisData.insights.map((insight: any) => (
            <div key={insight.id} className="bg-white p-3 rounded-lg border">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-blue-600">{insight.type}</span>
                <span className="text-xs text-gray-500">{Math.round(insight.confidence * 100)}%</span>
              </div>
              <p className="text-sm text-gray-900">{insight.summary}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}