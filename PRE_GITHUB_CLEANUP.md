# Pre-GitHub Cleanup Tasks

## Files to Remove Before Committing

Based on current git status, these files should be removed or moved:

### Test/Temporary Files (DELETE)
```bash
# Test JSON files - contain test data, not needed in git
rm -f case_25-10344_current.json
rm -f case_25-10344_fixed.json
rm -f case_25-10344_test.json
rm -f case_69566447_test.json
rm -f cl_test.json
rm -f final_test.json

# Backend test/analysis scripts
rm -f backend/analyze_documents.py
rm -f backend/analyze_response.py
rm -f backend/check_missing_entries.py
rm -f backend/check_raw_entries.py
rm -f backend/docket_analysis.json
rm -f backend/docket_response.json
rm -f backend/send_test_notification.py
rm -f backend/test_email_notification.py
rm -f verify_docket.py

# Windows batch scripts (keep in scripts/ folder if needed)
rm -f restart_backend.bat
rm -f restart_services.bat
```

### Investigation/Documentation Files (REVIEW & ARCHIVE)
```bash
# If valuable, move to docs/ folder
mv INVESTIGATION.md docs/investigation-notes.md

# Or delete if no longer needed
rm -f INVESTIGATION.md
```

### New Feature Files (REVIEW BEFORE COMMIT)

These look like new features - review for:
- Hard-coded secrets
- Personal email addresses
- Test data

```
backend/app/api/case_notifications.py
backend/app/api/notification_history.py
backend/app/api/test_notification.py
backend/app/models/case_notification_history.py
backend/app/services/case_monitor_service.py
backend/app/services/email_notification_service.py
backend/app/src/services/COURTLISTENER_API.md
backend/app/src/services/TROUBLESHOOTING.md
frontend/src/hooks/useCaseMonitorNotifications.ts
```

**Action**:
```bash
# Review each file for sensitive data
git diff --cached backend/app/api/case_notifications.py
# Look for: email addresses, API keys, test data
```

---

## Quick Cleanup Commands

### Option 1: Delete All Test Files
```bash
# From project root
rm -f *.json
rm -f *.bat
rm -f backend/*.json
rm -f backend/*.py
rm -f INVESTIGATION.md
```

### Option 2: Move to Temporary Folder
```bash
# Create temp folder
mkdir -p temp/pre-github-cleanup

# Move instead of delete (safer)
mv *.json temp/pre-github-cleanup/ 2>/dev/null
mv *.bat temp/pre-github-cleanup/ 2>/dev/null
mv backend/analyze_*.py temp/pre-github-cleanup/ 2>/dev/null
mv backend/test_*.py temp/pre-github-cleanup/ 2>/dev/null
mv backend/check_*.py temp/pre-github-cleanup/ 2>/dev/null
mv backend/*.json temp/pre-github-cleanup/ 2>/dev/null
mv verify_docket.py temp/pre-github-cleanup/ 2>/dev/null
mv INVESTIGATION.md temp/pre-github-cleanup/ 2>/dev/null

# Review what was moved
ls -la temp/pre-github-cleanup/

# Add temp/ to .gitignore
echo "temp/" >> .gitignore
```

---

## Verify Clean State

After cleanup:
```bash
# Check status
git status

# Should show only:
# - Modified files (review each)
# - New feature files (case_notifications, etc.)
# - NOT: test files, .json, .bat files

# Review modified files
git diff backend/app/api/courtlistener_endpoints.py
git diff backend/app/api/monitoring_endpoints.py
git diff backend/app/src/services/courtlistener_service.py
git diff backend/main.py
git diff frontend/src/components/CaseTracking/EnhancedCaseTracker.tsx

# Check for sensitive data in each
```

---

## Pre-Commit Checklist

Before `git add`:

- [ ] Removed all test JSON files
- [ ] Removed all test Python scripts
- [ ] Removed all Windows batch files (or moved to scripts/)
- [ ] Reviewed modified files for sensitive data
- [ ] No email addresses except in .env.example
- [ ] No API keys except placeholders in .env.example
- [ ] No hard-coded localhost URLs (or documented as known issue)
- [ ] All new files reviewed and ready to commit

---

## Sensitive Data Scan

Run this before committing:
```bash
# Search for potential secrets in staged files
git diff --cached | grep -i "api.key\|password\|secret\|token" | grep -v "your-.*-here" | grep -v ".env.example"

# Should return empty or only .env.example references
```

---

## Safe Commit Process

```bash
# 1. Clean up test files
mkdir -p temp/pre-github-cleanup
mv *.json *.bat backend/*.json backend/analyze_*.py backend/test_*.py temp/

# 2. Review what's left
git status

# 3. Stage new features
git add backend/app/api/case_notifications.py
git add backend/app/api/notification_history.py
git add backend/app/models/case_notification_history.py
git add backend/app/services/case_monitor_service.py
git add backend/app/services/email_notification_service.py
git add frontend/src/hooks/useCaseMonitorNotifications.ts

# 4. Stage documentation
git add backend/app/src/services/COURTLISTENER_API.md
git add backend/app/src/services/TROUBLESHOOTING.md

# 5. Stage modified files (after review)
git add backend/app/api/courtlistener_endpoints.py
git add backend/app/api/monitoring_endpoints.py
git add backend/app/src/services/courtlistener_service.py
git add backend/main.py
git add frontend/src/components/CaseTracking/EnhancedCaseTracker.tsx

# 6. Commit
git commit -m "feat: Add case monitoring and notification system

- Add CourtListener case monitoring
- Implement email notifications for case updates
- Add notification history tracking
- Enhance case tracker UI
- Update API endpoints for monitoring"

# 7. Review before push
git log -1 --stat
```

---

## After First Commit

### Tag as Pre-Production
```bash
git tag -a v0.1.0-alpha -m "Initial commit - pre-production state

Known issues:
- Hard-coded URLs in frontend
- TypeScript errors suppressed
- Limited test coverage
- Security improvements needed

See DEPLOY.md for deployment guide"

git push origin main --tags
```

### Create GitHub Repository

```bash
# On GitHub, create new repository (private recommended)
# Then:
git remote add origin https://github.com/yourusername/legal-ai-system.git
git branch -M main
git push -u origin main
```

---

## Post-GitHub Setup

1. **Enable branch protection**
   - Protect main branch
   - Require pull request reviews
   - Require status checks

2. **Add GitHub Secrets**
   - OPENAI_API_KEY
   - ANTHROPIC_API_KEY
   - COURTLISTENER_API_KEY
   - DATABASE_URL (for CI/CD)

3. **Set up GitHub Actions** (future)
   - Run tests on PR
   - Type checking
   - Lint checking
   - Build verification

4. **Add collaborators** (if team project)
   - Set appropriate permissions
   - Review access levels
