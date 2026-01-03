'use client';

import React, { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload, FileText, Calendar, Users, DollarSign, Tag, CheckCircle, X, Loader2, Trash2, AlertTriangle, Scale } from 'lucide-react';
import { useDocuments } from '@/contexts/DocumentContext';
import { toast } from 'sonner';
import { NoDocumentsEmpty } from '@/components/EmptyState';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';
import { useConfirmDialog } from '@/components/ConfirmDialog';
import BankruptcyAnalysisDashboard from '@/components/BankruptcyAnalysisDashboard';
import type { BankruptcyAnalysisResponse } from '@/types/bankruptcy';

interface FileUploadProgress {
  filename: string;
  status: 'uploading' | 'analyzing' | 'completed' | 'failed';
  error?: string;
}

export function DocumentsTab() {
  const { documents, currentDocument, sessionId, addDocument, setCurrentDocument, removeDocument } = useDocuments();
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<FileUploadProgress[]>([]);
  const [bankruptcyAnalysisData, setBankruptcyAnalysisData] = useState<BankruptcyAnalysisResponse | null>(null);
  const [showBankruptcyAnalysis, setShowBankruptcyAnalysis] = useState(false);
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

  const handleBankruptcyAnalysis = async (file: File) => {
    setIsAnalyzing(true);
    setBankruptcyAnalysisData(null);
    setShowBankruptcyAnalysis(false);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/api/v1/documents/process-document', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const data: BankruptcyAnalysisResponse = await response.json();
      setBankruptcyAnalysisData(data);
      setShowBankruptcyAnalysis(true);

      // Show alert for critical issues
      if (data.ui_display?.alerts?.has_critical) {
        const criticalCount = data.ui_display.alerts.critical.length;
        toast.error(`CRITICAL: ${criticalCount} critical issue(s) detected!`, {
          description: 'Review bankruptcy analysis immediately',
          duration: 8000,
        });
      } else {
        toast.success('Bankruptcy analysis complete', {
          description: `Extracted ${data.extraction_stats?.amounts_found || 0} amounts and ${data.extraction_stats?.claims_found || 0} claims`,
          duration: 5000,
        });
      }

    } catch (error) {
      console.error('Bankruptcy analysis failed:', error);
      toast.error('Bankruptcy analysis failed', {
        description: error instanceof Error ? error.message : 'Please try again',
        duration: 5000,
      });
    } finally {
      setIsAnalyzing(false);
    }
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
        const extractResponse = await fetch('http://localhost:8000/api/v1/documents/extract-text', {
          method: 'POST',
          body: formData
        });

        if (!extractResponse.ok) {
          throw new Error('Failed to extract text from document');
        }

        const extractData = await extractResponse.json();
        const documentText = extractData.extracted_text || extractData.text || '';

        // Update progress: now analyzing
        setUploadProgress(prev => prev.map((p, idx) =>
          idx === i ? { ...p, status: 'analyzing' } : p
        ));

        // Step 2: Analyze document with AI
        const analyzeResponse = await fetch('http://localhost:8000/api/v1/documents/analyze-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: documentText,
            filename: file.name,
            session_id: sessionId,
            include_operational_details: true,  // Enable enhanced extraction
            include_financial_details: true     // Enable detailed financial extraction
          })
        });

        if (!analyzeResponse.ok) {
          throw new Error('Failed to analyze document');
        }

        const analysisData = await analyzeResponse.json();

        // Create document object using backend's document_id
        const newDocument = {
          id: analysisData.document_id || crypto.randomUUID(),
          fileName: file.name,
          fileType: file.type || 'application/pdf',
          uploadDate: new Date(),
          text: documentText,
          summary: analysisData.summary || generateSummary(documentText),
          parties: analysisData.parties || extractParties(documentText),
          importantDates: analysisData.key_dates || extractDates(documentText),
          keyFigures: analysisData.key_figures || extractKeyFigures(documentText),
          keywords: analysisData.key_terms || extractKeywords(documentText),
          analysis: analysisData
        };

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
      // Analyze sample document
      const analyzeResponse = await fetch('http://localhost:8000/api/v1/documents/analyze-text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: sampleText,
          filename: 'Sample_Debt_Collection_Case.txt',
          session_id: sessionId,  // Pass session ID for persistence
          include_operational_details: true,  // Enable enhanced extraction
          include_financial_details: true     // Enable detailed financial extraction
        })
      });

      const analysisData = await analyzeResponse.json();

      const sampleDocument = {
        id: analysisData.document_id || crypto.randomUUID(),  // Use backend's ID
        fileName: 'Sample_Debt_Collection_Case.txt',
        fileType: 'text/plain',
        uploadDate: new Date(),
        text: sampleText,
        summary: analysisData.summary || 'Debt collection lawsuit filed by Midland Credit Management against John Doe for an outstanding credit card debt of $8,542.00 originally owed to Chase Bank.',
        parties: analysisData.parties || ['Midland Credit Management, Inc. (Plaintiff)', 'John Doe (Defendant)', 'Chase Bank (Original Creditor)'],
        importantDates: analysisData.key_dates || [
          { date: '2024-01-15', description: 'Debt assigned to plaintiff' },
          { date: '2024-03-15', description: 'Case filed' }
        ],
        keyFigures: analysisData.key_figures || [
          { label: 'Amount Claimed', value: '$8,542.00' },
          { label: 'Case Number', value: '2024-CC-12345' }
        ],
        keywords: analysisData.key_terms || ['debt collection', 'credit card', 'assignment', 'judgment'],
        analysis: analysisData
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
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Upload Legal Documents
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-gray-600">
            Upload your legal documents to analyze them and use them across all features of the system.
          </p>
          <p className="text-sm text-blue-600 font-medium">
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
                  ? 'bg-gray-100 border-gray-300 cursor-not-allowed'
                  : 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-400 hover:border-blue-600 hover:bg-gradient-to-br hover:from-blue-100 hover:to-indigo-100'
              }`}
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-3" />
                  <span className="text-lg font-semibold text-blue-900">Processing Documents...</span>
                  <span className="text-sm text-gray-600 mt-1">
                    {uploadProgress.filter(p => p.status === 'completed').length} / {uploadProgress.length} complete
                  </span>
                </>
              ) : isAnalyzing ? (
                <>
                  <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-3" />
                  <span className="text-lg font-semibold text-blue-900">Analyzing Document...</span>
                </>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-blue-600 mb-3" />
                  <span className="text-lg font-semibold text-blue-900">Click to Upload Documents</span>
                  <span className="text-sm text-gray-600 mt-1">Select up to 20 PDF, DOC, DOCX, or TXT files</span>
                </>
              )}
            </label>

            {/* Sample Document Button */}
            <div className="flex items-center gap-4">
              <div className="flex-1 h-px bg-gray-300"></div>
              <span className="text-gray-500 text-sm font-medium">OR</span>
              <div className="flex-1 h-px bg-gray-300"></div>
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
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              Processing {uploadProgress.length} Document{uploadProgress.length > 1 ? 's' : ''}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {uploadProgress.map((progress, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-lg border-2 ${
                    progress.status === 'completed'
                      ? 'border-green-500 bg-green-50'
                      : progress.status === 'failed'
                      ? 'border-red-500 bg-red-50'
                      : 'border-blue-500 bg-blue-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      {progress.status === 'uploading' && (
                        <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                      )}
                      {progress.status === 'analyzing' && (
                        <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                      )}
                      {progress.status === 'completed' && (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                      )}
                      {progress.status === 'failed' && (
                        <X className="w-5 h-5 text-red-600" />
                      )}
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{progress.filename}</p>
                        <p className="text-sm text-gray-600">
                          {progress.status === 'uploading' && 'Extracting text...'}
                          {progress.status === 'analyzing' && 'Analyzing with AI...'}
                          {progress.status === 'completed' && 'Successfully processed'}
                          {progress.status === 'failed' && `Failed: ${progress.error}`}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Analyzing Skeleton */}
      {isAnalyzing && uploadProgress.length === 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
              Analyzing Document...
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Summary Skeleton */}
            <div>
              <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Summary
              </h3>
              <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
                <Skeleton count={3} />
              </div>
            </div>

            {/* Parties Skeleton */}
            <div>
              <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                <Users className="w-5 h-5 text-purple-600" />
                Parties Involved
              </h3>
              <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                <Skeleton count={2} />
              </div>
            </div>

            {/* Dates Skeleton */}
            <div>
              <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-green-600" />
                Important Dates
              </h3>
              <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500">
                <Skeleton count={2} />
              </div>
            </div>

            {/* Figures Skeleton */}
            <div>
              <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                <DollarSign className="w-5 h-5 text-amber-600" />
                Key Figures & Numbers
              </h3>
              <div className="bg-amber-50 p-4 rounded-lg border-l-4 border-amber-500">
                <Skeleton count={2} />
              </div>
            </div>

            {/* Keywords Skeleton */}
            <div>
              <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                <Tag className="w-5 h-5 text-indigo-600" />
                Keywords & Terms
              </h3>
              <div className="bg-indigo-50 p-4 rounded-lg border-l-4 border-indigo-500">
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

      {/* Current Document Analysis */}
      {currentDocument && (
        <Card>
          <CardHeader>
            <CardTitle>Document Analysis: {currentDocument.fileName}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Summary - Enhanced with more detail */}
            {currentDocument.summary && (
              <div>
                <h3 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="w-6 h-6 text-blue-600" />
                  Comprehensive Summary
                </h3>
                <div className="text-gray-800 bg-blue-50 p-5 rounded-lg border-l-4 border-blue-500 leading-relaxed">
                  <p className="text-base whitespace-pre-line">
                    {currentDocument.summary}
                  </p>
                </div>
              </div>
            )}

            {/* Factual Background - NEW */}
            {(currentDocument as any).factual_background && (
              <div>
                <h3 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="w-6 h-6 text-indigo-600" />
                  Factual Background
                </h3>
                <div className="text-gray-800 bg-indigo-50 p-5 rounded-lg border-l-4 border-indigo-500">
                  <p className="text-base whitespace-pre-line">
                    {(currentDocument as any).factual_background}
                  </p>
                </div>
              </div>
            )}

            {/* Immediate Actions Required - NEW */}
            {(currentDocument as any).immediate_actions && (currentDocument as any).immediate_actions.length > 0 && (
              <div>
                <h3 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6 text-red-600" />
                  Immediate Actions Required
                </h3>
                <div className="bg-red-50 p-5 rounded-lg border-l-4 border-red-500">
                  <ul className="space-y-3">
                    {(currentDocument as any).immediate_actions.map((action: string, index: number) => (
                      <li key={index} className="text-gray-800 flex items-start gap-3">
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
                <h3 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
                  <Scale className="w-6 h-6 text-purple-600" />
                  Relief/Remedies Requested
                </h3>
                <div className="text-gray-800 bg-purple-50 p-5 rounded-lg border-l-4 border-purple-500">
                  <p className="text-base whitespace-pre-line">
                    {(currentDocument as any).relief_requested}
                  </p>
                </div>
              </div>
            )}

            {/* Potential Risks - NEW */}
            {(currentDocument as any).potential_risks && (currentDocument as any).potential_risks.length > 0 && (
              <div>
                <h3 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-6 h-6 text-orange-600" />
                  Potential Legal Risks
                </h3>
                <div className="bg-orange-50 p-5 rounded-lg border-l-4 border-orange-500">
                  <ul className="space-y-2">
                    {(currentDocument as any).potential_risks.map((risk: string, index: number) => (
                      <li key={index} className="text-gray-800 flex items-start gap-2">
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
                <h3 className="font-bold text-lg text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="w-6 h-6 text-teal-600" />
                  Procedural Status
                </h3>
                <div className="text-gray-800 bg-teal-50 p-5 rounded-lg border-l-4 border-teal-500">
                  <p className="text-base whitespace-pre-line">
                    {(currentDocument as any).procedural_status}
                  </p>
                </div>
              </div>
            )}

            {/* Parties */}
            {currentDocument.parties && currentDocument.parties.length > 0 && (
              <div>
                <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                  <Users className="w-5 h-5 text-purple-600" />
                  Parties Involved
                </h3>
                <div className="bg-purple-50 p-4 rounded-lg border-l-4 border-purple-500">
                  <ul className="space-y-1">
                    {currentDocument.parties.map((party, index) => (
                      <li key={index} className="text-gray-700 flex items-center gap-2">
                        <span className="w-2 h-2 bg-purple-600 rounded-full"></span>
                        {party}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Important Dates */}
            {currentDocument.importantDates && currentDocument.importantDates.length > 0 && (
              <div>
                <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-green-600" />
                  Important Dates
                </h3>
                <div className="bg-green-50 p-4 rounded-lg border-l-4 border-green-500 space-y-2">
                  {currentDocument.importantDates.map((dateInfo, index) => (
                    <div key={index} className="flex items-start gap-3">
                      <span className="font-semibold text-green-900 min-w-[100px]">
                        {dateInfo.date}
                      </span>
                      <span className="text-gray-700">{dateInfo.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Key Figures */}
            {currentDocument.keyFigures && currentDocument.keyFigures.length > 0 && (
              <div>
                <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-amber-600" />
                  Key Figures & Numbers
                </h3>
                <div className="bg-amber-50 p-4 rounded-lg border-l-4 border-amber-500 space-y-2">
                  {currentDocument.keyFigures.map((figure, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-gray-700">{figure.label}:</span>
                      <span className="font-bold text-amber-900">{figure.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Keywords */}
            {currentDocument.keywords && currentDocument.keywords.length > 0 && (
              <div>
                <h3 className="font-bold text-gray-900 mb-2 flex items-center gap-2">
                  <Tag className="w-5 h-5 text-indigo-600" />
                  Keywords & Terms
                </h3>
                <div className="bg-indigo-50 p-4 rounded-lg border-l-4 border-indigo-500">
                  <div className="flex flex-wrap gap-2">
                    {currentDocument.keywords.map((keyword, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-indigo-200 text-indigo-900 rounded-full text-sm font-medium"
                      >
                        {keyword}
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

      {/* Bankruptcy Analysis Section */}
      {currentDocument && !showBankruptcyAnalysis && (
        <Card className="mt-6 border-2 border-orange-300 bg-orange-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-orange-900">
              <Scale className="w-6 h-6" />
              Bankruptcy Document Analysis
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-orange-800 text-sm">
                Run comprehensive bankruptcy analysis on this document to extract:
              </p>
              <ul className="text-orange-800 text-sm list-disc list-inside space-y-1 ml-4">
                <li>All monetary amounts, claims, and settlements</li>
                <li>Ownership structures and control disparities</li>
                <li>Fraud indicators and preferential treatments</li>
                <li>Legal violations and precedent conflicts</li>
                <li>Settlement metrics and recovery rates</li>
              </ul>
              <div className="flex gap-4">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => {
                    const file = e.target.files?.[0];
                    if (file) handleBankruptcyAnalysis(file);
                  }}
                  accept=".pdf"
                  className="hidden"
                  id="bankruptcy-file-input"
                />
                <Button
                  onClick={() => document.getElementById('bankruptcy-file-input')?.click()}
                  disabled={isAnalyzing}
                  className="bg-orange-600 hover:bg-orange-700 text-white"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing Bankruptcy Document...
                    </>
                  ) : (
                    <>
                      <Scale className="w-4 h-4 mr-2" />
                      Run Bankruptcy Analysis
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bankruptcy Analysis Dashboard */}
      {showBankruptcyAnalysis && bankruptcyAnalysisData && (
        <div className="mt-6">
          <div className="mb-4 flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <Scale className="w-7 h-7 text-orange-600" />
                Bankruptcy Analysis Results
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Analyzed: <span className="font-semibold">{bankruptcyAnalysisData.filename}</span>
              </p>
            </div>
            <Button
              onClick={() => {
                setShowBankruptcyAnalysis(false);
                setBankruptcyAnalysisData(null);
              }}
              variant="outline"
              className="flex items-center gap-2"
            >
              <X className="w-4 h-4" />
              Close Analysis
            </Button>
          </div>
          <BankruptcyAnalysisDashboard data={bankruptcyAnalysisData} />
        </div>
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
