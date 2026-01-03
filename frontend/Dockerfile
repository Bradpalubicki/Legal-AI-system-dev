# Frontend Next.js Docker Container
# Multi-stage build for optimized production image

# =============================================================================
# DEPENDENCIES STAGE
# =============================================================================
FROM node:20-alpine AS dependencies

# Install system dependencies
RUN apk add --no-cache \
    libc6-compat \
    python3 \
    make \
    g++ \
    git

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./

# Install ALL dependencies (including devDependencies for build)
RUN \
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
  elif [ -f package-lock.json ]; then npm ci; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \
  else echo "Lockfile not found." && exit 1; \
  fi

# =============================================================================
# BUILDER STAGE
# =============================================================================
FROM node:20-alpine AS builder

# Build arguments for Next.js public env vars (must be set at build time)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

WORKDIR /app

# Copy dependencies from dependencies stage
COPY --from=dependencies /app/node_modules ./node_modules

# Copy source code
COPY . .

# Set environment variables for build
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Log the API URL being used (for debugging)
RUN echo "Building with NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}"

# Build the application (creates .next/standalone with output: 'standalone')
RUN npm run build

# =============================================================================
# DEVELOPMENT STAGE (for local docker-compose development)
# =============================================================================
FROM node:20-alpine AS development

WORKDIR /app

# Install all dependencies including dev dependencies
COPY package.json package-lock.json* yarn.lock* pnpm-lock.yaml* ./
RUN npm install

# Install development tools
RUN apk add --no-cache git vim curl wget

# Copy source code
COPY . .

# Set development environment
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs && \
    chown -R nextjs:nodejs /app

USER nextjs
EXPOSE 3000
CMD ["npm", "run", "dev"]

# =============================================================================
# TESTING STAGE (for CI/CD testing)
# =============================================================================
FROM development AS testing

USER root

# Install testing tools
RUN apk add --no-cache chromium chromium-chromedriver

ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/lib/chromium/

USER nextjs
CMD ["npm", "run", "test:ci"]

# =============================================================================
# PRODUCTION STAGE (DEFAULT - must be last for Railway/Docker defaults)
# =============================================================================
FROM node:20-alpine AS production

WORKDIR /app

# Set environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# PORT is set by Railway/hosting platform, default to 3000
ENV PORT=3000

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built application from builder stage (standalone output)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000

# Start the application - server.js respects PORT env var
CMD ["node", "server.js"]
