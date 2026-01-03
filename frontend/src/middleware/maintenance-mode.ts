import { NextRequest, NextResponse } from 'next/server'

/**
 * EMERGENCY MAINTENANCE MODE MIDDLEWARE
 * 
 * This middleware blocks ALL user access to the system during critical
 * legal compliance maintenance. It overrides all other middleware and
 * ensures no content is served until maintenance is complete.
 */

export function maintenanceModeMiddleware(req: NextRequest) {
  const isMaintenanceActive = process.env.MAINTENANCE_MODE === 'true'
  
  // Allow health checks and admin endpoints during maintenance
  const allowedPaths = [
    '/api/health',
    '/api/admin/maintenance',
    '/_next/static',
    '/_next/image',
    '/favicon.ico'
  ]
  
  const isAllowedPath = allowedPaths.some(path => 
    req.nextUrl.pathname.startsWith(path)
  )
  
  if (isMaintenanceActive && !isAllowedPath) {
    // Log maintenance access attempt for compliance audit
    console.log('[MAINTENANCE] Access blocked during maintenance mode', {
      timestamp: new Date().toISOString(),
      path: req.nextUrl.pathname,
      ip: req.ip || req.headers.get('x-forwarded-for') || 'unknown',
      userAgent: req.headers.get('user-agent') || 'unknown'
    })
    
    // Return maintenance page HTML directly
    const maintenanceHtml = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Maintenance - Legal AI</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: #fef2f2; 
            margin: 0; 
            padding: 20px; 
            display: flex; 
            min-height: 100vh; 
            align-items: center; 
            justify-content: center;
        }
        .container { 
            max-width: 600px; 
            background: white; 
            padding: 40px; 
            border-radius: 8px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            text-align: center;
            border: 2px solid #dc2626;
        }
        .icon { 
            font-size: 64px; 
            margin-bottom: 20px; 
        }
        .title { 
            color: #dc2626; 
            font-size: 24px; 
            margin-bottom: 10px; 
            font-weight: bold;
        }
        .message { 
            color: #374151; 
            margin-bottom: 30px; 
            line-height: 1.6;
        }
        .status {
            background: #fee; 
            border: 1px solid #dc2626; 
            padding: 15px; 
            border-radius: 4px; 
            margin: 20px 0;
        }
        .legal-notice {
            background: #fffbeb;
            border: 1px solid #d97706;
            padding: 15px;
            border-radius: 4px;
            margin-top: 20px;
            font-size: 14px;
            color: #92400e;
        }
        .timestamp {
            font-size: 12px;
            color: #6b7280;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="icon">🚨</div>
        <div class="title">SYSTEM UNDER MAINTENANCE</div>
        <div class="message">
            The Legal AI System is currently undergoing critical legal compliance updates.
            All user access has been temporarily suspended to ensure system integrity.
        </div>
        <div class="status">
            <strong>Status:</strong> Maintenance in progress<br>
            <strong>Estimated Duration:</strong> 2-4 hours<br>
            <strong>Reason:</strong> Critical legal compliance updates
        </div>
        <div class="legal-notice">
            <strong>Legal Notice:</strong> This maintenance is being performed to ensure 
            full legal compliance. The system will not be available until all compliance 
            requirements are verified and restored.
        </div>
        <div class="timestamp">
            Maintenance started: ${new Date().toLocaleString()}<br>
            For urgent matters: admin@legalai.com
        </div>
    </div>
    
    <!-- Hidden maintenance marker for monitoring -->
    <div id="maintenance-mode-active" 
         data-maintenance-active="true"
         data-started="${new Date().toISOString()}"
         style="display: none;">
    </div>
</body>
</html>
    `
    
    return new NextResponse(maintenanceHtml, {
      status: 503,
      headers: {
        'Content-Type': 'text/html',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-Maintenance-Mode': 'active',
        'X-Maintenance-Reason': 'Critical legal compliance updates',
        'X-Maintenance-Started': new Date().toISOString(),
        'Retry-After': '7200' // 2 hours in seconds
      }
    })
  }
  
  return NextResponse.next()
}