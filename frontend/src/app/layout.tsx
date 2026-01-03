import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/providers/AuthProvider'
import { ThemeProvider } from '@/providers/ThemeProvider'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { Toaster } from '@/components/ui/toaster'
import { Toaster as SonnerToaster } from 'sonner'
import { DocumentProvider } from '@/contexts/DocumentContext'
import dynamic from 'next/dynamic'

const QueryProvider = dynamic(
  () => import('@/components/providers/QueryProvider'),
  { ssr: false }
)

const DisclaimerWrapper = dynamic(
  () => import('@/components/layout/DisclaimerWrapper'),
  {
    ssr: false,
    loading: () => <div className="flex items-center justify-center min-h-screen">Loading...</div>
  }
)

const HelpAgent = dynamic(
  () => import('@/components/HelpAgent'),
  {
    ssr: false
  }
)

// Initialize Sentry error tracking (production only)
import { initSentry } from '@/lib/sentry'
if (typeof window !== 'undefined') {
  initSentry()
}

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Legal AI System - General Information Only',
  description: 'AI-powered legal document analysis and research system - General Information Only - Not Legal Advice',
  keywords: 'legal AI, document analysis, legal research, general information, not legal advice, educational',
  authors: [{ name: 'Legal AI System' }],
  robots: 'noindex, nofollow', // Prevent indexing to avoid legal liability
  other: {
    // Legal compliance meta tags - REQUIRED for compliance
    'legal-disclaimer': 'This system provides general information only and does not constitute legal advice',
    'attorney-client': 'No attorney-client relationship is created by use of this system',
    'compliance-version': '2.0',
    'disclaimer-required': 'true',
    'content-type': 'general-information-only',
  },
}

// Move viewport to separate export (Next.js 14 requirement)
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#334155',
}

// Idle timeout configuration from environment variables
const idleTimeoutMinutes = parseInt(process.env.NEXT_PUBLIC_IDLE_TIMEOUT_MINUTES || '15', 10)
const idleWarningMinutes = parseInt(process.env.NEXT_PUBLIC_IDLE_WARNING_MINUTES || '2', 10)

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {/*
        ERROR BOUNDARY - TOP LEVEL:
        Catches all React errors and prevents white screen of death
        Automatically reports errors to Sentry (if configured)
        Shows user-friendly error page with error ID for support
        */}
        <ErrorBoundary boundaryName="RootLayout">
          <ThemeProvider>
            <AuthProvider
              idleTimeoutMinutes={idleTimeoutMinutes}
              idleWarningMinutes={idleWarningMinutes}
            >
              <QueryProvider>
                <DocumentProvider>
                  {/*
                  CRITICAL COMPLIANCE LAYER:
                  DisclaimerWrapper provides mandatory disclaimers and bypass protection
                  This wrapper ensures NO page can load without proper legal disclaimers
                  Dynamic import with ssr: false prevents hydration mismatches with localStorage
                  */}
                  <ErrorBoundary boundaryName="DisclaimerWrapper">
                    <DisclaimerWrapper>
                      <ErrorBoundary boundaryName="AppContent">
                        {children}
                      </ErrorBoundary>
                    </DisclaimerWrapper>
                  </ErrorBoundary>
                </DocumentProvider>
              </QueryProvider>
            </AuthProvider>
          </ThemeProvider>
        </ErrorBoundary>
        <Toaster />
        <SonnerToaster position="top-right" richColors closeButton />
        {/* AI Help Agent - Available on all pages */}
        <HelpAgent />
      </body>
    </html>
  )
}
