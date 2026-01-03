# CourtListener API Integration - Critical Parameters Guide

## Overview
This document contains critical information about CourtListener API parameters to prevent data integrity bugs.

## CRITICAL: Query Parameter Names

### ⚠️ RECAP Documents API (`/recap-documents/`)

**CORRECT Parameter Name:** `docket_id`
**WRONG Parameter Name:** `docket` ❌

```python
# ✅ CORRECT - Filters documents by docket
url = f"{base_url}/recap-documents/?docket_id={docket_id}"

# ❌ WRONG - Returns ALL documents (unfiltered)
url = f"{base_url}/recap-documents/?docket={docket_id}"
```

**Why This Matters:**
- Using `docket=` instead of `docket_id=` will cause the API to ignore the filter
- Result: API returns ALL documents in the entire RECAP database
- This can result in 10,000+ unrelated documents being fetched
- Documents will be from random cases, different years, completely unrelated

**Historical Bug:**
- Date: 2025-11-12
- Issue: Parameter changed from `docket_id` to `docket`
- Impact: Fetched 1,840+ unrelated documents from 2016
- Fix: Changed back to `docket_id` and added validation

## API Endpoints and Correct Parameters

### 1. Search Dockets
```
GET /api/rest/v4/search/?type=r
Parameters:
  - q: search query string
  - type: "r" for RECAP (dockets)
  - page: page number
  - page_size: results per page (max 100, usually returns 20)
```

### 2. Get Docket Details (Metadata Only)
```
GET /api/rest/v4/dockets/{docket_id}/
Path parameter:
  - docket_id: CourtListener docket ID (integer)

IMPORTANT: This endpoint returns docket metadata ONLY.
It does NOT include docket_entries or documents in the response.
Use endpoint #3 below to get documents.
```

### 3. Get Docket Entries (✅ CORRECT WAY TO GET DOCUMENTS)
```
GET /api/rest/v4/docket-entries/?docket={docket_id}
Query parameters:
  - docket: Filter by docket ID (NOTE: uses "docket" not "docket_id")
  - order_by: Sort field (e.g., "entry_number")
  - page: Page number for pagination

Returns: Paginated list of docket entries
Each entry contains:
  - entry_number: Entry number on docket
  - date_filed: Date the entry was filed
  - recap_documents: Array of documents attached to this entry

How to use:
  1. Call this endpoint with docket={id}
  2. Follow "next" URLs for pagination (~20 entries per page)
  3. Extract recap_documents array from each entry
  4. Flatten all documents into a single list
```

### 4. ❌ Get RECAP Documents (BROKEN - DO NOT USE)
```
GET /api/rest/v4/recap-documents/
Query parameters:
  - docket_id: Filter by docket ID

⚠️ WARNING: This endpoint does NOT filter by docket_id!
It returns ALL documents in sequential order, ignoring the parameter.
Use endpoint #3 (docket-entries) instead.
```

### 4. Get Single RECAP Document
```
GET /api/rest/v4/recap-documents/{document_id}/
Path parameter:
  - document_id: CourtListener RECAP document ID
```

### 5. RECAP Query (Check Availability)
```
GET /api/rest/v4/recap-query/
Query parameters:
  - court: Court identifier (e.g., 'cand', 'nysd')
  - pacer_doc_id__in: Comma-separated PACER doc IDs
```

### 6. RECAP Fetch (Purchase from PACER)
```
POST /api/rest/v4/recap-fetch/
Body (JSON):
  - pacer_username: PACER credentials
  - pacer_password: PACER credentials
  - request_type: 1=docket, 2=PDF, 3=attachment
  - pacer_doc_id: Document identifier
  - court: Court identifier
```

## Safety Mechanisms

### Client-Side Validation
All document fetching includes client-side filtering to verify documents belong to the requested docket:

```python
doc_docket_id = doc.get("docket")
if doc_docket_id != requested_docket_id:
    # Filter out wrong documents
    continue
```

### Early Detection
If first page has 0 valid documents, immediately raise error - indicates API filter is broken.

### Filter Rate Monitoring
Warns if >50% of documents are being filtered out - indicates API query may be incorrect.

## Testing Checklist

Before deploying changes to CourtListener integration:

- [ ] Verify `docket_id` parameter is used (not `docket`)
- [ ] Check logs show correct URL: `?docket_id={id}`
- [ ] Test with known docket: should return only documents for that case
- [ ] Verify filtered_out_count is 0 in logs (all docs belong to requested docket)
- [ ] Check total document count matches CourtListener website

## Common Mistakes

1. **Using `docket` instead of `docket_id`** ⚠️ Most common!
2. **Not validating document docket matches request**
3. **Infinite pagination without max_pages limit**
4. **Continuing after API errors (502, 503)**
5. **Not checking API's reported count field**

## References

- CourtListener API Docs: https://www.courtlistener.com/api/rest-info/
- RECAP API: https://www.courtlistener.com/help/api/recap/
- This integration: `backend/app/src/services/courtlistener_service.py`
