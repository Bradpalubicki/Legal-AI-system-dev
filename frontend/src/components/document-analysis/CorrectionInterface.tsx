'use client';

import React, { useState, useCallback } from 'react';
import {
  Edit3,
  Save,
  X,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Undo,
  RotateCcw,
  Brain,
  User,
  Scale,
  Clock,
  FileText,
  MessageSquare,
  Flag
} from 'lucide-react';

interface CorrectionData {
  originalValue: string;
  correctedValue: string;
  reason: string;
  confidence: number;
  timestamp: string;
  reviewerNotes?: string;
}

interface CorrectionInterfaceProps {
  fieldName: string;
  originalValue: string;
  fieldType: 'text' | 'date' | 'number' | 'list' | 'boolean';
  aiConfidence: number;
  onCorrect: (correction: CorrectionData) => void;
  onRevert?: () => void;
  existingCorrection?: CorrectionData;
  isReadOnly?: boolean;
  className?: string;
}

const CorrectionInterface: React.FC<CorrectionInterfaceProps> = ({
  fieldName,
  originalValue,
  fieldType,
  aiConfidence,
  onCorrect,
  onRevert,
  existingCorrection,
  isReadOnly = false,
  className = ''
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [correctedValue, setCorrectedValue] = useState(
    existingCorrection?.correctedValue || originalValue
  );
  const [correctionReason, setCorrectionReason] = useState(
    existingCorrection?.reason || ''
  );
  const [reviewerNotes, setReviewerNotes] = useState(
    existingCorrection?.reviewerNotes || ''
  );
  const [showReasonDialog, setShowReasonDialog] = useState(false);

  const correctionReasons = [
    'AI misinterpreted text format',
    'Context was misunderstood',
    'Legal terminology was incorrect',
    'Date format was parsed incorrectly',
    'Numbers were transcribed incorrectly',
    'Party names were confused',
    'Citation format was wrong',
    'Missing or extra information',
    'Conflicting information in document',
    'Other (see notes)'
  ];

  const handleStartEdit = useCallback(() => {
    if (isReadOnly) return;
    setIsEditing(true);
  }, [isReadOnly]);

  const handleCancelEdit = useCallback(() => {
    setCorrectedValue(existingCorrection?.correctedValue || originalValue);
    setCorrectionReason(existingCorrection?.reason || '');
    setReviewerNotes(existingCorrection?.reviewerNotes || '');
    setIsEditing(false);
    setShowReasonDialog(false);
  }, [existingCorrection, originalValue]);

  const handleSaveCorrection = useCallback(() => {
    if (!correctionReason.trim()) {
      setShowReasonDialog(true);
      return;
    }

    const correction: CorrectionData = {
      originalValue,
      correctedValue,
      reason: correctionReason,
      confidence: 1.0, // Human corrections have 100% confidence
      timestamp: new Date().toISOString(),
      reviewerNotes: reviewerNotes.trim() || undefined
    };

    onCorrect(correction);
    setIsEditing(false);
    setShowReasonDialog(false);
  }, [correctedValue, correctionReason, reviewerNotes, originalValue, onCorrect]);

  const handleRevert = useCallback(() => {
    if (onRevert) {
      onRevert();
      setCorrectedValue(originalValue);
      setCorrectionReason('');
      setReviewerNotes('');
    }
  }, [onRevert, originalValue]);

  const getFieldInput = () => {
    const baseClasses = "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500";
    
    switch (fieldType) {
      case 'date':
        return (
          <input
            type="date"
            value={correctedValue}
            onChange={(e) => setCorrectedValue(e.target.value)}
            className={baseClasses}
            disabled={!isEditing}
          />
        );
      case 'number':
        return (
          <input
            type="number"
            value={correctedValue}
            onChange={(e) => setCorrectedValue(e.target.value)}
            className={baseClasses}
            disabled={!isEditing}
          />
        );
      case 'boolean':
        return (
          <select
            value={correctedValue}
            onChange={(e) => setCorrectedValue(e.target.value)}
            className={baseClasses}
            disabled={!isEditing}
          >
            <option value="true">Yes</option>
            <option value="false">No</option>
            <option value="">Unknown</option>
          </select>
        );
      case 'list':
        return (
          <textarea
            value={correctedValue}
            onChange={(e) => setCorrectedValue(e.target.value)}
            className={baseClasses}
            rows={3}
            disabled={!isEditing}
            placeholder="Enter items separated by commas or new lines"
          />
        );
      default:
        return (
          <textarea
            value={correctedValue}
            onChange={(e) => setCorrectedValue(e.target.value)}
            className={baseClasses}
            rows={2}
            disabled={!isEditing}
          />
        );
    }
  };

  const hasChanges = correctedValue !== originalValue;
  const isOriginalLowConfidence = aiConfidence < 0.6;

  return (
    <div className={`space-y-3 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <h5 className="text-sm font-medium text-gray-900">{fieldName}</h5>
          {isOriginalLowConfidence && (
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-error-100 text-error-800">
              <Flag className="h-3 w-3 mr-1" />
              Review Needed
            </span>
          )}
          {existingCorrection && (
            <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-success-100 text-success-800">
              <User className="h-3 w-3 mr-1" />
              Corrected
            </span>
          )}
        </div>

        {!isReadOnly && (
          <div className="flex items-center space-x-1">
            {!isEditing ? (
              <>
                <button
                  onClick={handleStartEdit}
                  className="p-1 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
                  title="Edit this field"
                >
                  <Edit3 className="h-4 w-4" />
                </button>
                {existingCorrection && onRevert && (
                  <button
                    onClick={handleRevert}
                    className="p-1 text-error-600 hover:text-error-800 hover:bg-error-100 rounded"
                    title="Revert to original AI value"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </button>
                )}
              </>
            ) : (
              <>
                <button
                  onClick={handleSaveCorrection}
                  className="p-1 text-success-600 hover:text-success-800 hover:bg-success-100 rounded"
                  title="Save correction"
                >
                  <Save className="h-4 w-4" />
                </button>
                <button
                  onClick={handleCancelEdit}
                  className="p-1 text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded"
                  title="Cancel editing"
                >
                  <X className="h-4 w-4" />
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {/* Original vs Current Value Display */}
      <div className="grid grid-cols-1 gap-3">
        {/* Original AI Value */}
        <div className="bg-blue-50 border border-blue-200 rounded p-3">
          <div className="flex items-center space-x-2 mb-1">
            <Brain className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Original AI Extraction</span>
            <span className="text-xs text-blue-700">
              ({(aiConfidence * 100).toFixed(0)}% confidence)
            </span>
          </div>
          <div className="text-sm text-blue-800 font-mono bg-white border border-blue-200 rounded p-2">
            {originalValue || <em className="text-gray-500">No value extracted</em>}
          </div>
        </div>

        {/* Current/Corrected Value */}
        <div className={`border rounded p-3 ${
          hasChanges 
            ? 'bg-success-50 border-success-200' 
            : 'bg-white border-gray-200'
        }`}>
          <div className="flex items-center space-x-2 mb-2">
            {hasChanges ? (
              <>
                <User className="h-4 w-4 text-success-600" />
                <span className="text-sm font-medium text-success-900">Attorney Corrected</span>
              </>
            ) : (
              <>
                <FileText className="h-4 w-4 text-gray-600" />
                <span className="text-sm font-medium text-gray-900">Current Value</span>
              </>
            )}
          </div>
          {getFieldInput()}
        </div>
      </div>

      {/* Correction Reason (when editing) */}
      {isEditing && (
        <div className="space-y-2">
          <label className="text-sm font-medium text-gray-700">
            Reason for Correction *
          </label>
          <select
            value={correctionReason}
            onChange={(e) => setCorrectionReason(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
            required
          >
            <option value="">Select reason...</option>
            {correctionReasons.map((reason, index) => (
              <option key={index} value={reason}>
                {reason}
              </option>
            ))}
          </select>
          
          <div className="mt-2">
            <label className="text-sm font-medium text-gray-700">
              Additional Notes (Optional)
            </label>
            <textarea
              value={reviewerNotes}
              onChange={(e) => setReviewerNotes(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 mt-1"
              rows={2}
              placeholder="Additional context or explanation for this correction..."
            />
          </div>
        </div>
      )}

      {/* Existing Correction Details */}
      {existingCorrection && !isEditing && (
        <div className="bg-gray-50 border border-gray-200 rounded p-3">
          <div className="flex items-center space-x-2 mb-2">
            <MessageSquare className="h-4 w-4 text-gray-600" />
            <span className="text-sm font-medium text-gray-900">Correction Details</span>
          </div>
          <div className="space-y-2 text-sm text-gray-700">
            <div>
              <span className="font-medium">Reason:</span> {existingCorrection.reason}
            </div>
            {existingCorrection.reviewerNotes && (
              <div>
                <span className="font-medium">Notes:</span> {existingCorrection.reviewerNotes}
              </div>
            )}
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <div className="flex items-center space-x-1">
                <Clock className="h-3 w-3" />
                <span>{new Date(existingCorrection.timestamp).toLocaleString()}</span>
              </div>
              <div className="flex items-center space-x-1">
                <CheckCircle className="h-3 w-3 text-success-600" />
                <span>Human Verified</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reason Selection Dialog */}
      {showReasonDialog && (
        <div className="bg-amber-50 border border-amber-200 rounded p-3">
          <div className="flex items-start space-x-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-sm font-medium text-amber-900 mb-1">
                Correction Reason Required
              </h5>
              <p className="text-sm text-amber-800 mb-2">
                Please select a reason for this correction to maintain proper documentation 
                and improve AI training.
              </p>
              <button
                onClick={() => setShowReasonDialog(false)}
                className="text-xs text-amber-700 hover:text-amber-800 underline"
              >
                Okay, I'll select a reason
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Professional Responsibility Notice */}
      {isEditing && (
        <div className="bg-legal-50 border border-legal-200 rounded p-3">
          <div className="flex items-start space-x-2">
            <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
            <div className="text-xs text-legal-700">
              <p className="font-medium mb-1">Professional Responsibility</p>
              <p>
                Attorney corrections become part of the permanent record. Ensure accuracy 
                and maintain professional standards in all modifications to AI-extracted data.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CorrectionInterface;