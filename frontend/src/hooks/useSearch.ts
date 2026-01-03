import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { searchService } from '../services'
import type { UnifiedQuery, SearchResult, SavedSearch, SearchSession } from '../types/search'

// Query keys
export const searchKeys = {
  all: ['search'] as const,
  queries: (params?: any) => [...searchKeys.all, 'queries', params] as const,
  query: (id: string) => [...searchKeys.all, 'query', id] as const,
  sessions: (params?: any) => [...searchKeys.all, 'sessions', params] as const,
  session: (id: string) => [...searchKeys.all, 'session', id] as const,
  saved: (userId: string) => [...searchKeys.all, 'saved', userId] as const,
  analytics: (params?: any) => [...searchKeys.all, 'analytics', params] as const,
  suggestions: (query: string) => [...searchKeys.all, 'suggestions', query] as const,
  popular: () => [...searchKeys.all, 'popular'] as const,
}

// Search operations
export function useSearch() {
  return useMutation({
    mutationFn: (query: UnifiedQuery) => searchService.search(query),
  })
}

export function useSearchHistory(params?: {
  userId?: string
  page?: number
  pageSize?: number
  startDate?: string
  endDate?: string
}) {
  return useQuery({
    queryKey: searchKeys.queries(params),
    queryFn: () => searchService.getSearchHistory(params),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

export function useSearchQuery(queryId: string) {
  return useQuery({
    queryKey: searchKeys.query(queryId),
    queryFn: () => searchService.getSearchQuery(queryId),
    enabled: !!queryId,
  })
}

// Search sessions
export function useCreateSearchSession() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (userId: string) => searchService.createSearchSession(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: searchKeys.sessions() })
    }
  })
}

export function useSearchSession(sessionId: string) {
  return useQuery({
    queryKey: searchKeys.session(sessionId),
    queryFn: () => searchService.getSearchSession(sessionId),
    enabled: !!sessionId,
    staleTime: 30 * 1000, // 30 seconds
  })
}

export function useEndSearchSession() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (sessionId: string) => searchService.endSearchSession(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: searchKeys.sessions() })
    }
  })
}

export function useActiveSessions(userId: string) {
  return useQuery({
    queryKey: [...searchKeys.sessions(), 'active', userId],
    queryFn: () => searchService.getActiveSessions(userId),
    enabled: !!userId,
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: 2 * 60 * 1000, // Refetch every 2 minutes
  })
}

// Saved searches
export function useSavedSearches(userId: string) {
  return useQuery({
    queryKey: searchKeys.saved(userId),
    queryFn: () => searchService.getSavedSearches(userId),
    enabled: !!userId,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useCreateSavedSearch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (savedSearch: Omit<SavedSearch, 'id' | 'createdAt' | 'updatedAt'>) =>
      searchService.createSavedSearch(savedSearch),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: searchKeys.saved(data.userId) })
    }
  })
}

export function useUpdateSavedSearch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, updates }: { id: string; updates: Partial<SavedSearch> }) =>
      searchService.updateSavedSearch(id, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: searchKeys.saved(data.userId) })
    }
  })
}

export function useDeleteSavedSearch() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, userId }: { id: string; userId: string }) =>
      searchService.deleteSavedSearch(id),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: searchKeys.saved(variables.userId) })
    }
  })
}

export function useRunSavedSearch() {
  return useMutation({
    mutationFn: (id: string) => searchService.runSavedSearch(id),
  })
}

// Search analytics
export function useSearchAnalytics(params?: {
  startDate?: string
  endDate?: string
  userId?: string
  resourceType?: string
}) {
  return useQuery({
    queryKey: searchKeys.analytics(params),
    queryFn: () => searchService.getSearchAnalytics(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Search suggestions
export function useSearchSuggestions(query: string, limit: number = 10) {
  return useQuery({
    queryKey: searchKeys.suggestions(query),
    queryFn: () => searchService.getSearchSuggestions(query, limit),
    enabled: query.length > 2,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function usePopularSearches(limit: number = 10) {
  return useQuery({
    queryKey: searchKeys.popular(),
    queryFn: () => searchService.getPopularSearches(limit),
    staleTime: 30 * 60 * 1000, // 30 minutes
  })
}

// Document access
export function useAccessDocument() {
  return useMutation({
    mutationFn: (resultId: string) => searchService.accessDocument(resultId),
  })
}

export function useDownloadDocument() {
  return useMutation({
    mutationFn: ({ resultId, format }: { resultId: string; format?: string }) =>
      searchService.downloadDocument(resultId, format),
  })
}

// Search optimization
export function useOptimizeQuery() {
  return useMutation({
    mutationFn: (query: UnifiedQuery) => searchService.optimizeQuery(query),
  })
}

export function useBestResources() {
  return useMutation({
    mutationFn: ({ query, userPreferences }: { query: string; userPreferences?: any }) =>
      searchService.getBestResources(query, userPreferences),
  })
}

// Search feedback
export function useSubmitSearchFeedback() {
  return useMutation({
    mutationFn: ({ 
      queryId, 
      feedback 
    }: { 
      queryId: string
      feedback: {
        relevanceRating: number
        resultQuality: number
        comments?: string
        helpfulResults?: string[]
      }
    }) => searchService.submitSearchFeedback(queryId, feedback),
  })
}