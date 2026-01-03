# CourtListener Document Fetching - Troubleshooting Guide

## ⚠️ SYMPTOM: "Load All Documents" returns 0 documents or wrong documents

### FIRST CHECK THIS:

1. **Verify Correct Endpoint Usage** ✅
   ```python
   # In backend/app/src/services/courtlistener_service.py
   # Function: get_docket_with_documents()

   # CORRECT:
   url = f"{self.base_url}/docket-entries/?docket={docket_id}&order_by=entry_number"

   # WRONG - DO NOT USE:
   url = f"{self.base_url}/recap-documents/?docket_id={docket_id}"  # ❌ Returns ALL documents
   url = f"{self.base_url}/dockets/{docket_id}/"  # ❌ Doesn't include entries
   ```

2. **Check Backend Logs**
   Look for these log messages:
   ```
   ✅ GOOD: "Fetching docket entries page 1: .../docket-entries/?docket=..."
   ✅ GOOD: "Page 1: Found X docket entries"
   ✅ GOOD: "✓ Extracted X total documents from docket..."

   ⚠️ BAD: "⚠️ WARNING: Got 0 documents for docket..."
   ```

3. **Test the Endpoint Directly**
   ```bash
   # Should return documents:
   curl -s http://localhost:8000/api/v1/courtlistener/docket/69566447/documents | grep "total_documents"

   # Expected: "total_documents":97 (or similar positive number)
   # Problem: "total_documents":0
   ```

4. **Verify Backend is Running New Code**
   - Check if backend auto-reload completed successfully
   - Look for "Application startup complete" after file changes
   - If stuck, force restart:
     ```bash
     cd backend
     find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
     find . -name "*.pyc" -delete 2>/dev/null
     taskkill //F //IM python.exe
     uvicorn main:app --reload --host 0.0.0.0 --port 8000
     ```

### Common Causes & Solutions:

| Problem | Cause | Solution |
|---------|-------|----------|
| 0 documents returned | Using `/dockets/{id}/` endpoint | Use `/docket-entries/?docket={id}` |
| 0 documents returned | Using `/recap-documents/?docket_id={id}` | Use `/docket-entries/?docket={id}` |
| Wrong documents (from different cases) | Using wrong endpoint | Use `/docket-entries/?docket={id}` |
| Backend stuck/not reloading | Auto-reload failed | Clear cache + force restart |
| Frontend shows 0 but API works | Browser cache | Hard refresh (Ctrl+Shift+R) |

### Reference Files:
- **Implementation**: `backend/app/src/services/courtlistener_service.py:415-522`
- **API Guide**: `backend/app/src/services/COURTLISTENER_API.md`
- **Investigation**: `INVESTIGATION.md`

### Quick Fix Checklist:
- [ ] Check endpoint in `courtlistener_service.py:451` - should be `/docket-entries/`
- [ ] Check parameter name - should be `?docket={id}` not `?docket_id={id}`
- [ ] Clear Python cache: `find . -type d -name "__pycache__" -exec rm -rf {} +`
- [ ] Restart backend if auto-reload stuck
- [ ] Hard refresh browser (Ctrl+Shift+R)
- [ ] Check backend logs for warnings

### Last Known Working Configuration:
- **Date**: 2025-11-12
- **Endpoint**: `/docket-entries/?docket={docket_id}`
- **Test Case**: Docket 69566447 returns 97 documents
- **File**: `courtlistener_service.py` lines 415-522

---

**Remember**: The CourtListener API structure is counter-intuitive. Always use the docket-entries endpoint, not the recap-documents or dockets endpoints!
