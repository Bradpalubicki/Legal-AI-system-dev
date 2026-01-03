import { NextRequest } from 'next/server'
import { maintenanceModeMiddleware } from './src/middleware/maintenance-mode'
import { disclaimerProtectionMiddleware } from './src/middleware/disclaimer-protection'

export function middleware(request: NextRequest) {
  // CRITICAL: Check maintenance mode FIRST - overrides all other middleware
  const maintenanceResponse = maintenanceModeMiddleware(request)
  if (maintenanceResponse.status === 503) {
    return maintenanceResponse
  }
  
  // Only apply disclaimer protection if not in maintenance mode
  return disclaimerProtectionMiddleware(request)
}

export const config = {
  // Apply middleware to all routes except static files and API routes that don't serve user content
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api/health (system health checks)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder files
     */
    '/((?!api/health|_next/static|_next/image|favicon.ico|public/).*)',
  ],
}