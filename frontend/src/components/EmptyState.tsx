'use client';

import React, { ReactNode } from 'react';
import { FileText, MessageSquare, Shield, Upload } from 'lucide-react';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = ''
}: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 text-center ${className}`}>
      <div className="mb-4 flex items-center justify-center w-16 h-16 rounded-full bg-gray-100">
        {icon}
      </div>

      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {title}
      </h3>

      <p className="text-sm text-gray-600 mb-6 max-w-sm">
        {description}
      </p>

      {action && (
        <div className="flex gap-3">
          {action}
        </div>
      )}
    </div>
  );
}

// Preset empty states for common scenarios
export function NoDocumentsEmpty({ onUpload }: { onUpload: () => void }) {
  return (
    <EmptyState
      icon={<FileText className="w-8 h-8 text-gray-400" />}
      title="No documents yet"
      description="Upload your first legal document to get started with AI-powered analysis, Q&A, and defense building."
      action={
        <button
          onClick={onUpload}
          className="px-6 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition-colors flex items-center gap-2"
        >
          <Upload className="w-4 h-4" />
          Upload Document
        </button>
      }
    />
  );
}

export function NoQAHistoryEmpty() {
  return (
    <EmptyState
      icon={<MessageSquare className="w-8 h-8 text-gray-400" />}
      title="No questions asked yet"
      description="Start a conversation by asking questions about your legal document. The AI will provide detailed answers based on the document content."
      action={null}
    />
  );
}

export function NoDefenseAnalysisEmpty() {
  return (
    <EmptyState
      icon={<Shield className="w-8 h-8 text-gray-400" />}
      title="No defense strategy yet"
      description="Answer a few questions about your case, and the AI will build a comprehensive defense strategy tailored to your situation."
      action={null}
    />
  );
}
