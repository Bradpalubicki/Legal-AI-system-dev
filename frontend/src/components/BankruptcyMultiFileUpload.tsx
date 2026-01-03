'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { API_CONFIG } from '../config/api';
import {
  Upload,
  X,
  File as FileIcon,
  CheckCircle,
  AlertCircle,
  Loader2,
  Trash2,
  Calendar,
  FileText,
  Settings,
  AlertTriangle,
  Pause,
  Play,
  RotateCcw,
  Download,
  XCircle,
  Clock,
  Shield,
  ShieldAlert,
  Lock,
  Key,
  ShieldCheck
} from 'lucide-react';

interface DocumentClassification {
  suggestedType: string;
  caseNumber?: string;
  exhibitNumber?: string;
  confidence: 'high' | 'medium' | 'low';
}

interface UploadLog {
  fileId: string;
  filename: string;
  timestamp: Date;
  status: 'started' | 'completed' | 'failed' | 'cancelled';
  error?: string;
  duration?: number;
  size: number;
}

interface SecurityValidation {
  mimeTypeValid: boolean;
  mimeType: string;
  structureValid: boolean;
  isPasswordProtected: boolean;
  hashedSHA256?: string;
  isEncrypted: boolean;
  sanitizedFilename?: string;
  maliciousContentDetected: boolean;
  validationErrors: string[];
  validationWarnings: string[];
  securityScore: number; // 0-100
}

interface AuditLog {
  fileId: string;
  filename: string;
  timestamp: Date;
  action: 'validation' | 'upload' | 'security_check' | 'encryption';
  userId?: string;
  ipAddress?: string;
  details: string;
  securityFlags: string[];
}

interface FileWithProgress {
  id: string;
  file: File;
  progress: number;
  status: 'queued' | 'uploading' | 'completed' | 'failed' | 'cancelled' | 'paused' | 'validating';
  errorMessage?: string;
  classification: DocumentClassification;
  selectedType: string;
  retryCount: number;
  uploadSpeed: number; // bytes per second
  startTime?: number;
  endTime?: number;
  xhr?: XMLHttpRequest; // For pause/cancel
  security?: SecurityValidation; // Security validation results
  encryptedBlob?: Blob; // Encrypted file data
}

interface UploadedDocument {
  id: string;
  filename: string;
  size: number;
  type: string;
  url: string;
}

interface UploadResponse {
  success: boolean;
  documents: UploadedDocument[];
  message: string;
}

interface BankruptcyMultiFileUploadProps {
  onUploadComplete?: (response: UploadResponse) => void;
  onUploadError?: (error: Error) => void;
  uploadEndpoint?: string;
  caseId: string; // Now required
  className?: string;
}

const BankruptcyMultiFileUpload: React.FC<BankruptcyMultiFileUploadProps> = ({
  onUploadComplete,
  onUploadError,
  uploadEndpoint,
  caseId,
  className = ''
}) => {
  // Use API_CONFIG for default endpoint if not provided
  const actualEndpoint = uploadEndpoint || `${API_CONFIG.BASE_URL}/api/v1/batch/upload`;
  const [selectedFiles, setSelectedFiles] = useState<FileWithProgress[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // New form fields
  const [documentType, setDocumentType] = useState<string>('motion');
  const [filingDate, setFilingDate] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [descriptionError, setDescriptionError] = useState<string>('');

  // Validation warnings
  const [validationWarnings, setValidationWarnings] = useState<string[]>([]);

  // Queue management
  const [uploadLogs, setUploadLogs] = useState<UploadLog[]>([]);
  const [overallProgress, setOverallProgress] = useState(0);
  const [uploadSpeed, setUploadSpeed] = useState(0); // overall speed in bytes/sec
  const [timeRemaining, setTimeRemaining] = useState(0); // in seconds
  const activeUploadsRef = useRef<Set<string>>(new Set());
  const BATCH_SIZE = 3;
  const MAX_RETRIES = 3;
  const UPLOAD_TIMEOUT = 30000; // 30 seconds

  // Security and compliance
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [uploadCount, setUploadCount] = useState(0); // Track uploads per hour for rate limiting
  const [lastUploadReset, setLastUploadReset] = useState<number>(Date.now());
  const MAX_UPLOADS_PER_HOUR = 100;
  const MAX_FILENAME_LENGTH = 200;
  const ALLOWED_MIME_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/tiff',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain'
  ];
  const RESTRICTED_DOCUMENT_TYPES = ['sealed', 'classified', 'attorney-eyes-only'];

  // Document type options
  const documentTypes = [
    { value: 'motion', label: 'Motion' },
    { value: 'order', label: 'Order' },
    { value: 'notice', label: 'Notice' },
    { value: 'exhibit', label: 'Exhibit' },
    { value: 'creditor_matrix', label: 'Creditor Matrix' },
    { value: 'proof_of_claim', label: 'Proof of Claim' },
    { value: 'other', label: 'Other' }
  ];

  // Classify document based on filename
  const classifyDocument = (filename: string): DocumentClassification => {
    const lowerName = filename.toLowerCase();

    let suggestedType = 'other';
    let confidence: 'high' | 'medium' | 'low' = 'low';
    let caseNumber: string | undefined;
    let exhibitNumber: string | undefined;

    // Extract case number pattern (e.g., 23-12345, 2023-12345)
    const caseNumberMatch = filename.match(/(\d{2,4}[-_]\d{4,6})/);
    if (caseNumberMatch) {
      caseNumber = caseNumberMatch[1];
    }

    // Classify by filename patterns
    if (lowerName.includes('motion')) {
      suggestedType = 'motion';
      confidence = 'high';
    } else if (lowerName.includes('order')) {
      suggestedType = 'order';
      confidence = 'high';
    } else if (lowerName.includes('notice')) {
      suggestedType = 'notice';
      confidence = 'high';
    } else if (lowerName.includes('claim')) {
      suggestedType = 'proof_of_claim';
      confidence = 'high';
    } else if (lowerName.includes('exhibit') || /^[a-z][-_\s]/i.test(filename)) {
      suggestedType = 'exhibit';
      confidence = lowerName.includes('exhibit') ? 'high' : 'medium';

      // Try to extract exhibit letter/number
      const exhibitMatch = filename.match(/exhibit[-_\s]*([a-z0-9]+)/i) ||
                          filename.match(/^([a-z])[-_\s]/i);
      if (exhibitMatch) {
        exhibitNumber = exhibitMatch[1].toUpperCase();
      }
    } else if (lowerName.includes('creditor') || lowerName.includes('matrix')) {
      suggestedType = 'creditor_matrix';
      confidence = 'high';
    }

    return {
      suggestedType,
      caseNumber,
      exhibitNumber,
      confidence
    };
  };

  // Set default filing date to today
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    setFilingDate(today);
  }, []);

  // Calculate overall progress, speed, and time remaining (Phase 5)
  useEffect(() => {
    const completed = selectedFiles.filter(f => f.status === 'completed').length;
    const total = selectedFiles.length;
    const progress = total > 0 ? (completed / total) * 100 : 0;
    setOverallProgress(progress);

    // Calculate overall speed from uploading files
    const uploading = selectedFiles.filter(f => f.status === 'uploading');
    const totalSpeed = uploading.reduce((sum, f) => sum + f.uploadSpeed, 0);
    setUploadSpeed(totalSpeed);

    // Calculate time remaining
    const remaining = selectedFiles.filter(f =>
      f.status === 'queued' || f.status === 'uploading'
    );
    const remainingBytes = remaining.reduce((sum, f) => {
      const uploaded = (f.progress / 100) * f.file.size;
      return sum + (f.file.size - uploaded);
    }, 0);
    const timeRem = totalSpeed > 0 ? remainingBytes / totalSpeed : 0;
    setTimeRemaining(timeRem);
  }, [selectedFiles]);

  // Allowed file types
  const ALLOWED_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/png'
  ];

  const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'];
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const MAX_TOTAL_SIZE = 50 * 1024 * 1024; // 50MB

  // Format file size for display
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  // Calculate total size of selected files
  const getTotalSize = (): number => {
    return selectedFiles.reduce((total, fileWithProgress) => total + fileWithProgress.file.size, 0);
  };

  // Validate file type
  const isValidFileType = (file: File): boolean => {
    return ALLOWED_TYPES.includes(file.type) ||
           ALLOWED_EXTENSIONS.some(ext => file.name.toLowerCase().endsWith(ext));
  };

  // Validate individual file
  const validateFile = (file: File): string | null => {
    if (!isValidFileType(file)) {
      return `Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`;
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File size exceeds ${formatFileSize(MAX_FILE_SIZE)} limit`;
    }
    return null;
  };

  // Handle file selection
  const handleFileSelect = async (files: FileList | null) => {
    console.log('[FILE SELECT DEBUG] handleFileSelect called with:', files?.length, 'files');
    if (!files || files.length === 0) {
      console.log('[FILE SELECT DEBUG] No files selected, returning');
      return;
    }

    const newFiles: FileWithProgress[] = [];
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check rate limiting first
    const { allowed: rateLimitAllowed, remaining } = checkRateLimit();
    if (!rateLimitAllowed) {
      errors.push(`❌ Rate limit exceeded. You can upload ${MAX_UPLOADS_PER_HOUR} files per hour. Try again later.`);
      alert(errors.join('\n'));
      return;
    }

    if (remaining < files.length) {
      warnings.push(`⚠️ Only ${remaining} uploads remaining in this hour (limit: ${MAX_UPLOADS_PER_HOUR}/hour)`);
    }

    // Check user permission for case ID
    const hasPermission = await verifyUserPermission(caseId);
    if (!hasPermission) {
      errors.push(`❌ You do not have permission to upload documents to case ${caseId}`);
      alert(errors.join('\n'));
      return;
    }

    // Pre-upload validation checks
    const currentFileNames = selectedFiles.map(f => f.file.name);
    const newFileNames = Array.from(files).map(f => f.name);

    // Check for duplicates
    const duplicates = newFileNames.filter(name => currentFileNames.includes(name));
    if (duplicates.length > 0) {
      warnings.push(`⚠️ Duplicate files detected: ${duplicates.join(', ')}`);
    }

    // Check if total would exceed 50 documents
    const totalAfterAdd = selectedFiles.length + files.length;
    if (totalAfterAdd > 50) {
      warnings.push(`⚠️ Total documents would exceed 50 (current: ${selectedFiles.length}, adding: ${files.length})`);
    }

    // Check for executable files
    const executableExtensions = ['.exe', '.bat', '.cmd', '.sh', '.ps1', '.msi', '.app'];
    const executableFiles = Array.from(files).filter(file =>
      executableExtensions.some(ext => file.name.toLowerCase().endsWith(ext))
    );
    if (executableFiles.length > 0) {
      errors.push(`❌ Executable files are not allowed: ${executableFiles.map(f => f.name).join(', ')}`);
    }

    // Validate each file and classify
    Array.from(files).forEach(file => {
      const error = validateFile(file);
      if (error) {
        errors.push(`${file.name}: ${error}`);
      } else {
        // Classify the document
        const classification = classifyDocument(file.name);

        // Create file entry with validating status
        const fileId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

        newFiles.push({
          id: fileId,
          file,
          progress: 0,
          status: 'validating', // Set to validating initially
          classification,
          selectedType: classification.suggestedType,
          retryCount: 0,
          uploadSpeed: 0
        });
      }
    });

    // Check total size
    const currentSize = getTotalSize();
    const newSize = newFiles.reduce((total, f) => total + f.file.size, 0);
    if (currentSize + newSize > MAX_TOTAL_SIZE) {
      errors.push(`Total size would exceed ${formatFileSize(MAX_TOTAL_SIZE)} limit`);
      return;
    }

    if (errors.length > 0) {
      alert(errors.join('\n'));
      return;
    }

    if (warnings.length > 0) {
      setValidationWarnings(warnings);
    } else {
      setValidationWarnings([]);
    }

    if (newFiles.length > 0) {
      console.log('[FILE SELECT DEBUG] Adding', newFiles.length, 'files to state');
      // Add files to state immediately with validating status
      setSelectedFiles(prev => {
        console.log('[FILE SELECT DEBUG] Previous files:', prev.length, 'New files:', newFiles.length, 'Total will be:', prev.length + newFiles.length);
        return [...prev, ...newFiles];
      });

      // Run security validation asynchronously for each file
      for (const fileEntry of newFiles) {
        try {
          // Run comprehensive security validation
          const securityValidation = await validateFileSecurity(fileEntry.file, fileEntry.id);

          // Check if validation passed
          if (securityValidation.validationErrors.length > 0) {
            // Security validation failed - mark as failed
            setSelectedFiles(prev =>
              prev.map(f =>
                f.id === fileEntry.id
                  ? {
                      ...f,
                      status: 'failed' as const,
                      errorMessage: `Security validation failed: ${securityValidation.validationErrors.join(', ')}`,
                      security: securityValidation
                    }
                  : f
              )
            );
          } else {
            // Security validation passed - mark as queued
            setSelectedFiles(prev =>
              prev.map(f =>
                f.id === fileEntry.id
                  ? {
                      ...f,
                      status: 'queued' as const,
                      security: securityValidation
                    }
                  : f
              )
            );
          }

          // Get IP address for audit log
          const ipAddress = await getUserIPAddress();

          // Add audit log entry
          addAuditLog({
            fileId: fileEntry.id,
            filename: fileEntry.file.name,
            timestamp: new Date(),
            action: 'validation',
            userId: 'current-user-id', // In production, get from auth context
            ipAddress,
            details: `File validated. Security score: ${securityValidation.securityScore}/100`,
            securityFlags: [...securityValidation.validationErrors, ...securityValidation.validationWarnings]
          });
        } catch (err) {
          // Validation error - mark as failed
          setSelectedFiles(prev =>
            prev.map(f =>
              f.id === fileEntry.id
                ? {
                    ...f,
                    status: 'failed' as const,
                    errorMessage: 'Security validation error occurred'
                  }
                : f
            )
          );
        }
      }

      // Increment upload count for rate limiting
      setUploadCount(prev => prev + newFiles.length);
    }

    // Clear input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Remove file from selection
  const removeFile = (fileId: string) => {
    setSelectedFiles(prev => prev.filter(f => f.id !== fileId));
    // Clear warnings if we removed files
    if (selectedFiles.length <= 1) {
      setValidationWarnings([]);
    }
  };

  // Update individual file type
  const updateFileType = (fileId: string, newType: string) => {
    setSelectedFiles(prev =>
      prev.map(f => f.id === fileId ? { ...f, selectedType: newType } : f)
    );
  };

  // Bulk action: Set all document types
  const setAllDocumentTypes = (type: string) => {
    setSelectedFiles(prev =>
      prev.map(f => ({ ...f, selectedType: type }))
    );
  };

  // Bulk action: Add prefix to all filenames
  const addPrefixToAll = () => {
    const prefix = prompt('Enter prefix to add to all filenames:');
    if (!prefix) return;

    setSelectedFiles(prev =>
      prev.map(f => {
        const newFile = new File([f.file], `${prefix}_${f.file.name}`, { type: f.file.type });
        return { ...f, file: newFile };
      })
    );
  };

  // Handle drag over
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  // Handle drag leave
  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  // Handle drop
  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  // Handle description change with validation
  const handleDescriptionChange = (value: string) => {
    setDescription(value);
    if (value.length > 500) {
      setDescriptionError(`Description exceeds maximum length (${value.length}/500 characters)`);
    } else {
      setDescriptionError('');
    }
  };

  // Get auth token from localStorage
  const getAuthToken = (): string | null => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('authToken') || localStorage.getItem('token');
    }
    return null;
  };

  // Format upload speed
  const formatSpeed = (bytesPerSec: number): string => {
    if (bytesPerSec === 0) return '0 B/s';
    const k = 1024;
    const sizes = ['B/s', 'KB/s', 'MB/s'];
    const i = Math.floor(Math.log(bytesPerSec) / Math.log(k));
    return Math.round((bytesPerSec / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  // Format time remaining
  const formatTimeRemaining = (seconds: number): string => {
    if (seconds === 0 || !isFinite(seconds)) return '--';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${Math.round(seconds / 3600)}h`;
  };

  // Add log entry
  const addLog = (log: UploadLog) => {
    setUploadLogs(prev => [...prev, log]);
  };

  // Calculate exponential backoff delay
  const getBackoffDelay = (retryCount: number): number => {
    return Math.min(1000 * Math.pow(2, retryCount), 10000); // Max 10 seconds
  };

  // ====================
  // SECURITY VALIDATION FUNCTIONS
  // ====================

  // Sanitize filename - remove special characters, limit length
  const sanitizeFilename = (filename: string): string => {
    // Remove path components
    const nameOnly = filename.replace(/^.*[\\\/]/, '');

    // Remove or replace dangerous characters
    let sanitized = nameOnly
      .replace(/[<>:"|?*\x00-\x1f]/g, '') // Remove illegal chars
      .replace(/\.\./g, '.') // Prevent directory traversal
      .replace(/^\.+/, '') // Remove leading dots
      .trim();

    // Limit length while preserving extension
    if (sanitized.length > MAX_FILENAME_LENGTH) {
      const ext = sanitized.substring(sanitized.lastIndexOf('.'));
      const nameWithoutExt = sanitized.substring(0, sanitized.lastIndexOf('.'));
      sanitized = nameWithoutExt.substring(0, MAX_FILENAME_LENGTH - ext.length) + ext;
    }

    return sanitized || 'document.pdf'; // Default if sanitization results in empty string
  };

  // Validate actual MIME type from file content (not just extension)
  const validateMimeType = async (file: File): Promise<{ valid: boolean; detectedType: string }> => {
    return new Promise((resolve) => {
      const reader = new FileReader();

      reader.onloadend = () => {
        const arr = new Uint8Array(reader.result as ArrayBuffer);
        let header = '';
        for (let i = 0; i < Math.min(arr.length, 8); i++) {
          header += arr[i].toString(16).padStart(2, '0');
        }

        // Check magic numbers/file signatures
        let detectedType = 'unknown';

        if (header.startsWith('25504446')) {
          detectedType = 'application/pdf'; // PDF: %PDF
        } else if (header.startsWith('ffd8ff')) {
          detectedType = 'image/jpeg'; // JPEG
        } else if (header.startsWith('89504e47')) {
          detectedType = 'image/png'; // PNG
        } else if (header.startsWith('47494638')) {
          detectedType = 'image/gif'; // GIF
        } else if (header.startsWith('49492a00') || header.startsWith('4d4d002a')) {
          detectedType = 'image/tiff'; // TIFF
        } else if (header.startsWith('504b0304') || header.startsWith('504b0506') || header.startsWith('504b0708')) {
          // ZIP-based formats (DOCX, etc.)
          if (file.name.toLowerCase().endsWith('.docx')) {
            detectedType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
          }
        } else if (header.startsWith('d0cf11e0')) {
          detectedType = 'application/msword'; // Old DOC format
        }

        const valid = ALLOWED_MIME_TYPES.includes(detectedType) ||
                     ALLOWED_MIME_TYPES.includes(file.type);

        resolve({ valid, detectedType });
      };

      reader.onerror = () => {
        resolve({ valid: false, detectedType: 'error' });
      };

      // Read first 8 bytes for magic number
      reader.readAsArrayBuffer(file.slice(0, 8));
    });
  };

  // Check if PDF is password protected
  const checkPasswordProtectedPDF = async (file: File): Promise<boolean> => {
    if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
      return false; // Not a PDF
    }

    return new Promise((resolve) => {
      const reader = new FileReader();

      reader.onload = () => {
        const text = reader.result as string;
        // Check for encryption markers in PDF
        const isEncrypted = text.includes('/Encrypt') &&
                          (text.includes('/Filter') || text.includes('/O') || text.includes('/U'));
        resolve(isEncrypted);
      };

      reader.onerror = () => resolve(false);

      // Read first 10KB to check for encryption markers
      reader.readAsText(file.slice(0, 10240));
    });
  };

  // Validate PDF structure
  const validatePDFStructure = async (file: File): Promise<boolean> => {
    if (!file.type.includes('pdf') && !file.name.toLowerCase().endsWith('.pdf')) {
      return true; // Not a PDF, skip validation
    }

    return new Promise((resolve) => {
      const reader = new FileReader();

      reader.onload = () => {
        const text = reader.result as string;

        // Check for PDF header
        const hasHeader = text.startsWith('%PDF-');

        // Check for EOF marker
        const hasEOF = text.includes('%%EOF');

        // Basic structure validation
        const hasObjects = text.includes('obj') && text.includes('endobj');

        resolve(hasHeader && hasEOF && hasObjects);
      };

      reader.onerror = () => resolve(false);

      // Read first and last chunks to validate structure
      const chunkSize = 5000;
      const blob = new Blob([
        file.slice(0, chunkSize),
        file.slice(Math.max(0, file.size - chunkSize))
      ]);
      reader.readAsText(blob);
    });
  };

  // Validate image file integrity
  const validateImageFile = async (file: File): Promise<boolean> => {
    if (!file.type.startsWith('image/')) {
      return true; // Not an image, skip validation
    }

    return new Promise((resolve) => {
      const img = new Image();
      const url = URL.createObjectURL(file);

      img.onload = () => {
        URL.revokeObjectURL(url);
        // Image loaded successfully
        resolve(img.width > 0 && img.height > 0);
      };

      img.onerror = () => {
        URL.revokeObjectURL(url);
        // Image failed to load - corrupted
        resolve(false);
      };

      img.src = url;
    });
  };

  // Scan for potentially malicious content patterns
  const scanMaliciousContent = async (file: File): Promise<{ detected: boolean; patterns: string[] }> => {
    return new Promise((resolve) => {
      const reader = new FileReader();

      reader.onload = () => {
        const text = (reader.result as string).toLowerCase();
        const detectedPatterns: string[] = [];

        // Check for suspicious patterns
        const maliciousPatterns = [
          { pattern: '<script', name: 'JavaScript code' },
          { pattern: 'javascript:', name: 'JavaScript protocol' },
          { pattern: 'vbscript:', name: 'VBScript protocol' },
          { pattern: 'on error resume', name: 'VB error handling' },
          { pattern: 'eval(', name: 'Code evaluation' },
          { pattern: 'powershell', name: 'PowerShell' },
          { pattern: 'cmd.exe', name: 'Command prompt' },
          { pattern: '/bin/bash', name: 'Bash shell' },
          { pattern: '/bin/sh', name: 'Shell script' }
        ];

        for (const { pattern, name } of maliciousPatterns) {
          if (text.includes(pattern)) {
            detectedPatterns.push(name);
          }
        }

        resolve({
          detected: detectedPatterns.length > 0,
          patterns: detectedPatterns
        });
      };

      reader.onerror = () => {
        resolve({ detected: false, patterns: [] });
      };

      // Read first 50KB to scan for patterns
      reader.readAsText(file.slice(0, 51200));
    });
  };

  // Generate SHA-256 hash of file
  const generateFileHash = async (file: File): Promise<string> => {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  };

  // Add audit log entry
  const addAuditLog = (log: AuditLog) => {
    setAuditLogs(prev => [...prev, log]);
  };

  // Comprehensive security validation for a file
  const validateFileSecurity = async (file: File, fileId: string): Promise<SecurityValidation> => {
    const errors: string[] = [];
    const warnings: string[] = [];
    let securityScore = 100;

    // 1. Validate MIME type
    const { valid: mimeValid, detectedType } = await validateMimeType(file);
    if (!mimeValid) {
      errors.push('Invalid or disallowed file type');
      securityScore -= 30;
    }

    // 2. Check for password protection
    const isPasswordProtected = await checkPasswordProtectedPDF(file);
    if (isPasswordProtected) {
      warnings.push('PDF appears to be password protected');
      securityScore -= 10;
    }

    // 3. Validate PDF structure
    const pdfValid = await validatePDFStructure(file);
    if (!pdfValid && file.type.includes('pdf')) {
      errors.push('Invalid PDF structure detected');
      securityScore -= 25;
    }

    // 4. Validate image integrity
    const imageValid = await validateImageFile(file);
    if (!imageValid && file.type.startsWith('image/')) {
      errors.push('Corrupted or invalid image file');
      securityScore -= 25;
    }

    // 5. Scan for malicious content
    const { detected: maliciousDetected, patterns } = await scanMaliciousContent(file);
    if (maliciousDetected) {
      errors.push(`Potentially malicious content detected: ${patterns.join(', ')}`);
      securityScore -= 50;
    }

    // 6. Generate hash
    let hashedSHA256: string | undefined;
    try {
      hashedSHA256 = await generateFileHash(file);
    } catch (err) {
      warnings.push('Could not generate file hash');
      securityScore -= 5;
    }

    // 7. Sanitize filename
    const sanitizedFilename = sanitizeFilename(file.name);
    if (sanitizedFilename !== file.name) {
      warnings.push('Filename was sanitized for security');
    }

    // Add audit log
    addAuditLog({
      fileId,
      filename: file.name,
      timestamp: new Date(),
      action: 'security_check',
      details: `Security validation completed. Score: ${securityScore}/100`,
      securityFlags: [...errors, ...warnings]
    });

    return {
      mimeTypeValid: mimeValid,
      mimeType: detectedType,
      structureValid: pdfValid,
      isPasswordProtected,
      hashedSHA256,
      isEncrypted: false, // Will be set after encryption
      sanitizedFilename,
      maliciousContentDetected: maliciousDetected,
      validationErrors: errors,
      validationWarnings: warnings,
      securityScore: Math.max(0, securityScore)
    };
  };

  // ====================
  // ENCRYPTION & SECURITY FEATURES
  // ====================

  // Generate encryption key using Web Crypto API
  const generateEncryptionKey = async (): Promise<CryptoKey> => {
    return await crypto.subtle.generateKey(
      {
        name: 'AES-GCM',
        length: 256
      },
      true, // extractable
      ['encrypt', 'decrypt']
    );
  };

  // Encrypt file using AES-GCM
  const encryptFile = async (file: File): Promise<{ encryptedBlob: Blob; iv: Uint8Array; key: CryptoKey }> => {
    // Generate encryption key
    const key = await generateEncryptionKey();

    // Generate initialization vector
    const iv = crypto.getRandomValues(new Uint8Array(12));

    // Read file as array buffer
    const buffer = await file.arrayBuffer();

    // Encrypt the data
    const encryptedData = await crypto.subtle.encrypt(
      {
        name: 'AES-GCM',
        iv: iv
      },
      key,
      buffer
    );

    // Create blob from encrypted data
    const encryptedBlob = new Blob([encryptedData], { type: 'application/octet-stream' });

    return { encryptedBlob, iv, key };
  };

  // Check rate limiting
  const checkRateLimit = (): { allowed: boolean; remaining: number } => {
    const now = Date.now();
    const oneHour = 60 * 60 * 1000;

    // Reset counter if hour has passed
    if (now - lastUploadReset > oneHour) {
      setUploadCount(0);
      setLastUploadReset(now);
      return { allowed: true, remaining: MAX_UPLOADS_PER_HOUR };
    }

    const remaining = MAX_UPLOADS_PER_HOUR - uploadCount;

    return {
      allowed: uploadCount < MAX_UPLOADS_PER_HOUR,
      remaining: Math.max(0, remaining)
    };
  };

  // Generate CSRF token
  const generateCSRFToken = (): string => {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  };

  // Get user IP address (from headers or client info)
  const getUserIPAddress = async (): Promise<string> => {
    try {
      // In production, this would come from your auth system or API
      // For now, return placeholder
      return 'client-ip-address';
    } catch {
      return 'unknown';
    }
  };

  // Check if document type is restricted
  const isRestrictedDocumentType = (documentType: string): boolean => {
    return RESTRICTED_DOCUMENT_TYPES.includes(documentType.toLowerCase());
  };

  // Verify user has permission for case ID
  const verifyUserPermission = async (caseId: string): Promise<boolean> => {
    // In production, this would check with your backend API
    // For now, return true as placeholder
    try {
      // Example: const response = await fetch(`/api/cases/${caseId}/check-permission`);
      // return response.ok;
      return true;
    } catch {
      return false;
    }
  };

  // Upload single file with retry logic
  const uploadSingleFile = async (fileWithProgress: FileWithProgress): Promise<UploadedDocument | null> => {
    return new Promise(async (resolve, reject) => {
      const { id, file, selectedType, classification, retryCount } = fileWithProgress;

      // Check if paused
      if (isPaused) {
        setSelectedFiles(prev =>
          prev.map(f => f.id === id ? { ...f, status: 'paused' as const } : f)
        );
        resolve(null);
        return;
      }

      // Log start
      addLog({
        fileId: id,
        filename: file.name,
        timestamp: new Date(),
        status: 'started',
        size: file.size
      });

      const formData = new FormData();
      formData.append('files', file);
      formData.append('session_id', caseId);
      // Additional metadata for bankruptcy documents (backend will ignore if not supported)
      formData.append('document_type', selectedType);
      formData.append('case_id', caseId);
      formData.append('filing_date', filingDate);
      if (description.trim()) {
        formData.append('description', description.trim());
      }
      if (classification.caseNumber) {
        formData.append('case_number', classification.caseNumber);
      }
      if (classification.exhibitNumber) {
        formData.append('exhibit_number', classification.exhibitNumber);
      }

      const xhr = new XMLHttpRequest();
      const startTime = Date.now();
      let lastLoaded = 0;
      let lastTime = startTime;

      // Store XHR for pause/cancel
      setSelectedFiles(prev =>
        prev.map(f => f.id === id ? { ...f, xhr, startTime } : f)
      );

      // Track progress and speed
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          const now = Date.now();
          const timeDiff = (now - lastTime) / 1000; // seconds
          const bytesDiff = e.loaded - lastLoaded;
          const speed = timeDiff > 0 ? bytesDiff / timeDiff : 0;

          setSelectedFiles(prev =>
            prev.map(f => f.id === id ? {
              ...f,
              progress,
              status: 'uploading' as const,
              uploadSpeed: speed
            } : f)
          );

          lastLoaded = e.loaded;
          lastTime = now;
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        const endTime = Date.now();
        const duration = endTime - startTime;

        if (xhr.status >= 200 && xhr.status < 300) {
          // Success
          setSelectedFiles(prev =>
            prev.map(f => f.id === id ? {
              ...f,
              progress: 100,
              status: 'completed' as const,
              endTime,
              uploadSpeed: 0
            } : f)
          );

          addLog({
            fileId: id,
            filename: file.name,
            timestamp: new Date(),
            status: 'completed',
            duration,
            size: file.size
          });

          activeUploadsRef.current.delete(id);

          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response.documents?.[0] || null);
          } catch (e) {
            resolve(null);
          }
        } else {
          // Error - attempt retry
          const errorMessage = handleUploadError(xhr.status, xhr.responseText);

          if (retryCount < MAX_RETRIES) {
            // Retry with backoff
            const delay = getBackoffDelay(retryCount);

            setSelectedFiles(prev =>
              prev.map(f => f.id === id ? {
                ...f,
                status: 'queued' as const,
                retryCount: retryCount + 1,
                errorMessage: `Retry ${retryCount + 1}/${MAX_RETRIES} in ${delay / 1000}s...`,
                uploadSpeed: 0
              } : f)
            );

            setTimeout(async () => {
              try {
                const result = await uploadSingleFile({
                  ...fileWithProgress,
                  retryCount: retryCount + 1
                });
                resolve(result);
              } catch (err) {
                reject(err);
              }
            }, delay);
          } else {
            // Max retries reached
            setSelectedFiles(prev =>
              prev.map(f => f.id === id ? {
                ...f,
                status: 'failed' as const,
                errorMessage,
                endTime,
                uploadSpeed: 0
              } : f)
            );

            addLog({
              fileId: id,
              filename: file.name,
              timestamp: new Date(),
              status: 'failed',
              error: errorMessage,
              duration,
              size: file.size
            });

            activeUploadsRef.current.delete(id);
            reject(new Error(errorMessage));
          }
        }
      });

      // Handle network errors
      xhr.addEventListener('error', () => {
        const errorMessage = 'Network error occurred';

        if (retryCount < MAX_RETRIES) {
          const delay = getBackoffDelay(retryCount);

          setSelectedFiles(prev =>
            prev.map(f => f.id === id ? {
              ...f,
              status: 'queued' as const,
              errorMessage: `Network error. Retrying in ${delay / 1000}s...`,
              uploadSpeed: 0
            } : f)
          );

          setTimeout(async () => {
            try {
              const result = await uploadSingleFile({
                ...fileWithProgress,
                retryCount: retryCount + 1
              });
              resolve(result);
            } catch (err) {
              reject(err);
            }
          }, delay);
        } else {
          setSelectedFiles(prev =>
            prev.map(f => f.id === id ? {
              ...f,
              status: 'failed' as const,
              errorMessage,
              uploadSpeed: 0
            } : f)
          );

          addLog({
            fileId: id,
            filename: file.name,
            timestamp: new Date(),
            status: 'failed',
            error: errorMessage,
            size: file.size
          });

          activeUploadsRef.current.delete(id);
          reject(new Error(errorMessage));
        }
      });

      // Handle timeout
      xhr.addEventListener('timeout', () => {
        const errorMessage = 'Upload timeout (30s)';

        if (retryCount < MAX_RETRIES) {
          const delay = getBackoffDelay(retryCount);

          setSelectedFiles(prev =>
            prev.map(f => f.id === id ? {
              ...f,
              status: 'queued' as const,
              errorMessage: `Timeout. Retrying in ${delay / 1000}s...`,
              uploadSpeed: 0
            } : f)
          );

          setTimeout(async () => {
            try {
              const result = await uploadSingleFile({
                ...fileWithProgress,
                retryCount: retryCount + 1
              });
              resolve(result);
            } catch (err) {
              reject(err);
            }
          }, delay);
        } else {
          setSelectedFiles(prev =>
            prev.map(f => f.id === id ? {
              ...f,
              status: 'failed' as const,
              errorMessage,
              uploadSpeed: 0
            } : f)
          );

          addLog({
            fileId: id,
            filename: file.name,
            timestamp: new Date(),
            status: 'failed',
            error: errorMessage,
            size: file.size
          });

          activeUploadsRef.current.delete(id);
          reject(new Error(errorMessage));
        }
      });

      // Get auth token (optional for development)
      const authToken = getAuthToken();
      if (!authToken) {
        console.warn('[UPLOAD DEBUG] No auth token found - proceeding without authentication');
      }

      // Configure and send request
      xhr.open('POST', actualEndpoint);
      // Only add Authorization header if token exists
      if (authToken) {
        xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
      }
      xhr.timeout = UPLOAD_TIMEOUT;
      xhr.send(formData);

      // Add to active uploads
      activeUploadsRef.current.add(id);
    });
  };

  // Handle specific error codes
  const handleUploadError = (status: number, responseText: string): string => {
    switch (status) {
      case 401:
        // Unauthorized - redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('authToken');
          localStorage.removeItem('token');
          window.location.href = '/auth/login?redirect=' + encodeURIComponent(window.location.pathname);
        }
        return 'Authentication failed. Please log in again.';

      case 413:
        // File too large
        return 'File size exceeds server limit. Please upload smaller files.';

      case 422:
        // Validation error
        try {
          const errorData = JSON.parse(responseText);
          return errorData.message || 'Validation failed. Please check your input.';
        } catch (e) {
          return 'Validation failed. Please check your input.';
        }

      case 500:
        return 'Server error occurred. Please try again later.';

      default:
        return `Upload failed with status ${status}`;
    }
  };

  // Process upload queue with batching (Phase 3)
  const processUploadQueue = useCallback(async () => {
    if (isPaused) return;

    // Get files sorted by size (smaller first)
    const queue = selectedFiles
      .filter(f => f.status === 'queued')
      .sort((a, b) => a.file.size - b.file.size);

    if (queue.length === 0) {
      // Check if all uploads complete
      const allComplete = selectedFiles.every(f =>
        f.status === 'completed' || f.status === 'failed' || f.status === 'cancelled'
      );

      if (allComplete && isUploading) {
        setIsUploading(false);
        activeUploadsRef.current.clear();

        // Call onUploadComplete if any successful
        const successfulFiles = selectedFiles.filter(f => f.status === 'completed');
        if (successfulFiles.length > 0 && onUploadComplete) {
          onUploadComplete({
            success: true,
            documents: [], // Backend would populate this
            message: `Successfully uploaded ${successfulFiles.length} of ${selectedFiles.length} files`
          });
        }

        // Check for failures
        const failedFiles = selectedFiles.filter(f => f.status === 'failed');
        if (failedFiles.length > 0 && onUploadError) {
          onUploadError(new Error(
            `${failedFiles.length} file(s) failed to upload: ${
              failedFiles.map(f => f.file.name).join(', ')
            }`
          ));
        }
      }
      return;
    }

    // Process batch (max 3 files at a time)
    const batch = queue.slice(0, Math.min(BATCH_SIZE, queue.length));

    // Upload batch in parallel
    await Promise.allSettled(
      batch.map(file => uploadSingleFile(file))
    );

    // Continue with next batch
    if (!isPaused) {
      setTimeout(() => processUploadQueue(), 100); // Small delay between batches
    }
  }, [selectedFiles, isPaused, isUploading, caseId, documentType, filingDate, description, onUploadComplete, onUploadError]);

  // Pause all uploads (Phase 4)
  const pauseUploads = () => {
    setIsPaused(true);
    selectedFiles.forEach(f => {
      if (f.status === 'uploading' && f.xhr) {
        f.xhr.abort();
      }
    });
    setSelectedFiles(prev =>
      prev.map(f => f.status === 'uploading' ? { ...f, status: 'paused' as const, uploadSpeed: 0 } : f)
    );
  };

  // Resume uploads (Phase 4)
  const resumeUploads = () => {
    setIsPaused(false);
    setSelectedFiles(prev =>
      prev.map(f => f.status === 'paused' ? { ...f, status: 'queued' as const } : f)
    );
    // Trigger queue processing
    setTimeout(() => processUploadQueue(), 100);
  };

  // Cancel individual file (Phase 4)
  const cancelFile = (fileId: string) => {
    const file = selectedFiles.find(f => f.id === fileId);
    if (file?.xhr) {
      file.xhr.abort();
    }

    setSelectedFiles(prev =>
      prev.map(f => f.id === fileId ? { ...f, status: 'cancelled' as const, uploadSpeed: 0 } : f)
    );

    addLog({
      fileId,
      filename: file?.file.name || 'Unknown',
      timestamp: new Date(),
      status: 'cancelled',
      size: file?.file.size || 0
    });

    activeUploadsRef.current.delete(fileId);
  };

  // Retry all failed uploads (Phase 4)
  const retryFailedUploads = () => {
    setSelectedFiles(prev =>
      prev.map(f => f.status === 'failed' ? {
        ...f,
        status: 'queued' as const,
        retryCount: 0,
        errorMessage: undefined,
        uploadSpeed: 0
      } : f)
    );

    if (!isUploading) {
      setIsUploading(true);
      processUploadQueue();
    } else {
      processUploadQueue();
    }
  };

  // Retry single failed file (Phase 4)
  const retrySingleFile = (fileId: string) => {
    setSelectedFiles(prev =>
      prev.map(f => f.id === fileId && f.status === 'failed' ? {
        ...f,
        status: 'queued' as const,
        retryCount: 0,
        errorMessage: undefined,
        uploadSpeed: 0
      } : f)
    );

    if (!isUploading) {
      setIsUploading(true);
      processUploadQueue();
    } else {
      processUploadQueue();
    }
  };

  // Validate form before upload
  const validateForm = (): boolean => {
    if (selectedFiles.length === 0) {
      return false;
    }

    if (!documentType) {
      alert('Please select a document type');
      return false;
    }

    if (!filingDate) {
      alert('Please select a filing date');
      return false;
    }

    if (description.length > 500) {
      alert('Description exceeds maximum length of 500 characters');
      return false;
    }

    // Authentication is optional for development - backend endpoint doesn't require it
    const authToken = getAuthToken();
    if (!authToken) {
      console.warn('[AUTH WARNING] No authentication token found. Proceeding without authentication (dev mode).');
    }

    return true;
  };

  // Handle upload all - batch upload all files at once
  const handleUploadAll = async () => {
    console.log('[UPLOAD DEBUG] handleUploadAll called');
    console.log('[UPLOAD DEBUG] Current selectedFiles state:', selectedFiles.length, 'files');
    console.log('[UPLOAD DEBUG] File statuses:', selectedFiles.map(f => `${f.file.name}: ${f.status}`));

    if (!validateForm() || isUploading) {
      console.log('[UPLOAD DEBUG] Validation failed or already uploading');
      return;
    }

    setIsUploading(true);
    setIsPaused(false);

    // Get files that are ready to upload (status: queued)
    const filesToUpload = selectedFiles.filter(f => f.status === 'queued');
    console.log('[UPLOAD DEBUG] Files with status=queued:', filesToUpload.length);

    if (filesToUpload.length === 0) {
      alert('No files ready to upload');
      setIsUploading(false);
      return;
    }

    // Create FormData with ALL files
    const formData = new FormData();

    // Add all files
    console.log(`[UPLOAD DEBUG] Preparing to upload ${filesToUpload.length} files`);
    filesToUpload.forEach((fileEntry, index) => {
      console.log(`[UPLOAD DEBUG] Adding file ${index + 1}: ${fileEntry.file.name} (${fileEntry.file.size} bytes)`);
      formData.append('files', fileEntry.file);
    });

    // Add session_id
    formData.append('session_id', caseId);
    console.log(`[UPLOAD DEBUG] Sending batch request with ${filesToUpload.length} files to ${actualEndpoint}`);

    // Mark all files as uploading
    setSelectedFiles(prev =>
      prev.map(f => filesToUpload.find(ftf => ftf.id === f.id)
        ? { ...f, status: 'uploading' as const, startTime: Date.now() }
        : f
      )
    );

    try {
      const authToken = getAuthToken();
      if (!authToken) {
        console.warn('[UPLOAD DEBUG] No auth token found - proceeding without authentication');
      }

      const xhr = new XMLHttpRequest();

      // Track progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100);
          setOverallProgress(progress);
        }
      });

      // Handle completion
      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          // Success
          const response = JSON.parse(xhr.responseText);

          setSelectedFiles(prev =>
            prev.map(f => filesToUpload.find(ftf => ftf.id === f.id)
              ? { ...f, status: 'completed' as const, progress: 100, endTime: Date.now() }
              : f
            )
          );

          setIsUploading(false);

          if (onUploadComplete) {
            onUploadComplete({
              success: true,
              documents: response.documents || [],
              message: `Successfully uploaded ${filesToUpload.length} files`
            });
          }
        } else {
          // Error
          const errorMsg = handleUploadError(xhr.status, xhr.responseText);

          setSelectedFiles(prev =>
            prev.map(f => filesToUpload.find(ftf => ftf.id === f.id)
              ? { ...f, status: 'failed' as const, errorMessage: errorMsg, endTime: Date.now() }
              : f
            )
          );

          setIsUploading(false);

          if (onUploadError) {
            onUploadError(new Error(errorMsg));
          }
        }
      });

      // Handle errors
      xhr.addEventListener('error', () => {
        const errorMsg = 'Network error occurred';

        setSelectedFiles(prev =>
          prev.map(f => filesToUpload.find(ftf => ftf.id === f.id)
            ? { ...f, status: 'failed' as const, errorMessage: errorMsg }
            : f
          )
        );

        setIsUploading(false);

        if (onUploadError) {
          onUploadError(new Error(errorMsg));
        }
      });

      // Send request
      xhr.open('POST', actualEndpoint);
      // Only add Authorization header if token exists
      if (authToken) {
        xhr.setRequestHeader('Authorization', `Bearer ${authToken}`);
      }
      xhr.send(formData);

    } catch (error: any) {
      setSelectedFiles(prev =>
        prev.map(f => filesToUpload.find(ftf => ftf.id === f.id)
          ? { ...f, status: 'failed' as const, errorMessage: error.message }
          : f
        )
      );

      setIsUploading(false);

      if (onUploadError) {
        onUploadError(error);
      }
    }
  };

  // Export logs to CSV (Phase 5)
  const exportLogsToCSV = () => {
    if (uploadLogs.length === 0) {
      alert('No upload logs to export');
      return;
    }

    const headers = ['Filename', 'Status', 'Timestamp', 'Duration (s)', 'Size (bytes)', 'Error'];
    const rows = uploadLogs.map(log => [
      log.filename,
      log.status,
      log.timestamp.toISOString(),
      log.duration ? (log.duration / 1000).toFixed(2) : '',
      log.size.toString(),
      log.error || ''
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `upload-report-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Get status icon (updated for all states)
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'uploading':
        return <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'validating':
        return <ShieldCheck className="h-5 w-5 text-purple-600 animate-pulse" />;
      case 'queued':
        return <Clock className="h-5 w-5 text-gray-400" />;
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-gray-600" />;
      case 'paused':
        return <Pause className="h-5 w-5 text-orange-600" />;
      default:
        return <FileIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  return (
    <div className={`bankruptcy-multi-upload ${className}`}>
      {/* Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
          isDragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ALLOWED_EXTENSIONS.join(',')}
          onChange={(e) => handleFileSelect(e.target.files)}
          className="hidden"
        />

        <Upload className="h-12 w-12 text-blue-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Upload Bankruptcy Documents
        </h3>
        <p className="text-gray-600 mb-2">
          Drag and drop files here, or click to select
        </p>
        <p className="text-sm text-gray-500">
          Supported: PDF, DOC, DOCX, JPG, PNG (max {formatFileSize(MAX_FILE_SIZE)} per file)
        </p>
      </div>

      {/* Validation Warnings */}
      {validationWarnings.length > 0 && (
        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h5 className="text-sm font-semibold text-yellow-900 mb-2">
                Validation Warnings
              </h5>
              <ul className="text-sm text-yellow-800 space-y-1">
                {validationWarnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
              <button
                onClick={() => setValidationWarnings([])}
                className="mt-2 text-xs text-yellow-700 hover:text-yellow-900 underline"
              >
                Dismiss warnings
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Form Fields */}
      {selectedFiles.length > 0 && (
        <div className="mt-6 space-y-4">
          {/* Document Type Selector */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Document Type <span className="text-red-600">*</span>
            </label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              disabled={isUploading}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {documentTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          {/* Filing Date Picker */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Filing Date <span className="text-red-600">*</span>
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="date"
                value={filingDate}
                onChange={(e) => setFilingDate(e.target.value)}
                disabled={isUploading}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
          </div>

          {/* Description Field */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              Description <span className="text-gray-500 text-xs">(Optional)</span>
            </label>
            <div className="relative">
              <FileText className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <textarea
                value={description}
                onChange={(e) => handleDescriptionChange(e.target.value)}
                disabled={isUploading}
                maxLength={500}
                rows={3}
                placeholder="Add notes or description for these documents..."
                className={`w-full pl-10 pr-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed resize-none ${
                  descriptionError ? 'border-red-500' : 'border-gray-300'
                }`}
              />
            </div>
            <div className="flex items-center justify-between mt-1">
              {descriptionError ? (
                <p className="text-xs text-red-600">{descriptionError}</p>
              ) : (
                <p className="text-xs text-gray-500">
                  Add any relevant notes about these documents
                </p>
              )}
              <p className={`text-xs ${description.length > 450 ? 'text-red-600' : 'text-gray-500'}`}>
                {description.length}/500
              </p>
            </div>
          </div>

          {/* Case ID Display */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              <strong>Case ID:</strong> {caseId}
            </p>
          </div>
        </div>
      )}

      {/* File List */}
      {selectedFiles.length > 0 && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-lg font-semibold text-gray-900">
                Selected Files ({selectedFiles.length})
              </h4>
              <p className="text-sm text-gray-600">
                Total size: {formatFileSize(getTotalSize())} / {formatFileSize(MAX_TOTAL_SIZE)}
              </p>
            </div>

            <div className="flex gap-2">
              {/* Queue Control Buttons */}
              {isUploading && !isPaused && (
                <button
                  onClick={pauseUploads}
                  className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                >
                  <Pause className="h-4 w-4" />
                  Pause
                </button>
              )}

              {isUploading && isPaused && (
                <button
                  onClick={resumeUploads}
                  className="px-3 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <Play className="h-4 w-4" />
                  Resume
                </button>
              )}

              {selectedFiles.some(f => f.status === 'failed') && !isUploading && (
                <button
                  onClick={retryFailedUploads}
                  className="px-3 py-2 text-sm font-medium text-white bg-orange-600 rounded-lg hover:bg-orange-700 flex items-center gap-2"
                >
                  <RotateCcw className="h-4 w-4" />
                  Retry Failed
                </button>
              )}

              {uploadLogs.length > 0 && (
                <button
                  onClick={exportLogsToCSV}
                  className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
                >
                  <Download className="h-4 w-4" />
                  Export Report
                </button>
              )}

              <button
                onClick={() => {
                  setSelectedFiles([]);
                  setUploadLogs([]);
                  setValidationWarnings([]);
                }}
                disabled={isUploading}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Clear All
              </button>

              {!isUploading && (
                <button
                  onClick={handleUploadAll}
                  disabled={selectedFiles.length === 0 || description.length > 500}
                  className="px-6 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Upload className="h-4 w-4" />
                  Upload {selectedFiles.length} File{selectedFiles.length !== 1 ? 's' : ''}
                </button>
              )}
            </div>
          </div>

          {/* Overall Progress Bar */}
          {isUploading && (
            <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex justify-between text-sm mb-2">
                <span className="font-medium text-blue-900">
                  {selectedFiles.filter(f => f.status === 'completed').length} of{' '}
                  {selectedFiles.length} files completed
                </span>
                <div className="flex items-center gap-3 text-blue-700">
                  <span>{formatSpeed(uploadSpeed)}</span>
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatTimeRemaining(timeRemaining)} remaining
                  </span>
                </div>
              </div>

              <div className="w-full bg-blue-200 rounded-full h-3">
                <div
                  className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${overallProgress}%` }}
                />
              </div>

              <div className="flex justify-between text-xs text-blue-700 mt-1">
                <span>{Math.round(overallProgress)}% complete</span>
                <span>
                  Queued: {selectedFiles.filter(f => f.status === 'queued').length} •
                  Uploading: {selectedFiles.filter(f => f.status === 'uploading').length} •
                  Failed: {selectedFiles.filter(f => f.status === 'failed').length}
                </span>
              </div>
            </div>
          )}

          {/* Bulk Actions */}
          {selectedFiles.length > 1 && !isUploading && (
            <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Settings className="h-4 w-4 text-gray-600" />
                <h5 className="text-sm font-semibold text-gray-700">Bulk Actions</h5>
              </div>
              <div className="flex flex-wrap gap-2">
                <select
                  onChange={(e) => {
                    if (e.target.value) {
                      setAllDocumentTypes(e.target.value);
                      e.target.value = '';
                    }
                  }}
                  className="px-3 py-1.5 text-xs font-medium border border-gray-300 rounded bg-white hover:bg-gray-50"
                  defaultValue=""
                >
                  <option value="">Set All Types...</option>
                  {documentTypes.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={addPrefixToAll}
                  className="px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
                >
                  Add Prefix to All
                </button>
              </div>
            </div>
          )}

          {/* Progress Bar */}
          {isUploading && (
            <div className="mb-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{
                    width: `${
                      (selectedFiles.filter(f => f.status === 'completed').length /
                        selectedFiles.length) *
                      100
                    }%`
                  }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-2 text-center">
                {selectedFiles.filter(f => f.status === 'completed').length} of{' '}
                {selectedFiles.length} files uploaded
              </p>
            </div>
          )}

          {/* Files */}
          <div className="space-y-3">
            {selectedFiles.map((fileWithProgress) => (
              <div
                key={fileWithProgress.id}
                className={`rounded-lg border ${
                  fileWithProgress.status === 'failed'
                    ? 'border-red-200 bg-red-50'
                    : fileWithProgress.status === 'completed'
                    ? 'border-green-200 bg-green-50'
                    : 'border-gray-200 bg-white'
                }`}
              >
                {/* Main file info row */}
                <div className="flex items-center justify-between p-4">
                  <div className="flex items-center gap-3 flex-1">
                    {getStatusIcon(fileWithProgress.status)}

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {fileWithProgress.file.name}
                      </p>
                      <div className="flex items-center gap-4 mt-1">
                        <p className="text-xs text-gray-500">
                          {formatFileSize(fileWithProgress.file.size)}
                        </p>
                        <p className="text-xs text-gray-500 capitalize">
                          {fileWithProgress.file.type.split('/')[1] || 'Unknown'}
                        </p>
                        {fileWithProgress.status === 'uploading' && (
                          <>
                            <p className="text-xs text-blue-600 font-medium">
                              {fileWithProgress.progress}%
                            </p>
                            <p className="text-xs text-blue-600">
                              {formatSpeed(fileWithProgress.uploadSpeed)}
                            </p>
                          </>
                        )}
                        {fileWithProgress.retryCount > 0 && (
                          <p className="text-xs text-orange-600">
                            Retry {fileWithProgress.retryCount}/{MAX_RETRIES}
                          </p>
                        )}
                      </div>
                      {fileWithProgress.errorMessage && (
                        <p className="text-xs text-red-600 mt-1">
                          {fileWithProgress.errorMessage}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Progress bar for individual file */}
                  {fileWithProgress.status === 'uploading' && (
                    <div className="w-32 mx-4">
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${fileWithProgress.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="flex items-center gap-2">
                    {/* Cancel button for uploading files */}
                    {fileWithProgress.status === 'uploading' && (
                      <button
                        onClick={() => cancelFile(fileWithProgress.id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                        title="Cancel upload"
                      >
                        <XCircle className="h-4 w-4" />
                      </button>
                    )}

                    {/* Retry button for failed files */}
                    {fileWithProgress.status === 'failed' && (
                      <button
                        onClick={() => retrySingleFile(fileWithProgress.id)}
                        className="p-2 text-orange-600 hover:bg-orange-50 rounded"
                        title="Retry upload"
                      >
                        <RotateCcw className="h-4 w-4" />
                      </button>
                    )}

                    {/* Remove button for non-uploading files */}
                    {fileWithProgress.status !== 'uploading' && (
                      <button
                        onClick={() => removeFile(fileWithProgress.id)}
                        disabled={isUploading && fileWithProgress.status === 'queued'}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Remove file"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Classification and document type row */}
                {(fileWithProgress.status === 'queued' || fileWithProgress.status === 'paused') && (
                  <div className="px-4 pb-4 border-t border-gray-100 pt-3">
                    <div className="flex items-start gap-4">
                      {/* Document type selector */}
                      <div className="flex-1">
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Document Type
                        </label>
                        <select
                          value={fileWithProgress.selectedType}
                          onChange={(e) => updateFileType(fileWithProgress.id, e.target.value)}
                          disabled={isUploading}
                          className="w-full px-3 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
                        >
                          {documentTypes.map((type) => (
                            <option key={type.value} value={type.value}>
                              {type.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Classification info */}
                      <div className="flex-1">
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Auto-detected Info
                        </label>
                        <div className="flex flex-wrap gap-2">
                          {/* Confidence badge */}
                          {fileWithProgress.classification.confidence === 'high' && (
                            <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 rounded">
                              High Confidence
                            </span>
                          )}
                          {fileWithProgress.classification.confidence === 'medium' && (
                            <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
                              Medium Confidence
                            </span>
                          )}
                          {fileWithProgress.classification.confidence === 'low' && (
                            <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                              Low Confidence
                            </span>
                          )}

                          {/* Case number */}
                          {fileWithProgress.classification.caseNumber && (
                            <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                              Case: {fileWithProgress.classification.caseNumber}
                            </span>
                          )}

                          {/* Exhibit number */}
                          {fileWithProgress.classification.exhibitNumber && (
                            <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800 rounded">
                              Exhibit: {fileWithProgress.classification.exhibitNumber}
                            </span>
                          )}

                          {/* Security status */}
                          {fileWithProgress.security && (
                            <>
                              {/* Security score */}
                              <span
                                className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded ${
                                  fileWithProgress.security.securityScore >= 80
                                    ? 'bg-green-100 text-green-800'
                                    : fileWithProgress.security.securityScore >= 60
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-red-100 text-red-800'
                                }`}
                              >
                                <Shield className="h-3 w-3" />
                                Security: {fileWithProgress.security.securityScore}/100
                              </span>

                              {/* Password protected */}
                              {fileWithProgress.security.isPasswordProtected && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-orange-100 text-orange-800 rounded">
                                  <Lock className="h-3 w-3" />
                                  Password Protected
                                </span>
                              )}

                              {/* Malicious content detected */}
                              {fileWithProgress.security.maliciousContentDetected && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-red-100 text-red-800 rounded">
                                  <ShieldAlert className="h-3 w-3" />
                                  Security Risk
                                </span>
                              )}

                              {/* File hash */}
                              {fileWithProgress.security.hashedSHA256 && (
                                <span
                                  className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 rounded cursor-help"
                                  title={`SHA-256: ${fileWithProgress.security.hashedSHA256}`}
                                >
                                  <Key className="h-3 w-3" />
                                  Hashed
                                </span>
                              )}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Info Banner */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-blue-900 mb-1">
              Document Upload Guidelines
            </h5>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Maximum file size: {formatFileSize(MAX_FILE_SIZE)} per file</li>
              <li>• Maximum total size: {formatFileSize(MAX_TOTAL_SIZE)} per batch</li>
              <li>• Supported formats: PDF, Word documents, JPG, PNG</li>
              <li>• Files are uploaded securely and encrypted</li>
              <li>• You can remove files before uploading</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BankruptcyMultiFileUpload;
