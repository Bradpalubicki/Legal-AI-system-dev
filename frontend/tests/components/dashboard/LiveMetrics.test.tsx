/**
 * Unit Tests for LiveMetrics Component
 * 
 * Tests the real-time metrics display component including data fetching,
 * WebSocket connections, and metric visualization.
 */

import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import LiveMetrics from '@/components/dashboard/LiveMetrics'
import { useWebSocket } from '@/hooks/useWebSocket'

// Mock the WebSocket hook
jest.mock('@/hooks/useWebSocket')
const mockUseWebSocket = useWebSocket as jest.MockedFunction<typeof useWebSocket>

// Mock Chart.js and react-chartjs-2
jest.mock('react-chartjs-2', () => ({
  Line: ({ data, options, ...props }: any) => (
    <div data-testid="line-chart" {...props}>
      <div data-testid="chart-data">{JSON.stringify(data)}</div>
      <div data-testid="chart-options">{JSON.stringify(options)}</div>
    </div>
  ),
  Bar: ({ data, options, ...props }: any) => (
    <div data-testid="bar-chart" {...props}>
      <div data-testid="chart-data">{JSON.stringify(data)}</div>
      <div data-testid="chart-options">{JSON.stringify(options)}</div>
    </div>
  )
}))

// Mock API calls
const mockApiClient = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn()
}

jest.mock('@/lib/api', () => ({
  apiClient: mockApiClient
}))

// Create test wrapper with React Query
const createTestWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
    },
  })

  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('LiveMetrics Component', () => {
  let mockWebSocketReturn: any
  let TestWrapper: any

  beforeEach(() => {
    TestWrapper = createTestWrapper()
    
    // Default WebSocket mock
    mockWebSocketReturn = {
      isConnected: true,
      connectionState: 'OPEN',
      send: jest.fn(),
      close: jest.fn(),
      reconnect: jest.fn(),
      data: null,
      error: null
    }
    
    mockUseWebSocket.mockReturnValue(mockWebSocketReturn)

    // Default API mock responses
    mockApiClient.get.mockResolvedValue({
      data: {
        metrics: {
          activeUsers: 25,
          totalDocuments: 1547,
          processingQueue: 3,
          systemLoad: 0.65,
          responseTime: 150
        },
        timestamp: new Date().toISOString()
      }
    })

    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders the live metrics dashboard', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      expect(screen.getByText('Live Metrics')).toBeInTheDocument()
      expect(screen.getByText('System Performance')).toBeInTheDocument()
      
      await waitFor(() => {
        expect(screen.getByText('Active Users')).toBeInTheDocument()
        expect(screen.getByText('Total Documents')).toBeInTheDocument()
      })
    })

    it('displays loading state initially', () => {
      mockApiClient.get.mockImplementation(() => new Promise(() => {}))

      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      expect(screen.getByText('Loading metrics...')).toBeInTheDocument()
    })

    it('shows connection status indicator', () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      expect(screen.getByTestId('connection-status')).toBeInTheDocument()
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })

    it('displays disconnected state when WebSocket is not connected', () => {
      mockWebSocketReturn.isConnected = false
      mockWebSocketReturn.connectionState = 'CLOSED'

      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      expect(screen.getByText('Disconnected')).toBeInTheDocument()
      expect(screen.getByText('Reconnect')).toBeInTheDocument()
    })
  })

  describe('Metric Display', () => {
    const mockMetrics = {
      activeUsers: 42,
      totalDocuments: 2589,
      processingQueue: 7,
      systemLoad: 0.78,
      responseTime: 185,
      errorRate: 0.02,
      throughput: 145
    }

    beforeEach(() => {
      mockApiClient.get.mockResolvedValue({
        data: {
          metrics: mockMetrics,
          timestamp: new Date().toISOString()
        }
      })
    })

    it('displays current metric values', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('42')).toBeInTheDocument() // Active Users
        expect(screen.getByText('2,589')).toBeInTheDocument() // Total Documents
        expect(screen.getByText('7')).toBeInTheDocument() // Processing Queue
      })
    })

    it('formats large numbers correctly', async () => {
      mockApiClient.get.mockResolvedValue({
        data: {
          metrics: {
            ...mockMetrics,
            totalDocuments: 1500000
          },
          timestamp: new Date().toISOString()
        }
      })

      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('1.5M')).toBeInTheDocument()
      })
    })

    it('displays percentage values correctly', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('78%')).toBeInTheDocument() // System Load
        expect(screen.getByText('2%')).toBeInTheDocument() // Error Rate
      })
    })

    it('shows response time with units', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('185ms')).toBeInTheDocument()
      })
    })

    it('displays metric trends with indicators', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('trend-indicator')).toBeInTheDocument()
      })
    })
  })

  describe('Real-time Updates', () => {
    it('updates metrics when WebSocket data is received', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('25')).toBeInTheDocument() // Initial active users
      })

      // Simulate WebSocket message
      act(() => {
        mockWebSocketReturn.data = {
          type: 'METRICS_UPDATE',
          data: {
            activeUsers: 35,
            timestamp: new Date().toISOString()
          }
        }
      })

      await waitFor(() => {
        expect(screen.getByText('35')).toBeInTheDocument() // Updated active users
      })
    })

    it('handles real-time alerts', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      // Simulate alert WebSocket message
      act(() => {
        mockWebSocketReturn.data = {
          type: 'ALERT',
          data: {
            severity: 'warning',
            message: 'High system load detected',
            timestamp: new Date().toISOString()
          }
        }
      })

      await waitFor(() => {
        expect(screen.getByText('High system load detected')).toBeInTheDocument()
        expect(screen.getByTestId('alert-warning')).toBeInTheDocument()
      })
    })

    it('updates charts with new data points', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      })

      // Simulate new data point
      act(() => {
        mockWebSocketReturn.data = {
          type: 'METRICS_UPDATE',
          data: {
            systemLoad: 0.85,
            responseTime: 200,
            timestamp: new Date().toISOString()
          }
        }
      })

      await waitFor(() => {
        const chartData = screen.getByTestId('chart-data')
        expect(chartData.textContent).toContain('0.85')
      })
    })

    it('maintains historical data for charts', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      // Send multiple updates
      for (let i = 0; i < 5; i++) {
        act(() => {
          mockWebSocketReturn.data = {
            type: 'METRICS_UPDATE',
            data: {
              systemLoad: 0.6 + (i * 0.05),
              timestamp: new Date(Date.now() + i * 60000).toISOString()
            }
          }
        })
      }

      await waitFor(() => {
        const chartElement = screen.getByTestId('line-chart')
        expect(chartElement).toBeInTheDocument()
      })
    })
  })

  describe('Chart Rendering', () => {
    it('renders system load chart', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      })

      const chartData = JSON.parse(screen.getByTestId('chart-data').textContent!)
      expect(chartData.datasets[0].label).toBe('System Load')
    })

    it('renders response time chart', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        const charts = screen.getAllByTestId('line-chart')
        expect(charts.length).toBeGreaterThan(1)
      })
    })

    it('applies correct chart styling', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        const chartOptions = JSON.parse(screen.getByTestId('chart-options').textContent!)
        expect(chartOptions.responsive).toBe(true)
        expect(chartOptions.maintainAspectRatio).toBe(false)
      })
    })

    it('updates chart colors based on metric values', async () => {
      // High system load should show warning color
      mockApiClient.get.mockResolvedValue({
        data: {
          metrics: {
            systemLoad: 0.95, // High load
            errorRate: 0.15    // High error rate
          },
          timestamp: new Date().toISOString()
        }
      })

      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        const chartElement = screen.getByTestId('line-chart')
        expect(chartElement).toBeInTheDocument()
      })
    })
  })

  describe('User Interactions', () => {
    it('allows manual refresh of metrics', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      expect(mockApiClient.get).toHaveBeenCalledTimes(2) // Initial + manual refresh
    })

    it('handles time range selection', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      const timeRangeSelect = screen.getByRole('combobox', { name: /time range/i })
      await user.selectOptions(timeRangeSelect, '24h')

      expect(mockApiClient.get).toHaveBeenCalledWith('/metrics', {
        params: { timeRange: '24h' }
      })
    })

    it('allows pausing/resuming real-time updates', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      const pauseButton = screen.getByRole('button', { name: /pause/i })
      await user.click(pauseButton)

      expect(screen.getByRole('button', { name: /resume/i })).toBeInTheDocument()
    })

    it('shows metric details on hover', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Active Users')).toBeInTheDocument()
      })

      const metricCard = screen.getByTestId('metric-active-users')
      await user.hover(metricCard)

      await waitFor(() => {
        expect(screen.getByText('Users currently active in the system')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('displays error message when API call fails', async () => {
      mockApiClient.get.mockRejectedValue(new Error('API Error'))

      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Failed to load metrics')).toBeInTheDocument()
      })
    })

    it('shows retry button on error', async () => {
      mockApiClient.get.mockRejectedValue(new Error('Network Error'))

      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
      })
    })

    it('handles WebSocket connection errors', () => {
      mockWebSocketReturn.error = new Error('WebSocket connection failed')
      mockWebSocketReturn.isConnected = false

      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      expect(screen.getByText('Connection Error')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reconnect/i })).toBeInTheDocument()
    })

    it('handles malformed WebSocket data gracefully', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      // Send malformed data
      act(() => {
        mockWebSocketReturn.data = {
          type: 'INVALID_TYPE',
          data: null
        }
      })

      // Should not crash
      expect(screen.getByText('Live Metrics')).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('throttles WebSocket message processing', async () => {
      const processingTimes: number[] = []
      
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      // Send multiple rapid updates
      for (let i = 0; i < 10; i++) {
        const startTime = Date.now()
        act(() => {
          mockWebSocketReturn.data = {
            type: 'METRICS_UPDATE',
            data: { activeUsers: i, timestamp: new Date().toISOString() }
          }
        })
        processingTimes.push(Date.now() - startTime)
      }

      // Processing should be efficient
      const avgProcessingTime = processingTimes.reduce((a, b) => a + b, 0) / processingTimes.length
      expect(avgProcessingTime).toBeLessThan(10) // Less than 10ms average
    })

    it('limits historical data points for charts', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      // Send many data points
      for (let i = 0; i < 100; i++) {
        act(() => {
          mockWebSocketReturn.data = {
            type: 'METRICS_UPDATE',
            data: {
              systemLoad: Math.random(),
              timestamp: new Date(Date.now() + i * 1000).toISOString()
            }
          }
        })
      }

      await waitFor(() => {
        const chartData = JSON.parse(screen.getByTestId('chart-data').textContent!)
        // Should limit to reasonable number of points (e.g., 50)
        expect(chartData.labels.length).toBeLessThanOrEqual(50)
      })
    })
  })

  describe('Accessibility', () => {
    it('provides appropriate ARIA labels', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByLabelText('Active users metric')).toBeInTheDocument()
        expect(screen.getByLabelText('System load metric')).toBeInTheDocument()
      })
    })

    it('announces metric updates to screen readers', async () => {
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      // Update should trigger aria-live announcement
      act(() => {
        mockWebSocketReturn.data = {
          type: 'METRICS_UPDATE',
          data: { activeUsers: 50, timestamp: new Date().toISOString() }
        }
      })

      await waitFor(() => {
        expect(screen.getByRole('status')).toHaveTextContent('Active users updated to 50')
      })
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      // Tab through interactive elements
      await user.tab()
      expect(screen.getByRole('button', { name: /refresh/i })).toHaveFocus()

      await user.tab()
      expect(screen.getByRole('combobox', { name: /time range/i })).toHaveFocus()
    })
  })

  describe('Integration', () => {
    it('integrates with React Query for caching', async () => {
      const queryClient = new QueryClient()
      const TestWrapperWithQuery = ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )

      render(
        <TestWrapperWithQuery>
          <LiveMetrics />
        </TestWrapperWithQuery>
      )

      await waitFor(() => {
        expect(mockApiClient.get).toHaveBeenCalledTimes(1)
      })

      // Re-render should use cached data
      render(
        <TestWrapperWithQuery>
          <LiveMetrics />
        </TestWrapperWithQuery>
      )

      // Should not make additional API call
      expect(mockApiClient.get).toHaveBeenCalledTimes(1)
    })

    it('cleans up WebSocket connection on unmount', () => {
      const { unmount } = render(
        <TestWrapper>
          <LiveMetrics />
        </TestWrapper>
      )

      unmount()

      expect(mockWebSocketReturn.close).toHaveBeenCalled()
    })
  })
})