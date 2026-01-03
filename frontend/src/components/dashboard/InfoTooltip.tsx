'use client';

import React, { useState } from 'react';
import { HelpCircle, Info, Scale, BookOpen } from 'lucide-react';

interface InfoTooltipProps {
  content: string;
  title?: string;
  type?: 'info' | 'warning' | 'legal' | 'educational';
  position?: 'top' | 'bottom' | 'left' | 'right';
  className?: string;
  maxWidth?: string;
}

const InfoTooltip: React.FC<InfoTooltipProps> = ({
  content,
  title,
  type = 'info',
  position = 'top',
  className = '',
  maxWidth = 'w-64'
}) => {
  const [isVisible, setIsVisible] = useState(false);

  const getTypeStyles = () => {
    switch (type) {
      case 'warning':
        return {
          icon: 'text-warning-500 hover:text-warning-600',
          tooltip: 'bg-warning-50 border-warning-200 text-warning-900',
          titleColor: 'text-warning-800'
        };
      case 'legal':
        return {
          icon: 'text-legal-500 hover:text-legal-600',
          tooltip: 'bg-legal-50 border-legal-200 text-legal-900',
          titleColor: 'text-legal-800'
        };
      case 'educational':
        return {
          icon: 'text-blue-500 hover:text-blue-600',
          tooltip: 'bg-blue-50 border-blue-200 text-blue-900',
          titleColor: 'text-blue-800'
        };
      default:
        return {
          icon: 'text-gray-400 hover:text-gray-600',
          tooltip: 'bg-white border-gray-200 text-gray-900',
          titleColor: 'text-gray-800'
        };
    }
  };

  const getPositionStyles = () => {
    switch (position) {
      case 'bottom':
        return 'top-full left-1/2 transform -translate-x-1/2 mt-2';
      case 'left':
        return 'right-full top-1/2 transform -translate-y-1/2 mr-2';
      case 'right':
        return 'left-full top-1/2 transform -translate-y-1/2 ml-2';
      default: // top
        return 'bottom-full left-1/2 transform -translate-x-1/2 mb-2';
    }
  };

  const getArrowStyles = () => {
    const baseArrow = 'absolute w-2 h-2 bg-white border transform rotate-45';
    switch (position) {
      case 'bottom':
        return `${baseArrow} -top-1 left-1/2 -translate-x-1/2 border-b-0 border-r-0`;
      case 'left':
        return `${baseArrow} -right-1 top-1/2 -translate-y-1/2 border-l-0 border-t-0`;
      case 'right':
        return `${baseArrow} -left-1 top-1/2 -translate-y-1/2 border-r-0 border-b-0`;
      default: // top
        return `${baseArrow} -bottom-1 left-1/2 -translate-x-1/2 border-t-0 border-l-0`;
    }
  };

  const styles = getTypeStyles();

  const getIcon = () => {
    switch (type) {
      case 'legal':
        return <Scale className="h-4 w-4" />;
      case 'educational':
        return <BookOpen className="h-4 w-4" />;
      case 'warning':
        return <Info className="h-4 w-4" />;
      default:
        return <HelpCircle className="h-4 w-4" />;
    }
  };

  return (
    <div className={`relative inline-block ${className}`}>
      <button
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        onFocus={() => setIsVisible(true)}
        onBlur={() => setIsVisible(false)}
        className={`transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-50 rounded ${styles.icon}`}
        aria-label="Information tooltip"
        type="button"
      >
        {getIcon()}
      </button>

      {isVisible && (
        <div
          className={`
            absolute ${getPositionStyles()} ${maxWidth} p-3 rounded-lg shadow-lg border z-50
            ${styles.tooltip}
            animate-fade-in
          `}
          role="tooltip"
        >
          {/* Arrow */}
          <div className={`${getArrowStyles()} ${styles.tooltip.includes('bg-white') ? 'bg-white' : 'bg-gray-50'}`} />
          
          {/* Content */}
          <div>
            {title && (
              <h6 className={`text-xs font-semibold mb-1 ${styles.titleColor}`}>
                {title}
              </h6>
            )}
            <p className="text-xs leading-relaxed">
              {content}
            </p>
          </div>

          {/* Educational Enhancement */}
          {type === 'educational' && (
            <div className="mt-2 pt-2 border-t border-blue-200">
              <p className="text-xs text-blue-700 font-medium">
                💡 Learn More: This information helps you understand legal concepts and professional requirements.
              </p>
            </div>
          )}

          {/* Legal Professional Notice */}
          {type === 'legal' && (
            <div className="mt-2 pt-2 border-t border-legal-200">
              <p className="text-xs text-legal-600">
                ⚖️ <strong>Professional Note:</strong> Always verify legal information with authoritative sources.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Enhanced version with "Learn More" functionality
interface LearnMoreTooltipProps extends InfoTooltipProps {
  learnMoreUrl?: string;
  whyThisMatters?: string;
}

export const LearnMoreTooltip: React.FC<LearnMoreTooltipProps> = ({
  learnMoreUrl,
  whyThisMatters,
  ...props
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const styles = props.type === 'legal' ? 
    { tooltip: 'bg-legal-50 border-legal-200 text-legal-900' } : 
    { tooltip: 'bg-blue-50 border-blue-200 text-blue-900' };

  return (
    <div className={`relative inline-block ${props.className || ''}`}>
      <button
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className="text-primary-500 hover:text-primary-600 transition-colors"
        aria-label="Learn more information"
      >
        <BookOpen className="h-4 w-4" />
      </button>

      {isVisible && (
        <div
          className={`
            absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-80 p-4 
            rounded-lg shadow-lg border z-50 ${styles.tooltip} animate-fade-in
          `}
        >
          <div className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 w-2 h-2 bg-white border rotate-45 border-t-0 border-l-0" />
          
          <div>
            <h6 className="text-sm font-semibold mb-2 text-gray-900">
              {props.title || 'Learn More'}
            </h6>
            
            <p className="text-sm text-gray-700 mb-3">
              {props.content}
            </p>

            {whyThisMatters && (
              <div className="mb-3 p-2 bg-blue-100 border border-blue-200 rounded">
                <h6 className="text-xs font-semibold text-blue-900 mb-1">
                  Why This Matters
                </h6>
                <p className="text-xs text-blue-800">
                  {whyThisMatters}
                </p>
              </div>
            )}

            {learnMoreUrl && (
              <a
                href={learnMoreUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
                onClick={() => setIsVisible(false)}
              >
                Learn More →
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default InfoTooltip;