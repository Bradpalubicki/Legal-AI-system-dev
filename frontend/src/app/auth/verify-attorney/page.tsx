'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { 
  AttorneyVerificationRequest, 
  AttorneyVerificationResponse, 
  VerificationStatus,
  LicenseStatus,
  DisciplinaryStatus
} from '@/types/legal-compliance';
import { AttorneyVerificationForm } from '@/components/compliance';
import { useAuth } from '@/hooks';
import { 
  buildApiUrl, 
  getErrorMessage, 
  getVerificationStatusColor,
  getLicenseStatusColor,
  logComplianceEvent,
  logComplianceError
} from '@/utils/compliance-utils';
import { 
  CheckCircle, 
  AlertTriangle, 
  Clock, 
  XCircle, 
  User,
  Scale,
  Building,
  MapPin,
  Calendar,
  Shield
} from 'lucide-react';
import axios from 'axios';

const AttorneyVerificationPage = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user } = useAuth();
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<AttorneyVerificationResponse | null>(null);
  const [isSkipped, setIsSkipped] = useState(false);

  const isFromOnboarding = searchParams?.get('from') === 'onboarding';
  const skipAllowed = searchParams?.get('skipAllowed') !== 'false';

  useEffect(() => {
    // Check if user is already verified
    if (user?.profileData?.licenseStatus === LicenseStatus.ACTIVE) {
      router.push('/dashboard');
    }
  }, [user, router]);

  const handleSubmit = async (data: AttorneyVerificationRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      logComplianceEvent('Starting attorney verification', { 
        barNumber: data.barNumber,
        jurisdiction: data.jurisdiction 
      });

      const response = await axios.post(
        buildApiUrl('/api/auth/verify-attorney'),
        data,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
          }
        }
      );

      if (response.data.success) {
        const result: AttorneyVerificationResponse = response.data.data;
        setVerificationResult(result);
        
        logComplianceEvent('Attorney verification completed', {
          status: result.verificationStatus,
          licenseStatus: result.licenseStatus
        });

        // If verification successful, update user profile
        if (result.isVerified && result.verificationStatus === VerificationStatus.VERIFIED) {
          setTimeout(() => {
            if (isFromOnboarding) {
              router.push('/onboarding/complete');
            } else {
              router.push('/dashboard');
            }
          }, 3000);
        }
      } else {
        throw new Error(response.data.error || 'Verification failed');
      }
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('Attorney verification failed', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    setIsSkipped(true);
    logComplianceEvent('Attorney verification skipped');
    
    setTimeout(() => {
      if (isFromOnboarding) {
        router.push('/onboarding/complete');
      } else {
        router.push('/dashboard');
      }
    }, 1000);
  };

  const getVerificationStatusIcon = (status: VerificationStatus) => {
    switch (status) {
      case VerificationStatus.VERIFIED:
        return <CheckCircle className="h-8 w-8 text-success-600" />;
      case VerificationStatus.PENDING:
        return <Clock className="h-8 w-8 text-warning-600" />;
      case VerificationStatus.FAILED:
        return <XCircle className="h-8 w-8 text-error-600" />;
      case VerificationStatus.MANUAL_REVIEW:
        return <AlertTriangle className="h-8 w-8 text-blue-600" />;
      default:
        return <Clock className="h-8 w-8 text-gray-600" />;
    }
  };

  const getStatusMessage = (result: AttorneyVerificationResponse) => {
    switch (result.verificationStatus) {
      case VerificationStatus.VERIFIED:
        return {
          title: 'Verification Successful!',
          message: 'Your attorney credentials have been verified. You now have full access to all platform features.',
          color: 'success'
        };
      case VerificationStatus.PENDING:
        return {
          title: 'Verification Pending',
          message: 'Your verification is being processed. You will receive an email notification once complete.',
          color: 'warning'
        };
      case VerificationStatus.FAILED:
        return {
          title: 'Verification Failed',
          message: 'We were unable to verify your credentials. Please check your information or contact support.',
          color: 'error'
        };
      case VerificationStatus.MANUAL_REVIEW:
        return {
          title: 'Manual Review Required',
          message: 'Your verification requires manual review by our compliance team. This typically takes 1-2 business days.',
          color: 'blue'
        };
      default:
        return {
          title: 'Unknown Status',
          message: 'Please contact support for assistance.',
          color: 'gray'
        };
    }
  };

  if (isSkipped) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-legal-50 to-primary-50 flex items-center justify-center py-12 px-4">
        <div className="max-w-md w-full text-center">
          <div className="bg-white rounded-lg shadow-legal p-8">
            <CheckCircle className="h-16 w-16 text-success-600 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Verification Skipped
            </h2>
            <p className="text-gray-600 mb-4">
              You can complete attorney verification later from your profile settings.
            </p>
            <div className="animate-pulse text-sm text-gray-500">
              Redirecting to dashboard...
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (verificationResult) {
    const statusInfo = getStatusMessage(verificationResult);
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-legal-50 to-primary-50 flex items-center justify-center py-12 px-4">
        <div className="max-w-2xl w-full">
          <div className="bg-white rounded-lg shadow-legal p-8">
            {/* Header */}
            <div className="text-center mb-8">
              {getVerificationStatusIcon(verificationResult.verificationStatus)}
              <h2 className="text-2xl font-bold text-gray-900 mt-4">
                {statusInfo.title}
              </h2>
              <p className="text-gray-600 mt-2">
                {statusInfo.message}
              </p>
            </div>

            {/* Verification Details */}
            <div className="bg-gray-50 rounded-lg p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <Shield className="h-5 w-5 mr-2" />
                Verification Details
              </h3>
              
              <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Verification Status</dt>
                  <dd className={`mt-1 text-sm font-semibold ${getVerificationStatusColor(verificationResult.verificationStatus)}`}>
                    {verificationResult.verificationStatus.replace('_', ' ').toUpperCase()}
                  </dd>
                </div>
                
                <div>
                  <dt className="text-sm font-medium text-gray-500">License Status</dt>
                  <dd className={`mt-1 text-sm font-semibold ${getLicenseStatusColor(verificationResult.licenseStatus)}`}>
                    {verificationResult.licenseStatus.replace('_', ' ').toUpperCase()}
                  </dd>
                </div>
                
                <div>
                  <dt className="text-sm font-medium text-gray-500">Disciplinary Status</dt>
                  <dd className={`mt-1 text-sm ${
                    verificationResult.disciplinaryStatus === DisciplinaryStatus.GOOD_STANDING 
                      ? 'text-success-600 font-semibold' 
                      : 'text-error-600 font-semibold'
                  }`}>
                    {verificationResult.disciplinaryStatus.replace('_', ' ').toUpperCase()}
                  </dd>
                </div>
                
                <div>
                  <dt className="text-sm font-medium text-gray-500">Verified At</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {new Date(verificationResult.verifiedAt).toLocaleString()}
                  </dd>
                </div>

                {verificationResult.expiresAt && (
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-gray-500">Verification Expires</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {new Date(verificationResult.expiresAt).toLocaleString()}
                    </dd>
                  </div>
                )}
              </dl>
            </div>

            {/* Next Steps */}
            {verificationResult.verificationStatus === VerificationStatus.VERIFIED && (
              <div className="bg-success-50 border border-success-200 rounded-lg p-4 mb-6">
                <h4 className="text-sm font-semibold text-success-800 mb-2">
                  What's Next?
                </h4>
                <ul className="text-sm text-success-700 space-y-1">
                  <li>• Access to attorney-specific features and tools</li>
                  <li>• Enhanced privilege protection for client documents</li>
                  <li>• Jurisdiction-specific legal information</li>
                  <li>• Compliance tracking and professional responsibility tools</li>
                </ul>
              </div>
            )}

            {verificationResult.verificationStatus === VerificationStatus.FAILED && (
              <div className="bg-error-50 border border-error-200 rounded-lg p-4 mb-6">
                <h4 className="text-sm font-semibold text-error-800 mb-2">
                  Need Help?
                </h4>
                <div className="text-sm text-error-700 space-y-2">
                  <p>If you believe this is an error:</p>
                  <ul className="list-disc ml-4 space-y-1">
                    <li>Double-check your bar number and jurisdiction</li>
                    <li>Ensure your license is active with the bar association</li>
                    <li>Contact our support team for manual verification</li>
                  </ul>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-3">
              {verificationResult.verificationStatus === VerificationStatus.FAILED && (
                <button
                  onClick={() => setVerificationResult(null)}
                  className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-primary-300 rounded-md text-sm font-medium text-primary-700 bg-white hover:bg-primary-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors duration-200"
                >
                  Try Again
                </button>
              )}
              
              <button
                onClick={() => {
                  if (isFromOnboarding) {
                    router.push('/onboarding/complete');
                  } else {
                    router.push('/dashboard');
                  }
                }}
                className="flex-1 inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors duration-200"
              >
                Continue to Dashboard
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-legal-50 to-primary-50">
      <AttorneyVerificationForm
        onSubmit={handleSubmit}
        onSkip={skipAllowed ? handleSkip : undefined}
        isLoading={isLoading}
        error={error ?? undefined}
      />
    </div>
  );
};

export default AttorneyVerificationPage;