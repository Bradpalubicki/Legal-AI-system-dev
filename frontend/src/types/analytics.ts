// Analytics Data Types
export interface AnalyticsData {
  id: string
  timestamp: string
  value: number
  category?: string
  metadata?: Record<string, any>
}

export interface TimeSeriesData {
  date: string
  value: number
  label?: string
  category?: string
}

export interface CategoryData {
  category: string
  value: number
  percentage?: number
  color?: string
}

export interface HeatMapData {
  id: string
  data: Record<string, number>
}

export interface TreeMapData {
  name: string
  value?: number
  children?: TreeMapData[]
  color?: string
}

// Legal Analytics Specific Types
export interface LegalResearchMetrics {
  totalSearches: number
  successfulSearches: number
  averageSearchTime: number
  totalCost: number
  averageCostPerSearch: number
  searchesByDatabase: CategoryData[]
  searchesByPracticeArea: CategoryData[]
  searchTrends: TimeSeriesData[]
  costTrends: TimeSeriesData[]
  userActivity: UserActivityData[]
}

export interface UserActivityData {
  userId: string
  userName: string
  searches: number
  documents: number
  annotations: number
  cost: number
  timeSpent: number
  lastActive: string
}

export interface DocumentAnalytics {
  totalDocuments: number
  documentsByType: CategoryData[]
  documentsByStatus: CategoryData[]
  processingTimes: TimeSeriesData[]
  annotationActivity: TimeSeriesData[]
  complianceScores: CategoryData[]
  riskDistribution: CategoryData[]
}

export interface CaseMetrics {
  totalCases: number
  casesByStatus: CategoryData[]
  casesByPriority: CategoryData[]
  casesOverTime: TimeSeriesData[]
  averageCaseValue: number
  caseResolutionTime: TimeSeriesData[]
  successRate: number
}

export interface PerformanceMetrics {
  responseTime: TimeSeriesData[]
  systemLoad: TimeSeriesData[]
  errorRate: TimeSeriesData[]
  userSatisfaction: number
  uptime: number
  apiUsage: CategoryData[]
}

// Chart Configuration Types
export interface ChartConfig {
  title?: string
  subtitle?: string
  width?: number
  height?: number
  margin?: {
    top?: number
    right?: number
    bottom?: number
    left?: number
  }
  colors?: string[]
  theme?: 'light' | 'dark'
  animate?: boolean
  interactive?: boolean
  showLegend?: boolean
  showTooltip?: boolean
  showGrid?: boolean
}

export interface LineChartConfig extends ChartConfig {
  xAxisLabel?: string
  yAxisLabel?: string
  curve?: 'linear' | 'cardinal' | 'monotoneX' | 'step'
  showPoints?: boolean
  showArea?: boolean
  stacked?: boolean
}

export interface BarChartConfig extends ChartConfig {
  orientation?: 'vertical' | 'horizontal'
  grouped?: boolean
  stacked?: boolean
  showValues?: boolean
  xAxisLabel?: string
  yAxisLabel?: string
}

export interface PieChartConfig extends ChartConfig {
  innerRadius?: number
  cornerRadius?: number
  padAngle?: number
  sortByValue?: boolean
  startAngle?: number
  endAngle?: number
}

export interface HeatMapConfig extends ChartConfig {
  xAxisLabel?: string
  yAxisLabel?: string
  cellOpacity?: number
  cellBorderWidth?: number
  colorScheme?: string[]
  minValue?: number
  maxValue?: number
}

export interface TreeMapConfig extends ChartConfig {
  labelSkipSize?: number
  tileComponent?: 'rect' | 'circle'
  orientLabels?: boolean
  innerPadding?: number
  outerPadding?: number
}

// Dashboard Types
export interface DashboardWidget {
  id: string
  type: WidgetType
  title: string
  description?: string
  dataSource: string
  config: ChartConfig
  position: {
    x: number
    y: number
    width: number
    height: number
  }
  refreshInterval?: number
  filters?: WidgetFilter[]
}

export enum WidgetType {
  LINE_CHART = 'line_chart',
  BAR_CHART = 'bar_chart',
  PIE_CHART = 'pie_chart',
  AREA_CHART = 'area_chart',
  HEATMAP = 'heatmap',
  TREEMAP = 'treemap',
  METRIC_CARD = 'metric_card',
  TABLE = 'table',
  GAUGE = 'gauge',
  FUNNEL = 'funnel'
}

export interface WidgetFilter {
  field: string
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'between'
  value: any
  label?: string
}

export interface DashboardLayout {
  id: string
  name: string
  description?: string
  widgets: DashboardWidget[]
  createdBy: string
  createdAt: string
  updatedAt: string
  isPublic: boolean
  tags: string[]
}

// Export Types
export interface ExportConfig {
  format: ExportFormat
  filename?: string
  quality?: 'low' | 'medium' | 'high'
  includeData?: boolean
  includeConfig?: boolean
}

export enum ExportFormat {
  PNG = 'png',
  JPEG = 'jpeg',
  PDF = 'pdf',
  SVG = 'svg',
  CSV = 'csv',
  JSON = 'json',
  EXCEL = 'excel'
}

// Reporting Types
export interface ReportTemplate {
  id: string
  name: string
  description?: string
  sections: ReportSection[]
  schedule?: ReportSchedule
  recipients: string[]
  format: ExportFormat
}

export interface ReportSection {
  id: string
  title: string
  description?: string
  widgets: string[]
  pageBreak?: boolean
}

export interface ReportSchedule {
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly'
  time: string
  timezone: string
  enabled: boolean
}

// Filter and Query Types
export interface AnalyticsQuery {
  startDate: string
  endDate: string
  filters: QueryFilter[]
  groupBy?: string[]
  aggregation?: 'sum' | 'avg' | 'count' | 'min' | 'max'
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
  limit?: number
}

export interface QueryFilter {
  field: string
  operator: string
  value: any
}

// Real-time Analytics Types
export interface RealtimeMetric {
  id: string
  name: string
  value: number
  change: number
  changeType: 'increase' | 'decrease' | 'neutral'
  timestamp: string
  unit?: string
  format?: 'number' | 'currency' | 'percentage' | 'time'
}

export interface AlertRule {
  id: string
  name: string
  metric: string
  condition: 'greater_than' | 'less_than' | 'equals' | 'change_by'
  threshold: number
  enabled: boolean
  recipients: string[]
  cooldownMinutes: number
}

// Drill-down Types
export interface DrilldownLevel {
  field: string
  label: string
  data: CategoryData[]
}

export interface DrilldownPath {
  levels: DrilldownLevel[]
  breadcrumbs: BreadcrumbItem[]
}

export interface BreadcrumbItem {
  label: string
  value: string
  level: number
}

// Comparison Types
export interface ComparisonData {
  current: AnalyticsData[]
  previous: AnalyticsData[]
  change: number
  changePercentage: number
  trend: 'up' | 'down' | 'stable'
}