import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { Card, CardHeader, CardBody } from '../ui'
import { ResourceType } from '../../types/cost'

interface ResourceUsageProps {
  data: Array<{
    resource: ResourceType
    cost: number
    percentage: number
  }>
}

const COLORS = [
  '#3b82f6', // Blue
  '#10b981', // Green  
  '#f59e0b', // Amber
  '#ef4444', // Red
  '#8b5cf6', // Purple
  '#06b6d4', // Cyan
  '#84cc16', // Lime
  '#f97316'  // Orange
]

const RESOURCE_LABELS: Record<ResourceType, string> = {
  [ResourceType.WESTLAW]: 'Westlaw',
  [ResourceType.LEXISNEXIS]: 'LexisNexis',
  [ResourceType.BLOOMBERG_LAW]: 'Bloomberg Law',
  [ResourceType.COURTLISTENER]: 'CourtListener',
  [ResourceType.GOOGLE_SCHOLAR]: 'Google Scholar',
  [ResourceType.INTERNAL_AI]: 'Internal AI',
  [ResourceType.DOCUMENT_PROCESSING]: 'Document Processing',
  [ResourceType.STORAGE]: 'Storage'
}

export default function ResourceUsage({ data }: ResourceUsageProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value)
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900">
            {RESOURCE_LABELS[data.resource as ResourceType]}
          </p>
          <p className="text-sm text-gray-600">
            Cost: <span className="font-medium text-gray-900">{formatCurrency(data.cost)}</span>
          </p>
          <p className="text-sm text-gray-600">
            Share: <span className="font-medium text-gray-900">{data.percentage.toFixed(1)}%</span>
          </p>
        </div>
      )
    }
    return null
  }

  const CustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percentage }: any) => {
    if (percentage < 5) return null // Don't show labels for small slices
    
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize="12"
        fontWeight="medium"
      >
        {`${percentage.toFixed(0)}%`}
      </text>
    )
  }

  return (
    <Card>
      <CardHeader>
        <h3 className="text-lg font-medium text-gray-900">Resource Usage</h3>
      </CardHeader>
      <CardBody>
        <div className="flex flex-col lg:flex-row">
          {/* Chart */}
          <div className="h-64 lg:w-2/3">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={CustomLabel}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="cost"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Legend */}
          <div className="lg:w-1/3 lg:pl-6">
            <div className="space-y-2">
              {data.map((item, index) => (
                <div key={item.resource} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div 
                      className="w-3 h-3 rounded-full mr-2"
                      style={{ backgroundColor: COLORS[index % COLORS.length] }}
                    />
                    <span className="text-sm text-gray-700">
                      {RESOURCE_LABELS[item.resource]}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {formatCurrency(item.cost)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {item.percentage.toFixed(1)}%
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardBody>
    </Card>
  )
}