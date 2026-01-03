/**
 * UpgradePrompt Component
 * Displays upgrade messaging and CTAs for locked features
 */
import React from 'react';
import { useRouter } from 'next/router';
import { Zap, ArrowRight, Lock, Star } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

interface UpgradeInfo {
  feature: string;
  description: string;
  target_tier: string;
  tier_name: string;
  price: string;
  message: string;
  cta: string;
  upgrade_url: string;
}

interface UpgradePromptProps {
  feature: string;
  upgradeInfo?: UpgradeInfo;
  reason?: string;
  compact?: boolean;
  className?: string;
}

export function UpgradePrompt({
  feature,
  upgradeInfo,
  reason,
  compact = false,
  className = '',
}: UpgradePromptProps) {
  const router = useRouter();

  const handleUpgrade = () => {
    if (upgradeInfo?.upgrade_url) {
      router.push(upgradeInfo.upgrade_url);
    } else {
      router.push('/upgrade');
    }
  };

  if (compact) {
    return (
      <div className={`flex items-center gap-4 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200 ${className}`}>
        <div className="flex-shrink-0">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Lock className="h-5 w-5 text-purple-600" />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900">
            {upgradeInfo?.message || 'Upgrade to unlock this feature'}
          </p>
          <p className="text-xs text-gray-500 mt-0.5">
            {upgradeInfo?.tier_name} • {upgradeInfo?.price}
          </p>
        </div>

        <Button onClick={handleUpgrade} size="sm" variant="default">
          Upgrade
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    );
  }

  return (
    <Card className={`max-w-md ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-purple-500 to-blue-500 rounded-xl">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl">Unlock This Feature</CardTitle>
              <CardDescription>{reason || 'Upgrade your plan to continue'}</CardDescription>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="p-4 bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg border border-purple-100">
          <div className="flex items-start gap-3">
            <Star className="h-5 w-5 text-purple-600 mt-0.5 flex-shrink-0" />
            <div>
              <p className="font-medium text-gray-900 mb-1">
                {upgradeInfo?.tier_name || 'Pro'}
              </p>
              <p className="text-sm text-gray-600">
                {upgradeInfo?.description || 'Get full access to all features'}
              </p>
            </div>
          </div>
        </div>

        {upgradeInfo && (
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-gray-900">
              {upgradeInfo.price}
            </span>
            {upgradeInfo.tier_name !== 'Case Monitor' && (
              <span className="text-gray-500">/month</span>
            )}
          </div>
        )}

        <ul className="space-y-2 text-sm text-gray-600">
          <li className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-purple-500" />
            Unlock immediately after upgrade
          </li>
          <li className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-purple-500" />
            Cancel anytime
          </li>
          <li className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-purple-500" />
            14-day money-back guarantee
          </li>
        </ul>
      </CardContent>

      <CardFooter className="flex gap-3">
        <Button onClick={handleUpgrade} className="flex-1" size="lg">
          {upgradeInfo?.cta || 'Upgrade Now'}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          onClick={() => router.push('/pricing')}
          size="lg"
        >
          Compare Plans
        </Button>
      </CardFooter>
    </Card>
  );
}

/**
 * Inline upgrade banner for page headers
 */
export function UpgradeBanner({
  message,
  tierName,
  price,
  onUpgrade,
  onDismiss,
}: {
  message: string;
  tierName?: string;
  price?: string;
  onUpgrade?: () => void;
  onDismiss?: () => void;
}) {
  const router = useRouter();

  const handleUpgrade = () => {
    if (onUpgrade) {
      onUpgrade();
    } else {
      router.push('/upgrade');
    }
  };

  return (
    <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-4">
            <Zap className="h-5 w-5" />
            <div>
              <p className="font-medium">{message}</p>
              {tierName && price && (
                <p className="text-sm text-purple-100">
                  {tierName} • {price}
                </p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              onClick={handleUpgrade}
              variant="secondary"
              size="sm"
              className="bg-white text-purple-600 hover:bg-gray-100"
            >
              Upgrade Now
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-purple-100 hover:text-white text-sm"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Feature preview card with upgrade prompt
 */
export function FeaturePreviewCard({
  title,
  description,
  icon: Icon,
  tierName,
  price,
  benefits,
  onUpgrade,
}: {
  title: string;
  description: string;
  icon?: React.ElementType;
  tierName: string;
  price: string;
  benefits: string[];
  onUpgrade?: () => void;
}) {
  const router = useRouter();

  const handleUpgrade = () => {
    if (onUpgrade) {
      onUpgrade();
    } else {
      router.push('/upgrade');
    }
  };

  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {Icon && (
              <div className="p-2 bg-gradient-to-br from-purple-100 to-blue-100 rounded-lg">
                <Icon className="h-5 w-5 text-purple-600" />
              </div>
            )}
            <div>
              <CardTitle className="text-lg">{title}</CardTitle>
              <CardDescription className="mt-1">{description}</CardDescription>
            </div>
          </div>
          <Lock className="h-5 w-5 text-yellow-500" />
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="inline-flex items-baseline gap-2 px-3 py-1 bg-purple-50 rounded-full">
          <span className="text-sm font-medium text-purple-700">{tierName}</span>
          <span className="text-sm text-purple-600">• {price}</span>
        </div>

        <ul className="space-y-2">
          {benefits.map((benefit, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
              <Zap className="h-4 w-4 text-purple-500 mt-0.5 flex-shrink-0" />
              {benefit}
            </li>
          ))}
        </ul>
      </CardContent>

      <CardFooter>
        <Button onClick={handleUpgrade} className="w-full">
          Upgrade to {tierName}
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
