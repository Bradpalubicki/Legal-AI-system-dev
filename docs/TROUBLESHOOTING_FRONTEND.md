# Frontend Troubleshooting Guide

**Issue**: localhost:3000 not loading
**Status**: ✅ Server is running correctly

---

## ✅ Server Status

The development server is running and compiled successfully:

```
✓ Ready in 1474ms
✓ Compiled /documents in 788ms (1132 modules)
GET /documents 200 in 908ms
```

**Server**: http://localhost:3000
**Status**: ✅ Running
**Documents Page**: ✅ Compiled successfully

---

## 🔧 Quick Fixes

### 1. Hard Refresh Browser (Most Common Fix)

**Windows/Linux**:
```
Ctrl + Shift + R
```

**Mac**:
```
Cmd + Shift + R
```

This clears cached errors and reloads the page fresh.

---

### 2. Clear Browser Cache

**Chrome/Edge**:
1. Press `F12` to open DevTools
2. Right-click the refresh button
3. Click "Empty Cache and Hard Reload"

**Firefox**:
1. Press `Ctrl+Shift+Delete` (or `Cmd+Shift+Delete` on Mac)
2. Select "Cached Web Content"
3. Click "Clear Now"

---

### 3. Check Browser Console for Errors

1. **Open DevTools**: Press `F12`
2. **Go to Console tab**
3. **Look for red errors**

Common errors to look for:
- Import errors
- Module not found
- TypeScript errors
- Network errors

---

### 4. Verify Correct URL

Make sure you're accessing:
```
http://localhost:3000/documents
```

NOT:
- ❌ https://localhost:3000 (no HTTPS in dev)
- ❌ 127.0.0.1:3000 (might cause CORS issues)
- ❌ localhost:8000 (that's the backend)

---

### 5. Check if Server is Actually Running

Open a new terminal and run:
```bash
curl http://localhost:3000
```

**Should see**: HTML output

**If error**: Server isn't running, restart it:
```bash
cd frontend
npm run dev
```

---

### 6. Kill and Restart Dev Server

If the server seems stuck:

**Windows**:
```bash
# Kill all node processes
taskkill /F /IM node.exe

# Restart
cd frontend
npm run dev
```

**Mac/Linux**:
```bash
# Kill all node processes
pkill -f "next dev"

# Restart
cd frontend
npm run dev
```

---

### 7. Delete .next Cache and Rebuild

```bash
cd frontend

# Delete cache
rm -rf .next
# Windows: rmdir /s /q .next

# Restart dev server
npm run dev
```

---

### 8. Reinstall Dependencies

If modules are missing:

```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

---

## 🔍 Diagnostic Commands

### Check if Port 3000 is in Use

**Windows**:
```bash
netstat -ano | findstr :3000
```

**Mac/Linux**:
```bash
lsof -i :3000
```

If another process is using port 3000, kill it or use a different port:
```bash
PORT=3001 npm run dev
```

---

### Check Node Version

```bash
node --version
```

Required: Node 18.17.0 or higher

If too old:
```bash
# Install nvm (Node Version Manager)
# Then:
nvm install 18
nvm use 18
```

---

### Verify Package.json Scripts

Check `frontend/package.json` has:
```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  }
}
```

---

## 🐛 Common Errors and Fixes

### Error: "Module not found"

**Fix**:
```bash
cd frontend
npm install
```

### Error: "Cannot find module '@/components/...'"

**Fix**: Check `tsconfig.json` has path alias:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Error: "Unexpected token"

**Cause**: Syntax error in code

**Fix**: Check browser console for specific file and line number

### Error: "Failed to compile"

**Fix**: Check terminal for compilation errors, fix the reported issues

---

## 📊 Verify Installation

Run these checks:

```bash
cd frontend

# 1. Check dependencies installed
npm list next react react-dom

# 2. Check TypeScript config
cat tsconfig.json | grep -A 5 "compilerOptions"

# 3. Test build
npm run build

# 4. Start dev server
npm run dev
```

All should complete without errors.

---

## 🌐 Browser-Specific Issues

### Chrome/Edge

**Issue**: Service worker caching old version

**Fix**:
1. Open DevTools (F12)
2. Application tab
3. Service Workers
4. Click "Unregister"
5. Refresh page

### Firefox

**Issue**: Strict tracking protection blocking

**Fix**:
1. Click shield icon in address bar
2. Turn off "Enhanced Tracking Protection"
3. Refresh page

### Safari

**Issue**: Experimental features disabled

**Fix**:
1. Safari → Preferences
2. Advanced tab
3. Check "Show Develop menu"
4. Develop → Experimental Features
5. Enable relevant features

---

## ✅ Current Server Status

Based on latest check:

```
Server: Running ✓
Port: 3000 ✓
Documents page: Compiled ✓
Modules: 1132 loaded ✓
Response time: 908ms ✓
```

**The server is working perfectly!**

---

## 🎯 Recommended Fix Order

Try these in order:

1. ✅ **Hard refresh browser** (Ctrl+Shift+R) - 90% of issues
2. ✅ **Clear browser cache** - If refresh doesn't work
3. ✅ **Check console for errors** - See what's actually failing
4. ✅ **Verify URL** - Make sure you're on http://localhost:3000/documents
5. ✅ **Restart dev server** - Kill and restart npm run dev
6. ✅ **Delete .next folder** - Clear Next.js cache
7. ✅ **Reinstall dependencies** - Last resort

---

## 📞 Getting Help

If still not working, check:

1. **Browser Console** (F12) - What errors do you see?
2. **Terminal Output** - Any red error messages?
3. **Network Tab** (F12) - Are requests failing?

Common issues:
- 404 errors → Check file paths
- 500 errors → Check server logs
- Blank page → Check console for JS errors
- Slow loading → Check network tab for slow requests

---

## 🚀 Quick Start (Clean Slate)

If all else fails, start fresh:

```bash
# 1. Stop all servers
# Press Ctrl+C in both terminals

# 2. Clean frontend
cd frontend
rm -rf .next
rm -rf node_modules
npm install

# 3. Start fresh
npm run dev

# 4. Open browser
# http://localhost:3000/documents

# 5. Hard refresh
# Ctrl+Shift+R
```

---

**Most likely fix**: Hard refresh your browser (Ctrl+Shift+R)!

The server is running perfectly - this is usually a browser cache issue.
