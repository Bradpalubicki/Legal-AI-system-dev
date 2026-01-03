# Bulk Document Processing Guide

## Overview

The Legal AI System can now handle **hundreds of documents** sequentially without confusion using the new batch processing system. This guide explains how to upload and process large document collections efficiently.

## Current Answer: YES, With Batch Processing ✅

With the batch processing endpoints, you can:
- Upload **up to 500 documents per batch**
- Process **3 documents concurrently** to avoid API rate limits
- Track **real-time progress** of your bulk upload
- Retrieve **individual results** for each document
- Handle **failures gracefully** without losing successful uploads

## How It Works

### 1. Upload Documents (Returns Immediately)

```http
POST /api/v1/batch/upload
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf, ..., file100.pdf]
session_id: optional-session-uuid
```

**Response (Immediate)**:
```json
{
  "success": true,
  "job_id": "batch-uuid-12345",
  "session_id": "session-uuid-67890",
  "total_documents": 100,
  "status": "processing",
  "message": "Batch processing started in background",
  "estimated_completion_seconds": 500,
  "check_status_url": "/api/v1/batch/status/batch-uuid-12345"
}
```

### 2. Poll For Progress

```http
GET /api/v1/batch/status/{job_id}
```

**Response**:
```json
{
  "job_id": "batch-uuid-12345",
  "session_id": "session-uuid-67890",
  "status": "processing",
  "total_documents": 100,
  "processed_documents": 45,
  "successful_documents": 43,
  "failed_documents": 2,
  "started_at": "2025-10-17T18:30:00Z",
  "completed_at": null,
  "progress_percentage": 45.0,
  "estimated_time_remaining": 275,
  "errors": [
    {
      "filename": "corrupted.pdf",
      "error": "Invalid PDF file"
    }
  ]
}
```

### 3. Get Final Results

```http
GET /api/v1/batch/result/{job_id}
```

**Response** (when status = "completed"):
```json
{
  "job_id": "batch-uuid-12345",
  "session_id": "session-uuid-67890",
  "total_documents": 100,
  "successful_count": 98,
  "failed_count": 2,
  "processing_time_seconds": 487.3,
  "documents": [
    {
      "document_id": "doc-uuid-1",
      "filename": "contract_001.pdf",
      "status": "success",
      "summary": "Standard NDA with non-compete clause...",
      "document_type": "Non-Disclosure Agreement",
      "error": null,
      "processed_at": "2025-10-17T18:31:15Z"
    },
    {
      "document_id": "doc-uuid-2",
      "filename": "contract_002.pdf",
      "status": "success",
      "summary": "Employment agreement for software engineer...",
      "document_type": "Employment Contract",
      "error": null,
      "processed_at": "2025-10-17T18:31:22Z"
    },
    {
      "document_id": null,
      "filename": "corrupted.pdf",
      "status": "failed",
      "summary": null,
      "document_type": null,
      "error": "Invalid PDF file",
      "processed_at": "2025-10-17T18:31:05Z"
    }
  ]
}
```

## Usage Examples

### Python Example

```python
import requests
import time
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000"
DOCUMENTS_DIR = Path("./legal_documents")

# Step 1: Prepare documents
pdf_files = list(DOCUMENTS_DIR.glob("*.pdf"))
print(f"Found {len(pdf_files)} PDF files")

# Step 2: Upload batch
files = [
    ('files', (pdf.name, open(pdf, 'rb'), 'application/pdf'))
    for pdf in pdf_files
]

response = requests.post(
    f"{API_BASE}/api/v1/batch/upload",
    files=files
)

result = response.json()
job_id = result['job_id']
session_id = result['session_id']

print(f"Batch upload started: {job_id}")
print(f"Estimated completion: {result['estimated_completion_seconds']}s")

# Step 3: Poll for progress
while True:
    status_response = requests.get(
        f"{API_BASE}/api/v1/batch/status/{job_id}"
    )
    status = status_response.json()

    print(f"Progress: {status['progress_percentage']:.1f}% "
          f"({status['processed_documents']}/{status['total_documents']})")

    if status['status'] == 'completed':
        print("Batch processing completed!")
        break
    elif status['status'] == 'failed':
        print("Batch processing failed!")
        break

    time.sleep(5)  # Poll every 5 seconds

# Step 4: Get final results
results_response = requests.get(
    f"{API_BASE}/api/v1/batch/result/{job_id}"
)
results = results_response.json()

print(f"\n=== Results ===")
print(f"Successful: {results['successful_count']}")
print(f"Failed: {results['failed_count']}")
print(f"Processing time: {results['processing_time_seconds']:.1f}s")

# Process individual documents
for doc in results['documents']:
    if doc['status'] == 'success':
        print(f"✓ {doc['filename']}: {doc['document_type']}")
    else:
        print(f"✗ {doc['filename']}: {doc['error']}")

# Step 5: Retrieve all documents from session
session_response = requests.get(
    f"{API_BASE}/api/v1/documents/session/{session_id}"
)
session_docs = session_response.json()
print(f"\nTotal documents in session: {session_docs['document_count']}")
```

### JavaScript Example

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const API_BASE = 'http://localhost:8000';

async function batchUploadDocuments(filePaths) {
  // Step 1: Create form data with multiple files
  const formData = new FormData();
  filePaths.forEach(filePath => {
    formData.append('files', fs.createReadStream(filePath));
  });

  // Step 2: Upload batch
  const uploadResponse = await axios.post(
    `${API_BASE}/api/v1/batch/upload`,
    formData,
    { headers: formData.getHeaders() }
  );

  const { job_id, session_id } = uploadResponse.data;
  console.log(`Batch upload started: ${job_id}`);

  // Step 3: Poll for completion
  let status = 'processing';
  while (status === 'processing') {
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5s

    const statusResponse = await axios.get(
      `${API_BASE}/api/v1/batch/status/${job_id}`
    );

    const statusData = statusResponse.data;
    console.log(`Progress: ${statusData.progress_percentage}%`);

    status = statusData.status;
  }

  // Step 4: Get results
  const resultsResponse = await axios.get(
    `${API_BASE}/api/v1/batch/result/${job_id}`
  );

  return {
    job_id,
    session_id,
    results: resultsResponse.data
  };
}

// Usage
const files = [
  '/path/to/contract1.pdf',
  '/path/to/contract2.pdf',
  // ... up to 500 files
];

batchUploadDocuments(files)
  .then(({ results }) => {
    console.log(`Success: ${results.successful_count}`);
    console.log(`Failed: ${results.failed_count}`);
  })
  .catch(console.error);
```

### cURL Example

```bash
#!/bin/bash

# Upload batch
RESPONSE=$(curl -X POST http://localhost:8000/api/v1/batch/upload \
  -F "files=@document1.pdf" \
  -F "files=@document2.pdf" \
  -F "files=@document3.pdf" \
  # ... add more files
)

JOB_ID=$(echo $RESPONSE | jq -r '.job_id')
echo "Job ID: $JOB_ID"

# Poll for status
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/batch/status/$JOB_ID)
  PROGRESS=$(echo $STATUS | jq -r '.progress_percentage')
  STATE=$(echo $STATUS | jq -r '.status')

  echo "Progress: $PROGRESS%"

  if [ "$STATE" = "completed" ]; then
    echo "Completed!"
    break
  fi

  sleep 5
done

# Get results
curl -s http://localhost:8000/api/v1/batch/result/$JOB_ID | jq '.'
```

## API Reference

### POST /api/v1/batch/upload

**Purpose**: Upload multiple documents for background processing

**Parameters**:
- `files` (required): Array of PDF files (max 500)
- `session_id` (optional): Session identifier (generated if not provided)

**Limits**:
- Max documents: 500 per batch
- Max total size: 100 MB per batch
- File types: PDF only

**Returns**: Job ID and session ID for tracking

---

### GET /api/v1/batch/status/{job_id}

**Purpose**: Get real-time progress of a batch job

**Returns**:
- Current status (pending/processing/completed/failed)
- Progress percentage
- Counts of processed/successful/failed documents
- Estimated time remaining
- List of errors

**Polling Recommendations**:
- Poll every 5-10 seconds
- Stop polling when status is "completed" or "failed"

---

### GET /api/v1/batch/result/{job_id}

**Purpose**: Get final results of a completed batch

**Returns**:
- Full list of all processed documents
- Document IDs for successful uploads
- Error details for failed documents
- Total processing time

**Note**: Only available when job status is "completed"

---

### DELETE /api/v1/batch/job/{job_id}

**Purpose**: Cancel a running batch job or delete completed job records

**Behavior**:
- If job is "processing": Marks as cancelled (prevents new documents from starting)
- If job is "completed" or "failed": Deletes job record

---

### GET /api/v1/batch/jobs

**Purpose**: List all batch jobs

**Parameters**:
- `session_id` (optional): Filter by session
- `status` (optional): Filter by status

**Returns**: Summary of all batch jobs (without full document lists)

## Performance Characteristics

### Processing Speed
- **Single document**: ~5-10 seconds (AI analysis time)
- **100 documents** (batch): ~8-15 minutes
- **500 documents** (batch): ~40-75 minutes

### Concurrency
- **Concurrent documents**: 3 at a time
- **Rate limit protection**: 0.5s delay between documents
- **Memory efficient**: Processes in chunks, not all at once

### Scalability
- ✅ **Memory**: Fixed overhead, doesn't grow with document count
- ✅ **API limits**: Built-in rate limiting prevents hitting API quotas
- ✅ **Database**: Indexed by session_id for fast retrieval
- ✅ **Progress tracking**: Real-time updates without database polling

## Best Practices

### 1. Organize by Session

Upload related documents in the same batch with a consistent `session_id`:

```python
# All contracts for Case #12345
response = requests.post(
    f"{API_BASE}/api/v1/batch/upload",
    files=contract_files,
    data={"session_id": "case-12345"}
)
```

Later, retrieve all documents for that case:

```python
# Get all documents for Case #12345
session_docs = requests.get(
    f"{API_BASE}/api/v1/documents/session/case-12345"
).json()
```

### 2. Handle Failures Gracefully

Some documents may fail (corrupted PDFs, unreadable text). Always check individual document status:

```python
for doc in results['documents']:
    if doc['status'] == 'failed':
        # Log failure, notify user, or retry
        logger.error(f"Failed to process {doc['filename']}: {doc['error']}")
```

### 3. Use Progress Callbacks

Show users real-time progress:

```javascript
async function uploadWithProgress(files, onProgress) {
  const { job_id } = await uploadBatch(files);

  while (true) {
    const status = await getStatus(job_id);
    onProgress(status.progress_percentage, status.processed_documents);

    if (status.status === 'completed') break;
    await sleep(5000);
  }
}

// Usage in UI
uploadWithProgress(files, (percent, processed) => {
  progressBar.update(percent);
  statusText.innerText = `Processed ${processed} documents`;
});
```

### 4. Batch Size Recommendations

| Document Count | Strategy | Reason |
|----------------|----------|--------|
| 1-10 | Single requests | Faster, simpler |
| 10-50 | Single batch | Optimal concurrency |
| 50-200 | Single batch | Good balance |
| 200-500 | Single batch | Maximum efficiency |
| 500+ | Multiple batches | Split into 500-doc chunks |

### 5. Error Recovery

If a batch fails partway through:

```python
# Check status
status = get_batch_status(job_id)

# Identify failed documents
failed_files = [
    doc['filename']
    for doc in status['errors']
]

# Retry only failed documents
retry_files = [f for f in original_files if f.name in failed_files]
retry_batch = upload_batch(retry_files)
```

## Troubleshooting

### Issue: Batch Stuck at "processing"

**Solution**:
```python
# Check status
status = get_batch_status(job_id)

# If truly stuck (no progress for > 5 minutes), cancel and retry
if time_since_last_update > 300:  # 5 minutes
    requests.delete(f"/api/v1/batch/job/{job_id}")
    # Re-upload batch
```

### Issue: High failure rate

**Possible Causes**:
1. Corrupted PDF files
2. Scanned images without OCR
3. Password-protected PDFs
4. Extremely large PDFs (>50MB)

**Solution**: Pre-validate files before uploading

```python
from app.src.services.pdf_service import pdf_service

# Validate before uploading
valid_files = []
for pdf_path in pdf_files:
    with open(pdf_path, 'rb') as f:
        contents = f.read()
        if pdf_service.validate_pdf(contents):
            valid_files.append(pdf_path)
        else:
            print(f"Skipping invalid PDF: {pdf_path}")

# Upload only valid files
upload_batch(valid_files)
```

### Issue: API rate limit errors

**Solution**: Batch processing already includes rate limiting, but if you're running multiple batches simultaneously:

```python
import asyncio

# Don't run multiple batches concurrently
jobs = []
for batch in document_batches:
    job_id = upload_batch(batch)
    await wait_for_completion(job_id)  # Wait before starting next batch
    jobs.append(job_id)
```

## Document Organization After Upload

### Retrieve All Documents by Session

```http
GET /api/v1/documents/session/{session_id}
```

Returns all documents with full analysis for that session.

### Retrieve Single Document

```http
GET /api/v1/documents/document/{document_id}
```

Returns full details and analysis for one document.

### Cross-Document Analysis

Once documents are uploaded, you can perform cross-document analysis:

```python
# Get all documents in session
session_docs = get_session_documents(session_id)

# Extract all parties mentioned across all documents
all_parties = set()
for doc in session_docs['documents']:
    all_parties.update(doc.get('parties', []))

# Find documents mentioning specific party
party_docs = [
    doc for doc in session_docs['documents']
    if 'Acme Corp' in doc.get('parties', [])
]
```

## Production Recommendations

### 1. Use Redis for Job Tracking

Current implementation uses in-memory storage. For production:

```python
import redis

redis_client = redis.Redis()

def create_batch_job(job_id, session_id, total_docs):
    job_data = {
        "job_id": job_id,
        "session_id": session_id,
        "status": "pending",
        "total_documents": total_docs,
        # ... other fields
    }
    redis_client.setex(
        f"batch_job:{job_id}",
        3600,  # Expire after 1 hour
        json.dumps(job_data)
    )
```

### 2. Use Celery for Background Tasks

For even better scalability:

```python
from celery import Celery

app = Celery('legal_ai', broker='redis://localhost:6379')

@app.task
def process_document_task(file_contents, filename, session_id, job_id):
    # Process document
    result = analyze_document(file_contents, filename)
    # Update job status in Redis
    update_batch_job(job_id, processed_count=+1)
    return result

# In API endpoint
@router.post("/batch/upload")
async def batch_upload(files):
    job_id = create_batch_job()
    for file in files:
        process_document_task.delay(
            await file.read(),
            file.filename,
            session_id,
            job_id
        )
    return {"job_id": job_id}
```

### 3. Add Webhooks

Notify users when batches complete:

```python
class BatchJobConfig(BaseModel):
    webhook_url: Optional[str] = None

@router.post("/batch/upload")
async def batch_upload(
    files: List[UploadFile],
    config: BatchJobConfig
):
    job_id = create_batch_job()
    # ... process documents
    # When complete:
    if config.webhook_url:
        requests.post(config.webhook_url, json={
            "job_id": job_id,
            "status": "completed",
            "results_url": f"/api/v1/batch/result/{job_id}"
        })
```

## Summary

**Current Capability**: YES, the system can handle hundreds of documents ✅

**Key Features**:
- ✅ Batch upload API for up to 500 documents
- ✅ Background processing with progress tracking
- ✅ Rate limiting to avoid API throttling
- ✅ Concurrent processing (3 documents at a time)
- ✅ Graceful error handling (failures don't stop batch)
- ✅ Session-based organization (retrieve all related documents)
- ✅ Real-time progress updates
- ✅ Memory-efficient chunk processing

**Performance**: 100 documents in ~10-15 minutes with full AI analysis

**Next Steps**: See `/api/v1/batch/*` endpoints in the API docs at http://localhost:8000/docs
