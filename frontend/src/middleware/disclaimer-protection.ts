import { NextRequest, NextResponse } from 'next/server'

export function disclaimerProtectionMiddleware(req: NextRequest) {
  const response = NextResponse.next()
  
  // Add disclaimer headers to ALL responses
  response.headers.set('X-Legal-Disclaimer', 'This system provides general information only and does not constitute legal advice')
  response.headers.set('X-Attorney-Client', 'No attorney-client relationship is created')
  response.headers.set('X-Compliance-Protected', 'true')
  response.headers.set('X-Disclaimer-Required', 'mandatory')
  response.headers.set('X-Content-Nature', 'general-information-only')
  
  // Security headers for legal content
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('Referrer-Policy', 'no-referrer')
  response.headers.set('X-Robots-Tag', 'noindex, nofollow')
  
  // Page-specific disclaimer requirements
  const pathname = req.nextUrl.pathname
  
  if (pathname.startsWith('/research')) {
    response.headers.set('X-Page-Disclaimer', 'Legal research is for informational purposes only - Not a substitute for attorney consultation')
  } else if (pathname.startsWith('/contracts')) {
    response.headers.set('X-Page-Disclaimer', 'Contract analysis does not constitute legal review - Consult an attorney before signing')
  } else if (pathname.startsWith('/dashboard')) {
    response.headers.set('X-Page-Disclaimer', 'Dashboard information is not legal advice - Deadlines shown are estimates')
  } else if (pathname.startsWith('/analyze')) {
    response.headers.set('X-Page-Disclaimer', 'Document analysis is for informational purposes only - Not legal advice')
  }
  
  // Log disclaimer header injection for compliance audit
  console.log(`[COMPLIANCE] Disclaimer headers injected for ${pathname}`, {
    timestamp: new Date().toISOString(),
    path: pathname,
    userAgent: req.headers.get('user-agent'),
    ip: req.ip || req.headers.get('x-forwarded-for') || 'unknown'
  })
  
  return response
}