# GitHub Setup Commands

## Step 1: Add GitHub as Remote

Replace YOUR_USERNAME with your actual GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/legal-ai-system.git
```

## Step 2: Verify Remote was Added

```bash
git remote -v
```

Should show:
```
origin  https://github.com/YOUR_USERNAME/legal-ai-system.git (fetch)
origin  https://github.com/YOUR_USERNAME/legal-ai-system.git (push)
```

## Step 3: Rename Branch to 'main' (GitHub default)

```bash
git branch -M main
```

## Step 4: Push Code to GitHub

```bash
git push -u origin main
```

**What happens:**
- Uploads all your code to GitHub
- Creates 'main' branch on GitHub
- Sets up tracking so future pushes just need `git push`

**First time:** GitHub will ask for authentication
- Enter GitHub username
- Enter password OR personal access token (see below)

---

## GitHub Authentication

### Option 1: GitHub Desktop (Easiest)
1. Download: https://desktop.github.com/
2. Sign in with GitHub account
3. Clone repository through desktop app
4. Handles authentication automatically

### Option 2: Personal Access Token (Recommended for CLI)
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name: "legal-ai-system-dev"
4. Expiration: 90 days
5. Select scopes:
   - ✅ repo (all)
   - ✅ workflow
6. Click "Generate token"
7. **COPY TOKEN IMMEDIATELY** (you won't see it again)
8. Use this token as password when pushing

### Option 3: SSH Key (Most Secure)
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your-email@example.com"

# Copy public key
cat ~/.ssh/id_ed25519.pub

# Add to GitHub: https://github.com/settings/keys
```

Then use SSH URL instead:
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/legal-ai-system.git
```

---

## Verification Commands

After pushing, verify on GitHub:

```bash
# Check remote connection
git remote -v

# Check branch tracking
git branch -vv

# View recent commits
git log --oneline -5
```

Then visit: https://github.com/YOUR_USERNAME/legal-ai-system
- You should see all your code
- README.md should display
- Check commits are there

---

## Common Issues & Solutions

### Issue: "repository not found"
**Solution:** Check repository name and your username in the URL

### Issue: "permission denied"
**Solution:** Use personal access token instead of password

### Issue: "Updates were rejected"
**Solution:** Repository shouldn't have this on first push. If it does:
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### Issue: Large files rejected
**Solution:** Check .gitignore is working
```bash
git status
# Should NOT show .env, node_modules/, *.db files
```

---

## Next Steps After Successful Push

1. ✅ Verify code on GitHub web interface
2. ⚠️ **IMMEDIATELY ROTATE API KEYS** (security best practice)
3. 🔒 Add GitHub Secrets (for CI/CD later)
4. 📝 Update README with GitHub badges
5. 🚀 Deploy to production (optional)

See TOMORROW_CHECKLIST.md for detailed next steps.
