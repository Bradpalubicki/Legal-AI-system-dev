# Nginx Reverse Proxy for Legal AI System
# Optimized for legal document serving and load balancing

FROM nginx:1.25-alpine

# Set labels for metadata
LABEL maintainer="Legal AI Development Team" \
      version="1.0" \
      description="Legal AI System Nginx Reverse Proxy" \
      nginx.version="1.25"

# Install additional tools
RUN apk add --no-cache \
    curl \
    bash \
    openssl \
    certbot \
    certbot-nginx \
    && rm -rf /var/cache/apk/*

# Create directories
RUN mkdir -p /etc/nginx/conf.d/legal-ai \
             /etc/nginx/ssl \
             /var/log/nginx/legal-ai \
             /var/cache/nginx/legal-ai \
             /usr/share/nginx/html/legal-ai

# Copy Nginx configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/legal-ai/
COPY html/ /usr/share/nginx/html/legal-ai/

# Copy SSL configuration and scripts
COPY ssl/ /etc/nginx/ssl/
COPY scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# Generate self-signed certificates for development
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/legal-ai-dev.key \
    -out /etc/nginx/ssl/legal-ai-dev.crt \
    -subj "/C=US/ST=CA/L=San Francisco/O=Legal AI System/CN=localhost"

# Set proper permissions
RUN chown -R nginx:nginx /var/log/nginx/legal-ai \
    && chown -R nginx:nginx /var/cache/nginx/legal-ai \
    && chown -R nginx:nginx /usr/share/nginx/html/legal-ai

# Create nginx user directories
RUN mkdir -p /var/cache/nginx/client_temp \
             /var/cache/nginx/proxy_temp \
             /var/cache/nginx/fastcgi_temp \
             /var/cache/nginx/uwsgi_temp \
             /var/cache/nginx/scgi_temp \
    && chown -R nginx:nginx /var/cache/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

# Expose ports
EXPOSE 80 443

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]