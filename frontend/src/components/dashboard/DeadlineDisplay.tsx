'use client';

import React, { useState } from 'react';
import { 
  Clock, 
  AlertTriangle, 
  Info, 
  Calendar,
  Scale,
  HelpCircle,
  ExternalLink
} from 'lucide-react';
import { formatComplianceDate, getDaysUntilExpiration } from '@/utils/compliance-utils';

interface Deadline {
  id: string;
  matterId: string;
  matterTitle: string;
  description: string;
  dueDate: string;
  type: 'filing' | 'hearing' | 'discovery' | 'statute_of_limitations' | 'other';
  priority: 'low' | 'medium' | 'high' | 'critical';
  isInformational: boolean;
}

interface DeadlineDisplayProps {
  deadline: Deadline;
  showDisclaimers?: boolean;
  className?: string;
}

const DeadlineDisplay: React.FC<DeadlineDisplayProps> = ({ 
  deadline, 
  showDisclaimers = true,
  className = '' 
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  const daysUntil = getDaysUntilExpiration(deadline.dueDate);
  const isOverdue = daysUntil < 0;
  const isUrgent = daysUntil <= 3 && daysUntil >= 0;

  const getPriorityColor = (priority: Deadline['priority']) => {
    switch (priority) {
      case 'critical':
        return 'text-error-600 bg-error-50 border-error-200';
      case 'high':
        return 'text-warning-600 bg-warning-50 border-warning-200';
      case 'medium':
        return 'text-primary-600 bg-primary-50 border-primary-200';
      case 'low':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getTypeIcon = (type: Deadline['type']) => {
    switch (type) {
      case 'filing':
        return <Calendar className="h-4 w-4" />;
      case 'hearing':
        return <Scale className="h-4 w-4" />;
      case 'discovery':
        return <Info className="h-4 w-4" />;
      case 'statute_of_limitations':
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getUrgencyStyles = () => {
    if (isOverdue) {
      return 'border-l-4 border-l-error-500 bg-error-50';
    } else if (isUrgent) {
      return 'border-l-4 border-l-warning-500 bg-warning-50';
    } else if (daysUntil <= 7) {
      return 'border-l-4 border-l-primary-500 bg-primary-50';
    }
    return 'border-l-4 border-l-gray-300 bg-white';
  };

  const formatDaysUntil = (days: number) => {
    if (days < 0) {
      return `${Math.abs(days)} day${Math.abs(days) !== 1 ? 's' : ''} overdue`;
    } else if (days === 0) {
      return 'Due today';
    } else if (days === 1) {
      return 'Due tomorrow';
    } else {
      return `${days} day${days !== 1 ? 's' : ''} remaining`;
    }
  };

  const getDisclaimerText = (type: Deadline['type']) => {
    switch (type) {
      case 'filing':
        return 'Filing deadlines shown are typical timeframes. Always verify actual deadlines with applicable court rules and orders.';
      case 'hearing':
        return 'Hearing dates are informational. Confirm all court dates through official court calendars and notices.';
      case 'discovery':
        return 'Discovery deadlines may vary by jurisdiction and case specifics. Verify with local rules and court orders.';
      case 'statute_of_limitations':
        return 'Statute of limitations information is general. Consult applicable statutes and case law for specific situations.';
      default:
        return 'Deadline information is provided for reference only. Always verify through official sources.';
    }
  };

  return (
    <div className={`
      relative rounded-lg p-4 border transition-all duration-200
      ${getUrgencyStyles()}
      ${className}
    `}>
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div className={`p-1 rounded ${getPriorityColor(deadline.priority)}`}>
            {getTypeIcon(deadline.type)}
          </div>
          <div>
            <h4 className="font-medium text-gray-900">
              {deadline.description}
            </h4>
            <p className="text-sm text-gray-600">
              {deadline.matterTitle}
            </p>
          </div>
        </div>

        {/* Informational Badge */}
        {showDisclaimers && deadline.isInformational && (
          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            <Info className="h-3 w-3 mr-1" />
            Info Only
          </span>
        )}
      </div>

      {/* Due Date and Urgency */}
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="text-sm font-medium text-gray-900">
            {formatComplianceDate(deadline.dueDate)}
          </div>
          <div className={`text-sm font-medium ${
            isOverdue ? 'text-error-600' : 
            isUrgent ? 'text-warning-600' : 
            'text-gray-600'
          }`}>
            {formatDaysUntil(daysUntil)}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Priority Badge */}
          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getPriorityColor(deadline.priority)}`}>
            {deadline.priority.toUpperCase()}
          </span>

          {/* Help Tooltip */}
          {showDisclaimers && (
            <div className="relative">
              <button
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Deadline disclaimer information"
              >
                <HelpCircle className="h-4 w-4" />
              </button>

              {showTooltip && (
                <div className="absolute right-0 bottom-full mb-2 w-64 bg-white border border-gray-200 rounded-lg shadow-lg p-3 z-10">
                  <div className="flex items-start space-x-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <h5 className="text-xs font-semibold text-gray-900 mb-1">
                        Deadline Disclaimer
                      </h5>
                      <p className="text-xs text-gray-700">
                        {getDisclaimerText(deadline.type)}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Type-specific Information */}
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span className="capitalize">
          {deadline.type.replace('_', ' ')} deadline
        </span>
        
        <a 
          href={`/dashboard/${deadline.matterId}`}
          className="inline-flex items-center text-primary-600 hover:text-primary-500 font-medium"
        >
          View matter
          <ExternalLink className="h-3 w-3 ml-1" />
        </a>
      </div>

      {/* Professional Responsibility Notice */}
      {showDisclaimers && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="flex items-start space-x-2">
            <Scale className="h-3 w-3 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs text-legal-700">
                <strong>Professional Responsibility:</strong> You remain responsible for verifying 
                all deadlines through official court records, applicable rules, and case-specific orders. 
                This information is provided for reference only.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Educational "Why This Matters" Section */}
      {showDisclaimers && deadline.type === 'statute_of_limitations' && (
        <div className="mt-3 pt-3 border-t border-blue-100 bg-blue-25 -mx-4 -mb-4 px-4 pb-4 rounded-b-lg">
          <div className="flex items-start space-x-2">
            <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-xs font-semibold text-blue-900 mb-1">
                Why This Matters
              </h5>
              <p className="text-xs text-blue-800">
                Statute of limitations deadlines are absolute. Missing these deadlines typically 
                results in permanent loss of the right to bring a claim. Always verify with 
                applicable statutes and recent case law, as calculation rules can be complex.
              </p>
              <a 
                href="/resources/statute-limitations" 
                className="inline-flex items-center mt-1 text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                Learn More About Statute of Limitations
                <ExternalLink className="h-3 w-3 ml-1" />
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeadlineDisplay;