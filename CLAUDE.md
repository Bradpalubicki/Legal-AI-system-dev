# Legal AI System - Project Context

**EDUCATIONAL CONTENT DISCLAIMER**: All information provided by this system is for educational purposes only and does not constitute legal advice. This platform is designed for informational purposes and learning about legal processes, not for providing professional legal counsel.

## Project Overview
A comprehensive AI-powered legal document analysis and research system designed to assist legal professionals with document review, case research, and legal analysis tasks.

## Architecture
- **Backend**: Python FastAPI for APIs and document processing
- **Frontend**: Next.js 14 with TypeScript and Tailwind CSS
- **Database**: PostgreSQL for structured data
- **Cache**: Redis for sessions and caching
- **Background Jobs**: Celery with Redis broker
- **Storage**: MinIO (S3-compatible) for document storage
- **AI Models**: OpenAI GPT-4, Anthropic Claude, and local models

## Key Features
1. **Document Analysis**: AI-powered analysis of legal documents (contracts, briefs, etc.)
2. **Legal Research**: Integration with legal databases (Westlaw, LexisNexis, CourtListener)
3. **Citation Processing**: Automatic extraction and validation of legal citations
4. **Client Management**: Secure client portal with document sharing
5. **Compliance & Audit**: Full audit trails and data retention policies
6. **Multi-format Support**: PDF, DOCX, TXT, RTF document processing

## Environment Configuration (CRITICAL - READ THIS)

### Two .env Files - Know Which to Use!

| File | Purpose | Contains |
|------|---------|----------|
| `/.env` (ROOT) | **Backend + All Secrets** | API keys, database, Redis, email, Stripe, ALL sensitive config |
| `/frontend/.env` | **Frontend Only** | ONLY `NEXT_PUBLIC_*` variables (public config, no secrets!) |

### Rules for Claude Code:
1. **API keys, passwords, secrets** → ALWAYS go in ROOT `/.env`
2. **NEXT_PUBLIC_* variables** → Go in `/frontend/.env` (these are exposed to browser!)
3. **NEVER put secrets in frontend/.env** - it gets bundled into client JavaScript
4. **Backend reads from ROOT .env** - see `backend/main.py` lines 19-21
5. **Port must match**: Both files should have `NEXT_PUBLIC_API_URL=http://localhost:8000`

### When Adding New Config:
- New backend setting? → Add to ROOT `/.env`
- New frontend public setting? → Add to `/frontend/.env` with `NEXT_PUBLIC_` prefix
- New API key or secret? → ROOT `/.env` ONLY, access via backend API

### File Locations:
```
legal-ai-system/
├── .env                    ← MAIN CONFIG (all secrets here)
├── .env.example            ← Template for .env (safe to commit)
├── frontend/
│   ├── .env                ← Frontend public config only
│   └── .env.example        ← Template (safe to commit)
└── backend/
    └── .env.deprecated     ← OLD FILE - DO NOT USE
```

## Court Record Coverage (IMPORTANT)

### What's Searchable in PACER Search Tab
Our CourtListener integration provides **FREE** access to:
- **All U.S. District Courts** - Federal civil/criminal cases
- **All U.S. Bankruptcy Courts** - All bankruptcy filings
- **All U.S. Circuit Courts of Appeals** - Federal appeals
- **U.S. Supreme Court** - Supreme Court cases
- **State Appellate Opinions** - Published opinions only, NOT dockets

### What's NOT Available (State Trial Courts)
State trial court records are **NOT available** through our system. This includes:
- State Circuit Courts / Superior Courts
- County Courts
- Municipal Courts
- Foreclosures (most are in state court)
- Divorces and custody cases
- Evictions and landlord-tenant disputes
- Traffic violations
- Most misdemeanors
- Probate matters
- Small claims

### Why State Courts Aren't Available
This is an industry-wide limitation, not a bug in our system:
1. **No Public APIs**: Most state courts don't offer programmatic access
2. **Scraping Prohibited**: Many states explicitly prohibit automated data collection
3. **Expensive Subscriptions**: The few states with APIs charge $2,250-$12,500+/year
4. **Fragmented Systems**: Some states have 50+ separate county systems

### State Court Portal Reference
Full documentation with official portal URLs for all 50 states is available at:
- Data file: `backend/app/data/state_court_coverage.json`
- Service: `backend/app/services/state_court_info_service.py`
- API: `/api/v1/state-courts/*`

### Key States with Good Free Search (Direct Users Here)
- **Wisconsin**: https://wcca.wicourts.gov/ (all 72 counties)
- **Missouri**: https://www.courts.mo.gov/casenet/base/welcome.do (Case.net)
- **Indiana**: https://mycase.in.gov/ (MyCase)
- **Minnesota**: https://publicaccess.courts.state.mn.us/CaseSearch (MCRO - free docs!)
- **Oklahoma**: https://www.oscn.net/ (OSCN - free docs!)

### Example User Scenarios
**User asks**: "Why can't I find Timothy Brielmaier's foreclosure in Wisconsin?"
**Answer**: Foreclosures are filed in Wisconsin Circuit Court (state court), not federal court. Search directly at https://wcca.wicourts.gov/

**User asks**: "Where are the California divorce records?"
**Answer**: California has no unified state court search. Each of 58 counties has its own system. For Los Angeles: https://www.lacourt.org/

## Project Structure
```
legal-ai-system/
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Configuration and security
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic
│   │   └── utils/          # Utility functions
│   ├── tests/              # Backend tests
│   └── main.py             # FastAPI app entry point
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Next.js pages
│   │   ├── hooks/          # Custom React hooks
│   │   ├── utils/          # Frontend utilities
│   │   └── types/          # TypeScript types
│   ├── public/             # Static assets
│   └── next.config.js      # Next.js configuration
├── docker/                 # Docker configurations
│   ├── backend/
│   ├── frontend/
│   └── nginx/
├── storage/                # Local file storage
└── docs/                   # Documentation
```

## Key Dependencies

### Backend (Python)
- **FastAPI**: Modern web framework for APIs
- **SQLAlchemy**: Database ORM
- **Pydantic**: Data validation and settings
- **Celery**: Background task processing
- **OpenAI/Anthropic**: AI model integrations
- **PyPDF2/python-docx**: Document processing
- **SpaCy/NLTK**: Natural language processing
- **Eyecite**: Legal citation parsing

### Frontend (Next.js/TypeScript)
- **Next.js 14**: React framework with App Router
- **Radix UI**: Accessible component library
- **Tailwind CSS**: Utility-first CSS framework
- **React Hook Form + Zod**: Form handling and validation
- **TanStack Query**: Data fetching and caching
- **React PDF**: PDF viewing capabilities
- **Socket.io**: Real-time communication

## Development Workflow
1. Use `docker-compose up` for local development
2. Backend runs on port 8000, frontend on port 3000
3. Database migrations handled by Alembic
4. Background tasks processed by Celery workers
5. File uploads stored in MinIO (port 9000)

## Testing Strategy
- **Backend**: pytest with async support and coverage
- **Frontend**: Jest + Testing Library for unit/integration tests
- **E2E**: Consider Playwright for end-to-end testing

## Security & Compliance
- JWT-based authentication with secure session management
- Role-based access control (RBAC)
- Data encryption at rest and in transit
- Comprehensive audit logging
- GDPR/CCPA compliance considerations
- Legal-grade document security and retention

## AI Integration Points
1. **Document Summarization**: Automatic summaries of legal documents
2. **Key Clause Extraction**: Identify important contractual terms
3. **Risk Assessment**: AI-powered risk analysis of contracts
4. **Legal Research**: AI-assisted case law and statute research
5. **Citation Verification**: Automated validation of legal citations
6. **Document Classification**: Categorize documents by type and relevance

## Environment Configuration
- Development: Docker Compose with hot reload
- Production: Kubernetes deployment with proper secrets management
- Environment variables configured via .env files
- Separate configs for different deployment stages

## Commands for Development
- `npm run dev`: Start Next.js development server
- `uvicorn main:app --reload`: Start FastAPI development server
- `docker-compose up`: Start all services locally
- `npm run lint`: Run linting checks
- `npm run typecheck`: Run TypeScript checks
- `pytest`: Run backend tests
- `npm test`: Run frontend tests

## API Documentation
- FastAPI automatically generates OpenAPI/Swagger docs at `/docs`
- Authentication required for most endpoints
- RESTful API design with consistent response formats
- WebSocket support for real-time features

## Database Schema
- **Users**: Authentication and profile information
- **Clients**: Client management and relationship data
- **Documents**: Document metadata and processing status
- **Cases**: Case management and document associations
- **Audit Logs**: Comprehensive activity tracking
- **AI Analyses**: Stored AI analysis results and metadata

## Deployment Notes
- Use environment-specific Docker images
- Implement proper logging and monitoring
- Configure SSL/TLS certificates
- Set up database backups and disaster recovery
- Monitor AI API usage and costs
- Implement rate limiting for API endpoints

## Development Standards (User Preferences)

### Systematic Code Fixing Approach
When fixing or writing code:
1. **Understand the full application** - Don't make isolated fixes; understand how the change affects the entire system
2. **Trace every code path** - Follow each execution path to understand the complete flow
3. **Test each path systematically** - Verify every branch, condition, and edge case works correctly
4. **Anticipate failures** - Proactively identify potential failure points before they become bugs
5. **Fix comprehensively** - When a bug is found, check for similar issues in related code paths
6. **Verify 100% operation** - Don't consider a fix complete until the entire feature/flow is confirmed working end-to-end

**Goal**: Every fix should leave the app at 100% operational status, not just patch the immediate symptom.

### Test After Implementation
After implementing any fix or new function:
1. **Run the relevant code** - Execute the function/endpoint/component to verify it works
2. **Test edge cases** - Check boundary conditions and error scenarios
3. **Confirm success before reporting** - Only report completion after verifying the fix works
4. **Reduce back-and-forth** - Catch issues proactively rather than waiting for user feedback

**Goal**: Minimize iteration cycles by validating changes work correctly before presenting them as complete.

### Process Safety
When killing ports or processes:
1. **Never kill Node processes running on port 3000** - This is likely the Claude Code terminal
2. **Be specific with process termination** - Target exact PIDs rather than broad process names
3. **Avoid `taskkill /F /IM node.exe`** - This kills ALL Node processes including Claude Code itself
4. **Use port-specific kills** - Prefer `npx kill-port <port>` for targeted termination

**Goal**: Avoid self-termination loops that disrupt the development session.

### API Key & Secrets Security (CRITICAL)
Before writing or pushing ANY code:
1. **NEVER hard-code API keys** - No API keys, tokens, or secrets directly in source code
2. **NEVER expose secrets in frontend code** - Client-side code is always visible to users
3. **Use environment variables** - All secrets must come from `.env` files or environment variables
4. **Check before committing** - Scan all changes for accidentally included secrets before any git commit
5. **Use `.env.example` templates** - Provide example files with placeholder values, never real keys
6. **Validate `.gitignore`** - Ensure `.env`, `*.key`, `credentials.json`, and similar files are ignored
7. **Server-side only for secrets** - API calls requiring keys must go through backend, never frontend
8. **Rotate if exposed** - If a key is ever committed, treat it as compromised and rotate immediately

**Security Checklist Before Every Push:**
- [ ] No API keys or tokens in code
- [ ] No passwords or secrets hard-coded
- [ ] `.env` files are gitignored
- [ ] Frontend doesn't contain sensitive keys
- [ ] No secrets in console.log or error messages
- [ ] No credentials in comments or documentation

**Goal**: Zero secrets exposure - every deployment must maintain complete security integrity.