# Deployment & GitHub Setup Guide

## ⚠️ CRITICAL: Pre-GitHub Checklist

Before pushing to GitHub (public or private), you MUST complete these steps:

### 1. Verify Secrets Are Protected ✅

Run this command to verify no secrets in git:
```bash
git log --all --full-history --source --full-diff -- .env | head -20
```

If ANY output appears, your .env was committed. You must:
- Rotate ALL API keys immediately
- Remove .env from git history
- Update .gitignore

### 2. Create Environment Configuration

```bash
# Copy template
cp .env.example .env

# Edit .env with your actual API keys (NEVER commit this file)
# Get keys from:
# - OpenAI: https://platform.openai.com/api-keys
# - Anthropic: https://console.anthropic.com/settings/keys
# - CourtListener: https://www.courtlistener.com/help/api/
```

### 3. Verify .gitignore Coverage

Ensure these are in .gitignore:
- ✅ `.env` and all `.env.*` files
- ✅ `*.db` and `*.sqlite` files
- ✅ `node_modules/` and `__pycache__/`
- ✅ `storage/` and `uploads/`
- ✅ Test files and temporary data

### 4. Clean Up Untracked Files

Before committing:
```bash
# Review untracked files
git status

# Remove test/temporary files:
rm -f backend/*.json  # Test JSON files
rm -f *.json  # Root-level test files
rm -f backend/*.py  # Test Python scripts (analyze_*, test_*, etc.)
rm -f *.bat  # Windows batch scripts
```

### 5. Remove Sensitive Data from Modified Files

Check modified files for:
- API keys
- Passwords
- Email addresses
- Personal information

```bash
# Review changes
git diff backend/app/api/
git diff frontend/src/
```

---

## Production Deployment Checklist

### Frontend Environment Variables

Create `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=https://your-api-domain.com
NEXT_PUBLIC_WS_URL=wss://your-api-domain.com
NEXTAUTH_SECRET=<generate-32-char-random-string>
SENTRY_DSN=<your-sentry-dsn>
```

### Backend Environment Variables

Production .env must have:
```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@host:5432/dbname
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>
COURTLISTENER_API_KEY=<your-key>
SMTP_PASSWORD=<your-app-password>
```

### Security Hardening

1. **Rotate ALL API keys** if any were ever exposed
2. **Use strong SECRET_KEY and JWT_SECRET** (32+ random characters)
3. **Enable HTTPS** in production
4. **Set CORS_ORIGINS** to your production domains only
5. **Configure rate limiting** appropriately

### Database Setup

```bash
# Initialize database
python backend/main.py  # Auto-creates tables

# For production with PostgreSQL:
# 1. Create database
# 2. Set DATABASE_URL in .env
# 3. Run migrations (when Alembic configured)
```

### Frontend Build

```bash
cd frontend
npm install
npm run build
npm start  # Production server on port 3000
```

### Backend Server

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Known Issues & Limitations

### Critical (Fix Before Production)

1. **Hard-coded URLs** in frontend components
   - Status: In Progress
   - Impact: Deployment will fail
   - Fix: Use environment variables everywhere

2. **TypeScript errors ignored**
   - Status: `next.config.js` has `ignoreBuildErrors: true`
   - Impact: Hidden type errors may cause runtime failures
   - Fix: Remove flag, fix all errors

3. **Auth tokens in localStorage**
   - Status: XSS vulnerability
   - Impact: Security risk
   - Fix: Move to httpOnly cookies

### Performance Issues

4. **Waterfall API requests**
   - Location: `dashboard/page.tsx`, case loading
   - Impact: 10+ second load times
   - Fix: Use `Promise.all()` for parallel requests

5. **Bundle size**
   - Impact: 3MB+ JavaScript bundle
   - Fix: Remove duplicate chart libraries, use dynamic imports

### Testing

6. **No test coverage**
   - Status: Only 2 compliance tests exist
   - Impact: High risk of regressions
   - Fix: Add Jest + React Testing Library tests

---

## Minimal Viable Deployment (Quick Path)

If you need to deploy ASAP with known limitations:

### 1. Environment Setup (30 min)
- Create production .env files
- Set all required API keys
- Configure database URL

### 2. Quick Fixes (2-3 hours)
```bash
# Fix hard-coded URLs
cd frontend
# Replace all 'http://localhost:8000' with process.env.NEXT_PUBLIC_API_URL
find src -type f -name "*.tsx" -o -name "*.ts" | xargs sed -i 's|http://localhost:8000|${process.env.NEXT_PUBLIC_API_URL}|g'
```

### 3. Build & Deploy
```bash
# Frontend
cd frontend
npm run build
# Deploy to Vercel/Netlify

# Backend
cd backend
# Deploy to Railway/Render/Heroku
```

### 4. Post-Deployment Monitoring
- Monitor Sentry for errors
- Check API usage and costs
- Review logs for issues

---

## Recommended Production Stack

- **Frontend**: Vercel (automatic HTTPS, CDN, serverless)
- **Backend**: Railway / Render (easy Python deployment)
- **Database**: Neon / Supabase (managed PostgreSQL)
- **Redis**: Upstash (serverless Redis)
- **Storage**: AWS S3 / Cloudflare R2
- **Monitoring**: Sentry (errors) + Vercel Analytics

---

## Cost Estimates

### AI API Usage
- **OpenAI GPT-4**: ~$0.03/request (document analysis)
- **Anthropic Claude**: ~$0.02/request (explanations)
- **Monthly estimate**: $100-500 (depends on usage)

### Infrastructure
- Vercel (Hobby): $0 (limited)
- Vercel (Pro): $20/month
- Railway: $5-20/month (usage-based)
- Database: $0-25/month (depending on size)

**Total**: ~$25-100/month for low traffic

---

## Support & Troubleshooting

### Common Issues

**Q: Frontend can't connect to backend**
- Check NEXT_PUBLIC_API_URL is set correctly
- Verify CORS settings in backend allow frontend domain
- Check backend is running and accessible

**Q: Database connection fails**
- Verify DATABASE_URL format
- Check database server is running
- Ensure firewall allows connections

**Q: AI API calls failing**
- Verify API keys are correct
- Check API usage limits
- Review error logs in Sentry

### Getting Help

1. Check logs: `docker-compose logs` or Vercel/Railway logs
2. Enable DEBUG mode temporarily: `DEBUG=true` in .env
3. Review Sentry error reports
4. Check backend health: `http://your-api/api/health`

---

## Next Steps After Deployment

1. **Set up monitoring** - Configure alerts for errors, usage
2. **Add tests** - Prevent regressions
3. **Performance optimization** - Fix waterfall requests, bundle size
4. **Security audit** - Review all endpoints, add rate limiting
5. **Documentation** - API docs, user guides
