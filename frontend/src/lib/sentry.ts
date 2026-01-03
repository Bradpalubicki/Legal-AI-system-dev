/**
 * Sentry Frontend Error Tracking Initialization
 *
 * Configures Sentry for React/Next.js error tracking and performance monitoring.
 * Only enabled in production or when explicitly configured.
 *
 * Features:
 * - Automatic React error boundary integration
 * - Performance monitoring (Core Web Vitals)
 * - Session replay for debugging
 * - User feedback integration
 * - Privacy-first data filtering
 */

// Only import Sentry in production or when explicitly enabled
const SENTRY_ENABLED = process.env.NEXT_PUBLIC_SENTRY_ENABLED === 'true';
const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;
const ENVIRONMENT = process.env.NEXT_PUBLIC_ENVIRONMENT || process.env.NODE_ENV || 'development';

/**
 * Initialize Sentry error tracking
 *
 * Call this function early in your application lifecycle.
 * For Next.js, call in _app.tsx or layout.tsx
 */
export function initSentry() {
  // Only initialize if enabled and DSN is provided
  if (!SENTRY_ENABLED || !SENTRY_DSN) {
    console.log('[Sentry] Disabled - Set NEXT_PUBLIC_SENTRY_ENABLED=true to enable');
    return;
  }

  // Dynamic import to avoid bundling Sentry in development
  import('@sentry/react')
    .then((Sentry) => {
      Sentry.init({
        dsn: SENTRY_DSN,
        environment: ENVIRONMENT,

        // Performance Monitoring
        integrations: [
          // Browser tracing for performance monitoring
          new Sentry.BrowserTracing({
            // Trace all route changes
            tracePropagationTargets: [
              'localhost',
              /^https:\/\/yourproductiondomain\.com/,
            ],
          }),

          // Replay integration for session recording
          new Sentry.Replay({
            // Privacy settings for session replay
            maskAllText: true, // Mask all text by default (legal data protection)
            blockAllMedia: true, // Block all media elements
            maskAllInputs: true, // Mask all input fields
          }),
        ],

        // Performance monitoring sample rate
        // 10% of transactions = good balance between cost and insights
        tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 0.0,

        // Session replay sample rate
        // Only capture replays for errors
        replaysSessionSampleRate: 0.0, // Don't record successful sessions
        replaysOnErrorSampleRate: 1.0, // Always record sessions with errors

        // Privacy & Security
        beforeSend(event, hint) {
          // Filter sensitive data before sending to Sentry
          return filterSensitiveData(event, hint);
        },

        // Ignore specific errors
        ignoreErrors: [
          // Browser extensions
          'top.GLOBALS',
          'canvas.contentDocument',
          'MyApp_RemoveAllHighlights',
          'atomicFindClose',

          // Network errors (expected in flaky connections)
          'NetworkError',
          'Network request failed',
          'Failed to fetch',

          // React hydration errors (expected in some Next.js scenarios)
          'Hydration failed',
          'There was an error while hydrating',

          // User aborted operations (not actual errors)
          'AbortError',
          'The operation was aborted',
        ],

        // Release tracking
        release: process.env.NEXT_PUBLIC_APP_VERSION || 'legal-ai-system@1.0.0',

        // Enable debug mode in development
        debug: ENVIRONMENT === 'development',
      });

      console.log(`[Sentry] Initialized for ${ENVIRONMENT}`);

      // Make Sentry available globally for ErrorBoundary
      if (typeof window !== 'undefined') {
        (window as any).Sentry = Sentry;
      }
    })
    .catch((error) => {
      console.error('[Sentry] Failed to initialize:', error);
    });
}

/**
 * Filter sensitive data from Sentry events
 *
 * Critical for legal applications - never send PII or sensitive data
 */
function filterSensitiveData(event: any, hint: any) {
  // Remove sensitive headers
  if (event.request && event.request.headers) {
    const sensitiveHeaders = [
      'authorization',
      'cookie',
      'x-api-key',
      'x-auth-token',
      'x-csrf-token',
    ];

    for (const header of sensitiveHeaders) {
      delete event.request.headers[header];
      delete event.request.headers[header.toUpperCase()];
    }
  }

  // Remove sensitive form data
  if (event.request && event.request.data) {
    const sensitiveFields = [
      'password',
      'token',
      'secret',
      'api_key',
      'ssn',
      'social_security',
      'credit_card',
      'cvv',
      'pin',
      'tax_id',
      'drivers_license',
    ];

    for (const field of sensitiveFields) {
      if (event.request.data[field]) {
        event.request.data[field] = '[FILTERED]';
      }
    }
  }

  // Filter sensitive data from exception messages
  if (event.exception && event.exception.values) {
    for (const exception of event.exception.values) {
      if (exception.value) {
        // Remove potential API keys, tokens, etc. from error messages
        exception.value = exception.value
          .replace(/sk-[a-zA-Z0-9]{32,}/g, '[API_KEY_FILTERED]')
          .replace(/Bearer [a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+/g, '[JWT_FILTERED]')
          .replace(/api[_-]?key[=:]\s*[a-zA-Z0-9_-]+/gi, 'api_key=[FILTERED]')
          .replace(/token[=:]\s*[a-zA-Z0-9_-]+/gi, 'token=[FILTERED]');
      }
    }
  }

  // Filter breadcrumbs (user activity trail)
  if (event.breadcrumbs) {
    event.breadcrumbs = event.breadcrumbs.map((breadcrumb: any) => {
      // Remove sensitive data from breadcrumb messages
      if (breadcrumb.message) {
        breadcrumb.message = breadcrumb.message
          .replace(/password=.+/gi, 'password=[FILTERED]')
          .replace(/token=.+/gi, 'token=[FILTERED]');
      }

      // Remove sensitive data from breadcrumb data
      if (breadcrumb.data) {
        const sensitiveKeys = ['password', 'token', 'api_key', 'secret'];
        for (const key of sensitiveKeys) {
          if (breadcrumb.data[key]) {
            breadcrumb.data[key] = '[FILTERED]';
          }
        }
      }

      return breadcrumb;
    });
  }

  return event;
}

/**
 * Set user context for Sentry
 *
 * Call this when user logs in to track errors by user
 * Only sets non-sensitive user identifiers
 */
export function setUserContext(user: { id: string; email?: string; username?: string }) {
  if (!SENTRY_ENABLED) return;

  import('@sentry/react')
    .then((Sentry) => {
      Sentry.setUser({
        id: user.id,
        // Only include email domain for privacy (not full email)
        email: user.email ? `***@${user.email.split('@')[1]}` : undefined,
        username: user.username,
      });
    })
    .catch((error) => {
      console.error('[Sentry] Failed to set user context:', error);
    });
}

/**
 * Clear user context from Sentry
 *
 * Call this when user logs out
 */
export function clearUserContext() {
  if (!SENTRY_ENABLED) return;

  import('@sentry/react')
    .then((Sentry) => {
      Sentry.setUser(null);
    })
    .catch((error) => {
      console.error('[Sentry] Failed to clear user context:', error);
    });
}

/**
 * Add custom context to Sentry events
 *
 * Useful for adding application-specific context to errors
 */
export function addContext(name: string, context: Record<string, any>) {
  if (!SENTRY_ENABLED) return;

  import('@sentry/react')
    .then((Sentry) => {
      Sentry.setContext(name, context);
    })
    .catch((error) => {
      console.error('[Sentry] Failed to add context:', error);
    });
}

/**
 * Manually capture an exception
 *
 * Use this for handling errors that don't trigger ErrorBoundary
 */
export function captureException(error: Error, context?: Record<string, any>) {
  if (!SENTRY_ENABLED) {
    console.error('Error (Sentry disabled):', error, context);
    return;
  }

  import('@sentry/react')
    .then((Sentry) => {
      Sentry.captureException(error, { extra: context });
    })
    .catch((sentryError) => {
      console.error('[Sentry] Failed to capture exception:', sentryError);
      console.error('Original error:', error);
    });
}

/**
 * Capture a message (not an error)
 *
 * Useful for logging important events or warnings
 */
export function captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info') {
  if (!SENTRY_ENABLED) {
    console.log(`[${level.toUpperCase()}] ${message}`);
    return;
  }

  import('@sentry/react')
    .then((Sentry) => {
      Sentry.captureMessage(message, level);
    })
    .catch((error) => {
      console.error('[Sentry] Failed to capture message:', error);
    });
}
