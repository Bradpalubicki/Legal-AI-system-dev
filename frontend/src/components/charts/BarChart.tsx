'use client'

import { ResponsiveBar } from '@nivo/bar'
import BaseChart from './BaseChart'
import { CategoryData, BarChartConfig, ExportConfig } from '../../types/analytics'

interface BarChartProps {
  data: CategoryData[]
  config?: BarChartConfig
  loading?: boolean
  error?: string
  onExport?: (config: ExportConfig) => void
  className?: string
  height?: number
}

export default function BarChart({
  data,
  config = {},
  loading = false,
  error,
  onExport,
  className = '',
  height = 400
}: BarChartProps) {
  // Transform data for Nivo
  const chartData = data.map((item, index) => ({
    category: item.category,
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
    axis: {
      domain: {
        line: {
          stroke: config.theme === 'dark' ? '#555555' : '#e0e0e0',
          strokeWidth: 1
        }
      },
      legend: {
        text: {
          fontSize: 12,
          fill: config.theme === 'dark' ? '#ffffff' : '#333333'
        }
      },
      ticks: {
        line: {
          stroke: config.theme === 'dark' ? '#555555' : '#e0e0e0',
          strokeWidth: 1
        },
        text: {
          fontSize: 10,
          fill: config.theme === 'dark' ? '#cccccc' : '#666666'
        }
      }
    },
    grid: {
      line: {
        stroke: config.theme === 'dark' ? '#444444' : '#f0f0f0',
        strokeWidth: config.showGrid === false ? 0 : 1
      }
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

  const layout = config.orientation === 'horizontal' ? 'horizontal' : 'vertical'

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
        <ResponsiveBar
          data={chartData}
          keys={['value']}
          indexBy="category"
          margin={config.margin || { top: 20, right: 30, bottom: 50, left: 60 }}
          padding={0.3}
          layout={layout}
          valueScale={{ type: 'linear' }}
          indexScale={{ type: 'band', round: true }}
          colors={colors}
          theme={theme}
          animate={config.animate !== false}
          motionConfig="gentle"
          axisTop={null}
          axisRight={null}
          axisBottom={layout === 'vertical' ? {
            tickSize: 5,
            tickPadding: 5,
            tickRotation: -45,
            legend: config.xAxisLabel || 'Category',
            legendPosition: 'middle',
            legendOffset: 40
          } : null}
          axisLeft={layout === 'vertical' ? {
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: config.yAxisLabel || 'Value',
            legendPosition: 'middle',
            legendOffset: -50
          } : {
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: config.yAxisLabel || 'Category',
            legendPosition: 'middle',
            legendOffset: -50
          }}
          labelSkipWidth={12}
          labelSkipHeight={12}
          labelTextColor={{
            from: 'color',
            modifiers: [['darker', 1.6]]
          }}
          legends={config.showLegend === false ? [] : [
            {
              dataFrom: 'keys',
              anchor: 'bottom-right',
              direction: 'column',
              justify: false,
              translateX: 120,
              translateY: 0,
              itemsSpacing: 2,
              itemWidth: 100,
              itemHeight: 20,
              itemDirection: 'left-to-right',
              itemOpacity: 0.85,
              symbolSize: 20,
              effects: [
                {
                  on: 'hover',
                  style: {
                    itemOpacity: 1
                  }
                }
              ]
            }
          ]}
          tooltip={({ id, value, color, indexValue }) => (
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
              <div className="flex items-center space-x-2 mb-1">
                <div 
                  className="w-3 h-3 rounded"
                  style={{ backgroundColor: color }}
                />
                <div className="text-sm font-medium text-gray-900">
                  {indexValue}
                </div>
              </div>
              <div className="text-sm text-gray-600">
                Value: <span className="font-medium">{value.toLocaleString()}</span>
              </div>
            </div>
          )}
        />
      </div>
    </BaseChart>
  )
}

// Specialized bar charts for legal analytics
export function DatabaseUsageChart({ data, ...props }: Omit<BarChartProps, 'data'> & { data: CategoryData[] }) {
  return (
    <BarChart
      data={data}
      config={{
        title: 'Database Usage',
        yAxisLabel: 'Number of Searches',
        colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
        ...props.config
      }}
      {...props}
    />
  )
}

export function PracticeAreaChart({ data, ...props }: Omit<BarChartProps, 'data'> & { data: CategoryData[] }) {
  return (
    <BarChart
      data={data}
      config={{
        title: 'Search Volume by Practice Area',
        orientation: 'horizontal',
        yAxisLabel: 'Practice Area',
        colors: ['#8b5cf6', '#06b6d4', '#84cc16', '#f97316'],
        ...props.config
      }}
      {...props}
    />
  )
}

export function DocumentTypeChart({ data, ...props }: Omit<BarChartProps, 'data'> & { data: CategoryData[] }) {
  return (
    <BarChart
      data={data}
      config={{
        title: 'Documents by Type',
        yAxisLabel: 'Number of Documents',
        colors: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6'],
        ...props.config
      }}
      {...props}
    />
  )
}