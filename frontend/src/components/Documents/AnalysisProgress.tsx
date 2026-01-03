'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Loader2, CheckCircle, Clock, FileText, Brain, Sparkles, Upload } from 'lucide-react';

export type AnalysisStage = 'uploading' | 'extracting' | 'analyzing' | 'formatting' | 'complete' | 'error';

interface StageConfig {
  name: string;
  description: string;
  icon: React.ReactNode;
  progressStart: number;
  progressEnd: number;
  estimatedSeconds: number;
}

const STAGE_CONFIG: Record<AnalysisStage, StageConfig> = {
  uploading: {
    name: 'Uploading',
    description: 'Uploading document to server...',
    icon: <Upload className="w-5 h-5" />,
    progressStart: 0,
    progressEnd: 5,
    estimatedSeconds: 2,
  },
  extracting: {
    name: 'Extracting Text',
    description: 'Extracting text content from document...',
    icon: <FileText className="w-5 h-5" />,
    progressStart: 5,
    progressEnd: 20,
    estimatedSeconds: 5,
  },
  analyzing: {
    name: 'AI Analysis',
    description: 'AI is analyzing document content...',
    icon: <Brain className="w-5 h-5" />,
    progressStart: 20,
    progressEnd: 90,
    estimatedSeconds: 45, // Base estimate, adjusted by file size
  },
  formatting: {
    name: 'Formatting Results',
    description: 'Preparing analysis results...',
    icon: <Sparkles className="w-5 h-5" />,
    progressStart: 90,
    progressEnd: 100,
    estimatedSeconds: 2,
  },
  complete: {
    name: 'Complete',
    description: 'Analysis complete!',
    icon: <CheckCircle className="w-5 h-5 text-green-600" />,
    progressStart: 100,
    progressEnd: 100,
    estimatedSeconds: 0,
  },
  error: {
    name: 'Error',
    description: 'An error occurred',
    icon: <Loader2 className="w-5 h-5 text-red-600" />,
    progressStart: 0,
    progressEnd: 0,
    estimatedSeconds: 0,
  },
};

interface AnalysisProgressProps {
  stage: AnalysisStage;
  fileName: string;
  fileSizeBytes?: number;
  onComplete?: () => void;
  errorMessage?: string;
}

export function AnalysisProgress({
  stage,
  fileName,
  fileSizeBytes = 0,
  onComplete,
  errorMessage,
}: AnalysisProgressProps) {
  const [progress, setProgress] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [estimatedTotalSeconds, setEstimatedTotalSeconds] = useState(0);
  const [stageStartTime, setStageStartTime] = useState<number>(Date.now());

  // Calculate size-adjusted analysis time
  const getAdjustedAnalysisTime = useCallback(() => {
    // Base: 45 seconds for a 100KB document
    // Scale: +15 seconds per additional 100KB, capped at 120 seconds
    const baseTime = 45;
    const sizeInKB = fileSizeBytes / 1024;
    const additionalTime = Math.floor(sizeInKB / 100) * 15;
    return Math.min(baseTime + additionalTime, 120);
  }, [fileSizeBytes]);

  // Calculate total estimated time
  useEffect(() => {
    const adjustedAnalysisTime = getAdjustedAnalysisTime();
    const total =
      STAGE_CONFIG.uploading.estimatedSeconds +
      STAGE_CONFIG.extracting.estimatedSeconds +
      adjustedAnalysisTime +
      STAGE_CONFIG.formatting.estimatedSeconds;
    setEstimatedTotalSeconds(total);
  }, [getAdjustedAnalysisTime]);

  // Track elapsed time
  useEffect(() => {
    if (stage === 'complete' || stage === 'error') return;

    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [stage]);

  // Animate progress within current stage
  useEffect(() => {
    if (stage === 'complete') {
      setProgress(100);
      onComplete?.();
      return;
    }

    if (stage === 'error') {
      return;
    }

    const config = STAGE_CONFIG[stage];
    const adjustedTime = stage === 'analyzing'
      ? getAdjustedAnalysisTime()
      : config.estimatedSeconds;

    setStageStartTime(Date.now());

    // Animate progress from start to end of current stage
    const progressRange = config.progressEnd - config.progressStart;
    const intervalMs = 100; // Update every 100ms
    const totalIntervals = (adjustedTime * 1000) / intervalMs;
    const progressPerInterval = progressRange / totalIntervals;

    let currentProgress = config.progressStart;
    setProgress(currentProgress);

    const timer = setInterval(() => {
      currentProgress += progressPerInterval;

      // Don't exceed the stage's end progress (leave room for actual completion)
      if (currentProgress >= config.progressEnd - 2) {
        currentProgress = config.progressEnd - 2;
        clearInterval(timer);
      }

      setProgress(Math.min(currentProgress, config.progressEnd - 2));
    }, intervalMs);

    return () => clearInterval(timer);
  }, [stage, getAdjustedAnalysisTime, onComplete]);

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate remaining time estimate
  const getRemainingTime = (): number => {
    if (stage === 'complete') return 0;

    const stageConfig = STAGE_CONFIG[stage];
    const adjustedTime = stage === 'analyzing'
      ? getAdjustedAnalysisTime()
      : stageConfig.estimatedSeconds;

    // Time spent in current stage
    const timeInCurrentStage = (Date.now() - stageStartTime) / 1000;
    const remainingInCurrentStage = Math.max(0, adjustedTime - timeInCurrentStage);

    // Add time for remaining stages
    let remainingStagesTime = 0;
    const stageOrder: AnalysisStage[] = ['uploading', 'extracting', 'analyzing', 'formatting'];
    const currentIndex = stageOrder.indexOf(stage);

    for (let i = currentIndex + 1; i < stageOrder.length; i++) {
      const futureStage = stageOrder[i];
      if (futureStage === 'analyzing') {
        remainingStagesTime += getAdjustedAnalysisTime();
      } else {
        remainingStagesTime += STAGE_CONFIG[futureStage].estimatedSeconds;
      }
    }

    return remainingInCurrentStage + remainingStagesTime;
  };

  const currentConfig = STAGE_CONFIG[stage];
  const remainingTime = getRemainingTime();
  const stageOrder: AnalysisStage[] = ['uploading', 'extracting', 'analyzing', 'formatting', 'complete'];

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-gray-900 truncate max-w-[200px]">
            {fileName}
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>Elapsed: {formatTime(elapsedSeconds)}</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden mb-3">
        <div
          className={`absolute inset-y-0 left-0 transition-all duration-300 ease-out rounded-full ${
            stage === 'error'
              ? 'bg-red-500'
              : stage === 'complete'
                ? 'bg-green-500'
                : 'bg-blue-600'
          }`}
          style={{ width: `${progress}%` }}
        />
        {/* Animated shimmer effect during processing */}
        {stage !== 'complete' && stage !== 'error' && (
          <div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer"
            style={{ backgroundSize: '200% 100%' }}
          />
        )}
      </div>

      {/* Stage Info */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {stage !== 'complete' && stage !== 'error' ? (
            <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
          ) : (
            currentConfig.icon
          )}
          <div>
            <span className="text-sm font-medium text-gray-900">
              {currentConfig.name}
            </span>
            <span className="text-xs text-gray-500 ml-2">
              {Math.round(progress)}%
            </span>
          </div>
        </div>

        {stage !== 'complete' && stage !== 'error' && (
          <div className="text-xs text-gray-500">
            ~{formatTime(remainingTime)} remaining
          </div>
        )}
      </div>

      {/* Stage description */}
      <p className="text-xs text-gray-500 mt-1">
        {stage === 'error' ? errorMessage || 'An error occurred during analysis' : currentConfig.description}
      </p>

      {/* Stage indicators */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
        {stageOrder.slice(0, -1).map((s, index) => {
          const isActive = s === stage;
          const isCompleted = stageOrder.indexOf(stage) > index || stage === 'complete';
          const stageInfo = STAGE_CONFIG[s];

          return (
            <div key={s} className="flex flex-col items-center flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
                  isCompleted
                    ? 'bg-green-100 text-green-600'
                    : isActive
                      ? 'bg-blue-100 text-blue-600'
                      : 'bg-gray-100 text-gray-400'
                }`}
              >
                {isCompleted ? (
                  <CheckCircle className="w-4 h-4" />
                ) : isActive ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  stageInfo.icon
                )}
              </div>
              <span
                className={`text-[10px] mt-1 text-center ${
                  isActive ? 'text-blue-600 font-medium' : 'text-gray-400'
                }`}
              >
                {stageInfo.name}
              </span>
              {/* Connector line */}
              {index < stageOrder.length - 2 && (
                <div
                  className={`absolute h-0.5 w-[calc(25%-16px)] top-1/2 left-[calc(${
                    (index + 1) * 25
                  }%+8px)] ${
                    stageOrder.indexOf(stage) > index ? 'bg-green-300' : 'bg-gray-200'
                  }`}
                  style={{ display: 'none' }} // Hidden for now, can be styled later
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Hook to manage analysis progress state
export function useAnalysisProgress() {
  const [stage, setStage] = useState<AnalysisStage>('uploading');
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const startAnalysis = useCallback(() => {
    setIsActive(true);
    setStage('uploading');
    setError(null);
  }, []);

  const advanceToStage = useCallback((newStage: AnalysisStage) => {
    setStage(newStage);
  }, []);

  const completeAnalysis = useCallback(() => {
    setStage('complete');
    // Keep active briefly to show completion
    setTimeout(() => {
      setIsActive(false);
    }, 2000);
  }, []);

  const failAnalysis = useCallback((errorMessage: string) => {
    setStage('error');
    setError(errorMessage);
    // Keep active to show error
    setTimeout(() => {
      setIsActive(false);
    }, 5000);
  }, []);

  const reset = useCallback(() => {
    setIsActive(false);
    setStage('uploading');
    setError(null);
  }, []);

  return {
    stage,
    isActive,
    error,
    startAnalysis,
    advanceToStage,
    completeAnalysis,
    failAnalysis,
    reset,
  };
}

export default AnalysisProgress;
