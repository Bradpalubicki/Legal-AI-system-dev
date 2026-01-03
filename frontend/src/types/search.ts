export interface SearchQuery {
  id: string
  query: string
  userId: string
  sessionId: string
  resources: ResourceType[]
  filters: SearchFilters
  timestamp: string
  results: SearchResult[]
  cost: number
  processingTime: number
}

export interface SearchFilters {
  dateRange?: {
    start: string
    end: string
  }
  jurisdiction?: string[]
  courtLevel?: string[]
  documentType?: string[]
  practiceArea?: string[]
  language?: string
  sortBy?: SortOption
  resultsPerPage?: number
}

export enum SortOption {
  RELEVANCE = 'relevance',
  DATE_DESC = 'date_desc',
  DATE_ASC = 'date_asc',
  CITATION_COUNT = 'citation_count'
}

export interface SearchResult {
  id: string
  title: string
  source: ResourceType
  url: string
  snippet: string
  relevanceScore: number
  date?: string
  jurisdiction?: string
  court?: string
  citationCount?: number
  documentType: string
  accessCost?: number
  isFullTextAvailable: boolean
  metadata: Record<string, any>
}

export interface UnifiedQuery {
  query: string
  natural_language_query?: string
  filters: SearchFilters
  preferred_resources?: ResourceType[]
  max_results?: number
  include_ai_analysis?: boolean
  user_context?: UserContext
}

export interface UserContext {
  practice_areas: string[]
  jurisdiction_preferences: string[]
  cost_sensitivity: 'low' | 'medium' | 'high'
  quality_preference: 'speed' | 'balanced' | 'comprehensive'
}

export interface SearchSession {
  id: string
  userId: string
  startTime: string
  endTime?: string
  queries: SearchQuery[]
  totalCost: number
  totalResults: number
  isActive: boolean
}

export interface SavedSearch {
  id: string
  userId: string
  name: string
  query: UnifiedQuery
  alertsEnabled: boolean
  lastRun?: string
  resultCount?: number
  createdAt: string
  updatedAt: string
}

export interface SearchAnalytics {
  period: string
  totalQueries: number
  averageResultsPerQuery: number
  averageCostPerQuery: number
  mostSearchedTerms: Array<{
    term: string
    count: number
  }>
  resourceUsage: Array<{
    resource: ResourceType
    queries: number
    cost: number
  }>
  userEngagement: {
    clickThroughRate: number
    averageSessionDuration: number
    queryRefinementRate: number
  }
}