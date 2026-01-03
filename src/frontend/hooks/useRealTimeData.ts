import { useState, useEffect, useCallback } from 'react'

export interface RealTimeData {
  documents: {
    processing: number
    completed: number
    failed: number
    queue: DocumentStatus[]
  }
  analysis: {
    inProgress: number
    completed: number
    confidence: number
    insights: AnalysisInsight[]
  }
  qa: {
    pendingResponses: number
    totalSessions: number
    activeUsers: number
    recentQuestions: QAItem[]
  }
  defense: {
    availableStrategies: number
    recommendations: DefenseRecommendation[]
    riskAssessments: RiskAssessment[]
  }
  attorney: {
    activeUsers: number
    productivityScore: number
    billableHours: number
    caseLoad: number
  }
  deadlines: {
    upcoming: DeadlineItem[]
    overdue: DeadlineItem[]
    completed: number
  }
  actions: {
    pending: ActionItem[]
    completed: number
    overdue: number
  }
  notifications: {
    unread: number
    recent: NotificationItem[]
    alerts: AlertItem[]
  }
  system: {
    uptime: number
    performance: number
    errors: number
    lastUpdate: string
  }
}

export interface DocumentStatus {
  id: string
  name: string
  status: 'processing' | 'completed' | 'failed'
  progress: number
  estimatedTime: number
  priority: 'high' | 'medium' | 'low'
}

export interface AnalysisInsight {
  id: string
  type: string
  confidence: number
  summary: string
  timestamp: string
}

export interface QAItem {
  id: string
  question: string
  status: 'pending' | 'answered' | 'escalated'
  priority: 'high' | 'medium' | 'low'
  timestamp: string
}

export interface DefenseRecommendation {
  id: string
  strategy: string
  confidence: number
  impact: 'high' | 'medium' | 'low'
  priority: number
}

export interface RiskAssessment {
  id: string
  risk: string
  level: 'critical' | 'high' | 'medium' | 'low'
  mitigation: string
  timestamp: string
}

export interface DeadlineItem {
  id: string
  title: string
  date: string
  type: 'filing' | 'hearing' | 'discovery' | 'response'
  priority: 'critical' | 'high' | 'medium' | 'low'
  daysRemaining: number
}

export interface ActionItem {
  id: string
  title: string
  description: string
  assignee: string
  dueDate: string
  priority: 'high' | 'medium' | 'low'
  status: 'pending' | 'in-progress' | 'completed'
  caseId: string
}

export interface NotificationItem {
  id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  timestamp: string
  read: boolean
}

export interface AlertItem {
  id: string
  title: string
  message: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  timestamp: string
  acknowledged: boolean
}

export interface UseRealTimeDataReturn {
  data: RealTimeData
  isLoading: boolean
  error: string | null
  refresh: () => Promise<void>
  lastUpdated: string | null
}

// Mock data generator for development
const generateMockData = (): RealTimeData => {
  return {
    documents: {
      processing: Math.floor(Math.random() * 10) + 1,
      completed: Math.floor(Math.random() * 50) + 20,
      failed: Math.floor(Math.random() * 3),
      queue: [
        {
          id: '1',
          name: 'Contract_Analysis_v2.pdf',
          status: 'processing',
          progress: Math.floor(Math.random() * 80) + 10,
          estimatedTime: Math.floor(Math.random() * 300) + 60,
          priority: 'high'
        },
        {
          id: '2',
          name: 'Discovery_Documents.docx',
          status: 'processing',
          progress: Math.floor(Math.random() * 60) + 20,
          estimatedTime: Math.floor(Math.random() * 180) + 30,
          priority: 'medium'
        }
      ]
    },
    analysis: {
      inProgress: Math.floor(Math.random() * 5) + 1,
      completed: Math.floor(Math.random() * 30) + 10,
      confidence: Math.floor(Math.random() * 20) + 75,
      insights: [
        {
          id: '1',
          type: 'Risk Assessment',
          confidence: 0.92,
          summary: 'High probability of favorable outcome based on precedent analysis',
          timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString()
        },
        {
          id: '2',
          type: 'Strategy Recommendation',
          confidence: 0.87,
          summary: 'Consider motion to dismiss based on jurisdictional issues',
          timestamp: new Date(Date.now() - Math.random() * 7200000).toISOString()
        }
      ]
    },
    qa: {
      pendingResponses: Math.floor(Math.random() * 8) + 2,
      totalSessions: Math.floor(Math.random() * 20) + 15,
      activeUsers: Math.floor(Math.random() * 5) + 1,
      recentQuestions: [
        {
          id: '1',
          question: 'What is the statute of limitations for this type of case?',
          status: 'pending',
          priority: 'high',
          timestamp: new Date(Date.now() - Math.random() * 1800000).toISOString()
        },
        {
          id: '2',
          question: 'Are there any similar cases with favorable outcomes?',
          status: 'answered',
          priority: 'medium',
          timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString()
        }
      ]
    },
    defense: {
      availableStrategies: Math.floor(Math.random() * 6) + 3,
      recommendations: [
        {
          id: '1',
          strategy: 'Motion to Dismiss - Lack of Standing',
          confidence: 0.78,
          impact: 'high',
          priority: 1
        },
        {
          id: '2',
          strategy: 'Summary Judgment - No Material Facts',
          confidence: 0.65,
          impact: 'medium',
          priority: 2
        }
      ],
      riskAssessments: [
        {
          id: '1',
          risk: 'Potential liability exposure exceeds $2M',
          level: 'high',
          mitigation: 'Consider settlement negotiations',
          timestamp: new Date().toISOString()
        }
      ]
    },
    attorney: {
      activeUsers: Math.floor(Math.random() * 8) + 3,
      productivityScore: Math.floor(Math.random() * 15) + 82,
      billableHours: Math.floor(Math.random() * 20) + 35,
      caseLoad: Math.floor(Math.random() * 10) + 15
    },
    deadlines: {
      upcoming: [
        {
          id: '1',
          title: 'Response to Motion for Summary Judgment',
          date: new Date(Date.now() + 5 * 24 * 3600000).toISOString(),
          type: 'response',
          priority: 'critical',
          daysRemaining: 5
        },
        {
          id: '2',
          title: 'Discovery Deadline',
          date: new Date(Date.now() + 14 * 24 * 3600000).toISOString(),
          type: 'discovery',
          priority: 'high',
          daysRemaining: 14
        }
      ],
      overdue: [],
      completed: Math.floor(Math.random() * 20) + 8
    },
    actions: {
      pending: [
        {
          id: '1',
          title: 'Review deposition transcripts',
          description: 'Analyze key testimony for inconsistencies',
          assignee: 'John Smith',
          dueDate: new Date(Date.now() + 2 * 24 * 3600000).toISOString(),
          priority: 'high',
          status: 'pending',
          caseId: 'case-123'
        },
        {
          id: '2',
          title: 'Draft settlement proposal',
          description: 'Prepare initial settlement terms',
          assignee: 'Sarah Johnson',
          dueDate: new Date(Date.now() + 7 * 24 * 3600000).toISOString(),
          priority: 'medium',
          status: 'in-progress',
          caseId: 'case-124'
        }
      ],
      completed: Math.floor(Math.random() * 15) + 25,
      overdue: Math.floor(Math.random() * 3)
    },
    notifications: {
      unread: Math.floor(Math.random() * 8) + 2,
      recent: [
        {
          id: '1',
          title: 'Document Analysis Complete',
          message: 'Contract_Analysis_v2.pdf has been successfully processed',
          type: 'success',
          timestamp: new Date(Date.now() - Math.random() * 1800000).toISOString(),
          read: false
        },
        {
          id: '2',
          title: 'New Q&A Response Available',
          message: 'Your question about statute of limitations has been answered',
          type: 'info',
          timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
          read: true
        }
      ],
      alerts: [
        {
          id: '1',
          title: 'Deadline Alert',
          message: 'Response due in 5 days for Case #2024-CV-123',
          severity: 'high',
          timestamp: new Date().toISOString(),
          acknowledged: false
        }
      ]
    },
    system: {
      uptime: 99.8,
      performance: Math.floor(Math.random() * 10) + 85,
      errors: Math.floor(Math.random() * 3),
      lastUpdate: new Date().toISOString()
    }
  }
}

export const useRealTimeData = (): UseRealTimeDataReturn => {
  const [data, setData] = useState<RealTimeData>(generateMockData)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  const fetchData = useCallback(async (): Promise<RealTimeData> => {
    // In production, this would make actual API calls
    // For now, we'll simulate API delay and return mock data
    await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500))

    return generateMockData()
  }, [])

  const refresh = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const newData = await fetchData()
      setData(newData)
      setLastUpdated(new Date().toISOString())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setIsLoading(false)
    }
  }, [fetchData])

  // Auto-refresh data
  useEffect(() => {
    const interval = setInterval(refresh, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [refresh])

  // Listen for manual refresh events
  useEffect(() => {
    const handleRefresh = () => refresh()
    window.addEventListener('dashboard-refresh', handleRefresh)
    return () => window.removeEventListener('dashboard-refresh', handleRefresh)
  }, [refresh])

  // Listen for real-time updates
  useEffect(() => {
    const handleRealTimeUpdate = (event: CustomEvent) => {
      const update = event.detail

      // Update specific data based on the update type
      setData(prevData => {
        const newData = { ...prevData }

        switch (update.type) {
          case 'document-processed':
            newData.documents.processing = Math.max(0, newData.documents.processing - 1)
            newData.documents.completed += 1
            break
          case 'analysis-completed':
            newData.analysis.inProgress = Math.max(0, newData.analysis.inProgress - 1)
            newData.analysis.completed += 1
            break
          case 'qa-answered':
            newData.qa.pendingResponses = Math.max(0, newData.qa.pendingResponses - 1)
            break
          case 'notification':
            newData.notifications.unread += 1
            newData.notifications.recent.unshift({
              id: Date.now().toString(),
              title: update.title,
              message: update.message,
              type: update.severity || 'info',
              timestamp: new Date().toISOString(),
              read: false
            })
            break
          default:
            // Handle other update types
            break
        }

        return newData
      })

      setLastUpdated(new Date().toISOString())
    }

    window.addEventListener('real-time-update', handleRealTimeUpdate as EventListener)
    return () => window.removeEventListener('real-time-update', handleRealTimeUpdate as EventListener)
  }, [])

  // Initial data load
  useEffect(() => {
    refresh()
  }, [refresh])

  return {
    data,
    isLoading,
    error,
    refresh,
    lastUpdated
  }
}