# Quick Start: Multi-Document Upload

**Status**: ✅ **READY TO USE**
**Integration**: Option 1 - Full-Featured Component

---

## 🚀 You're All Set!

The multi-document upload feature is now **live** on your main documents page!

---

## How to Access

### 1. Start Your Application

```bash
# Terminal 1 - Start Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2 - Start Frontend
cd frontend
npm run dev
```

### 2. Navigate to Documents Page

Open your browser and go to:
```
http://localhost:3000/documents
```

---

## What You'll See

### Main Documents Page Layout

```
┌─────────────────────────────────────────────────────────┐
│ Document Management                                     │
│ Upload, analyze, and manage your legal documents       │
│                                                         │
│ ✓ Multi-Upload  ✓ AI Analysis  ✓ Drag & Drop          │
│                                                         │
│ Upload Documents                    [📚 View Library]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│         ⬆  DROP FILES HERE                             │
│                                                         │
│    Click to upload or drag and drop                    │
│    Multiple files supported                            │
│    PDF, DOC, DOCX, TXT • Max 50MB                     │
│                                                         │
│    ↑ 3 concurrent uploads   AI-powered analysis        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## How to Use

### Method 1: Click to Upload

1. **Click** the upload zone
2. **Select multiple files** (hold Ctrl/Cmd to select many)
3. Click **Open**
4. Watch the progress bars!

### Method 2: Drag & Drop

1. **Select files** in your file explorer
2. **Drag** them over the upload zone
3. **Drop** when the zone highlights
4. Processing starts automatically!

---

## What Happens Next

### Upload Process (Per File)

```
1. File Added to Queue
   Status: Pending
   Progress: 0%

2. Text Extraction
   Status: Uploading
   Progress: 10%

3. AI Analysis Started
   Status: Analyzing
   Progress: 50%

4. Processing Complete
   Status: Complete
   Progress: 100%

5. Added to Library
   ✓ Ready to view
```

### Real-Time Tracking

You'll see a **statistics dashboard**:
```
┌─────────┬─────────┬───────────┬──────────┬─────────┐
│  Total  │ Pending │Processing │ Complete │ Failed  │
│    10   │    2    │     3     │     5    │    0    │
└─────────┴─────────┴───────────┴──────────┴─────────┘
```

And an **upload queue**:
```
✓ contract.pdf         [Complete]      100%
🔄 agreement.pdf       [Analyzing...]   75% ████████████████████████████████░░░░░░░░
🔄 complaint.pdf       [Uploading...]   25% ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
📄 motion.pdf          [Waiting...]      0%
```

---

## View Your Documents

### Toggle to Library View

Click the **"📚 View Library"** button at the top to see all your uploaded documents.

### Document Library

```
┌─────────────────────────────────────────────────────────┐
│ Document Library (5)                                    │
├─────────────────────────────────────────────────────────┤
│ 📄 contract.pdf                                    [🗑️] │
│    Uploaded: 12/20/2024, 3:45 PM                       │
│    This is a contract between Party A and Party B...   │
│                                                         │
│ 📄 agreement.pdf                                   [🗑️] │
│    Uploaded: 12/20/2024, 3:46 PM                       │
│    This agreement outlines the terms of...             │
└─────────────────────────────────────────────────────────┘
```

### Click Any Document

When you click a document, you'll see **full AI analysis**:

- **Summary**: Complete document overview
- **Parties**: All parties identified
- **Important Dates**: Key dates extracted
- **Key Figures**: Dollar amounts, numbers
- **Keywords**: Legal terms found

---

## Example Workflow

### Uploading 10 Documents at Once

1. **Select 10 PDFs** from your case folder
2. **Drag and drop** into upload zone
3. **Watch progress**:
   - 3 files upload simultaneously
   - Each shows individual progress
   - Completed files move to library
   - Queue processes remaining files
4. **Total time**: ~40 seconds (vs ~100 seconds sequential)
5. **View library** to see all 10 analyzed documents

---

## Features Enabled

### ✅ Drag & Drop
- Drop files anywhere in upload zone
- Visual feedback when dragging
- Multiple files at once

### ✅ Progress Tracking
- Real-time progress bars per file
- Percentage complete
- Status indicators
- Time estimates

### ✅ Queue Management
- Automatic queueing
- 3 concurrent uploads max
- Smart processing order
- Clear/retry options

### ✅ Error Handling
- Per-file error messages
- Retry individual failures
- File validation (size/type)
- Clear error states

### ✅ Document Library
- View all uploaded documents
- Click to see full analysis
- Delete documents
- Quick statistics

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Focus upload zone | Tab |
| Activate upload | Enter/Space |
| Toggle library view | Click button |
| Close dialog | Escape |

---

## Configuration

Your current settings:

```typescript
maxConcurrentUploads: 3     // 3 files at once
maxFileSize: 50             // 50MB per file
acceptedFileTypes: [        // Supported formats
  '.pdf',
  '.doc',
  '.docx',
  '.txt'
]
```

To change these, edit `frontend/src/app/documents/page.tsx` lines 94-97.

---

## Troubleshooting

### Files Not Uploading?

1. **Check backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check browser console** for errors (F12)

3. **Verify file formats**: Only PDF, DOC, DOCX, TXT

4. **Check file size**: Must be under 50MB

### Upload Slow?

1. **Large files take longer** (normal for 20MB+ PDFs)
2. **Reduce concurrent uploads** to 1-2 if server is slow
3. **Check network speed**

### Analysis Failed?

1. **Check if text was extracted** (try opening PDF)
2. **Verify AI API keys** are configured in backend
3. **Check backend logs** for errors

---

## Tips for Best Results

### 1. File Naming
Use descriptive names:
- ✅ `2024_Employment_Contract_Smith.pdf`
- ❌ `document1.pdf`

### 2. File Organization
Group related documents before uploading:
- Upload all contracts together
- Upload all discovery documents together
- Makes library browsing easier

### 3. Batch Size
For best performance:
- **1-5 files**: Very fast
- **5-20 files**: Optimal
- **20+ files**: Takes time but works great

### 4. File Quality
For best AI analysis:
- Use text-based PDFs (not scanned images)
- Ensure documents are not password-protected
- Remove any encryption

---

## Quick Reference

### Upload Flow
```
Select Files → Validate → Queue → Upload (3 at a time) → Extract Text → AI Analyze → Complete → Library
```

### File Status
- 📄 **Pending**: Waiting in queue
- 🔄 **Uploading**: Sending to server
- 🔄 **Analyzing**: AI processing
- ✓ **Complete**: Ready to view
- ❌ **Error**: Upload failed

### Actions
- **Upload**: Click zone or drag files
- **View Library**: Click toggle button
- **View Analysis**: Click document
- **Delete**: Click trash icon
- **Retry**: Click retry button (on failed files)

---

## What's Included

Your `/documents` page now has:

✅ **Multi-Document Upload Component**
- Drag-and-drop zone
- Multiple file selection
- Progress tracking
- Queue management

✅ **Document Library**
- All uploaded documents
- Click to view analysis
- Delete functionality
- Search and filter (coming soon)

✅ **AI Analysis Display**
- Summary
- Parties
- Important dates
- Key figures
- Keywords

✅ **Statistics Dashboard**
- Total documents
- Parties identified
- Dates extracted
- Keywords found

---

## Next Steps

### Try It Now!

1. **Start your servers** (backend + frontend)
2. **Navigate to** `http://localhost:3000/documents`
3. **Upload some PDFs** to test it out
4. **View the library** to see AI analysis

### Customize (Optional)

Edit `frontend/src/app/documents/page.tsx` to:
- Change concurrent upload limit
- Adjust file size limits
- Add more file types
- Customize UI colors

### Integrate Elsewhere

Use the same component in other pages:
```typescript
import { MultiDocumentUpload } from '@/components/Documents/MultiDocumentUpload';

<MultiDocumentUpload
  maxConcurrentUploads={3}
  maxFileSize={50}
  onUploadComplete={(files) => console.log('Done!', files)}
/>
```

---

## Success! 🎉

Your multi-document upload feature is **ready to use** right now at:

**http://localhost:3000/documents**

Just start your servers and try uploading multiple files!

---

**For detailed documentation**, see:
- `docs/MULTI_DOCUMENT_UPLOAD_GUIDE.md` - Complete guide
- `docs/MULTI_UPLOAD_SUMMARY.md` - Feature summary

**Need help?** Check the troubleshooting section above or review the backend logs.
