# SSL/TLS Configuration Guide

**Status:** 📋 Documentation Complete
**Priority:** Critical (Production Security)
**Last Updated:** 2025-10-14

## Overview

SSL/TLS encryption is **mandatory** for production deployment of the Legal AI System. This guide covers certificate acquisition, configuration, and best practices for securing your application with HTTPS.

## Why SSL/TLS is Critical

### Legal Requirements
- **Attorney-Client Privilege**: Communications must be encrypted
- **HIPAA Compliance**: PHI must be encrypted in transit
- **GDPR**: Personal data must be protected
- **State Bar Requirements**: Most states require encryption for client data

### Security Benefits
- ✅ Encrypts all data in transit
- ✅ Prevents man-in-the-middle attacks
- ✅ Authenticates your server
- ✅ Required for modern web features (geolocation, camera, etc.)
- ✅ SEO benefits (Google ranking factor)
- ✅ Browser trust indicators

### Business Impact
- ❌ No SSL = Browser warnings = Lost clients
- ❌ No SSL = No modern APIs (Service Workers, etc.)
- ❌ No SSL = Potential liability for data breaches
- ✅ SSL = Professional, trustworthy appearance

## Certificate Options

### 1. Let's Encrypt (Recommended for Most)

**Pros:**
- ✅ **FREE** certificates
- ✅ Automated renewal
- ✅ Trusted by all browsers
- ✅ Easy to set up
- ✅ Wildcard certificates available
- ✅ API for automation

**Cons:**
- ❌ 90-day expiration (requires renewal automation)
- ❌ No extended validation (EV) certificates
- ❌ Rate limits (50 certs/week per domain)

**Best For:** Most production deployments

### 2. Commercial CAs (DigiCert, Sectigo, GlobalSign)

**Pros:**
- ✅ Extended Validation (EV) available
- ✅ Longer expiration (1-2 years)
- ✅ Insurance/warranty included
- ✅ 24/7 support
- ✅ Organization validation

**Cons:**
- ❌ Costs $50-$300+ per year
- ❌ Manual renewal process
- ❌ More complex validation

**Best For:** Large enterprises, financial institutions

### 3. Self-Signed Certificates

**Pros:**
- ✅ Free
- ✅ No external dependency

**Cons:**
- ❌ Browser warnings
- ❌ Not trusted by default
- ❌ Manual trust configuration required

**Best For:** Development/testing ONLY, never production

## Quick Start: Let's Encrypt with Certbot

### Prerequisites

```bash
# Domain requirements
- Your domain must point to your server (DNS A record)
- Port 80 must be accessible (for HTTP-01 challenge)
- OR Port 443 (for TLS-ALPN-01 challenge)

# Server requirements
- Ubuntu 20.04+ / Debian 10+
- Root or sudo access
- Nginx or Apache installed
```

### Step 1: Install Certbot

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx

# Verify installation
certbot --version
```

### Step 2: Obtain Certificate

```bash
# For Nginx (automated configuration)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# For manual certificate only
sudo certbot certonly --nginx -d yourdomain.com

# For wildcard certificate (requires DNS challenge)
sudo certbot certonly --manual --preferred-challenges dns \
  -d '*.yourdomain.com' -d yourdomain.com
```

**Follow the prompts:**
1. Enter your email (for renewal notifications)
2. Agree to Terms of Service
3. Choose whether to share email with EFF
4. Certbot will automatically configure Nginx

### Step 3: Verify Certificate

```bash
# Check certificate details
sudo certbot certificates

# Test SSL configuration
curl -I https://yourdomain.com

# Use SSL Labs test (thorough)
# Visit: https://www.ssllabs.com/ssltest/
```

### Step 4: Configure Automatic Renewal

```bash
# Test renewal process
sudo certbot renew --dry-run

# Certbot automatically creates renewal timer
# Verify it's running
sudo systemctl status certbot.timer

# Manual renewal (if needed)
sudo certbot renew
```

## Nginx Configuration

### Basic SSL Configuration

Create: `/etc/nginx/sites-available/legal-ai-system`

```nginx
# HTTP - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;

    # Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS - Main configuration
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Certificate Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;

    # SSL Security Settings (Mozilla Intermediate)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;

    # SSL Session Configuration
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:50m;
    ssl_session_tickets off;

    # OCSP Stapling (certificate validation)
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Proxy to Backend API
    location /api {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Proxy to Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Logging
    access_log /var/log/nginx/legal-ai-access.log;
    error_log /var/log/nginx/legal-ai-error.log;
}
```

### Enable Configuration

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/legal-ai-system /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Production Hardening

Create: `/etc/nginx/conf.d/ssl-hardening.conf`

```nginx
# SSL Hardening Configuration
# Apply to all SSL servers

# Disable SSL (only TLS)
ssl_protocols TLSv1.2 TLSv1.3;

# Modern cipher suite (Mozilla Intermediate)
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';

# Let client choose cipher (better performance)
ssl_prefer_server_ciphers off;

# SSL session configuration
ssl_session_timeout 1d;
ssl_session_cache shared:MozSSL:10m;
ssl_session_tickets off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;

# DNS resolver for OCSP
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# Diffie-Hellman parameters (generate once)
# Generate with: sudo openssl dhparam -out /etc/nginx/dhparam.pem 2048
ssl_dhparam /etc/nginx/dhparam.pem;
```

## Docker Configuration

### Docker Compose with SSL Termination

Create: `docker-compose.production.yml`

```yaml
version: '3.8'

services:
  # Nginx - SSL Termination
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/conf.d:/etc/nginx/conf.d:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - certbot-webroot:/var/www/certbot:ro
    depends_on:
      - backend
      - frontend
    networks:
      - app-network
    restart: unless-stopped

  # Certbot - Certificate Management
  certbot:
    image: certbot/certbot
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt
      - certbot-webroot:/var/www/certbot
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done;'"
    networks:
      - app-network

  # Backend API
  backend:
    build:
      context: .
      dockerfile: docker/backend/Dockerfile.production
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=${DATABASE_URL}
    networks:
      - app-network
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: .
      dockerfile: docker/frontend/Dockerfile.production
    environment:
      - NEXT_PUBLIC_API_URL=https://yourdomain.com/api
    networks:
      - app-network
    restart: unless-stopped

volumes:
  certbot-webroot:

networks:
  app-network:
    driver: bridge
```

### Initial Certificate Acquisition with Docker

```bash
# 1. Start nginx without SSL first
docker-compose -f docker-compose.production.yml up -d nginx

# 2. Obtain certificate
docker-compose run --rm certbot certonly --webroot \
  --webroot-path=/var/www/certbot \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email \
  -d yourdomain.com -d www.yourdomain.com

# 3. Update nginx config with SSL configuration

# 4. Restart nginx
docker-compose -f docker-compose.production.yml restart nginx

# 5. Start certbot for auto-renewal
docker-compose -f docker-compose.production.yml up -d certbot
```

## Security Best Practices

### 1. HSTS (HTTP Strict Transport Security)

**What it does:** Forces browsers to always use HTTPS

```nginx
# Add to your nginx SSL server block
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

**Levels:**
- `max-age=31536000` (1 year) - Minimum recommended
- `max-age=63072000` (2 years) - Better
- `includeSubDomains` - Apply to all subdomains
- `preload` - Include in browser HSTS preload list

**HSTS Preload:** https://hstspreload.org/

### 2. Perfect Forward Secrecy

Ensures past communications remain secure even if private key is compromised.

```nginx
# Use ECDHE or DHE cipher suites
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256...';

# Generate strong DH parameters
sudo openssl dhparam -out /etc/nginx/dhparam.pem 2048
ssl_dhparam /etc/nginx/dhparam.pem;
```

### 3. OCSP Stapling

Improves SSL handshake performance and privacy.

```nginx
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
resolver 8.8.8.8 8.8.4.4 valid=300s;
```

### 4. Security Headers

```nginx
# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Prevent clickjacking
add_header X-Frame-Options "SAMEORIGIN" always;

# Prevent MIME sniffing
add_header X-Content-Type-Options "nosniff" always;

# XSS Protection (legacy browsers)
add_header X-XSS-Protection "1; mode=block" always;

# Referrer policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Content Security Policy (customize for your app)
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
```

### 5. Disable Weak Protocols/Ciphers

```nginx
# Only TLS 1.2 and 1.3
ssl_protocols TLSv1.2 TLSv1.3;

# No weak ciphers
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256...';

# Disable SSL session tickets (potential vulnerability)
ssl_session_tickets off;
```

## Certificate Renewal

### Automated Renewal (Recommended)

Let's Encrypt certificates expire in 90 days. Automate renewal:

```bash
# Certbot creates systemd timer automatically
sudo systemctl status certbot.timer

# Or use cron
sudo crontab -e

# Add this line (runs twice daily)
0 0,12 * * * certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

### Monitoring Certificate Expiration

```bash
# Check expiration date
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Or use openssl
openssl x509 -enddate -noout -in /etc/letsencrypt/live/yourdomain.com/cert.pem
```

### Renewal Notifications

- Let's Encrypt emails you at 20, 10, and 1 day before expiration
- Set up monitoring (see Monitoring section)
- Use external services (SSL Labs, Certificate Monitor)

## Testing & Validation

### 1. SSL Labs Test (Recommended)

https://www.ssllabs.com/ssltest/

**Target Grade: A or A+**

Checks:
- Certificate validity
- Protocol support
- Cipher suites
- Vulnerability testing
- Configuration issues

### 2. Command Line Testing

```bash
# Test SSL connection
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com

# Check certificate
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -text

# Test specific protocol
openssl s_client -connect yourdomain.com:443 -tls1_2

# Test cipher
openssl s_client -connect yourdomain.com:443 -cipher 'ECDHE-RSA-AES128-GCM-SHA256'
```

### 3. Browser Testing

```bash
# Test in browser
https://yourdomain.com

# Check:
- Lock icon appears
- Certificate is valid
- No mixed content warnings
- HSTS header present (in DevTools)
```

### 4. Automated Testing

```bash
# testssl.sh - comprehensive SSL/TLS testing
git clone https://github.com/drwetter/testssl.sh.git
cd testssl.sh
./testssl.sh https://yourdomain.com
```

## Troubleshooting

### Certificate Not Trusted

**Problem:** Browser shows "Not Secure" or certificate warning

**Solutions:**
```bash
# 1. Check certificate chain
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com | grep -A 2 "Certificate chain"

# 2. Verify fullchain.pem is used (not cert.pem)
# In nginx:
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;

# 3. Check certificate order
openssl storeutl -noout -text -certs /etc/letsencrypt/live/yourdomain.com/fullchain.pem
```

### Mixed Content Warnings

**Problem:** HTTPS page loading HTTP resources

**Solutions:**
```bash
# 1. Check all resources use HTTPS
grep -r "http://" frontend/src/

# 2. Use protocol-relative URLs
<script src="//example.com/script.js">

# 3. Add CSP header to enforce HTTPS
add_header Content-Security-Policy "upgrade-insecure-requests" always;
```

### Certificate Renewal Fails

**Problem:** Certbot renewal fails

**Common Causes & Solutions:**

```bash
# 1. Port 80 not accessible
# Check firewall
sudo ufw status
sudo ufw allow 80/tcp

# 2. Webroot permission issues
sudo chown -R www-data:www-data /var/www/certbot

# 3. Rate limit hit
# Wait or use different domain/subdomain

# 4. DNS issues
dig yourdomain.com
```

### OCSP Stapling Not Working

**Problem:** SSL Labs shows "OCSP stapling: No"

**Solutions:**
```nginx
# 1. Verify configuration
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/letsencrypt/live/yourdomain.com/chain.pem;
resolver 8.8.8.8 8.8.4.4 valid=300s;

# 2. Test OCSP
openssl ocsp -no_nonce -issuer /etc/letsencrypt/live/yourdomain.com/chain.pem -cert /etc/letsencrypt/live/yourdomain.com/cert.pem -url http://ocsp.int-x3.letsencrypt.org -header "HOST" "ocsp.int-x3.letsencrypt.org"
```

## Monitoring

### Certificate Expiration Monitoring

```bash
# Create monitoring script
cat > /usr/local/bin/check-cert-expiry.sh << 'EOF'
#!/bin/bash
DOMAIN="yourdomain.com"
DAYS_WARN=30

EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))

if [ $DAYS_LEFT -lt $DAYS_WARN ]; then
    echo "WARNING: Certificate expires in $DAYS_LEFT days"
    # Send alert (email, Slack, etc.)
fi
EOF

chmod +x /usr/local/bin/check-cert-expiry.sh

# Add to cron
echo "0 6 * * * /usr/local/bin/check-cert-expiry.sh" | sudo crontab -
```

### External Monitoring Services

- **SSL Labs Monitor**: Monitors SSL/TLS configuration
- **UptimeRobot**: Free uptime monitoring
- **Pingdom**: Enterprise monitoring
- **Datadog**: Infrastructure monitoring with SSL checks

## Compliance Requirements

### Legal Industry Standards

**Required:**
- ✅ TLS 1.2 or higher
- ✅ Strong cipher suites
- ✅ Valid, trusted certificate
- ✅ No mixed content
- ✅ HSTS enabled

**Recommended:**
- ✅ TLS 1.3 support
- ✅ Perfect Forward Secrecy
- ✅ Certificate transparency
- ✅ CAA DNS records
- ✅ Grade A or A+ on SSL Labs

### Industry-Specific

**HIPAA:**
- TLS 1.2 minimum
- FIPS 140-2 compliant ciphers
- Audit logging
- Annual security review

**PCI DSS:**
- TLS 1.2 minimum (TLS 1.0/1.1 prohibited)
- Strong cryptography
- Key management procedures
- Quarterly vulnerability scans

## Backup & Disaster Recovery

### Backup Certificates

```bash
# Backup Let's Encrypt directory
sudo tar czf letsencrypt-backup-$(date +%Y%m%d).tar.gz /etc/letsencrypt/

# Store securely offsite
# DO NOT commit to version control!
```

### Certificate Rotation

```bash
# Force renewal (30 days before expiry)
sudo certbot renew --force-renewal

# Deploy new certificate
sudo systemctl reload nginx
```

### Emergency Certificate Revocation

```bash
# If private key is compromised
sudo certbot revoke --cert-path /etc/letsencrypt/live/yourdomain.com/cert.pem

# Obtain new certificate
sudo certbot certonly --nginx -d yourdomain.com
```

## Cost Analysis

### Let's Encrypt (FREE)
- Certificate: $0
- Renewal: $0 (automated)
- Support: Community
- **Total: $0/year**

### Commercial CA (Paid)
- Standard SSL: $50-$150/year
- Wildcard SSL: $150-$300/year
- EV SSL: $200-$500/year
- **Total: $50-$500/year**

### Hidden Costs
- Server time: ~1 hour setup
- Monitoring: Included or $10-50/month
- Maintenance: ~30 min/quarter

**Recommendation:** Use Let's Encrypt unless you need EV certificates or have specific compliance requirements.

## Next Steps

After SSL/TLS is configured:

1. ✅ Test with SSL Labs (aim for A+)
2. ✅ Enable HSTS preload
3. ✅ Set up certificate monitoring
4. ✅ Configure auto-renewal
5. ✅ Test renewal process
6. ✅ Document in runbook
7. ✅ Train team on certificate management
8. ✅ Schedule quarterly security reviews

---

**Questions?** Check Certbot documentation or Let's Encrypt community forums
**Security Issue?** Consult with security professional before deploying
