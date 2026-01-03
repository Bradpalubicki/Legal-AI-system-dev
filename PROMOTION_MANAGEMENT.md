# Promotion & Feature Flag Management

## Quick Commands

### **Check Current Status**
```bash
cd backend
python -m app.scripts.manage_promotions status
```

### **Launch Promotions**

**Option 1: Disable Credits Entirely (Simplest)**
```bash
# Make everything free for everyone
python -m app.scripts.manage_promotions disable-credits
```
Output:
```
[OK] Credits DISABLED globally
   Users WILL NOT be charged for searches
```

**Option 2: Create "Free Month" Campaign**
```bash
# Unlimited searches for 30 days
python -m app.scripts.manage_promotions free-month
```
Output:
```
[OK] Created 'Free Month' promotion
   Code: FREEMONTH
   Benefits: Unlimited searches (no credits required)
   Valid: 2025-01-15 to 2025-02-15
   Duration: 30 days
```

**Option 3: "$20 Signup Bonus"**
```bash
# New users get $20 free credits
python -m app.scripts.manage_promotions signup-bonus
```

### **Grant VIP Access**
```bash
# Give specific user unlimited access
python -m app.scripts.manage_promotions grant-unlimited dev@example.com 30 "Beta tester"
```

### **Re-enable Credits After Promo**
```bash
python -m app.scripts.manage_promotions enable-credits
```

---

## Launch Strategy Recommendations

### **Week 1-4: Free Beta** (Recommended)

**Simplest approach - disable credits:**
```bash
cd backend
python -m app.scripts.manage_promotions disable-credits
```

**What happens:**
- ✅ All searches FREE for everyone
- ✅ No credit system active
- ✅ Users can test everything
- ✅ You collect feedback

**When to re-enable:**
```bash
# After 30 days, turn on credits
python -m app.scripts.manage_promotions enable-credits
```

---

### **Month 2: Paid Launch with Grandfather**

**Re-enable credits but grandfather beta users:**
```bash
# 1. Enable credits globally
python -m app.scripts.manage_promotions enable-credits

# 2. Grant unlimited to beta testers (optional)
python -m app.scripts.manage_promotions grant-unlimited beta1@example.com 365 "Beta tester - free year"
python -m app.scripts.manage_promotions grant-unlimited beta2@example.com 365 "Beta tester - free year"
```

**Result:**
- New users pay credits
- Beta users keep free access for 1 year
- You reward early adopters!

---

## Use Cases

### **1. Launch Day - Everything Free**

**Command:**
```bash
python -m app.scripts.manage_promotions disable-credits
```

**Use when:**
- First month of launch
- Want maximum user growth
- Collecting feedback
- No payment system ready yet

**Duration:** 30 days typical

---

### **2. Limited Time Promotion**

**Create campaign:**
```bash
python -m app.scripts.manage_promotions free-month
```

**Use when:**
- Special event (Black Friday, etc.)
- Re-engagement campaign
- Competitive response
- Want tracking/analytics

**Benefits:**
- Can set start/end dates
- Track redemptions
- Target specific users
- Better analytics than global disable

---

### **3. VIP Users**

**Grant access:**
```bash
python -m app.scripts.manage_promotions grant-unlimited lawyer@bigfirm.com 365 "Enterprise pilot"
```

**Use for:**
- Beta testers
- Enterprise trials
- Partners/affiliates
- Press/reviewers

**Flexible expiry:**
- 7 days = Trial
- 30 days = Beta
- 90 days = Quarterly
- 365 days = Annual

---

### **4. New User Incentive**

**Create bonus:**
```bash
python -m app.scripts.manage_promotions signup-bonus
```

**Result:**
- New users get $20 credits
- Reduces signup friction
- Limited to first 1000 users
- Auto-expires after 90 days

---

## How It Works Behind the Scenes

### **Credit Check Flow:**

```python
# In your PACER search endpoint:

from app.utils.feature_flags import credits_required_for_user

@router.post("/search")
async def search_pacer(
    search_request: PACERSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Check if credits required
    if credits_required_for_user(db, current_user.id):
        # Credits enabled - check balance
        user_credits = get_user_credits(current_user.id)
        if user_credits.balance < SEARCH_COST:
            raise HTTPException(402, "Insufficient credits")

        # Deduct credits
        deduct_credits(current_user.id, SEARCH_COST)

    # Perform search (free or paid)
    results = pacer_service.search(...)
    return results
```

**Priority Order:**
1. User has unlimited override? → Free
2. Active promotional campaign? → Free
3. Credits globally disabled? → Free
4. Otherwise → Check balance

---

## Frontend Integration

### **Show Promotional Banner:**

```typescript
// Check for active campaigns
const { data: campaigns } = await axios.get('/api/v1/campaigns/active');

if (campaigns.unlimited_searches) {
  return (
    <Banner variant="success">
      🎉 Free unlimited searches during our launch month!
      Valid until {campaigns.ends_at}
    </Banner>
  );
}
```

### **Show Credit Balance (when enabled):**

```typescript
// Only show if credits required
if (creditsEnabled) {
  return (
    <div className="credit-balance">
      Balance: ${userCredits}
      <Button onClick={() => navigate('/credits/purchase')}>
        Add Credits
      </Button>
    </div>
  );
}
```

---

## Database Tables

**Created by migration:**

1. `feature_flags` - Global on/off switches
2. `user_feature_overrides` - Per-user overrides
3. `promotional_campaigns` - Time-limited promotions
4. `user_campaign_redemptions` - Track who redeemed what

---

## Migration Needed

**Create tables:**
```bash
cd backend

# Create migration
alembic revision -m "Add feature flags and promotions"

# Apply migration
alembic upgrade head
```

**Or manually run:**
```sql
-- See backend/app/models/feature_flags.py for schema
CREATE TABLE feature_flags (...);
CREATE TABLE user_feature_overrides (...);
CREATE TABLE promotional_campaigns (...);
CREATE TABLE user_campaign_redemptions (...);
```

---

## Recommended Timeline

### **Week 1 (Launch Week):**
```bash
# Disable credits for free beta
python -m app.scripts.manage_promotions disable-credits
```

**Announce:**
> "🎉 Free unlimited searches during our launch month!
> Try everything - no credit card required!"

---

### **Week 2-4:**
```bash
# Check status weekly
python -m app.scripts.manage_promotions list-campaigns
```

**Monitor:**
- User signups
- Search volume
- Cost to you
- User feedback

---

### **Month 2 (Paid Launch):**
```bash
# 1. Enable credits
python -m app.scripts.manage_promotions enable-credits

# 2. Create signup bonus for new users
python -m app.scripts.manage_promotions signup-bonus

# 3. Grant free year to beta users
for email in $(cat beta_users.txt); do
  python -m app.scripts.manage_promotions grant-unlimited "$email" 365 "Beta tester"
done
```

**Announce:**
> "Thanks for beta testing! As a thank you, you have
> free unlimited searches for the next year. 🎁
>
> New users: Get $20 free credits with code WELCOME20!"

---

## Testing

**Test the flow:**

1. **Start with credits disabled:**
   ```bash
   python -m app.scripts.manage_promotions disable-credits
   ```

2. **Verify all searches are free**

3. **Enable credits:**
   ```bash
   python -m app.scripts.manage_promotions enable-credits
   ```

4. **Verify credit check happens**

5. **Grant yourself unlimited:**
   ```bash
   python -m app.scripts.manage_promotions grant-unlimited dev@example.com 7 "Testing"
   ```

6. **Verify searches free again**

---

## Analytics Queries

**Check campaign effectiveness:**
```sql
-- How many users redeemed FREEMONTH?
SELECT COUNT(*) FROM user_campaign_redemptions
WHERE campaign_code = 'FREEMONTH';

-- Total credits awarded
SELECT SUM(credits_awarded) FROM user_campaign_redemptions;

-- Most popular campaign
SELECT campaign_code, COUNT(*) as redemptions
FROM user_campaign_redemptions
GROUP BY campaign_code
ORDER BY redemptions DESC;
```

---

## Pro Tips

1. **Start simple:** Disable credits for first month - easiest!

2. **Grandfather early users:** Loyalty matters - give beta users free year

3. **Limited time creates urgency:** "First 100 users get free year!"

4. **Track everything:** Use campaigns (not global disable) for better data

5. **Communicate clearly:**
   - "Free during beta" = temporary
   - "Free trial" = then pay
   - "Early bird bonus" = reward for joining early

6. **Re-engage lapsed users:**
   ```bash
   # Give them 30 days free
   python -m app.scripts.manage_promotions grant-unlimited user@example.com 30 "Win-back campaign"
   ```

---

## Quick Reference

| Goal | Command |
|------|---------|
| Make everything free | `disable-credits` |
| Start charging | `enable-credits` |
| Free month promo | `free-month` |
| Signup bonus | `signup-bonus` |
| VIP access | `grant-unlimited <email> <days> <reason>` |
| Check status | `status` |
| List campaigns | `list-campaigns` |

---

**Ready to launch? Start with:**
```bash
python -m app.scripts.manage_promotions disable-credits
```

All searches will be free! Turn on credits when ready to monetize.
