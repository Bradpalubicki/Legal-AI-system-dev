import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Routes that require authentication (server-side redirect)
// Note: /settings uses client-side auth check via useAuth() hook
const protectedRoutes = ['/dashboard', '/documents', '/cases', '/clients', '/profile'];

// Routes that require compliance check
const complianceRequiredRoutes = ['/dashboard', '/documents', '/cases', '/clients'];

// Public routes that don't require authentication
const publicRoutes = ['/auth/login', '/auth/register', '/auth/forgot-password', '/auth/reset-password'];

// Legal document routes
const legalRoutes = ['/terms', '/privacy', '/acceptable-use'];

// Compliance routes
const complianceRoutes = ['/compliance/terms-acceptance', '/compliance/onboarding'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
  const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));
  const isLegalRoute = legalRoutes.some(route => pathname.startsWith(route));
  const isComplianceRoute = complianceRoutes.some(route => pathname.startsWith(route));
  const requiresComplianceCheck = complianceRequiredRoutes.some(route => pathname.startsWith(route));

  // Get authentication token from cookies or headers
  const token = request.cookies.get('accessToken')?.value || 
                request.headers.get('authorization')?.replace('Bearer ', '');

  // Allow legal document and compliance routes without authentication
  if (isLegalRoute || isComplianceRoute) {
    return NextResponse.next();
  }

  // Redirect unauthenticated users to login for protected routes
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/auth/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Allow public routes
  if (isPublicRoute) {
    return NextResponse.next();
  }

  // For authenticated users accessing compliance-required routes,
  // add compliance headers to trigger client-side checks
  if (requiresComplianceCheck && token) {
    const response = NextResponse.next();
    response.headers.set('X-Requires-Compliance-Check', 'true');
    return response;
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
};