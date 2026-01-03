# Frontend Error Boundaries - React Error Handling

**Status:** ✅ Configured
**Priority:** High (Production)
**Last Updated:** 2025-10-14

## Overview

React Error Boundaries provide a safety net for catching JavaScript errors in component trees, preventing the entire app from crashing and showing a user-friendly error page instead.

## What Are Error Boundaries?

Error boundaries are React components that:
- Catch JavaScript errors anywhere in their child component tree
- Log those errors
- Display a fallback UI instead of crashing
- Can report errors to error tracking services (Sentry)

**Important:** Error boundaries do NOT catch:
- Errors in event handlers (use try-catch)
- Errors in async code (use try-catch)
- Errors in server-side rendering
- Errors in the error boundary itself

## Implementation

### 1. Error Boundary Component

Location: `frontend/src/components/ErrorBoundary.tsx`

**Features:**
- ✅ Automatic Sentry error reporting
- ✅ Unique error ID generation for support
- ✅ Development vs Production UI
- ✅ Component stack trace logging
- ✅ Custom fallback UI support
- ✅ Reset functionality
- ✅ Boundary naming for debugging
- ✅ Privacy-first (filters sensitive data)

**Basic Usage:**
```tsx
import { ErrorBoundary } from '@/components/ErrorBoundary'

function MyComponent() {
  return (
    <ErrorBoundary boundaryName="MyFeature">
      <YourComponent />
    </ErrorBoundary>
  )
}
```

**With Custom Fallback:**
```tsx
<ErrorBoundary
  boundaryName="CriticalFeature"
  fallback={<div>Custom error message</div>}
  onError={(error, errorInfo) => {
    // Custom error handling
    console.log('Feature failed:', error)
  }}
>
  <YourComponent />
</ErrorBoundary>
```

### 2. App-Level Integration

Location: `frontend/src/app/layout.tsx`

**Three-Level Error Boundary Strategy:**

```tsx
<ErrorBoundary boundaryName="RootLayout">
  <AuthProvider>
    <ErrorBoundary boundaryName="DisclaimerWrapper">
      <DisclaimerWrapper>
        <ErrorBoundary boundaryName="AppContent">
          {children}
        </ErrorBoundary>
      </DisclaimerWrapper>
    </ErrorBoundary>
  </AuthProvider>
</ErrorBoundary>
```

**Why Multiple Boundaries?**
- **RootLayout**: Catches critical app-level errors
- **DisclaimerWrapper**: Catches auth/compliance errors
- **AppContent**: Catches page content errors

This allows graceful degradation - if one part fails, the rest can still work.

### 3. Sentry Integration

Location: `frontend/src/lib/sentry.ts`

**Features:**
- Automatic error tracking in production
- Performance monitoring (Core Web Vitals)
- Session replay on errors (with PII masking)
- Breadcrumbs for debugging
- Privacy-first data filtering

**Configuration:**
```bash
# .env
NEXT_PUBLIC_SENTRY_ENABLED=true
NEXT_PUBLIC_SENTRY_DSN=https://your-dsn@o0.ingest.sentry.io/project
NEXT_PUBLIC_ENVIRONMENT=production
```

**Manual Error Capture:**
```tsx
import { captureException, captureMessage, addContext } from '@/lib/sentry'

// Capture an error
try {
  riskyOperation()
} catch (error) {
  captureException(error, { operation: 'riskyOperation' })
}

// Log a message
captureMessage('User completed important action', 'info')

// Add custom context
addContext('legal_case', {
  case_id: case.id,
  case_number: case.number
})
```

## Error Boundary Strategies

### 1. Page-Level Boundaries

Wrap individual pages to prevent one page's errors from affecting others:

```tsx
// app/dashboard/page.tsx
export default function DashboardPage() {
  return (
    <ErrorBoundary
      boundaryName="DashboardPage"
      fallback={
        <div className="p-6">
          <h2>Dashboard temporarily unavailable</h2>
          <button onClick={() => window.location.reload()}>
            Refresh
          </button>
        </div>
      }
    >
      <DashboardContent />
    </ErrorBoundary>
  )
}
```

### 2. Feature-Level Boundaries

Wrap complex features to isolate failures:

```tsx
// components/DocumentAnalysis.tsx
export default function DocumentAnalysis() {
  return (
    <ErrorBoundary
      boundaryName="DocumentAnalysis"
      onError={(error) => {
        // Feature-specific error handling
        logAnalysisFailure(error)
      }}
    >
      <AnalysisEngine />
    </ErrorBoundary>
  )
}
```

### 3. Widget-Level Boundaries

Wrap individual widgets/cards to prevent cascading failures:

```tsx
// components/Dashboard.tsx
export default function Dashboard() {
  return (
    <div className="grid grid-cols-3 gap-4">
      <ErrorBoundary boundaryName="RecentCases" fallback={<WidgetError />}>
        <RecentCases />
      </ErrorBoundary>

      <ErrorBoundary boundaryName="Analytics" fallback={<WidgetError />}>
        <Analytics />
      </ErrorBoundary>

      <ErrorBoundary boundaryName="Notifications" fallback={<WidgetError />}>
        <Notifications />
      </ErrorBoundary>
    </div>
  )
}
```

## Best Practices

### 1. Boundary Naming

Always name your boundaries for easy debugging:

```tsx
// ✅ Good
<ErrorBoundary boundaryName="UserProfile">

// ❌ Bad
<ErrorBoundary>
```

### 2. Appropriate Granularity

**Too Broad:**
```tsx
// One boundary for entire app - too coarse
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

**Too Fine:**
```tsx
// Boundary for every component - too fine
<ErrorBoundary><Button /></ErrorBoundary>
<ErrorBoundary><Input /></ErrorBoundary>
```

**Just Right:**
```tsx
// Boundaries at feature/page level
<ErrorBoundary boundaryName="PageContent">
  <ComplexFeature />
</ErrorBoundary>
```

### 3. Custom Fallback UI

Provide context-specific fallback UI:

```tsx
<ErrorBoundary
  boundaryName="PaymentForm"
  fallback={
    <div className="text-center p-6">
      <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
      <h3 className="font-bold mb-2">Payment Form Error</h3>
      <p className="text-gray-600 mb-4">
        We couldn't load the payment form. Please try again.
      </p>
      <button onClick={() => window.location.reload()}>
        Reload Page
      </button>
    </div>
  }
>
  <PaymentForm />
</ErrorBoundary>
```

### 4. Error Recovery

Provide ways to recover from errors:

```tsx
function FeatureWithRecovery() {
  const [error, setError] = useState(null)

  return (
    <ErrorBoundary
      boundaryName="RecoverableFeature"
      onError={(err) => setError(err)}
      fallback={
        <div>
          <p>Something went wrong</p>
          <button onClick={() => setError(null)}>
            Try Again
          </button>
        </div>
      }
    >
      <Feature />
    </ErrorBoundary>
  )
}
```

## Development vs Production

### Development Mode

**Shows:**
- Full error message
- Component stack trace
- Boundary name
- Detailed debugging info

**Example:**
```
🔴 Error Boundary: DocumentAnalysis
Error: Cannot read property 'data' of undefined
Component Stack:
  at DocumentView
  at DocumentAnalysis
  at Dashboard
```

### Production Mode

**Shows:**
- User-friendly message
- Error ID for support
- Recovery options
- No sensitive details

**Example:**
```
Something went wrong

We're sorry, but something unexpected happened.
Please try refreshing the page or contact support.

Error ID: err_1697123456_abc123
```

## Handling Specific Errors

### Network Errors

```tsx
function DataFetcher() {
  return (
    <ErrorBoundary
      boundaryName="DataFetcher"
      fallback={
        <div>
          <p>Unable to load data</p>
          <p>Please check your connection</p>
          <button onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      }
    >
      <DataComponent />
    </ErrorBoundary>
  )
}
```

### Permission Errors

```tsx
function ProtectedContent() {
  return (
    <ErrorBoundary
      boundaryName="ProtectedContent"
      onError={(error) => {
        if (error.message.includes('401')) {
          router.push('/login')
        }
      }}
    >
      <SecureComponent />
    </ErrorBoundary>
  )
}
```

## Testing Error Boundaries

### Manual Testing

Create a test button to trigger errors:

```tsx
function ErrorTestButton() {
  const [shouldError, setShouldError] = useState(false)

  if (shouldError) {
    throw new Error('Test error for boundary')
  }

  return (
    <button onClick={() => setShouldError(true)}>
      Trigger Error (Dev Only)
    </button>
  )
}

// Wrap in boundary
<ErrorBoundary boundaryName="ErrorTest">
  {process.env.NODE_ENV === 'development' && <ErrorTestButton />}
</ErrorBoundary>
```

### Automated Testing

Test with React Testing Library:

```tsx
import { render, screen } from '@testing-library/react'
import { ErrorBoundary } from '@/components/ErrorBoundary'

const ThrowError = () => {
  throw new Error('Test error')
}

test('ErrorBoundary shows fallback UI on error', () => {
  // Suppress console.error for this test
  jest.spyOn(console, 'error').mockImplementation(() => {})

  render(
    <ErrorBoundary>
      <ThrowError />
    </ErrorBoundary>
  )

  expect(screen.getByText(/something went wrong/i)).toBeInTheDocument()
})
```

## Monitoring & Alerts

### Sentry Dashboard

Monitor these metrics:
- Error frequency by boundary
- Most common errors
- Error trends over time
- User impact (how many users affected)

### Alert Rules

Set up alerts for:
- **Critical**: > 10 errors/minute in any boundary
- **Warning**: New error type appears
- **Info**: Error rate increases 50% above baseline

### Error Grouping

Sentry groups errors by:
- Error message
- Stack trace
- Boundary name (via tags)

## Troubleshooting

### Error Boundary Not Catching Errors

**Problem:** Error not caught by boundary

**Solutions:**
1. Check if error is in event handler (use try-catch)
2. Check if error is async (use try-catch)
3. Verify boundary wraps the component
4. Check if error is in boundary itself

### Sentry Not Receiving Errors

**Problem:** Errors not appearing in Sentry

**Check:**
1. `NEXT_PUBLIC_SENTRY_ENABLED=true` in production
2. Valid `NEXT_PUBLIC_SENTRY_DSN` configured
3. Browser console shows "✅ Error logged to Sentry"
4. Check Sentry project settings
5. Verify error isn't filtered by `ignoreErrors`

### Infinite Error Loops

**Problem:** Error boundary keeps re-rendering

**Solution:**
```tsx
// Don't throw errors in error boundary's render
public render() {
  if (this.state.hasError) {
    try {
      return this.renderFallback()
    } catch (err) {
      // Fallback for fallback
      return <div>Critical Error</div>
    }
  }
  return this.props.children
}
```

## Privacy & Legal Compliance

### PII Filtering

The error boundary automatically filters:
- User passwords
- API keys and tokens
- Credit card numbers
- Social security numbers
- Personal identifiers

### Session Replay Privacy

Session replay is configured with:
- `maskAllText: true` - All text masked
- `blockAllMedia: true` - Images/videos blocked
- `maskAllInputs: true` - Form inputs masked
- `replaysOnErrorSampleRate: 1.0` - Only record error sessions

### GDPR Compliance

- Error IDs don't contain PII
- User emails are domain-only in Sentry (`***@example.com`)
- Full error details only in development
- Users can request error data deletion via Sentry

## Support Workflow

### When User Reports Error

1. **Get Error ID** from user
2. **Search Sentry** by error ID
3. **View Context**:
   - Full stack trace
   - Component that failed
   - Boundary that caught it
   - User session replay (if available)
4. **Fix & Deploy**
5. **Notify User** when fixed

### Error ID Format

```
err_1697123456_abc123
    └─ timestamp └─ random
```

This format ensures:
- Unique IDs
- Sortable by time
- Easy to communicate

## Next Steps

After error boundaries are set up:

1. ✅ Add boundaries to critical pages
2. ✅ Configure Sentry alerts
3. ✅ Test error scenarios
4. ✅ Train team on error triage
5. ✅ Monitor error rates
6. ✅ Create error playbooks
7. ✅ Set up on-call rotation
8. ✅ Review errors weekly

---

**Questions?** Check console logs or Sentry documentation
**Errors?** Error boundaries should catch them! 😄
