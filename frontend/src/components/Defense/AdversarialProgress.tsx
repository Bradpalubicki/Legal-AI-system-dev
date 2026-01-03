'use client';

import React, { useEffect, useState } from 'react';
import { Swords, Loader2, AlertCircle, CheckCircle, Lock } from 'lucide-react';

interface AdversarialProgressProps {
  simulationId?: string;
  isActive: boolean;
  progress: number;
  counterCount: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'disabled';
  estimatedTimeRemaining?: number;
  onComplete?: () => void;
  isPaidFeature?: boolean;
}

const AdversarialProgress: React.FC<AdversarialProgressProps> = ({
  simulationId,
  isActive,
  progress,
  counterCount,
  status,
  estimatedTimeRemaining,
  onComplete,
  isPaidFeature = true
}) => {
  const [dots, setDots] = useState('');

  // Animate dots
  useEffect(() => {
    if (status === 'running') {
      const interval = setInterval(() => {
        setDots(prev => (prev.length >= 3 ? '' : prev + '.'));
      }, 500);
      return () => clearInterval(interval);
    }
  }, [status]);

  // Call onComplete when simulation finishes
  useEffect(() => {
    if (status === 'completed' && onComplete) {
      onComplete();
    }
  }, [status, onComplete]);

  // Don't render if not active and not disabled
  if (!isActive && status !== 'disabled') return null;

  // Disabled state - show upgrade prompt
  if (status === 'disabled') {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mt-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gray-100 rounded-full">
            <Lock className="h-4 w-4 text-gray-500" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium text-gray-700">Opposing Counsel Analysis</p>
            <p className="text-xs text-gray-500">
              Upgrade to Basic or higher to see what arguments opposing counsel will likely make
            </p>
          </div>
          <a
            href="/settings?tab=subscription"
            className="text-xs font-medium text-teal-600 hover:text-teal-700"
          >
            Upgrade
          </a>
        </div>
      </div>
    );
  }

  // Get status icon
  const getStatusIcon = () => {
    switch (status) {
      case 'pending':
        return <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />;
      case 'running':
        return <Swords className="h-4 w-4 text-amber-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Swords className="h-4 w-4 text-gray-400" />;
    }
  };

  // Get status text
  const getStatusText = () => {
    switch (status) {
      case 'pending':
        return 'Preparing adversarial analysis...';
      case 'running':
        return `Analyzing opposing arguments${dots}`;
      case 'completed':
        return 'Analysis complete!';
      case 'failed':
        return 'Analysis failed - click to retry';
      default:
        return 'Waiting to start...';
    }
  };

  // Get progress bar color
  const getProgressColor = () => {
    switch (status) {
      case 'running':
        return 'bg-amber-500';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-300';
    }
  };

  // Format time remaining
  const formatTimeRemaining = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`;
  };

  return (
    <div className={`border rounded-lg p-4 mt-4 ${
      status === 'running' ? 'bg-amber-50 border-amber-200' :
      status === 'completed' ? 'bg-green-50 border-green-200' :
      status === 'failed' ? 'bg-red-50 border-red-200' :
      'bg-gray-50 border-gray-200'
    }`}>
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-full ${
          status === 'running' ? 'bg-amber-100' :
          status === 'completed' ? 'bg-green-100' :
          status === 'failed' ? 'bg-red-100' :
          'bg-gray-100'
        }`}>
          {getStatusIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <p className={`text-sm font-medium ${
              status === 'running' ? 'text-amber-800' :
              status === 'completed' ? 'text-green-800' :
              status === 'failed' ? 'text-red-800' :
              'text-gray-700'
            }`}>
              {getStatusText()}
            </p>
            <span className="text-xs text-gray-500">
              {counterCount > 0 && `${counterCount} counter${counterCount !== 1 ? 's' : ''} found`}
            </span>
          </div>

          {/* Progress Bar */}
          <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${getProgressColor()}`}
              style={{ width: `${Math.min(progress, 100)}%` }}
            />
          </div>

          {/* Time Remaining */}
          {status === 'running' && estimatedTimeRemaining !== undefined && estimatedTimeRemaining > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Est. {formatTimeRemaining(estimatedTimeRemaining)} remaining
            </p>
          )}
        </div>
      </div>

      {/* Completion Message */}
      {status === 'completed' && (
        <p className="text-xs text-green-700 mt-2 ml-11">
          View the counter-argument matrix below to prepare your rebuttals.
        </p>
      )}

      {/* Error Message */}
      {status === 'failed' && (
        <p className="text-xs text-red-700 mt-2 ml-11">
          Something went wrong. The analysis will be retried automatically.
        </p>
      )}
    </div>
  );
};

export default AdversarialProgress;
