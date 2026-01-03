import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { costService } from '../services'
import type { CostEvent, Budget, DashboardData, ResourceType } from '../types/cost'

// Query keys
export const costKeys = {
  all: ['costs'] as const,
  dashboard: (range: string) => [...costKeys.all, 'dashboard', range] as const,
  events: (params?: any) => [...costKeys.all, 'events', params] as const,
  analysis: (startDate: string, endDate: string) => [...costKeys.all, 'analysis', startDate, endDate] as const,
  budgets: (params?: any) => [...costKeys.all, 'budgets', params] as const,
  usage: (params?: any) => [...costKeys.all, 'usage', params] as const,
  alerts: (params?: any) => [...costKeys.all, 'alerts', params] as const,
}

// Dashboard data hook
export function useDashboardData(timeRange: string = '30d') {
  return useQuery({
    queryKey: costKeys.dashboard(timeRange),
    queryFn: () => costService.getDashboardData(timeRange),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// Cost events hooks
export function useCostEvents(params?: {
  startDate?: string
  endDate?: string
  userId?: string
  resourceType?: ResourceType
  page?: number
  pageSize?: number
}) {
  return useQuery({
    queryKey: costKeys.events(params),
    queryFn: () => costService.getCostEvents(params),
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

export function useCreateCostEvent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (event: Omit<CostEvent, 'id' | 'timestamp'>) => 
      costService.createCostEvent(event),
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: costKeys.events() })
      queryClient.invalidateQueries({ queryKey: costKeys.dashboard('30d') })
      queryClient.invalidateQueries({ queryKey: costKeys.usage() })
    }
  })
}

// Cost analysis hook
export function useCostAnalysis(startDate: string, endDate: string) {
  return useQuery({
    queryKey: costKeys.analysis(startDate, endDate),
    queryFn: () => costService.getCostAnalysis(startDate, endDate),
    enabled: !!startDate && !!endDate,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Budget hooks
export function useBudgets(params?: {
  entityId?: string
  isActive?: boolean
  page?: number
  pageSize?: number
}) {
  return useQuery({
    queryKey: costKeys.budgets(params),
    queryFn: () => costService.getBudgets(params),
    staleTime: 3 * 60 * 1000, // 3 minutes
  })
}

export function useCreateBudget() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (budget: Omit<Budget, 'id' | 'spent' | 'remaining' | 'createdAt' | 'updatedAt'>) =>
      costService.createBudget(budget),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: costKeys.budgets() })
    }
  })
}

export function useUpdateBudget() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<Budget> }) =>
      costService.updateBudget(id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: costKeys.budgets() })
    }
  })
}

export function useDeleteBudget() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: string) => costService.deleteBudget(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: costKeys.budgets() })
    }
  })
}

// Usage metrics hook
export function useUsageMetrics(params?: {
  startDate?: string
  endDate?: string
  userId?: string
  resourceType?: ResourceType
}) {
  return useQuery({
    queryKey: costKeys.usage(params),
    queryFn: () => costService.getUsageMetrics(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// Optimization suggestions hook
export function useOptimizationSuggestions(params?: {
  userId?: string
  timeRange?: string
}) {
  return useQuery({
    queryKey: [...costKeys.all, 'optimization', params],
    queryFn: () => costService.getOptimizationSuggestions(params),
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

// Cost forecast hook
export function useCostForecast(params: {
  resourceType?: ResourceType
  userId?: string
  months?: number
}) {
  return useQuery({
    queryKey: [...costKeys.all, 'forecast', params],
    queryFn: () => costService.getCostForecast(params),
    enabled: !!params,
    staleTime: 15 * 60 * 1000, // 15 minutes
  })
}

// Budget alerts hook
export function useBudgetAlerts(params?: {
  userId?: string
  isActive?: boolean
  severity?: 'low' | 'medium' | 'high' | 'critical'
}) {
  return useQuery({
    queryKey: costKeys.alerts(params),
    queryFn: () => costService.getBudgetAlerts(params),
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  })
}

export function useMarkAlertAsRead() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (alertId: string) => costService.markAlertAsRead(alertId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: costKeys.alerts() })
    }
  })
}