'use client';

import React, { useState, useCallback } from 'react';
import {
  Download,
  FileText,
  Table,
  FileJson,
  Shield,
  AlertTriangle,
  Eye,
  EyeOff,
  Scale,
  Lock,
  Users,
  Calendar,
  CheckCircle,
  X,
  Printer,
  Mail,
  Copy,
  Settings,
  Clock,
  User
} from 'lucide-react';

interface ExportData {
  documentId: string;
  documentName: string;
  privilegeLevel: 'public' | 'confidential' | 'attorney_client' | 'work_product';
  analysisResults: Record<string, any>;
  verificationStatus: Record<string, boolean>;
  corrections: Record<string, any>;
  reviewNotes: string;
  reviewerInfo: {
    name: string;
    barNumber?: string;
    timestamp: string;
  };
}

interface ExportFormat {
  id: string;
  name: string;
  extension: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  privilegeCompatible: boolean;
  redactionSupport: boolean;
}

interface ExportOperationsProps {
  data: ExportData;
  onExport: (format: string, options: ExportOptions) => Promise<void>;
  className?: string;
}

interface ExportOptions {
  format: string;
  includeConfidential: boolean;
  includePrivileged: boolean;
  includeVerificationNotes: boolean;
  includeCorrections: boolean;
  redactSensitive: boolean;
  watermark: boolean;
  passwordProtect: boolean;
  recipients?: string[];
  expirationDate?: string;
}

const ExportOperations: React.FC<ExportOperationsProps> = ({
  data,
  onExport,
  className = ''
}) => {
  const [selectedFormat, setSelectedFormat] = useState<string>('pdf');
  const [exportOptions, setExportOptions] = useState<ExportOptions>({
    format: 'pdf',
    includeConfidential: false,
    includePrivileged: false,
    includeVerificationNotes: true,
    includeCorrections: true,
    redactSensitive: true,
    watermark: true,
    passwordProtect: false,
    recipients: [],
    expirationDate: ''
  });
  
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
  const [showPrivilegeWarning, setShowPrivilegeWarning] = useState(false);
  const [exportInProgress, setExportInProgress] = useState(false);

  const exportFormats: ExportFormat[] = [
    {
      id: 'pdf',
      name: 'PDF Report',
      extension: 'pdf',
      icon: FileText,
      description: 'Professional PDF with redaction support',
      privilegeCompatible: true,
      redactionSupport: true
    },
    {
      id: 'docx',
      name: 'Word Document',
      extension: 'docx',
      icon: FileText,
      description: 'Editable Word document',
      privilegeCompatible: true,
      redactionSupport: false
    },
    {
      id: 'excel',
      name: 'Excel Spreadsheet',
      extension: 'xlsx',
      icon: Table,
      description: 'Structured data in Excel format',
      privilegeCompatible: false,
      redactionSupport: false
    },
    {
      id: 'json',
      name: 'JSON Data',
      extension: 'json',
      icon: FileJson,
      description: 'Machine-readable JSON format',
      privilegeCompatible: false,
      redactionSupport: false
    }
  ];

  const getPrivilegeLevelColor = (level: string) => {
    switch (level) {
      case 'attorney_client':
      case 'work_product':
        return 'text-error-700 bg-error-100 border-error-300';
      case 'confidential':
        return 'text-warning-700 bg-warning-100 border-warning-300';
      default:
        return 'text-gray-700 bg-gray-100 border-gray-300';
    }
  };

  const getPrivilegeLevelLabel = (level: string) => {
    switch (level) {
      case 'attorney_client':
        return 'Attorney-Client Privileged';
      case 'work_product':
        return 'Work Product Protected';
      case 'confidential':
        return 'Confidential';
      default:
        return 'Public';
    }
  };

  const handleFormatChange = useCallback((formatId: string) => {
    setSelectedFormat(formatId);
    setExportOptions(prev => ({ ...prev, format: formatId }));
    
    const format = exportFormats.find(f => f.id === formatId);
    if (format && !format.privilegeCompatible && 
        (data.privilegeLevel === 'attorney_client' || data.privilegeLevel === 'work_product')) {
      setShowPrivilegeWarning(true);
    } else {
      setShowPrivilegeWarning(false);
    }
  }, [data.privilegeLevel, exportFormats]);

  const handleExport = useCallback(async () => {
    if ((exportOptions.includeConfidential || exportOptions.includePrivileged) &&
        !exportOptions.passwordProtect) {
      alert('Password protection is required when including confidential or privileged information.');
      return;
    }

    setExportInProgress(true);
    try {
      await onExport(selectedFormat, exportOptions);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again.');
    } finally {
      setExportInProgress(false);
    }
  }, [selectedFormat, exportOptions, onExport]);

  const selectedFormatInfo = exportFormats.find(f => f.id === selectedFormat);

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Document Privilege Warning */}
      <div className={`border rounded-lg p-3 ${getPrivilegeLevelColor(data.privilegeLevel)}`}>
        <div className="flex items-start space-x-2">
          <Shield className="h-5 w-5 mt-0.5 flex-shrink-0" />
          <div>
            <h4 className="font-semibold mb-1">
              {getPrivilegeLevelLabel(data.privilegeLevel)} Document
            </h4>
            <p className="text-sm">
              This document contains {data.privilegeLevel.replace('_', '-')} information. 
              Export operations must comply with privilege protection requirements.
            </p>
          </div>
        </div>
      </div>

      {/* Export Format Selection */}
      <div>
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Export Format</h4>
        <div className="grid grid-cols-2 gap-3">
          {exportFormats.map((format) => {
            const IconComponent = format.icon;
            const isCompatible = format.privilegeCompatible || 
              !['attorney_client', 'work_product'].includes(data.privilegeLevel);
            
            return (
              <button
                key={format.id}
                onClick={() => handleFormatChange(format.id)}
                disabled={!isCompatible}
                className={`p-3 border rounded-lg text-left transition-colors ${
                  selectedFormat === format.id
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : isCompatible
                    ? 'border-gray-200 hover:border-gray-300 text-gray-700'
                    : 'border-gray-200 text-gray-400 cursor-not-allowed opacity-50'
                }`}
              >
                <div className="flex items-start space-x-2">
                  <IconComponent className="h-5 w-5 mt-0.5 flex-shrink-0" />
                  <div>
                    <div className="font-medium">{format.name}</div>
                    <div className="text-xs mt-1">{format.description}</div>
                    {!isCompatible && (
                      <div className="text-xs text-error-600 mt-1 flex items-center space-x-1">
                        <AlertTriangle className="h-3 w-3" />
                        <span>Not privilege-compatible</span>
                      </div>
                    )}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Privilege Warning */}
      {showPrivilegeWarning && (
        <div className="bg-error-50 border border-error-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <AlertTriangle className="h-5 w-5 text-error-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-sm font-semibold text-error-900 mb-1">
                Privilege Protection Warning
              </h5>
              <p className="text-sm text-error-800">
                The selected export format may not adequately protect privileged information. 
                Consider using PDF format with redaction for privileged documents.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Basic Export Options */}
      <div>
        <h4 className="text-sm font-semibold text-gray-900 mb-3">Export Content</h4>
        <div className="space-y-2">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={exportOptions.includeVerificationNotes}
              onChange={(e) => setExportOptions(prev => ({
                ...prev,
                includeVerificationNotes: e.target.checked
              }))}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Include verification notes</span>
          </label>
          
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={exportOptions.includeCorrections}
              onChange={(e) => setExportOptions(prev => ({
                ...prev,
                includeCorrections: e.target.checked
              }))}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Include attorney corrections</span>
          </label>

          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={exportOptions.watermark}
              onChange={(e) => setExportOptions(prev => ({
                ...prev,
                watermark: e.target.checked
              }))}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm text-gray-700">Add confidentiality watermark</span>
          </label>
        </div>
      </div>

      {/* Advanced Options */}
      <div className="border-t border-gray-200 pt-4">
        <button
          onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
          className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-800"
        >
          <Settings className="h-4 w-4" />
          <span>Advanced Options</span>
          {showAdvancedOptions ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </button>

        {showAdvancedOptions && (
          <div className="mt-3 space-y-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
            {/* Sensitive Content Options */}
            {(data.privilegeLevel === 'attorney_client' || data.privilegeLevel === 'work_product') && (
              <div>
                <h5 className="text-sm font-semibold text-gray-900 mb-2">Privileged Content</h5>
                <div className="space-y-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={exportOptions.includePrivileged}
                      onChange={(e) => setExportOptions(prev => ({
                        ...prev,
                        includePrivileged: e.target.checked
                      }))}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700">Include privileged information</span>
                    <Lock className="h-3 w-3 text-error-600" />
                  </label>
                  
                  {selectedFormatInfo?.redactionSupport && (
                    <label className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        checked={exportOptions.redactSensitive}
                        onChange={(e) => setExportOptions(prev => ({
                          ...prev,
                          redactSensitive: e.target.checked
                        }))}
                        className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <span className="text-sm text-gray-700">Auto-redact sensitive information</span>
                    </label>
                  )}
                </div>
              </div>
            )}

            {/* Security Options */}
            <div>
              <h5 className="text-sm font-semibold text-gray-900 mb-2">Security</h5>
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={exportOptions.passwordProtect}
                    onChange={(e) => setExportOptions(prev => ({
                      ...prev,
                      passwordProtect: e.target.checked
                    }))}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm text-gray-700">Password protect export</span>
                  <Lock className="h-3 w-3 text-gray-500" />
                </label>

                <div className="ml-6">
                  <label className="block text-xs text-gray-600 mb-1">
                    Document expiration (optional)
                  </label>
                  <input
                    type="date"
                    value={exportOptions.expirationDate || ''}
                    onChange={(e) => setExportOptions(prev => ({
                      ...prev,
                      expirationDate: e.target.value
                    }))}
                    className="text-xs border border-gray-300 rounded px-2 py-1"
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
              </div>
            </div>

            {/* Recipients (for sharing) */}
            <div>
              <h5 className="text-sm font-semibold text-gray-900 mb-2">Authorized Recipients</h5>
              <div className="flex items-center space-x-2 text-xs text-gray-600">
                <Users className="h-3 w-3" />
                <span>Track who receives this export for privilege protection</span>
              </div>
              <textarea
                placeholder="Enter email addresses of authorized recipients (optional)"
                className="mt-1 w-full px-2 py-1 border border-gray-300 rounded text-xs"
                rows={2}
                onChange={(e) => setExportOptions(prev => ({
                  ...prev,
                  recipients: e.target.value.split(/[,\n]/).map(r => r.trim()).filter(Boolean)
                }))}
              />
            </div>
          </div>
        )}
      </div>

      {/* Export Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <FileText className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <h5 className="font-semibold text-blue-900 mb-1">Export Summary</h5>
            <div className="text-blue-800 space-y-1">
              <div>Format: <strong>{selectedFormatInfo?.name}</strong></div>
              <div>Security: <strong>
                {exportOptions.passwordProtect ? 'Password Protected' : 'Standard'}
                {exportOptions.watermark ? ' + Watermarked' : ''}
              </strong></div>
              <div>Privilege Level: <strong>{getPrivilegeLevelLabel(data.privilegeLevel)}</strong></div>
              {exportOptions.recipients && exportOptions.recipients.length > 0 && (
                <div>Recipients: <strong>{exportOptions.recipients.length} authorized</strong></div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Export Button */}
      <div className="flex items-center justify-between pt-4 border-t border-gray-200">
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <User className="h-4 w-4" />
          <span>Reviewed by: {data.reviewerInfo.name}</span>
          {data.reviewerInfo.barNumber && (
            <span>(Bar #: {data.reviewerInfo.barNumber})</span>
          )}
        </div>

        <button
          onClick={handleExport}
          disabled={exportInProgress}
          className={`inline-flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium ${
            exportInProgress
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-primary-600 text-white hover:bg-primary-700'
          }`}
        >
          {exportInProgress ? (
            <>
              <Clock className="h-4 w-4 animate-spin" />
              <span>Exporting...</span>
            </>
          ) : (
            <>
              <Download className="h-4 w-4" />
              <span>Export {selectedFormatInfo?.name}</span>
            </>
          )}
        </button>
      </div>

      {/* Professional Responsibility Notice */}
      <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
        <div className="flex items-start space-x-2">
          <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-legal-700">
            <p className="font-medium mb-1">Export Compliance Notice</p>
            <p>
              By exporting this document analysis, you acknowledge responsibility for maintaining 
              attorney-client privilege, work product protection, and confidentiality requirements 
              in accordance with applicable professional responsibility rules.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportOperations;