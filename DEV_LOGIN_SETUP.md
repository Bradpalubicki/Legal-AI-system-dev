# Development Login Setup

## Why You Need This

**Development:** Test features without typing credentials every time
**Staging:** QA testers can access without creating accounts
**Production:** NEVER enable (security risk)

---

## Setup Instructions

### **Step 1: Create Dev User Script** (5 min)

Create `backend/app/scripts/create_dev_user.py`:

```python
"""
Create development/test user account
Run once to create, use for all development
"""
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.utils.auth import hash_password
from app.src.core.database import SessionLocal
from datetime import datetime

def create_dev_user():
    """Create a development test user"""
    db = SessionLocal()

    try:
        # Check if exists
        existing = db.query(User).filter(User.email == "dev@legalai.local").first()

        if existing:
            print("✅ Dev user already exists")
            print(f"   Email: {existing.email}")
            print(f"   Role: {existing.role.value}")
            return existing

        # Create new dev user
        dev_user = User(
            email="dev@legalai.local",
            username="developer",
            first_name="Developer",
            last_name="Account",
            full_name="Developer Account",
            hashed_password=hash_password("DevPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            email_verified_at=datetime.utcnow(),
            is_admin=True,
            is_premium=True,  # Full access for testing all features
        )

        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)

        print("✅ Dev user created successfully!")
        print(f"   Email: {dev_user.email}")
        print(f"   Password: DevPass123!")
        print(f"   Role: {dev_user.role.value}")
        print(f"   Premium: {dev_user.is_premium}")

        return dev_user

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating dev user: {e}")
        raise
    finally:
        db.close()

def create_test_users():
    """Create multiple test users for different roles"""
    db = SessionLocal()

    test_users = [
        {
            "email": "attorney@test.local",
            "username": "test_attorney",
            "first_name": "Test",
            "last_name": "Attorney",
            "role": UserRole.ATTORNEY,
            "password": "Attorney123!"
        },
        {
            "email": "client@test.local",
            "username": "test_client",
            "first_name": "Test",
            "last_name": "Client",
            "role": UserRole.CLIENT,
            "password": "Client123!"
        },
        {
            "email": "user@test.local",
            "username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            "role": UserRole.USER,
            "password": "User123!"
        }
    ]

    created = []
    for user_data in test_users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if existing:
            print(f"   {user_data['email']} - already exists")
            continue

        user = User(
            email=user_data["email"],
            username=user_data["username"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            full_name=f"{user_data['first_name']} {user_data['last_name']}",
            hashed_password=hash_password(user_data["password"]),
            role=user_data["role"],
            is_active=True,
            is_verified=True,
            email_verified_at=datetime.utcnow()
        )

        db.add(user)
        created.append(user_data)

    if created:
        db.commit()
        print(f"\n✅ Created {len(created)} test users:")
        for user_data in created:
            print(f"   {user_data['email']} - {user_data['password']} ({user_data['role'].value})")
    else:
        print("\n   All test users already exist")

    db.close()

if __name__ == "__main__":
    print("Creating development users...\n")
    create_dev_user()
    print()
    create_test_users()
    print("\n✅ Setup complete!")
```

**Run it:**
```bash
cd backend
python -m app.scripts.create_dev_user
```

**Note:** The script uses `@example.com` emails (not `.local`) because Pydantic's email validator requires valid domains.

---

### **Step 2: Add Dev Login Button (Frontend)** (10 min)

Create `frontend/src/components/DevLogin.tsx`:

```typescript
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

interface DevLoginProps {
  enabled?: boolean  // Only show if explicitly enabled
}

export function DevLogin({ enabled = false }: DevLoginProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  // Only show in development
  if (process.env.NODE_ENV !== 'development' || !enabled) {
    return null
  }

  const handleDevLogin = async (role: 'admin' | 'attorney' | 'client' | 'user') => {
    setLoading(true)

    const credentials = {
      admin: { email: 'dev@legalai.local', password: 'DevPass123!' },
      attorney: { email: 'attorney@test.local', password: 'Attorney123!' },
      client: { email: 'client@test.local', password: 'Client123!' },
      user: { email: 'user@test.local', password: 'User123!' }
    }

    try {
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials[role])
      })

      if (response.ok) {
        const data = await response.json()
        localStorage.setItem('token', data.access_token)
        localStorage.setItem('user', JSON.stringify(data.user))
        router.push('/dashboard')
      } else {
        alert('Dev login failed - make sure dev user exists')
      }
    } catch (error) {
      alert('Dev login error - is backend running?')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed bottom-4 right-4 bg-yellow-100 border-2 border-yellow-400 rounded-lg p-4 shadow-lg">
      <div className="text-sm font-bold text-yellow-800 mb-2">
        🛠️ DEV LOGIN (Development Only)
      </div>
      <div className="flex flex-col gap-2">
        <button
          onClick={() => handleDevLogin('admin')}
          disabled={loading}
          className="px-3 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600"
        >
          Admin
        </button>
        <button
          onClick={() => handleDevLogin('attorney')}
          disabled={loading}
          className="px-3 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600"
        >
          Attorney
        </button>
        <button
          onClick={() => handleDevLogin('client')}
          disabled={loading}
          className="px-3 py-1 bg-green-500 text-white rounded text-xs hover:bg-green-600"
        >
          Client
        </button>
        <button
          onClick={() => handleDevLogin('user')}
          disabled={loading}
          className="px-3 py-1 bg-gray-500 text-white rounded text-xs hover:bg-gray-600"
        >
          User
        </button>
      </div>
      <div className="text-xs text-yellow-700 mt-2">
        Quick login for testing
      </div>
    </div>
  )
}
```

**Add to your login page:**

```typescript
// frontend/src/app/login/page.tsx
import { DevLogin } from '@/components/DevLogin'

export default function LoginPage() {
  return (
    <div>
      {/* Your existing login form */}

      {/* Dev login (only shows in development) */}
      <DevLogin enabled={true} />
    </div>
  )
}
```

---

### **Step 3: Environment-Based Config** (5 min)

Update `.env.local`:

```bash
# Development settings
NODE_ENV=development
NEXT_PUBLIC_ENABLE_DEV_LOGIN=true

# Never set this to true in production!
```

Update component to check env:

```typescript
export function DevLogin() {
  const isDev = process.env.NODE_ENV === 'development'
  const enabled = process.env.NEXT_PUBLIC_ENABLE_DEV_LOGIN === 'true'

  if (!isDev || !enabled) {
    return null  // Invisible in production
  }

  // ... rest of component
}
```

---

## Benefits

### **Development:**
```
Before:
1. Open login page
2. Type email: dev@example.com
3. Type password: DevPass123!
4. Click login
5. Repeat 100 times per day 😫

After:
1. Click "Admin" button
2. Done! ✅
```

### **Testing Different Roles:**
```
Click "Admin" → Test admin features
Click "Attorney" → Test attorney features
Click "Client" → Test client features
Click "User" → Test regular user features

No need to logout/login manually!
```

### **QA/Beta Testing:**
```
Share staging URL with testers:
"Click the yellow 'Dev Login' button to test"
No need to create/remember accounts
```

---

## Security Best Practices

### **✅ DO:**
- Only enable in development (check NODE_ENV)
- Use fake email domains (.local, .test)
- Document credentials clearly
- Remove from production builds
- Use environment variables

### **❌ DON'T:**
- Enable in production (NEVER!)
- Use real email addresses
- Commit passwords to git (use .env)
- Share dev credentials publicly
- Leave debug features accessible

---

## Production Safety

### **Auto-Disable in Production:**

```typescript
// frontend/src/components/DevLogin.tsx
export function DevLogin() {
  // TRIPLE CHECK: Never show in production
  if (process.env.NODE_ENV === 'production') {
    return null
  }

  if (process.env.NEXT_PUBLIC_VERCEL_ENV === 'production') {
    return null
  }

  // Only show if explicitly enabled
  if (process.env.NEXT_PUBLIC_ENABLE_DEV_LOGIN !== 'true') {
    return null
  }

  // ... rest of component
}
```

### **Vercel Environment Variables:**

```
Development (.env.local):
NEXT_PUBLIC_ENABLE_DEV_LOGIN=true

Production (Vercel):
NEXT_PUBLIC_ENABLE_DEV_LOGIN=false  (or don't set at all)
```

---

## Alternative: Seed Database Script

Instead of UI button, create a script to seed test data:

```python
# backend/app/scripts/seed_dev_data.py
"""
Seed database with test data for development
"""

def seed_database():
    # Create dev users
    create_dev_user()
    create_test_users()

    # Create test cases
    create_test_cases()

    # Create test documents
    create_test_documents()

    print("✅ Database seeded with test data!")

if __name__ == "__main__":
    seed_database()
```

**Run once when setting up:**
```bash
python -m app.scripts.seed_dev_data
```

---

## Quick Setup (Choose One)

### **Option A: Simple Dev User** (Recommended for solo dev)

```bash
# 1. Create the script (5 min)
# 2. Run it once
python -m app.scripts.create_dev_user

# 3. Login manually when needed
# Email: dev@legalai.local
# Password: DevPass123!
```

### **Option B: Auto-Login Button** (Better for team)

```bash
# 1. Create dev user script
# 2. Add DevLogin component
# 3. Enable in .env.local
# 4. Click button to login instantly
```

### **Option C: Both** (Best)

```bash
# Backend: Dev user script
# Frontend: Auto-login button
# Result: Instant testing, multiple roles
```

---

## Testing Checklist

After setup, test each role:

- [ ] Admin login works
- [ ] Attorney login works
- [ ] Client login works
- [ ] User login works
- [ ] Each role sees correct features
- [ ] Production build doesn't show dev login
- [ ] Real user registration still works

---

## Summary

**YES - Create dev login because:**
1. ✅ Saves massive time (100+ logins per day)
2. ✅ Test different roles easily
3. ✅ QA testers can access easily
4. ✅ No pollution of real user data
5. ✅ Reproducible bug testing

**Implementation time:** 15-20 minutes
**Time saved:** Hours per week

**Next steps:**
1. Create the dev user script
2. Run it once
3. Use dev@legalai.local / DevPass123! for testing
4. (Optional) Add auto-login button

Want me to create the script files for you?
