'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Calendar } from '@/components/ui/calendar'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { CalendarIcon, Download, RefreshCw, TrendingUp, TrendingDown, Star, ThumbsUp, AlertTriangle, MessageSquare } from 'lucide-react'
import { format } from 'date-fns'
import { toast } from '@/components/ui/use-toast'

interface FeedbackMetrics {
  accuracy_metrics: {
    average_rating: number
    rating_distribution: Record<string, number>
    total_feedback: number
    flagged_content: number
    improvement_trend: number
  }
  usefulness_metrics: {
    average_rating: number
    rating_distribution: Record<string, number>
    total_feedback: number
    improvement_suggestions: number
  }
  error_metrics: {
    total_errors: number
    by_severity: Record<string, number>
    by_type: Record<string, number>
    resolution_rate: number
    avg_resolution_time: number
  }
  suggestion_metrics: {
    total_suggestions: number
    by_category: Record<string, number>
    implemented_count: number
    implementation_rate: number
  }
  overall_quality_score: number
  generated_at: string
}

interface AttorneyQueue {
  pending_corrections: Array<{
    id: string
    content_id: string
    correction_type: string
    severity: string
    created_at: string
    attorney_id: string
    explanation: string
  }>
  total_pending: number
  average_review_time: number
  overdue_corrections: number
}

const severityColors = {
  low: 'bg-green-100 text-green-800',
  medium: 'bg-yellow-100 text-yellow-800', 
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800'
}

const ratingLabels = {
  'EXCELLENT': 'Excellent',
  'GOOD': 'Good',
  'FAIR': 'Fair', 
  'POOR': 'Poor',
  'VERY_POOR': 'Very Poor',
  'VERY_USEFUL': 'Very Useful',
  'USEFUL': 'Useful',
  'SOMEWHAT_USEFUL': 'Somewhat Useful',
  'NOT_USEFUL': 'Not Useful'
}

export function FeedbackDashboard() {
  const [metrics, setMetrics] = useState<FeedbackMetrics | null>(null)
  const [attorneyQueue, setAttorneyQueue] = useState<AttorneyQueue | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [dateRange, setDateRange] = useState<{ start: Date | null; end: Date | null }>({
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30 days ago
    end: new Date()
  })
  const [selectedMetrics, setSelectedMetrics] = useState(['accuracy', 'usefulness', 'errors', 'suggestions'])

  const fetchMetrics = async () => {
    try {
      setIsLoading(true)
      const params = new URLSearchParams()
      
      if (dateRange.start) {
        params.append('start_date', dateRange.start.toISOString())
      }
      if (dateRange.end) {
        params.append('end_date', dateRange.end.toISOString())
      }
      selectedMetrics.forEach(metric => {
        params.append('metric_types', metric === 'errors' ? 'errors' : metric === 'suggestions' ? 'suggestions' : metric)
      })

      const response = await fetch(`/api/feedback/metrics?${params}`)
      if (!response.ok) {
        throw new Error('Failed to fetch metrics')
      }
      
      const data = await response.json()
      setMetrics(data)
    } catch (error) {
      toast({
        title: 'Failed to load metrics',
        description: error instanceof Error ? error.message : 'Please try again',
        variant: 'destructive'
      })
    } finally {
      setIsLoading(false)
    }
  }

  const fetchAttorneyQueue = async () => {
    try {
      const response = await fetch('/api/feedback/attorney-queue')
      if (!response.ok) {
        throw new Error('Failed to fetch attorney queue')
      }
      
      const data = await response.json()
      setAttorneyQueue(data)
    } catch (error) {
      toast({
        title: 'Failed to load attorney queue',
        description: error instanceof Error ? error.message : 'Please try again',
        variant: 'destructive'
      })
    }
  }

  const downloadReport = async (reportType: string, format: 'json' | 'csv' | 'pdf' = 'csv') => {
    try {
      const params = new URLSearchParams()
      if (dateRange.start) params.append('start_date', dateRange.start.toISOString())
      if (dateRange.end) params.append('end_date', dateRange.end.toISOString())
      params.append('format', format)

      const response = await fetch(`/api/feedback/reports/${reportType}?${params}`)
      if (!response.ok) {
        throw new Error('Failed to generate report')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${reportType}_report_${format}.${format}`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast({
        title: 'Report Downloaded',
        description: `${reportType} report has been downloaded successfully`
      })
    } catch (error) {
      toast({
        title: 'Download Failed',
        description: error instanceof Error ? error.message : 'Please try again',
        variant: 'destructive'
      })
    }
  }

  useEffect(() => {
    fetchMetrics()
    fetchAttorneyQueue()
  }, [dateRange, selectedMetrics])

  if (isLoading || !metrics) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  const renderOverviewCards = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Overall Quality Score</CardTitle>
          <Star className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {metrics.overall_quality_score.toFixed(1)}
          </div>
          <div className="flex items-center text-xs text-muted-foreground">
            {metrics.accuracy_metrics.improvement_trend > 0 ? (
              <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
            ) : (
              <TrendingDown className="h-3 w-3 text-red-500 mr-1" />
            )}
            {Math.abs(metrics.accuracy_metrics.improvement_trend).toFixed(1)}% from last period
          </div>
          <Progress 
            value={metrics.overall_quality_score * 10} 
            className="mt-2"
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Feedback</CardTitle>
          <ThumbsUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {(metrics.accuracy_metrics.total_feedback + metrics.usefulness_metrics.total_feedback).toLocaleString()}
          </div>
          <p className="text-xs text-muted-foreground">
            {metrics.accuracy_metrics.total_feedback} accuracy, {metrics.usefulness_metrics.total_feedback} usefulness
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Error Reports</CardTitle>
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {metrics.error_metrics.total_errors}
          </div>
          <p className="text-xs text-muted-foreground">
            {metrics.error_metrics.resolution_rate.toFixed(1)}% resolution rate
          </p>
          <div className="flex gap-1 mt-2">
            {Object.entries(metrics.error_metrics.by_severity).map(([severity, count]) => (
              <Badge key={severity} variant="outline" className={`text-xs ${severityColors[severity as keyof typeof severityColors]}`}>
                {count}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Suggestions</CardTitle>
          <MessageSquare className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {metrics.suggestion_metrics.total_suggestions}
          </div>
          <p className="text-xs text-muted-foreground">
            {metrics.suggestion_metrics.implemented_count} implemented ({metrics.suggestion_metrics.implementation_rate.toFixed(1)}%)
          </p>
        </CardContent>
      </Card>
    </div>
  )

  const renderAccuracyMetrics = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Accuracy Rating Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(metrics.accuracy_metrics.rating_distribution).map(([rating, count]) => (
                <div key={rating} className="flex items-center justify-between">
                  <span className="text-sm">{ratingLabels[rating as keyof typeof ratingLabels] || rating}</span>
                  <div className="flex items-center gap-2">
                    <div className="w-24 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${(count / metrics.accuracy_metrics.total_feedback) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium w-8">{count}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Accuracy Statistics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Average Rating</span>
                <span className="text-lg font-bold">{metrics.accuracy_metrics.average_rating.toFixed(2)}</span>
              </div>
              <Progress value={metrics.accuracy_metrics.average_rating * 20} />
            </div>
            <div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Total Feedback</span>
                <span>{metrics.accuracy_metrics.total_feedback}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Flagged for Review</span>
                <Badge variant="outline" className="bg-yellow-100 text-yellow-800">
                  {metrics.accuracy_metrics.flagged_content}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )

  const renderUsefulnessMetrics = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Usefulness Rating Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {Object.entries(metrics.usefulness_metrics.rating_distribution).map(([rating, count]) => (
              <div key={rating} className="flex items-center justify-between">
                <span className="text-sm">{ratingLabels[rating as keyof typeof ratingLabels] || rating}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${(count / metrics.usefulness_metrics.total_feedback) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium w-8">{count}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Improvement Insights</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium">Average Usefulness</span>
              <span className="text-lg font-bold">{metrics.usefulness_metrics.average_rating.toFixed(2)}</span>
            </div>
            <Progress value={metrics.usefulness_metrics.average_rating * 25} />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm">Total Reviews</span>
              <span>{metrics.usefulness_metrics.total_feedback}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Improvement Suggestions</span>
              <span>{metrics.usefulness_metrics.improvement_suggestions}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderErrorMetrics = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Errors by Severity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(metrics.error_metrics.by_severity).map(([severity, count]) => (
                <div key={severity} className="flex items-center justify-between">
                  <Badge className={severityColors[severity as keyof typeof severityColors]}>
                    {severity.charAt(0).toUpperCase() + severity.slice(1)}
                  </Badge>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Errors by Type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(metrics.error_metrics.by_type).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <span className="text-sm capitalize">{type.replace('_', ' ')}</span>
                  <span className="font-medium">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Resolution Stats</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm">Resolution Rate</span>
                <span className="font-bold">{metrics.error_metrics.resolution_rate.toFixed(1)}%</span>
              </div>
              <Progress value={metrics.error_metrics.resolution_rate} />
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm">Avg Resolution Time</span>
              <span>{metrics.error_metrics.avg_resolution_time.toFixed(1)}h</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )

  const renderAttorneyQueue = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Attorney Review Queue</CardTitle>
        <CardDescription>
          Corrections pending attorney review and approval
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{attorneyQueue?.total_pending || 0}</div>
            <div className="text-sm text-muted-foreground">Pending Reviews</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{attorneyQueue?.average_review_time.toFixed(1) || 0}h</div>
            <div className="text-sm text-muted-foreground">Avg Review Time</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{attorneyQueue?.overdue_corrections || 0}</div>
            <div className="text-sm text-muted-foreground">Overdue ({'>'}24h)</div>
          </div>
        </div>

        {attorneyQueue?.pending_corrections && attorneyQueue.pending_corrections.length > 0 && (
          <div className="space-y-2">
            <h4 className="font-medium">Recent Submissions</h4>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {attorneyQueue.pending_corrections.slice(0, 10).map((correction) => (
                <div key={correction.id} className="flex items-center justify-between p-2 border rounded">
                  <div className="flex-1">
                    <div className="font-medium text-sm">{correction.correction_type}</div>
                    <div className="text-xs text-muted-foreground">
                      {correction.explanation.substring(0, 100)}...
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={severityColors[correction.severity as keyof typeof severityColors]}>
                      {correction.severity}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {format(new Date(correction.created_at), 'MMM d, HH:mm')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Feedback Dashboard</h2>
          <p className="text-muted-foreground">
            Monitor user feedback and system quality metrics
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Select value={selectedMetrics.join(',')} onValueChange={(value) => setSelectedMetrics(value.split(','))}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="accuracy,usefulness,errors,suggestions">All Metrics</SelectItem>
              <SelectItem value="accuracy,usefulness">User Ratings</SelectItem>
              <SelectItem value="errors">Errors Only</SelectItem>
              <SelectItem value="suggestions">Suggestions Only</SelectItem>
            </SelectContent>
          </Select>
          
          <Button variant="outline" onClick={() => fetchMetrics()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          
          <Button variant="outline" onClick={() => downloadReport('comprehensive', 'csv')}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {renderOverviewCards()}

      <Tabs defaultValue="accuracy" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="accuracy">Accuracy</TabsTrigger>
          <TabsTrigger value="usefulness">Usefulness</TabsTrigger>
          <TabsTrigger value="errors">Errors</TabsTrigger>
          <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
          <TabsTrigger value="attorney-queue">Attorney Queue</TabsTrigger>
        </TabsList>
        
        <TabsContent value="accuracy">
          {renderAccuracyMetrics()}
        </TabsContent>
        
        <TabsContent value="usefulness">
          {renderUsefulnessMetrics()}
        </TabsContent>
        
        <TabsContent value="errors">
          {renderErrorMetrics()}
        </TabsContent>
        
        <TabsContent value="suggestions">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">User Suggestions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-2">By Category</h4>
                  <div className="space-y-2">
                    {Object.entries(metrics.suggestion_metrics.by_category).map(([category, count]) => (
                      <div key={category} className="flex items-center justify-between">
                        <span className="text-sm capitalize">{category.replace('_', ' ')}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Implementation Status</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Total Suggestions</span>
                      <span>{metrics.suggestion_metrics.total_suggestions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Implemented</span>
                      <span className="text-green-600 font-medium">{metrics.suggestion_metrics.implemented_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Implementation Rate</span>
                      <span>{metrics.suggestion_metrics.implementation_rate.toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="attorney-queue">
          {renderAttorneyQueue()}
        </TabsContent>
      </Tabs>
    </div>
  )
}