# Redis Cache Container for Legal AI System
# Optimized for session management and caching legal document metadata

FROM redis:7-alpine

# Set labels for metadata
LABEL maintainer="Legal AI Development Team" \
      version="1.0" \
      description="Legal AI System Redis Cache" \
      redis.version="7"

# Install additional tools
RUN apk add --no-cache \
    curl \
    bash \
    && rm -rf /var/cache/apk/*

# Create directories for configuration and data
RUN mkdir -p /usr/local/etc/redis \
             /var/log/redis \
             /data/backups

# Copy Redis configuration
COPY redis.conf /usr/local/etc/redis/redis.conf
COPY sentinel.conf /usr/local/etc/redis/sentinel.conf

# Copy custom scripts
COPY scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# Set proper ownership
RUN chown -R redis:redis /var/log/redis \
    && chown -R redis:redis /data \
    && chown -R redis:redis /usr/local/etc/redis

# Create non-root user (redis user already exists in base image)
USER redis

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD redis-cli ping || exit 1

# Expose ports
EXPOSE 6379

# Start Redis with custom configuration
CMD ["redis-server", "/usr/local/etc/redis/redis.conf"]