export interface CostEvent {
  id: string
  userId: string
  sessionId: string
  resourceType: ResourceType
  operation: OperationType
  amount: number
  currency: string
  metadata: Record<string, any>
  timestamp: string
  clientId?: string
  matterId?: string
  billingCode?: string
}

export const ResourceType = {
  WESTLAW: 'westlaw',
  LEXISNEXIS: 'lexisnexis',
  BLOOMBERG_LAW: 'bloomberg_law',
  COURTLISTENER: 'courtlistener',
  GOOGLE_SCHOLAR: 'google_scholar',
  INTERNAL_AI: 'internal_ai',
  DOCUMENT_PROCESSING: 'document_processing',
  STORAGE: 'storage'
} as const

export type ResourceType = typeof ResourceType[keyof typeof ResourceType]

export enum OperationType {
  SEARCH = 'search',
  DOCUMENT_ACCESS = 'document_access',
  API_CALL = 'api_call',
  DOWNLOAD = 'download',
  CITATION_CHECK = 'citation_check',
  ANALYSIS = 'analysis'
}

export interface CostAnalysis {
  id: string
  startDate: string
  endDate: string
  totalCost: number
  costByResource: Record<ResourceType, number>
  costByUser: Record<string, number>
  costByOperation: Record<OperationType, number>
  trends: CostTrend[]
  drivers: CostDriver[]
  opportunities: OptimizationOpportunity[]
  generatedAt: string
}

export interface CostTrend {
  period: string
  amount: number
  change: number
  changePercentage: number
}

export interface CostDriver {
  category: string
  subcategory: string
  amount: number
  percentage: number
  description: string
}

export interface OptimizationOpportunity {
  type: string
  description: string
  potentialSavings: number
  difficulty: 'easy' | 'medium' | 'hard'
  priority: 'low' | 'medium' | 'high'
  actionItems: string[]
}

export interface Budget {
  id: string
  name: string
  allocationType: AllocationType
  entityId: string
  amount: number
  currency: string
  period: BudgetPeriod
  startDate: string
  endDate: string
  spent: number
  remaining: number
  alerts: BudgetAlert[]
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export enum AllocationType {
  USER = 'user',
  CLIENT = 'client',
  MATTER = 'matter',
  DEPARTMENT = 'department',
  GLOBAL = 'global'
}

export enum BudgetPeriod {
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  YEARLY = 'yearly',
  CUSTOM = 'custom'
}

export interface BudgetAlert {
  id: string
  type: AlertType
  threshold: number
  isTriggered: boolean
  lastTriggered?: string
  recipients: string[]
}

export enum AlertType {
  THRESHOLD = 'threshold',
  FORECAST_EXCEEDED = 'forecast_exceeded',
  UNUSUAL_SPENDING = 'unusual_spending'
}

export interface UsageMetrics {
  period: string
  totalSearches: number
  totalDocuments: number
  totalCost: number
  averageCostPerSearch: number
  mostUsedResource: ResourceType
  peakUsageHour: number
  userActivity: UserActivityMetric[]
}

export interface UserActivityMetric {
  userId: string
  userName: string
  searches: number
  documents: number
  cost: number
  efficiency: number
}

export interface DashboardData {
  totalCost: number
  monthlySpend: number
  budgetUtilization: number
  costTrends: CostTrend[]
  topResources: Array<{
    resource: ResourceType
    cost: number
    percentage: number
  }>
  recentTransactions: CostEvent[]
  alerts: BudgetAlert[]
  projectedSpend: number
}