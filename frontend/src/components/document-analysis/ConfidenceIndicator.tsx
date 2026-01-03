'use client';

import React from 'react';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Brain,
  Info,
  HelpCircle
} from 'lucide-react';

interface ConfidenceIndicatorProps {
  confidence: number;
  context?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showTooltip?: boolean;
  className?: string;
}

const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  confidence,
  context = 'extraction',
  size = 'md',
  showLabel = true,
  showTooltip = true,
  className = ''
}) => {
  const getConfidenceLevel = (score: number) => {
    if (score >= 0.9) return 'excellent';
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    if (score >= 0.4) return 'low';
    return 'very_low';
  };

  const getConfidenceConfig = (level: string) => {
    switch (level) {
      case 'excellent':
        return {
          color: 'text-green-700 bg-green-100 border-green-300',
          icon: CheckCircle,
          label: 'Excellent',
          description: 'Very high AI confidence - likely accurate but verify',
          warningLevel: 'minimal'
        };
      case 'high':
        return {
          color: 'text-success-700 bg-success-100 border-success-300',
          icon: CheckCircle,
          label: 'High Confidence',
          description: 'High AI confidence - review recommended',
          warningLevel: 'low'
        };
      case 'medium':
        return {
          color: 'text-warning-700 bg-warning-100 border-warning-300',
          icon: AlertTriangle,
          label: 'Medium Confidence',
          description: 'Moderate AI confidence - careful review required',
          warningLevel: 'medium'
        };
      case 'low':
        return {
          color: 'text-error-700 bg-error-100 border-error-300',
          icon: XCircle,
          label: 'Low Confidence',
          description: 'Low AI confidence - thorough verification essential',
          warningLevel: 'high'
        };
      case 'very_low':
        return {
          color: 'text-red-700 bg-red-100 border-red-300',
          icon: XCircle,
          label: 'Very Low',
          description: 'Very low AI confidence - likely inaccurate, manual review critical',
          warningLevel: 'critical'
        };
      default:
        return {
          color: 'text-gray-700 bg-gray-100 border-gray-300',
          icon: HelpCircle,
          label: 'Unknown',
          description: 'Confidence score unavailable',
          warningLevel: 'unknown'
        };
    }
  };

  const getSizeConfig = (size: string) => {
    switch (size) {
      case 'sm':
        return {
          container: 'px-2 py-1 text-xs',
          icon: 'h-3 w-3',
          text: 'text-xs'
        };
      case 'lg':
        return {
          container: 'px-3 py-2 text-base',
          icon: 'h-5 w-5',
          text: 'text-base'
        };
      default:
        return {
          container: 'px-2 py-1 text-sm',
          icon: 'h-4 w-4',
          text: 'text-sm'
        };
    }
  };

  const level = getConfidenceLevel(confidence);
  const config = getConfidenceConfig(level);
  const sizeConfig = getSizeConfig(size);
  const IconComponent = config.icon;

  const getVerificationGuidance = (level: string, context: string) => {
    const baseGuidance = {
      excellent: `High reliability ${context} - spot check recommended`,
      high: `Good reliability ${context} - standard review advised`,
      medium: `Moderate reliability ${context} - careful verification needed`,
      low: `Poor reliability ${context} - thorough manual review required`,
      very_low: `Unreliable ${context} - independent verification essential`
    };

    return baseGuidance[level as keyof typeof baseGuidance] || `Review ${context} carefully`;
  };

  return (
    <div className={`inline-flex items-center space-x-1 ${className}`}>
      <div 
        className={`
          inline-flex items-center space-x-1 rounded border font-medium
          ${config.color} ${sizeConfig.container}
        `}
        title={showTooltip ? config.description : undefined}
      >
        <IconComponent className={sizeConfig.icon} />
        {showLabel && (
          <span className={sizeConfig.text}>
            {config.label}
          </span>
        )}
        <span className={`font-mono ${sizeConfig.text}`}>
          {(confidence * 100).toFixed(0)}%
        </span>
      </div>

      {showTooltip && size !== 'sm' && (
        <div className="group relative">
          <Info className="h-3 w-3 text-gray-400 hover:text-gray-600 cursor-help" />
          <div className="invisible group-hover:visible absolute left-0 top-full mt-1 w-64 p-2 bg-gray-900 text-white text-xs rounded shadow-lg z-10">
            <p className="mb-1 font-medium">{config.description}</p>
            <p className="text-gray-300">{getVerificationGuidance(level, context)}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfidenceIndicator;