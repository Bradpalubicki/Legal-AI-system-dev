/**
 * Next.js Configuration for CDN Optimization
 * Legal AI System - Production CDN Integration
 *
 * This configuration optimizes Next.js for use with CloudFront or Cloudflare CDN.
 *
 * Usage:
 *   1. Copy this file to next.config.js (or merge with existing config)
 *   2. Set CDN_URL environment variable
 *   3. Build and deploy
 *
 * Environment Variables Required:
 *   - CDN_URL: Full CDN URL (e.g., https://cdn.legal-ai.example.com)
 *   - NEXT_PUBLIC_CDN_URL: Public CDN URL for client-side
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // =============================================================================
  // CDN Configuration
  // =============================================================================

  // Asset prefix for CDN (all static assets will be served from CDN)
  assetPrefix: process.env.CDN_URL || '',

  // Generate unique build ID for cache busting
  generateBuildId: async () => {
    // Use git commit hash if available, otherwise timestamp
    const { execSync } = require('child_process');
    try {
      return execSync('git rev-parse --short HEAD').toString().trim();
    } catch (e) {
      return `build-${Date.now()}`;
    }
  },

  // =============================================================================
  // Image Optimization
  // =============================================================================

  images: {
    // Loader configuration for CDN
    loader: process.env.CDN_URL ? 'custom' : 'default',

    // Custom loader for CloudFront/Cloudflare
    loaderFile: process.env.CDN_URL ? './src/utils/imageLoader.js' : undefined,

    // Image domains allowed (add your CDN domain)
    domains: [
      'legal-ai.example.com',
      'cdn.legal-ai.example.com',
      'd123abc.cloudfront.net', // CloudFront domain
    ],

    // Remote patterns for Next.js 13+
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.legal-ai.example.com',
      },
      {
        protocol: 'https',
        hostname: '**.cloudfront.net',
      },
    ],

    // Image formats
    formats: ['image/avif', 'image/webp'],

    // Device sizes for responsive images
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],

    // Image sizes for srcset
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],

    // Disable static image imports optimization if using CDN
    disableStaticImages: false,

    // Minimize quality slightly for better compression
    minimumCacheTTL: 31536000, // 1 year in seconds

    // Dangerously allow SVG (if needed, with caution)
    dangerouslyAllowSVG: false,
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },

  // =============================================================================
  // Compiler Options
  // =============================================================================

  compiler: {
    // Remove console logs in production
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,

    // React strict mode
    reactStrictMode: true,
  },

  // Strict mode for better performance
  reactStrictMode: true,

  // Power by header
  poweredByHeader: false,

  // Compression (usually handled by CDN, but enable for origin)
  compress: true,

  // =============================================================================
  // Production Optimizations
  // =============================================================================

  // Production browser list
  productionBrowserSourceMaps: false,

  // Optimize fonts
  optimizeFonts: true,

  // SWC minification (faster than Terser)
  swcMinify: true,

  // =============================================================================
  // Headers for CDN
  // =============================================================================

  async headers() {
    return [
      // Static assets - long cache
      {
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },

      // Images - long cache
      {
        source: '/images/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=2592000, immutable', // 30 days
          },
        ],
      },

      // Fonts - very long cache
      {
        source: '/fonts/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
        ],
      },

      // API routes - no cache
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
        ],
      },

      // HTML pages - short cache with revalidation
      {
        source: '/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=3600, must-revalidate',
          },
          // Security headers (CloudFront function should also set these)
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'SAMEORIGIN',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },

  // =============================================================================
  // Redirects and Rewrites
  // =============================================================================

  async redirects() {
    return [
      // Redirect www to non-www (or vice versa)
      {
        source: '/:path*',
        has: [
          {
            type: 'host',
            value: 'www.legal-ai.example.com',
          },
        ],
        destination: 'https://legal-ai.example.com/:path*',
        permanent: true,
      },
    ];
  },

  // =============================================================================
  // Experimental Features
  // =============================================================================

  experimental: {
    // Optimize CSS
    optimizeCss: true,

    // Optimize package imports
    optimizePackageImports: ['@radix-ui/react-icons', 'lucide-react'],

    // Modern build
    modern: true,
  },

  // =============================================================================
  // Webpack Configuration
  // =============================================================================

  webpack: (config, { dev, isServer }) => {
    // Production optimizations
    if (!dev && !isServer) {
      // Split chunks for better caching
      config.optimization.splitChunks = {
        chunks: 'all',
        cacheGroups: {
          default: false,
          vendors: false,
          // Vendor chunk
          vendor: {
            name: 'vendor',
            chunks: 'all',
            test: /node_modules/,
            priority: 20,
          },
          // Common chunk
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'all',
            priority: 10,
            reuseExistingChunk: true,
            enforce: true,
          },
          // Styles
          styles: {
            name: 'styles',
            test: /\.css$/,
            chunks: 'all',
            enforce: true,
          },
        },
      };

      // Minimize bundle size
      config.optimization.minimize = true;
    }

    return config;
  },

  // =============================================================================
  // Output Configuration
  // =============================================================================

  // Output as standalone for Docker
  output: process.env.BUILD_STANDALONE === 'true' ? 'standalone' : undefined,

  // =============================================================================
  // Environment Variables
  // =============================================================================

  env: {
    // Expose CDN URL to client-side
    NEXT_PUBLIC_CDN_URL: process.env.CDN_URL || '',
  },

  // Public runtime config (deprecated in Next.js 13+, use env instead)
  publicRuntimeConfig: {
    cdnUrl: process.env.CDN_URL || '',
  },
};

module.exports = nextConfig;

// =============================================================================
// Example imageLoader.js
// =============================================================================

/**
 * Create this file at: src/utils/imageLoader.js
 *
 * export default function cloudflareImageLoader({ src, width, quality }) {
 *   const params = [`width=${width}`];
 *   if (quality) {
 *     params.push(`quality=${quality}`);
 *   }
 *   const paramsString = params.join(',');
 *   return `https://cdn.legal-ai.example.com/cdn-cgi/image/${paramsString}/${src}`;
 * }
 *
 * // For CloudFront with Lambda@Edge or CloudFront Functions:
 * export default function cloudfrontImageLoader({ src, width, quality }) {
 *   const url = new URL(src, process.env.NEXT_PUBLIC_CDN_URL);
 *   url.searchParams.set('width', width.toString());
 *   if (quality) {
 *     url.searchParams.set('quality', quality.toString());
 *   }
 *   return url.toString();
 * }
 */
