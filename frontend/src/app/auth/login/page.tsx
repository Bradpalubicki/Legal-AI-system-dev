'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';
import { 
  Eye, 
  EyeOff, 
  Scale, 
  Shield, 
  AlertTriangle,
  Loader2,
  CheckCircle
} from 'lucide-react';
import { useAuth, useCompliance } from '@/hooks';
import { LoginRequest } from '@/types/legal-compliance';
import { DisclaimerBanner, LegalWarningModal } from '@/components/compliance';
import { DISCLAIMER_TEMPLATES } from '@/utils/compliance-utils';
// NewFilingModal is now shown on the home page, not the login page

// Validation schema
const loginSchema = z.object({
  email: z.string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  password: z.string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters')
});

type FormData = z.infer<typeof loginSchema>;

// Map backend errors to user-friendly messages
const getErrorMessage = (error: string | null): { title: string; message: string; suggestion?: string } => {
  if (!error) return { title: '', message: '' };

  const errorLower = error.toLowerCase();

  if (errorLower.includes('invalid credentials') || errorLower.includes('incorrect password') || errorLower.includes('wrong password')) {
    return {
      title: 'Incorrect Password',
      message: 'The password you entered is incorrect.',
      suggestion: 'Please check your password and try again, or use "Forgot password" to reset it.'
    };
  }

  if (errorLower.includes('user not found') || errorLower.includes('no user') || errorLower.includes('email not found')) {
    return {
      title: 'Account Not Found',
      message: 'No account exists with this email address.',
      suggestion: 'Please check your email or create a new account.'
    };
  }

  if (errorLower.includes('account locked') || errorLower.includes('too many attempts') || errorLower.includes('locked out')) {
    return {
      title: 'Account Temporarily Locked',
      message: 'Your account has been temporarily locked due to multiple failed login attempts.',
      suggestion: 'Please wait 15 minutes and try again, or contact support.'
    };
  }

  if (errorLower.includes('account disabled') || errorLower.includes('account deactivated')) {
    return {
      title: 'Account Disabled',
      message: 'Your account has been disabled.',
      suggestion: 'Please contact support for assistance.'
    };
  }

  if (errorLower.includes('mfa') || errorLower.includes('two-factor') || errorLower.includes('2fa')) {
    return {
      title: 'Verification Required',
      message: 'Two-factor authentication is required for this account.',
      suggestion: 'Please enter your authenticator code below.'
    };
  }

  if (errorLower.includes('network') || errorLower.includes('connection') || errorLower.includes('timeout')) {
    return {
      title: 'Connection Error',
      message: 'Unable to connect to the server.',
      suggestion: 'Please check your internet connection and try again.'
    };
  }

  // Default fallback
  return {
    title: 'Authentication Failed',
    message: error,
    suggestion: 'Please try again or contact support if the problem persists.'
  };
};

const LoginPage = () => {
  const router = useRouter();
  const { login, isLoading, error: authError } = useAuth();
  const { checkCompliance } = useCompliance();

  const [showPassword, setShowPassword] = useState(false);
  const [showLegalWarning, setShowLegalWarning] = useState(false);
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaToken, setMfaToken] = useState('');
  const [pendingFormData, setPendingFormData] = useState<FormData | null>(null);

  // Get user-friendly error message
  const errorInfo = getErrorMessage(authError);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid }
  } = useForm<FormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onChange'
  });

  const handleLogin = async (data: FormData) => {
    try {
      setPendingFormData(data);
      setShowLegalWarning(true);
    } catch (err) {
      // Error handling is done in useAuth hook
    }
  };

  const handleLegalWarningAccept = async () => {
    setShowLegalWarning(false);

    if (!pendingFormData) return;

    try {
      const loginRequest: LoginRequest = {
        email: pendingFormData.email,
        password: pendingFormData.password,
        mfaToken: mfaRequired ? mfaToken : undefined
      };

      // Login now returns response data including new_filings
      const loginResponse = await login(loginRequest);

      // Check compliance after successful login (non-blocking)
      try {
        await checkCompliance();
      } catch (complianceErr) {
        // Log but don't block login - compliance check is optional
        console.warn('Compliance check failed:', complianceErr);
      }

      // Check for new filings in the login response (no separate API call needed!)
      // The backend now returns new_filings directly in the login response
      console.log('[LOGIN DEBUG] Login response new_filings:', loginResponse?.new_filings);

      if (loginResponse?.new_filings?.has_new_filings &&
          loginResponse.new_filings.cases &&
          loginResponse.new_filings.cases.length > 0) {
        // Store filings data in sessionStorage for the home page to display
        try {
          sessionStorage.setItem('newFilingsData', JSON.stringify({
            cases: loginResponse.new_filings.cases,
            totalDocs: loginResponse.new_filings.total_new_documents || 0,
            since: loginResponse.new_filings.since
          }));
          console.log('[LOGIN DEBUG] Stored new filings data in sessionStorage');
        } catch (storageErr) {
          // SessionStorage might be full or disabled - log but don't block login
          console.warn('[LOGIN] Failed to store new filings data:', storageErr);
        }
      }

      // Redirect to main application
      router.push('/');
    } catch (err: any) {
      if (err.message?.includes('MFA')) {
        setMfaRequired(true);
      }
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-navy-50 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mx-auto h-16 w-16 bg-navy-600 dark:bg-slate-700 rounded-full flex items-center justify-center mb-4">
            <Scale className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-navy-800 dark:text-slate-100">
            Legal AI System
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-slate-400">
            Sign in to your account to access AI-powered legal tools
          </p>
        </div>

        {/* Legal Disclaimer */}
        <DisclaimerBanner
          disclaimer={{
            id: 'login-no-legal-advice',
            type: 'no_legal_advice' as any,
            title: DISCLAIMER_TEMPLATES.no_legal_advice.title,
            content: DISCLAIMER_TEMPLATES.no_legal_advice.content,
            displayFormat: 'inline_text' as any,
            isRequired: false,
            showForRoles: [],
            context: ['login'],
            priority: 1,
            isActive: true,
            requiresAcknowledgment: false,
            dismissible: true
          }}
          className="mb-6"
        />

        {/* Login Form */}
        <div className="bg-white dark:bg-slate-800 py-8 px-6 shadow-legal rounded-lg border border-gray-200 dark:border-slate-700">
          <form className="space-y-6" onSubmit={handleSubmit(handleLogin)}>
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                {...register('email')}
                className={`
                  appearance-none rounded-md relative block w-full px-3 py-2 border
                  placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2
                  focus:ring-teal-500 focus:border-teal-500 focus:z-10 sm:text-sm
                  ${errors.email ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                `}
                placeholder="Enter your email address"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600" role="alert">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  {...register('password')}
                  className={`
                    appearance-none rounded-md relative block w-full px-3 py-2 pr-10 border
                    placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2
                    focus:ring-teal-500 focus:border-teal-500 sm:text-sm
                    ${errors.password ? 'border-red-300 bg-red-50' : 'border-gray-300'}
                  `}
                  placeholder="Enter your password"
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
                <p className="mt-1 text-sm text-red-600" role="alert">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* MFA Token (if required) */}
            {mfaRequired && (
              <div>
                <label htmlFor="mfaToken" className="block text-sm font-medium text-gray-700 mb-2">
                  Two-Factor Authentication Code
                </label>
                <input
                  id="mfaToken"
                  type="text"
                  value={mfaToken}
                  onChange={(e) => setMfaToken(e.target.value)}
                  className="appearance-none rounded-md relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 focus:z-10 sm:text-sm"
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Enter the code from your authenticator app
                </p>
              </div>
            )}

            {/* Error Display */}
            {authError && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <div className="flex">
                  <AlertTriangle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      {errorInfo.title}
                    </h3>
                    <div className="mt-1 text-sm text-red-700">
                      {errorInfo.message}
                    </div>
                    {errorInfo.suggestion && (
                      <p className="mt-2 text-xs text-red-600">
                        {errorInfo.suggestion}
                      </p>
                    )}
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
                    Signing In...
                  </>
                ) : (
                  <>
                    <Shield className="h-4 w-4 mr-2" />
                    Sign In
                  </>
                )}
              </button>
            </div>

            {/* Links */}
            <div className="flex items-center justify-between text-sm">
              <Link
                href="/auth/forgot-password"
                className="text-teal-600 hover:text-teal-700 font-medium"
              >
                Forgot your password?
              </Link>
              <Link
                href="/auth/register"
                className="text-teal-600 hover:text-teal-700 font-medium"
              >
                Create account
              </Link>
            </div>
          </form>
        </div>

        {/* Security Notice */}
        <div className="bg-navy-50 dark:bg-slate-800 border border-navy-200 dark:border-slate-700 rounded-lg p-4">
          <div className="flex items-start">
            <Shield className="h-5 w-5 text-navy-600 dark:text-teal-400 mt-0.5 mr-3" />
            <div>
              <h4 className="text-sm font-semibold text-navy-800 dark:text-slate-100">
                Security & Privacy Notice
              </h4>
              <p className="mt-1 text-sm text-navy-700 dark:text-slate-400">
                This system implements enterprise-grade security measures including encryption,
                audit trails, and compliance monitoring. Your data is protected according to
                legal industry standards.
              </p>
            </div>
          </div>
        </div>

        {/* Legal Warning Modal */}
        <LegalWarningModal
          isOpen={showLegalWarning}
          onClose={() => setShowLegalWarning(false)}
          onAccept={handleLegalWarningAccept}
          title="System Access Agreement"
          content={`
            <p>By accessing this Legal AI System, you acknowledge and agree that:</p>
            <ul class="list-disc ml-6 mt-2 space-y-1">
              <li>This system provides legal information, not legal advice</li>
              <li>No attorney-client relationship is created through system use</li>
              <li>All AI-generated content requires professional review</li>
              <li>You are responsible for compliance with professional conduct rules</li>
              <li>System usage is monitored for compliance and security purposes</li>
            </ul>
            <p class="mt-3">Continued use indicates acceptance of all terms and conditions.</p>
          `}
          acceptButtonText="I Understand and Accept"
          severity="warning"
        />
      </div>
    </div>
  );
};

export default LoginPage;