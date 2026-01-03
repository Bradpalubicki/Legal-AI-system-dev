# Legal AI System

**IMPORTANT DISCLAIMER**: This system provides information for educational purposes only and does not constitute legal advice. All content is for informational purposes only and should not be relied upon for making legal decisions. Please consult with a qualified attorney for specific legal matters.

A comprehensive AI-powered legal document analysis and research system designed to assist legal professionals with document review, case research, and legal analysis tasks.

## Features

- 🤖 **AI-Powered Document Analysis**: Advanced document summarization and key clause extraction
- 📚 **Legal Research Integration**: Connect with Westlaw, LexisNexis, and CourtListener APIs
- 📄 **Multi-Format Support**: Process PDF, DOCX, TXT, and RTF documents
- 🔍 **Citation Processing**: Automatic extraction and validation of legal citations
- 👥 **Client Management**: Secure client portal with document sharing capabilities
- 📊 **Compliance & Audit**: Full audit trails and data retention policies
- 🔒 **Enterprise Security**: Role-based access control and data encryption

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and session storage
- **Celery** - Background task processing
- **SQLAlchemy** - Database ORM

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Accessible components
- **TanStack Query** - Data fetching and caching

### AI & ML
- **OpenAI GPT-4** - Document analysis and research
- **Anthropic Claude** - Legal reasoning and analysis
- **SpaCy/NLTK** - Natural language processing
- **Transformers** - Local model support

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.9+ (for local development)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd legal-ai-system
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your configuration:

```bash
# Required: Add your AI API keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Database (defaults work for Docker)
DATABASE_URL=postgresql://legalai:legalai_password@localhost:5432/legal_ai_db

# Redis
REDIS_URL=redis://localhost:6379

# Security (generate secure keys for production)
JWT_SECRET=your-super-secret-jwt-key
SESSION_SECRET=your-session-secret-key
ENCRYPTION_KEY=your-32-character-encryption-key
```

### 3. Start with Docker

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database Admin**: Connect to `localhost:5432`
- **Redis**: localhost:6379
- **File Storage (MinIO)**: http://localhost:9001
- **Task Monitor (Flower)**: http://localhost:5555

## Development Setup

### Backend Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload --port 8000
```

### Frontend Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Run in development mode with hot reload
npm run dev -- --port 3000
```

### Running Tests

```bash
# Backend tests
pytest

# Frontend tests
npm test

# Run with coverage
pytest --cov=app
npm run test:coverage
```

## API Documentation

The API is automatically documented using FastAPI's built-in OpenAPI support:

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:

```bash
Authorization: Bearer <your-jwt-token>
```

## Database Management

### Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade (if needed)
alembic downgrade -1
```

### Seeding Data

```bash
# Run database seeds
python scripts/seed_database.py
```

## Deployment

### Production Environment

1. **Environment Variables**: Set production values in `.env`
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service
4. **File Storage**: Configure AWS S3 or compatible service
5. **Monitoring**: Set up Sentry for error tracking

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=legal-ai-system
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for complete list):

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude
- `JWT_SECRET` - Secret key for JWT tokens
- `SENTRY_DSN` - Sentry error tracking DSN

### File Storage

Configure file storage backend:

- **Local**: Files stored in `./storage` directory
- **S3**: Configure AWS credentials and bucket
- **MinIO**: S3-compatible local storage (development)

## Security

### Best Practices

- All API endpoints require authentication (except public routes)
- JWT tokens expire after 7 days by default
- Passwords are hashed using bcrypt
- File uploads are validated for type and size
- SQL injection protection via SQLAlchemy ORM
- XSS protection enabled

### Compliance

- **GDPR**: Data retention policies and user data export
- **Legal Requirements**: Audit trails and document retention
- **Security**: Encryption at rest and in transit

## Monitoring

### Application Monitoring

- **Logs**: Structured logging with timestamps
- **Metrics**: API response times and error rates
- **Health Checks**: `/health` endpoint for service monitoring
- **Background Tasks**: Monitor via Flower dashboard

### Error Tracking

Configure Sentry for production error tracking:

```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

## Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for all frontend code
- Write tests for new features
- Update documentation for API changes
- Use conventional commits for commit messages

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support:

- **Documentation**: See `/docs` directory
- **Issues**: Open a GitHub issue
- **API Questions**: Check the interactive docs at `/docs`

## Roadmap

- [ ] Advanced contract analysis features
- [ ] Integration with more legal databases
- [ ] Mobile application
- [ ] Advanced workflow automation
- [ ] Multi-language document support
- [ ] Enhanced AI model fine-tuning