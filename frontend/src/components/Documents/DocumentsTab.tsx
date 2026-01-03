'use client';

import React, { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, Button } from '@/components/design-system';
import { Upload, FileText, Calendar, Users, DollarSign, Tag, CheckCircle, X, Loader2, Trash2, AlertTriangle, Scale } from 'lucide-react';
import { useDocuments } from '@/contexts/DocumentContext';
import { toast } from 'sonner';
import { NoDocumentsEmpty } from '@/components/EmptyState';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import { useConfirmDialog } from '@/components/ConfirmDialog';
import { AnalysisProgressTracker } from './AnalysisProgressTracker';

import { API_CONFIG } from '../../config/api';

// Helper to get auth headers
const getAuthHeaders = (): HeadersInit => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('accessToken');
    if (token) {
      return { 'Authorization': `Bearer ${token}` };
    }
  }
  return {};
};

interface FileUploadProgress {
  filename: string;
  status: 'uploading' | 'analyzing' | 'completed' | 'failed';
  error?: string;
  jobId?: string;  // For progress tracking
}

export function DocumentsTab() {
  const { documents, currentDocument, sessionId, addDocument, setCurrentDocument, removeDocument } = useDocuments();
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<FileUploadProgress[]>([]);
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

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    // Convert FileList to Array
    const filesArray = Array.from(files);

    // Limit to 20 documents at a time
    const MAX_FILES = 20;
    if (filesArray.length > MAX_FILES) {
      toast.warning(`Upload limit exceeded`, {
        description: `You can upload a maximum of ${MAX_FILES} documents at a time. Only the first ${MAX_FILES} files will be processed.`,
        duration: 5000,
      });
      filesArray.splice(MAX_FILES); // Keep only first 20
    }

    // Initialize progress tracking for all files
    const initialProgress: FileUploadProgress[] = filesArray.map(file => ({
      filename: file.name,
      status: 'uploading' as const
    }));
    setUploadProgress(initialProgress);

    // Show notification about multiple files
    if (filesArray.length > 1) {
      toast.info(`Processing ${filesArray.length} documents`, {
        description: 'Uploads will be processed sequentially',
        duration: 3000,
      });
    }

    setIsUploading(true);

    // Process each file sequentially
    let successCount = 0;
    let failCount = 0;

    for (let i = 0; i < filesArray.length; i++) {
      const file = filesArray[i];

      try {
        // Update progress: currently uploading
        setUploadProgress(prev => prev.map((p, idx) =>
          idx === i ? { ...p, status: 'uploading' } : p
        ));

        const formData = new FormData();
        formData.append('file', file);

        // Step 1: Extract text from document
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
        console.log('[DocumentsTab] STEP 1 COMPLETE: Text extracted, length:', documentText.length, 'chars');

        // Step 2: Start async analysis (returns immediately with job_id for real-time progress)
        console.log('[DocumentsTab] STEP 2: About to call /analyze-text-async with text length:', documentText.length);
        const startResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/analyze-text-async`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAuthHeaders()
          },
          body: JSON.stringify({
            text: documentText,
            filename: file.name,
            session_id: sessionId,
            // Comprehensive mode: include all extractors for detailed analysis
            include_operational_details: true,
            include_financial_details: true,
            use_multi_layer_analysis: true,  // Enable 4-layer verification for accuracy
            thorough_analysis: true           // Full pipeline with inspections
          })
        });

        console.log('[DocumentsTab] STEP 2: /analyze-text-async response status:', startResponse.status, startResponse.ok);
        if (!startResponse.ok) {
          const errorText = await startResponse.text();
          console.error('[DocumentsTab] /analyze-text-async FAILED:', errorText);
          throw new Error('Failed to start document analysis');
        }

        const startData = await startResponse.json();
        console.log('[DocumentsTab] STEP 2: /analyze-text-async FULL RESPONSE:', JSON.stringify(startData, null, 2));
        const jobId = startData.job_id;
        const documentId = startData.document_id;

        // DEBUG: Log the API response to verify job_id is present
        console.log('[DocumentsTab] analyze-text-async response:', { jobId, documentId, startData });

        // Update progress with real job_id for progress tracking
        // IMPORTANT: Must have valid jobId for AnalysisProgressTracker to render
        if (!jobId) {
          console.error('[DocumentsTab] No job_id in response! AnalysisProgressTracker will not render.');
        }
        setUploadProgress(prev => prev.map((p, idx) =>
          idx === i ? { ...p, status: 'analyzing', jobId: jobId } : p
        ));
        console.log('[DocumentsTab] Updated uploadProgress with jobId:', jobId);

        // CRITICAL: Yield to React to allow AnalysisProgressTracker to render
        // This initial delay allows the UI to show the progress tracker before polling starts
        await new Promise(resolve => setTimeout(resolve, 100));

        // Step 3: Poll for completion (with timeout)
        // Use a polling function that yields to React's render cycle
        const MAX_POLL_TIME = 300000; // 5 minutes max for thorough analysis max
        const POLL_INTERVAL = 2000;   // Poll every 2 seconds
        const startTime = Date.now();
        let analysisData = null;

        const pollForCompletion = async (): Promise<any> => {
          while (Date.now() - startTime < MAX_POLL_TIME) {
            // Yield to React's render cycle by using setTimeout
            await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));

            try {
              const progressResponse = await fetch(
                `${API_CONFIG.BASE_URL}/api/v1/documents/analysis-progress/${jobId}`,
                { headers: getAuthHeaders() }
              );

              if (!progressResponse.ok) {
                continue; // Keep polling
              }

              const progressData = await progressResponse.json();

              if (progressData.is_failed) {
                throw new Error(progressData.error || 'Analysis failed');
              }

              if (progressData.is_complete) {
                // Fetch the full result
                const resultResponse = await fetch(
                  `${API_CONFIG.BASE_URL}/api/v1/documents/analysis-result/${jobId}`,
                  { headers: getAuthHeaders() }
                );

                if (resultResponse.ok) {
                  return await resultResponse.json();
                }
                throw new Error('Failed to fetch analysis result');
              }
            } catch (err) {
              if ((err as Error).message.includes('Analysis failed')) {
                throw err;
              }
              // Continue polling on network errors
              console.warn('Poll error, retrying:', err);
            }
          }
          return null;
        };

        analysisData = await pollForCompletion();

        if (!analysisData) {
          throw new Error('Analysis timed out. Please try again.');
        }

        // ========== DIAGNOSTIC LOGGING ==========
        console.log('[DocumentsTab] ========== FINAL ANALYSIS RESULT ==========');
        console.log('[DocumentsTab] Full analysisData object keys:', Object.keys(analysisData));
        console.log('[DocumentsTab] Financial data fields:', {
          all_financial_amounts: analysisData.all_financial_amounts,
          financial_amounts: analysisData.financial_amounts,
          key_figures: analysisData.key_figures
        });
        console.log('[DocumentsTab] Summary fields:', {
          comprehensive_summary: analysisData.comprehensive_summary?.substring(0, 100) + '...',
          summary: analysisData.summary?.substring(0, 100) + '...'
        });
        console.log('[DocumentsTab] Parties:', analysisData.all_parties || analysisData.parties);
        console.log('[DocumentsTab] Dates:', analysisData.all_dates || analysisData.key_dates);
        // ========================================

        // Create document object using backend's document_id
        // Map ALL comprehensive data from the analysis
        const newDocument = {
          id: analysisData.document_id || documentId || crypto.randomUUID(),
          fileName: file.name,
          fileType: file.type || 'application/pdf',
          uploadDate: new Date(),
          text: documentText,
          // Use comprehensive summary if available, fallback to regular summary
          summary: analysisData.comprehensive_summary || analysisData.summary || generateSummary(documentText),
          // Map parties with full details (name, role, relationship)
          parties: analysisData.all_parties || analysisData.parties || extractParties(documentText),
          // Map dates with WHY explanations - prefer all_dates which has significance
          importantDates: (analysisData.all_dates || analysisData.key_dates || extractDates(documentText)).map((d: any) => ({
            date: d.date || d,
            description: d.event || d.description || '',
            why_important: d.why_important || d.significance || '',
            action_required: d.action_required || '',
            consequence: d.consequence_if_missed || d.consequence || '',
            urgency: d.urgency || 'normal'
          })),
          // Map financial amounts with dispute info - ensure array before mapping
          keyFigures: (Array.isArray(analysisData.all_financial_amounts) ? analysisData.all_financial_amounts :
                       Array.isArray(analysisData.financial_amounts) ? analysisData.financial_amounts :
                       Array.isArray(analysisData.key_figures) ? analysisData.key_figures :
                       extractKeyFigures(documentText)).map((f: any) => ({
            label: f.description || f.label || 'Amount',
            value: f.amount || f.value || '',
            disputed: f.disputed || false,
            dispute_reason: f.dispute_reason || ''
          })),
          keywords: analysisData.key_terms || extractKeywords(documentText),
          // Store ALL analysis data for comprehensive display
          analysis: analysisData,
          // Additional structured data from analysis
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

        // Log the normalized document before adding
        console.log('[DocumentsTab] ========== NORMALIZED DOCUMENT ==========');
        console.log('[DocumentsTab] newDocument.keyFigures:', newDocument.keyFigures);
        console.log('[DocumentsTab] newDocument.summary length:', newDocument.summary?.length);
        console.log('[DocumentsTab] newDocument.importantDates:', newDocument.importantDates);
        console.log('[DocumentsTab] =========================================');

        addDocument(newDocument);

        // Update progress: completed
        setUploadProgress(prev => prev.map((p, idx) =>
          idx === i ? { ...p, status: 'completed' } : p
        ));

        successCount++;

      } catch (error: any) {
        console.error(`Error uploading ${file.name}:`, error);

        // Update progress: failed
        setUploadProgress(prev => prev.map((p, idx) =>
          idx === i ? { ...p, status: 'failed', error: error.message } : p
        ));

        failCount++;
      }
    }

    // Clear file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }

    // Show final summary
    if (filesArray.length === 1) {
      // Single file: show specific message
      if (successCount === 1) {
        toast.success(`${filesArray[0].name} analyzed successfully!`, {
          description: 'Document added to your library',
          duration: 3000,
        });
      } else {
        toast.error(`Failed to upload ${filesArray[0].name}`, {
          description: uploadProgress[0]?.error || 'Please try again',
          duration: 5000,
        });
      }
    } else {
      // Multiple files: show summary
      if (successCount === filesArray.length) {
        toast.success(`All ${successCount} documents processed successfully!`, {
          description: 'All documents added to your library',
          duration: 4000,
        });
      } else if (successCount > 0) {
        toast.warning(`Processed ${successCount} of ${filesArray.length} documents`, {
          description: `${failCount} document(s) failed to upload`,
          duration: 5000,
        });
      } else {
        toast.error('All document uploads failed', {
          description: 'Please check the files and try again',
          duration: 5000,
        });
      }
    }

    // Clear progress after a delay
    setTimeout(() => {
      setUploadProgress([]);
      setIsUploading(false);
      setIsAnalyzing(false);
    }, 3000);
  };

  const handleSampleDocument = async () => {
    setIsAnalyzing(true);

    const sampleText = `IN THE CIRCUIT COURT

MIDLAND CREDIT MANAGEMENT, INC.,
Plaintiff,

vs.

JOHN DOE,
Defendant.

Case No: 2024-CC-12345

COMPLAINT

Plaintiff alleges:
1. Defendant owes $8,542.00 on a credit card account
2. Original creditor was Chase Bank
3. Debt was assigned to Plaintiff on January 15, 2023
4. Defendant has failed to pay despite demand

WHEREFORE, Plaintiff seeks judgment for $8,542.00 plus interest, costs, and attorney fees.`;

    try {
      // Start async analysis (returns immediately with job_id)
      const startResponse = await fetch(`${API_CONFIG.BASE_URL}/api/v1/documents/analyze-text-async`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({
          text: sampleText,
          filename: 'Sample_Debt_Collection_Case.txt',
          session_id: sessionId,
          // Comprehensive mode: include all extractors for detailed analysis
          include_operational_details: true,
          include_financial_details: true,
          use_multi_layer_analysis: true,  // Enable 4-layer verification
          thorough_analysis: true           // Full pipeline with inspections
        })
      });

      const startData = await startResponse.json();
      const jobId = startData.job_id;
      const documentId = startData.document_id;

      // Poll for completion
      const MAX_POLL_TIME = 300000; // 5 minutes max for thorough analysis
      const POLL_INTERVAL = 2000;
      const startTime = Date.now();
      let analysisData = null;

      while (Date.now() - startTime < MAX_POLL_TIME) {
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL));

        const progressResponse = await fetch(
          `${API_CONFIG.BASE_URL}/api/v1/documents/analysis-progress/${jobId}`,
          { headers: getAuthHeaders() }
        );

        if (progressResponse.ok) {
          const progressData = await progressResponse.json();

          if (progressData.is_failed) {
            throw new Error(progressData.error || 'Analysis failed');
          }

          if (progressData.is_complete) {
            const resultResponse = await fetch(
              `${API_CONFIG.BASE_URL}/api/v1/documents/analysis-result/${jobId}`,
              { headers: getAuthHeaders() }
            );
            if (resultResponse.ok) {
              analysisData = await resultResponse.json();
            }
            break;
          }
        }
      }

      if (!analysisData) {
        throw new Error('Analysis timed out');
      }

      // Map ALL comprehensive data from the analysis (same as file upload)
      const sampleDocument = {
        id: analysisData.document_id || documentId || crypto.randomUUID(),
        fileName: 'Sample_Debt_Collection_Case.txt',
        fileType: 'text/plain',
        uploadDate: new Date(),
        text: sampleText,
        summary: analysisData.comprehensive_summary || analysisData.summary || 'Debt collection lawsuit filed by Midland Credit Management against John Doe for an outstanding credit card debt of $8,542.00 originally owed to Chase Bank.',
        parties: analysisData.all_parties || analysisData.parties || ['Midland Credit Management, Inc. (Plaintiff)', 'John Doe (Defendant)', 'Chase Bank (Original Creditor)'],
        importantDates: (analysisData.all_dates || analysisData.key_dates || [
          { date: '2024-01-15', description: 'Debt assigned to plaintiff' },
          { date: '2024-03-15', description: 'Case filed' }
        ]).map((d: any) => ({
          date: d.date || d,
          description: d.event || d.description || '',
          why_important: d.why_important || d.significance || '',
          action_required: d.action_required || '',
          consequence: d.consequence_if_missed || d.consequence || '',
          urgency: d.urgency || 'normal'
        })),
        keyFigures: (Array.isArray(analysisData.all_financial_amounts) ? analysisData.all_financial_amounts :
                     Array.isArray(analysisData.financial_amounts) ? analysisData.financial_amounts :
                     Array.isArray(analysisData.key_figures) ? analysisData.key_figures : [
          { label: 'Amount Claimed', value: '$8,542.00' },
          { label: 'Case Number', value: '2024-CC-12345' }
        ]).map((f: any) => ({
          label: f.description || f.label || 'Amount',
          value: f.amount || f.value || '',
          disputed: f.disputed || false,
          dispute_reason: f.dispute_reason || ''
        })),
        keywords: analysisData.key_terms || ['debt collection', 'credit card', 'assignment', 'judgment'],
        analysis: analysisData,
        documentType: analysisData.document_type || 'Debt Collection Complaint',
        caseNumber: analysisData.case_number || '2024-CC-12345',
        court: analysisData.court || 'Circuit Court',
        filingDate: analysisData.filing_date || '',
        deadlines: analysisData.all_deadlines || analysisData.deadlines || [],
        keyArguments: analysisData.key_arguments || [],
        reliefRequested: analysisData.relief_requested || [],
        citedAuthority: analysisData.cited_authority || [],
        hearingInfo: analysisData.hearing_info || null,
        coreDispute: analysisData.core_dispute || '',
        plainEnglishSummary: analysisData.plain_english_summary || ''
      };

      addDocument(sampleDocument);
    } catch (error) {
      console.error('Sample document error:', error);
      // Fallback if analysis fails
      const sampleDocument = {
        id: crypto.randomUUID(),
        fileName: 'Sample_Debt_Collection_Case.txt',
        fileType: 'text/plain',
        uploadDate: new Date(),
        text: sampleText,
        summary: 'Debt collection lawsuit filed by Midland Credit Management against John Doe for an outstanding credit card debt of $8,542.00 originally owed to Chase Bank.',
        parties: ['Midland Credit Management, Inc. (Plaintiff)', 'John Doe (Defendant)', 'Chase Bank (Original Creditor)'],
        importantDates: [
          { date: '2024-01-15', description: 'Debt assigned to plaintiff' }
        ],
        keyFigures: [
          { label: 'Amount Claimed', value: '$8,542.00' },
          { label: 'Case Number', value: '2024-CC-12345' }
        ],
        keywords: ['debt collection', 'credit card', 'assignment', 'judgment'],
      };
      addDocument(sampleDocument);
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="documents-tab space-y-6">
      {/* Upload Section */}
      <Card data-tour="documents-upload">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Upload Legal Documents
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-slate-600">
            Upload your legal documents to analyze them and use them across all features of the system.
          </p>
          <p className="text-sm text-teal-600 font-medium">
            💡 You can upload up to 20 documents at a time. Each document will be processed with AI-powered analysis.
          </p>

          <div className="space-y-3">
            {/* File Upload */}
            <input
              ref={fileInputRef}
              type="file"
              multiple
              onChange={handleFileUpload}
              accept=".pdf,.doc,.docx,.txt"
              className="hidden"
              id="document-upload"
              disabled={isUploading || isAnalyzing}
            />
            <label
              htmlFor="document-upload"
              className={`block w-full h-32 border-4 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition-all ${
                isUploading || isAnalyzing
                  ? 'bg-slate-100 border-slate-300 cursor-not-allowed'
                  : 'bg-gradient-to-br from-teal-50 to-navy-50 border-teal-400 hover:border-teal-600 hover:bg-gradient-to-br hover:from-teal-100 hover:to-navy-100'
              }`}
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-12 h-12 text-teal-600 animate-spin mb-3" />
                  <span className="text-lg font-semibold text-navy-800">Processing Documents...</span>
                  <span className="text-sm text-slate-600 mt-1">
                    {uploadProgress.filter(p => p.status === 'completed').length} / {uploadProgress.length} complete
                  </span>
                </>
              ) : isAnalyzing ? (
                <>
                  <Loader2 className="w-12 h-12 text-teal-600 animate-spin mb-3" />
                  <span className="text-lg font-semibold text-navy-800">Analyzing Document...</span>
                </>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-teal-600 mb-3" />
                  <span className="text-lg font-semibold text-navy-800">Click to Upload Documents</span>
                  <span className="text-sm text-slate-600 mt-1">Select up to 20 PDF, DOC, DOCX, or TXT files</span>
                </>
              )}
            </label>

            {/* Sample Document Button */}
            <div className="flex items-center gap-4">
              <div className="flex-1 h-px bg-slate-300"></div>
              <span className="text-slate-500 text-sm font-medium">OR</span>
              <div className="flex-1 h-px bg-slate-300"></div>
            </div>

            <Button
              onClick={handleSampleDocument}
              disabled={isUploading || isAnalyzing}
              className="w-full h-16 text-lg"
              variant="outline"
            >
              📄 Use Sample Debt Collection Case
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Multi-File Upload Progress */}
      {uploadProgress.length > 0 && (
        <div className="space-y-4">
          {/* Summary card */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
                Processing {uploadProgress.length} Document{uploadProgress.length > 1 ? 's' : ''}
                <span className="text-sm font-normal text-slate-500 ml-2">
                  ({uploadProgress.filter(p => p.status === 'completed').length} / {uploadProgress.length} complete)
                </span>
              </CardTitle>
            </CardHeader>
          </Card>

          {/* Individual file progress */}
          {/* DEBUG: Log uploadProgress state */}
          {console.log('[DocumentsTab] Rendering uploadProgress:', uploadProgress.map(p => ({ filename: p.filename, status: p.status, jobId: p.jobId })))}
          {uploadProgress.map((progress, index) => (
            <div key={index}>
              {/* Show detailed progress tracker for analyzing files */}
              {progress.status === 'analyzing' && progress.jobId ? (
                <AnalysisProgressTracker
                  jobId={progress.jobId}
                  filename={progress.filename}
                />
              ) : (
                <Card className={`border-2 ${
                  progress.status === 'completed'
                    ? 'border-green-500 bg-green-50'
                    : progress.status === 'failed'
                    ? 'border-red-500 bg-red-50'
                    : 'border-teal-300 bg-teal-50'
                }`}>
                  <CardContent className="py-4">
                    <div className="flex items-center gap-3">
                      {progress.status === 'uploading' && (
                        <Loader2 className="w-6 h-6 text-teal-600 animate-spin" />
                      )}
                      {progress.status === 'analyzing' && !progress.jobId && (
                        <Loader2 className="w-6 h-6 text-teal-600 animate-spin" />
                      )}
                      {progress.status === 'completed' && (
                        <CheckCircle className="w-6 h-6 text-green-600" />
                      )}
                      {progress.status === 'failed' && (
                        <X className="w-6 h-6 text-red-600" />
                      )}
                      <div className="flex-1">
                        <p className="font-semibold text-slate-900">{progress.filename}</p>
                        <p className="text-sm text-slate-600">
                          {progress.status === 'uploading' && 'Extracting text from document...'}
                          {progress.status === 'analyzing' && !progress.jobId && 'Starting AI analysis...'}
                          {progress.status === 'completed' && 'Analysis complete - document ready'}
                          {progress.status === 'failed' && `Error: ${progress.error}`}
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

      {/* Analyzing Skeleton */}
      {isAnalyzing && uploadProgress.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
              Analyzing Document...
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Summary Skeleton */}
            <div>
              <h3 className="font-bold text-slate-900 mb-2 flex items-center gap-2">
                <FileText className="w-5 h-5 text-teal-600" />
                Summary
              </h3>
              <div className="bg-teal-50 p-4 rounded-lg border-l-4 border-teal-500">
                <Skeleton count={3} />
              </div>
            </div>

            {/* Parties Skeleton */}
            <div>
              <h3 className="font-bold text-slate-900 mb-2 flex items-center gap-2">
                <Users className="w-5 h-5 text-purple-600" />
                Parties Involved
              </h3>
              <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                <Skeleton count={2} />
              </div>
            </div>

            {/* Dates Skeleton */}
            <div>
              <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-green-600 dark:text-green-400" />
                Important Dates
              </h3>
              <div className="bg-green-50 dark:bg-green-900/30 p-4 rounded-lg border-l-4 border-green-500 border dark:border-green-600">
                <Skeleton count={2} />
              </div>
            </div>

            {/* Figures Skeleton */}
            <div>
              <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                Key Figures & Numbers
              </h3>
              <div className="bg-amber-50 dark:bg-amber-900/30 p-4 rounded-lg border-l-4 border-amber-500 border dark:border-amber-600">
                <Skeleton count={2} />
              </div>
            </div>

            {/* Keywords Skeleton */}
            <div>
              <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                <Tag className="w-5 h-5 text-navy-600 dark:text-teal-400" />
                Keywords & Terms
              </h3>
              <div className="bg-navy-50 dark:bg-slate-700 p-4 rounded-lg border-l-4 border-navy-500 dark:border-teal-500 border dark:border-slate-500">
                <div className="flex flex-wrap gap-2">
                  <Skeleton width={80} height={24} count={5} inline containerClassName="flex gap-2 flex-wrap" />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Documents List */}
      {documents.length > 0 && (
        <Card data-tour="documents-list">
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
                      ? 'border-teal-500 bg-teal-50 dark:bg-teal-900/30 dark:border-teal-400'
                      : 'border-slate-200 dark:border-slate-600 hover:border-teal-300 dark:hover:border-teal-500 hover:bg-slate-50 dark:hover:bg-slate-700'
                  }`}
                  onClick={() => setCurrentDocument(doc)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <FileText className="w-5 h-5 text-teal-600 dark:text-teal-400" />
                        <span className="font-semibold text-slate-900 dark:text-slate-100">{doc.fileName}</span>
                        {currentDocument?.id === doc.id && (
                          <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                        )}
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
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

      {/* Current Document Analysis */}
      {currentDocument && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Document Analysis: {currentDocument.fileName}</span>
              {(currentDocument as any).documentType && (
                <span className="text-sm font-normal px-3 py-1 bg-teal-100 dark:bg-teal-900/50 text-navy-700 dark:text-teal-200 rounded-full">
                  {(currentDocument as any).documentType}
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Document Info Banner */}
            {((currentDocument as any).caseNumber || (currentDocument as any).court || (currentDocument as any).filingDate) && (
              <div className="bg-slate-100 p-4 rounded-lg grid grid-cols-1 md:grid-cols-3 gap-4">
                {(currentDocument as any).caseNumber && (
                  <div>
                    <span className="text-xs text-slate-500 uppercase font-semibold">Case Number</span>
                    <p className="font-bold text-slate-900">{(currentDocument as any).caseNumber}</p>
                  </div>
                )}
                {(currentDocument as any).court && (
                  <div>
                    <span className="text-xs text-slate-500 uppercase font-semibold">Court</span>
                    <p className="font-bold text-slate-900">{(currentDocument as any).court}</p>
                  </div>
                )}
                {(currentDocument as any).filingDate && (
                  <div>
                    <span className="text-xs text-slate-500 uppercase font-semibold">Filing Date</span>
                    <p className="font-bold text-slate-900">{(currentDocument as any).filingDate}</p>
                  </div>
                )}
              </div>
            )}

            {/* Core Dispute - What this is really about */}
            {(currentDocument as any).coreDispute && (
              <div>
                <h3 className="font-bold text-lg text-slate-900 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                  Core Dispute
                </h3>
                <div className="text-slate-800 bg-red-50 p-5 rounded-lg border-l-4 border-red-500 leading-relaxed">
                  <p className="text-base">{(currentDocument as any).coreDispute}</p>
                </div>
              </div>
            )}

            {/* Summary - Enhanced with more detail */}
            {currentDocument.summary && (
              <div>
                <h3 className="font-bold text-lg text-slate-900 mb-3 flex items-center gap-2">
                  <FileText className="w-6 h-6 text-teal-600" />
                  Comprehensive Summary
                </h3>
                <div className="text-slate-800 bg-teal-50 p-5 rounded-lg border-l-4 border-teal-500 leading-relaxed">
                  <p className="text-base whitespace-pre-line">
                    {currentDocument.summary}
                  </p>
                </div>
              </div>
            )}

            {/* Plain English Summary */}
            {(currentDocument as any).plainEnglishSummary && (
              <div>
                <h3 className="font-bold text-lg text-slate-900 mb-3 flex items-center gap-2">
                  <Scale className="w-6 h-6 text-green-600" />
                  In Plain English
                </h3>
                <div className="text-slate-800 bg-green-50 p-5 rounded-lg border-l-4 border-green-500 leading-relaxed">
                  <p className="text-base">{(currentDocument as any).plainEnglishSummary}</p>
                </div>
              </div>
            )}

            {/* Factual Background - NEW */}
            {(currentDocument as any).factual_background && (
              <div>
                <h3 className="font-bold text-lg text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
                  <FileText className="w-6 h-6 text-navy-600 dark:text-teal-400" />
                  Factual Background
                </h3>
                <div className="text-slate-800 dark:text-slate-200 bg-navy-50 dark:bg-slate-700 p-5 rounded-lg border-l-4 border-navy-500 dark:border-teal-500">
                  <p className="text-base whitespace-pre-line">
                    {(currentDocument as any).factual_background}
                  </p>
                </div>
              </div>
            )}

            {/* Immediate Actions Required - NEW */}
            {(currentDocument as any).immediate_actions && (currentDocument as any).immediate_actions.length > 0 && (
              <div>
                <h3 className="font-bold text-lg text-slate-900 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                  Immediate Actions Required
                </h3>
                <div className="bg-red-50 p-5 rounded-lg border-l-4 border-red-500">
                  <ul className="space-y-3">
                    {(currentDocument as any).immediate_actions.map((action: string, index: number) => (
                      <li key={index} className="text-slate-800 flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center font-bold text-sm mt-0.5">
                          {index + 1}
                        </span>
                        <span className="flex-1 text-base">{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Relief Requested - NEW */}
            {(currentDocument as any).relief_requested && (
              <div>
                <h3 className="font-bold text-lg text-slate-900 mb-3 flex items-center gap-2">
                  <Scale className="w-6 h-6 text-purple-600" />
                  Relief/Remedies Requested
                </h3>
                <div className="text-slate-800 bg-purple-50 p-5 rounded-lg border-l-4 border-purple-500">
                  <p className="text-base whitespace-pre-line">
                    {(currentDocument as any).relief_requested}
                  </p>
                </div>
              </div>
            )}

            {/* Potential Risks - NEW */}
            {(currentDocument as any).potential_risks && (currentDocument as any).potential_risks.length > 0 && (
              <div>
                <h3 className="font-bold text-lg text-slate-900 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6 text-orange-600" />
                  Potential Legal Risks
                </h3>
                <div className="bg-orange-50 p-5 rounded-lg border-l-4 border-orange-500">
                  <ul className="space-y-2">
                    {(currentDocument as any).potential_risks.map((risk: string, index: number) => (
                      <li key={index} className="text-slate-800 flex items-start gap-2">
                        <span className="w-2 h-2 bg-orange-600 rounded-full mt-2 flex-shrink-0"></span>
                        <span className="flex-1 text-base">{risk}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Procedural Status - NEW */}
            {(currentDocument as any).procedural_status && (
              <div>
                <h3 className="font-bold text-lg text-slate-900 mb-3 flex items-center gap-2">
                  <FileText className="w-6 h-6 text-teal-600" />
                  Procedural Status
                </h3>
                <div className="text-slate-800 bg-teal-50 p-5 rounded-lg border-l-4 border-teal-500">
                  <p className="text-base whitespace-pre-line">
                    {(currentDocument as any).procedural_status}
                  </p>
                </div>
              </div>
            )}

            {/* Parties */}
            {currentDocument.parties && currentDocument.parties.length > 0 && (
              <div>
                <h3 className="font-bold text-slate-900 mb-2 flex items-center gap-2">
                  <Users className="w-5 h-5 text-purple-600" />
                  Parties Involved
                </h3>
                <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                  <ul className="space-y-1">
                    {currentDocument.parties.map((party, index) => {
                      // Handle both string and object party formats
                      const partyName = typeof party === 'string'
                        ? party
                        : (party as any)?.name || String(party);
                      const partyRole = typeof party === 'object' && (party as any)?.role
                        ? ` (${(party as any).role})`
                        : '';
                      return (
                        <li key={index} className="text-slate-700 flex items-center gap-2">
                          <span className="w-2 h-2 bg-purple-600 rounded-full"></span>
                          {partyName}{partyRole}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              </div>
            )}

            {/* Important Dates - Enhanced with WHY explanations */}
            {currentDocument.importantDates && currentDocument.importantDates.length > 0 && (
              <div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-green-600 dark:text-green-400" />
                  Important Dates & Why They Matter
                </h3>
                <div className="bg-green-50 dark:bg-green-900/30 p-4 rounded-lg border-l-4 border-green-500 border dark:border-green-600 space-y-4">
                  {currentDocument.importantDates.map((dateInfo: any, index: number) => {
                    const isUrgent = dateInfo.urgency === 'high' || dateInfo.urgency === 'HIGH' || dateInfo.urgency === 'CRITICAL' || dateInfo.consequence;
                    return (
                      <div key={index} className="border-b border-green-300 dark:border-green-700 pb-4 last:border-0 last:pb-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`font-bold text-lg ${isUrgent ? 'text-red-900 dark:text-red-200' : 'text-green-900 dark:text-green-200'}`}>
                            {dateInfo.date}
                          </span>
                          {isUrgent && (
                            <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded-full flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3" />
                              CRITICAL
                            </span>
                          )}
                        </div>
                        <p className="text-slate-800 dark:text-slate-200 font-medium">{dateInfo.description}</p>

                        {/* WHY this date matters */}
                        {dateInfo.why_important && (
                          <div className="mt-2 flex items-start gap-2">
                            <span className="px-2 py-0.5 bg-blue-200 dark:bg-blue-900/50 text-navy-700 dark:text-blue-200 text-xs font-bold rounded">WHY</span>
                            <p className="text-sm text-slate-700 dark:text-slate-300">{dateInfo.why_important}</p>
                          </div>
                        )}

                        {/* Action required */}
                        {dateInfo.action_required && (
                          <div className="mt-2 flex items-start gap-2">
                            <span className="px-2 py-0.5 bg-green-200 dark:bg-green-800 text-green-800 dark:text-green-200 text-xs font-bold rounded">ACTION</span>
                            <p className="text-sm text-slate-700 dark:text-slate-300">{dateInfo.action_required}</p>
                          </div>
                        )}

                        {/* Consequence if missed */}
                        {dateInfo.consequence && (
                          <div className="mt-2 flex items-start gap-2">
                            <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded">RISK</span>
                            <p className="text-sm text-red-700 dark:text-red-300 font-medium">{dateInfo.consequence}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Key Figures - Enhanced with disputed amounts */}
            {currentDocument.keyFigures && currentDocument.keyFigures.length > 0 && (
              <div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-amber-600 dark:text-amber-400" />
                  Financial Amounts
                </h3>
                <div className="bg-amber-50 dark:bg-amber-900/30 p-4 rounded-lg border-l-4 border-amber-500 border dark:border-amber-600 space-y-4">
                  {currentDocument.keyFigures.map((figure: any, index: number) => (
                    <div key={index} className={`border-b border-amber-300 dark:border-amber-700 pb-4 last:border-0 last:pb-0 ${figure.disputed ? 'bg-red-50/50 dark:bg-red-900/20 -mx-4 px-4 py-2 first:rounded-t-lg last:rounded-b-lg' : ''}`}>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-700 dark:text-slate-300">{figure.label}:</span>
                          {figure.disputed && (
                            <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded-full flex items-center gap-1">
                              <AlertTriangle className="w-3 h-3" />
                              DISPUTED
                            </span>
                          )}
                        </div>
                        <span className={`font-bold text-lg ${figure.disputed ? 'text-red-900 dark:text-red-200' : 'text-amber-900 dark:text-amber-200'}`}>
                          {figure.value}
                        </span>
                      </div>
                      {figure.dispute_reason && (
                        <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                          <span className="font-semibold">Dispute reason:</span> {figure.dispute_reason}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Arguments */}
            {(currentDocument as any).keyArguments && (currentDocument as any).keyArguments.length > 0 && (
              <div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                  <Scale className="w-5 h-5 text-navy-600 dark:text-teal-400" />
                  Key Legal Arguments
                </h3>
                <div className="bg-navy-50 dark:bg-slate-700 p-4 rounded-lg border-l-4 border-navy-500 dark:border-teal-500 border dark:border-slate-500 space-y-3">
                  {(currentDocument as any).keyArguments.map((arg: any, index: number) => (
                    <div key={index} className="border-b border-navy-200 dark:border-slate-600 pb-3 last:border-0 last:pb-0">
                      <div className="flex items-start gap-2">
                        <span className="bg-navy-600 dark:bg-teal-600 text-white w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
                          {index + 1}
                        </span>
                        <div className="flex-1">
                          <p className="text-slate-800 dark:text-slate-200 font-medium">{arg.argument || arg}</p>
                          {arg.supporting_facts && (
                            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                              <span className="font-semibold">Support:</span> {arg.supporting_facts}
                            </p>
                          )}
                          {arg.legal_basis && (
                            <p className="text-sm text-navy-700 dark:text-teal-300 mt-1">
                              <span className="font-semibold">Legal basis:</span> {arg.legal_basis}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Deadlines with Consequences */}
            {(currentDocument as any).deadlines && (currentDocument as any).deadlines.length > 0 && (
              <div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                  Critical Deadlines
                </h3>
                <div className="space-y-2">
                  {(currentDocument as any).deadlines.map((deadline: any, index: number) => (
                    <div key={index} className="p-4 rounded-lg border-l-4 border-red-500 bg-red-50 dark:bg-red-900/30 border dark:border-red-600">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-lg text-red-900 dark:text-red-200">{deadline.deadline || deadline.date}</span>
                        {(deadline.urgency === 'high' || deadline.urgency === 'HIGH' || deadline.urgency === 'CRITICAL') && (
                          <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded-full">URGENT</span>
                        )}
                      </div>
                      <p className="text-slate-800 dark:text-slate-200 font-medium">{deadline.action_required || deadline.description}</p>
                      {(deadline.consequence_if_missed || deadline.consequence) && (
                        <div className="mt-2 flex items-start gap-2">
                          <span className="px-2 py-0.5 bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200 text-xs font-bold rounded">IF MISSED</span>
                          <p className="text-sm text-red-700 dark:text-red-300 font-medium">{deadline.consequence_if_missed || deadline.consequence}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Relief Requested */}
            {(currentDocument as any).reliefRequested && (currentDocument as any).reliefRequested.length > 0 && (
              <div>
                <h3 className="font-bold text-slate-900 mb-2 flex items-center gap-2">
                  <Scale className="w-5 h-5 text-purple-600" />
                  Relief / Remedies Requested
                </h3>
                <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                  <ul className="space-y-2">
                    {(currentDocument as any).reliefRequested.map((relief: string, index: number) => (
                      <li key={index} className="text-slate-800 flex items-start gap-2">
                        <span className="w-2 h-2 bg-purple-600 rounded-full mt-2 flex-shrink-0"></span>
                        <span>{relief}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Hearing Information */}
            {(currentDocument as any).hearingInfo && (currentDocument as any).hearingInfo.date && (
              <div>
                <h3 className="font-bold text-slate-900 mb-2 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-teal-600" />
                  Upcoming Hearing
                </h3>
                <div className="bg-teal-50 p-4 rounded-lg border-l-4 border-teal-500">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <span className="text-xs text-slate-500 dark:text-slate-400 uppercase font-semibold">Date & Time</span>
                      <p className="font-bold text-navy-800 dark:text-slate-100">
                        {(currentDocument as any).hearingInfo.date}
                        {(currentDocument as any).hearingInfo.time && ` at ${(currentDocument as any).hearingInfo.time}`}
                      </p>
                    </div>
                    {(currentDocument as any).hearingInfo.location && (
                      <div>
                        <span className="text-xs text-slate-500 dark:text-slate-400 uppercase font-semibold">Location</span>
                        <p className="font-bold text-navy-800 dark:text-slate-100">{(currentDocument as any).hearingInfo.location}</p>
                      </div>
                    )}
                  </div>
                  {(currentDocument as any).hearingInfo.purpose && (
                    <div className="mt-3">
                      <span className="text-xs text-slate-500 uppercase font-semibold">Purpose</span>
                      <p className="text-slate-800">{(currentDocument as any).hearingInfo.purpose}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Cited Legal Authority */}
            {(currentDocument as any).citedAuthority && (currentDocument as any).citedAuthority.length > 0 && (
              <div>
                <h3 className="font-bold text-slate-900 mb-2 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-slate-600" />
                  Cited Legal Authority
                </h3>
                <div className="bg-slate-50 p-4 rounded-lg border-l-4 border-slate-500">
                  <ul className="space-y-1 text-sm">
                    {(currentDocument as any).citedAuthority.map((cite: string, index: number) => (
                      <li key={index} className="text-slate-700 font-mono">{cite}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Keywords */}
            {currentDocument.keywords && currentDocument.keywords.length > 0 && (
              <div>
                <h3 className="font-bold text-slate-900 dark:text-slate-100 mb-2 flex items-center gap-2">
                  <Tag className="w-5 h-5 text-navy-600 dark:text-teal-400" />
                  Keywords & Terms
                </h3>
                <div className="bg-navy-50 dark:bg-slate-700 p-4 rounded-lg border-l-4 border-navy-500 dark:border-teal-500 border dark:border-slate-500">
                  <div className="flex flex-wrap gap-2">
                    {currentDocument.keywords.map((keyword: any, index: number) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-navy-200 dark:bg-slate-600 text-navy-900 dark:text-slate-100 rounded-full text-sm font-medium"
                        title={typeof keyword === 'object' && keyword?.explanation ? keyword.explanation : undefined}
                      >
                        {typeof keyword === 'object' ? (keyword?.term || keyword?.name || JSON.stringify(keyword)) : keyword}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* No Documents Message */}
      {documents.length === 0 && !isUploading && !isAnalyzing && (
        <NoDocumentsEmpty onUpload={() => fileInputRef.current?.click()} />
      )}

      {/* Confirmation Dialog */}
      <ConfirmDialog />
    </div>
  );
}

// Helper functions for fallback extraction
function generateSummary(text: string): string {
  return text.slice(0, 200) + '...';
}

function extractParties(text: string): string[] {
  const parties: string[] = [];
  const lines = text.split('\n');

  for (let i = 0; i < Math.min(lines.length, 20); i++) {
    const line = lines[i].trim();
    if (line.includes('Plaintiff') || line.includes('PLAINTIFF')) {
      parties.push(line);
    }
    if (line.includes('Defendant') || line.includes('DEFENDANT')) {
      parties.push(line);
    }
  }

  return parties.length > 0 ? parties : ['Parties not identified'];
}

function extractDates(text: string): Array<{ date: string; description: string }> {
  const dates: Array<{ date: string; description: string }> = [];
  const dateRegex = /\b(\d{1,2}\/\d{1,2}\/\d{2,4}|\d{4}-\d{2}-\d{2}|[A-Z][a-z]+ \d{1,2},? \d{4})\b/g;
  const matches = text.match(dateRegex);

  if (matches) {
    matches.slice(0, 5).forEach((date) => {
      dates.push({ date, description: 'Date mentioned in document' });
    });
  }

  return dates;
}

function extractKeyFigures(text: string): Array<{ label: string; value: string }> {
  const figures: Array<{ label: string; value: string }> = [];
  const amountRegex = /\$[\d,]+(?:\.\d{2})?/g;
  const amounts = text.match(amountRegex);

  if (amounts) {
    amounts.slice(0, 3).forEach((amount, index) => {
      figures.push({ label: `Amount ${index + 1}`, value: amount });
    });
  }

  return figures;
}

function extractKeywords(text: string): string[] {
  const legalTerms = [
    'complaint', 'defendant', 'plaintiff', 'judgment', 'debt',
    'collection', 'breach', 'contract', 'damages', 'relief'
  ];

  const found = legalTerms.filter(term =>
    text.toLowerCase().includes(term)
  );

  return found.length > 0 ? found : ['legal document'];
}
