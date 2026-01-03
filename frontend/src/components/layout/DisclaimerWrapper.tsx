'use client'

import { useState, useEffect } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertTriangle, Scale, FileText, Clock, Eye, EyeOff } from 'lucide-react'
import { usePathname } from 'next/navigation'

interface DisclaimerWrapperProps {
  children: React.ReactNode
}

interface PageDisclaimers {
  [key: string]: {
    title: string
    content: string[]
    icon: React.ReactNode
    color: string
  }
}

// Public pages that don't require disclaimer acceptance to view
const PUBLIC_PATHS = [
  '/',           // Landing page
  '/auth',       // All auth pages (login, register, etc.)
  '/terms',      // Terms of service
  '/privacy',    // Privacy policy
  '/acceptable-use', // Acceptable use policy
]

// Check if current path is a public page
const isPublicPath = (pathname: string): boolean => {
  return PUBLIC_PATHS.some(path =>
    pathname === path || pathname.startsWith(`${path}/`)
  )
}

const PAGE_SPECIFIC_DISCLAIMERS: PageDisclaimers = {
  '/': {
    title: 'General Information System Disclaimer',
    content: [
      'This legal AI system provides general information only and does NOT constitute legal advice.',
      'No attorney-client relationship is created by using this system.',
      'Information may be outdated, incomplete, or not applicable to your jurisdiction.',
      'Always consult with a qualified attorney for legal matters specific to your situation.'
    ],
    icon: <AlertTriangle className="h-5 w-5" />,
    color: 'border-red-200 bg-red-50'
  },
  '/research': {
    title: 'Legal Research Disclaimer',
    content: [
      'Legal research is for informational purposes only and does NOT constitute legal advice.',
      'Information provided may be outdated, incomplete, or jurisdiction-specific.',
      'This is NOT a substitute for attorney consultation or professional legal research.',
      'Always verify legal information with qualified legal counsel before relying on it.'
    ],
    icon: <FileText className="h-5 w-5" />,
    color: 'border-blue-200 bg-blue-50'
  },
  '/contracts': {
    title: 'Contract Analysis Disclaimer',
    content: [
      'Contract analysis does NOT constitute legal review or legal advice.',
      'AI analysis may miss critical terms, obligations, or legal implications.',
      'Consult a qualified attorney before signing ANY legal agreement.',
      'Contract interpretation varies by jurisdiction and specific circumstances.'
    ],
    icon: <Scale className="h-5 w-5" />,
    color: 'border-orange-200 bg-orange-50'
  },
  '/dashboard': {
    title: 'Dashboard Information Disclaimer',
    content: [
      'Dashboard information is NOT legal advice and is for informational purposes only.',
      'Deadlines shown are estimates - always verify actual deadlines with the court.',
      'Case status information may be delayed or incomplete.',
      'Consult your attorney for official case status and deadline confirmations.'
    ],
    icon: <Clock className="h-5 w-5" />,
    color: 'border-red-200 bg-red-50'
  },
  '/analyze': {
    title: 'Document Analysis Disclaimer',
    content: [
      'Document analysis is for informational purposes only and is NOT legal advice.',
      'AI analysis may not identify all issues, risks, or legal implications.',
      'Results should not be relied upon for legal decisions or strategy.',
      'Always have important documents reviewed by qualified legal counsel.'
    ],
    icon: <FileText className="h-5 w-5" />,
    color: 'border-purple-200 bg-purple-50'
  },
  '/documents': {
    title: 'Document Management Disclaimer',
    content: [
      'Document management features are for organizational purposes only.',
      'Document storage and analysis do NOT constitute legal advice or attorney work product.',
      'Confidentiality and privilege are NOT established through this system.',
      'Consult with your attorney regarding document management and legal strategy.'
    ],
    icon: <FileText className="h-5 w-5" />,
    color: 'border-indigo-200 bg-indigo-50'
  },
  '/costs': {
    title: 'Cost Information Disclaimer',
    content: [
      'Cost estimates are for informational purposes only and are NOT binding quotes.',
      'Actual legal costs may vary significantly based on case complexity and jurisdiction.',
      'This information does NOT constitute legal or financial advice.',
      'Consult with qualified legal counsel for accurate cost estimates and legal representation.'
    ],
    icon: <AlertTriangle className="h-5 w-5" />,
    color: 'border-green-200 bg-green-50'
  },
  '/auth': {
    title: 'Authentication System Disclaimer',
    content: [
      'Creating an account does NOT establish an attorney-client relationship.',
      'Account access is for informational system use only.',
      'No legal advice or attorney services are provided through account creation.',
      'Consult with a qualified attorney for actual legal representation.'
    ],
    icon: <Scale className="h-5 w-5" />,
    color: 'border-yellow-200 bg-yellow-50'
  },
  '/compliance': {
    title: 'Compliance Information Disclaimer',
    content: [
      'Compliance information is general and does NOT constitute legal compliance advice.',
      'Legal requirements vary by jurisdiction, industry, and specific circumstances.',
      'This system does NOT provide regulatory or compliance consulting services.',
      'Always consult qualified legal counsel for compliance matters affecting your organization.'
    ],
    icon: <AlertTriangle className="h-5 w-5" />,
    color: 'border-red-200 bg-red-50'
  },
  '/client-portal': {
    title: 'Client Portal Disclaimer',
    content: [
      'The client portal is for information sharing only and does NOT constitute legal advice.',
      'No attorney-client relationship is established through portal use.',
      'Communications through this portal are NOT privileged or confidential.',
      'Consult directly with qualified legal counsel for privileged attorney-client communications.'
    ],
    icon: <Scale className="h-5 w-5" />,
    color: 'border-blue-200 bg-blue-50'
  },
  '/admin': {
    title: 'Administrative Interface Disclaimer',
    content: [
      'Administrative functions are for system management only.',
      'Administrative access does NOT create attorney-client relationships or legal obligations.',
      'System data and analytics are for informational purposes only.',
      'Consult with qualified legal counsel regarding any legal matters or compliance issues.'
    ],
    icon: <AlertTriangle className="h-5 w-5" />,
    color: 'border-gray-200 bg-gray-50'
  },
  '/education': {
    title: 'Educational Content Disclaimer',
    content: [
      'Educational content is for general information only and does NOT constitute legal advice.',
      'Legal education materials may be outdated or not applicable to your jurisdiction.',
      'Educational content is NOT a substitute for formal legal education or attorney consultation.',
      'Always verify legal information with qualified legal counsel before making any legal decisions.'
    ],
    icon: <FileText className="h-5 w-5" />,
    color: 'border-purple-200 bg-purple-50'
  },
  '/referrals': {
    title: 'Attorney Referral Disclaimer',
    content: [
      'Attorney referrals are provided for informational purposes only.',
      'No endorsement, recommendation, or guarantee is made regarding referred attorneys.',
      'This system does NOT screen, verify, or evaluate referred attorneys.',
      'You are responsible for evaluating and selecting qualified legal counsel for your needs.'
    ],
    icon: <Scale className="h-5 w-5" />,
    color: 'border-orange-200 bg-orange-50'
  },
  '/mobile': {
    title: 'Mobile Application Disclaimer',
    content: [
      'Mobile access provides general information only and does NOT constitute legal advice.',
      'Mobile features are for convenience and do NOT create attorney-client relationships.',
      'Legal information on mobile may have limited functionality or outdated content.',
      'Always consult with qualified legal counsel for legal matters requiring professional advice.'
    ],
    icon: <AlertTriangle className="h-5 w-5" />,
    color: 'border-blue-200 bg-blue-50'
  }
}

const GLOBAL_DISCLAIMER = {
  title: 'IMPORTANT LEGAL NOTICE',
  content: [
    '⚖️ This system provides general information only and does NOT constitute legal advice.',
    '🚫 No attorney-client relationship is created by using this system.',
    '👨‍⚖️ Always consult with a qualified attorney licensed in your jurisdiction.',
    '📋 Laws vary by state and change frequently - verify current law with legal counsel.'
  ]
}

export function DisclaimerWrapper({ children }: DisclaimerWrapperProps) {
  const pathname = usePathname()

  // Prevent hydration mismatch - start with null to indicate we haven't checked yet
  const [hasAcceptedDisclaimer, setHasAcceptedDisclaimer] = useState<boolean | null>(null)
  const [isClient, setIsClient] = useState(false)

  const [headerCollapsed, setHeaderCollapsed] = useState(false)
  const [disclaimerVisible, setDisclaimerVisible] = useState(true)
  const [bypassAttempts, setBypassAttempts] = useState(0)
  const [isLocked, setIsLocked] = useState(false)
  const [showGlobalModal, setShowGlobalModal] = useState(false)

  // Interactive form state for blocking section
  const [disclaimer1Checked, setDisclaimer1Checked] = useState(false)
  const [disclaimer2Checked, setDisclaimer2Checked] = useState(false)
  const [userType, setUserType] = useState('')
  const [showDeclineMessage, setShowDeclineMessage] = useState(false)

  // Client-side hydration and localStorage check
  useEffect(() => {
    // Set client flag and check localStorage only on client
    setIsClient(true)
    const accepted = localStorage.getItem('disclaimerAccepted') === 'true'
    setHasAcceptedDisclaimer(accepted)
  }, [])

  useEffect(() => {
    // Simple bypass monitoring (reduced frequency) - only run on client after check
    if (!isClient || hasAcceptedDisclaimer === null) return

    const monitorBypass = () => {
      const complianceMarkers = document.getElementById('disclaimer-compliance-markers')
      if (!complianceMarkers && !hasAcceptedDisclaimer) {
        setBypassAttempts(prev => prev + 1)
        if (bypassAttempts >= 5) {
          setIsLocked(true)
        }
      }
    }

    // Only monitor if disclaimer not accepted
    if (!hasAcceptedDisclaimer) {
      const bypassMonitor = setInterval(monitorBypass, 10000) // Check every 10 seconds instead of 5
      return () => clearInterval(bypassMonitor)
    }
  }, [isClient, hasAcceptedDisclaimer, bypassAttempts])

  const logDisclaimerAcceptance = (type: string, path: string) => {
    // Simple logging for audit trail
    if (typeof window !== 'undefined') {
      console.log('[COMPLIANCE] Disclaimer accepted permanently', {
        timestamp: new Date().toISOString(),
        type: type,
        page: path,
        stored: 'localStorage'
      })
    }
  }

  // Show loading state while checking localStorage (prevents hydration mismatch)
  // But allow public pages to render immediately
  if (!isClient || hasAcceptedDisclaimer === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Loading Legal AI System...</p>
        </div>
      </div>
    )
  }

  // Public pages (landing, auth, terms, etc.) don't require disclaimer acceptance
  // Users will accept disclaimers during registration or first login
  if (isPublicPath(pathname)) {
    return (
      <div className="min-h-screen flex flex-col">
        <main className="flex-1 relative">
          {children}
        </main>
      </div>
    )
  }

  // Security lockout screen for bypass attempts
  if (isLocked) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50">
        <div className="text-center max-w-md">
          <AlertTriangle className="h-20 w-20 mx-auto mb-4 text-red-600" />
          <h2 className="text-2xl font-bold text-red-800 mb-2">ACCESS RESTRICTED</h2>
          <p className="text-red-700 mb-4">
            Multiple attempts to bypass legal disclaimers have been detected.
            Access has been temporarily restricted for security and compliance reasons.
          </p>
          <div className="bg-red-100 border border-red-300 rounded-lg p-4 text-sm text-red-800">
            <p className="font-semibold mb-2">⚖️ LEGAL COMPLIANCE REQUIRED</p>
            <p>This system requires acceptance of legal disclaimers to ensure compliance with legal and ethical obligations.</p>
          </div>
          <button
            onClick={() => window.location.reload()}
            className="mt-6 bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700"
          >
            Reload Page to Restart
          </button>
        </div>
      </div>
    )
  }

  // Handle decline action
  const handleDecline = () => {
    setShowDeclineMessage(true)
  }

  // Handle accept action - Store permanently in localStorage
  const handleAccept = () => {
    if (disclaimer1Checked && disclaimer2Checked && userType) {
      setHasAcceptedDisclaimer(true)

      // Store permanently in localStorage - never expires (only on client)
      if (typeof window !== 'undefined') {
        localStorage.setItem('disclaimerAccepted', 'true')
        localStorage.setItem('disclaimerAcceptedDate', new Date().toISOString())
        localStorage.setItem('userType', userType)
      }

      // Log acceptance for audit trail
      logDisclaimerAcceptance('permanent-acceptance', pathname)
    }
  }

  // Show decline message
  if (showDeclineMessage) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-red-50">
        <div className="text-center max-w-md">
          <AlertTriangle className="h-20 w-20 mx-auto mb-4 text-red-600" />
          <h2 className="text-2xl font-bold text-red-800 mb-2">Access Declined</h2>
          <p className="text-red-700 mb-4">
            You have chosen not to accept the legal disclaimers. This system cannot be used without accepting these mandatory disclaimers.
          </p>
          <div className="bg-red-100 border border-red-300 rounded-lg p-4 text-sm text-red-800 mb-4">
            <p className="font-semibold mb-2">⚖️ LEGAL COMPLIANCE REQUIRED</p>
            <p>All users must accept legal disclaimers to ensure compliance with legal and ethical obligations.</p>
          </div>
          <div className="flex gap-4 justify-center">
            <Button
              onClick={() => setShowDeclineMessage(false)}
              variant="outline"
              className="px-6 py-2"
            >
              Review Disclaimers Again
            </Button>
            <Button
              onClick={() => window.close()}
              className="bg-red-600 text-white px-6 py-2 hover:bg-red-700"
            >
              Leave Site
            </Button>
          </div>
        </div>
      </div>
    )
  }

  // Don't render content until disclaimer is accepted - ONE TIME ONLY
  if (hasAcceptedDisclaimer === false) {
    const canProceed = disclaimer1Checked && disclaimer2Checked && userType

    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-2xl">
          <CardHeader className="text-center">
            <AlertTriangle className="h-16 w-16 mx-auto mb-4 text-amber-500" />
            <CardTitle className="text-2xl font-semibold mb-2">Legal Disclaimers Required</CardTitle>
            <CardDescription className="text-gray-600">
              Please review and accept the mandatory legal disclaimers to continue using this system.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* User Type Selection */}
            <div className="space-y-3">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Scale className="h-5 w-5 text-blue-600" />
                Please select your role:
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {[
                  { value: 'attorney', label: 'I am an Attorney', icon: Scale },
                  { value: 'paralegal', label: 'I am a Paralegal', icon: FileText },
                  { value: 'client', label: 'I am a Client', icon: AlertTriangle },
                  { value: 'self-represented', label: 'I am Self-Represented', icon: AlertTriangle }
                ].map(({ value, label, icon: Icon }) => (
                  <label
                    key={value}
                    className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                      userType === value
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    <input
                      type="radio"
                      name="userType"
                      value={value}
                      checked={userType === value}
                      onChange={(e) => setUserType(e.target.value)}
                      className="mr-3"
                    />
                    <Icon className="h-4 w-4 mr-2 text-blue-600" />
                    <span className="text-sm font-medium">{label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Disclaimer Checkboxes */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
                Required Acknowledgments:
              </h3>

              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={disclaimer1Checked}
                  onChange={(e) => setDisclaimer1Checked(e.target.checked)}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  <strong>I understand this system provides legal information, not legal advice.</strong> I acknowledge that no attorney-client relationship is created through use of this system and that all information is for educational purposes only.
                </span>
              </label>

              <label className="flex items-start space-x-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={disclaimer2Checked}
                  onChange={(e) => setDisclaimer2Checked(e.target.checked)}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="text-sm text-gray-700">
                  <strong>I acknowledge I should consult an attorney for case-specific guidance.</strong> I understand that laws vary by jurisdiction and that I should verify all information with qualified legal counsel before making any legal decisions.
                </span>
              </label>
            </div>

            {/* Warning for Self-Represented Users */}
            {userType === 'self-represented' && (
              <Alert className="border-red-200 bg-red-50">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription className="text-red-800">
                  <strong>Additional Warning for Self-Represented Individuals:</strong> Representing yourself in legal matters carries significant risks. This system cannot substitute for legal representation. Strongly consider consulting with an attorney before proceeding with legal matters.
                </AlertDescription>
              </Alert>
            )}

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-4">
              <Button
                onClick={handleAccept}
                disabled={!canProceed}
                className={`flex-1 px-6 py-3 text-lg font-semibold ${
                  canProceed
                    ? 'bg-green-600 hover:bg-green-700'
                    : 'bg-gray-400 cursor-not-allowed'
                }`}
              >
                {canProceed ? (
                  <>✓ Accept and Continue</>
                ) : (
                  <>Complete Requirements Above</>
                )}
              </Button>

              <Button
                variant="outline"
                onClick={handleDecline}
                className="flex-1 px-6 py-3 border-red-300 text-red-600 hover:bg-red-50"
              >
                Decline and Leave
              </Button>
            </div>

            {/* Requirements Status */}
            {!canProceed && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-amber-800 mb-2">⚠️ Please complete all requirements:</p>
                <ul className="text-sm text-amber-700 space-y-1">
                  {!userType && <li>• Select your role/user type</li>}
                  {!disclaimer1Checked && <li>• Accept the legal information disclaimer</li>}
                  {!disclaimer2Checked && <li>• Accept the attorney consultation acknowledgment</li>}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">

      {/* Persistent Header Disclaimer */}
      {disclaimerVisible && (
        <div className={`bg-red-600 text-white transition-all duration-300 ${headerCollapsed ? 'py-1' : 'py-2'} border-b border-red-700 sticky top-0 z-[100]`}>
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between">
              <div className={`flex items-center gap-2 ${headerCollapsed ? 'text-xs' : 'text-sm'}`}>
                <AlertTriangle className={`${headerCollapsed ? 'h-3 w-3' : 'h-4 w-4'} flex-shrink-0`} />
                <span className="font-medium">
                  {headerCollapsed ? 
                    'NOT LEGAL ADVICE - General Information Only' : 
                    'IMPORTANT: This system provides general information only and does NOT constitute legal advice.'
                  }
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setHeaderCollapsed(!headerCollapsed)}
                  className="text-white hover:bg-red-700 p-1 h-auto"
                >
                  {headerCollapsed ? <Eye className="h-3 w-3" /> : <EyeOff className="h-3 w-3" />}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDisclaimerVisible(false)}
                  className="text-white hover:bg-red-700 text-xs px-2 py-1 h-auto"
                >
                  ×
                </Button>
              </div>
            </div>
            {!headerCollapsed && (
              <div className="mt-1 text-xs opacity-90">
                Consult a qualified attorney for legal advice specific to your situation.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="flex-1 relative">
          
        {children}
      </main>

      {/* Sticky Footer Disclaimer */}
      <footer className="bg-gray-900 text-white py-4 border-t border-gray-700">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <h4 className="font-semibold mb-2 flex items-center gap-1">
                <Scale className="h-4 w-4" />
                Legal Notice
              </h4>
              <p>This system does not provide legal advice. Information is for educational purposes only.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2 flex items-center gap-1">
                <AlertTriangle className="h-4 w-4" />
                No Attorney-Client Relationship
              </h4>
              <p>Use of this system does not create an attorney-client relationship or privilege.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-2 flex items-center gap-1">
                <FileText className="h-4 w-4" />
                Professional Consultation
              </h4>
              <p>Always consult with a qualified attorney licensed in your jurisdiction for legal matters.</p>
            </div>
          </div>
          <div className="border-t border-gray-700 mt-4 pt-4 text-xs text-gray-400 text-center">
            <p>Legal AI System • Not Legal Advice • For Informational Purposes Only • © {new Date().getFullYear()}</p>
            <p className="mt-1">
              Last Updated: {new Date().toLocaleDateString()} | 
              <button className="ml-2 underline hover:text-gray-300" onClick={() => setShowGlobalModal(true)}>
                Review Legal Disclaimers
              </button>
            </p>
          </div>
        </div>
      </footer>

      {/* Hidden compliance markers for automated testing and security monitoring */}
      <div 
        id="disclaimer-compliance-markers" 
        className="hidden"
        data-disclaimer-system="active"
        data-bypass-protection="enabled"
        data-global-disclaimer="present"
        data-page-disclaimer="present"
        data-footer-disclaimer="present"
        data-header-disclaimer={disclaimerVisible ? 'present' : 'minimized'}
        data-disclaimer-accepted={hasAcceptedDisclaimer.toString()}
        data-page-path={pathname}
        data-disclaimer-timestamp={new Date().toISOString()}
        data-bypass-attempts={bypassAttempts.toString()}
        data-system-locked={isLocked.toString()}
        data-compliance-version="2.1"
        data-mandatory-disclaimers="enforced"
      />

      {/* CSS-based bypass prevention - Override any attempts to hide disclaimers */}
      <style jsx>{`
        [data-disclaimer] {
          display: block !important;
          visibility: visible !important;
          opacity: 1 !important;
        }
        .disclaimer-modal {
          pointer-events: auto !important;
          z-index: 9999 !important;
        }
        .disclaimer-overlay {
          background-color: rgba(0, 0, 0, 0.8) !important;
          pointer-events: auto !important;
        }
      `}</style>

      {/* JavaScript-based bypass prevention monitoring */}
      <script
        dangerouslySetInnerHTML={{
          __html: `
            // Monitor for DOM manipulation attempts
            if (typeof window !== 'undefined') {
              const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                  if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    const target = mutation.target;
                    if (target.hasAttribute('data-disclaimer')) {
                      const style = target.style;
                      if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                        console.error('[SECURITY_VIOLATION] Attempt to hide disclaimer detected');
                        // Reset the style
                        style.display = '';
                        style.visibility = '';
                        style.opacity = '';
                      }
                    }
                  }
                });
              });
              
              // Start observing
              observer.observe(document.body, {
                attributes: true,
                subtree: true,
                attributeFilter: ['style', 'class']
              });
            }
          `,
        }}
      />
    </div>
  )
}export default DisclaimerWrapper
