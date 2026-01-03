import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import InteractiveDashboard from '../../../src/components/analytics/InteractiveDashboard'
import { mockAnalyticsData } from '../../utils/test-utils'
import { WidgetType } from '../../../src/types/analytics'

// Mock chart components
jest.mock('../../../src/components/charts/LineChart', () => {
  return function MockLineChart({ data, onExport, config }: any) {
    return (
      <div data-testid="line-chart" data-title={config?.title}>
        Line Chart: {data.length} data points
        {onExport && <button onClick={() => onExport({ format: 'png' })}>Export</button>}
      </div>
    )
  }
})

jest.mock('../../../src/components/charts/BarChart', () => {
  return function MockBarChart({ data, onExport, config }: any) {
    return (
      <div data-testid="bar-chart" data-title={config?.title}>
        Bar Chart: {data.length} categories
        {onExport && <button onClick={() => onExport({ format: 'png' })}>Export</button>}
      </div>
    )
  }
})

jest.mock('../../../src/components/charts/MetricCard', () => {
  return function MockMetricCard({ metric, onClick, onExport }: any) {
    return (
      <div 
        data-testid="metric-card" 
        data-name={metric.name}
        onClick={onClick}
        role="button"
        tabIndex={0}
      >
        {metric.name}: {metric.value}
        {onExport && <button onClick={() => onExport({ format: 'png' })}>Export</button>}
      </div>
    )
  }
})

describe('InteractiveDashboard', () => {
  const mockWidgets = [
    {
      id: 'widget-1',
      type: WidgetType.LINE_CHART,
      title: 'Document Trends',
      description: 'Documents uploaded over time',
      dataSource: 'documents',
      config: { title: 'Document Trends' },
      position: { x: 0, y: 0, width: 2, height: 1 }
    },
    {
      id: 'widget-2',
      type: WidgetType.BAR_CHART,
      title: 'Document Types',
      description: 'Distribution of document types',
      dataSource: 'document-types',
      config: { title: 'Document Types' },
      position: { x: 2, y: 0, width: 1, height: 1 }
    },
    {
      id: 'widget-3',
      type: WidgetType.METRIC_CARD,
      title: 'Total Documents',
      description: 'Total number of documents',
      dataSource: 'total-documents',
      config: { title: 'Total Documents' },
      position: { x: 0, y: 1, width: 1, height: 1 }
    }
  ]

  const defaultProps = {
    widgets: mockWidgets,
    onWidgetInteraction: jest.fn(),
    onExport: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders dashboard with all widgets', () => {
      render(<InteractiveDashboard {...defaultProps} />)
      
      expect(screen.getByText('Legal Analytics Dashboard')).toBeInTheDocument()
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
      expect(screen.getByTestId('metric-card')).toBeInTheDocument()
    })

    it('renders widgets with correct data', () => {
      render(<InteractiveDashboard {...defaultProps} />)
      
      const lineChart = screen.getByTestId('line-chart')
      expect(lineChart).toHaveAttribute('data-title', 'Document Trends')
      
      const barChart = screen.getByTestId('bar-chart')
      expect(barChart).toHaveAttribute('data-title', 'Document Types')
      
      const metricCard = screen.getByTestId('metric-card')
      expect(metricCard).toHaveAttribute('data-name', 'Total Documents')
    })

    it('shows empty state when no widgets provided', () => {
      render(<InteractiveDashboard {...defaultProps} widgets={[]} />)
      
      expect(screen.getByText('Legal Analytics Dashboard')).toBeInTheDocument()
      // Should not crash with empty widgets array
    })
  })

  describe('Widget Interactions', () => {
    it('handles widget click for drill-down', async () => {
      const user = userEvent.setup()
      const mockOnWidgetInteraction = jest.fn()
      
      render(
        <InteractiveDashboard 
          {...defaultProps} 
          onWidgetInteraction={mockOnWidgetInteraction}
        />
      )
      
      const metricCard = screen.getByTestId('metric-card')
      await user.click(metricCard)
      
      expect(mockOnWidgetInteraction).toHaveBeenCalledWith(
        'widget-3',
        expect.objectContaining({
          type: 'drilldown'
        })
      )
    })

    it('shows drill-down view with breadcrumbs', async () => {
      const user = userEvent.setup()
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      // Click on a widget to trigger drill-down
      const metricCard = screen.getByTestId('metric-card')
      await user.click(metricCard)
      
      // Should show drill-down header
      expect(screen.getByText('Back to Dashboard')).toBeInTheDocument()
      expect(screen.getByText('Overview')).toBeInTheDocument()
    })

    it('navigates back from drill-down view', async () => {
      const user = userEvent.setup()
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      // Enter drill-down
      const metricCard = screen.getByTestId('metric-card')
      await user.click(metricCard)
      
      // Navigate back
      const backButton = screen.getByText('Back to Dashboard')
      await user.click(backButton)
      
      // Should return to main dashboard
      expect(screen.getByText('Legal Analytics Dashboard')).toBeInTheDocument()
      expect(screen.queryByText('Back to Dashboard')).not.toBeInTheDocument()
    })

    it('handles breadcrumb navigation', async () => {
      const user = userEvent.setup()
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      // Enter drill-down
      const metricCard = screen.getByTestId('metric-card')
      await user.click(metricCard)
      
      // Click on breadcrumb
      const overviewBreadcrumb = screen.getByText('Overview')
      await user.click(overviewBreadcrumb)
      
      // Should return to main view
      expect(screen.getByText('Legal Analytics Dashboard')).toBeInTheDocument()
    })
  })

  describe('Filter Mode', () => {
    it('toggles filter mode', async () => {
      const user = userEvent.setup()
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      const filterButton = screen.getByTitle('Filter mode')
      await user.click(filterButton)
      
      expect(filterButton).toHaveClass('bg-blue-100')
    })

    it('allows widget selection in filter mode', async () => {
      const user = userEvent.setup()
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      // Enable filter mode
      const filterButton = screen.getByTitle('Filter mode')
      await user.click(filterButton)
      
      // Click on a widget
      const metricCard = screen.getByTestId('metric-card')
      await user.click(metricCard)
      
      // Should show selection count
      expect(screen.getByText('1 widget selected')).toBeInTheDocument()
    })

    it('shows selected widget count', async () => {
      const user = userEvent.setup()
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      // Enable filter mode
      const filterButton = screen.getByTitle('Filter mode')
      await user.click(filterButton)
      
      // Select multiple widgets
      const lineChart = screen.getByTestId('line-chart')
      const barChart = screen.getByTestId('bar-chart')
      
      await user.click(lineChart)
      await user.click(barChart)
      
      expect(screen.getByText('2 widgets selected')).toBeInTheDocument()
    })

    it('resets widget selection', async () => {
      const user = userEvent.setup()
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      // Enable filter mode and select widgets
      const filterButton = screen.getByTitle('Filter mode')
      await user.click(filterButton)
      
      const metricCard = screen.getByTestId('metric-card')
      await user.click(metricCard)
      
      // Reset selection
      const resetButton = screen.getByTitle('Reset view')
      await user.click(resetButton)
      
      expect(screen.queryByText(/widget selected/)).not.toBeInTheDocument()
    })
  })

  describe('Export Functionality', () => {
    it('handles widget export', async () => {
      const user = userEvent.setup()
      const mockOnExport = jest.fn()
      
      render(<InteractiveDashboard {...defaultProps} onExport={mockOnExport} />)
      
      const exportButton = screen.getAllByText('Export')[0]
      await user.click(exportButton)
      
      expect(mockOnExport).toHaveBeenCalledWith({ format: 'png' })
    })

    it('exports multiple selected widgets', async () => {
      const user = userEvent.setup()
      const mockOnExport = jest.fn()
      
      render(<InteractiveDashboard {...defaultProps} onExport={mockOnExport} />)
      
      // Enable filter mode and select widgets
      const filterButton = screen.getByTitle('Filter mode')
      await user.click(filterButton)
      
      const lineChart = screen.getByTestId('line-chart')
      await user.click(lineChart)
      
      // Export selected widget
      const exportButton = screen.getAllByText('Export')[0]
      await user.click(exportButton)
      
      expect(mockOnExport).toHaveBeenCalled()
    })
  })

  describe('Responsive Layout', () => {
    it('adapts to different screen sizes', () => {
      // Mock window size
      Object.defineProperty(window, 'innerWidth', { value: 768 })
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      const dashboard = screen.getByText('Legal Analytics Dashboard').closest('div')
      expect(dashboard).toHaveClass('grid')
    })

    it('handles widget positioning on mobile', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', { value: 375 })
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      // Should render widgets in mobile-friendly layout
      const widgets = screen.getAllByTestId(/chart|card/)
      expect(widgets).toHaveLength(mockWidgets.length)
    })
  })

  describe('Performance', () => {
    it('virtualizes large number of widgets', () => {
      const manyWidgets = Array.from({ length: 50 }, (_, i) => ({
        ...mockWidgets[0],
        id: `widget-${i}`,
        title: `Widget ${i}`
      }))
      
      render(<InteractiveDashboard {...defaultProps} widgets={manyWidgets} />)
      
      // Should not render all widgets immediately (virtualization)
      const renderedWidgets = screen.getAllByTestId('line-chart')
      expect(renderedWidgets.length).toBeLessThan(50)
    })

    it('debounces filter mode interactions', async () => {
      const user = userEvent.setup()
      const mockOnWidgetInteraction = jest.fn()
      
      render(
        <InteractiveDashboard 
          {...defaultProps} 
          onWidgetInteraction={mockOnWidgetInteraction}
        />
      )
      
      const filterButton = screen.getByTitle('Filter mode')
      
      // Rapid clicking
      await user.click(filterButton)
      await user.click(filterButton)
      await user.click(filterButton)
      
      // Should debounce the interactions
      await waitFor(() => {
        expect(mockOnWidgetInteraction).toHaveBeenCalledTimes(1)
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<InteractiveDashboard {...defaultProps} />)
      
      const dashboard = screen.getByRole('main') || screen.getByText('Legal Analytics Dashboard').closest('[role]')
      expect(dashboard).toBeInTheDocument()
      
      const filterButton = screen.getByTitle('Filter mode')
      expect(filterButton).toHaveAttribute('aria-label')
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      // Tab through interactive elements
      await user.tab()
      expect(document.activeElement).toHaveAttribute('title', 'Filter mode')
      
      await user.tab()
      expect(document.activeElement).toHaveAttribute('title', 'Reset view')
    })

    it('announces state changes to screen readers', async () => {
      const user = userEvent.setup()
      
      render(<InteractiveDashboard {...defaultProps} />)
      
      // Enable filter mode
      const filterButton = screen.getByTitle('Filter mode')
      await user.click(filterButton)
      
      // Should announce filter mode activation
      const announcement = screen.getByRole('status') || screen.getByLabelText(/filter mode/i)
      expect(announcement).toBeInTheDocument()
    })

    it('provides alternative text for charts', () => {
      render(<InteractiveDashboard {...defaultProps} />)
      
      const lineChart = screen.getByTestId('line-chart')
      expect(lineChart).toHaveAttribute('data-title')
      
      const barChart = screen.getByTestId('bar-chart')
      expect(barChart).toHaveAttribute('data-title')
    })
  })

  describe('Error Handling', () => {
    it('handles widget rendering errors gracefully', () => {
      // Mock console.error to avoid test output pollution
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      
      const widgetWithError = {
        ...mockWidgets[0],
        type: 'invalid-type' as any
      }
      
      render(<InteractiveDashboard {...defaultProps} widgets={[widgetWithError]} />)
      
      // Should show error placeholder instead of crashing
      expect(screen.getByText(/not implemented/i)).toBeInTheDocument()
      
      consoleSpy.mockRestore()
    })

    it('shows error message when widget interaction fails', async () => {
      const user = userEvent.setup()
      const mockOnWidgetInteraction = jest.fn().mockRejectedValue(new Error('Interaction failed'))
      
      render(
        <InteractiveDashboard 
          {...defaultProps} 
          onWidgetInteraction={mockOnWidgetInteraction}
        />
      )
      
      const metricCard = screen.getByTestId('metric-card')
      await user.click(metricCard)
      
      await waitFor(() => {
        expect(screen.getByText(/interaction failed/i)).toBeInTheDocument()
      })
    })

    it('recovers from export errors', async () => {
      const user = userEvent.setup()
      const mockOnExport = jest.fn().mockRejectedValue(new Error('Export failed'))
      
      render(<InteractiveDashboard {...defaultProps} onExport={mockOnExport} />)
      
      const exportButton = screen.getAllByText('Export')[0]
      await user.click(exportButton)
      
      await waitFor(() => {
        expect(screen.getByText(/export failed/i)).toBeInTheDocument()
      })
    })
  })

  describe('Real-time Updates', () => {
    it('updates widget data in real-time', async () => {
      const { rerender } = render(<InteractiveDashboard {...defaultProps} />)
      
      // Initial render
      expect(screen.getByText('Line Chart: 12 data points')).toBeInTheDocument()
      
      // Update with new data
      const updatedWidgets = mockWidgets.map(widget => ({
        ...widget,
        data: widget.type === WidgetType.LINE_CHART ? 
          Array.from({ length: 15 }, (_, i) => ({ date: `2023-${i+1}`, value: Math.random() * 100 })) :
          widget.data
      }))
      
      rerender(<InteractiveDashboard {...defaultProps} widgets={updatedWidgets} />)
      
      // Should reflect updated data
      await waitFor(() => {
        expect(screen.getByText('Line Chart: 15 data points')).toBeInTheDocument()
      })
    })

    it('handles widget configuration changes', () => {
      const { rerender } = render(<InteractiveDashboard {...defaultProps} />)
      
      const updatedWidgets = mockWidgets.map(widget => ({
        ...widget,
        config: { ...widget.config, title: `Updated ${widget.title}` }
      }))
      
      rerender(<InteractiveDashboard {...defaultProps} widgets={updatedWidgets} />)
      
      expect(screen.getByText('Updated Document Trends')).toBeInTheDocument()
    })
  })
})