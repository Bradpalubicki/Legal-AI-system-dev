# Unified Legal Database Search System

A comprehensive unified search interface that provides seamless access to multiple legal databases including commercial providers, free resources, government databases, and specialized legal collections.

## Features

### Comprehensive Database Coverage
- **Free/Public Sources**:
  - CourtListener - Federal and state case law, dockets, oral arguments
  - Google Scholar Legal - Academic legal research and case law
  - Justia - Free legal information and documents
  
- **Government Databases**:
  - GovInfo - Federal documents, regulations, CFR
  - Congress.gov - Legislative information and Congressional materials
  - SupremeCourt.gov - Supreme Court opinions and documents
  
- **Premium Sources** (with credentials):
  - HeinOnline - Law reviews, treaties, legislative history
  - Westlaw - Commercial legal database (via research_integration)
  - LexisNexis - Commercial legal database (via research_integration)

### Advanced Search Capabilities
- **Query Types**: Natural language, Boolean, citation search, field search
- **Content Filtering**: Cases, statutes, regulations, law reviews, etc.
- **Jurisdictional Filtering**: Federal, state, local, international
- **Temporal Filtering**: Date ranges, decision dates, publication dates
- **Quality Filters**: Authority scores, reliability thresholds, full-text requirements

### Intelligent Result Processing
- **Advanced Deduplication**: Multi-factor similarity detection
- **Sophisticated Ranking**: Relevance, authority, recency, completeness
- **Result Fusion**: Weighted combination from multiple sources
- **Diversity Optimization**: Balanced results across providers and jurisdictions

## Quick Start

### Basic Usage

```python
from unified_search import SearchOrchestrator, UnifiedQuery

# Initialize orchestrator
orchestrator = SearchOrchestrator()
await orchestrator.initialize()

# Create search query
query = UnifiedQuery(
    query_text="contract breach damages",
    max_results=50,
    content_types=[ContentType.CASES],
    jurisdictions=["federal", "california"]
)

# Execute search
result = await orchestrator.search(query)

print(f"Found {result.total_results} results across {len(result.providers_searched)} providers")
for doc in result.documents:
    print(f"- {doc.title} ({doc.source_provider.value})")
```

### API Usage

```python
from fastapi import FastAPI
from unified_search import unified_search_router

app = FastAPI()
app.include_router(unified_search_router)

# Start server: uvicorn main:app --reload
# Access API docs: http://localhost:8000/docs
```

### API Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/unified-search/search" \
     -H "Content-Type: application/json" \
     -d '{
       "query_text": "constitutional due process",
       "content_types": ["cases"],
       "jurisdictions": ["federal"],
       "max_results": 25,
       "free_sources_only": true,
       "sort_by": "relevance"
     }'
```

## Configuration

### Provider Credentials

```python
from unified_search.providers import (
    CourtListenerCredentials, HeinOnlineCredentials, GovernmentCredentials
)

# Optional API keys for enhanced access
credentials = {
    "courtlistener": CourtListenerCredentials(api_key="your_key"),
    "heinonline": HeinOnlineCredentials(
        api_key="your_key",
        username="your_username", 
        password="your_password"
    ),
    "government": GovernmentCredentials(
        govinfo_api_key="your_govinfo_key",
        congress_api_key="your_congress_key"
    )
}

orchestrator = SearchOrchestrator(**credentials)
```

### Custom Search Strategies

```python
from unified_search import SearchStrategy, DatabaseProvider

# Define custom search strategy
strategy = SearchStrategy(
    strategy_id="academic_research",
    name="Academic Research Strategy",
    description="Optimized for academic legal research",
    provider_priorities={
        DatabaseProvider.HEINONLINE: 95,
        DatabaseProvider.GOOGLE_SCHOLAR: 90,
        DatabaseProvider.COURTLISTENER: 85
    },
    max_providers=5,
    diversity_weight=0.2,
    min_relevance_score=0.4,
    prefer_free_sources=True
)

# Use custom strategy
result = await orchestrator.search(query, strategy)
```

## Database Models

### UnifiedQuery
Main search query model with comprehensive filtering options:

```python
query = UnifiedQuery(
    query_text="search terms",
    query_type="natural_language",  # or "boolean", "citation", "field"
    
    # Content filters
    content_types=[ContentType.CASES, ContentType.STATUTES],
    jurisdictions=["federal", "california"],
    courts=["Supreme Court", "9th Circuit"],
    
    # Date filters  
    date_from=date(2020, 1, 1),
    date_to=date.today(),
    
    # Advanced options
    case_law_only=False,
    primary_law_only=False,
    free_sources_only=True,
    max_results=100,
    sort_by="relevance",  # or "date", "jurisdiction", "court"
    
    # Quality requirements
    min_reliability_score=0.5,
    require_full_text=False,
    
    # Provider preferences
    preferred_providers=[DatabaseProvider.COURTLISTENER],
    exclude_providers=[DatabaseProvider.HEINONLINE]
)
```

### UnifiedDocument
Standardized document model across all providers:

```python
# Access document properties
doc = result.documents[0]
print(f"Title: {doc.title}")
print(f"Court: {doc.court}")  
print(f"Citation: {doc.citation}")
print(f"Decision Date: {doc.decision_date}")
print(f"Authority Score: {doc.authority_score}")
print(f"Full Text Available: {doc.full_text_available}")
print(f"Free Access: {doc.is_free_access}")
```

## Architecture

### Core Components

1. **SearchOrchestrator**: Main coordination engine
2. **ResultFusionEngine**: Advanced result processing and ranking
3. **Provider Clients**: Individual database integrations
4. **Database Models**: Unified data structures
5. **API Router**: REST API endpoints

### Search Flow

1. **Query Processing**: Parse and validate search parameters
2. **Provider Selection**: Choose optimal databases based on query and strategy
3. **Parallel Execution**: Search multiple providers concurrently
4. **Result Collection**: Gather results from all providers
5. **Deduplication**: Remove similar documents using advanced algorithms
6. **Relevance Enhancement**: Improve scoring using legal context
7. **Authority Scoring**: Evaluate document authority and precedential value
8. **Result Fusion**: Combine and rank results from all sources
9. **Diversity Optimization**: Balance results across sources and jurisdictions

### Advanced Features

#### Similarity Detection
- Title and content similarity
- Citation matching and normalization
- Court and date correlation
- Legal topic alignment

#### Legal Context Analysis
- Practice area detection
- Document type classification
- Jurisdictional relevance
- Precedential value assessment

#### Quality Metrics
- Relevance scoring with legal term weighting
- Authority scoring based on court hierarchy
- Recency scoring with legal longevity factors
- Completeness scoring for metadata richness

## API Endpoints

### Search Operations
- `POST /api/v1/unified-search/search` - Execute unified search
- `GET /api/v1/unified-search/document/{provider}/{id}` - Get document details
- `GET /api/v1/unified-search/suggestions/query` - Get query suggestions

### Administration  
- `GET /api/v1/unified-search/providers/status` - Provider health status
- `POST /api/v1/unified-search/strategies` - Create custom search strategy
- `GET /api/v1/unified-search/strategies` - List search strategies

### Analytics
- `GET /api/v1/unified-search/analytics/search-metrics` - Search analytics
- `GET /api/v1/unified-search/health` - Service health check

## Performance Considerations

### Rate Limiting
Each provider implements respectful rate limiting:
- CourtListener: 100 req/min
- Google Scholar: 10 req/min (conservative)
- Justia: 30 req/min
- Government APIs: 100-120 req/min

### Caching
- Result caching for identical queries
- Provider-specific caching strategies
- Intelligent cache invalidation

### Parallel Processing
- Concurrent provider searches
- Configurable timeouts per provider
- Graceful degradation on provider failures

## Legal Compliance

### Terms of Service
- Compliant with each provider's ToS
- Respectful usage patterns
- Appropriate attribution

### Rate Limiting
- Conservative default limits
- Configurable per provider
- Automatic backoff on errors

### Data Usage
- Read-only access to public legal information
- No redistribution of proprietary content
- Proper citation and attribution

## Development

### Adding New Providers

1. Create provider client in `providers/` directory
2. Implement required interface methods
3. Add provider to `DatabaseProvider` enum
4. Update orchestrator provider mapping
5. Add configuration options

### Testing

```bash
# Run unit tests
pytest src/unified_search/tests/

# Run integration tests with live APIs (requires credentials)
pytest src/unified_search/tests/ --integration
```

### Contributing

1. Fork the repository
2. Create feature branch
3. Implement changes with tests
4. Update documentation
5. Submit pull request

## Troubleshooting

### Common Issues

**Provider Connection Failures**
- Check API credentials
- Verify network connectivity
- Review rate limit settings

**Poor Search Results**
- Adjust relevance thresholds
- Modify provider priorities
- Refine search queries

**Performance Issues** 
- Reduce max results per provider
- Adjust timeout settings
- Enable result caching

### Monitoring

The system provides comprehensive logging and metrics:
- Request/response times per provider
- Success/failure rates
- Query performance analytics
- Cost tracking for premium providers

## License

This unified search system is part of the Legal AI System and follows the same licensing terms. Individual database providers may have their own terms of service that must be respected.