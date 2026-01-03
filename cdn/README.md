# CDN Configuration
## Legal AI System - Content Delivery Network Setup

This directory contains CDN configurations and deployment scripts for optimizing static asset delivery and improving global performance of the Legal AI System.

## Overview

The CDN setup supports two popular CDN providers:
1. **AWS CloudFront** - Full Terraform infrastructure-as-code deployment
2. **Cloudflare** - JSON configuration for page rules and caching

Both configurations include:
- **Optimized caching** for different asset types
- **Security headers** for enhanced protection
- **Cache key normalization** for better hit rates
- **WAF integration** for DDoS protection
- **Compression** (Gzip and Brotli)
- **HTTP/2 and HTTP/3** support

## Directory Structure

```
cdn/
├── cloudflare/             # Cloudflare CDN configuration
│   └── page-rules.json     # Cloudflare page rules and settings
├── cloudfront/             # AWS CloudFront configuration
│   ├── distribution-config.json
│   ├── cache-policies.json
│   └── functions/
│       ├── security-headers.js
│       └── cache-key-normalization.js
├── nginx/                  # NGINX cache headers
│   └── static-assets.conf  # NGINX configuration for static files
├── terraform/              # Terraform Infrastructure-as-Code
│   └── cloudfront.tf       # CloudFront distribution, WAF, S3
├── scripts/                # Deployment automation
│   └── deploy-cloudfront.sh
└── README.md              # This file
```

## Quick Start

### Option 1: AWS CloudFront (Recommended for Production)

#### Prerequisites
- AWS CLI installed and configured
- Terraform >= 1.0
- AWS account with appropriate permissions
- Domain configured in Route 53 (or external DNS)

#### Deployment

```bash
# Make script executable
chmod +x scripts/deploy-cloudfront.sh

# Deploy to production
./scripts/deploy-cloudfront.sh deploy production

# Deploy to staging
./scripts/deploy-cloudfront.sh deploy staging
```

#### Manual Steps After Deployment

1. **Update DNS Records**:
   ```bash
   # Get CloudFront domain name
   cd terraform
   terraform output cloudfront_domain_name

   # Create CNAME record in your DNS:
   # legal-ai.example.com -> d1234abcd.cloudfront.net
   ```

2. **Configure Origin Servers**:
   - Add the X-CDN-Secret header verification to your origin servers
   - Update CORS headers if needed

3. **Verify SSL Certificate**:
   - Complete DNS validation for ACM certificate
   - Check certificate status in AWS Certificate Manager

### Option 2: Cloudflare

#### Setup

1. **Add Site to Cloudflare**:
   - Go to Cloudflare dashboard
   - Add your domain
   - Update nameservers at your registrar

2. **Import Page Rules**:
   ```bash
   # The page rules are defined in cloudflare/page-rules.json
   # Manually create them in Cloudflare dashboard > Page Rules
   ```

3. **Configure Settings**:
   - Enable Brotli compression: Speed > Optimization > Brotli
   - Enable HTTP/2 and HTTP/3: Network > HTTP/2 & HTTP/3
   - Configure Polish for images: Speed > Optimization > Polish
   - Enable Argo Smart Routing: Traffic > Argo Smart Routing

### Option 3: NGINX Only (Without CDN)

If you're not using a CDN, you can still optimize static asset delivery with NGINX:

```bash
# Copy NGINX configuration
sudo cp nginx/static-assets.conf /etc/nginx/conf.d/

# Include in your main nginx.conf
# Add this line in your server block:
# include /etc/nginx/conf.d/static-assets.conf;

# Test configuration
sudo nginx -t

# Reload NGINX
sudo systemctl reload nginx
```

## Cache Strategy

### Asset Types and Cache TTLs

| Asset Type | Cache TTL | Immutable | Description |
|-----------|-----------|-----------|-------------|
| Versioned CSS/JS | 1 year | Yes | Files with content hash (app.abc123.js) |
| Images | 30 days | No | JPG, PNG, SVG, WebP |
| Fonts | 1 year | Yes | WOFF, WOFF2, TTF |
| HTML | 1 hour | No | With must-revalidate |
| API Reads | 5 minutes | No | Read-only operations with auth |
| API Writes | No cache | No | POST, PUT, DELETE, PATCH |
| Service Worker | No cache | No | Must always fetch fresh |

### Cache Bypass Rules

The following paths are **never cached**:
- `/api/*` (except specific read operations)
- `/auth/*` (authentication endpoints)
- `/admin/*` (admin panel)
- Service workers (`/service-worker.js`)

## Security Features

### Security Headers

All responses include the following security headers:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: [configured per asset type]
```

### WAF Protection (CloudFront)

AWS WAF is configured with:
- **Rate limiting**: 2000 requests/5 minutes per IP
- **AWS Managed Rules**: Core Rule Set
- **Known Bad Inputs**: SQL injection, XSS protection
- **IP Reputation List**: Blocks known malicious IPs

### Origin Protection

CloudFront uses a secret header (`X-CDN-Secret`) to authenticate with origin servers. Configure your backend to verify this header:

```python
# Example FastAPI middleware
@app.middleware("http")
async def verify_cdn_secret(request: Request, call_next):
    cdn_secret = request.headers.get("X-CDN-Secret")
    expected_secret = os.getenv("CDN_SECRET_HEADER")

    if expected_secret and cdn_secret != expected_secret:
        # Only allow direct access in development
        if os.getenv("ENVIRONMENT") == "production":
            raise HTTPException(status_code=403, detail="Direct access forbidden")

    return await call_next(request)
```

## Performance Optimizations

### 1. Cache Key Normalization

The CloudFront function `cache-key-normalization.js` improves cache hit rates by:
- Removing tracking query parameters (utm_*, fbclid, gclid)
- Sorting query parameters alphabetically
- Lowercasing URIs
- Adding default files (index.html)

### 2. Compression

- **Gzip**: Enabled for text assets (CSS, JS, HTML, JSON)
- **Brotli**: Enabled for better compression ratios (where supported)
- **No compression** for pre-compressed formats (WOFF2, images)

### 3. Origin Shield

CloudFront Origin Shield reduces load on origin servers by:
- Consolidating requests from multiple edge locations
- Increasing cache hit ratio
- Reducing origin bandwidth costs

### 4. HTTP/2 and HTTP/3

- **HTTP/2**: Multiplexing, header compression, server push
- **HTTP/3 (QUIC)**: Faster connection establishment, better mobile performance

## Monitoring and Analytics

### CloudFront Metrics

View CloudFront metrics in AWS CloudWatch:
```bash
# Get distribution metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/CloudFront \
    --metric-name Requests \
    --dimensions Name=DistributionId,Value=YOUR_DIST_ID \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period 3600 \
    --statistics Sum
```

### Key Metrics to Monitor

- **Cache Hit Ratio**: Should be >85% for optimal performance
- **Origin Latency**: Time to fetch from origin server
- **Error Rate**: 4xx and 5xx responses
- **Data Transfer**: Bandwidth usage and costs
- **Popular Objects**: Most frequently requested assets

### Logging

CloudFront logs are stored in S3:
```
s3://legal-ai-cdn-logs-production/cloudfront/
```

Analyze logs with AWS Athena or download for analysis:
```bash
aws s3 sync s3://legal-ai-cdn-logs-production/cloudfront/ ./logs/
```

## Cost Optimization

### CloudFront Pricing Tiers

The configuration uses `PriceClass_All` by default (all edge locations). To reduce costs:

```hcl
# In terraform/cloudfront.tf
variable "cdn_price_class" {
  default = "PriceClass_100"  # North America & Europe only
}
```

Available price classes:
- `PriceClass_All`: All edge locations (most expensive, best performance)
- `PriceClass_200`: All except South America
- `PriceClass_100`: North America & Europe only (cheapest)

### S3 Lifecycle Policies

Static assets bucket includes lifecycle policies:
- **Standard-IA**: After 90 days
- **Glacier**: After 180 days
- **Delete old versions**: After 90 days

## Troubleshooting

### Cache Not Working

1. **Check cache headers**:
   ```bash
   curl -I https://legal-ai.example.com/static/image.jpg
   # Look for: X-Cache: Hit from cloudfront
   ```

2. **Verify cache policy**:
   - Check CloudFront distribution cache behaviors
   - Ensure appropriate cache policy is attached

3. **Check query strings**:
   - Some query parameters may bypass cache
   - Review cache key normalization function

### High Origin Load

1. **Check cache hit ratio**:
   ```bash
   # Should be >85% for static assets
   aws cloudfront get-distribution-statistics --id YOUR_DIST_ID
   ```

2. **Enable Origin Shield**:
   - Reduces origin requests by consolidating at regional edge cache

3. **Review cache TTLs**:
   - Increase cache TTL for static assets
   - Use versioned filenames for immutable assets

### SSL/TLS Errors

1. **Verify ACM certificate**:
   ```bash
   aws acm list-certificates --region us-east-1
   ```

2. **Check DNS validation**:
   - Ensure CNAME records are created for validation
   - Wait for certificate to be issued (can take 30 minutes)

3. **Verify CloudFront certificate binding**:
   - Check viewer certificate configuration
   - Ensure SNI is enabled

### Cache Invalidation

Invalidate cache after deployment:

```bash
# Invalidate all
./scripts/deploy-cloudfront.sh invalidate

# Or manually
aws cloudfront create-invalidation \
    --distribution-id YOUR_DIST_ID \
    --paths "/*"

# Invalidate specific paths
aws cloudfront create-invalidation \
    --distribution-id YOUR_DIST_ID \
    --paths "/static/*" "/api/*"
```

**Note**: First 1000 invalidations per month are free, then $0.005 per path.

## Maintenance

### Regular Tasks

1. **Review cache hit ratio** (weekly):
   - Target: >85% for static assets
   - Investigate if below 70%

2. **Review WAF logs** (weekly):
   - Check for blocked attacks
   - Update rules if needed

3. **Update CloudFront Functions** (as needed):
   ```bash
   cd cloudfront/functions
   # Edit security-headers.js or cache-key-normalization.js

   # Deploy updates
   ../scripts/deploy-cloudfront.sh deploy production
   ```

4. **Review costs** (monthly):
   - Check CloudFront costs in AWS Billing
   - Optimize price class if needed
   - Review data transfer patterns

### Updating Configuration

```bash
# Update Terraform configuration
cd terraform
vim cloudfront.tf

# Plan changes
terraform plan -var="environment=production"

# Apply changes
terraform apply -var="environment=production"

# Invalidate cache if needed
../scripts/deploy-cloudfront.sh invalidate
```

## Migration Checklist

When migrating from direct origin to CDN:

- [ ] Set up CDN infrastructure (CloudFront or Cloudflare)
- [ ] Configure DNS (update CNAME records)
- [ ] Verify SSL certificate
- [ ] Update origin servers (add X-CDN-Secret verification)
- [ ] Test cache headers
- [ ] Configure WAF rules
- [ ] Set up monitoring and alerts
- [ ] Update deployment pipeline
- [ ] Test invalidation process
- [ ] Monitor cache hit ratio
- [ ] Update documentation

## Support and Resources

### Documentation Links

- **AWS CloudFront**: https://docs.aws.amazon.com/cloudfront/
- **Cloudflare CDN**: https://developers.cloudflare.com/cache/
- **NGINX Caching**: https://nginx.org/en/docs/http/ngx_http_proxy_module.html

### Useful Commands

```bash
# Get distribution info
aws cloudfront get-distribution --id YOUR_DIST_ID

# List all distributions
aws cloudfront list-distributions

# Update distribution
aws cloudfront update-distribution --id YOUR_DIST_ID --if-match ETAG

# Get real-time logs
aws cloudfront get-monitoring-subscription --distribution-id YOUR_DIST_ID

# Create invalidation
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"

# Wait for invalidation
aws cloudfront wait invalidation-completed \
    --distribution-id YOUR_DIST_ID \
    --id INVALIDATION_ID
```

## License

This CDN configuration is part of the Legal AI System project.

---

**Last Updated**: 2024-01-15
**Maintained By**: Legal AI System Team
