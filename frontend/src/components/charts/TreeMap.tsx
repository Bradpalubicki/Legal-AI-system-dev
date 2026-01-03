'use client'

import { ResponsiveTreeMap } from '@nivo/treemap'
import BaseChart from './BaseChart'
import { TreeMapData, TreeMapConfig, ExportConfig } from '../../types/analytics'

interface TreeMapProps {
  data: TreeMapData
  config?: TreeMapConfig
  loading?: boolean
  error?: string
  onExport?: (config: ExportConfig) => void
  className?: string
  height?: number
  onNodeClick?: (node: { id: string; value: number; data: any }) => void
}

export default function TreeMap({
  data,
  config = {},
  loading = false,
  error,
  onExport,
  className = '',
  height = 400,
  onNodeClick
}: TreeMapProps) {
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
        <ResponsiveTreeMap
          data={data}
          identity="name"
          value="value"
          valueFormat=".02s"
          margin={config.margin || { top: 10, right: 10, bottom: 10, left: 10 }}
          labelSkipSize={config.labelSkipSize || 12}
          labelTextColor={{
            from: 'color',
            modifiers: [['darker', 1.2]]
          }}
          parentLabelPosition="left"
          parentLabelTextColor={{
            from: 'color',
            modifiers: [['darker', 2]]
          }}
          borderColor={{
            from: 'color',
            modifiers: [['darker', 0.1]]
          }}
          colors={colors}
          theme={theme}
          animate={config.animate !== false}
          motionConfig="gentle"
          onClick={({ data: nodeData }) => {
            onNodeClick?.({
              id: nodeData.id as string,
              value: nodeData.value as number,
              data: nodeData
            })
          }}
          tooltip={({ node }) => (
            <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
              <div className="text-sm font-medium text-gray-900 mb-1">
                {node.id}
              </div>
              <div className="text-sm text-gray-600">
                Value: <span className="font-medium">{node.formattedValue}</span>
              </div>
              {node.data.percentage && (
                <div className="text-sm text-gray-600">
                  Percentage: <span className="font-medium">{node.data.percentage}%</span>
                </div>
              )}
            </div>
          )}
        />
      </div>
    </BaseChart>
  )
}

// Specialized treemaps for legal analytics
export function BudgetAllocationTreeMap({ data, ...props }: Omit<TreeMapProps, 'data'> & { data: TreeMapData }) {
  return (
    <TreeMap
      data={data}
      config={{
        title: 'Budget Allocation by Department',
        colors: ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6'],
        labelSkipSize: 8,
        ...props.config
      }}
      {...props}
    />
  )
}

export function CaseComplexityTreeMap({ data, ...props }: Omit<TreeMapProps, 'data'> & { data: TreeMapData }) {
  return (
    <TreeMap
      data={data}
      config={{
        title: 'Case Complexity Distribution',
        colors: ['#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
        labelSkipSize: 10,
        ...props.config
      }}
      {...props}
    />
  )
}

export function DocumentSizeTreeMap({ data, ...props }: Omit<TreeMapProps, 'data'> & { data: TreeMapData }) {
  return (
    <TreeMap
      data={data}
      config={{
        title: 'Document Repository Size',
        colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
        labelSkipSize: 6,
        ...props.config
      }}
      {...props}
    />
  )
}