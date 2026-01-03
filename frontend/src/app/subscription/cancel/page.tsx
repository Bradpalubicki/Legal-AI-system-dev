'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { XCircle, ArrowLeft, CreditCard, HelpCircle } from 'lucide-react';

export default function SubscriptionCancelPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-navy-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full text-center">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Cancel Icon */}
          <div className="mx-auto w-20 h-20 mb-6 bg-amber-100 rounded-full flex items-center justify-center">
            <XCircle className="h-12 w-12 text-amber-600" />
          </div>

          <h1 className="text-2xl font-bold text-navy-800 mb-2">
            Payment Cancelled
          </h1>

          <p className="text-gray-600 mb-6">
            No worries! Your payment was not processed. You can continue using the free features or try subscribing again when you're ready.
          </p>

          {/* Options */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
            <h3 className="font-semibold text-gray-800 mb-3">Your options:</h3>
            <ul className="space-y-3">
              <li className="flex items-start gap-3">
                <CreditCard className="h-5 w-5 text-teal-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-800">Try again</p>
                  <p className="text-xs text-gray-500">
                    Return to pricing and choose a plan
                  </p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <ArrowLeft className="h-5 w-5 text-teal-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-800">Use free tier</p>
                  <p className="text-xs text-gray-500">
                    Continue with limited free features
                  </p>
                </div>
              </li>
              <li className="flex items-start gap-3">
                <HelpCircle className="h-5 w-5 text-teal-500 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-gray-800">Need help?</p>
                  <p className="text-xs text-gray-500">
                    Contact us at support@courtcase-search.com
                  </p>
                </div>
              </li>
            </ul>
          </div>

          {/* CTA Buttons */}
          <div className="space-y-3">
            <Link
              href="/#pricing"
              className="flex items-center justify-center gap-2 w-full bg-teal-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-teal-700 transition-colors"
            >
              <CreditCard className="h-4 w-4" />
              View Pricing Plans
            </Link>

            <Link
              href="/"
              className="flex items-center justify-center gap-2 w-full bg-gray-100 text-gray-700 py-3 px-4 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Go to Dashboard
            </Link>
          </div>

          {/* Support Note */}
          <p className="mt-6 text-xs text-gray-500">
            Having trouble with payment?{' '}
            <a
              href="mailto:support@courtcase-search.com"
              className="text-teal-600 hover:text-teal-700 underline"
            >
              Contact support
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
