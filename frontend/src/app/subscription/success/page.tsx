'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { CheckCircle, ArrowRight, Loader2, PartyPopper } from 'lucide-react';
import axios from 'axios';
import { API_CONFIG } from '@/config/api';

export default function SubscriptionSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionId = searchParams.get('session_id');

  const [isVerifying, setIsVerifying] = useState(true);
  const [subscriptionDetails, setSubscriptionDetails] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const verifySubscription = async () => {
      if (!sessionId) {
        setIsVerifying(false);
        return;
      }

      try {
        // Optional: Verify the session with your backend
        const token = localStorage.getItem('accessToken');
        if (token) {
          const response = await axios.get(
            `${API_CONFIG.BASE_URL}/api/v1/billing/subscription`,
            {
              headers: { Authorization: `Bearer ${token}` },
            }
          );
          setSubscriptionDetails(response.data);
        }
      } catch (err) {
        console.error('Failed to verify subscription:', err);
        // Don't show error - subscription might still be processing via webhook
      } finally {
        setIsVerifying(false);
      }
    };

    verifySubscription();
  }, [sessionId]);

  // Auto-redirect to dashboard after 5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      router.push('/');
    }, 8000);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-navy-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full text-center">
        {isVerifying ? (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <Loader2 className="h-16 w-16 text-teal-600 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-800">
              Confirming your subscription...
            </h2>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            {/* Success Icon */}
            <div className="relative mx-auto w-20 h-20 mb-6">
              <div className="absolute inset-0 bg-teal-100 rounded-full animate-ping opacity-25" />
              <div className="relative bg-teal-100 rounded-full w-20 h-20 flex items-center justify-center">
                <CheckCircle className="h-12 w-12 text-teal-600" />
              </div>
            </div>

            {/* Celebration */}
            <div className="flex justify-center gap-2 mb-4">
              <PartyPopper className="h-6 w-6 text-amber-500" />
              <PartyPopper className="h-6 w-6 text-amber-500 transform scale-x-[-1]" />
            </div>

            <h1 className="text-2xl font-bold text-navy-800 mb-2">
              Welcome to the Team!
            </h1>

            <p className="text-gray-600 mb-6">
              Your subscription is now active. You have full access to all the features included in your plan.
            </p>

            {subscriptionDetails && (
              <div className="bg-teal-50 border border-teal-200 rounded-lg p-4 mb-6 text-left">
                <h3 className="font-semibold text-teal-800 mb-2">Subscription Details</h3>
                <p className="text-sm text-teal-700">
                  <strong>Plan:</strong> {subscriptionDetails.plan_name}
                </p>
                {subscriptionDetails.trial_end && (
                  <p className="text-sm text-teal-700">
                    <strong>Trial ends:</strong> {new Date(subscriptionDetails.trial_end).toLocaleDateString()}
                  </p>
                )}
              </div>
            )}

            {/* What's Next */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
              <h3 className="font-semibold text-gray-800 mb-3">What you can do now:</h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-teal-500" />
                  Search federal court cases
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-teal-500" />
                  Upload documents for AI analysis
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-teal-500" />
                  Monitor cases for new filings
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-teal-500" />
                  Build defense strategies with AI
                </li>
              </ul>
            </div>

            {/* CTA Buttons */}
            <div className="space-y-3">
              <Link
                href="/"
                className="flex items-center justify-center gap-2 w-full bg-teal-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-teal-700 transition-colors"
              >
                Go to Dashboard
                <ArrowRight className="h-4 w-4" />
              </Link>

              <p className="text-xs text-gray-500">
                Redirecting automatically in a few seconds...
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
