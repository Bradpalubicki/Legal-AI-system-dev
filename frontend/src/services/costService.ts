import { apiClient } from '../lib/api'
import type { 
  CostAnalysis, 
  CostEvent, 
  Budget, 
  DashboardData,
  UsageMetrics,
  ResourceType 
} from '../types/cost'

export class CostService {
  // Dashboard data
  async getDashboardData(timeRange: string = '30d'): Promise<DashboardData> {
    const response = await apiClient.get<DashboardData>(`/api/costs/dashboard?range=${timeRange}`)
    if (!response.data) throw new Error('No data received')
    return response.data
  }

  // Cost events
  async getCostEvents(params?: {
    startDate?: string
    endDate?: string
    userId?: string
    resourceType?: ResourceType
    page?: number
    pageSize?: number
  }) {
    const response = await apiClient.getPaginated<CostEvent>('/api/costs/events', params)
    return response
  }

  async createCostEvent(event: Omit<CostEvent, 'id' | 'timestamp'>): Promise<CostEvent> {
    const response = await apiClient.post<CostEvent>('/api/costs/events', event)
    if (!response.data) throw new Error('Failed to create cost event')
    return response.data
  }

  // Cost analysis
  async getCostAnalysis(startDate: string, endDate: string): Promise<CostAnalysis> {
    const response = await apiClient.get<CostAnalysis>(
      `/api/costs/analysis?start_date=${startDate}&end_date=${endDate}`
    )
    if (!response.data) throw new Error('No analysis data received')
    return response.data
  }

  // Budget management
  async getBudgets(params?: {
    entityId?: string
    isActive?: boolean
    page?: number
    pageSize?: number
  }) {
    const response = await apiClient.getPaginated<Budget>('/api/budgets', params)
    return response
  }

  async createBudget(budget: Omit<Budget, 'id' | 'spent' | 'remaining' | 'createdAt' | 'updatedAt'>): Promise<Budget> {
    const response = await apiClient.post<Budget>('/api/budgets', budget)
    if (!response.data) throw new Error('Failed to create budget')
    return response.data
  }

  async updateBudget(id: string, updates: Partial<Budget>): Promise<Budget> {
    const response = await apiClient.patch<Budget>(`/api/budgets/${id}`, updates)
    if (!response.data) throw new Error('Failed to update budget')
    return response.data
  }

  async deleteBudget(id: string): Promise<void> {
    await apiClient.delete(`/api/budgets/${id}`)
  }

  // Usage metrics
  async getUsageMetrics(params?: {
    startDate?: string
    endDate?: string
    userId?: string
    resourceType?: ResourceType
  }): Promise<UsageMetrics> {
    const response = await apiClient.get<UsageMetrics>('/api/costs/usage-metrics', { params })
    if (!response.data) throw new Error('No usage metrics received')
    return response.data
  }

  // Cost optimization
  async getOptimizationSuggestions(params?: {
    userId?: string
    timeRange?: string
  }) {
    const response = await apiClient.get('/api/costs/optimization-suggestions', { params })
    return response.data
  }

  // Forecasting
  async getCostForecast(params: {
    resourceType?: ResourceType
    userId?: string
    months?: number
  }) {
    const response = await apiClient.get('/api/costs/forecast', { params })
    return response.data
  }

  // Reports
  async generateReport(params: {
    type: 'monthly' | 'quarterly' | 'yearly' | 'custom'
    startDate?: string
    endDate?: string
    format: 'pdf' | 'excel' | 'csv'
    includeCharts?: boolean
  }) {
    const response = await apiClient.post('/api/costs/reports/generate', params)
    return response.data
  }

  async downloadReport(reportId: string, format: string): Promise<void> {
    await apiClient.downloadFile(`/api/costs/reports/${reportId}/download?format=${format}`)
  }

  // Alerts
  async getBudgetAlerts(params?: {
    userId?: string
    isActive?: boolean
    severity?: 'low' | 'medium' | 'high' | 'critical'
  }) {
    const response = await apiClient.get('/api/costs/alerts', { params })
    return response.data
  }

  async markAlertAsRead(alertId: string): Promise<void> {
    await apiClient.patch(`/api/costs/alerts/${alertId}/read`)
  }
}

export const costService = new CostService()
export default costService