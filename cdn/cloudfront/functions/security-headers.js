/**
 * CloudFront Function: Security Headers
 *
 * Adds security headers to all responses for enhanced security.
 * This function runs at edge locations for minimal latency impact.
 *
 * Event Type: viewer-response
 */

function handler(event) {
    var response = event.response;
    var headers = response.headers;

    // Strict-Transport-Security (HSTS)
    // Force HTTPS for 1 year, include subdomains
    headers['strict-transport-security'] = {
        value: 'max-age=31536000; includeSubDomains; preload'
    };

    // X-Content-Type-Options
    // Prevent MIME type sniffing
    headers['x-content-type-options'] = {
        value: 'nosniff'
    };

    // X-Frame-Options
    // Prevent clickjacking attacks
    headers['x-frame-options'] = {
        value: 'SAMEORIGIN'
    };

    // X-XSS-Protection
    // Enable XSS filter in browsers
    headers['x-xss-protection'] = {
        value: '1; mode=block'
    };

    // Referrer-Policy
    // Control referrer information
    headers['referrer-policy'] = {
        value: 'strict-origin-when-cross-origin'
    };

    // Permissions-Policy (formerly Feature-Policy)
    // Control browser features
    headers['permissions-policy'] = {
        value: 'geolocation=(), microphone=(), camera=(), payment=()'
    };

    // Content-Security-Policy
    // Prevent XSS and data injection attacks
    // Note: Adjust based on your specific needs
    headers['content-security-policy'] = {
        value: [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https:",
            "connect-src 'self' https://api.legal-ai.example.com",
            "frame-ancestors 'self'",
            "base-uri 'self'",
            "form-action 'self'"
        ].join('; ')
    };

    return response;
}
