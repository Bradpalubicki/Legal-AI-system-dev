/**
 * Enhanced Documents Tab with Multi-File Upload Support
 * Backward compatible with existing DocumentsTab but adds multiple file selection
 */

'use client';

import React, { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, FileText, Loader2, CheckCircle, Trash2, X } from 'lucide-react';
import { useDocuments } from '@/contexts/DocumentContext';
import { toast } from 'sonner';
import { NoDocumentsEmpty } from '@/components/EmptyState';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import { useConfirmDialog } from '@/components/ConfirmDialog';
import { AnalysisProgressTracker } from './AnalysisProgressTracker';

import { API_CONFIG, buildApiUrl } from '../../config/api';

// Helper to get auth token
const getAuthToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('accessToken');
  }
  return null;
};

// Helper to get auth headers
const getAuthHeaders = (): HeadersInit => {
  const token = getAuthToken();
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

interface UploadProgress {
  fileName: string;
  status: 'uploading' | 'analyzing' | 'complete' | 'error';
  progress: number;
  error?: string;
  jobId?: string;  // For progress tracking
}

export function EnhancedDocumentsTab() {
  const { documents, currentDocument, sessionId, addDocument, setCurrentDocument, removeDocument } = useDocuments();
  const [uploadQueue, setUploadQueue] = useState<UploadProgress[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { confirm, ConfirmDialog } = useConfirmDialog();

  const handleDeleteDocument = async (docId: string, docName: string) => {
    await confirm({
      title: 'Delete Document?',
      description: `Are you sure you want to delete "${docName}"? This action cannot be undone and will remove all associated analysis data.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      variant: 'danger',
      icon: <Trash2 className="w-6 h-6 text-red-600" />,
      onConfirm: async () => {
        try {
          await removeDocument(docId);
          toast.success('Document deleted', {
            description: `"${docName}" has been removed`,
            duration: 3000,
          });
        } catch (error) {
          console.error('Delete error:', error);
          toast.error('Failed to delete document', {
            description: 'Please try again',
            duration: 5000,
          });
        }
      }
    });
  };

  const updateProgress = (fileName: string, updates: Partial<UploadProgress>) => {
    setUploadQueue(prev =>
      prev.map(item => item.fileName === fileName ? { ...item, ...updates } : item)
    );
  };

  const removeFromQueue = (fileName: string) => {
    setUploadQueue(prev => prev.filter(item => item.fileName !== fileName));
  };

  const processFile = async (file: File) => {
    const fileName = file.name;
    const POLL_INTERVAL = 2000; // 2 seconds
    const MAX_POLL_TIME = 10 * 60 * 1000; // 10 minutes max

    try {
      // Add to upload queue
      setUploadQueue(prev => [...prev, {
        fileName,
        status: 'uploading',
        progress: 10
      }]);

      // Step 1: Extract text from document
      const formData = new FormData();
      formData.append('file', file);

      const extractResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/extract-text`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
      });

      if (!extractResponse.ok) {
        throw new Error('Failed to extract text from document');
      }

      const extractData = await extractResponse.json();
      const documentText = extractData.extracted_text || extractData.text || '';

      updateProgress(fileName, { progress: 15, status: 'analyzing' });

      // Step 2: Start ASYNC analysis
      console.log(`[EnhancedDocumentsTab] Starting async analysis for ${fileName}`);
      const analyzeResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/analyze-text-async`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
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
      console.log(`[EnhancedDocumentsTab] Got job_id: ${jobId} for ${fileName}`);

      // Store job ID for progress tracker component
      updateProgress(fileName, { jobId, progress: 20 });

      // Step 3: Poll for completion
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
            if (progressResponse.status === 404) {
              console.log(`[EnhancedDocumentsTab] Job ${jobId} not found yet, continuing...`);
              continue;
            }
            throw new Error('Failed to fetch analysis progress');
          }

          const progressData = await progressResponse.json();
          console.log(`[EnhancedDocumentsTab] Progress for ${fileName}:`, {
            stage: progressData.stage,
            progress: progressData.progress,
            is_complete: progressData.is_complete
          });

          // Update progress (minimum 20% since we started analysis)
          updateProgress(fileName, {
            progress: Math.max(20, progressData.progress)
          });

          if (progressData.is_failed) {
            throw new Error(progressData.error || 'Analysis failed');
          }

          if (progressData.is_complete) {
            console.log(`[EnhancedDocumentsTab] Analysis complete for ${fileName}, fetching result...`);

            const resultResponse = await fetch(
              `${API_CONFIG.BASE_URL}/api/v1/documents/analysis-result/${jobId}`,
              { headers: getAuthHeaders() }
            );

            if (resultResponse.ok) {
              analysisData = await resultResponse.json();
              console.log(`[EnhancedDocumentsTab] Got analysis result for ${fileName}`);
              break;
            } else {
              throw new Error('Failed to fetch analysis result');
            }
          }
        } catch (pollError: any) {
          console.error(`[EnhancedDocumentsTab] Poll error for ${fileName}:`, pollError);
          if (pollError.message.includes('Analysis failed')) {
            throw pollError;
          }
        }
      }

      if (!analysisData) {
        throw new Error('Analysis timed out after 10 minutes');
      }

      updateProgress(fileName, { progress: 95 });

      // Create document object with properly normalized data
      // Get keyFigures from various possible sources
      const rawKeyFigures = Array.isArray(analysisData.all_financial_amounts) ? analysisData.all_financial_amounts :
                           Array.isArray(analysisData.financial_amounts) ? analysisData.financial_amounts :
                           Array.isArray(analysisData.key_figures) ? analysisData.key_figures : [];

      // Normalize keyFigures to standard format
      const normalizedKeyFigures = rawKeyFigures.map((f: any) => ({
        label: f.description || f.label || 'Amount',
        value: f.amount || f.value || '',
        disputed: f.disputed || false,
        dispute_reason: f.dispute_reason || ''
      }));

      // Get and normalize dates
      const rawDates = analysisData.all_dates || analysisData.key_dates || [];
      const normalizedDates = (Array.isArray(rawDates) ? rawDates : []).map((d: any) => ({
        date: d.date || d,
        description: d.event || d.description || '',
        why_important: d.why_important || d.significance || '',
        action_required: d.action_required || '',
        consequence: d.consequence_if_missed || d.consequence || '',
        urgency: d.urgency || 'normal'
      }));

      const newDocument = {
        id: analysisData.document_id || crypto.randomUUID(),
        fileName: file.name,
        fileType: file.type || 'application/pdf',
        uploadDate: new Date(),
        text: documentText,
        summary: analysisData.comprehensive_summary || analysisData.summary || 'Summary not available',
        parties: analysisData.all_parties || analysisData.parties || [],
        importantDates: normalizedDates,
        keyFigures: normalizedKeyFigures,
        keywords: analysisData.key_terms || [],
        analysis: analysisData,
        // Additional fields from analysis
        documentType: analysisData.document_type || 'Unknown',
        caseNumber: analysisData.case_number || '',
        court: analysisData.court || '',
        filingDate: analysisData.filing_date || '',
        deadlines: analysisData.all_deadlines || analysisData.deadlines || [],
        keyArguments: analysisData.key_arguments || [],
        reliefRequested: analysisData.relief_requested || [],
        citedAuthority: analysisData.cited_authority || [],
        hearingInfo: analysisData.hearing_info || null,
        coreDispute: analysisData.core_dispute || '',
        plainEnglishSummary: analysisData.plain_english_summary || ''
      };

      addDocument(newDocument);

      updateProgress(fileName, { status: 'complete', progress: 100 });

      // Remove from queue after 2 seconds
      setTimeout(() => {
        removeFromQueue(fileName);
      }, 2000);

      toast.success(`${file.name} analyzed successfully!`, {
        description: `Document added with ${newDocument.keywords?.length || 0} keywords extracted`,
        duration: 3000,
      });

    } catch (error: any) {
      console.error(`Upload error for ${fileName}:`, error);
      updateProgress(fileName, {
        status: 'error',
        progress: 0,
        error: error.message || 'Upload failed'
      });
      toast.error(`${fileName}: Upload failed`, {
        description: error.message || 'Please try again',
        duration: 5000,
      });

      // Remove from queue after 5 seconds
      setTimeout(() => {
        removeFromQueue(fileName);
      }, 5000);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    // Show notification about multiple files
    if (files.length > 1) {
      toast.info(`Processing ${files.length} documents`, {
        description: 'Uploads will be processed sequentially',
        duration: 3000,
      });
    }

    // Process files sequentially (can be made concurrent if needed)
    for (let i = 0; i < files.length; i++) {
      await processFile(files[i]);
    }

    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const isProcessing = uploadQueue.some(item => item.status === 'uploading' || item.status === 'analyzing');

  return (
    <div className="documents-tab space-y-6">
      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Upload Legal Documents
            <span className="text-sm font-normal text-blue-600 ml-2">
              (Multiple files supported)
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-600">
            Upload one or more legal documents to analyze them simultaneously and use them across all features of the system.
          </p>

          <div className="space-y-3">
            {/* File Upload - Now supports multiple files */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileUpload}
              accept=".pdf,.doc,.docx,.txt"
              className="hidden"
              id="document-upload-enhanced"
              disabled={isProcessing}
            />
            <label
              htmlFor="document-upload-enhanced"
              className={`block w-full h-32 border-4 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all ${
                isProcessing
                  ? 'bg-gray-100 border-gray-300 cursor-not-allowed'
                  : 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-400 hover:border-blue-600 hover:bg-gradient-to-br hover:from-blue-100 hover:to-indigo-100'
              }`}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-3" />
                  <span className="text-lg font-semibold text-blue-900">Processing Documents...</span>
                  <span className="text-sm text-gray-600 mt-1">
                    {uploadQueue.filter(u => u.status !== 'complete').length} remaining
                  </span>
                </>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-blue-600 mb-3" />
                  <span className="text-lg font-semibold text-blue-900">Click to Upload Document(s)</span>
                  <span className="text-sm text-gray-600 mt-1">PDF, DOC, DOCX, or TXT files</span>
                  <span className="text-xs text-blue-600 mt-2 font-medium">Select multiple files at once!</span>
                </>
              )}
            </label>
          </div>

          {/* Upload Progress Queue */}
          {uploadQueue.length > 0 && (
            <div className="mt-4 space-y-3">
              <h3 className="font-semibold text-gray-700 text-sm">Upload Progress:</h3>
              {uploadQueue.map((item) => (
                <div key={item.fileName}>
                  {/* Show detailed progress tracker for analyzing files */}
                  {item.status === 'analyzing' && item.jobId ? (
                    <AnalysisProgressTracker
                      jobId={item.jobId}
                      filename={item.fileName}
                    />
                  ) : (
                    <Card className={`border-2 ${
                      item.status === 'complete'
                        ? 'border-green-500 bg-green-50'
                        : item.status === 'error'
                        ? 'border-red-500 bg-red-50'
                        : 'border-blue-300 bg-blue-50'
                    }`}>
                      <CardContent className="py-4">
                        <div className="flex items-center gap-3">
                          {item.status === 'uploading' && (
                            <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                          )}
                          {item.status === 'analyzing' && !item.jobId && (
                            <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                          )}
                          {item.status === 'complete' && (
                            <CheckCircle className="w-6 h-6 text-green-600" />
                          )}
                          {item.status === 'error' && (
                            <X className="w-6 h-6 text-red-600" />
                          )}
                          <div className="flex-1">
                            <p className="font-semibold text-gray-900">{item.fileName}</p>
                            <p className="text-sm text-gray-600">
                              {item.status === 'uploading' && 'Extracting text from document...'}
                              {item.status === 'analyzing' && !item.jobId && 'Starting AI analysis...'}
                              {item.status === 'complete' && 'Analysis complete - document ready'}
                              {item.status === 'error' && `Error: ${item.error}`}
                            </p>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Documents List */}
      {documents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Uploaded Documents ({documents.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    currentDocument?.id === doc.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                  }`}
                  onClick={() => setCurrentDocument(doc)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-blue-600" />
                        <span className="font-semibold text-gray-900">{doc.fileName}</span>
                        {currentDocument?.id === doc.id && (
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        Uploaded: {doc.uploadDate.toLocaleString()}
                      </p>
                    </div>
                    <Button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteDocument(doc.id, doc.fileName);
                      }}
                      variant="ghost"
                      size="sm"
                    >
                      <Trash2 className="w-4 h-4 text-red-600" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Documents Message */}
      {documents.length === 0 && !isProcessing && (
        <NoDocumentsEmpty onUpload={() => fileInputRef.current?.click()} />
      )}

      {/* Confirmation Dialog */}
      <ConfirmDialog />
    </div>
  );
}
