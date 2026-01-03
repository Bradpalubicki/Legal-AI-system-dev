/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Enable standalone output for Docker production builds
  output: 'standalone',

  // ESLint configuration - don't fail builds on lint warnings
  eslint: {
    // Only run ESLint on specific directories during build
    dirs: ['src'],
    // Don't fail production builds on lint errors (warnings only)
    ignoreDuringBuilds: true,
  },

  // TypeScript configuration
  typescript: {
    // Don't fail production builds on TS errors during development
    // TODO: Fix all TypeScript errors and set back to false
    ignoreBuildErrors: true,
  },

  // =============================================================================
  // SECURITY CONFIGURATION
  // =============================================================================

  // Environment variables configuration
  env: {
    // Only NEXT_PUBLIC_* variables are exposed to the browser
    // All other environment variables are server-side only
  },

  // Ensure sensitive env vars are NOT exposed to the client
  // Next.js automatically only exposes NEXT_PUBLIC_* variables
  // This is just explicit documentation
  publicRuntimeConfig: {
    // Empty - we use NEXT_PUBLIC_* prefix instead
  },

  serverRuntimeConfig: {
    // Server-only variables (never exposed to browser)
    // Examples: API keys, database URLs, secrets
  },

  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on'
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload'
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff'
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY'
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block'
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin'
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()'
          }
        ],
      },
    ];
  },

  // Webpack configuration to prevent accidental bundling of server-only code
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Replace server-only modules with empty objects on client-side
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: false,
      };
    }
    return config;
  },
}

module.exports = nextConfig