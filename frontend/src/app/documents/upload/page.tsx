'use client';

import React, { useState, useCallback, useRef } from 'react';
import {
  Upload,
  File,
  AlertTriangle,
  Shield,
  Scale,
  Info,
  CheckCircle,
  X,
  FileText,
  Eye,
  Clock,
  User,
  Lock,
  Download,
  ExternalLink
} from 'lucide-react';

interface UploadedFile {
  id: string;
  file: File;
  privilegeLevel: 'public' | 'confidential' | 'attorney_client' | 'work_product';
  documentType: string;
  description: string;
  uploadedBy: string;
  uploadedAt: string;
  chainOfCustody: ChainEvent[];
  status: 'uploading' | 'uploaded' | 'processing' | 'analyzed' | 'error';
  confidentialityAgreement: boolean;
}

interface ChainEvent {
  timestamp: string;
  event: string;
  user: string;
  details: string;
}

const DocumentUploadPage: React.FC = () => {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [showPrivilegeGuide, setShowPrivilegeGuide] = useState(false);
  const [currentFile, setCurrentFile] = useState<{
    file: File;
    privilegeLevel: string;
    documentType: string;
    description: string;
    confidentialityAgreement: boolean;
  } | null>(null);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [totalFilesInBatch, setTotalFilesInBatch] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedFileTypes = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'image/jpeg',
    'image/png'
  ];

  const acceptedExtensions = '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png';

  const documentTypes = [
    'Contract/Agreement',
    'Court Filing',
    'Correspondence',
    'Evidence/Exhibit',
    'Medical Records',
    'Financial Document',
    'Legal Brief',
    'Deposition Transcript',
    'Expert Report',
    'Other Legal Document'
  ];

  const privilegeLevels = [
    {
      value: 'public',
      label: 'Public Information',
      description: 'No confidentiality restrictions',
      icon: <Info className="h-4 w-4" />,
      color: 'bg-gray-100 text-gray-800 border-gray-200',
      warning: null
    },
    {
      value: 'confidential',
      label: 'Confidential',
      description: 'Protected by confidentiality agreement',
      icon: <Eye className="h-4 w-4" />,
      color: 'bg-blue-100 text-blue-800 border-blue-200',
      warning: 'Handle according to confidentiality requirements'
    },
    {
      value: 'attorney_client',
      label: 'Attorney-Client Privileged',
      description: 'Protected by attorney-client privilege',
      icon: <Shield className="h-4 w-4" />,
      color: 'bg-error-100 text-error-800 border-error-200',
      warning: 'PRIVILEGED - Unauthorized disclosure may waive privilege'
    },
    {
      value: 'work_product',
      label: 'Work Product',
      description: 'Protected attorney work product',
      icon: <Shield className="h-4 w-4" />,
      color: 'bg-warning-100 text-warning-800 border-warning-200',
      warning: 'WORK PRODUCT - Protected from discovery'
    }
  ];

  const validateFile = (file: File): string | null => {
    if (!allowedFileTypes.includes(file.type)) {
      return 'File type not allowed. Please upload PDF, Word, text, or image files.';
    }
    if (file.size > 50 * 1024 * 1024) {
      return 'File size too large. Maximum size is 50MB.';
    }
    return null;
  };

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      // Validate all files first
      for (const file of files) {
        const error = validateFile(file);
        if (error) {
          alert(`${file.name}: ${error}`);
          return;
        }
      }

      // Set the first file for processing
      const [firstFile, ...remainingFiles] = files;
      setCurrentFile({
        file: firstFile,
        privilegeLevel: '',
        documentType: '',
        description: '',
        confidentialityAgreement: false
      });

      // Store remaining files for sequential processing
      setPendingFiles(remainingFiles);
      setTotalFilesInBatch(files.length);

      // Notify user about batch processing
      if (files.length > 1) {
        alert(`${files.length} files selected. You'll configure privilege settings for each file individually.`);
      }
    }
  }, []);

  const onDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const onDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0) {
      // Validate all files first
      for (const file of files) {
        const error = validateFile(file);
        if (error) {
          alert(`${file.name}: ${error}`);
          return;
        }
      }

      // Set the first file for processing
      const [firstFile, ...remainingFiles] = files;
      setCurrentFile({
        file: firstFile,
        privilegeLevel: '',
        documentType: '',
        description: '',
        confidentialityAgreement: false
      });

      // Store remaining files for sequential processing
      setPendingFiles(remainingFiles);
      setTotalFilesInBatch(files.length);

      // Notify user about batch processing
      if (files.length > 1) {
        alert(`${files.length} files selected. You'll configure privilege settings for each file individually.`);
      }
    }
  };

  const handleUpload = () => {
    if (!currentFile) return;

    const uploadedFile: UploadedFile = {
      id: Date.now().toString(),
      file: currentFile.file,
      privilegeLevel: currentFile.privilegeLevel as any,
      documentType: currentFile.documentType,
      description: currentFile.description,
      uploadedBy: 'Current User',
      uploadedAt: new Date().toISOString(),
      chainOfCustody: [
        {
          timestamp: new Date().toISOString(),
          event: 'Document Uploaded',
          user: 'Current User',
          details: `File: ${currentFile.file.name}, Type: ${currentFile.documentType}, Privilege: ${currentFile.privilegeLevel}`
        }
      ],
      status: 'uploading',
      confidentialityAgreement: currentFile.confidentialityAgreement
    };

    setUploadedFiles(prev => [...prev, uploadedFile]);
    setCurrentFile(null);

    // Simulate upload process
    setTimeout(() => {
      setUploadedFiles(prev => prev.map(f =>
        f.id === uploadedFile.id
          ? { ...f, status: 'uploaded', chainOfCustody: [...f.chainOfCustody, {
              timestamp: new Date().toISOString(),
              event: 'Upload Completed',
              user: 'System',
              details: 'File successfully uploaded and secured'
            }] }
          : f
      ));

      // Check if there are more files to process
      if (pendingFiles.length > 0) {
        const [nextFile, ...remaining] = pendingFiles;
        setPendingFiles(remaining);

        // Load next file for configuration
        setTimeout(() => {
          setCurrentFile({
            file: nextFile,
            privilegeLevel: '',
            documentType: '',
            description: '',
            confidentialityAgreement: false
          });
        }, 500); // Small delay for better UX
      } else {
        // Reset batch tracking when all files are done
        setTotalFilesInBatch(0);
      }
    }, 2000);
  };

  const getPrivilegeConfig = (level: string) => {
    return privilegeLevels.find(p => p.value === level) || privilegeLevels[0];
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Document Upload & Processing</h1>
          <p className="text-gray-600">
            Secure document upload with privilege designation and chain of custody tracking
          </p>
        </div>

        {/* Professional Responsibility Warning */}
        <div className="mb-6 bg-legal-50 border border-legal-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <Scale className="h-5 w-5 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-legal-900 mb-2">Professional Responsibility Notice</h3>
              <ul className="text-sm text-legal-700 space-y-1">
                <li>• Proper privilege designation is essential for maintaining confidentiality protections</li>
                <li>• Once uploaded, privilege levels should not be changed without careful consideration</li>
                <li>• All document handling must comply with applicable ethical rules and court orders</li>
                <li>• Maintain secure custody and access controls for privileged materials</li>
                <li>• Document metadata and processing logs create permanent audit trails</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Batch Upload Progress Indicator */}
        {totalFilesInBatch > 1 && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileText className="h-5 w-5 text-blue-600" />
                <div>
                  <h3 className="text-sm font-semibold text-blue-900">
                    Batch Upload in Progress
                  </h3>
                  <p className="text-sm text-blue-700">
                    Processing file {uploadedFiles.length + (currentFile ? 1 : 0)} of {totalFilesInBatch}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-sm font-medium text-blue-900">
                    {uploadedFiles.length} completed
                  </div>
                  <div className="text-xs text-blue-600">
                    {pendingFiles.length} remaining
                  </div>
                </div>
                {pendingFiles.length > 0 && (
                  <button
                    onClick={() => {
                      if (confirm(`Cancel upload for ${pendingFiles.length} remaining file${pendingFiles.length > 1 ? 's' : ''}?`)) {
                        setPendingFiles([]);
                        setTotalFilesInBatch(0);
                        setCurrentFile(null);
                      }
                    }}
                    className="text-xs px-3 py-1 bg-red-100 text-red-700 hover:bg-red-200 rounded-md font-medium"
                  >
                    Cancel Batch
                  </button>
                )}
              </div>
            </div>
            {/* Progress bar */}
            <div className="mt-3 w-full bg-blue-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(uploadedFiles.length / totalFilesInBatch) * 100}%` }}
              />
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Upload Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Upload Document</h2>
              <button
                onClick={() => setShowPrivilegeGuide(!showPrivilegeGuide)}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                <Info className="h-4 w-4 inline mr-1" />
                Privilege Guide
              </button>
            </div>

            {/* Privilege Guide */}
            {showPrivilegeGuide && (
              <div className="mb-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                <h4 className="text-sm font-semibold text-blue-900 mb-2">Privilege Level Guidelines</h4>
                <div className="space-y-2 text-sm text-blue-800">
                  {privilegeLevels.map(level => (
                    <div key={level.value} className="flex items-start space-x-2">
                      <div className="text-blue-600 mt-0.5">{level.icon}</div>
                      <div>
                        <strong>{level.label}:</strong> {level.description}
                        {level.warning && (
                          <div className="text-xs text-amber-700 mt-1">⚠️ {level.warning}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!currentFile ? (
              /* Drop Zone */
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragOver 
                    ? 'border-primary-400 bg-primary-50' 
                    : 'border-gray-300 hover:border-gray-400'
                }`}
                onDrop={onDrop}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
              >
                <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Drop files here to upload</h3>
                <p className="text-gray-500 mb-4">or click to select files</p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center px-4 py-2 border border-primary-600 text-sm font-medium rounded-md text-primary-600 bg-white hover:bg-primary-50"
                >
                  Select Files
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  onChange={handleFileSelect}
                  className="hidden"
                  accept={acceptedExtensions}
                />
                <div className="mt-4 text-xs text-gray-500">
                  Supported: PDF, Word, Text, Images • Max size: 50MB
                </div>
              </div>
            ) : (
              /* File Configuration */
              <div className="space-y-4">
                <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <FileText className="h-8 w-8 text-blue-600" />
                  <div>
                    <h4 className="font-medium text-gray-900">{currentFile.file.name}</h4>
                    <p className="text-sm text-gray-500">
                      {(currentFile.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  <button
                    onClick={() => setCurrentFile(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* Privilege Level Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Privilege Level *
                  </label>
                  <div className="space-y-2">
                    {privilegeLevels.map(level => (
                      <label key={level.value} className="flex items-start space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer">
                        <input
                          type="radio"
                          name="privilegeLevel"
                          value={level.value}
                          checked={currentFile.privilegeLevel === level.value}
                          onChange={(e) => setCurrentFile({...currentFile, privilegeLevel: e.target.value})}
                          className="mt-1"
                        />
                        <div className="text-gray-600 mt-0.5">{level.icon}</div>
                        <div className="flex-1">
                          <div className="font-medium text-gray-900">{level.label}</div>
                          <div className="text-sm text-gray-600">{level.description}</div>
                          {level.warning && (
                            <div className="text-xs text-amber-700 mt-1 font-medium">
                              ⚠️ {level.warning}
                            </div>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Document Type */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Document Type *
                  </label>
                  <select
                    value={currentFile.documentType}
                    onChange={(e) => setCurrentFile({...currentFile, documentType: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Select document type...</option>
                    {documentTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={currentFile.description}
                    onChange={(e) => setCurrentFile({...currentFile, description: e.target.value})}
                    placeholder="Brief description of the document and its relevance..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
                    rows={3}
                  />
                </div>

                {/* Confidentiality Agreement */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                  <label className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      checked={currentFile.confidentialityAgreement}
                      onChange={(e) => setCurrentFile({...currentFile, confidentialityAgreement: e.target.checked})}
                      className="mt-1"
                    />
                    <div className="text-sm">
                      <div className="font-medium text-amber-900">Confidentiality Acknowledgment</div>
                      <div className="text-amber-800 mt-1">
                        I acknowledge that this document will be processed using AI technology and understand 
                        the privilege designation I have selected. I confirm that I have the authority to 
                        upload this document and designate its privilege level.
                      </div>
                    </div>
                  </label>
                </div>

                {/* Upload Button */}
                <button
                  onClick={handleUpload}
                  disabled={!currentFile.privilegeLevel || !currentFile.documentType || !currentFile.confidentialityAgreement}
                  className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Upload & Process Document
                </button>
              </div>
            )}
          </div>

          {/* Uploaded Files Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Uploaded Documents</h2>
            
            {uploadedFiles.length === 0 ? (
              <div className="text-center py-8">
                <File className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No documents uploaded yet</p>
              </div>
            ) : (
              <div className="space-y-4">
                {uploadedFiles.map(file => {
                  const privilegeConfig = getPrivilegeConfig(file.privilegeLevel);
                  return (
                    <div key={file.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-3">
                          <FileText className="h-6 w-6 text-blue-600" />
                          <div>
                            <h4 className="font-medium text-gray-900">{file.file.name}</h4>
                            <p className="text-sm text-gray-500">{file.documentType}</p>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${privilegeConfig.color}`}>
                            {privilegeConfig.icon}
                            <span className="ml-1">{privilegeConfig.label}</span>
                          </span>
                          
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            file.status === 'uploading' ? 'bg-blue-100 text-blue-800' :
                            file.status === 'uploaded' ? 'bg-success-100 text-success-800' :
                            file.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                            file.status === 'analyzed' ? 'bg-green-100 text-green-800' :
                            'bg-error-100 text-error-800'
                          }`}>
                            {file.status.toUpperCase()}
                          </span>
                        </div>
                      </div>

                      {file.description && (
                        <p className="text-sm text-gray-600 mb-2">{file.description}</p>
                      )}

                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center space-x-4">
                          <div className="flex items-center space-x-1">
                            <User className="h-3 w-3" />
                            <span>Uploaded by {file.uploadedBy}</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Clock className="h-3 w-3" />
                            <span>{new Date(file.uploadedAt).toLocaleString()}</span>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <button className="text-primary-600 hover:text-primary-700 font-medium">
                            View Chain of Custody
                          </button>
                          {file.status === 'analyzed' && (
                            <button className="text-primary-600 hover:text-primary-700 font-medium">
                              View Analysis
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Chain of Custody Information */}
        <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-2 mb-4">
            <Shield className="h-5 w-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-gray-900">Chain of Custody & Security</h2>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-2">Automatic Tracking</h3>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• Upload timestamp and user identification</li>
                <li>• Privilege level designation and changes</li>
                <li>• Processing status and AI analysis events</li>
                <li>• Access logs and document views</li>
                <li>• Export and sharing activities</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-2">Security Measures</h3>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• End-to-end encryption for privileged documents</li>
                <li>• Access controls based on privilege levels</li>
                <li>• Automated backup and disaster recovery</li>
                <li>• Audit trail preservation and integrity</li>
                <li>• Compliance with legal retention requirements</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Usage Guidelines */}
        <div className="mt-6 bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-amber-800 mb-2">Document Upload Guidelines</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-amber-700">
                <div>
                  <h4 className="font-medium mb-1">Before Uploading:</h4>
                  <ul className="space-y-1">
                    <li>• Verify you have authority to upload the document</li>
                    <li>• Determine correct privilege level designation</li>
                    <li>• Remove or redact unnecessary personal information</li>
                    <li>• Ensure document is relevant to the matter</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-medium mb-1">After Uploading:</h4>
                  <ul className="space-y-1">
                    <li>• Verify privilege designation was applied correctly</li>
                    <li>• Monitor processing status for any errors</li>
                    <li>• Review AI analysis results for accuracy</li>
                    <li>• Maintain original documents per retention policies</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUploadPage;