# PostgreSQL Database Container for Legal AI System
# Optimized for legal document storage and analytics

FROM postgres:16-alpine

# Set labels for metadata
LABEL maintainer="Legal AI Development Team" \
      version="1.0" \
      description="Legal AI System PostgreSQL Database" \
      postgres.version="16"

# Install additional packages for legal data processing
RUN apk add --no-cache \
    postgresql-contrib \
    postgresql-client \
    curl \
    bash \
    && rm -rf /var/cache/apk/*

# Set environment variables
ENV POSTGRES_DB=legalai_db
ENV POSTGRES_USER=legalai_user
ENV POSTGRES_PASSWORD=changeme123
ENV PGDATA=/var/lib/postgresql/data/pgdata

# Create directories for custom configurations and scripts
RUN mkdir -p /docker-entrypoint-initdb.d \
             /var/lib/postgresql/backups \
             /var/lib/postgresql/logs

# Copy initialization scripts
COPY init-scripts/ /docker-entrypoint-initdb.d/
COPY config/postgresql.conf /etc/postgresql/postgresql.conf
COPY config/pg_hba.conf /etc/postgresql/pg_hba.conf

# Copy custom scripts
COPY scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# Set ownership and permissions
RUN chown -R postgres:postgres /var/lib/postgresql/backups \
    && chown -R postgres:postgres /var/lib/postgresql/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} -h localhost || exit 1

# Expose port
EXPOSE 5432

# Use custom configuration
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]