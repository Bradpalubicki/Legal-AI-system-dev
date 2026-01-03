'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw, Bug } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  /** Optional name to identify which boundary caught the error */
  boundaryName?: string;
  /** Optional callback when error occurs */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** Whether to show reset button */
  showReset?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

/**
 * ErrorBoundary Component
 *
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 *
 * Features:
 * - Automatic Sentry error reporting (if configured)
 * - Development vs Production UI differences
 * - Error ID generation for support tracking
 * - Optional custom fallback UI
 * - Reset functionality to recover from errors
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary boundaryName="MainApp">
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
    errorId: null
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    // Generate unique error ID
    const errorId = `err_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    return {
      hasError: true,
      error,
      errorInfo: null,
      errorId
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    const { boundaryName, onError } = this.props;
    const { errorId } = this.state;

    // Log to console in all environments
    console.group(`🔴 Error Boundary: ${boundaryName || 'Unknown'}`);
    console.error('Error:', error);
    console.error('Error Info:', errorInfo);
    console.error('Error ID:', errorId);
    console.groupEnd();

    // Log to error tracking service (Sentry)
    this.logErrorToSentry(error, errorInfo, boundaryName, errorId);

    // Call custom error handler if provided
    if (onError) {
      try {
        onError(error, errorInfo);
      } catch (handlerError) {
        console.error('Error handler threw an error:', handlerError);
      }
    }

    this.setState({
      error,
      errorInfo
    });
  }

  private logErrorToSentry(
    error: Error,
    errorInfo: ErrorInfo,
    boundaryName?: string,
    errorId?: string | null
  ) {
    // Only in browser environment
    if (typeof window === 'undefined') return;

    try {
      // Check if Sentry is available
      // @ts-ignore - Sentry may not be defined
      if (window.Sentry && typeof window.Sentry.captureException === 'function') {
        // @ts-ignore
        window.Sentry.captureException(error, {
          contexts: {
            react: {
              componentStack: errorInfo.componentStack,
              boundaryName: boundaryName || 'Unknown'
            }
          },
          tags: {
            errorBoundary: boundaryName || 'Unknown',
            errorId: errorId || 'unknown'
          },
          level: 'error'
        });

        console.log('✅ Error logged to Sentry');
      } else {
        console.warn('⚠️ Sentry not available - error not tracked remotely');
      }
    } catch (sentryError) {
      console.error('Failed to log error to Sentry:', sentryError);
    }
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    const { showReset = true } = this.props;

    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>

            <h2 className="text-xl font-bold text-gray-900 text-center mb-2">
              Something went wrong
            </h2>

            <p className="text-gray-600 text-center mb-6">
              We're sorry, but something unexpected happened. Please try refreshing the page or contact support if the problem persists.
            </p>

            {/* Show error details in development */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="mb-6 p-4 bg-gray-100 rounded-lg overflow-auto max-h-64">
                <div className="flex items-center gap-2 mb-2">
                  <Bug className="w-4 h-4 text-gray-700" />
                  <p className="text-sm font-semibold text-gray-900">Development Error Details:</p>
                </div>
                <pre className="text-xs text-red-600 whitespace-pre-wrap break-words mb-3">
                  {this.state.error.toString()}
                </pre>
                {this.state.errorInfo && (
                  <details className="mt-2">
                    <summary className="text-xs font-semibold text-gray-700 cursor-pointer hover:text-gray-900">
                      Component Stack Trace
                    </summary>
                    <pre className="text-xs text-gray-600 whitespace-pre-wrap break-words mt-2 p-2 bg-white rounded">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </details>
                )}
                {this.props.boundaryName && (
                  <p className="text-xs text-gray-600 mt-2">
                    Boundary: <code className="bg-white px-1 py-0.5 rounded">{this.props.boundaryName}</code>
                  </p>
                )}
              </div>
            )}

            <div className="flex gap-3">
              {showReset && (
                <button
                  onClick={this.handleReset}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
                  aria-label="Try again"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>
              )}
              <button
                onClick={() => window.location.href = '/'}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                aria-label="Go to home page"
              >
                Go Home
              </button>
            </div>

            {/* Error ID for support */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-500 text-center">
                Error ID: <code className="font-mono text-gray-700">{this.state.errorId || 'unknown'}</code>
              </p>
              <p className="text-xs text-gray-400 text-center mt-1">
                Please provide this ID when contacting support
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// HOC version for easier use
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode
) {
  return function WithErrorBoundary(props: P) {
    return (
      <ErrorBoundary fallback={fallback}>
        <Component {...props} />
      </ErrorBoundary>
    );
  };
}
