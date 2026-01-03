# Case Access Integration Guide

This guide shows how to integrate case access validation into existing endpoints.

## Quick Integration Examples

### Protect Case Endpoints (Backend)

**Before:**
```python
@router.get("/cases/{case_id}")
async def get_case(
    case_id: int,
    user: User = Depends(get_user_from_db),
    db: Session = Depends(get_db)
):
    case = db.query(TrackedDocket).filter(TrackedDocket.id == case_id).first()
    return case
```

**After:**
```python
from app.api.deps.case_access_deps import require_case_access

@router.get("/cases/{case_id}")
async def get_case(
    case_id: int,
    user: User = Depends(require_case_access(case_id)),  # Added this
    db: Session = Depends(get_db)
):
    case = db.query(TrackedDocket).filter(TrackedDocket.id == case_id).first()
    return case
```

That's it! The endpoint now requires case access. If user doesn't have access, they get a 402 Payment Required with purchase options.

---

## Integration Patterns

### Pattern 1: Protect Entire Endpoint

For endpoints that should only be accessible with case access:

```python
from app.api.deps.case_access_deps import require_case_access

@router.get("/cases/{case_id}/documents")
async def get_case_documents(
    case_id: int,
    user: User = Depends(require_case_access(case_id)),
    db: Session = Depends(get_db)
):
    # User is guaranteed to have access here
    documents = db.query(Document).filter(Document.case_id == case_id).all()
    return documents
```

### Pattern 2: Check Access Without Blocking

For endpoints that return different data based on access:

```python
from app.api.deps.case_access_deps import check_case_access_optional

@router.get("/cases/{case_id}/info")
async def get_case_info(
    case_id: int,
    user: User = Depends(get_user_from_db),
    access_info: dict = Depends(lambda: check_case_access_optional(case_id)),
    db: Session = Depends(get_db)
):
    case = db.query(TrackedDocket).filter(TrackedDocket.id == case_id).first()

    # Return limited info if no access
    if not access_info["has_access"]:
        return {
            "case_number": case.docket_number,
            "case_name": case.case_name,
            "has_access": False,
            "purchase_options": access_info.get("purchase_options")
        }

    # Return full info if has access
    return {
        "case": case,
        "documents": case.documents,
        "events": case.events,
        "has_access": True
    }
```

### Pattern 3: Manual Access Check in Function

For complex logic that needs custom access handling:

```python
from app.services.case_access_service import CaseAccessService

@router.post("/cases/{case_id}/analyze")
async def analyze_case(
    case_id: int,
    user: User = Depends(get_user_from_db),
    db: Session = Depends(get_db)
):
    # Manual access check
    case_service = CaseAccessService(db)
    access_check = case_service.check_user_access(user, case_id)

    if not access_check["has_access"]:
        # Custom error response
        raise HTTPException(
            status_code=402,
            detail={
                "error": "case_access_required",
                "message": "Purchase case access to use AI analysis",
                "purchase_url": f"/case-access/purchase?case_id={case_id}"
            }
        )

    # Proceed with analysis
    result = await analyze_case_with_ai(case_id)
    return result
```

---

## Frontend Integration

### Pattern 1: Show Purchase Prompt for Locked Cases

```tsx
import { useCaseAccessCheck } from '@/hooks/useCaseAccess';
import { PurchaseCaseAccessButton } from '@/components/CaseAccessCheckout';

function CasePage({ caseId }: { caseId: number }) {
  const { data: access, isLoading } = useCaseAccessCheck(caseId);

  if (isLoading) return <Loader />;

  if (!access?.has_access) {
    return (
      <div>
        <h1>Case Details</h1>
        <PurchaseCaseAccessButton caseId={caseId} caseName="Smith v. Jones" />
      </div>
    );
  }

  // User has access - show full case
  return <CaseDetails caseId={caseId} />;
}
```

### Pattern 2: Conditionally Show Features

```tsx
function CaseActions({ caseId }: { caseId: number }) {
  const { data: access } = useCaseAccessCheck(caseId);

  return (
    <div>
      {access?.has_access ? (
        <>
          <Button>Download Documents</Button>
          <Button>View Timeline</Button>
          <Button>Set Alerts</Button>
        </>
      ) : (
        <PurchaseCaseAccessButton caseId={caseId} compact />
      )}
    </div>
  );
}
```

---

## Notification Integration

### Send Notification When Case Updated

```python
from app.services.case_notification_service import CaseNotificationService

# When a new document is filed
@router.post("/cases/{case_id}/documents")
async def file_document(
    case_id: int,
    document_data: DocumentCreate,
    db: Session = Depends(get_db)
):
    # Create document
    document = Document(**document_data.dict(), case_id=case_id)
    db.add(document)
    db.commit()

    # Notify all users monitoring this case
    notification_service = CaseNotificationService(db)
    notification_service.notify_case_update(
        case_id=case_id,
        event_type="new_filing",
        event_title=f"New Document Filed: {document.title}",
        event_description=f"A new document was filed in this case.",
        event_data={"document_id": document.id}
    )

    return document
```

### Common Notification Events

```python
# New filing
notification_service.notify_case_update(
    case_id=case_id,
    event_type="new_filing",
    event_title="New Motion Filed",
    event_description="Defendant filed Motion to Dismiss"
)

# Status change
notification_service.notify_case_update(
    case_id=case_id,
    event_type="status_change",
    event_title="Case Status Updated",
    event_description="Case status changed to 'Under Review'"
)

# Deadline approaching
notification_service.notify_case_update(
    case_id=case_id,
    event_type="deadline",
    event_title="Deadline Approaching",
    event_description="Discovery deadline is in 3 days"
)

# Hearing scheduled
notification_service.notify_case_update(
    case_id=case_id,
    event_type="hearing",
    event_title="Hearing Scheduled",
    event_description="Motion hearing scheduled for March 15, 2025"
)
```

---

## Migration Checklist

### Backend Endpoints to Update

- [ ] `GET /cases/{case_id}` - View case details
- [ ] `GET /cases/{case_id}/documents` - List documents
- [ ] `GET /cases/{case_id}/documents/{doc_id}` - View document
- [ ] `POST /cases/{case_id}/documents/{doc_id}/download` - Download document
- [ ] `GET /cases/{case_id}/timeline` - View timeline
- [ ] `GET /cases/{case_id}/events` - List events
- [ ] `POST /cases/{case_id}/notes` - Add notes

### Add Case Access Checks

```python
# For each endpoint, add:
from app.api.deps.case_access_deps import require_case_access

# Change from:
user: User = Depends(get_user_from_db)

# To:
user: User = Depends(require_case_access(case_id))
```

### Frontend Pages to Update

- [ ] `/cases/[id]` - Case detail page
- [ ] `/cases/[id]/documents` - Documents page
- [ ] `/cases/[id]/timeline` - Timeline page
- [ ] `/dashboard` - Add "My Monitored Cases" widget

### Add Case Access Checks

```tsx
import { useCaseAccessCheck } from '@/hooks/useCaseAccess';
import { PurchaseCaseAccessButton } from '@/components/CaseAccessCheckout';

// At the top of your component:
const { data: access, isLoading } = useCaseAccessCheck(caseId);

// Before rendering protected content:
if (!access?.has_access) {
  return <PurchaseCaseAccessButton caseId={caseId} />;
}
```

---

## Error Handling

### Backend Error Response

When a user doesn't have access, they receive:

```json
{
  "error": "case_access_denied",
  "message": "You don't have access to this case",
  "case_id": 123,
  "purchase_options": [
    {
      "type": "one_time",
      "price": 5.00,
      "description": "Monitor this case until it closes"
    },
    {
      "type": "monthly",
      "price": 19.00,
      "description": "Monitor unlimited cases for 30 days"
    },
    {
      "type": "subscription_pro",
      "price": 49.00,
      "description": "Pro plan with unlimited case monitoring + AI features"
    }
  ]
}
```

### Frontend Error Handling

```tsx
try {
  const response = await fetch(`/api/v1/cases/${caseId}`);

  if (response.status === 402) {
    const error = await response.json();
    // Show purchase prompt with options
    showPurchasePrompt(error.purchase_options);
    return;
  }

  const data = await response.json();
  setCaseData(data);
} catch (err) {
  console.error(err);
}
```

---

## Testing

### Test Case Access Validation

```python
def test_case_access_denied_without_purchase(client, user, case):
    """Test that users without access get 402 error"""
    response = client.get(
        f"/api/v1/cases/{case.id}",
        headers={"Authorization": f"Bearer {user.token}"}
    )

    assert response.status_code == 402
    assert "purchase_options" in response.json()


def test_case_access_granted_after_purchase(client, user, case):
    """Test that users with purchase can access case"""
    # Purchase access
    purchase_case_access(user.id, case.id, "one_time")

    response = client.get(
        f"/api/v1/cases/{case.id}",
        headers={"Authorization": f"Bearer {user.token}"}
    )

    assert response.status_code == 200
    assert response.json()["id"] == case.id
```

---

## Performance Considerations

### Cache Access Checks

```python
# Use caching for frequently accessed cases
from functools import lru_cache

@lru_cache(maxsize=1000)
def check_access_cached(user_id: int, case_id: int) -> bool:
    # This will cache results for 5 minutes
    db = next(get_db())
    service = CaseAccessService(db)
    result = service.check_user_access(user_id, case_id)
    return result["has_access"]
```

### Batch Access Checks

```python
# For listing multiple cases
def check_access_batch(user_id: int, case_ids: List[int]) -> Dict[int, bool]:
    """Check access for multiple cases at once"""
    db = next(get_db())

    # Get all user's active case accesses
    accesses = db.query(CaseAccess).filter(
        CaseAccess.user_id == user_id,
        CaseAccess.status == CaseAccessStatus.ACTIVE,
        CaseAccess.case_id.in_(case_ids)
    ).all()

    accessible_case_ids = {a.case_id for a in accesses if a.is_active()}

    return {case_id: case_id in accessible_case_ids for case_id in case_ids}
```

---

## Summary

**Key Integration Points:**
1. Add `require_case_access(case_id)` dependency to protected endpoints
2. Use `useCaseAccessCheck()` hook in frontend
3. Show `<PurchaseCaseAccessButton>` when no access
4. Send notifications with `CaseNotificationService`
5. Handle 402 errors gracefully with purchase prompts

**Benefits:**
- ✅ Automatic case access validation
- ✅ Clear purchase flow for users
- ✅ Detailed error messages
- ✅ Easy to integrate
- ✅ Minimal code changes needed
