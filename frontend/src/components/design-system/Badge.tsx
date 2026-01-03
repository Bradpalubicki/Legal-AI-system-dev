'use client';

import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'error' | 'info' | 'outline';
  size?: 'sm' | 'md';
  className?: string;
  icon?: React.ReactNode;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  className = '',
  icon,
}: BadgeProps) {
  const variants = {
    default: 'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200',
    success: 'bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300 dark:border dark:border-teal-400',
    warning: 'bg-warning-50 text-warning-700 dark:bg-amber-900/30 dark:text-amber-300',
    error: 'bg-error-50 text-error-700 dark:bg-red-900/30 dark:text-red-300',
    info: 'bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-300',
    outline: 'bg-white border border-slate-300 text-slate-700 dark:bg-slate-800 dark:border-slate-600 dark:text-slate-200',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded-md ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </span>
  );
}

// Status badge specifically for document/case status
interface StatusBadgeProps {
  status: 'pending' | 'processing' | 'completed' | 'error' | 'new';
  className?: string;
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const statusConfig = {
    pending: { label: 'Pending', variant: 'warning' as const },
    processing: { label: 'Processing', variant: 'info' as const },
    completed: { label: 'Completed', variant: 'success' as const },
    error: { label: 'Error', variant: 'error' as const },
    new: { label: 'New', variant: 'info' as const },
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} size="sm" className={className}>
      <span className={`w-1.5 h-1.5 rounded-full ${
        status === 'pending' ? 'bg-warning-500' :
        status === 'processing' ? 'bg-teal-500 animate-pulse' :
        status === 'completed' ? 'bg-success-500' :
        status === 'error' ? 'bg-error-500' :
        'bg-teal-500'
      }`} />
      {config.label}
    </Badge>
  );
}

export default Badge;
