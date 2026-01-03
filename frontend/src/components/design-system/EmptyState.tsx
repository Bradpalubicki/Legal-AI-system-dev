'use client';

import React from 'react';
import { FileText, Search, FolderOpen, Inbox } from 'lucide-react';
import { Button } from './Button';

interface EmptyStateProps {
  icon?: 'document' | 'search' | 'folder' | 'inbox' | React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: 'primary' | 'secondary' | 'outline';
  };
  className?: string;
}

export function EmptyState({
  icon = 'document',
  title,
  description,
  action,
  className = '',
}: EmptyStateProps) {
  const iconMap = {
    document: FileText,
    search: Search,
    folder: FolderOpen,
    inbox: Inbox,
  };

  const IconComponent = typeof icon === 'string' ? iconMap[icon] : null;

  return (
    <div className={`flex flex-col items-center justify-center py-12 px-4 text-center ${className}`}>
      <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
        {IconComponent ? (
          <IconComponent className="w-8 h-8 text-slate-400" />
        ) : (
          icon
        )}
      </div>
      <h3 className="text-lg font-semibold text-navy-800 mb-2">{title}</h3>
      {description && (
        <p className="text-slate-500 max-w-sm mb-6">{description}</p>
      )}
      {action && (
        <Button
          variant={action.variant || 'primary'}
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  );
}

export default EmptyState;
