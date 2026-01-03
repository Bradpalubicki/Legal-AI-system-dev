'use client';

import React from 'react';
import Link from 'next/link';
import { 
  Clock, 
  FileText, 
  Shield, 
  Users, 
  TrendingUp, 
  AlertTriangle,
  Info,
  Eye,
  ChevronRight
} from 'lucide-react';
import { formatComplianceDate } from '@/utils/compliance-utils';

interface Matter {
  id: string;
  title: string;
  client: string;
  type: string;
  status: 'active' | 'pending' | 'closed' | 'on_hold';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  lastActivity: string;
  nextDeadline?: string;
  aiSuggestions: number;
  documentsCount: number;
  privilegeLevel: 'public' | 'confidential' | 'attorney_client' | 'work_product';
}

interface MatterCardProps {
  matter: Matter;
  showComplianceLabels?: boolean;
  className?: string;
}

const MatterCard: React.FC<MatterCardProps> = ({ 
  matter, 
  showComplianceLabels = true, 
  className = '' 
}) => {
  const getStatusColor = (status: Matter['status']) => {
    switch (status) {
      case 'active':
        return 'bg-success-100 text-success-800';
      case 'pending':
        return 'bg-warning-100 text-warning-800';
      case 'on_hold':
        return 'bg-gray-100 text-gray-800';
      case 'closed':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: Matter['priority']) => {
    switch (priority) {
      case 'urgent':
        return 'text-error-600';
      case 'high':
        return 'text-warning-600';
      case 'medium':
        return 'text-primary-600';
      case 'low':
        return 'text-gray-600';
      default:
        return 'text-gray-600';
    }
  };

  const getPrivilegeBadge = (level: Matter['privilegeLevel']) => {
    switch (level) {
      case 'attorney_client':
        return {
          icon: <Shield className="h-3 w-3" />,
          text: 'Attorney-Client Privileged',
          color: 'bg-error-100 text-error-800 border-error-200'
        };
      case 'work_product':
        return {
          icon: <Shield className="h-3 w-3" />,
          text: 'Work Product',
          color: 'bg-warning-100 text-warning-800 border-warning-200'
        };
      case 'confidential':
        return {
          icon: <Eye className="h-3 w-3" />,
          text: 'Confidential',
          color: 'bg-blue-100 text-blue-800 border-blue-200'
        };
      case 'public':
        return {
          icon: <Info className="h-3 w-3" />,
          text: 'Public Information',
          color: 'bg-gray-100 text-gray-800 border-gray-200'
        };
      default:
        return {
          icon: <Info className="h-3 w-3" />,
          text: 'Unspecified',
          color: 'bg-gray-100 text-gray-800 border-gray-200'
        };
    }
  };

  const privilegeBadge = getPrivilegeBadge(matter.privilegeLevel);
  const isUrgent = matter.priority === 'urgent' || matter.priority === 'high';

  return (
    <div className={`
      bg-white border rounded-lg p-4 hover:shadow-md transition-all duration-200
      ${isUrgent ? 'border-l-4 border-l-warning-500' : 'border-gray-200'}
      ${className}
    `}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          {/* Matter Title and Client */}
          <div className="flex items-start justify-between mb-2">
            <div>
              <Link 
                href={`/dashboard/${matter.id}`}
                className="text-lg font-semibold text-gray-900 hover:text-primary-600 transition-colors"
              >
                {matter.title}
              </Link>
              {showComplianceLabels && (
                <div className="flex items-center mt-1">
                  <span className="text-xs text-gray-500 mr-2">
                    Status for information only
                  </span>
                  <Info className="h-3 w-3 text-gray-400" />
                </div>
              )}
            </div>
            <ChevronRight className="h-4 w-4 text-gray-400 ml-2 flex-shrink-0" />
          </div>

          {/* Client and Matter Type */}
          <div className="flex items-center space-x-4 mb-3">
            <div className="flex items-center text-sm text-gray-600">
              <Users className="h-4 w-4 mr-1" />
              {matter.client}
            </div>
            <div className="text-sm text-gray-500">
              {matter.type}
            </div>
          </div>

          {/* Status and Priority Badges */}
          <div className="flex items-center space-x-2 mb-3">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(matter.status)}`}>
              {matter.status.replace('_', ' ').toUpperCase()}
            </span>
            
            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(matter.priority)}`}>
              {matter.priority.toUpperCase()} PRIORITY
            </span>

            {showComplianceLabels && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                <Info className="h-3 w-3 mr-1" />
                Info Only
              </span>
            )}
          </div>

          {/* Privilege Level Badge */}
          {showComplianceLabels && (
            <div className="mb-3">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${privilegeBadge.color}`}>
                {privilegeBadge.icon}
                <span className="ml-1">{privilegeBadge.text}</span>
              </span>
            </div>
          )}

          {/* Matter Stats */}
          <div className="grid grid-cols-3 gap-4 mb-3">
            <div className="text-center">
              <div className="text-sm font-semibold text-gray-900">
                {matter.documentsCount}
              </div>
              <div className="text-xs text-gray-500">
                Documents
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm font-semibold text-gray-900">
                {matter.aiSuggestions}
              </div>
              <div className="text-xs text-gray-500">
                AI Suggestions
              </div>
            </div>
            <div className="text-center">
              <div className="text-sm font-semibold text-gray-900">
                {matter.nextDeadline ? 
                  new Date(matter.nextDeadline).toLocaleDateString() : 'None'}
              </div>
              <div className="text-xs text-gray-500">
                Next Deadline
              </div>
            </div>
          </div>

          {/* Last Activity */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center">
              <Clock className="h-3 w-3 mr-1" />
              Last activity: {formatComplianceDate(matter.lastActivity)}
            </div>
            
            {matter.aiSuggestions > 0 && (
              <div className="flex items-center text-primary-600">
                <TrendingUp className="h-3 w-3 mr-1" />
                <span className="font-medium">
                  {matter.aiSuggestions} AI suggestion{matter.aiSuggestions !== 1 ? 's' : ''}
                </span>
              </div>
            )}
          </div>

          {/* Professional Responsibility Notice */}
          {showComplianceLabels && (
            <div className="mt-3 pt-3 border-t border-gray-100">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="h-3 w-3 text-amber-500 mt-0.5 flex-shrink-0" />
                <p className="text-xs text-amber-700">
                  <strong>Professional Responsibility:</strong> All case information displayed is for 
                  informational purposes only. Verify all details through official court records and 
                  maintain independent professional judgment.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MatterCard;