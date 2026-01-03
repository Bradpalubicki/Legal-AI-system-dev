'use client'

import { ResponsiveLine } from '@nivo/line'
import BaseChart from './BaseChart'
import { TimeSeriesData, LineChartConfig, ExportConfig } from '../../types/analytics'

interface LineChartProps {
  data: TimeSeriesData[]
  config?: LineChartConfig
  loading?: boolean
  error?: string
  onExport?: (config: ExportConfig) => void
  className?: string
  height?: number
}

export default function LineChart({
  data,
  config = {},
  loading = false,
  error,
  onExport,
  className = '',
  height = 400
}: LineChartProps) {
  // Transform data for Nivo
  const chartData = [{
    id: 'series',
    data: data.map(item => ({
      x: item.date,
      y: item.value
    }))
  }]

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

  const colors = config.colors || ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

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
        <ResponsiveLine
          data={chartData}
          margin={config.margin || { top: 20, right: 30, bottom: 50, left: 60 }}
          xScale={{ type: 'point' }}
          yScale={{
            type: 'linear',
            min: 'auto',
            max: 'auto',
            stacked: config.stacked || false,
            reverse: false
          }}
          curve={config.curve || 'cardinal'}
          axisTop={null}
          axisRight={null}
          axisBottom={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: -45,
            legend: config.xAxisLabel,
            legendOffset: 40,
            legendPosition: 'middle'
          }}
          axisLeft={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: config.yAxisLabel,
            legendOffset: -50,
            legendPosition: 'middle'
          }}
          pointSize={config.showPoints === false ? 0 : 6}
          pointColor={{ theme: 'background' }}
          pointBorderWidth={2}
          pointBorderColor={{ from: 'serieColor' }}
          pointLabelYOffset={-12}
          enableArea={config.showArea || false}
          areaOpacity={0.1}
          useMesh={true}
          colors={colors}
          theme={theme}
          animate={config.animate !== false}
          motionConfig="gentle"
          legends={config.showLegend === false ? [] : [
            {
              anchor: 'bottom-right',
              direction: 'column',
              justify: false,
              translateX: 100,
              translateY: 0,
              itemsSpacing: 0,
              itemDirection: 'left-to-right',
              itemWidth: 80,
              itemHeight: 20,
              itemOpacity: 0.75,
              symbolSize: 12,
              symbolShape: 'circle',
              symbolBorderColor: 'rgba(0, 0, 0, .5)',
              effects: [
                {
                  on: 'hover',
                  style: {
                    itemBackground: 'rgba(0, 0, 0, .03)',
                    itemOpacity: 1
                  }
                }
              ]
            }
          ]}
          tooltip={({ point }) => (
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
              <div className="text-sm font-medium text-gray-900">
                {point.data.xFormatted}
              </div>
              <div className="text-sm text-gray-600">
                Value: <span className="font-medium">{point.data.yFormatted}</span>
              </div>
            </div>
          )}
        />
      </div>
    </BaseChart>
  )
}

// Specialized line charts for legal analytics
export function CostTrendChart({ data, ...props }: Omit<LineChartProps, 'data'> & { data: TimeSeriesData[] }) {
  return (
    <LineChart
      data={data}
      config={{
        title: 'Cost Trends',
        yAxisLabel: 'Cost ($)',
        xAxisLabel: 'Time',
        colors: ['#ef4444'],
        showArea: true,
        ...props.config
      }}
      {...props}
    />
  )
}

export function SearchVolumeChart({ data, ...props }: Omit<LineChartProps, 'data'> & { data: TimeSeriesData[] }) {
  return (
    <LineChart
      data={data}
      config={{
        title: 'Search Volume Over Time',
        yAxisLabel: 'Number of Searches',
        xAxisLabel: 'Time',
        colors: ['#3b82f6'],
        showPoints: true,
        ...props.config
      }}
      {...props}
    />
  )
}

export function UserActivityChart({ data, ...props }: Omit<LineChartProps, 'data'> & { data: TimeSeriesData[] }) {
  return (
    <LineChart
      data={data}
      config={{
        title: 'User Activity',
        yAxisLabel: 'Active Users',
        xAxisLabel: 'Time',
        colors: ['#10b981'],
        curve: 'monotone',
        ...props.config
      }}
      {...props}
    />
  )
}