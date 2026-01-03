# Legal AI System - Launch Checklist

Complete launch guide for deploying tier-based pricing and pay-per-case access.

---

## 🚀 Phase 1: Beta Launch (Free Access)

**Goal:** Test all features with real users before charging

### Week 1: Setup & Configuration

- [ ] **Database Migrations**
  ```bash
  cd backend
  alembic revision --autogenerate -m "Add case access and feature flags"
  alembic upgrade head
  ```

- [ ] **Environment Variables**
  ```bash
  # Add to .env
  STRIPE_SECRET_KEY=sk_test_...
  STRIPE_PUBLISHABLE_KEY=pk_test_...
  STRIPE_WEBHOOK_SECRET_CASE_ACCESS=whsec_...

  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USERNAME=your-email@gmail.com
  SMTP_PASSWORD=your-app-password
  FROM_EMAIL=notifications@yourdomain.com

  FRONTEND_URL=http://localhost:3000
  ```

- [ ] **Apply Beta Launch Preset**
  ```bash
  # Via admin API
  POST /api/v1/admin/tiers/presets/beta-launch
  ```

  This will:
  - ✅ Disable credit requirements
  - ✅ Create 30-day free access campaign
  - ✅ Unlock all features for testing

- [ ] **Create Test Billing Plans in Stripe**
  ```
  - Case Monitor ($5 one-time, $19/month)
  - Pro ($49/month)
  - Firm ($199/month)
  ```

- [ ] **Register API Routes**
  Add to `backend/main.py`:
  ```python
  from app.api.feature_access import router as feature_access_router
  app.include_router(feature_access_router, prefix="/api/v1/features", tags=["features"])

  from app.api.case_access import router as case_access_router
  app.include_router(case_access_router)

  from app.api.admin.tier_management import router as tier_admin_router
  app.include_router(tier_admin_router)
  ```

### Week 2-4: Beta Testing

- [ ] **Invite Beta Users** (50-100 users)
  - Create user overrides for unlimited access
  - Track usage and feedback
  - Monitor for bugs

- [ ] **Test All Features**
  - [ ] Case access purchase flow
  - [ ] Stripe checkout integration
  - [ ] Webhook processing
  - [ ] Email notifications
  - [ ] Feature gates on all endpoints
  - [ ] Upgrade prompts in UI

- [ ] **Analytics Setup**
  - Track feature usage
  - Monitor conversion funnels
  - Identify most-used features

- [ ] **Performance Testing**
  - Load test payment processing
  - Test concurrent case access checks
  - Verify database query performance

---

## 💰 Phase 2: Soft Launch (Limited Paid Access)

**Goal:** Start charging a small group while refining pricing

### Week 5: Preparation

- [ ] **Legal & Compliance**
  - [ ] Terms of Service updated
  - [ ] Privacy Policy reviewed
  - [ ] Refund policy defined
  - [ ] GDPR compliance verified

- [ ] **Stripe Production Setup**
  - [ ] Move to live API keys
  - [ ] Set up webhook endpoints
  - [ ] Test live payments with small amounts
  - [ ] Configure tax collection (if applicable)

- [ ] **Email Templates**
  - [ ] Purchase confirmation
  - [ ] Receipt/invoice
  - [ ] Case monitoring welcome
  - [ ] Feature unlocked notifications
  - [ ] Subscription renewal reminders

- [ ] **Support Infrastructure**
  - [ ] Support email configured
  - [ ] FAQ page created
  - [ ] Refund request form
  - [ ] Billing support docs

### Week 6: Soft Launch

- [ ] **Apply Production Preset (for small group)**
  ```bash
  POST /api/v1/admin/tiers/presets/production-launch
  ```

  This enables:
  - ✅ Credit requirements
  - ✅ Tier-based access
  - ✅ 20% launch discount (90 days)

- [ ] **Enable for 10% of Users**
  - Use feature flags to gradually roll out
  - Monitor closely for issues
  - Gather feedback on pricing

- [ ] **Monitor Metrics**
  - Conversion rate (free → paid)
  - Average purchase value
  - Churn rate
  - Support ticket volume

---

## 🎯 Phase 3: Full Launch (Public Availability)

**Goal:** Full rollout with pricing tiers live

### Week 7-8: Full Rollout

- [ ] **Final Pricing Adjustments**
  - Review soft launch data
  - Adjust prices if needed
  - Update Stripe products

- [ ] **Marketing Campaign**
  - [ ] Landing page updated with pricing
  - [ ] Blog post announcing tiers
  - [ ] Email existing users
  - [ ] Social media announcements

- [ ] **Enable for All Users**
  - Remove beta campaign
  - Apply production configuration globally
  - Monitor for issues

- [ ] **Launch Promotions**
  Create campaigns:
  ```python
  # Early adopter discount
  {
    "name": "Early Adopter - 30% Off",
    "discount_percentage": 30,
    "ends_at": "2025-02-01",
    "max_redemptions": 500,
    "new_users_only": true
  }

  # First case free
  {
    "name": "First Case Free",
    "campaign_type": "free_credits",
    "free_credits": 5,
    "new_users_only": true
  }
  ```

---

## ✅ Pre-Launch Verification

### Backend Checklist

- [ ] All database migrations applied
- [ ] Stripe webhooks configured and tested
- [ ] Email notifications working
- [ ] Case access validation on all protected endpoints
- [ ] Feature gates properly configured
- [ ] Admin endpoints secured (admin-only access)
- [ ] Error handling for payment failures
- [ ] Refund handling tested
- [ ] Rate limiting configured
- [ ] Monitoring and logging enabled

### Frontend Checklist

- [ ] Pricing page displays correctly
- [ ] Feature gates show upgrade prompts
- [ ] Checkout flow works end-to-end
- [ ] Success page displays after purchase
- [ ] My Cases dashboard functional
- [ ] Notification settings work
- [ ] Mobile responsive
- [ ] Loading states on all async operations
- [ ] Error messages user-friendly

### Payment Testing

- [ ] Test card payments (4242 4242 4242 4242)
- [ ] Test declined cards
- [ ] Test webhook delivery
- [ ] Test refund flow
- [ ] Test subscription cancellation
- [ ] Verify receipts sent to customers
- [ ] Test international cards (if applicable)

### Security Audit

- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF tokens implemented
- [ ] Rate limiting on payment endpoints
- [ ] Webhook signature verification
- [ ] PII data encrypted
- [ ] Access control tested

---

## 📊 Post-Launch Monitoring

### Daily (First Week)

- [ ] Monitor error logs
- [ ] Check payment success rate
- [ ] Review support tickets
- [ ] Track conversion rates
- [ ] Monitor server performance

### Weekly

- [ ] Review tier distribution
- [ ] Analyze feature usage
- [ ] Check churn rate
- [ ] Review customer feedback
- [ ] Optimize slow endpoints

### Monthly

- [ ] Calculate MRR (Monthly Recurring Revenue)
- [ ] Analyze customer lifetime value
- [ ] Review and adjust pricing
- [ ] Plan new features based on feedback

---

## 🛠 Admin Commands

### Feature Flag Management

```bash
# Disable credits (beta mode)
POST /api/v1/admin/tiers/feature-flags/credits_enabled
{
  "is_enabled": false
}

# Enable credits (production mode)
POST /api/v1/admin/tiers/feature-flags/credits_enabled
{
  "is_enabled": true
}
```

### Grant Free Access to User

```bash
POST /api/v1/admin/tiers/user-overrides
{
  "user_id": 123,
  "flag_key": "unlimited_access",
  "is_enabled": true,
  "expires_at": "2025-12-31",
  "reason": "Beta tester reward"
}
```

### Create Promotional Campaign

```bash
POST /api/v1/admin/tiers/campaigns
{
  "name": "Summer Sale - 25% Off",
  "description": "25% off all plans",
  "campaign_type": "discount",
  "discount_percentage": 25,
  "starts_at": "2025-06-01T00:00:00",
  "ends_at": "2025-08-31T23:59:59",
  "max_redemptions": 1000,
  "new_users_only": false
}
```

### Change User Tier

```bash
POST /api/v1/admin/tiers/change-tier
{
  "user_id": 123,
  "new_tier": "pro",
  "reason": "Upgraded for excellent feedback"
}
```

---

## 🔧 Troubleshooting

### Payments Not Processing

1. Check Stripe webhook is receiving events
2. Verify webhook secret matches
3. Check server logs for errors
4. Test with Stripe CLI

```bash
stripe listen --forward-to localhost:8000/api/v1/case-access/webhook
```

### Users Not Getting Access After Purchase

1. Check webhook processed successfully
2. Verify CaseAccess record created
3. Check status is ACTIVE
4. Verify case_id matches

### Notifications Not Sending

1. Check SMTP credentials
2. Verify FROM_EMAIL is configured
3. Check email templates render correctly
4. Review notification service logs

### Feature Gates Not Working

1. Verify user has correct role
2. Check subscription status
3. Review feature flag configuration
4. Clear any stale caches

---

## 📈 Success Metrics

### Week 1 Goals

- 10% of beta users purchase case access
- 5% convert to Pro subscription
- <1% refund rate
- 99.9% payment success rate

### Month 1 Goals

- 100 paying customers
- $2,000 MRR
- 4-star average rating
- <5% churn rate

### Quarter 1 Goals

- 500 paying customers
- $15,000 MRR
- Feature parity with competitors
- Positive unit economics

---

## 🎓 Training Materials

### For Support Team

- [ ] How to check user's tier
- [ ] How to process refunds
- [ ] How to grant promotional access
- [ ] Common troubleshooting steps

### For Users

- [ ] Getting Started guide
- [ ] Pricing FAQ
- [ ] How to monitor cases
- [ ] How to upgrade/downgrade

---

## 🚨 Rollback Plan

If major issues arise:

1. **Disable new payments**
   ```bash
   POST /api/v1/admin/tiers/feature-flags/payments_enabled
   {"is_enabled": false}
   ```

2. **Grant free access to all**
   ```bash
   POST /api/v1/admin/tiers/presets/beta-launch
   ```

3. **Process refunds for affected users**

4. **Communicate transparently**
   - Email all affected users
   - Explain issue and resolution
   - Offer compensation if appropriate

---

## ✅ Launch Day Checklist

**T-1 Day:**
- [ ] Final testing in staging
- [ ] Backup database
- [ ] Review monitoring dashboards
- [ ] Prepare support team
- [ ] Draft announcement emails

**Launch Day:**
- [ ] Apply production configuration
- [ ] Send announcement emails (in batches)
- [ ] Monitor closely for issues
- [ ] Be ready to rollback if needed
- [ ] Celebrate! 🎉

**T+1 Day:**
- [ ] Review metrics
- [ ] Address any urgent issues
- [ ] Respond to user feedback
- [ ] Plan optimizations

---

## 📞 Emergency Contacts

- **Stripe Support:** [Stripe Dashboard](https://dashboard.stripe.com)
- **Server Issues:** [Your hosting provider]
- **Database Issues:** [Your DBA contact]
- **Code Issues:** [Your dev team lead]

---

## 🎉 You're Ready to Launch!

This system includes:
- ✅ 3 pricing tiers with 30+ features
- ✅ Pay-per-case ($5) and subscription options
- ✅ Complete Stripe integration
- ✅ Automated notifications
- ✅ Admin controls
- ✅ Feature flags for safe rollout
- ✅ Promotional campaigns
- ✅ Comprehensive access control

**Good luck with your launch!** 🚀
