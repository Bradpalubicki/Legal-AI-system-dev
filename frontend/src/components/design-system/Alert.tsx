'use client';

import React from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react';

interface AlertProps {
  children: React.ReactNode;
  variant?: 'info' | 'success' | 'warning' | 'error';
  title?: string;
  dismissible?: boolean;
  onDismiss?: () => void;
  className?: string;
  icon?: React.ReactNode;
}

export function Alert({
  children,
  variant = 'info',
  title,
  dismissible = false,
  onDismiss,
  className = '',
  icon,
}: AlertProps) {
  const variants = {
    info: {
      container: 'bg-teal-50 border-teal-200 text-teal-800',
      icon: <Info className="w-5 h-5 text-teal-600" />,
      title: 'text-teal-800',
    },
    success: {
      container: 'bg-success-50 border-success-200 text-success-800',
      icon: <CheckCircle className="w-5 h-5 text-success-600" />,
      title: 'text-success-800',
    },
    warning: {
      container: 'bg-warning-50 border-warning-200 text-warning-800',
      icon: <AlertTriangle className="w-5 h-5 text-warning-600" />,
      title: 'text-warning-800',
    },
    error: {
      container: 'bg-error-50 border-error-200 text-error-800',
      icon: <AlertCircle className="w-5 h-5 text-error-600" />,
      title: 'text-error-800',
    },
  };

  const config = variants[variant];

  return (
    <div
      className={`flex items-start gap-3 p-4 rounded-lg border ${config.container} ${className}`}
      role="alert"
    >
      <span className="flex-shrink-0 mt-0.5">{icon || config.icon}</span>
      <div className="flex-1 min-w-0">
        {title && (
          <h4 className={`font-semibold mb-1 ${config.title}`}>{title}</h4>
        )}
        <div className="text-sm">{children}</div>
      </div>
      {dismissible && onDismiss && (
        <button
          onClick={onDismiss}
          className="flex-shrink-0 p-1 rounded hover:bg-black/5 transition-colors"
          aria-label="Dismiss"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

export default Alert;
