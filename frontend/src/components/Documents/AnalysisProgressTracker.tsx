'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Loader2,
  CheckCircle,
  XCircle,
  Brain,
  ShieldCheck,
  Search,
  FileSearch,
  Sparkles,
  ClipboardCheck
} from 'lucide-react';
import { API_CONFIG } from '../../config/api';

// Auth helper functions
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('accessToken') || localStorage.getItem('auth_token');
  }
  return null;
};

const getAuthHeaders = (): Record<string, string> => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// Try to refresh the access token using the refresh token
const tryRefreshToken = async (): Promise<boolean> => {
  const refreshTokenValue = localStorage.getItem('refreshToken');
  if (!refreshTokenValue) {
    console.log('[ProgressTracker] No refresh token available');
    return false;
  }

  try {
    const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshTokenValue })
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('accessToken', data.access_token);
      if (data.refresh_token) {
        localStorage.setItem('refreshToken', data.refresh_token);
      }
      console.log('[ProgressTracker] Token refreshed successfully');
      return true;
    }
  } catch (err) {
    console.error('[ProgressTracker] Token refresh failed:', err);
  }
  return false;
};

interface ProgressStatus {
  job_id: string;
  document_id: string;
  filename: string;
  stage: string;
  stage_title: string;
  stage_description: string;
  progress: number;
  current_stage_detail: string;
  stages_completed: string[];
  elapsed_seconds: number;
  estimated_remaining_seconds?: number;
  estimated_total_seconds?: number;
  items_extracted: number;
  hallucinations_detected: number;
  corrections_made: number;
  confidence_score: number;
  is_complete: boolean;
  is_failed: boolean;
  error?: string;
}

interface AnalysisProgressTrackerProps {
  jobId: string;
  filename: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

// Map stages to icons
const stageIcons: Record<string, React.ReactNode> = {
  'queued': <Loader2 className="w-5 h-5 animate-spin text-gray-400" />,
  'extracting_text': <FileSearch className="w-5 h-5 text-blue-500" />,
  'layer1_extraction': <Brain className="w-5 h-5 text-purple-500" />,
  'layer1_inspection': <Search className="w-5 h-5 text-purple-400" />,
  'layer2_verification': <ShieldCheck className="w-5 h-5 text-green-500" />,
  'layer2_inspection': <Search className="w-5 h-5 text-green-400" />,
  'layer3_hallucination': <Sparkles className="w-5 h-5 text-amber-500" />,
  'layer3_inspection': <Search className="w-5 h-5 text-amber-400" />,
  'layer4_validation': <ClipboardCheck className="w-5 h-5 text-blue-500" />,
  'expert_review': <Brain className="w-5 h-5 text-indigo-500" />,
  'final_inspection': <ShieldCheck className="w-5 h-5 text-teal-500" />,
  'completed': <CheckCircle className="w-5 h-5 text-green-600" />,
  'failed': <XCircle className="w-5 h-5 text-red-600" />,
};

// All stages in order for timeline display (thorough mode - 10 stages)
const allStages = [
  { key: 'layer1_extraction', label: 'Deep Extraction (Claude Opus)', shortLabel: 'Extract', estimatedSeconds: 60 },
  { key: 'layer1_inspection', label: 'Extraction Review', shortLabel: 'Review', estimatedSeconds: 20 },
  { key: 'layer2_verification', label: 'Cross-Verification (GPT-4o)', shortLabel: 'Verify', estimatedSeconds: 25 },
  { key: 'layer2_inspection', label: 'Verification Review', shortLabel: 'Check', estimatedSeconds: 20 },
  { key: 'layer3_hallucination', label: 'Accuracy Check', shortLabel: 'Accuracy', estimatedSeconds: 5 },
  { key: 'layer3_inspection', label: 'Accuracy Review', shortLabel: 'Audit', estimatedSeconds: 20 },
  { key: 'layer4_validation', label: 'Data Merging', shortLabel: 'Merge', estimatedSeconds: 5 },
  { key: 'expert_review', label: 'Expert Analysis', shortLabel: 'Expert', estimatedSeconds: 35 },
  { key: 'final_inspection', label: 'Quality Check', shortLabel: 'Quality', estimatedSeconds: 20 },
  { key: 'completed', label: 'Complete', shortLabel: 'Done', estimatedSeconds: 0 },
];

// Total estimated time for thorough analysis (~3.5 minutes)
const TOTAL_ESTIMATED_SECONDS = allStages.reduce((sum, s) => sum + s.estimatedSeconds, 0);

// Helper function to format time
const formatTime = (seconds: number): string => {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
  }
};

export function AnalysisProgressTracker({
  jobId,
  filename,
  onComplete,
  onError
}: AnalysisProgressTrackerProps) {
  const [progress, setProgress] = useState<ProgressStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    // Check if this is a temporary job ID
    const isTempJob = jobId.startsWith('temp_');

    // For temporary job IDs, show generic "starting" progress
    if (isTempJob) {
      setProgress({
        job_id: jobId,
        document_id: '',
        filename,
        stage: 'initializing',
        stage_title: 'Initializing Analysis',
        stage_description: 'Preparing document for comprehensive AI analysis...',
        progress: 5,
        current_stage_detail: 'Starting analysis engines',
        stages_completed: [],
        elapsed_seconds: 0,
        items_extracted: 0,
        hallucinations_detected: 0,
        corrections_made: 0,
        confidence_score: 0,
        is_complete: false,
        is_failed: false
      });
      // Don't poll for temp jobs - wait for real job ID
      return;
    }

    console.log('[ProgressTracker] Starting poll for job:', jobId);

    const pollProgress = async () => {
      try {
        console.log('[ProgressTracker] Polling progress for job:', jobId);
        const response = await fetch(
          `${API_CONFIG.BASE_URL}/api/v1/documents/analysis-progress/${jobId}`,
          { headers: getAuthHeaders() }
        );

        console.log('[ProgressTracker] Poll response status:', response.status);

        if (!response.ok) {
          // Job might not exist yet or has been cleaned up
          if (response.status === 404) {
            console.log('[ProgressTracker] Job not found yet, continuing to poll');
            return; // Keep polling
          }
          // Token expired - try to refresh
          if (response.status === 401) {
            console.log('[ProgressTracker] Token expired, attempting refresh...');
            const refreshed = await tryRefreshToken();
            if (refreshed) {
              // Token refreshed, retry on next poll
              return;
            } else {
              // Refresh failed - user needs to re-login
              setError('Session expired. Please log in again.');
              onError?.('Session expired. Please log in again.');
              return;
            }
          }
          throw new Error('Failed to fetch progress');
        }

        const data: ProgressStatus = await response.json();
        console.log('[ProgressTracker] Poll response data:', {
          stage: data.stage,
          progress: data.progress,
          is_complete: data.is_complete,
          is_failed: data.is_failed,
          items_extracted: data.items_extracted
        });
        setProgress(data);

        if (data.is_complete) {
          console.log('[ProgressTracker] Analysis COMPLETE for job:', jobId);
          onComplete?.();
          return; // Stop polling
        }

        if (data.is_failed) {
          console.log('[ProgressTracker] Analysis FAILED for job:', jobId, 'Error:', data.error);
          setError(data.error || 'Analysis failed');
          onError?.(data.error || 'Analysis failed');
          return; // Stop polling
        }
      } catch (err) {
        console.error('[ProgressTracker] Progress poll error:', err);
        // Continue polling even on error
      }
    };

    // Initial poll with small delay to let backend task start
    console.log('[ProgressTracker] Starting initial poll');
    const initialPollTimeout = setTimeout(() => {
      pollProgress();
    }, 200); // Wait 200ms for backend task to register initial state

    // Poll every 1 second for responsive updates during analysis
    const interval = setInterval(pollProgress, 1000);

    return () => {
      clearTimeout(initialPollTimeout);
      clearInterval(interval);
    };
  }, [jobId, filename, onComplete, onError]);

  if (error) {
    return (
      <Card className="border-red-300 bg-red-50">
        <CardContent className="py-4">
          <div className="flex items-center gap-3">
            <XCircle className="w-6 h-6 text-red-600" />
            <div>
              <p className="font-semibold text-red-800">Analysis Failed</p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!progress) {
    return (
      <Card className="border-blue-300 bg-blue-50">
        <CardContent className="py-4">
          <div className="flex items-center gap-3">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            <div>
              <p className="font-semibold text-blue-800">Starting Analysis...</p>
              <p className="text-sm text-blue-600">Preparing {filename}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const currentStageIndex = allStages.findIndex(s => s.key === progress.stage);

  return (
    <Card className="border-blue-300 bg-gradient-to-br from-blue-50 to-indigo-50">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-lg">
          {stageIcons[progress.stage] || <Loader2 className="w-5 h-5 animate-spin" />}
          <span>{progress.stage_title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current stage description */}
        <div className="text-sm text-gray-700">
          {progress.stage_description}
          {progress.current_stage_detail && (
            <span className="block text-gray-500 mt-1">{progress.current_stage_detail}</span>
          )}
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Progress</span>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-blue-700">{progress.progress}%</span>
              {progress.estimated_remaining_seconds !== undefined && progress.estimated_remaining_seconds > 0 && (
                <span className="text-xs text-blue-600">
                  • ~{formatTime(progress.estimated_remaining_seconds)} left
                </span>
              )}
            </div>
          </div>
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-500 ease-out"
              style={{ width: `${progress.progress}%` }}
            />
          </div>
        </div>

        {/* Stage timeline */}
        <div className="flex justify-between items-center pt-2">
          {allStages.map((stage, index) => {
            const isCompleted = progress.stages_completed.includes(stage.key) ||
                               (currentStageIndex > index);
            const isCurrent = progress.stage === stage.key;

            return (
              <div key={stage.key} className="flex flex-col items-center flex-1">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  isCompleted ? 'bg-green-500 text-white' :
                  isCurrent ? 'bg-blue-500 text-white animate-pulse' :
                  'bg-gray-200 text-gray-400'
                }`}>
                  {isCompleted ? (
                    <CheckCircle className="w-5 h-5" />
                  ) : isCurrent ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <span className="text-xs">{index + 1}</span>
                  )}
                </div>
                <span className={`text-xs mt-1 text-center ${
                  isCompleted ? 'text-green-600 font-medium' :
                  isCurrent ? 'text-blue-600 font-medium' :
                  'text-gray-400'
                }`}>
                  {stage.shortLabel}
                </span>
              </div>
            );
          })}
        </div>

        {/* Stats row */}
        <div className="flex justify-between text-xs text-gray-500 pt-2 border-t">
          <div className="flex flex-col gap-0.5">
            <span>Elapsed: {formatTime(progress.elapsed_seconds)}</span>
            {progress.estimated_remaining_seconds !== undefined && progress.estimated_remaining_seconds > 0 && (
              <span className="text-blue-600 font-medium">
                ~{formatTime(progress.estimated_remaining_seconds)} remaining
              </span>
            )}
          </div>
          {progress.items_extracted > 0 && (
            <span>Items: {progress.items_extracted}</span>
          )}
          {progress.hallucinations_detected > 0 && (
            <span className="text-amber-600">
              Corrections: {progress.hallucinations_detected}
            </span>
          )}
        </div>

        {/* AI models being used */}
        <div className="flex gap-2 text-xs pt-1">
          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
            Claude Opus
          </span>
          <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full">
            GPT-4o
          </span>
          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full">
            4-Layer Verification
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
