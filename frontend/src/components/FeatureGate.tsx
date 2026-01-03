/**
 * FeatureGate Component
 * Conditionally renders content based on feature access
 * Shows upgrade prompts for locked features
 */
import React, { ReactNode } from 'react';
import { useFeatureAccess } from '@/hooks/useFeatureAccess';
import { UpgradePrompt } from './UpgradePrompt';
import { Loader2, Lock } from 'lucide-react';

interface FeatureGateProps {
  feature: string;
  children: ReactNode;
  fallback?: ReactNode;
  showBlur?: boolean;
  showOverlay?: boolean;
  loadingComponent?: ReactNode;
}

export function FeatureGate({
  feature,
  children,
  fallback,
  showBlur = true,
  showOverlay = true,
  loadingComponent,
}: FeatureGateProps) {
  const { data: accessData, isLoading, error } = useFeatureAccess(feature);

  // Loading state
  if (isLoading) {
    return (
      <>
        {loadingComponent || (
          <div className="flex items-center justify-center p-8">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
          </div>
        )}
      </>
    );
  }

  // Error state - show content (fail open for better UX)
  if (error) {
    console.error('Feature gate error:', error);
    return <>{children}</>;
  }

  // Has access - show content
  if (accessData?.has_access) {
    return <>{children}</>;
  }

  // No access - show upgrade prompt
  if (fallback) {
    return <>{fallback}</>;
  }

  // Default fallback with blur and overlay
  return (
    <div className="relative">
      {/* Blurred content preview */}
      {showBlur && (
        <div className="blur-sm pointer-events-none select-none opacity-50">
          {children}
        </div>
      )}

      {/* Upgrade overlay */}
      {showOverlay && (
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-b from-transparent via-white/80 to-white">
          <UpgradePrompt
            feature={feature}
            upgradeInfo={accessData?.upgrade_info}
            reason={accessData?.reason}
          />
        </div>
      )}
    </div>
  );
}

/**
 * Simple feature check without rendering children
 * Useful for conditional logic without UI
 */
export function useFeatureCheck(feature: string): {
  hasAccess: boolean;
  isLoading: boolean;
  upgradeInfo?: any;
} {
  const { data, isLoading } = useFeatureAccess(feature);

  return {
    hasAccess: data?.has_access || false,
    isLoading,
    upgradeInfo: data?.upgrade_info,
  };
}

/**
 * Feature gate for navigation items
 * Shows lock icon for locked features
 */
interface FeatureNavItemProps {
  feature: string;
  children: ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
}

export function FeatureNavItem({
  feature,
  children,
  href,
  onClick,
  className = '',
}: FeatureNavItemProps) {
  const { data: accessData, isLoading } = useFeatureAccess(feature);

  const hasAccess = accessData?.has_access || false;
  const isLocked = !hasAccess && !isLoading;

  const handleClick = (e: React.MouseEvent) => {
    if (isLocked) {
      e.preventDefault();
      // TODO: Show upgrade modal
      return;
    }

    if (onClick) {
      onClick();
    }
  };

  return (
    <a
      href={isLocked ? '#' : href}
      onClick={handleClick}
      className={`${className} ${isLocked ? 'opacity-60 cursor-not-allowed' : ''}`}
    >
      <span className="flex items-center gap-2">
        {children}
        {isLocked && <Lock className="h-4 w-4 text-yellow-500" />}
      </span>
    </a>
  );
}

/**
 * Feature badge to show tier requirement
 */
interface FeatureBadgeProps {
  tier: 'case_monitor' | 'pro' | 'firm';
  className?: string;
}

export function FeatureBadge({ tier, className = '' }: FeatureBadgeProps) {
  const tierConfig = {
    case_monitor: {
      label: 'Case Monitor',
      color: 'bg-blue-100 text-blue-700',
    },
    pro: {
      label: 'Pro',
      color: 'bg-purple-100 text-purple-700',
    },
    firm: {
      label: 'Firm',
      color: 'bg-green-100 text-green-700',
    },
  };

  const config = tierConfig[tier];

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium ${config.color} ${className}`}
    >
      <Lock className="h-3 w-3" />
      {config.label}
    </span>
  );
}
