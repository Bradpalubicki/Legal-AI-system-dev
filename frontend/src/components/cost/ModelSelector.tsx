'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'
import { Button } from '../ui/Button'
import {
  CpuChipIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  LightBulbIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'
import { clsx } from 'clsx'

export type AIModelTier = 'haiku' | 'sonnet' | 'opus'

interface ModelCapabilities {
  tier: AIModelTier
  name: string
  description: string
  costPer1K: number
  processingSpeed: string
  strengths: string[]
  limitations: string[]
  bestFor: string[]
  color: string
  bgColor: string
  borderColor: string
  textColor: string
}

interface ModelRecommendation {
  recommendedTier: AIModelTier
  confidence: number
  reasoning: string
  alternativeTiers: {
    tier: AIModelTier
    reason: string
    tradeoff: string
  }[]
}

interface ModelSelectorProps {
  // Current selection and recommendation
  selectedTier?: AIModelTier
  recommendedTier?: AIModelTier
  recommendation?: ModelRecommendation

  // Document context
  documentType?: string
  taskType?: string
  complexity?: number
  urgency?: 'low' | 'normal' | 'high' | 'critical'

  // User preferences and constraints
  budgetConstraint?: number
  qualityRequirement?: 'minimum' | 'standard' | 'high' | 'critical'
  userOverride?: boolean

  // Display options
  variant?: 'selector' | 'comparison' | 'recommendation'
  showCostProjection?: boolean
  showPerformanceMetrics?: boolean
  allowOverride?: boolean

  // Callbacks
  onTierChange?: (tier: AIModelTier, reason: string) => void
  onOverrideToggle?: (enabled: boolean) => void
  onRecommendationRequest?: () => void
}

const MODEL_CAPABILITIES: Record<AIModelTier, ModelCapabilities> = {
  haiku: {
    tier: 'haiku',
    name: 'Claude 3 Haiku',
    description: 'Fast, efficient processing for routine tasks',
    costPer1K: 0.01,
    processingSpeed: '2-5 seconds',
    strengths: [
      'Extremely fast processing',
      'Cost-effective for high volume',
      'Good for structured data extraction',
      'Reliable for classification tasks'
    ],
    limitations: [
      'Limited complex reasoning',
      'May miss nuanced legal concepts',
      'Less effective for strategy analysis'
    ],
    bestFor: [
      'Document classification',
      'Date and deadline extraction',
      'Simple pattern recognition',
      'Routine data processing'
    ],
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800'
  },
  sonnet: {
    tier: 'sonnet',
    name: 'Claude 3 Sonnet',
    description: 'Balanced performance for comprehensive analysis',
    costPer1K: 0.15,
    processingSpeed: '10-30 seconds',
    strengths: [
      'Strong legal reasoning',
      'Comprehensive analysis',
      'Good cost-performance balance',
      'Handles complex documents well'
    ],
    limitations: [
      'Slower than Haiku',
      'Higher cost for simple tasks',
      'May not catch all edge cases'
    ],
    bestFor: [
      'Contract analysis',
      'Legal document review',
      'Risk assessment',
      'Standard legal research'
    ],
    color: 'yellow',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-800'
  },
  opus: {
    tier: 'opus',
    name: 'Claude 3 Opus',
    description: 'Premium analysis for critical legal work',
    costPer1K: 0.75,
    processingSpeed: '30-90 seconds',
    strengths: [
      'Exceptional legal reasoning',
      'Comprehensive risk analysis',
      'Handles complex edge cases',
      'Highest quality output'
    ],
    limitations: [
      'Highest cost',
      'Slower processing',
      'May be overkill for simple tasks'
    ],
    bestFor: [
      'Litigation strategy',
      'Complex contract negotiation',
      'High-stakes legal analysis',
      'Comprehensive case review'
    ],
    color: 'red',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800'
  }
}

export default function ModelSelector({
  selectedTier = 'sonnet',
  recommendedTier,
  recommendation,
  documentType = 'Legal Document',
  taskType = 'analysis',
  complexity = 0.5,
  urgency = 'normal',
  budgetConstraint,
  qualityRequirement = 'standard',
  userOverride = false,
  variant = 'selector',
  showCostProjection = true,
  showPerformanceMetrics = true,
  allowOverride = true,
  onTierChange,
  onOverrideToggle,
  onRecommendationRequest
}: ModelSelectorProps) {
  const [expandedTier, setExpandedTier] = useState<AIModelTier | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const currentModel = MODEL_CAPABILITIES[selectedTier]
  const recommendedModel = recommendedTier ? MODEL_CAPABILITIES[recommendedTier] : null

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 3,
      maximumFractionDigits: 3
    }).format(amount)
  }

  const getComplexityColor = (complexity: number) => {
    if (complexity < 0.3) return 'text-green-600'
    if (complexity < 0.7) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getUrgencyIcon = (urgency: string) => {
    switch (urgency) {
      case 'critical':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />
      case 'high':
        return <ExclamationTriangleIcon className="w-4 h-4 text-yellow-500" />
      default:
        return <InformationCircleIcon className="w-4 h-4 text-blue-500" />
    }
  }

  const handleTierSelection = (tier: AIModelTier, reason: string) => {
    onTierChange?.(tier, reason)
  }

  if (variant === 'recommendation' && recommendation) {
    return (
      <Card variant="elevated" className="w-full">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <LightBulbIcon className="w-5 h-5 text-blue-500" />
            <span>AI Model Recommendation</span>
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Recommended Model */}
          <div className={clsx(
            'p-4 rounded-lg border-2',
            MODEL_CAPABILITIES[recommendation.recommendedTier].bgColor,
            MODEL_CAPABILITIES[recommendation.recommendedTier].borderColor
          )}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <CheckCircleIcon className="w-5 h-5 text-green-500" />
                <span className="font-semibold">
                  {MODEL_CAPABILITIES[recommendation.recommendedTier].name}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                {recommendation.confidence}% confidence
              </div>
            </div>

            <p className="text-sm text-gray-700 mb-3">{recommendation.reasoning}</p>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Estimated Cost: </span>
                {formatCurrency(MODEL_CAPABILITIES[recommendation.recommendedTier].costPer1K)}
              </div>
              <div>
                <span className="font-medium">Processing Time: </span>
                {MODEL_CAPABILITIES[recommendation.recommendedTier].processingSpeed}
              </div>
            </div>
          </div>

          {/* Alternative Options */}
          {recommendation.alternativeTiers.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">Alternative Options</h4>
              {recommendation.alternativeTiers.map((alt) => (
                <div key={alt.tier} className="p-3 bg-gray-50 rounded border">
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-medium">{MODEL_CAPABILITIES[alt.tier].name}</span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTierSelection(alt.tier, alt.reason)}
                    >
                      Select
                    </Button>
                  </div>
                  <p className="text-xs text-gray-600 mb-1">{alt.reason}</p>
                  <p className="text-xs text-gray-500">{alt.tradeoff}</p>
                </div>
              ))}
            </div>
          )}

          <Button
            onClick={() => handleTierSelection(recommendation.recommendedTier, 'accepted_recommendation')}
            className="w-full"
          >
            Use Recommended Model
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (variant === 'comparison') {
    return (
      <Card variant="elevated" className="w-full">
        <CardHeader>
          <CardTitle>AI Model Comparison</CardTitle>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {Object.values(MODEL_CAPABILITIES).map((model) => (
              <div
                key={model.tier}
                className={clsx(
                  'p-4 rounded-lg border-2 cursor-pointer transition-all',
                  selectedTier === model.tier
                    ? `${model.bgColor} ${model.borderColor} ring-2 ring-blue-300`
                    : 'bg-white border-gray-200 hover:border-gray-300',
                  recommendedTier === model.tier && 'ring-2 ring-green-300'
                )}
                onClick={() => handleTierSelection(model.tier, 'user_selection')}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">{model.name}</span>
                  {selectedTier === model.tier && (
                    <CheckCircleIcon className="w-5 h-5 text-blue-500" />
                  )}
                  {recommendedTier === model.tier && selectedTier !== model.tier && (
                    <LightBulbIcon className="w-5 h-5 text-green-500" />
                  )}
                </div>

                <p className="text-sm text-gray-600 mb-3">{model.description}</p>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span>Cost:</span>
                    <span className="font-medium">{formatCurrency(model.costPer1K)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Speed:</span>
                    <span>{model.processingSpeed}</span>
                  </div>
                </div>

                {expandedTier === model.tier && (
                  <div className="mt-3 pt-3 border-t border-gray-200 space-y-2 text-xs">
                    <div>
                      <span className="font-medium text-green-600">Strengths:</span>
                      <ul className="list-disc list-inside text-gray-600">
                        {model.strengths.slice(0, 2).map((strength, idx) => (
                          <li key={idx}>{strength}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <span className="font-medium text-amber-600">Best for:</span>
                      <ul className="list-disc list-inside text-gray-600">
                        {model.bestFor.slice(0, 2).map((use, idx) => (
                          <li key={idx}>{use}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                <button
                  className="text-xs text-blue-600 hover:text-blue-800 mt-2"
                  onClick={(e) => {
                    e.stopPropagation()
                    setExpandedTier(expandedTier === model.tier ? null : model.tier)
                  }}
                >
                  {expandedTier === model.tier ? 'Show less' : 'Show details'}
                </button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Default selector variant
  return (
    <Card variant="elevated" className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CpuChipIcon className="w-5 h-5" />
            <span>AI Model Selection</span>
          </div>
          {allowOverride && (
            <div className="flex items-center space-x-2">
              <label className="text-sm text-gray-600">Manual Override</label>
              <button
                onClick={() => onOverrideToggle?.(!userOverride)}
                className={clsx(
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                  userOverride ? 'bg-blue-600' : 'bg-gray-200'
                )}
              >
                <span
                  className={clsx(
                    'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                    userOverride ? 'translate-x-6' : 'translate-x-1'
                  )}
                />
              </button>
            </div>
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Context Information */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-3 bg-gray-50 rounded">
          <div>
            <div className="text-xs text-gray-500 uppercase">Document</div>
            <div className="text-sm font-medium">{documentType}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500 uppercase">Task</div>
            <div className="text-sm font-medium">{taskType}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500 uppercase">Complexity</div>
            <div className={clsx('text-sm font-medium', getComplexityColor(complexity))}>
              {(complexity * 100).toFixed(0)}%
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 uppercase">Urgency</div>
            <div className="flex items-center space-x-1">
              {getUrgencyIcon(urgency)}
              <span className="text-sm font-medium capitalize">{urgency}</span>
            </div>
          </div>
        </div>

        {/* Current Selection */}
        <div className={clsx(
          'p-4 rounded-lg border-2',
          currentModel.bgColor,
          currentModel.borderColor
        )}>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full" />
              <span className="font-semibold">Selected: {currentModel.name}</span>
            </div>
            {recommendedModel && selectedTier !== recommendedTier && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleTierSelection(recommendedTier!, 'accepted_recommendation')}
              >
                Use Recommended
              </Button>
            )}
          </div>

          <p className="text-sm text-gray-700 mb-3">{currentModel.description}</p>

          {showCostProjection && (
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Estimated Cost: </span>
                <span className="font-semibold">{formatCurrency(currentModel.costPer1K)}</span>
              </div>
              <div>
                <span className="text-gray-600">Processing Time: </span>
                <span className="font-semibold">{currentModel.processingSpeed}</span>
              </div>
            </div>
          )}
        </div>

        {/* Recommendation Alert */}
        {recommendedModel && selectedTier !== recommendedTier && (
          <div className="p-3 bg-blue-50 border border-blue-200 rounded flex items-start space-x-2">
            <LightBulbIcon className="w-5 h-5 text-blue-500 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-blue-800">
                {recommendedModel.name} is recommended for this task
              </div>
              <div className="text-xs text-blue-600 mt-1">
                Based on document complexity and task requirements
              </div>
            </div>
          </div>
        )}

        {/* Model Options */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Available Models</span>
            <button
              onClick={onRecommendationRequest}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              Get Recommendation
            </button>
          </div>

          <div className="grid grid-cols-1 gap-2">
            {Object.values(MODEL_CAPABILITIES).map((model) => (
              <button
                key={model.tier}
                onClick={() => handleTierSelection(model.tier, 'user_selection')}
                className={clsx(
                  'p-3 rounded border text-left transition-all',
                  selectedTier === model.tier
                    ? `${model.bgColor} ${model.borderColor} ring-1 ring-blue-300`
                    : 'bg-white border-gray-200 hover:border-gray-300',
                  userOverride || selectedTier === model.tier ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
                )}
                disabled={!userOverride && selectedTier !== model.tier}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {selectedTier === model.tier && (
                      <CheckCircleIcon className="w-4 h-4 text-blue-500" />
                    )}
                    {recommendedTier === model.tier && selectedTier !== model.tier && (
                      <ShieldCheckIcon className="w-4 h-4 text-green-500" />
                    )}
                    <span className="font-medium">{model.name}</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    {formatCurrency(model.costPer1K)}
                  </div>
                </div>

                {showPerformanceMetrics && (
                  <div className="mt-1 text-xs text-gray-500">
                    {model.processingSpeed} • Best for: {model.bestFor[0]}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Advanced Options */}
        {showAdvanced && (
          <div className="space-y-2">
            <div className="text-sm font-medium text-gray-700">Quality Requirements</div>
            <div className="grid grid-cols-4 gap-2">
              {['minimum', 'standard', 'high', 'critical'].map((level) => (
                <button
                  key={level}
                  className={clsx(
                    'p-2 rounded text-xs border transition-all',
                    qualityRequirement === level
                      ? 'bg-blue-100 border-blue-300 text-blue-800'
                      : 'bg-gray-50 border-gray-200 text-gray-600 hover:bg-gray-100'
                  )}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-gray-600 hover:text-gray-800"
        >
          {showAdvanced ? 'Hide' : 'Show'} Advanced Options
        </button>
      </CardContent>
    </Card>
  )
}