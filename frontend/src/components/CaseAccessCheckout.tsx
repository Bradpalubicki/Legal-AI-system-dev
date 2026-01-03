/**
 * CaseAccessCheckout Component
 * Purchase access to monitor a specific case
 */
import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { Check, Lock, Bell, Download, Eye, Zap, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

interface CaseDetails {
  id: number;
  docket_number: string;
  case_name: string;
  court: string;
  filed_date?: string;
}

interface CaseAccessCheckoutProps {
  caseDetails: CaseDetails;
  onPurchaseComplete?: (caseAccessId: number) => void;
}

type AccessType = 'one_time' | 'monthly';

export function CaseAccessCheckout({ caseDetails, onPurchaseComplete }: CaseAccessCheckoutProps) {
  const router = useRouter();
  const [selectedType, setSelectedType] = useState<AccessType>('one_time');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePurchase = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/case-access/purchase', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          case_id: caseDetails.id,
          access_type: selectedType,
          success_url: `${window.location.origin}/case-access/success`,
          cancel_url: `${window.location.origin}/cases/${caseDetails.id}`,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || 'Failed to create checkout session');
      }

      const data = await response.json();

      // Redirect to Stripe checkout
      window.location.href = data.checkout_url;
    } catch (err: any) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  const accessOptions = [
    {
      type: 'one_time' as AccessType,
      name: 'One-Time Access',
      price: '$5',
      priceNumeric: 5,
      description: 'Monitor this case until it closes',
      features: [
        'Full case access',
        'Email notifications',
        'Download documents',
        'View case timeline',
        'No expiration',
      ],
      badge: 'Best for single cases',
    },
    {
      type: 'monthly' as AccessType,
      name: 'Monthly Unlimited',
      price: '$19/month',
      priceNumeric: 19,
      description: 'Monitor unlimited cases for 30 days',
      features: [
        'Monitor any case',
        'Unlimited cases',
        'Email notifications',
        'Download documents',
        'Renews monthly',
      ],
      badge: 'Best value for multiple cases',
      popular: true,
    },
  ];

  const selectedOption = accessOptions.find(opt => opt.type === selectedType)!;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Case Information */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <CardTitle className="text-xl">Monitor Case</CardTitle>
              <CardDescription className="mt-2">
                Get notified about updates and access all documents
              </CardDescription>
            </div>
            <Lock className="h-8 w-8 text-yellow-500" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 rounded-lg p-4 space-y-2">
            <div>
              <span className="text-sm text-gray-500">Case Number:</span>
              <p className="font-medium">{caseDetails.docket_number}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Case Name:</span>
              <p className="font-medium">{caseDetails.case_name}</p>
            </div>
            <div>
              <span className="text-sm text-gray-500">Court:</span>
              <p className="font-medium">{caseDetails.court}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Access Type Selection */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold">Choose Access Type</h3>

        <RadioGroup value={selectedType} onValueChange={(value: string) => setSelectedType(value as AccessType)}>
          <div className="grid md:grid-cols-2 gap-4">
            {accessOptions.map((option) => (
              <label
                key={option.type}
                className={`relative cursor-pointer ${
                  selectedType === option.type ? 'ring-2 ring-purple-500' : ''
                }`}
              >
                <Card className={`h-full transition-all hover:shadow-lg ${
                  selectedType === option.type ? 'border-purple-500' : ''
                }`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <RadioGroupItem value={option.type} id={option.type} />
                          <CardTitle className="text-lg">{option.name}</CardTitle>
                        </div>
                        <CardDescription>{option.description}</CardDescription>
                      </div>
                    </div>

                    {option.popular && (
                      <Badge className="absolute top-4 right-4 bg-purple-600">
                        Popular
                      </Badge>
                    )}

                    <div className="mt-4">
                      <span className="text-3xl font-bold">{option.price}</span>
                    </div>
                  </CardHeader>

                  <CardContent>
                    <ul className="space-y-2">
                      {option.features.map((feature, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <Check className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-gray-700">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </label>
            ))}
          </div>
        </RadioGroup>
      </div>

      {/* What's Included */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-purple-600" />
            What You Get
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Bell className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <h4 className="font-medium">Email Notifications</h4>
                <p className="text-sm text-gray-600">
                  Get notified instantly when there are new filings or updates
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Download className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h4 className="font-medium">Document Access</h4>
                <p className="text-sm text-gray-600">
                  Download all documents filed in the case
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Eye className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <h4 className="font-medium">Case Timeline</h4>
                <p className="text-sm text-gray-600">
                  View complete case history and upcoming events
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Lock className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <h4 className="font-medium">Secure Access</h4>
                <p className="text-sm text-gray-600">
                  Your data is encrypted and securely stored
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {/* Purchase Button */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total</p>
              <p className="text-2xl font-bold">{selectedOption.price}</p>
            </div>

            <Button
              onClick={handlePurchase}
              disabled={isLoading}
              size="lg"
              className="px-8"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  Purchase Access
                  <ArrowRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </div>

          <div className="mt-4 flex items-center justify-center gap-4 text-xs text-gray-500">
            <span>✓ Secure payment</span>
            <span>✓ Instant access</span>
            <span>✓ Cancel anytime</span>
          </div>
        </CardContent>
      </Card>

      {/* Upgrade Suggestion */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-100">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h4 className="font-semibold text-gray-900 mb-2">
              Need more features?
            </h4>
            <p className="text-sm text-gray-600 mb-4">
              Upgrade to Pro for AI document analysis, unlimited case monitoring,
              and PACER credits starting at $49/month
            </p>
            <Button
              variant="outline"
              onClick={() => router.push('/pricing')}
            >
              View Pro Plans
            </Button>
          </div>
          <Zap className="h-8 w-8 text-purple-500" />
        </div>
      </div>
    </div>
  );
}

/**
 * Compact purchase button for case pages
 */
export function PurchaseCaseAccessButton({
  caseId,
  caseName,
  compact = false,
}: {
  caseId: number;
  caseName: string;
  compact?: boolean;
}) {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/case-access/purchase?case_id=${caseId}`);
  };

  if (compact) {
    return (
      <Button onClick={handleClick} size="sm">
        <Lock className="mr-2 h-4 w-4" />
        Get Access ($5)
      </Button>
    );
  }

  return (
    <Card className="bg-gradient-to-br from-purple-50 to-blue-50 border-purple-200">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lock className="h-5 w-5 text-purple-600" />
          Monitor This Case
        </CardTitle>
        <CardDescription>
          Get notified about updates and access all documents
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">One-time access</span>
            <span className="text-xl font-bold">$5</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-600">Monthly unlimited</span>
            <span className="text-lg font-semibold">$19/month</span>
          </div>
        </div>

        <ul className="space-y-1 text-sm text-gray-600">
          <li className="flex items-center gap-2">
            <Check className="h-4 w-4 text-green-500" />
            Email notifications
          </li>
          <li className="flex items-center gap-2">
            <Check className="h-4 w-4 text-green-500" />
            Download documents
          </li>
          <li className="flex items-center gap-2">
            <Check className="h-4 w-4 text-green-500" />
            Case timeline
          </li>
        </ul>
      </CardContent>
      <CardFooter>
        <Button onClick={handleClick} className="w-full">
          Purchase Access
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  );
}
