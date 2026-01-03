# AI Continuous Learning System

## Overview

The Legal AI System includes a comprehensive continuous learning infrastructure that enables AI agents to improve their performance over time through user feedback, knowledge accumulation, and performance tracking.

## Architecture

The learning system consists of six main components:

### 1. Feedback Collection
Captures user feedback on AI-generated responses to identify what works and what doesn't.

### 2. Knowledge Base (RAG)
Stores successful patterns and analyses that can be retrieved to inform future responses.

### 3. Performance Metrics
Tracks quantitative performance measures over time to identify improvement trends.

### 4. Document Similarity
Pre-computes document similarities to find relevant precedents and examples.

### 5. User Preferences
Learns user and firm-specific preferences for personalized responses.

### 6. Learning Tasks
Manages automated improvement tasks like fine-tuning and prompt optimization.

## Database Models

### AIFeedback
Stores user feedback on AI responses:
- **user_rating**: 1-5 star rating
- **was_helpful**: Boolean flag
- **was_accurate**: Boolean flag
- **feedback_text**: Free-form comments
- **corrected_response**: User's correction if response was wrong
- **confidence_score**: AI's confidence in its response
- **processing_time_ms**: Response latency
- **token_count**: Tokens used
- **cost_usd**: API cost

### DocumentKnowledge
Knowledge base for successful analyses:
- **knowledge_type**: pattern, precedent, clause, citation, etc.
- **content**: Full knowledge content
- **embedding**: Vector embedding for similarity search (planned)
- **usage_count**: How many times this knowledge was used
- **success_rate**: How often it led to good results
- **avg_user_rating**: Average user rating

### PerformanceMetric
Tracks AI model performance over time:
- **metric_type**: accuracy, precision, recall, f1, etc.
- **task_type**: classification, extraction, analysis, etc.
- **value**: The metric value
- **sample_size**: Number of samples
- **measured_at**: Timestamp

### UserPreference
Learns user/firm preferences:
- **preference_type**: citation_style, analysis_depth, etc.
- **preference_value**: The preference value
- **confidence**: Confidence in this preference (0-1)
- **evidence_count**: Number of examples supporting this

### DocumentSimilarity
Pre-computed document similarities:
- **similarity_score**: 0.0 to 1.0
- **similarity_type**: semantic, structural, citation_based, etc.
- **common_features**: Shared features

### LearningTask
Manages improvement tasks:
- **task_type**: fine_tune, prompt_optimization, knowledge_update
- **status**: pending, running, completed, failed
- **improvement_percentage**: Performance gain
- **baseline_score / new_score**: Before/after metrics

## API Endpoints

### Feedback Endpoints

#### Submit Feedback
```http
POST /api/v1/learning/feedback
Content-Type: application/json

{
  "session_id": "session-uuid",
  "request_type": "document_analysis",
  "model_used": "claude-3-5-sonnet",
  "response_text": "AI's response text",
  "user_rating": 5,
  "was_helpful": true,
  "was_accurate": true,
  "feedback_text": "Great analysis!",
  "confidence_score": 0.95,
  "processing_time_ms": 1500,
  "token_count": 250,
  "cost_usd": 0.015,
  "prompt_version": "1.0"
}

Response:
{
  "id": 1,
  "message": "Feedback recorded successfully",
  "knowledge_extracted": true
}
```

**Note**: Feedback with rating >= 4 and was_accurate=true automatically extracts knowledge.

#### Get Feedback Statistics
```http
GET /api/v1/learning/feedback/stats?request_type=document_analysis&days=30

Response:
{
  "total_feedback": 150,
  "average_rating": 4.5,
  "helpful_percentage": 92.0,
  "accurate_percentage": 88.0,
  "period_days": 30
}
```

### Knowledge Base Endpoints

#### Search Knowledge
```http
POST /api/v1/learning/knowledge/search
Content-Type: application/json

{
  "query": "NDA confidentiality clause",
  "knowledge_type": "clause",
  "document_type": "contract",
  "jurisdiction": "California",
  "limit": 10
}

Response:
[
  {
    "id": 1,
    "knowledge_type": "clause",
    "title": "Standard NDA Confidentiality Clause",
    "content": "Full clause text...",
    "document_type": "contract",
    "jurisdiction": "California",
    "usage_count": 45,
    "success_rate": 0.95,
    "avg_user_rating": 4.7
  }
]
```

#### Find Similar Documents
```http
GET /api/v1/learning/knowledge/{document_id}/similar?min_similarity=0.7&limit=5

Response:
[
  {
    "document_id": "doc-uuid-2",
    "file_name": "similar_contract.pdf",
    "document_type": "NDA",
    "similarity_score": 0.85,
    "summary": "Similar NDA with comparable terms..."
  }
]
```

### Performance Tracking Endpoints

#### Get Performance Trends
```http
POST /api/v1/learning/performance/trends
Content-Type: application/json

{
  "metric_type": "accuracy",
  "task_type": "document_classification",
  "model_name": "claude-3-5-sonnet",
  "days": 30
}

Response:
[
  {
    "date": "2025-10-01T00:00:00",
    "value": 0.82,
    "sample_size": 50
  },
  {
    "date": "2025-10-15T00:00:00",
    "value": 0.87,
    "sample_size": 75
  }
]
```

#### Calculate Improvement
```http
POST /api/v1/learning/performance/improvement
Content-Type: application/json

{
  "metric_type": "accuracy",
  "task_type": "document_classification",
  "model_name": "claude-3-5-sonnet",
  "days": 30
}

Response:
{
  "baseline": 0.82,
  "current": 0.87,
  "improvement_pct": 6.1,
  "trend": "improving",
  "data_points": 15
}
```

### Preference Learning Endpoints

#### Learn Preference
```http
POST /api/v1/learning/preferences/learn
Content-Type: application/json

{
  "user_id": "user-123",
  "firm_id": "firm-456",
  "preference_type": "citation_style",
  "preference_key": "preferred_citation_format",
  "preference_value": "Bluebook",
  "confidence": 0.8
}

Response:
{
  "id": 1,
  "message": "Preference learned",
  "confidence": 0.8,
  "evidence_count": 1
}
```

#### Get Preferences
```http
GET /api/v1/learning/preferences?user_id=user-123&preference_type=citation_style

Response:
[
  {
    "id": 1,
    "preference_type": "citation_style",
    "preference_key": "preferred_citation_format",
    "preference_value": "Bluebook",
    "confidence": 0.9,
    "evidence_count": 5
  }
]
```

### System Statistics

#### Get Learning Statistics
```http
GET /api/v1/learning/stats

Response:
{
  "total_feedback_items": 1250,
  "average_user_rating": 4.3,
  "total_knowledge_items": 450,
  "total_performance_metrics": 75,
  "rating_distribution": {
    "1": 15,
    "2": 30,
    "3": 125,
    "4": 450,
    "5": 630
  },
  "top_request_types": [
    {"type": "document_analysis", "count": 500},
    {"type": "contract_review", "count": 350}
  ],
  "learning_status": "active"
}
```

#### Health Check
```http
GET /api/v1/learning/health

Response:
{
  "status": "healthy",
  "learning_active": true,
  "total_data_points": 1775
}
```

## Integration Guide

### Automatic Feedback Collection

Integrate feedback collection into your existing AI endpoints:

```python
from app.src.services.learning_service import get_learning_service

async def analyze_document(document_id: str, db: Session):
    # Your existing analysis logic
    response = await ai_service.analyze(document_id)

    # Record feedback automatically
    learning_service = get_learning_service(db)
    learning_service.record_feedback(
        document_id=document_id,
        session_id=session_id,
        request_type="document_analysis",
        model_used="claude-3-5-sonnet",
        response_text=response.text,
        user_rating=5,  # Can be set by user later
        confidence_score=response.confidence,
        processing_time_ms=response.latency_ms,
        token_count=response.token_count,
        cost_usd=response.cost
    )

    return response
```

### Knowledge Retrieval (RAG)

Enhance responses with relevant past knowledge:

```python
async def generate_response(query: str, context: str, db: Session):
    # Search knowledge base for relevant information
    learning_service = get_learning_service(db)
    knowledge_items = learning_service.search_knowledge(
        query=query,
        knowledge_type="successful_response",
        limit=5
    )

    # Build enhanced context with past knowledge
    enhanced_context = context
    if knowledge_items:
        enhanced_context += "\n\nRelevant past analyses:\n"
        for item in knowledge_items:
            enhanced_context += f"- {item.content}\n"

    # Generate response with enhanced context
    response = await ai_service.generate(enhanced_context)
    return response
```

### Performance Tracking

Track metrics after batch processing:

```python
async def process_document_batch(documents: List[Document], db: Session):
    results = []
    correct_count = 0
    total_count = len(documents)

    for doc in documents:
        result = await classify_document(doc)
        results.append(result)
        if result.is_correct:
            correct_count += 1

    # Track performance metric
    learning_service = get_learning_service(db)
    accuracy = correct_count / total_count

    learning_service.track_performance(
        metric_type="accuracy",
        task_type="document_classification",
        model_name="claude-3-5-sonnet",
        value=accuracy,
        sample_size=total_count
    )

    return results
```

## Production Enhancements

### 1. Vector Embeddings for Knowledge Search

Current implementation uses simple text search. For production:

```python
# Generate embeddings for knowledge items
from openai import OpenAI

client = OpenAI()

def add_knowledge_with_embedding(knowledge_item):
    # Generate embedding
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=knowledge_item.content
    )

    knowledge_item.embedding = response.data[0].embedding
    db.add(knowledge_item)
    db.commit()

# Search using vector similarity
def search_knowledge_vector(query: str, limit: int = 10):
    # Generate query embedding
    query_embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    # Use pgvector or similar for similarity search
    # This requires PostgreSQL with pgvector extension
    results = db.execute("""
        SELECT *,
               1 - (embedding <=> :query_embedding) as similarity
        FROM document_knowledge
        ORDER BY similarity DESC
        LIMIT :limit
    """, {"query_embedding": query_embedding, "limit": limit})

    return results
```

### 2. Automated Learning Pipeline

Set up automated learning tasks:

```python
from celery import Celery

app = Celery('learning')

@app.task
def daily_learning_pipeline():
    """
    Daily task to:
    1. Analyze feedback from past 24 hours
    2. Extract knowledge from highly-rated responses
    3. Calculate performance metrics
    4. Identify areas for improvement
    """
    db = get_db()
    learning_service = get_learning_service(db)

    # Get recent feedback
    cutoff = datetime.utcnow() - timedelta(days=1)
    recent_feedback = db.query(AIFeedback).filter(
        AIFeedback.created_at >= cutoff,
        AIFeedback.user_rating >= 4
    ).all()

    # Extract knowledge
    for feedback in recent_feedback:
        learning_service._extract_knowledge_from_feedback(feedback)

    # Calculate daily metrics
    # ... metric calculation logic

    logger.info(f"Daily learning pipeline: Processed {len(recent_feedback)} items")
```

### 3. Model Fine-tuning Preparation

Export training data for fine-tuning:

```python
def export_training_data(output_file: str, min_rating: int = 4):
    """
    Export feedback as JSONL for fine-tuning.
    Format compatible with OpenAI/Anthropic fine-tuning APIs.
    """
    feedback_items = db.query(AIFeedback).filter(
        AIFeedback.user_rating >= min_rating,
        AIFeedback.was_accurate == True
    ).all()

    with open(output_file, 'w') as f:
        for item in feedback_items:
            training_example = {
                "messages": [
                    {"role": "user", "content": item.request_context},
                    {"role": "assistant", "content": item.response_text}
                ]
            }
            f.write(json.dumps(training_example) + '\n')

    logger.info(f"Exported {len(feedback_items)} training examples to {output_file}")
```

## Best Practices

### 1. Feedback Collection
- Collect feedback immediately after AI responses
- Make feedback submission easy and non-intrusive
- Incentivize users to provide corrections for wrong responses
- Track confidence scores to identify uncertain predictions

### 2. Knowledge Management
- Regularly review and curate knowledge base
- Remove outdated or incorrect knowledge
- Tag knowledge with metadata for better retrieval
- Implement version control for knowledge items

### 3. Performance Monitoring
- Set up automated alerts for performance degradation
- Track metrics by category (document type, jurisdiction, etc.)
- Compare performance across different models
- Monitor cost and latency alongside accuracy

### 4. Privacy and Security
- Never store sensitive client information in feedback
- Anonymize data before using for training
- Implement proper access controls for learning data
- Comply with data retention policies

## Monitoring and Alerts

Set up monitoring for the learning system:

```python
# Example: Alert on low performance
def check_performance_alerts():
    learning_service = get_learning_service(db)

    # Check recent accuracy
    improvement = learning_service.calculate_improvement(
        metric_type="accuracy",
        task_type="document_classification",
        model_name="claude-3-5-sonnet",
        days=7
    )

    if improvement["current"] < 0.80:
        send_alert(
            severity="warning",
            message=f"Classification accuracy dropped to {improvement['current']:.2%}"
        )

    if improvement["trend"] == "declining":
        send_alert(
            severity="info",
            message=f"Performance declining: {improvement['improvement_pct']:.1f}%"
        )
```

## Future Enhancements

1. **Active Learning**: Identify uncertain predictions and request user feedback
2. **A/B Testing**: Compare different prompts and models systematically
3. **Federated Learning**: Learn from multiple firms without sharing data
4. **Explainable AI**: Track which knowledge items influenced responses
5. **Automated Prompt Engineering**: Optimize prompts based on performance data

## API Reference

Full API documentation available at: `http://localhost:8000/docs#tag/Learning-&-Improvement`

Interactive testing: `http://localhost:8000/docs`

## Support

For questions or issues with the learning system:
- Check logs: `backend/logs/learning.log`
- Database: `backend/legal_ai.db` (tables: ai_feedback, document_knowledge, performance_metrics, etc.)
- Health check: `GET /api/v1/learning/health`
