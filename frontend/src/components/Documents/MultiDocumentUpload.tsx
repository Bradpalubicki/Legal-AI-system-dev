/**
 * Multi-Document Upload Component
 * Supports multiple file uploads with drag-and-drop, progress tracking, and queue management
 */

'use client';

import React, { useState, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { API_CONFIG } from '../../config/api';
import {
  Upload,
  FileText,
  Loader2,
  CheckCircle,
  XCircle,
  X,
  AlertCircle,
  Trash2,
  RotateCcw,
  Brain,
  ShieldCheck
} from 'lucide-react';
import { toast } from 'sonner';
import { useDocuments } from '@/contexts/DocumentContext';

// Helper to get auth token
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('accessToken');
  }
  return null;
};

// Helper to get auth headers for JSON requests
const getAuthHeaders = (): HeadersInit => {
  const token = getAuthToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// Helper to get auth headers for FormData uploads (no Content-Type - browser sets it with boundary)
const getUploadAuthHeaders = (): HeadersInit => {
  const token = getAuthToken();
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// Helper to format time
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

// File upload status types
type FileStatus = 'pending' | 'uploading' | 'analyzing' | 'complete' | 'error' | 'cancelled';

interface UploadFile {
  id: string;
  file: File;
  status: FileStatus;
  progress: number;
  error?: string;
  documentId?: string;
  analysis?: any;
  jobId?: string;
  stageTitle?: string;
  stageDescription?: string;
  elapsedSeconds?: number;
  estimatedRemainingSeconds?: number;
}

interface MultiDocumentUploadProps {
  maxConcurrentUploads?: number;
  maxFileSize?: number; // in MB
  acceptedFileTypes?: string[];
  onUploadComplete?: (files: UploadFile[]) => void;
}

export function MultiDocumentUpload({
  maxConcurrentUploads = 3,
  maxFileSize = 50, // 50MB default
  acceptedFileTypes = ['.pdf', '.doc', '.docx', '.txt'],
  onUploadComplete
}: MultiDocumentUploadProps) {
  const { sessionId, addDocument } = useDocuments();
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [activeUploads, setActiveUploads] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const dragCounterRef = useRef(0);

  // Generate unique ID for file
  const generateFileId = () => `file-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  // Validate file
  const validateFile = (file: File): { valid: boolean; error?: string } => {
    // Check file size
    const fileSizeMB = file.size / (1024 * 1024);
    if (fileSizeMB > maxFileSize) {
      return { valid: false, error: `File exceeds ${maxFileSize}MB limit` };
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!acceptedFileTypes.some(type => fileExtension === type.toLowerCase())) {
      return { valid: false, error: `File type not supported. Accepted: ${acceptedFileTypes.join(', ')}` };
    }

    return { valid: true };
  };

  // Add files to upload queue
  const addFilesToQueue = (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const newUploadFiles: UploadFile[] = [];

    fileArray.forEach(file => {
      const validation = validateFile(file);

      if (validation.valid) {
        newUploadFiles.push({
          id: generateFileId(),
          file,
          status: 'pending',
          progress: 0
        });
      } else {
        toast.error(`${file.name}: ${validation.error}`);
      }
    });

    if (newUploadFiles.length > 0) {
      setUploadFiles(prev => [...prev, ...newUploadFiles]);
      toast.success(`Added ${newUploadFiles.length} file(s) to upload queue`);

      // Start processing queue
      processQueue(newUploadFiles);
    }
  };

  // File input change handler
  const handleFileInput = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      addFilesToQueue(files);
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Drag and drop handlers
  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounterRef.current = 0;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      addFilesToQueue(files);
    }
  };

  // Update file status
  const updateFileStatus = (fileId: string, updates: Partial<UploadFile>) => {
    setUploadFiles(prev =>
      prev.map(f => f.id === fileId ? { ...f, ...updates } : f)
    );
  };

  // Process upload queue with concurrency control
  const processQueue = useCallback(async (newFiles: UploadFile[]) => {
    // Get all pending files
    const getPendingFiles = () => {
      return uploadFiles.concat(newFiles).filter(f => f.status === 'pending');
    };

    let pendingFiles = getPendingFiles();
    const inProgress = new Set<string>();

    while (pendingFiles.length > 0 || inProgress.size > 0) {
      // Wait if we've hit the concurrent upload limit
      if (inProgress.size >= maxConcurrentUploads) {
        await new Promise(resolve => setTimeout(resolve, 500));
        continue;
      }

      // Get next file to upload (that's not already in progress)
      const fileToUpload = pendingFiles.find(f => !inProgress.has(f.id));

      if (fileToUpload) {
        inProgress.add(fileToUpload.id);

        // Upload file and remove from in-progress when done
        uploadFile(fileToUpload).finally(() => {
          inProgress.delete(fileToUpload.id);
        });
      }

      // Small delay before checking for next file
      await new Promise(resolve => setTimeout(resolve, 100));

      // Refresh pending files list
      pendingFiles = getPendingFiles();
    }
  }, [uploadFiles, activeUploads, maxConcurrentUploads]);

  // Upload single file with async analysis and polling
  const uploadFile = async (uploadFile: UploadFile) => {
    const { id, file } = uploadFile;
    const POLL_INTERVAL = 2000; // 2 seconds
    const MAX_POLL_TIME = 10 * 60 * 1000; // 10 minutes max

    try {
      // Increment active uploads counter
      setActiveUploads(prev => prev + 1);

      // Update status to uploading
      updateFileStatus(id, { status: 'uploading', progress: 5, stageTitle: 'Extracting Text' });

      // Step 1: Extract text from document
      const formData = new FormData();
      formData.append('file', file);

      const extractResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/extract-text`, {
        method: 'POST',
        headers: getUploadAuthHeaders(),
        body: formData
      });

      if (!extractResponse.ok) {
        throw new Error('Failed to extract text from document');
      }

      const extractData = await extractResponse.json();
      const documentText = extractData.extracted_text || extractData.text || '';

      // Update progress - text extracted
      updateFileStatus(id, {
        progress: 10,
        status: 'analyzing',
        stageTitle: 'Starting AI Analysis',
        stageDescription: 'Initializing multi-layer verification...'
      });

      // Step 2: Start ASYNC analysis with the async endpoint
      console.log(`[MultiDocUpload] Starting async analysis for ${file.name}`);
      const analyzeResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/analyze-text-async`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          text: documentText,
          filename: file.name,
          session_id: sessionId,
          include_operational_details: true,
          include_financial_details: true
        })
      });

      if (!analyzeResponse.ok) {
        const errorData = await analyzeResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to start document analysis');
      }

      const asyncData = await analyzeResponse.json();
      const jobId = asyncData.job_id;
      console.log(`[MultiDocUpload] Got job_id: ${jobId} for ${file.name}`);

      // Store job ID in file state
      updateFileStatus(id, { jobId });

      // Step 3: Poll for progress until complete or failed
      const startTime = Date.now();
      let analysisData: any = null;

      while (Date.now() - startTime < MAX_POLL_TIME) {
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));

        try {
          const progressResponse = await fetch(
            `${API_CONFIG.BASE_URL}/api/v1/documents/analysis-progress/${jobId}`,
            { headers: getAuthHeaders() }
          );

          if (!progressResponse.ok) {
            // Job might not be registered yet, keep polling
            if (progressResponse.status === 404) {
              console.log(`[MultiDocUpload] Job ${jobId} not found yet, continuing...`);
              continue;
            }
            throw new Error('Failed to fetch analysis progress');
          }

          const progressData = await progressResponse.json();
          console.log(`[MultiDocUpload] Progress for ${file.name}:`, {
            stage: progressData.stage,
            progress: progressData.progress,
            is_complete: progressData.is_complete
          });

          // Update file status with real progress from backend
          updateFileStatus(id, {
            progress: Math.max(10, progressData.progress), // Minimum 10% since we extracted text
            stageTitle: progressData.stage_title || 'Analyzing',
            stageDescription: progressData.stage_description || progressData.current_stage_detail || '',
            elapsedSeconds: progressData.elapsed_seconds,
            estimatedRemainingSeconds: progressData.estimated_remaining_seconds
          });

          // Check if failed
          if (progressData.is_failed) {
            throw new Error(progressData.error || 'Analysis failed');
          }

          // Check if complete
          if (progressData.is_complete) {
            console.log(`[MultiDocUpload] Analysis complete for ${file.name}, fetching result...`);

            // Fetch final result
            const resultResponse = await fetch(
              `${API_CONFIG.BASE_URL}/api/v1/documents/analysis-result/${jobId}`,
              { headers: getAuthHeaders() }
            );

            if (resultResponse.ok) {
              analysisData = await resultResponse.json();
              console.log(`[MultiDocUpload] Got analysis result for ${file.name}`);
              break;
            } else {
              throw new Error('Failed to fetch analysis result');
            }
          }
        } catch (pollError: any) {
          console.error(`[MultiDocUpload] Poll error for ${file.name}:`, pollError);
          // If it's a fatal error, rethrow. Otherwise continue polling.
          if (pollError.message.includes('Analysis failed')) {
            throw pollError;
          }
        }
      }

      // Check if we timed out
      if (!analysisData) {
        throw new Error('Analysis timed out after 10 minutes');
      }

      // Transform financial data into keyFigures format
      const keyFigures: Array<{ label: string; value: string }> = [];

      // Add amount_claimed if exists
      if (analysisData.amount_claimed) {
        keyFigures.push({
          label: 'Total Amount',
          value: analysisData.amount_claimed
        });
      }

      // Add individual financial_amounts if exists - check both old and new field names
      const financialAmounts = analysisData.all_financial_amounts ||
                               analysisData.financial_amounts ||
                               [];
      if (Array.isArray(financialAmounts)) {
        financialAmounts.forEach((item: any) => {
          if (item.amount && item.description) {
            keyFigures.push({
              label: item.description,
              value: item.amount
            });
          }
        });
      }

      // Add any other numerical data from analysis
      if (analysisData.case_number) {
        keyFigures.push({
          label: 'Case Number',
          value: analysisData.case_number
        });
      }

      // Create document object
      const newDocument = {
        id: analysisData.document_id || crypto.randomUUID(),
        fileName: file.name,
        fileType: file.type || 'application/pdf',
        uploadDate: new Date(),
        text: documentText,
        summary: analysisData.summary,
        parties: analysisData.all_parties || analysisData.parties || [],
        importantDates: analysisData.all_dates || analysisData.key_dates || [],
        keyFigures: keyFigures.length > 0 ? keyFigures : undefined,
        keywords: analysisData.key_terms,
        analysis: analysisData
      };

      // Add to document context
      addDocument(newDocument);

      // Mark as complete
      updateFileStatus(id, {
        status: 'complete',
        progress: 100,
        documentId: newDocument.id,
        analysis: analysisData,
        stageTitle: 'Complete',
        stageDescription: 'Analysis finished successfully'
      });

      toast.success(`${file.name} uploaded and analyzed successfully`);

    } catch (error: any) {
      console.error(`Upload error for ${file.name}:`, error);
      updateFileStatus(id, {
        status: 'error',
        error: error.message || 'Upload failed',
        progress: 0,
        stageTitle: 'Error',
        stageDescription: error.message
      });
      toast.error(`${file.name}: ${error.message || 'Upload failed'}`);
    } finally {
      // Decrement active uploads counter
      setActiveUploads(prev => prev - 1);
    }
  };

  // Retry failed upload
  const retryUpload = (fileId: string) => {
    const file = uploadFiles.find(f => f.id === fileId);
    if (file) {
      updateFileStatus(fileId, { status: 'pending', progress: 0, error: undefined });
      processQueue([file]);
    }
  };

  // Cancel upload
  const cancelUpload = (fileId: string) => {
    updateFileStatus(fileId, { status: 'cancelled' });
  };

  // Remove file from queue
  const removeFile = (fileId: string) => {
    setUploadFiles(prev => prev.filter(f => f.id !== fileId));
  };

  // Clear completed files
  const clearCompleted = () => {
    setUploadFiles(prev => prev.filter(f => f.status !== 'complete'));
  };

  // Clear all files
  const clearAll = () => {
    setUploadFiles([]);
  };

  // Get status icon
  const getStatusIcon = (status: FileStatus) => {
    switch (status) {
      case 'pending':
        return <FileText className="w-5 h-5 text-gray-400" />;
      case 'uploading':
      case 'analyzing':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'complete':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'error':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'cancelled':
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
      default:
        return <FileText className="w-5 h-5 text-gray-400" />;
    }
  };

  // Get status text
  const getStatusText = (file: UploadFile): string => {
    switch (file.status) {
      case 'pending':
        return 'Waiting...';
      case 'uploading':
        return 'Uploading...';
      case 'analyzing':
        return 'Analyzing with AI...';
      case 'complete':
        return 'Complete';
      case 'error':
        return file.error || 'Error';
      case 'cancelled':
        return 'Cancelled';
      default:
        return 'Unknown';
    }
  };

  // Get status color
  const getStatusColor = (status: FileStatus): string => {
    switch (status) {
      case 'uploading':
      case 'analyzing':
        return 'bg-blue-50 border-blue-200';
      case 'complete':
        return 'bg-green-50 border-green-200';
      case 'error':
        return 'bg-red-50 border-red-200';
      case 'cancelled':
        return 'bg-gray-50 border-gray-200';
      default:
        return 'bg-white border-gray-200';
    }
  };

  // Calculate statistics
  const stats = {
    total: uploadFiles.length,
    pending: uploadFiles.filter(f => f.status === 'pending').length,
    uploading: uploadFiles.filter(f => f.status === 'uploading' || f.status === 'analyzing').length,
    complete: uploadFiles.filter(f => f.status === 'complete').length,
    error: uploadFiles.filter(f => f.status === 'error').length
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Multi-Document Upload
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Drag and Drop Zone */}
          <div
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className={`relative border-4 border-dashed rounded-lg transition-all ${
              isDragging
                ? 'border-blue-600 bg-blue-50 dark:bg-slate-700 dark:border-blue-500 scale-105'
                : 'border-blue-400 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-800 dark:border-slate-600'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileInput}
              accept={acceptedFileTypes.join(',')}
              className="hidden"
              id="multi-document-upload"
            />
            <label
              htmlFor="multi-document-upload"
              className="block p-12 cursor-pointer"
            >
              <div className="flex flex-col items-center justify-center space-y-4">
                <Upload className={`w-16 h-16 ${isDragging ? 'text-blue-600 dark:text-blue-400 animate-bounce' : 'text-blue-600 dark:text-blue-400'}`} />
                <div className="text-center">
                  <p className="text-xl font-semibold text-blue-900 dark:text-slate-100">
                    {isDragging ? 'Drop files here' : 'Click to upload or drag and drop'}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-slate-400 mt-2">
                    Multiple files supported: {acceptedFileTypes.join(', ')}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-slate-500 mt-1">
                    Maximum file size: {maxFileSize}MB per file
                  </p>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-slate-400">
                  <span className="px-3 py-1 bg-blue-100 dark:bg-slate-700 text-blue-700 dark:text-blue-300 rounded-full font-medium">
                    ↑ {maxConcurrentUploads} concurrent uploads
                  </span>
                  <span className="px-3 py-1 bg-purple-100 dark:bg-slate-700 text-purple-700 dark:text-purple-300 rounded-full font-medium">
                    AI-powered analysis
                  </span>
                </div>
              </div>
            </label>
          </div>

          {/* Statistics */}
          {uploadFiles.length > 0 && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="bg-gray-50 dark:bg-slate-700 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{stats.total}</p>
                <p className="text-xs text-gray-600 dark:text-slate-400">Total Files</p>
              </div>
              <div className="bg-yellow-50 dark:bg-slate-700 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-yellow-900 dark:text-yellow-300">{stats.pending}</p>
                <p className="text-xs text-yellow-700 dark:text-yellow-400">Pending</p>
              </div>
              <div className="bg-blue-50 dark:bg-slate-700 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-blue-900 dark:text-blue-300">{stats.uploading}</p>
                <p className="text-xs text-blue-700 dark:text-blue-400">Processing</p>
              </div>
              <div className="bg-green-50 dark:bg-slate-700 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-green-900 dark:text-green-300">{stats.complete}</p>
                <p className="text-xs text-green-700 dark:text-green-400">Complete</p>
              </div>
              <div className="bg-red-50 dark:bg-slate-700 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-red-900 dark:text-red-300">{stats.error}</p>
                <p className="text-xs text-red-700 dark:text-red-400">Failed</p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {uploadFiles.length > 0 && (
            <div className="flex gap-2">
              <Button
                onClick={clearCompleted}
                variant="outline"
                size="sm"
                disabled={stats.complete === 0}
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Clear Completed ({stats.complete})
              </Button>
              <Button
                onClick={clearAll}
                variant="outline"
                size="sm"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Clear All
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upload Queue */}
      {uploadFiles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Upload Queue ({uploadFiles.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {uploadFiles.map((file) => (
                <div
                  key={file.id}
                  className={`p-4 border-2 rounded-lg transition-all ${getStatusColor(file.status)}`}
                >
                  <div className="flex items-start gap-3">
                    {/* Status Icon */}
                    <div className="flex-shrink-0 mt-1">
                      {getStatusIcon(file.status)}
                    </div>

                    {/* File Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-gray-900 truncate">
                            {file.file.name}
                          </p>
                          <p className="text-sm text-gray-600">
                            {(file.file.size / 1024 / 1024).toFixed(2)} MB • {getStatusText(file)}
                          </p>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-2 flex-shrink-0">
                          {file.status === 'error' && (
                            <Button
                              onClick={() => retryUpload(file.id)}
                              variant="ghost"
                              size="sm"
                              title="Retry upload"
                            >
                              <RotateCcw className="w-4 h-4 text-orange-600" />
                            </Button>
                          )}
                          {(file.status === 'pending' || file.status === 'uploading' || file.status === 'analyzing') && (
                            <Button
                              onClick={() => cancelUpload(file.id)}
                              variant="ghost"
                              size="sm"
                              title="Cancel upload"
                            >
                              <X className="w-4 h-4 text-red-600" />
                            </Button>
                          )}
                          {(file.status === 'complete' || file.status === 'error' || file.status === 'cancelled') && (
                            <Button
                              onClick={() => removeFile(file.id)}
                              variant="ghost"
                              size="sm"
                              title="Remove from list"
                            >
                              <Trash2 className="w-4 h-4 text-gray-600" />
                            </Button>
                          )}
                        </div>
                      </div>

                      {/* Progress Bar */}
                      {(file.status === 'uploading' || file.status === 'analyzing') && (
                        <div className="mt-3">
                          <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                            <div className="flex items-center gap-2">
                              <Brain className="w-3 h-3 text-purple-500 animate-pulse" />
                              <span className="font-medium text-purple-700">
                                {file.stageTitle || (file.status === 'uploading' ? 'Uploading...' : 'Analyzing with AI...')}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-semibold">{file.progress}%</span>
                              {file.estimatedRemainingSeconds !== undefined && file.estimatedRemainingSeconds > 0 && (
                                <span className="text-blue-600">
                                  ~{formatTime(file.estimatedRemainingSeconds)} left
                                </span>
                              )}
                            </div>
                          </div>
                          {file.stageDescription && (
                            <p className="text-xs text-gray-500 mb-1">{file.stageDescription}</p>
                          )}
                          <div className="w-full bg-gray-200 rounded-full h-2.5">
                            <div
                              className="bg-gradient-to-r from-blue-500 to-purple-600 h-2.5 rounded-full transition-all duration-500 ease-out"
                              style={{ width: `${file.progress}%` }}
                            />
                          </div>
                          {/* AI model badges */}
                          <div className="flex gap-2 mt-2">
                            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                              Claude Opus
                            </span>
                            <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
                              GPT-4o
                            </span>
                            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                              4-Layer Verification
                            </span>
                          </div>
                        </div>
                      )}

                      {/* Error Message */}
                      {file.status === 'error' && file.error && (
                        <div className="mt-2 p-2 bg-red-100 border border-red-200 rounded text-sm text-red-800">
                          {file.error}
                        </div>
                      )}

                      {/* Success Info */}
                      {file.status === 'complete' && file.analysis && (
                        <div className="mt-2 text-sm text-green-700">
                          ✓ Analysis complete: {file.analysis.summary?.substring(0, 100)}...
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {uploadFiles.length === 0 && (
        <Card className="bg-gray-50">
          <CardContent className="py-12 text-center">
            <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-lg font-medium text-gray-700">No files in queue</p>
            <p className="text-sm text-gray-500 mt-1">Upload multiple documents to get started</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
