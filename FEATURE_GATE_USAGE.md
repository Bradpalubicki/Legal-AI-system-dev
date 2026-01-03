# Feature Gate Usage Guide

This guide shows how to use the feature gating system to control access to features based on user tier.

## Quick Start

### 1. Wrap Features with FeatureGate

```tsx
import { FeatureGate } from '@/components/FeatureGate';

function DocumentAnalysisPage() {
  return (
    <div>
      <h1>Document Analysis</h1>

      {/* This feature is only available to Pro and Firm tiers */}
      <FeatureGate feature="ai_analysis">
        <AIAnalysisPanel />
      </FeatureGate>
    </div>
  );
}
```

### 2. Check Feature Access Programmatically

```tsx
import { useFeatureCheck } from '@/components/FeatureGate';

function MyComponent() {
  const { hasAccess, isLoading, upgradeInfo } = useFeatureCheck('pacer_search');

  if (isLoading) return <Loader />;

  if (!hasAccess) {
    return <UpgradePrompt upgradeInfo={upgradeInfo} />;
  }

  return <PACERSearchForm />;
}
```

### 3. Protect API Routes (Backend)

```python
from fastapi import Depends
from app.api.deps.feature_gates import require_feature
from app.core.feature_access import Feature

@router.post("/documents/analyze")
async def analyze_document(
    document_id: int,
    user: User = Depends(require_feature(Feature.AI_ANALYSIS))
):
    # Only users with AI_ANALYSIS feature can access this
    return {"status": "analyzing"}
```

## Component Examples

### FeatureGate with Custom Fallback

```tsx
<FeatureGate
  feature="document_comparison"
  fallback={
    <UpgradeCard
      title="Compare Documents with AI"
      description="Identify differences and track changes automatically"
      tier="Pro"
      price="$49/month"
    />
  }
>
  <DocumentComparison docs={docs} />
</FeatureGate>
```

### FeatureGate with Blur Effect

```tsx
{/* Show blurred preview of locked feature */}
<FeatureGate
  feature="ai_summarization"
  showBlur={true}
  showOverlay={true}
>
  <DocumentSummary document={doc} />
</FeatureGate>
```

### Navigation with Locked Items

```tsx
import { FeatureNavItem } from '@/components/FeatureGate';

function Sidebar() {
  return (
    <nav>
      <NavItem href="/dashboard">Dashboard</NavItem>
      <NavItem href="/cases">Cases</NavItem>

      {/* Shows lock icon if user doesn't have access */}
      <FeatureNavItem
        feature="ai_analysis"
        href="/ai-analysis"
      >
        AI Analysis
      </FeatureNavItem>

      <FeatureNavItem
        feature="team_collaboration"
        href="/team"
      >
        Team
      </FeatureNavItem>
    </nav>
  );
}
```

### Upgrade Banners

```tsx
import { UpgradeBanner } from '@/components/UpgradePrompt';

function Dashboard() {
  const { hasAccess } = useFeatureCheck('ai_analysis');

  return (
    <div>
      {!hasAccess && (
        <UpgradeBanner
          message="Unlock AI-powered document analysis"
          tierName="Pro"
          price="$49/month"
        />
      )}

      <DashboardContent />
    </div>
  );
}
```

### Feature Preview Cards

```tsx
import { FeaturePreviewCard } from '@/components/UpgradePrompt';
import { Brain, FileCompare, Search } from 'lucide-react';

function UpgradePage() {
  return (
    <div className="grid md:grid-cols-3 gap-6">
      <FeaturePreviewCard
        title="AI Document Analysis"
        description="Let AI analyze contracts, briefs, and legal documents"
        icon={Brain}
        tierName="Pro"
        price="$49/month"
        benefits={[
          "Automatic clause extraction",
          "Risk assessment",
          "Summary generation",
          "100 analyses per month"
        ]}
      />

      <FeaturePreviewCard
        title="Document Comparison"
        description="Compare multiple documents and track changes"
        icon={FileCompare}
        tierName="Pro"
        price="$49/month"
        benefits={[
          "Side-by-side comparison",
          "Highlight differences",
          "Track revisions",
          "50 comparisons per month"
        ]}
      />

      <FeaturePreviewCard
        title="PACER Integration"
        description="Search and download federal court documents"
        icon={Search}
        tierName="Pro"
        price="$49/month"
        benefits={[
          "$100 credits included",
          "Automatic document retrieval",
          "RECAP archive first",
          "Download history"
        ]}
      />
    </div>
  );
}
```

## Backend Protection Examples

### Protect Individual Endpoints

```python
from app.api.deps.feature_gates import require_feature, check_feature_limit
from app.core.feature_access import Feature

# Require feature access
@router.post("/ai/analyze")
async def analyze_document(
    user: User = Depends(require_feature(Feature.AI_ANALYSIS))
):
    return await ai_service.analyze()

# Check usage limits
@router.post("/ai/summarize")
async def summarize_document(
    user: User = Depends(check_feature_limit(Feature.AI_SUMMARIZATION))
):
    # Track usage
    await track_feature_usage("ai_summarization", 1)
    return await ai_service.summarize()
```

### Require Multiple Features

```python
from app.api.deps.feature_gates import require_all_features

@router.post("/advanced-analysis")
async def advanced_analysis(
    user: User = Depends(require_all_features(
        Feature.AI_ANALYSIS,
        Feature.DOCUMENT_COMPARISON
    ))
):
    return {"status": "analyzing"}
```

### Require Any of Several Features

```python
from app.api.deps.feature_gates import require_any_feature

@router.get("/legal-research")
async def legal_research(
    user: User = Depends(require_any_feature(
        Feature.PACER_SEARCH,
        Feature.COURTLISTENER_SEARCH,
        Feature.LEGAL_RESEARCH
    ))
):
    return {"results": [...]}
```

## Available Features

All features are defined in `backend/app/core/feature_access.py`:

### Case Management
- `CASE_MONITORING` - Monitor legal cases
- `CASE_CREATION` - Create and track cases
- `CASE_NOTES` - Add notes to cases

### Document Features
- `DOCUMENT_VIEW` - View documents
- `DOCUMENT_UPLOAD` - Upload documents
- `DOCUMENT_DOWNLOAD` - Download documents
- `DOCUMENT_EXPORT` - Export to PDF/Word
- `DOCUMENT_COMPARISON` - Compare documents
- `DOCUMENT_BATCH_PROCESSING` - Process multiple documents

### AI Features
- `AI_ANALYSIS` - AI document analysis
- `AI_SUMMARIZATION` - AI summaries
- `AI_CLAUSE_EXTRACTION` - Extract key clauses
- `AI_RISK_ASSESSMENT` - Risk analysis
- `AI_ASSISTANT` - AI legal assistant

### Research Features
- `PACER_SEARCH` - PACER searches
- `PACER_DOWNLOAD` - PACER downloads
- `COURTLISTENER_SEARCH` - CourtListener searches
- `LEGAL_RESEARCH` - Legal research tools
- `CITATION_VALIDATION` - Validate citations

### Notifications
- `EMAIL_NOTIFICATIONS` - Email alerts
- `SMS_NOTIFICATIONS` - SMS alerts
- `WEBHOOK_NOTIFICATIONS` - Webhook notifications

### Collaboration
- `TEAM_COLLABORATION` - Team features
- `CLIENT_PORTAL` - Client portal access
- `MATTER_MANAGEMENT` - Matter management

### API & Integration
- `API_ACCESS` - REST API access
- `WEBHOOK_INTEGRATION` - Webhooks
- `ZAPIER_INTEGRATION` - Zapier integration

## Tier Configuration

### Free Tier
- No case monitoring
- Limited document viewing (5/month)
- Basic CourtListener searches (10/month)

### Case Monitor ($5/case or $19/month)
- Monitor 1 case ($5) or unlimited ($19/mo)
- Unlimited document viewing for monitored cases
- Email notifications
- Unlimited CourtListener searches

### Pro ($49/month)
- Unlimited case monitoring
- AI analysis (100/month)
- Document comparison (50/month)
- PACER searches ($100 credits included)
- AI assistant (200 queries/month)
- SMS notifications (100/month)
- Export features

### Firm ($199/month)
- Everything unlimited
- Team collaboration (10 users)
- Client portal
- API access (10k requests/day)
- $500 PACER credits
- Compliance reporting
- Priority support

## Testing

### Test Feature Access

```typescript
// In your tests
import { renderWithProviders } from '@/test-utils';
import { FeatureGate } from '@/components/FeatureGate';

test('shows upgrade prompt for locked feature', async () => {
  const { getByText } = renderWithProviders(
    <FeatureGate feature="ai_analysis">
      <div>AI Analysis Content</div>
    </FeatureGate>,
    {
      user: { tier: 'case_monitor' } // User without AI access
    }
  );

  expect(getByText(/Upgrade to unlock/i)).toBeInTheDocument();
});
```

### Backend Tests

```python
def test_feature_gate_blocks_access(client, case_monitor_user):
    """Test that feature gate blocks Case Monitor users from AI analysis"""
    response = client.post(
        "/api/v1/documents/analyze",
        headers={"Authorization": f"Bearer {case_monitor_user.token}"}
    )

    assert response.status_code == 402
    assert "upgrade" in response.json()
```

## Migration Guide

### Protecting Existing Features

1. **Identify features to gate**: Review your app and decide which features should be premium

2. **Add FeatureGate wrapper**: Wrap components with `<FeatureGate>`

3. **Protect API endpoints**: Add `require_feature()` dependency

4. **Test thoroughly**: Ensure users see upgrade prompts, not errors

### Example Migration

**Before:**
```tsx
function DocumentAnalysis() {
  return <AIAnalysisPanel />;
}
```

**After:**
```tsx
import { FeatureGate } from '@/components/FeatureGate';

function DocumentAnalysis() {
  return (
    <FeatureGate feature="ai_analysis">
      <AIAnalysisPanel />
    </FeatureGate>
  );
}
```

## Best Practices

1. **Always provide upgrade path**: Show users what they're missing and how to get it

2. **Use blur previews**: Let users see features before upgrading (builds desire)

3. **Track interactions**: Monitor which locked features users try to access

4. **Be transparent**: Clearly show tier requirements in UI

5. **Fail gracefully**: If feature check fails, default to showing content (better UX)

6. **Cache access checks**: Use React Query's caching to avoid repeated API calls

7. **Test both states**: Test both locked and unlocked states of features

8. **Progressive disclosure**: Show features gradually as users explore the app

## Troubleshooting

### Feature gate not working?

1. Check user is authenticated
2. Verify feature name matches backend enum
3. Check API endpoint is registered in `main.py`
4. Look for errors in browser console

### Backend returning 500 error?

1. Check database connection
2. Verify User model has subscription relationship
3. Check feature_flags table exists
4. Review backend logs

### Always shows upgrade prompt?

1. Verify user's tier in database
2. Check subscription status (active/trialing)
3. Review tier-to-role mapping in `feature_access.py`

## Support

- Documentation: `/docs/feature-gating`
- API Docs: `http://localhost:8000/docs`
- Issues: Create ticket in project tracker
