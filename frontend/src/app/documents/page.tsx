/**
 * Main Documents Page
 * Multi-document upload with full-featured interface
 */

'use client';

import React, { useState } from 'react';
import { MultiDocumentUpload } from '@/components/Documents/MultiDocumentUpload';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Badge,
  EmptyState,
} from '@/components/design-system';
import {
  FileText,
  Calendar,
  Users,
  DollarSign,
  Tag,
  CheckCircle,
  Trash2,
  Upload,
  FolderOpen,
  Clock,
  ArrowRight,
} from 'lucide-react';
import { useDocuments } from '@/contexts/DocumentContext';
import { useConfirmDialog } from '@/components/ConfirmDialog';
import { toast } from 'sonner';

export default function DocumentsPage() {
  const { documents, currentDocument, setCurrentDocument, removeDocument } = useDocuments();
  const { confirm, ConfirmDialog } = useConfirmDialog();
  const [showUploadSection, setShowUploadSection] = useState(true);

  const handleDeleteDocument = async (docId: string, docName: string) => {
    await confirm({
      title: 'Delete Document?',
      description: `Are you sure you want to delete "${docName}"? This action cannot be undone.`,
      confirmText: 'Delete',
      cancelText: 'Cancel',
      variant: 'danger',
      icon: <Trash2 className="w-6 h-6 text-error-600" />,
      onConfirm: async () => {
        try {
          await removeDocument(docId);
          toast.success('Document deleted', {
            description: `"${docName}" has been removed`,
            duration: 3000,
          });
        } catch (error) {
          console.error('Delete error:', error);
          toast.error('Failed to delete document');
        }
      }
    });
  };

  const handleUploadComplete = (files: any[]) => {
    console.log('Upload complete:', files);
    toast.success('All uploads complete!', {
      description: `${files.filter(f => f.status === 'complete').length} documents processed successfully`,
      duration: 5000,
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-content mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-navy-800 dark:text-slate-100 flex items-center gap-3">
                <div className="p-2 bg-teal-50 dark:bg-slate-700 rounded-lg">
                  <FileText className="w-6 h-6 text-teal-600 dark:text-teal-400" />
                </div>
                Document Management
              </h1>
              <p className="text-slate-500 dark:text-slate-400 mt-2">
                Upload, analyze, and manage your legal documents with AI-powered intelligence
              </p>
            </div>
            <Button
              variant={showUploadSection ? 'outline' : 'primary'}
              onClick={() => setShowUploadSection(!showUploadSection)}
              leftIcon={showUploadSection ? <FolderOpen className="w-4 h-4" /> : <Upload className="w-4 h-4" />}
            >
              {showUploadSection ? 'View Library' : 'Upload Documents'}
            </Button>
          </div>

          {/* Feature badges */}
          <div className="mt-4 flex flex-wrap gap-2">
            <Badge variant="info" size="sm">
              <CheckCircle className="w-3 h-3" />
              Multi-Upload
            </Badge>
            <Badge variant="success" size="sm">
              <CheckCircle className="w-3 h-3" />
              AI Analysis
            </Badge>
            <Badge variant="info" size="sm">
              <CheckCircle className="w-3 h-3" />
              Drag & Drop
            </Badge>
            <Badge variant="success" size="sm">
              <CheckCircle className="w-3 h-3" />
              Progress Tracking
            </Badge>
          </div>
        </div>

        {/* Multi-Document Upload Section */}
        {showUploadSection && (
          <div className="mb-8">
            <MultiDocumentUpload
              maxConcurrentUploads={3}
              maxFileSize={50}
              acceptedFileTypes={['.pdf', '.doc', '.docx', '.txt']}
              onUploadComplete={handleUploadComplete}
            />
          </div>
        )}

        {/* Document Library Section */}
        {!showUploadSection && documents.length > 0 && (
          <>
            {/* Documents List */}
            <Card className="mb-8">
              <CardHeader>
                <CardTitle icon={<FolderOpen className="w-5 h-5" />}>
                  Document Library
                </CardTitle>
                <CardDescription>
                  {documents.length} document{documents.length !== 1 ? 's' : ''} in your library
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                        currentDocument?.id === doc.id
                          ? 'border-teal-500 bg-teal-50/50'
                          : 'border-slate-200 hover:border-teal-300 hover:bg-slate-50'
                      }`}
                      onClick={() => setCurrentDocument(doc)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <div className="p-1.5 bg-navy-50 rounded">
                              <FileText className="w-4 h-4 text-navy-600" />
                            </div>
                            <span className="font-semibold text-navy-800">{doc.fileName}</span>
                            {currentDocument?.id === doc.id && (
                              <Badge variant="success" size="sm">
                                <CheckCircle className="w-3 h-3" />
                                Selected
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-1 mt-2 text-slate-500 text-sm">
                            <Clock className="w-3 h-3" />
                            <span>Uploaded: {doc.uploadDate.toLocaleString()}</span>
                          </div>
                          {doc.summary && (
                            <p className="text-sm text-slate-600 mt-2 line-clamp-2">
                              {doc.summary.substring(0, 150)}...
                            </p>
                          )}
                        </div>
                        <Button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteDocument(doc.id, doc.fileName);
                          }}
                          variant="ghost"
                          size="sm"
                        >
                          <Trash2 className="w-4 h-4 text-error-500" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Current Document Analysis */}
            {currentDocument && (
              <Card>
                <CardHeader>
                  <CardTitle icon={<FileText className="w-5 h-5" />}>
                    Document Analysis
                  </CardTitle>
                  <CardDescription>{currentDocument.fileName}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Summary */}
                  {currentDocument.summary && (
                    <div className="p-4 bg-navy-50 rounded-lg border-l-4 border-navy-500">
                      <h3 className="font-semibold text-navy-800 mb-2 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-navy-600" />
                        Summary
                      </h3>
                      <p className="text-slate-700 leading-relaxed whitespace-pre-line">
                        {currentDocument.summary}
                      </p>
                    </div>
                  )}

                  {/* Parties */}
                  {currentDocument.parties && currentDocument.parties.length > 0 && (
                    <div className="p-4 bg-purple-50 rounded-lg border-l-4 border-purple-500">
                      <h3 className="font-semibold text-purple-800 mb-3 flex items-center gap-2">
                        <Users className="w-4 h-4 text-purple-600" />
                        Parties Involved
                      </h3>
                      <ul className="space-y-2">
                        {currentDocument.parties.map((party, index) => {
                          const partyName = typeof party === 'string'
                            ? party
                            : (party as any)?.name || String(party);
                          const partyRole = typeof party === 'object' && (party as any)?.role
                            ? ` (${(party as any).role})`
                            : '';
                          return (
                            <li key={index} className="text-slate-700 flex items-center gap-2">
                              <span className="w-2 h-2 bg-purple-500 rounded-full"></span>
                              {partyName}{partyRole}
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  )}

                  {/* Important Dates */}
                  {currentDocument.importantDates && currentDocument.importantDates.length > 0 && (
                    <div className="p-4 bg-success-50 rounded-lg border-l-4 border-success-500">
                      <h3 className="font-semibold text-success-800 mb-3 flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-success-600" />
                        Important Dates
                      </h3>
                      <div className="space-y-2">
                        {currentDocument.importantDates.map((dateInfo, index) => (
                          <div key={index} className="flex items-start gap-3">
                            <span className="font-semibold text-success-700 min-w-[100px]">
                              {dateInfo.date}
                            </span>
                            <span className="text-slate-700">{dateInfo.description}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Key Figures */}
                  {currentDocument.keyFigures && currentDocument.keyFigures.length > 0 && (
                    <div className="p-4 bg-warning-50 rounded-lg border-l-4 border-warning-500">
                      <h3 className="font-semibold text-warning-800 mb-3 flex items-center gap-2">
                        <DollarSign className="w-4 h-4 text-warning-600" />
                        Key Figures & Numbers
                      </h3>
                      <div className="space-y-2">
                        {currentDocument.keyFigures.map((figure, index) => (
                          <div key={index} className="flex items-center justify-between">
                            <span className="text-slate-700">{figure.label}:</span>
                            <span className="font-bold text-warning-800">{figure.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Keywords */}
                  {currentDocument.keywords && currentDocument.keywords.length > 0 && (
                    <div className="p-4 bg-indigo-50 rounded-lg border-l-4 border-indigo-500">
                      <h3 className="font-semibold text-indigo-800 mb-3 flex items-center gap-2">
                        <Tag className="w-4 h-4 text-indigo-600" />
                        Keywords & Terms
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {currentDocument.keywords.map((keyword: any, index: number) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium"
                            title={typeof keyword === 'object' && keyword?.explanation ? keyword.explanation : undefined}
                          >
                            {typeof keyword === 'object' ? (keyword?.term || keyword?.name || JSON.stringify(keyword)) : keyword}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Empty State for Library */}
        {!showUploadSection && documents.length === 0 && (
          <Card className="bg-slate-50/50">
            <CardContent className="py-12">
              <EmptyState
                icon="document"
                title="No Documents Yet"
                description="Upload your first document to get started with AI-powered analysis"
                action={{
                  label: 'Upload Documents',
                  onClick: () => setShowUploadSection(true),
                  variant: 'primary',
                }}
              />
            </CardContent>
          </Card>
        )}

        {/* Quick Stats */}
        {documents.length > 0 && (
          <Card className="mt-8 bg-gradient-to-br from-navy-50 to-teal-50 border-none">
            <CardContent className="py-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                <div>
                  <p className="text-3xl font-bold text-navy-800">{documents.length}</p>
                  <p className="text-sm text-slate-600">Total Documents</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-navy-800">
                    {documents.reduce((sum, doc) => sum + (doc.parties?.length || 0), 0)}
                  </p>
                  <p className="text-sm text-slate-600">Parties Identified</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-teal-700">
                    {documents.reduce((sum, doc) => sum + (doc.importantDates?.length || 0), 0)}
                  </p>
                  <p className="text-sm text-slate-600">Important Dates</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-teal-700">
                    {documents.reduce((sum, doc) => sum + (doc.keywords?.length || 0), 0)}
                  </p>
                  <p className="text-sm text-slate-600">Keywords Extracted</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Action CTA */}
        {showUploadSection && documents.length > 0 && (
          <Card className="mt-8">
            <CardContent className="py-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-navy-800">
                    Have documents in your library?
                  </h3>
                  <p className="text-slate-500 mt-1">
                    View and analyze your previously uploaded documents
                  </p>
                </div>
                <Button
                  onClick={() => setShowUploadSection(false)}
                  variant="outline"
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                >
                  View Library
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Confirmation Dialog */}
      <ConfirmDialog />
    </div>
  );
}
