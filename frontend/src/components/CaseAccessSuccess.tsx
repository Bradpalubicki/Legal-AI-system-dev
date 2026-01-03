/**
 * CaseAccessSuccess Component
 * Shows confirmation after successful case access purchase
 */
import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import { CheckCircle, Bell, Download, Eye, ArrowRight, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useCaseAccessCheck } from '@/hooks/useCaseAccess';

interface CaseAccessSuccessProps {
  caseId: number;
  sessionId?: string;
}

export function CaseAccessSuccess({ caseId, sessionId }: CaseAccessSuccessProps) {
  const router = useRouter();
  const { data: accessData, isLoading, refetch } = useCaseAccessCheck(caseId);

  // Poll for access activation (Stripe webhook might take a few seconds)
  useEffect(() => {
    if (!accessData?.has_access) {
      const pollInterval = setInterval(() => {
        refetch();
      }, 2000); // Check every 2 seconds

      // Stop polling after 30 seconds
      const timeout = setTimeout(() => {
        clearInterval(pollInterval);
      }, 30000);

      return () => {
        clearInterval(pollInterval);
        clearTimeout(timeout);
      };
    }
  }, [accessData, refetch]);

  if (isLoading || !accessData?.has_access) {
    return (
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardContent className="pt-12 pb-12 text-center">
            <Loader2 className="h-12 w-12 animate-spin text-purple-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Processing Your Purchase...</h3>
            <p className="text-gray-600">
              Please wait while we activate your case access. This usually takes just a few seconds.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Success Message */}
      <Card className="border-green-200 bg-green-50">
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-500 rounded-full">
              <CheckCircle className="h-8 w-8 text-white" />
            </div>
            <div>
              <CardTitle className="text-2xl text-green-900">
                Case Access Activated!
              </CardTitle>
              <CardDescription className="text-green-700">
                You now have full access to monitor this case
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* What's Next */}
      <Card>
        <CardHeader>
          <CardTitle>What happens next?</CardTitle>
          <CardDescription>
            Here's how to make the most of your case monitoring
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Bell className="h-6 w-6 text-purple-600" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold mb-1">You'll Get Notified</h4>
              <p className="text-sm text-gray-600">
                We'll send you an email whenever there are new filings, motions,
                or status changes in this case.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Download className="h-6 w-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold mb-1">Download Documents</h4>
              <p className="text-sm text-gray-600">
                Access and download all court documents filed in this case.
                We'll check RECAP first to save you money.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="p-2 bg-green-100 rounded-lg">
              <Eye className="h-6 w-6 text-green-600" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold mb-1">View Case Timeline</h4>
              <p className="text-sm text-gray-600">
                See the complete case history, upcoming events, and important deadlines
                in an easy-to-follow timeline.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Access Details */}
      <Card>
        <CardHeader>
          <CardTitle>Your Access Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-600">Access Type:</span>
            <span className="font-medium capitalize">
              {accessData.access_type?.replace('_', ' ')}
            </span>
          </div>

          {accessData.expires_at ? (
            <div className="flex justify-between">
              <span className="text-gray-600">Expires:</span>
              <span className="font-medium">
                {new Date(accessData.expires_at).toLocaleDateString()}
                {accessData.days_remaining !== null && (
                  <span className="text-sm text-gray-500 ml-2">
                    ({accessData.days_remaining} days)
                  </span>
                )}
              </span>
            </div>
          ) : (
            <div className="flex justify-between">
              <span className="text-gray-600">Duration:</span>
              <span className="font-medium text-green-600">
                Until case closes
              </span>
            </div>
          )}

          <div className="flex justify-between">
            <span className="text-gray-600">Notifications:</span>
            <span className="font-medium text-green-600">Enabled</span>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <div className="flex gap-4">
        <Button
          onClick={() => router.push(`/cases/${caseId}`)}
          size="lg"
          className="flex-1"
        >
          View Case
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
        <Button
          onClick={() => router.push('/cases')}
          variant="outline"
          size="lg"
          className="flex-1"
        >
          My Cases
        </Button>
      </div>

      {/* Receipt */}
      <div className="text-center text-sm text-gray-500">
        <p>A receipt has been sent to your email</p>
        {sessionId && (
          <p className="mt-1">Order ID: {sessionId.slice(0, 16)}...</p>
        )}
      </div>

      {/* Upgrade Suggestion */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-100">
        <h4 className="font-semibold mb-2">Want to monitor more cases?</h4>
        <p className="text-sm text-gray-600 mb-4">
          Upgrade to Pro for unlimited case monitoring, AI document analysis,
          and PACER credits starting at $49/month
        </p>
        <Button
          variant="outline"
          onClick={() => router.push('/pricing')}
        >
          View Plans
        </Button>
      </div>
    </div>
  );
}

/**
 * Compact success banner for inline display
 */
export function CaseAccessSuccessBanner({ caseId }: { caseId: number }) {
  const router = useRouter();
  const { data: accessData } = useCaseAccessCheck(caseId);

  if (!accessData?.has_access) {
    return null;
  }

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3">
          <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
          <div>
            <h4 className="font-semibold text-green-900">
              Case Access Active
            </h4>
            <p className="text-sm text-green-700 mt-1">
              You're now monitoring this case and will receive email notifications
            </p>
          </div>
        </div>
        <Button
          size="sm"
          variant="outline"
          onClick={() => router.push(`/cases/${caseId}`)}
        >
          View Case
        </Button>
      </div>
    </div>
  );
}
