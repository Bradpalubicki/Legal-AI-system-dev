import React, { useEffect, useState } from 'react'
import { Shield, TrendingUp, AlertTriangle } from 'lucide-react'

interface DefenseStrategyWidgetProps {
  filters: any
  realTimeData: any
  isSelected: boolean
}

export const DefenseStrategyWidget: React.FC<DefenseStrategyWidgetProps> = ({
  filters,
  realTimeData,
  isSelected
}) => {
  const [strategyData, setStrategyData] = useState({
    availableStrategies: 0,
    recommendations: [],
    riskAssessments: []
  })

  useEffect(() => {
    if (realTimeData?.defense) {
      setStrategyData(realTimeData.defense)
    }
  }, [realTimeData])

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-800 bg-red-100 border-red-200'
      case 'high': return 'text-red-700 bg-red-50 border-red-200'
      case 'medium': return 'text-yellow-700 bg-yellow-50 border-yellow-200'
      case 'low': return 'text-green-700 bg-green-50 border-green-200'
      default: return 'text-gray-700 bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="h-full flex flex-col">
      <div className="bg-blue-50 p-3 rounded-lg mb-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-blue-600">Available Strategies</p>
            <p className="text-2xl font-bold text-blue-900">{strategyData.availableStrategies}</p>
          </div>
          <Shield className="w-8 h-8 text-blue-500" />
        </div>
      </div>

      <div className="flex-1 overflow-auto space-y-4">
        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Top Recommendations</h4>
          <div className="space-y-2">
            {strategyData.recommendations.map((rec: any) => (
              <div key={rec.id} className="bg-white p-3 rounded-lg border">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-green-600">Strategy #{rec.priority}</span>
                  <span className="text-xs text-gray-500">{Math.round(rec.confidence * 100)}% confidence</span>
                </div>
                <p className="text-sm text-gray-900">{rec.strategy}</p>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-medium text-gray-700 mb-2">Risk Assessment</h4>
          <div className="space-y-2">
            {strategyData.riskAssessments.map((risk: any) => (
              <div key={risk.id} className="bg-white p-3 rounded-lg border">
                <div className="flex items-center justify-between mb-2">
                  <span className={`px-2 py-1 text-xs rounded-full border ${getRiskColor(risk.level)}`}>
                    {risk.level.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-900 mb-1">{risk.risk}</p>
                <p className="text-xs text-gray-600">{risk.mitigation}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}