'use client'

import { useState, useEffect } from 'react'
import { Layout } from '../../components/layout'
import CostOverview from '../../components/dashboard/CostOverview'
import CostChart from '../../components/dashboard/CostChart'
import ResourceUsage from '../../components/dashboard/ResourceUsage'
import { Card, CardHeader, CardBody, Button } from '../../components/ui'
import type { DashboardData } from '../../types/cost'
import { ResourceType } from '../../types/cost'

// Mock data - in real app, this would come from API
const mockDashboardData: DashboardData = {
  totalCost: 25420.50,
  monthlySpend: 3240.75,
  budgetUtilization: 67.8,
  costTrends: [
    { period: 'Jan', amount: 2850, change: 0, changePercentage: 0 },
    { period: 'Feb', amount: 3100, change: 250, changePercentage: 8.8 },
    { period: 'Mar', amount: 3240, change: 140, changePercentage: 4.5 },
    { period: 'Apr', amount: 2980, change: -260, changePercentage: -8.0 },
    { period: 'May', amount: 3350, change: 370, changePercentage: 12.4 },
    { period: 'Jun', amount: 3240, change: -110, changePercentage: -3.3 }
  ],
  topResources: [
    { resource: ResourceType.WESTLAW, cost: 1540.25, percentage: 47.5 },
    { resource: ResourceType.LEXISNEXIS, cost: 980.50, percentage: 30.2 },
    { resource: ResourceType.BLOOMBERG_LAW, cost: 450.00, percentage: 13.9 },
    { resource: ResourceType.INTERNAL_AI, cost: 270.00, percentage: 8.3 }
  ],
  recentTransactions: [],
  alerts: [],
  projectedSpend: 3580.00
}

export default function CostsPage() {
  const [data, setData] = useState<DashboardData>(mockDashboardData)
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | '1y'>('30d')

  useEffect(() => {
    // In real app, fetch data based on timeRange
    // fetchCostData(timeRange).then(setData)
  }, [timeRange])

  return (
    <Layout title="Cost Management">
      <div className="space-y-6">
        {/* Header with Time Range Selector */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Cost Management</h1>
            <p className="text-gray-600">Monitor and optimize your legal research spending</p>
          </div>
          
          <div className="flex space-x-2">
            {(['7d', '30d', '90d', '1y'] as const).map((range) => (
              <Button
                key={range}
                variant={timeRange === range ? 'default' : 'secondary'}
                size="sm"
                onClick={() => setTimeRange(range)}
              >
                {range === '7d' ? '7 Days' : 
                 range === '30d' ? '30 Days' :
                 range === '90d' ? '90 Days' : '1 Year'}
              </Button>
            ))}
          </div>
        </div>

        {/* Cost Overview Cards */}
        <CostOverview data={data} />

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CostChart data={data.costTrends} />
          <ResourceUsage data={data.topResources} />
        </div>

        {/* Budget Alerts */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-medium text-gray-900">Budget Alerts</h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              <div className="flex items-center p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-yellow-500 rounded-full"></div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-yellow-800">
                    Westlaw Budget Alert
                  </p>
                  <p className="text-sm text-yellow-700">
                    You've used 80% of your monthly Westlaw budget ($2,000). Current spend: $1,540.25
                  </p>
                </div>
              </div>
              
              <div className="flex items-center p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex-shrink-0">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-red-800">
                    Projected Overspend
                  </p>
                  <p className="text-sm text-red-700">
                    Based on current usage, you may exceed your monthly budget by $580 this month.
                  </p>
                </div>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </CardHeader>
          <CardBody>
            <div className="space-y-3">
              {[
                { time: '2 hours ago', action: 'Westlaw search', cost: '$12.50', user: 'John Doe' },
                { time: '4 hours ago', action: 'Document download', cost: '$8.00', user: 'Jane Smith' },
                { time: '6 hours ago', action: 'LexisNexis research', cost: '$15.75', user: 'Mike Johnson' },
                { time: '1 day ago', action: 'AI document analysis', cost: '$5.25', user: 'Sarah Wilson' }
              ].map((activity, index) => (
                <div key={index} className="flex items-center justify-between py-3 border-b border-gray-100 last:border-b-0">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{activity.action}</p>
                    <p className="text-xs text-gray-500">{activity.user} • {activity.time}</p>
                  </div>
                  <div className="text-sm font-medium text-gray-900">{activity.cost}</div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>
    </Layout>
  )
}