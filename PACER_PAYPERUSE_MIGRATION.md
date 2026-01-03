# PACER Pay-Per-Use Migration Plan

## Current Problem

**Users must provide their own PACER credentials** - Bad UX:
- Requires PACER account signup
- Users responsible for PACER costs
- Complex credential management
- Security concerns storing user credentials

## New Solution: Backend-Managed Pay-Per-Use

**You handle everything, users just pay credits:**
- ✅ Single system PACER account (your credentials)
- ✅ Users buy credits ($5, $10, $20, etc.)
- ✅ Credits deducted per search/download
- ✅ No PACER knowledge required from users

---

## Architecture Changes

### **Before (Current):**
```
User → Enters own PACER login → App uses their credentials → PACER charges user
```

### **After (New):**
```
User → Buys credits ($10) → Requests search → Your PACER account → Deduct credits
```

---

## Implementation Steps

### **Phase 1: System PACER Credentials (30 min)**

**1. Add System Credentials to Environment**

Update `.env`:
```bash
# System PACER Credentials (shared by all users)
PACER_USERNAME=your_pacer_username
PACER_PASSWORD=your_pacer_password
PACER_CLIENT_CODE=your_client_code

# CourtListener API (free, no user credentials needed)
COURTLISTENER_API_KEY=your_api_key
```

**2. Update Config to Use System Credentials**

`backend/app/src/core/config.py`:
```python
class Settings(BaseSettings):
    # ... existing settings ...

    # System PACER Credentials (used for all users)
    PACER_USERNAME: str = ""
    PACER_PASSWORD: str = ""
    PACER_CLIENT_CODE: str = ""

    # CourtListener (free tier)
    COURTLISTENER_API_KEY: str = ""
```

**3. Remove User Credential Requirements**

- Keep `UserPACERCredentials` model for legacy/enterprise users
- Add `use_system_credentials: bool = True` flag to User model
- Most users will use system credentials

---

### **Phase 2: Credit Pricing Model (1 hour)**

**Define Pricing Tiers:**

```python
# backend/app/models/pricing.py

PACER_PRICING = {
    # Document operations
    "document_download": {
        "cost": 0.10,  # $0.10 per page
        "description": "Download PACER document (per page)"
    },
    "docket_sheet": {
        "cost": 3.00,  # $3.00 per docket
        "description": "View full docket sheet"
    },

    # Search operations
    "case_search": {
        "cost": 5.00,  # $5.00 per search
        "description": "Case number search"
    },
    "party_search": {
        "cost": 5.00,
        "description": "Party name search"
    },

    # CourtListener (free/low-cost)
    "courtlistener_search": {
        "cost": 0.10,  # $0.10 per search
        "description": "CourtListener federal court search"
    },
    "courtlistener_docket": {
        "cost": 0.00,  # Free!
        "description": "CourtListener docket retrieval"
    }
}

CREDIT_PACKAGES = {
    "starter": {
        "credits": 10.00,
        "price": 10.00,
        "bonus": 0,
        "description": "Perfect for 2 case searches"
    },
    "basic": {
        "credits": 25.00,
        "price": 20.00,
        "bonus": 5.00,
        "description": "Save $5 - Best for light users"
    },
    "professional": {
        "credits": 100.00,
        "price": 75.00,
        "bonus": 25.00,
        "description": "Save $25 - Popular choice"
    },
    "firm": {
        "credits": 500.00,
        "price": 350.00,
        "bonus": 150.00,
        "description": "Save $150 - Best value"
    }
}
```

---

### **Phase 3: Update Search Endpoints (2 hours)**

**Update PACER Search to Use Credits:**

`backend/app/api/pacer_endpoints.py`:

```python
from ..models.pricing import PACER_PRICING
from ..models.credits import UserCredits, CreditTransaction, TransactionType

@router.post("/search")
async def search_pacer(
    search_request: PACERSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search PACER using system credentials, charge user credits.
    """
    # Check user has enough credits
    user_credits = db.query(UserCredits).filter(
        UserCredits.user_id == current_user.id
    ).first()

    if not user_credits:
        user_credits = UserCredits(user_id=current_user.id, balance=0.0)
        db.add(user_credits)
        db.commit()

    search_cost = PACER_PRICING["case_search"]["cost"]

    if user_credits.balance < search_cost:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail={
                "error": "insufficient_credits",
                "required": search_cost,
                "current_balance": user_credits.balance,
                "message": f"Need ${search_cost} credits. Current balance: ${user_credits.balance}",
                "purchase_url": "/credits/purchase"
            }
        )

    # Use SYSTEM credentials (from env)
    pacer_service = PACERService(
        username=settings.PACER_USERNAME,
        password=settings.PACER_PASSWORD,
        client_code=settings.PACER_CLIENT_CODE
    )

    try:
        # Perform search
        results = await pacer_service.search_cases(
            court=search_request.court,
            case_number=search_request.case_number
        )

        # Deduct credits on success
        user_credits.balance -= search_cost
        user_credits.total_spent += search_cost

        # Record transaction
        transaction = CreditTransaction(
            user_id=current_user.id,
            transaction_type=TransactionType.PURCHASE,
            amount=-search_cost,
            balance_after=user_credits.balance,
            description=f"PACER case search: {search_request.case_number}"
        )
        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "results": results,
            "cost": search_cost,
            "remaining_credits": user_credits.balance
        }

    except Exception as e:
        # Don't charge if search failed
        raise HTTPException(
            status_code=500,
            detail=f"PACER search failed: {str(e)}"
        )
```

---

### **Phase 4: Frontend Updates (2 hours)**

**Remove Credential Input Forms:**

Delete/update these files:
- `frontend/src/app/pacer/page.tsx` - Remove credential form
- `frontend/src/components/CaseTracking/EnhancedCaseTracker.tsx` - Remove PACER login

**Add Credit Purchase Flow:**

`frontend/src/components/Credits/CreditPurchase.tsx`:
```typescript
export function CreditPurchase() {
  const [selectedPackage, setSelectedPackage] = useState('basic');

  const packages = {
    starter: { credits: 10, price: 10, bonus: 0 },
    basic: { credits: 25, price: 20, bonus: 5 },
    professional: { credits: 100, price: 75, bonus: 25 },
    firm: { credits: 500, price: 350, bonus: 150 }
  };

  const handlePurchase = async () => {
    // Integrate with Stripe/PayPal
    const response = await axios.post('/api/v1/credits/purchase', {
      package: selectedPackage,
      payment_method: 'stripe'
    });

    // Redirect to Stripe checkout
    window.location.href = response.data.checkout_url;
  };

  return (
    <div className="grid grid-cols-4 gap-4">
      {Object.entries(packages).map(([key, pkg]) => (
        <PricingCard
          key={key}
          title={key}
          credits={pkg.credits}
          price={pkg.price}
          bonus={pkg.bonus}
          onSelect={() => handlePurchase()}
        />
      ))}
    </div>
  );
}
```

**Update Search Components to Show Credit Cost:**

`frontend/src/components/CaseTracking/EnhancedCaseTracker.tsx`:
```typescript
// Before search, show cost preview
<div className="bg-blue-50 p-4 rounded">
  <p>This search will cost: <strong>$5.00</strong></p>
  <p>Your balance: <strong>${userCredits}</strong></p>
  {userCredits < 5 && (
    <Link href="/credits/purchase">
      <Button>Add Credits</Button>
    </Link>
  )}
</div>

<Button
  onClick={handleSearch}
  disabled={userCredits < 5}
>
  Search PACER (Cost: $5.00)
</Button>
```

---

### **Phase 5: CourtListener (FREE Alternative)**

**Promote CourtListener as Free Option:**

CourtListener provides **FREE federal court data** without PACER fees!

```typescript
<div className="grid grid-cols-2 gap-4">
  {/* Free Option */}
  <Card className="border-green-500">
    <CardHeader>
      <h3>CourtListener (FREE)</h3>
      <Badge variant="success">No Credits Required</Badge>
    </CardHeader>
    <CardContent>
      <p>Search federal court dockets for free</p>
      <p className="text-sm text-gray-600">
        Most cases available within 24 hours of filing
      </p>
      <Button onClick={searchCourtListener}>
        Search Free
      </Button>
    </CardContent>
  </Card>

  {/* Paid Option */}
  <Card>
    <CardHeader>
      <h3>PACER (Real-Time)</h3>
      <Badge variant="warning">$5.00 per search</Badge>
    </CardHeader>
    <CardContent>
      <p>Official PACER records</p>
      <p className="text-sm text-gray-600">
        Immediate access to all documents
      </p>
      <Button onClick={searchPACER} disabled={credits < 5}>
        Search PACER ($5.00)
      </Button>
    </CardContent>
  </Card>
</div>
```

---

## Pricing Strategy Recommendations

### **Option 1: Prepaid Credits (Recommended)**

**User Flow:**
1. User signs up (no PACER needed!)
2. User buys $20 credit pack
3. Each search deducts credits
4. User adds more when low

**Pros:**
- Simple to implement
- Users control spending
- You get paid upfront
- No subscription management

**Pricing:**
```
PACER Search: $5.00
PACER Docket: $3.00
PACER Document: $0.10/page
CourtListener: FREE
```

---

### **Option 2: Subscription + Credits Hybrid**

**Tiers:**
```
Free Tier:
- CourtListener searches: Unlimited (FREE)
- PACER searches: 0/month
- Price: $0

Basic ($29/month):
- CourtListener: Unlimited
- PACER searches: 5/month
- Additional searches: $4/each
- Price: $29/month

Professional ($99/month):
- CourtListener: Unlimited
- PACER searches: 30/month
- Additional searches: $3/each
- Price: $99/month

Firm ($299/month):
- Everything unlimited
- Team features
- API access
- Price: $299/month
```

---

### **Option 3: Pay-Per-Search Only**

**No subscriptions, just pay for what you use:**
```
CourtListener Search: FREE
PACER Case Search: $5
PACER Docket Sheet: $3
PACER Document: $0.10/page
```

**User Flow:**
- Users add payment method (Stripe)
- Each search charges card directly
- No credits, no subscriptions
- Simple but higher per-transaction fees

---

## Migration Checklist

### **Immediate (This Week):**
- [ ] Add system PACER credentials to `.env`
- [ ] Update config.py to load system credentials
- [ ] Test PACER/CourtListener with system credentials
- [ ] Deploy backend with system credentials

### **Week 1:**
- [ ] Update PACER endpoints to use system credentials
- [ ] Add credit balance checks before operations
- [ ] Implement credit deduction on successful operations
- [ ] Add 402 Payment Required error handling

### **Week 2:**
- [ ] Create credit purchase page (frontend)
- [ ] Integrate Stripe for credit purchases
- [ ] Update search UI to show costs
- [ ] Add "insufficient credits" warnings

### **Week 3:**
- [ ] Remove user credential forms
- [ ] Add CourtListener as free alternative
- [ ] Update documentation
- [ ] Test end-to-end flow

### **Beta Launch:**
- [ ] Give beta users free credits ($50)
- [ ] Monitor usage and costs
- [ ] Adjust pricing based on data
- [ ] Collect feedback

---

## Cost Analysis

### **Your PACER Costs:**
- Case search: $0.00 (searches are free on PACER!)
- Docket sheet view: $0.10/page (max $3.00)
- Document download: $0.10/page (max $3.00/document)

### **Your Pricing (Markup):**
- Case search: $5.00 (you charge, PACER is free)
- Docket sheet: $3.00 (covers your cost)
- Document: $0.10/page (pass-through, or add markup)

### **Profit Margin:**
- Search: 100% profit (PACER searches are free!)
- Docket: ~50% profit ($3 charge, ~$1.50 avg cost)
- Documents: Break-even or small margin

### **CourtListener (FREE):**
- Completely free for you AND users
- Use as much as you want
- Promote this to reduce PACER costs!

---

## Implementation Priority

**Start with simplest:**

1. **This week:** System credentials + basic credit checks
2. **Next week:** Stripe integration for credit purchases
3. **Week 3:** Polish UI and add CourtListener promotion
4. **Week 4:** Beta test with real users

**Don't build:**
- ❌ Subscription tiers (yet) - add later if needed
- ❌ Complex billing - keep it simple with credits
- ❌ User PACER credentials - not needed anymore

---

## Quick Start: Minimal Implementation

**Want to launch fast? Do this:**

1. **Add system credentials to .env** (5 min)
2. **Update pacer_service.py to use system creds** (15 min)
3. **Add simple credit check** (30 min):
   ```python
   if user.credits < 5:
       raise HTTPException(402, "Need $5 credits")
   ```
4. **Manual credit top-ups** (for beta):
   ```bash
   # Add credits via script
   python -c "from app.models.credits import UserCredits; ..."
   ```
5. **Launch beta with free credits** - let users test
6. **Add Stripe later** - once you have paying users

**Total time: 1 hour to working beta!**

---

Want me to start implementing this? I can:
1. Update backend to use system credentials
2. Add credit checks to PACER endpoints
3. Create credit purchase UI
4. Remove user credential forms

Which part should we tackle first?
