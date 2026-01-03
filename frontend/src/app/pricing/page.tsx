'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { Check, ArrowLeft, Loader2, Sparkles } from 'lucide-react';
import { API_CONFIG } from '@/config/api';

interface PricingTier {
  name: string;
  planId: string;
  priceMonthly: string;
  priceAnnual: string;
  annualTotal?: string;
  period: string;
  description: string;
  features: string[];
  cta: string;
  highlighted: boolean;
  credits?: number;
  caseMonitoring?: number;
}

const pricingTiers: PricingTier[] = [
  {
    name: 'Free',
    planId: 'free',
    priceMonthly: '$0',
    priceAnnual: '$0',
    period: 'forever',
    description: 'Get started with basic access',
    features: [
      'Unlimited case search',
      '1 case monitoring',
      'Document preview',
      'Basic court information',
    ],
    cta: 'Get Started Free',
    highlighted: false,
    credits: 0,
    caseMonitoring: 1,
  },
  {
    name: 'Basic',
    planId: 'basic',
    priceMonthly: '$9.99',
    priceAnnual: '$8.33',
    annualTotal: '$99.99/year',
    period: '/month',
    description: 'Essential features for individuals',
    features: [
      '20 document credits/month',
      '5 case monitoring',
      'Email notifications',
      'Basic AI analysis',
      '14-day free trial',
    ],
    cta: 'Start Free Trial',
    highlighted: false,
    credits: 20,
    caseMonitoring: 5,
  },
  {
    name: 'Individual Pro',
    planId: 'individual_pro',
    priceMonthly: '$29.99',
    priceAnnual: '$25',
    annualTotal: '$299.99/year',
    period: '/month',
    description: 'Advanced features for power users',
    features: [
      '75 document credits/month',
      '25 case monitoring',
      'Advanced AI analysis',
      'Export reports',
      'API access',
      'Priority email support',
      '14-day free trial',
    ],
    cta: 'Start Free Trial',
    highlighted: true,
    credits: 75,
    caseMonitoring: 25,
  },
  {
    name: 'Professional',
    planId: 'professional',
    priceMonthly: '$99',
    priceAnnual: '$83.25',
    annualTotal: '$999/year',
    period: '/month',
    description: 'Complete toolkit for professionals',
    features: [
      '200 document credits/month',
      '100 case monitoring',
      'All AI features',
      'Bulk downloads',
      'Priority support',
      'Custom integrations',
      '14-day free trial',
    ],
    cta: 'Start Free Trial',
    highlighted: false,
    credits: 200,
    caseMonitoring: 100,
  },
];

export default function PricingPage() {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly');
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSelectPlan = async (tier: PricingTier) => {
    setError(null);

    // Free plan - go to registration or dashboard
    if (tier.planId === 'free') {
      if (isAuthenticated) {
        router.push('/');
      } else {
        router.push('/auth/register');
      }
      return;
    }

    // Paid plan - need to create checkout session
    if (isAuthenticated) {
      // Create Stripe checkout session
      setLoadingPlan(tier.planId);
      try {
        const token = localStorage.getItem('accessToken');
        const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/billing/create-checkout-session`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            plan: tier.planId,
            billing_period: billingPeriod,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to create checkout session');
        }

        const data = await response.json();
        if (data.checkout_url) {
          window.location.href = data.checkout_url;
        } else {
          throw new Error('No checkout URL returned');
        }
      } catch (err) {
        console.error('Checkout error:', err);
        setError(err instanceof Error ? err.message : 'Failed to start checkout');
        setLoadingPlan(null);
      }
    } else {
      // Not authenticated - go to registration with plan params
      router.push(`/auth/register?plan=${tier.planId}&billing=${billingPeriod}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-navy-900 to-slate-900">
      {/* Header */}
      <div className="border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Link
              href="/"
              className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to {isAuthenticated ? 'Dashboard' : 'Home'}
            </Link>
            {!isAuthenticated && (
              <Link
                href="/auth/login"
                className="text-teal-400 hover:text-teal-300 font-medium transition-colors"
              >
                Already have an account? Sign in
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
            Choose Your Plan
          </h1>
          <p className="text-xl text-slate-300 max-w-2xl mx-auto">
            {isAuthenticated
              ? 'Upgrade your account to unlock more features'
              : 'Start free and upgrade when you need more power'
            }
          </p>
        </div>

        {/* Billing Toggle */}
        <div className="flex items-center justify-center gap-4 mb-12">
          <button
            onClick={() => setBillingPeriod('monthly')}
            className={`px-6 py-2.5 rounded-lg font-medium transition-all ${
              billingPeriod === 'monthly'
                ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/25'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingPeriod('annual')}
            className={`px-6 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 ${
              billingPeriod === 'annual'
                ? 'bg-teal-500 text-white shadow-lg shadow-teal-500/25'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            Annual
            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
              billingPeriod === 'annual'
                ? 'bg-white text-teal-600'
                : 'bg-teal-500 text-white'
            }`}>
              Save 17%
            </span>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="max-w-md mx-auto mb-8 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-center">
            {error}
          </div>
        )}

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
          {pricingTiers.map((tier) => (
            <div
              key={tier.planId}
              className={`relative rounded-2xl p-8 transition-all duration-300 ${
                tier.highlighted
                  ? 'bg-white text-slate-900 shadow-2xl shadow-teal-500/20 scale-105 z-10'
                  : 'bg-slate-800/50 text-white border border-slate-700/50 hover:border-slate-600'
              }`}
            >
              {/* Popular Badge */}
              {tier.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <div className="bg-gradient-to-r from-teal-500 to-emerald-500 text-white text-sm font-semibold px-4 py-1 rounded-full flex items-center gap-1 shadow-lg">
                    <Sparkles className="w-4 h-4" />
                    Most Popular
                  </div>
                </div>
              )}

              {/* Plan Name */}
              <h3 className={`text-xl font-semibold mb-2 ${tier.highlighted ? 'text-slate-900' : 'text-white'}`}>
                {tier.name}
              </h3>

              {/* Price */}
              <div className="mb-2">
                <span className="text-4xl font-bold">
                  {billingPeriod === 'monthly' ? tier.priceMonthly : tier.priceAnnual}
                </span>
                <span className={tier.highlighted ? 'text-slate-500' : 'text-slate-400'}>
                  {tier.period}
                </span>
              </div>

              {/* Annual Total */}
              {billingPeriod === 'annual' && tier.annualTotal && (
                <p className={`text-sm mb-4 ${tier.highlighted ? 'text-teal-600' : 'text-teal-400'}`}>
                  Billed as {tier.annualTotal}
                </p>
              )}
              {(billingPeriod === 'monthly' || !tier.annualTotal) && <div className="h-6 mb-4" />}

              {/* Description */}
              <p className={`mb-6 ${tier.highlighted ? 'text-slate-600' : 'text-slate-400'}`}>
                {tier.description}
              </p>

              {/* Features */}
              <ul className="space-y-3 mb-8">
                {tier.features.map((feature, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <Check className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                      tier.highlighted ? 'text-teal-500' : 'text-teal-400'
                    }`} />
                    <span className={tier.highlighted ? 'text-slate-600' : 'text-slate-300'}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              {/* CTA Button */}
              <button
                onClick={() => handleSelectPlan(tier)}
                disabled={loadingPlan === tier.planId}
                className={`w-full py-3 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 ${
                  tier.highlighted
                    ? 'bg-teal-600 text-white hover:bg-teal-700 shadow-lg shadow-teal-500/25'
                    : 'bg-slate-700 text-white hover:bg-slate-600'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {loadingPlan === tier.planId ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  tier.cta
                )}
              </button>
            </div>
          ))}
        </div>

        {/* Additional Info */}
        <div className="mt-12 text-center space-y-4">
          <p className="text-slate-300">
            All paid plans include a <span className="text-teal-400 font-medium">14-day free trial</span> • Cancel anytime
          </p>
          <p className="text-slate-400 text-sm">
            Need more credits? Buy credit packs starting at $6.25 for 25 pages
          </p>
          <p className="text-slate-400">
            Need a custom solution?{' '}
            <a
              href="mailto:support@courtcase-search.com"
              className="text-teal-400 hover:text-teal-300 underline"
            >
              Contact us for Enterprise pricing
            </a>
          </p>
        </div>

        {/* Trust Badges */}
        <div className="mt-16 pt-8 border-t border-slate-700/50">
          <div className="flex flex-wrap justify-center items-center gap-8 text-slate-400 text-sm">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span>Secure payments via Stripe</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span>256-bit SSL encryption</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              <span>No credit card required for free tier</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
