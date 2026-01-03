'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';
import {
  Eye,
  EyeOff,
  Scale,
  User,
  Mail,
  Lock,
  Shield,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  Info,
  HelpCircle
} from 'lucide-react';
import { UserRole } from '@/types/legal-compliance';
import { DisclaimerBanner, TermsAcceptanceModal } from '@/components/compliance';
import { useTermsAcceptance } from '@/hooks';
import {
  buildApiUrl,
  getErrorMessage,
  validateEmail,
  logComplianceEvent,
  logComplianceError,
  DISCLAIMER_TEMPLATES
} from '@/utils/compliance-utils';
import { Alert, AlertDescription } from '@/components/ui';
import axios from 'axios';

// Validation schema
const registrationSchema = z.object({
  firstName: z.string()
    .min(1, 'First name is required')
    .min(2, 'First name must be at least 2 characters')
    .max(50, 'First name must not exceed 50 characters'),
  lastName: z.string()
    .min(1, 'Last name is required')
    .min(2, 'Last name must be at least 2 characters')
    .max(50, 'Last name must not exceed 50 characters'),
  email: z.string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  password: z.string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters')
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/, 
           'Password must contain at least one uppercase letter, lowercase letter, number, and special character'),
  confirmPassword: z.string()
    .min(1, 'Please confirm your password'),
  role: z.nativeEnum(UserRole),
  agreeToTerms: z.boolean().refine((val) => val === true, 'You must agree to the terms and conditions')
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type FormData = z.infer<typeof registrationSchema>;

const RegisterPage = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { documents, acceptTerms } = useTermsAcceptance();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [registrationData, setRegistrationData] = useState<FormData | null>(null);

  // Multi-step registration flow
  const [currentStep, setCurrentStep] = useState<'tier' | 'disclaimer' | 'details'>('tier');
  const [selectedRole, setSelectedRole] = useState<UserRole | null>(null);
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);
  const [disclaimer1Checked, setDisclaimer1Checked] = useState(false);
  const [disclaimer2Checked, setDisclaimer2Checked] = useState(false);

  // Get plan and billing from URL params (from landing page pricing)
  const selectedPlan = searchParams.get('plan');
  const billingPeriod = searchParams.get('billing') || 'monthly';

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid }
  } = useForm<FormData>({
    resolver: zodResolver(registrationSchema),
    mode: 'onChange',
    defaultValues: {
      role: UserRole.ATTORNEY
    }
  });

  // Sync selectedRole with form when it changes
  React.useEffect(() => {
    if (selectedRole) {
      setValue('role', selectedRole);
    }
  }, [selectedRole, setValue]);

  const handleRegistration = async (data: FormData) => {
    setRegistrationData(data);
    setShowTermsModal(true);
  };

  const handleTermsAccept = async (documentIds: string[]) => {
    if (!registrationData) return;

    setIsLoading(true);
    setError(null);

    try {
      // Terms accepted via checkbox - no need for API call during registration
      // The terms acceptance is tracked in the registration data itself
      logComplianceEvent('Terms accepted via registration form', { documentIds });

      logComplianceEvent('Starting user registration', {
        email: registrationData.email,
        role: registrationData.role
      });

      // Register user
      const response = await axios.post(buildApiUrl('/api/v1/auth/register'), {
        firstName: registrationData.firstName,
        lastName: registrationData.lastName,
        email: registrationData.email,
        password: registrationData.password,
        role: registrationData.role,
        termsAccepted: true,
        acceptedDocuments: documentIds
      });

      // Backend returns: { access_token, refresh_token, token_type, expires_in, user }
      if (response.data && response.data.user) {
        logComplianceEvent('User registration successful', {
          userId: response.data.user.id,
          email: registrationData.email
        });

        // Store tokens
        if (response.data.access_token) {
          localStorage.setItem('accessToken', response.data.access_token);
        }
        if (response.data.refresh_token) {
          localStorage.setItem('refreshToken', response.data.refresh_token);
        }

        // Check if a paid plan was selected from landing page
        if (selectedPlan && selectedPlan !== 'free') {
          // Create Stripe Checkout session and redirect
          try {
            const checkoutResponse = await axios.post(
              buildApiUrl('/api/v1/billing/create-checkout-session'),
              {
                plan: selectedPlan,
                billing_period: billingPeriod,
              },
              {
                headers: {
                  Authorization: `Bearer ${response.data.access_token}`,
                },
              }
            );

            if (checkoutResponse.data?.checkout_url) {
              // Redirect to Stripe Checkout
              window.location.href = checkoutResponse.data.checkout_url;
              return;
            }
          } catch (checkoutError) {
            console.error('Failed to create checkout session:', checkoutError);
            // Fall through to normal redirect if checkout fails
            // User can subscribe later from dashboard
          }
        }

        // Redirect to verification page if attorney
        if (registrationData.role === UserRole.ATTORNEY) {
          router.push('/auth/verify-attorney?from=registration');
        } else {
          router.push('/auth/login?message=Registration successful, please sign in');
        }
      } else {
        throw new Error('Registration failed - invalid response from server');
      }
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('User registration failed', err);
    } finally {
      setIsLoading(false);
      setShowTermsModal(false);
    }
  };

  const handleTermsDecline = () => {
    setShowTermsModal(false);
    setError('You must accept the terms and conditions to create an account.');
  };

  // Handle tier/role selection (Step 1)
  const handleTierSelect = (role: UserRole) => {
    setSelectedRole(role);
    setCurrentStep('disclaimer');
  };

  // Handle disclaimer acceptance (Step 2)
  const handleDisclaimerAccept = () => {
    if (disclaimer1Checked && disclaimer2Checked) {
      setDisclaimerAccepted(true);
      // Store disclaimer acceptance in localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('disclaimerAccepted', 'true');
        localStorage.setItem('disclaimerAcceptedDate', new Date().toISOString());
        localStorage.setItem('userType', selectedRole || 'user');
      }
      setCurrentStep('details');
    }
  };

  // Handle back to tier selection
  const handleBackToTier = () => {
    setCurrentStep('tier');
    setDisclaimer1Checked(false);
    setDisclaimer2Checked(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-navy-50 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-navy-600 rounded-full flex items-center justify-center mb-4">
            <Scale className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-navy-800">
            Create Your Account
          </h2>
          <p className="mt-2 text-sm text-gray-600">
            {currentStep === 'tier' && 'Step 1: Choose your account type'}
            {currentStep === 'disclaimer' && 'Step 2: Review legal disclaimers'}
            {currentStep === 'details' && 'Step 3: Complete your registration'}
          </p>
          {/* Show selected plan from pricing page */}
          {selectedPlan && selectedPlan !== 'free' && (
            <div className="mt-3 inline-flex items-center gap-2 bg-teal-50 border border-teal-200 text-teal-800 px-4 py-2 rounded-full text-sm">
              <CheckCircle className="h-4 w-4" />
              <span>
                <strong>{selectedPlan.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</strong> plan selected
                {billingPeriod === 'annual' && ' (Annual)'}
              </span>
            </div>
          )}
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-center gap-2">
          <div className={`w-3 h-3 rounded-full ${currentStep === 'tier' ? 'bg-teal-600' : 'bg-teal-300'}`} />
          <div className={`w-8 h-1 ${currentStep !== 'tier' ? 'bg-teal-600' : 'bg-gray-300'}`} />
          <div className={`w-3 h-3 rounded-full ${currentStep === 'disclaimer' ? 'bg-teal-600' : currentStep === 'details' ? 'bg-teal-300' : 'bg-gray-300'}`} />
          <div className={`w-8 h-1 ${currentStep === 'details' ? 'bg-teal-600' : 'bg-gray-300'}`} />
          <div className={`w-3 h-3 rounded-full ${currentStep === 'details' ? 'bg-teal-600' : 'bg-gray-300'}`} />
        </div>

        {/* STEP 1: Tier/Role Selection */}
        {currentStep === 'tier' && (
          <div className="bg-white py-8 px-6 shadow-legal rounded-lg border border-gray-200">
            <h3 className="text-lg font-semibold text-navy-800 mb-4">Select Your Account Type</h3>
            <p className="text-sm text-gray-600 mb-6">
              Choose the account type that best describes your role. This determines your access level and available features.
            </p>
            <div className="space-y-3">
              {/* Attorney Option */}
              <button
                type="button"
                onClick={() => handleTierSelect(UserRole.ATTORNEY)}
                className="w-full flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all border-gray-200 hover:border-teal-500 hover:bg-teal-50 text-left"
              >
                <Shield className="h-6 w-6 text-teal-600 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <span className="font-medium text-gray-900 block">Attorney</span>
                  <p className="text-xs text-gray-500 mt-1">
                    Full access to all features including case management, legal research, and client portal. Requires bar verification.
                  </p>
                </div>
              </button>

              {/* Paralegal Option */}
              <button
                type="button"
                onClick={() => handleTierSelect(UserRole.PARALEGAL)}
                className="w-full flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all border-gray-200 hover:border-teal-500 hover:bg-teal-50 text-left"
              >
                <User className="h-6 w-6 text-teal-600 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <span className="font-medium text-gray-900 block">Paralegal</span>
                  <p className="text-xs text-gray-500 mt-1">
                    Access to document analysis, research tools, and case support features under attorney supervision.
                  </p>
                </div>
              </button>

              {/* Pro Se Litigant Option */}
              <button
                type="button"
                onClick={() => handleTierSelect(UserRole.PRO_SE)}
                className="w-full flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all border-gray-200 hover:border-teal-500 hover:bg-teal-50 text-left"
              >
                <Scale className="h-6 w-6 text-teal-600 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <span className="font-medium text-gray-900 block">Pro Se Litigant</span>
                  <p className="text-xs text-gray-500 mt-1">
                    Self-represented individual. Access to educational resources, document templates, and basic legal research.
                  </p>
                </div>
              </button>

              {/* Client Option */}
              <button
                type="button"
                onClick={() => handleTierSelect(UserRole.CLIENT)}
                className="w-full flex items-start p-4 border-2 rounded-lg cursor-pointer transition-all border-gray-200 hover:border-teal-500 hover:bg-teal-50 text-left"
              >
                <User className="h-6 w-6 text-teal-600 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <span className="font-medium text-gray-900 block">Client</span>
                  <p className="text-xs text-gray-500 mt-1">
                    Client portal access to view case updates, share documents, and communicate with your attorney.
                  </p>
                </div>
              </button>
            </div>

            {/* Sign In Link */}
            <div className="text-center text-sm mt-6">
              <span className="text-gray-600">Already have an account? </span>
              <Link href="/auth/login" className="text-teal-600 hover:text-teal-700 font-medium">
                Sign in here
              </Link>
            </div>
          </div>
        )}

        {/* STEP 2: Legal Disclaimer */}
        {currentStep === 'disclaimer' && (
          <div className="bg-white py-8 px-6 shadow-legal rounded-lg border border-gray-200">
            <div className="text-center mb-6">
              <AlertTriangle className="h-12 w-12 text-amber-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-navy-800">Legal Disclaimers</h3>
              <p className="text-sm text-gray-600 mt-1">
                Please review and accept the following disclaimers to continue
              </p>
            </div>

            {/* Pro Se Warning */}
            {selectedRole === UserRole.PRO_SE && (
              <Alert className="mb-4 border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800">
                  <strong>Warning for Self-Represented Individuals:</strong> Representing yourself in legal matters carries significant risks. This system cannot substitute for legal representation. Strongly consider consulting with an attorney.
                </AlertDescription>
              </Alert>
            )}

            <div className="space-y-4 mb-6">
              <label className="flex items-start space-x-3 cursor-pointer p-3 border rounded-lg hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={disclaimer1Checked}
                  onChange={(e) => setDisclaimer1Checked(e.target.checked)}
                  className="mt-1 h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  <strong>I understand this system provides legal information, not legal advice.</strong> I acknowledge that no attorney-client relationship is created through use of this system and that all information is for educational purposes only.
                </span>
              </label>

              <label className="flex items-start space-x-3 cursor-pointer p-3 border rounded-lg hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={disclaimer2Checked}
                  onChange={(e) => setDisclaimer2Checked(e.target.checked)}
                  className="mt-1 h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  <strong>I acknowledge I should consult an attorney for case-specific guidance.</strong> I understand that laws vary by jurisdiction and that I should verify all information with qualified legal counsel before making any legal decisions.
                </span>
              </label>
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleBackToTier}
                className="flex-1 py-2 px-4 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Back
              </button>
              <button
                type="button"
                onClick={handleDisclaimerAccept}
                disabled={!disclaimer1Checked || !disclaimer2Checked}
                className={`flex-1 py-2 px-4 rounded-md text-white transition-colors ${
                  disclaimer1Checked && disclaimer2Checked
                    ? 'bg-teal-600 hover:bg-teal-700'
                    : 'bg-gray-400 cursor-not-allowed'
                }`}
              >
                Accept & Continue
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Registration Details Form */}
        {currentStep === 'details' && (
        <div className="bg-white py-8 px-6 shadow-legal rounded-lg border border-gray-200">
          <form className="space-y-6" onSubmit={handleSubmit(handleRegistration)}>

            {/* Selected Account Type Display */}
            <div className="bg-teal-50 border border-teal-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-teal-800">
                <strong>Account Type:</strong> {selectedRole === UserRole.ATTORNEY ? 'Attorney' : selectedRole === UserRole.PARALEGAL ? 'Paralegal' : selectedRole === UserRole.PRO_SE ? 'Pro Se Litigant' : 'Client'}
                <button
                  type="button"
                  onClick={() => setCurrentStep('tier')}
                  className="ml-2 text-teal-600 underline hover:text-teal-700"
                >
                  Change
                </button>
              </p>
            </div>

            {/* First Name & Last Name */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 mb-1">
                  First Name *
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    id="firstName"
                    type="text"
                    {...register('firstName')}
                    className={`
                      pl-10 appearance-none rounded-md relative block w-full px-3 py-2 border
                      placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2
                      focus:ring-teal-500 focus:border-teal-500 sm:text-sm
                      ${errors.firstName ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                    `}
                    placeholder="First name"
                  />
                </div>
                {errors.firstName && (
                  <p className="mt-1 text-xs text-red-600" role="alert">
                    {errors.firstName.message}
                  </p>
                )}
              </div>

              <div>
                <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 mb-1">
                  Last Name *
                </label>
                <input
                  id="lastName"
                  type="text"
                  {...register('lastName')}
                  className={`
                    appearance-none rounded-md relative block w-full px-3 py-2 border
                    placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2
                    focus:ring-teal-500 focus:border-teal-500 sm:text-sm
                    ${errors.lastName ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                  `}
                  placeholder="Last name"
                />
                {errors.lastName && (
                  <p className="mt-1 text-xs text-red-600" role="alert">
                    {errors.lastName.message}
                  </p>
                )}
              </div>
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address *
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  id="email"
                  type="email"
                  {...register('email')}
                  className={`
                    pl-10 appearance-none rounded-md relative block w-full px-3 py-2 border
                    placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2
                    focus:ring-teal-500 focus:border-teal-500 sm:text-sm
                    ${errors.email ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                  `}
                  placeholder="Enter your email address"
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-sm text-red-600" role="alert">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password *
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  {...register('password')}
                  className={`
                    pl-10 pr-10 appearance-none rounded-md relative block w-full px-3 py-2 border 
                    placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 
                    focus:ring-teal-500 focus:border-teal-500 sm:text-sm
                    ${errors.password ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                  `}
                  placeholder="Create a strong password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center z-10 hover:opacity-70 transition-opacity"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <Eye className="h-5 w-5 text-gray-500 hover:text-gray-700" />
                  ) : (
                    <EyeOff className="h-5 w-5 text-gray-500 hover:text-gray-700" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="mt-1 text-xs text-red-600" role="alert">
                  {errors.password.message}
                </p>
              )}

              {/* Password Requirements Indicator */}
              <div className="mt-3 p-3 bg-gray-50 rounded-md border border-gray-200">
                <p className="text-xs font-medium text-gray-700 mb-2">Password Requirements:</p>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {watch('password')?.length >= 8 ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-gray-400" />
                    )}
                    <span className={`text-xs ${watch('password')?.length >= 8 ? 'text-green-700' : 'text-gray-500'}`}>
                      At least 8 characters
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {/[A-Z]/.test(watch('password') || '') ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-gray-400" />
                    )}
                    <span className={`text-xs ${/[A-Z]/.test(watch('password') || '') ? 'text-green-700' : 'text-gray-500'}`}>
                      Contains uppercase letter (A-Z)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {/[a-z]/.test(watch('password') || '') ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-gray-400" />
                    )}
                    <span className={`text-xs ${/[a-z]/.test(watch('password') || '') ? 'text-green-700' : 'text-gray-500'}`}>
                      Contains lowercase letter (a-z)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {/\d/.test(watch('password') || '') ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-gray-400" />
                    )}
                    <span className={`text-xs ${/\d/.test(watch('password') || '') ? 'text-green-700' : 'text-gray-500'}`}>
                      Contains number (0-9)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {/[@$!%*?&]/.test(watch('password') || '') ? (
                      <CheckCircle className="h-3 w-3 text-green-600" />
                    ) : (
                      <XCircle className="h-3 w-3 text-gray-400" />
                    )}
                    <span className={`text-xs ${/[@$!%*?&]/.test(watch('password') || '') ? 'text-green-700' : 'text-gray-500'}`}>
                      Contains special character (@$!%*?&)
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                Confirm Password *
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-4 w-4 text-gray-400" />
                </div>
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  {...register('confirmPassword')}
                  className={`
                    pl-10 pr-10 appearance-none rounded-md relative block w-full px-3 py-2 border 
                    placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 
                    focus:ring-teal-500 focus:border-teal-500 sm:text-sm
                    ${errors.confirmPassword ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                  `}
                  placeholder="Confirm your password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center z-10 hover:opacity-70 transition-opacity"
                  tabIndex={-1}
                >
                  {showConfirmPassword ? (
                    <Eye className="h-5 w-5 text-gray-500 hover:text-gray-700" />
                  ) : (
                    <EyeOff className="h-5 w-5 text-gray-500 hover:text-gray-700" />
                  )}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-xs text-red-600" role="alert">
                  {errors.confirmPassword.message}
                </p>
              )}
            </div>

            {/* Terms Agreement */}
            <div>
              <label className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  {...register('agreeToTerms')}
                  className="mt-1 h-4 w-4 text-teal-600 focus:ring-teal-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  I agree to the{' '}
                  <Link href="/terms" className="text-teal-600 hover:text-teal-700 underline">
                    Terms of Service
                  </Link>
                  ,{' '}
                  <Link href="/privacy" className="text-teal-600 hover:text-teal-700 underline">
                    Privacy Policy
                  </Link>
                  , and{' '}
                  <Link href="/acceptable-use" className="text-teal-600 hover:text-teal-700 underline">
                    Acceptable Use Policy
                  </Link>
                  *
                </span>
              </label>
              {errors.agreeToTerms && (
                <p className="mt-1 text-sm text-red-600" role="alert">
                  {errors.agreeToTerms.message}
                </p>
              )}
            </div>

            {/* Role-specific disclaimer */}
            {selectedRole === UserRole.ATTORNEY && (
              <DisclaimerBanner
                disclaimer={{
                  id: 'attorney-registration',
                  type: 'professional_responsibility' as any,
                  title: 'Attorney Professional Responsibility',
                  content: 'As a licensed attorney, you are responsible for compliance with all applicable professional conduct rules. Use of this system does not alter your professional obligations.',
                  displayFormat: 'inline_text' as any,
                  isRequired: false,
                  showForRoles: [UserRole.ATTORNEY],
                  context: ['registration'],
                  priority: 1,
                  isActive: true,
                  requiresAcknowledgment: false,
                  dismissible: false
                }}
              />
            )}

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <div className="flex">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Registration Failed
                    </h3>
                    <div className="mt-1 text-sm text-red-700">
                      {error}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <div>
              <button
                type="submit"
                disabled={!isValid || isLoading}
                className={`
                  group relative w-full flex justify-center py-3 px-4 border border-transparent 
                  text-sm font-medium rounded-md text-white focus:outline-none focus:ring-2 
                  focus:ring-offset-2 focus:ring-teal-500 transition-colors duration-200
                  ${isValid && !isLoading 
                    ? 'bg-teal-600 hover:bg-teal-700' 
                    : 'bg-gray-400 cursor-not-allowed'
                  }
                `}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="animate-spin h-4 w-4 mr-2" />
                    Creating Account...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Create Account
                  </>
                )}
              </button>
            </div>

            {/* Sign In Link */}
            <div className="text-center text-sm">
              <span className="text-gray-600">Already have an account? </span>
              <Link 
                href="/auth/login" 
                className="text-teal-600 hover:text-teal-700 font-medium"
              >
                Sign in here
              </Link>
            </div>
          </form>
        </div>
        )}

        {/* Terms Acceptance Modal */}
        <TermsAcceptanceModal
          isOpen={showTermsModal}
          documents={documents}
          onAccept={handleTermsAccept}
          onDecline={handleTermsDecline}
          isForced={true}
        />
      </div>
    </div>
  );
};

export default RegisterPage;