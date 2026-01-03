/**
 * PricingTiers Component
 * Displays pricing tier comparison with feature lists
 */
import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { Check, Zap, Star, Building2, Eye, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useUserTier } from '@/hooks/useFeatureAccess';

interface PricingTier {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  price: {
    monthly?: number;
    perCase?: number;
    display: string;
  };
  features: string[];
  limitations?: string[];
  popular?: boolean;
  cta: string;
  href: string;
}

const tiers: PricingTier[] = [
  {
    id: 'case_monitor',
    name: 'Case Monitor',
    description: 'Perfect for tracking one case or monitoring unlimited cases',
    icon: Eye,
    price: {
      monthly: 19,
      perCase: 5,
      display: '$5/case or $19/month',
    },
    features: [
      'Monitor unlimited cases ($19/mo) or 1 case ($5)',
      'Email notifications for case updates',
      'View and download documents',
      'Basic case timeline',
      'Unlimited CourtListener searches',
    ],
    limitations: [
      'No AI document analysis',
      'No document comparison',
      'No PACER searches',
    ],
    cta: 'Start Monitoring',
    href: '/subscribe?tier=case_monitor',
  },
  {
    id: 'pro',
    name: 'Pro',
    description: 'For attorneys and power users who need AI analysis and research',
    icon: Zap,
    price: {
      monthly: 49,
      display: '$49/month',
    },
    features: [
      'Everything in Case Monitor, plus:',
      'AI-powered document analysis',
      'Document summarization (100/mo)',
      'Document comparison (50/mo)',
      'AI legal assistant (200 queries/mo)',
      'PACER searches ($100 credits included)',
      'Legal research tools',
      'Citation validation',
      'SMS notifications (100/mo)',
      'Export to PDF/Word',
    ],
    popular: true,
    cta: 'Start Pro Trial',
    href: '/subscribe?tier=pro',
  },
  {
    id: 'firm',
    name: 'Firm',
    description: 'For law firms needing team collaboration and API access',
    icon: Building2,
    price: {
      monthly: 199,
      display: '$199/month',
    },
    features: [
      'Everything in Pro, unlimited:',
      'Unlimited AI analysis',
      'Unlimited document comparisons',
      'Unlimited document uploads',
      'Team collaboration (up to 10 users)',
      'Client portal access',
      'Matter management',
      'PACER searches ($500 credits included)',
      'API access (10k requests/day)',
      'Webhook integrations',
      'Zapier integration',
      'Audit logs (1 year retention)',
      'Compliance reporting',
      'Priority support',
    ],
    cta: 'Contact Sales',
    href: '/contact-sales',
  },
];

export function PricingTiers() {
  const router = useRouter();
  const { data: userTier } = useUserTier();
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');

  const handleSubscribe = (tier: PricingTier) => {
    router.push(tier.href);
  };

  const isCurrentTier = (tierId: string) => {
    return userTier?.tier === tierId;
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h2 className="text-3xl font-bold text-gray-900">
          Choose the Right Plan for You
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Start with a free trial. Upgrade anytime. Cancel anytime.
        </p>

        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              billingCycle === 'monthly'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle('annual')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              billingCycle === 'annual'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            Annual
            <Badge className="ml-2 bg-green-500">Save 20%</Badge>
          </button>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid md:grid-cols-3 gap-8 max-w-7xl mx-auto">
        {tiers.map((tier) => {
          const Icon = tier.icon;
          const isCurrent = isCurrentTier(tier.id);

          return (
            <Card
              key={tier.id}
              className={`relative ${
                tier.popular
                  ? 'border-purple-500 border-2 shadow-xl'
                  : 'border-gray-200'
              }`}
            >
              {tier.popular && (
                <div className="absolute -top-4 left-0 right-0 flex justify-center">
                  <Badge className="bg-purple-600 text-white px-4 py-1">
                    <Star className="h-3 w-3 mr-1" />
                    Most Popular
                  </Badge>
                </div>
              )}

              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-gradient-to-br from-purple-100 to-blue-100 rounded-lg">
                    <Icon className="h-6 w-6 text-purple-600" />
                  </div>
                  <CardTitle className="text-2xl">{tier.name}</CardTitle>
                </div>
                <CardDescription className="text-base">
                  {tier.description}
                </CardDescription>

                {/* Price */}
                <div className="mt-4">
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-gray-900">
                      {tier.price.display}
                    </span>
                  </div>
                  {tier.price.perCase && (
                    <p className="text-sm text-gray-500 mt-1">
                      Pay per case or get unlimited for ${tier.price.monthly}/mo
                    </p>
                  )}
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* Features */}
                <ul className="space-y-3">
                  {tier.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-3">
                      <Check className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className="text-sm text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* Limitations */}
                {tier.limitations && tier.limitations.length > 0 && (
                  <div className="pt-4 border-t border-gray-100">
                    <p className="text-xs font-medium text-gray-500 mb-2">
                      Not included:
                    </p>
                    <ul className="space-y-2">
                      {tier.limitations.map((limitation, index) => (
                        <li key={index} className="text-xs text-gray-500 pl-3">
                          • {limitation}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>

              <CardFooter>
                {isCurrent ? (
                  <Button variant="outline" className="w-full" disabled>
                    Current Plan
                  </Button>
                ) : (
                  <Button
                    onClick={() => handleSubscribe(tier)}
                    className={`w-full ${
                      tier.popular
                        ? 'bg-purple-600 hover:bg-purple-700'
                        : ''
                    }`}
                    size="lg"
                  >
                    {tier.cta}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                )}
              </CardFooter>
            </Card>
          );
        })}
      </div>

      {/* FAQ or Additional Info */}
      <div className="text-center space-y-4 pt-8">
        <p className="text-gray-600">
          All plans include 14-day free trial • Cancel anytime
        </p>
        <div className="flex items-center justify-center gap-6 text-sm text-gray-500">
          <span>✓ No credit card required</span>
          <span>✓ Money-back guarantee</span>
          <span>✓ Secure payments</span>
        </div>
      </div>
    </div>
  );
}

/**
 * Compact tier selector for upgrade flows
 */
export function TierSelector({
  currentTier,
  onSelect,
}: {
  currentTier?: string;
  onSelect: (tierId: string) => void;
}) {
  return (
    <div className="grid gap-4">
      {tiers.map((tier) => {
        const Icon = tier.icon;
        const isCurrent = currentTier === tier.id;

        return (
          <button
            key={tier.id}
            onClick={() => onSelect(tier.id)}
            disabled={isCurrent}
            className={`text-left p-4 rounded-lg border-2 transition-all ${
              isCurrent
                ? 'border-gray-300 bg-gray-50 opacity-50 cursor-not-allowed'
                : 'border-gray-200 hover:border-purple-500 hover:shadow-md'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3 flex-1">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Icon className="h-5 w-5 text-purple-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-semibold text-gray-900">{tier.name}</h4>
                    {tier.popular && (
                      <Badge className="bg-purple-600 text-xs">Popular</Badge>
                    )}
                    {isCurrent && (
                      <Badge variant="outline" className="text-xs">
                        Current
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{tier.description}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-gray-900">{tier.price.display}</p>
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
