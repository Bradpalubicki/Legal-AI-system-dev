'use client'

import { ResponsiveHeatMap } from '@nivo/heatmap'
import BaseChart from './BaseChart'
import { HeatMapData, HeatMapConfig, ExportConfig } from '../../types/analytics'

interface HeatMapProps {
  data: HeatMapData[]
  config?: HeatMapConfig
  loading?: boolean
  error?: string
  onExport?: (config: ExportConfig) => void
  className?: string
  height?: number
  onCellClick?: (cell: { id: string; value: number; xKey: string; yKey: string }) => void
}

export default function HeatMap({
  data,
  config = {},
  loading = false,
  error,
  onExport,
  className = '',
  height = 400,
  onCellClick
}: HeatMapProps) {
  // Transform data for Nivo
  const chartData = data.map(item => ({
    id: item.id,
    ...item.data
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

  // Get all unique keys from data
  const keys = Array.from(new Set(
    data.flatMap(item => Object.keys(item.data))
  )).sort()

  const colors = config.colorScheme || ['#f7fafc', '#edf2f7', '#e2e8f0', '#cbd5e0', '#a0aec0', '#718096', '#4a5568']

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
        <ResponsiveHeatMap
          data={chartData}
          keys={keys}
          indexBy="id"
          margin={config.margin || { top: 60, right: 90, bottom: 60, left: 90 }}
          cellOpacity={config.cellOpacity || 1}
          cellBorderColor={config.theme === 'dark' ? '#555555' : '#ffffff'}
          cellBorderWidth={config.cellBorderWidth || 2}
          axisTop={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: -90,
            legend: '',
            legendOffset: 36
          }}
          axisRight={null}
          axisBottom={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: -90,
            legend: config.xAxisLabel || '',
            legendPosition: 'middle',
            legendOffset: 36
          }}
          axisLeft={{
            tickSize: 5,
            tickPadding: 5,
            tickRotation: 0,
            legend: config.yAxisLabel || '',
            legendPosition: 'middle',
            legendOffset: -72
          }}
          colors={colors}
          theme={theme}
          animate={config.animate !== false}
          motionConfig="gentle"
          hoverTarget="cell"
          cellHoverOthersOpacity={0.25}
          onClick={({ cell }) => {
            onCellClick?.({
              id: cell.id as string,
              value: cell.value as number,
              xKey: cell.serieId as string,
              yKey: cell.id as string
            })
          }}
          tooltip={({ cell }) => (
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
              <div className="text-sm font-medium text-gray-900 mb-1">
                {cell.serieId} × {cell.id}
              </div>
              <div className="text-sm text-gray-600">
                Value: <span className="font-medium">{cell.formattedValue}</span>
              </div>
            </div>
          )}
          legends={config.showLegend === false ? [] : [
            {
              anchor: 'bottom',
              translateX: 0,
              translateY: 30,
              length: 400,
              thickness: 8,
              direction: 'row',
              tickPosition: 'after',
              tickSize: 3,
              tickSpacing: 4,
              tickOverlap: false,
              titleAlign: 'start',
              titleOffset: 4
            }
          ]}
        />
      </div>
    </BaseChart>
  )
}

// Specialized heatmaps for legal analytics
export function UsageActivityHeatMap({ data, ...props }: Omit<HeatMapProps, 'data'> & { data: HeatMapData[] }) {
  return (
    <HeatMap
      data={data}
      config={{
        title: 'Usage Activity Heatmap',
        xAxisLabel: 'Hour of Day',
        yAxisLabel: 'Day of Week',
        colorScheme: ['#f7fafc', '#4299e1', '#3182ce', '#2b77cb', '#2c5282'],
        ...props.config
      }}
      {...props}
    />
  )
}

export function JurisdictionCostHeatMap({ data, ...props }: Omit<HeatMapProps, 'data'> & { data: HeatMapData[] }) {
  return (
    <HeatMap
      data={data}
      config={{
        title: 'Cost by Jurisdiction & Case Type',
        xAxisLabel: 'Case Type',
        yAxisLabel: 'Jurisdiction',
        colorScheme: ['#f7fafc', '#f56565', '#e53e3e', '#c53030', '#9b2c2c'],
        ...props.config
      }}
      {...props}
    />
  )
}

export function DocumentAccessHeatMap({ data, ...props }: Omit<HeatMapProps, 'data'> & { data: HeatMapData[] }) {
  return (
    <HeatMap
      data={data}
      config={{
        title: 'Document Access Patterns',
        xAxisLabel: 'Document Type',
        yAxisLabel: 'User Role',
        colorScheme: ['#f0fff4', '#9ae6b4', '#68d391', '#48bb78', '#38a169'],
        ...props.config
      }}
      {...props}
    />
  )
}