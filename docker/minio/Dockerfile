# MinIO Object Storage Container for Legal AI System
# S3-compatible storage for legal documents and files

FROM minio/minio:latest

# Set labels for metadata
LABEL maintainer="Legal AI Development Team" \
      version="1.0" \
      description="Legal AI System MinIO Object Storage" \
      minio.version="latest"

# Switch to root to install additional tools
USER root

# Install additional tools
RUN microdnf update && \
    microdnf install -y \
    curl \
    bash \
    mc \
    && microdnf clean all

# Create directories for configuration and scripts
RUN mkdir -p /etc/minio \
             /usr/local/bin/minio-scripts \
             /data/backups

# Copy MinIO configuration and scripts
COPY config/ /etc/minio/
COPY scripts/ /usr/local/bin/minio-scripts/
RUN chmod +x /usr/local/bin/minio-scripts/*.sh

# Create policies directory
RUN mkdir -p /etc/minio/policies

# Copy IAM policies
COPY policies/ /etc/minio/policies/

# Set proper ownership for minio user
RUN chown -R minio-user:minio-user /data \
    && chown -R minio-user:minio-user /etc/minio \
    && chown -R minio-user:minio-user /usr/local/bin/minio-scripts

# Switch back to minio user
USER minio-user

# Environment variables for MinIO
ENV MINIO_ROOT_USER=legalai_admin
ENV MINIO_ROOT_PASSWORD=changeme123456
ENV MINIO_BROWSER_REDIRECT_URL=http://localhost:9001
ENV MINIO_SERVER_URL=http://localhost:9000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:9000/minio/health/live || exit 1

# Expose ports
EXPOSE 9000 9001

# Default command
CMD ["minio", "server", "/data", "--console-address", ":9001"]