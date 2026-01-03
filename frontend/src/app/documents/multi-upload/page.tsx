/**
 * Multi-Document Upload Page
 * Demonstrates the multi-document upload component
 */

'use client';

import React from 'react';
import { MultiDocumentUpload } from '@/components/Documents/MultiDocumentUpload';
import { Card } from '@/components/ui/card';

export default function MultiUploadPage() {
  const handleUploadComplete = (files: any[]) => {
    console.log('All uploads complete:', files);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto p-6 max-w-6xl">
        {/* Header */}
        <Card className="p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Multi-Document Upload</h1>
          <p className="text-gray-600 mt-2">
            Upload multiple legal documents simultaneously with AI-powered analysis
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
              ✓ Drag & Drop Support
            </span>
            <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium">
              ✓ Multiple Files
            </span>
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
              ✓ Progress Tracking
            </span>
            <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-full text-sm font-medium">
              ✓ Queue Management
            </span>
            <span className="px-3 py-1 bg-pink-100 text-pink-700 rounded-full text-sm font-medium">
              ✓ AI Analysis
            </span>
          </div>
        </Card>

        {/* Multi-Document Upload Component */}
        <MultiDocumentUpload
          maxConcurrentUploads={3}
          maxFileSize={50}
          acceptedFileTypes={['.pdf', '.doc', '.docx', '.txt']}
          onUploadComplete={handleUploadComplete}
        />

        {/* Features Info */}
        <Card className="mt-6 p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-800">Upload Methods</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Click to browse and select multiple files</li>
                <li>• Drag and drop multiple files at once</li>
                <li>• Automatic file validation</li>
                <li>• Size and type checking</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-800">Queue Management</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Concurrent upload control (3 at a time)</li>
                <li>• Real-time progress tracking</li>
                <li>• Individual file status monitoring</li>
                <li>• Retry failed uploads</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-800">AI Processing</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Automatic text extraction</li>
                <li>• AI-powered document analysis</li>
                <li>• Party and date identification</li>
                <li>• Key terms extraction</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h3 className="font-semibold text-gray-800">User Controls</h3>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Cancel individual uploads</li>
                <li>• Retry failed files</li>
                <li>• Clear completed files</li>
                <li>• Remove from queue</li>
              </ul>
            </div>
          </div>
        </Card>

        {/* Usage Instructions */}
        <Card className="mt-6 p-6 bg-blue-50 border-blue-200">
          <h2 className="text-xl font-bold text-blue-900 mb-4">How to Use</h2>
          <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
            <li>Click the upload zone or drag and drop multiple PDF, DOC, DOCX, or TXT files</li>
            <li>Files will be automatically added to the upload queue</li>
            <li>The system will process up to 3 files concurrently</li>
            <li>Each file goes through text extraction and AI analysis</li>
            <li>Monitor progress with individual progress bars</li>
            <li>Completed documents are automatically added to your document library</li>
            <li>Use the retry button for any failed uploads</li>
            <li>Clear completed files to clean up the queue</li>
          </ol>
        </Card>
      </div>
    </div>
  );
}
