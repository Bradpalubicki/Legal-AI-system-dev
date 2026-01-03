'use client'

import { ResponsivePie } from '@nivo/pie'
import BaseChart from './BaseChart'
import { CategoryData, PieChartConfig, ExportConfig } from '../../types/analytics'

interface PieChartProps {
  data: CategoryData[]
  config?: PieChartConfig
  loading?: boolean
  error?: string
  onExport?: (config: ExportConfig) => void
  className?: string
  height?: number
}

export default function PieChart({
  data,
  config = {},
  loading = false,
  error,
  onExport,
  className = '',
  height = 400
}: PieChartProps) {
  // Transform data for Nivo
  const chartData = data.map((item, index) => ({
    id: item.category,
    label: item.category,
    value: item.value,
    color: item.color || config.colors?.[index % (config.colors?.length || 1)]
  }))

  const theme = {
    background: 'transparent',
    text: {
      fontSize: 11,
      fill: config.theme === 'dark' ? '#ffffff' : '#333333',
      outlineWidth: 0,
      outlineColor: 'transparent'
    },
    tooltip: {
      container: {
        background: config.theme === 'dark' ? '#333333' : '#ffffff',
        color: config.theme === 'dark' ? '#ffffff' : '#333333',
        fontSize: 12,
        borderRadius: 4,
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
      }
    }
  }

  const colors = config.colors || ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316']

  // Calculate total for percentages
  const total = data.reduce((sum, item) => sum + item.value, 0)

  return (
    <BaseChart
      title={config.title}
      subtitle={config.subtitle}
      loading={loading}
      error={error}
      onExport={onExport}
      config={config}
      className={className}
    >
      <div style={{ height: height }}>
        <ResponsivePie
          data={chartData}
          margin={config.margin || { top: 40, right: 80, bottom: 40, left: 80 }}
          innerRadius={config.innerRadius || 0.5}
          padAngle={config.padAngle || 0.7}
          cornerRadius={config.cornerRadius || 3}
          activeOuterRadiusOffset={8}
          borderWidth={1}
          borderColor={{
            from: 'color',
            modifiers: [['darker', 0.2]]
          }}
          colors={colors}
          theme={theme}
          animate={config.animate !== false}
          motionConfig="gentle"
          startAngle={config.startAngle || 0}
          endAngle={config.endAngle || 360}
          sortByValue={config.sortByValue !== false}
          arcLinkLabelsSkipAngle={10}
          arcLinkLabelsTextColor={config.theme === 'dark' ? '#ffffff' : '#333333'}
          arcLinkLabelsThickness={2}
          arcLinkLabelsColor={{ from: 'color' }}
          arcLabelsSkipAngle={10}
          arcLabelsTextColor={{
            from: 'color',
            modifiers: [['darker', 2]]
          }}
          arcLabel={(d) => `${((d.value / total) * 100).toFixed(1)}%`}
          legends={config.showLegend === false ? [] : [
            {
              anchor: 'bottom',
              direction: 'row',
              justify: false,
              translateX: 0,
              translateY: 56,
              itemsSpacing: 0,
              itemWidth: 100,
              itemHeight: 18,
              itemTextColor: config.theme === 'dark' ? '#ffffff' : '#333333',
              itemDirection: 'left-to-right',
              itemOpacity: 1,
              symbolSize: 18,
              symbolShape: 'circle',
              effects: [
                {
                  on: 'hover',
                  style: {
                    itemTextColor: config.theme === 'dark' ? '#ffffff' : '#000000'
                  }
                }
              ]
            }
          ]}
          tooltip={({ datum }) => {
            const percentage = ((datum.value / total) * 100).toFixed(1)
            return (
              <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
                <div className="flex items-center space-x-2 mb-1">
                  <div 
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: datum.color }}
                  />
                  <div className="text-sm font-medium text-gray-900">
                    {datum.label}
                  </div>
                </div>
                <div className="text-sm text-gray-600">
                  Value: <span className="font-medium">{datum.value.toLocaleString()}</span>
                </div>
                <div className="text-sm text-gray-600">
                  Percentage: <span className="font-medium">{percentage}%</span>
                </div>
              </div>
            )
          }}
        />
      </div>
    </BaseChart>
  )
}

// Donut chart variant
export function DonutChart({ data, config = {}, ...props }: PieChartProps) {
  return (
    <PieChart
      data={data}
      config={{
        innerRadius: 0.6,
        ...config
      }}
      {...props}
    />
  )
}

// Specialized pie charts for legal analytics
export function CostDistributionChart({ data, ...props }: Omit<PieChartProps, 'data'> & { data: CategoryData[] }) {
  return (
    <PieChart
      data={data}
      config={{
        title: 'Cost Distribution by Source',
        innerRadius: 0.5,
        colors: ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6'],
        ...props.config
      }}
      {...props}
    />
  )
}

export function CaseStatusChart({ data, ...props }: Omit<PieChartProps, 'data'> & { data: CategoryData[] }) {
  return (
    <DonutChart
      data={data}
      config={{
        title: 'Cases by Status',
        colors: ['#10b981', '#f59e0b', '#ef4444', '#6b7280', '#8b5cf6'],
        ...props.config
      }}
      {...props}
    />
  )
}

export function DocumentCategoryChart({ data, ...props }: Omit<PieChartProps, 'data'> & { data: CategoryData[] }) {
  return (
    <PieChart
      data={data}
      config={{
        title: 'Documents by Category',
        innerRadius: 0.3,
        colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
        ...props.config
      }}
      {...props}
    />
  )
}