import { apiClient } from '../lib/api'
import type { 
  SearchQuery,
  SearchResult, 
  UnifiedQuery,
  SearchSession,
  SavedSearch,
  SearchAnalytics
} from '../types/search'

export class SearchService {
  // Search operations
  async search(query: UnifiedQuery): Promise<SearchResult[]> {
    const response = await apiClient.post<SearchResult[]>('/api/search/unified', query)
    if (!response.data) throw new Error('No search results received')
    return response.data
  }

  async getSearchHistory(params?: {
    userId?: string
    page?: number
    pageSize?: number
    startDate?: string
    endDate?: string
  }) {
    const response = await apiClient.getPaginated<SearchQuery>('/api/search/history', params)
    return response
  }

  async getSearchQuery(queryId: string): Promise<SearchQuery> {
    const response = await apiClient.get<SearchQuery>(`/api/search/queries/${queryId}`)
    if (!response.data) throw new Error('Search query not found')
    return response.data
  }

  // Search sessions
  async createSearchSession(userId: string): Promise<SearchSession> {
    const response = await apiClient.post<SearchSession>('/api/search/sessions', { userId })
    if (!response.data) throw new Error('Failed to create search session')
    return response.data
  }

  async getSearchSession(sessionId: string): Promise<SearchSession> {
    const response = await apiClient.get<SearchSession>(`/api/search/sessions/${sessionId}`)
    if (!response.data) throw new Error('Search session not found')
    return response.data
  }

  async endSearchSession(sessionId: string): Promise<SearchSession> {
    const response = await apiClient.patch<SearchSession>(`/api/search/sessions/${sessionId}/end`)
    if (!response.data) throw new Error('Failed to end search session')
    return response.data
  }

  async getActiveSessions(userId: string) {
    const response = await apiClient.get(`/api/search/sessions/active?userId=${userId}`)
    return response.data
  }

  // Saved searches
  async getSavedSearches(userId: string) {
    const response = await apiClient.getPaginated<SavedSearch>(`/api/search/saved?userId=${userId}`)
    return response
  }

  async createSavedSearch(savedSearch: Omit<SavedSearch, 'id' | 'createdAt' | 'updatedAt'>): Promise<SavedSearch> {
    const response = await apiClient.post<SavedSearch>('/api/search/saved', savedSearch)
    if (!response.data) throw new Error('Failed to save search')
    return response.data
  }

  async updateSavedSearch(id: string, updates: Partial<SavedSearch>): Promise<SavedSearch> {
    const response = await apiClient.patch<SavedSearch>(`/api/search/saved/${id}`, updates)
    if (!response.data) throw new Error('Failed to update saved search')
    return response.data
  }

  async deleteSavedSearch(id: string): Promise<void> {
    await apiClient.delete(`/api/search/saved/${id}`)
  }

  async runSavedSearch(id: string): Promise<SearchResult[]> {
    const response = await apiClient.post<SearchResult[]>(`/api/search/saved/${id}/run`)
    if (!response.data) throw new Error('Failed to run saved search')
    return response.data
  }

  // Search analytics
  async getSearchAnalytics(params?: {
    startDate?: string
    endDate?: string
    userId?: string
    resourceType?: string
  }): Promise<SearchAnalytics> {
    const response = await apiClient.get<SearchAnalytics>('/api/search/analytics', { params })
    if (!response.data) throw new Error('No analytics data received')
    return response.data
  }

  // Search suggestions and autocomplete
  async getSearchSuggestions(query: string, limit: number = 10): Promise<string[]> {
    const response = await apiClient.get<string[]>(
      `/api/search/suggestions?q=${encodeURIComponent(query)}&limit=${limit}`
    )
    return response.data || []
  }

  async getPopularSearches(limit: number = 10): Promise<Array<{ query: string; count: number }>> {
    const response = await apiClient.get(`/api/search/popular?limit=${limit}`)
    return response.data || []
  }

  // Document access
  async accessDocument(resultId: string): Promise<{ url: string; cost?: number }> {
    const response = await apiClient.post(`/api/search/results/${resultId}/access`)
    if (!response.data) throw new Error('Failed to access document')
    return response.data
  }

  async downloadDocument(resultId: string, format?: string): Promise<void> {
    const url = `/api/search/results/${resultId}/download${format ? `?format=${format}` : ''}`
    await apiClient.downloadFile(url)
  }

  // Search optimization
  async optimizeQuery(query: UnifiedQuery): Promise<{
    optimizedQuery: UnifiedQuery
    estimatedCost: number
    suggestions: string[]
  }> {
    const response = await apiClient.post('/api/search/optimize', query)
    if (!response.data) throw new Error('Failed to optimize query')
    return response.data
  }

  async getBestResources(query: string, userPreferences?: any): Promise<Array<{
    resource: string
    confidence: number
    estimatedCost: number
    reasoning: string
  }>> {
    const response = await apiClient.post('/api/search/best-resources', {
      query,
      userPreferences
    })
    return response.data || []
  }

  // Search feedback
  async submitSearchFeedback(queryId: string, feedback: {
    relevanceRating: number
    resultQuality: number
    comments?: string
    helpfulResults?: string[]
  }): Promise<void> {
    await apiClient.post(`/api/search/queries/${queryId}/feedback`, feedback)
  }
}

export const searchService = new SearchService()
export default searchService