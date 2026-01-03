'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { ClockIcon, CpuChipIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

// AI Model tiers for cost estimation
export type AIModelTier = 'haiku' | 'sonnet' | 'opus'

interface CostEstimate {
  tier: AIModelTier
  estimatedCost: number
  processingTime: string
  confidence: number
}

interface ProcessingSession {
  id: string
  startTime: Date
  currentCost: number
  operations: ProcessingOperation[]
  estimatedTotal: number
}

interface ProcessingOperation {
  id: string
  type: string
  tier: AIModelTier
  cost: number
  timestamp: Date
  status: 'processing' | 'completed' | 'failed'
}

interface CostIndicatorProps {
  // Pre-processing estimation
  estimatedCost?: CostEstimate
  documentComplexity?: number
  taskType?: string

  // Real-time processing tracking
  session?: ProcessingSession
  isProcessing?: boolean

  // Budget and limits
  monthlyBudget?: number
  currentMonthlySpend?: number
  userBudgetLimit?: number

  // Display options
  variant?: 'compact' | 'detailed' | 'minimal'
  showBudgetProgress?: boolean
  showModelBreakdown?: boolean

  // Callbacks
  onModelTierChange?: (tier: AIModelTier) => void
  onBudgetAlert?: (alertType: 'warning' | 'critical', details: any) => void
}

const TIER_CONFIG = {
  haiku: {
    name: 'Claude 3 Haiku',
    costPer1K: 0.01,
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
    dotColor: 'bg-green-400',
    description: 'Fast, cost-effective processing'
  },
  sonnet: {
    name: 'Claude 3 Sonnet',
    costPer1K: 0.15,
    color: 'yellow',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-800',
    dotColor: 'bg-yellow-400',
    description: 'Balanced analysis and cost'
  },
  opus: {
    name: 'Claude 3 Opus',
    costPer1K: 0.75,
    color: 'red',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800',
    dotColor: 'bg-red-400',
    description: 'Highest quality analysis'
  }
}

export default function CostIndicator({
  estimatedCost,
  documentComplexity = 0.5,
  taskType = 'analysis',
  session,
  isProcessing = false,
  monthlyBudget,
  currentMonthlySpend = 0,
  userBudgetLimit,
  variant = 'detailed',
  showBudgetProgress = true,
  showModelBreakdown = true,
  onModelTierChange,
  onBudgetAlert
}: CostIndicatorProps) {
  const [realtimeCost, setRealtimeCost] = useState(0)
  const [processingDuration, setProcessingDuration] = useState(0)

  // Real-time cost accumulator
  useEffect(() => {
    if (!isProcessing || !session) return

    const interval = setInterval(() => {
      const now = new Date()
      const duration = Math.floor((now.getTime() - session.startTime.getTime()) / 1000)
      setProcessingDuration(duration)

      // Calculate current cost from operations
      const currentCost = session.operations.reduce((total, op) => total + op.cost, 0)
      setRealtimeCost(currentCost)
    }, 1000)

    return () => clearInterval(interval)
  }, [isProcessing, session])

  // Budget alert monitoring
  useEffect(() => {
    if (!onBudgetAlert || !monthlyBudget) return

    const budgetUsed = (currentMonthlySpend / monthlyBudget) * 100

    if (budgetUsed >= 90) {
      onBudgetAlert('critical', {
        budgetUsed,
        remaining: monthlyBudget - currentMonthlySpend,
        type: 'monthly_budget_critical'
      })
    } else if (budgetUsed >= 75) {
      onBudgetAlert('warning', {
        budgetUsed,
        remaining: monthlyBudget - currentMonthlySpend,
        type: 'monthly_budget_warning'
      })
    }
  }, [currentMonthlySpend, monthlyBudget, onBudgetAlert])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 3,
      maximumFractionDigits: 3
    }).format(amount)
  }

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}m ${remainingSeconds}s`
  }

  const getTierForComplexity = (complexity: number): AIModelTier => {
    if (complexity < 0.3) return 'haiku'
    if (complexity < 0.7) return 'sonnet'
    return 'opus'
  }

  const currentTier = estimatedCost?.tier || getTierForComplexity(documentComplexity)
  const tierConfig = TIER_CONFIG[currentTier]

  // Budget progress calculation
  const budgetProgress = monthlyBudget
    ? Math.min((currentMonthlySpend / monthlyBudget) * 100, 100)
    : 0

  const budgetStatus = budgetProgress >= 90 ? 'critical' : budgetProgress >= 75 ? 'warning' : 'good'

  if (variant === 'minimal') {
    return (
      <div className="flex items-center space-x-2">
        <div className={clsx('w-2 h-2 rounded-full', tierConfig.dotColor)} />
        <span className="text-sm text-gray-600">
          {isProcessing ? formatCurrency(realtimeCost) : formatCurrency(estimatedCost?.estimatedCost || 0)}
        </span>
        {isProcessing && (
          <ClockIcon className="w-4 h-4 text-gray-400 animate-spin" />
        )}
      </div>
    )
  }

  if (variant === 'compact') {
    return (
      <Card variant="outlined" padding="sm" className={clsx(tierConfig.bgColor, tierConfig.borderColor)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={clsx('w-3 h-3 rounded-full', tierConfig.dotColor)} />
            <span className={clsx('text-sm font-medium', tierConfig.textColor)}>
              {tierConfig.name}
            </span>
          </div>
          <div className="text-right">
            <div className="text-sm font-semibold">
              {isProcessing ? formatCurrency(realtimeCost) : formatCurrency(estimatedCost?.estimatedCost || 0)}
            </div>
            {isProcessing && (
              <div className="text-xs text-gray-500">
                {formatDuration(processingDuration)}
              </div>
            )}
          </div>
        </div>
      </Card>
    )
  }

  return (
    <Card variant="elevated" className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <CpuChipIcon className="w-5 h-5" />
          <span>Cost Tracking</span>
          {isProcessing && (
            <div className="flex items-center space-x-1">
              <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
              <span className="text-sm text-blue-600">Processing</span>
            </div>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Current Operation Cost */}
        <div className={clsx(
          'p-4 rounded-lg border-2',
          tierConfig.bgColor,
          tierConfig.borderColor
        )}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <div className={clsx('w-3 h-3 rounded-full', tierConfig.dotColor)} />
              <span className={clsx('font-medium', tierConfig.textColor)}>
                {tierConfig.name}
              </span>
            </div>
            <button
              onClick={() => onModelTierChange?.(currentTier)}
              className="text-xs text-blue-600 hover:text-blue-800 underline"
            >
              Change Model
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-gray-500 uppercase tracking-wide">
                {isProcessing ? 'Current Cost' : 'Estimated Cost'}
              </div>
              <div className="text-lg font-bold">
                {isProcessing ? formatCurrency(realtimeCost) : formatCurrency(estimatedCost?.estimatedCost || 0)}
              </div>
            </div>

            {isProcessing ? (
              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wide">Duration</div>
                <div className="text-lg font-bold">{formatDuration(processingDuration)}</div>
              </div>
            ) : (
              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wide">Est. Time</div>
                <div className="text-lg font-bold">{estimatedCost?.processingTime || '2-5s'}</div>
              </div>
            )}
          </div>

          <div className="mt-2 text-xs text-gray-600">
            {tierConfig.description} • Complexity: {(documentComplexity * 100).toFixed(0)}%
          </div>
        </div>

        {/* Model Tier Breakdown */}
        {showModelBreakdown && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">Model Tier Options</div>
            <div className="grid grid-cols-3 gap-2 text-xs">
              {Object.entries(TIER_CONFIG).map(([tier, config]) => (
                <div
                  key={tier}
                  className={clsx(
                    'p-2 rounded border text-center cursor-pointer transition-all',
                    currentTier === tier
                      ? `${config.bgColor} ${config.borderColor} ${config.textColor}`
                      : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                  )}
                  onClick={() => onModelTierChange?.(tier as AIModelTier)}
                >
                  <div className="font-medium">{config.name.split(' ')[2]}</div>
                  <div>${config.costPer1K.toFixed(3)}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Budget Progress */}
        {showBudgetProgress && monthlyBudget && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium text-gray-700">Monthly Budget</div>
              {budgetStatus !== 'good' && (
                <ExclamationTriangleIcon className={clsx(
                  'w-4 h-4',
                  budgetStatus === 'critical' ? 'text-red-500' : 'text-yellow-500'
                )} />
              )}
            </div>

            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={clsx(
                  'h-2 rounded-full transition-all duration-300',
                  budgetStatus === 'critical' ? 'bg-red-500' :
                  budgetStatus === 'warning' ? 'bg-yellow-500' : 'bg-green-500'
                )}
                style={{ width: `${budgetProgress}%` }}
              />
            </div>

            <div className="flex justify-between text-xs text-gray-600">
              <span>{formatCurrency(currentMonthlySpend)} used</span>
              <span>{formatCurrency(monthlyBudget - currentMonthlySpend)} remaining</span>
            </div>
          </div>
        )}

        {/* Processing Operations (if active) */}
        {isProcessing && session && session.operations.length > 0 && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">Processing Operations</div>
            <div className="max-h-32 overflow-y-auto space-y-1">
              {session.operations.slice(-5).map((operation) => (
                <div key={operation.id} className="flex items-center justify-between text-xs p-2 bg-gray-50 rounded">
                  <div className="flex items-center space-x-2">
                    <div className={clsx(
                      'w-2 h-2 rounded-full',
                      operation.status === 'completed' ? 'bg-green-400' :
                      operation.status === 'processing' ? 'bg-blue-400 animate-pulse' : 'bg-red-400'
                    )} />
                    <span>{operation.type}</span>
                    <span className={clsx('px-1 rounded text-xs', TIER_CONFIG[operation.tier].textColor)}>
                      {operation.tier}
                    </span>
                  </div>
                  <span className="font-medium">{formatCurrency(operation.cost)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}