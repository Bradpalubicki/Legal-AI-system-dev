'use client';

import React, { useState } from 'react';
import BankruptcyMultiFileUpload from '@/components/BankruptcyMultiFileUpload';
import { CheckCircle, AlertCircle, FileText } from 'lucide-react';

import { API_CONFIG } from '../../../config/api';
export default function BankruptcyUploadPage() {
  const [uploadedDocuments, setUploadedDocuments] = useState<any[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string>('');

  // Example case ID (in real app, would come from router params or context)
  const currentCaseId = 'case-12345';

  const handleUploadComplete = (response: any) => {
    console.log('Upload complete:', response);

    // Add uploaded documents to state
    if (response.documents && response.documents.length > 0) {
      setUploadedDocuments(prev => [...prev, ...response.documents]);
    }

    // Show success message
    setSuccessMessage(response.message || `Successfully uploaded ${response.documents?.length || 0} documents`);
    setShowSuccess(true);
    setErrorMessage(null);

    // Hide success message after 5 seconds
    setTimeout(() => setShowSuccess(false), 5000);
  };

  const handleUploadError = (error: Error) => {
    console.error('Upload error:', error);
    setErrorMessage(error.message);
    setShowSuccess(false);

    // Hide error message after 10 seconds
    setTimeout(() => setErrorMessage(null), 10000);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Bankruptcy Document Upload
          </h1>
          <p className="text-gray-600">
            Upload all relevant documents for your bankruptcy case. You can select multiple files at once.
          </p>
        </div>

        {/* Success Message */}
        {showSuccess && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <div>
                <h3 className="text-sm font-semibold text-green-900">
                  Upload Successful!
                </h3>
                <p className="text-sm text-green-800">
                  {successMessage || 'Your documents have been uploaded and are being processed.'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error Message */}
        {errorMessage && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <div>
                <h3 className="text-sm font-semibold text-red-900">
                  Upload Failed
                </h3>
                <p className="text-sm text-red-800">{errorMessage}</p>
              </div>
            </div>
          </div>
        )}

        {/* Multi-File Upload Component */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
          <BankruptcyMultiFileUpload
            onUploadComplete={handleUploadComplete}
            onUploadError={handleUploadError}
            uploadEndpoint={`${API_CONFIG.BASE_URL}/api/v1/batch/upload`}
            caseId={currentCaseId}
          />
        </div>

        {/* Uploaded Documents List */}
        {uploadedDocuments.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Previously Uploaded Documents ({uploadedDocuments.length})
            </h2>

            <div className="space-y-2">
              {uploadedDocuments.map((doc, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {doc.filename || `Document ${index + 1}`}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                        <span>Type: {doc.type || 'Unknown'}</span>
                        <span>Size: {Math.round(doc.size / 1024)} KB</span>
                      </div>
                    </div>
                  </div>
                  <a
                    href={doc.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                  >
                    View
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Guidelines Section */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            Document Checklist for Bankruptcy Filing
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h4 className="text-sm font-medium text-blue-800 mb-2">
                Financial Documents
              </h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Bank statements (6 months)</li>
                <li>• Pay stubs (60 days)</li>
                <li>• Tax returns (2 years)</li>
                <li>• Investment statements</li>
                <li>• Retirement account statements</li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-medium text-blue-800 mb-2">
                Debt Documentation
              </h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Credit card statements</li>
                <li>• Loan documents</li>
                <li>• Medical bills</li>
                <li>• Collection notices</li>
                <li>• Lawsuit documents</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
