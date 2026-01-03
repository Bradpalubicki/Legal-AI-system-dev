# Load Test Data Files

This directory contains sample files used for load testing file upload and processing functionality.

## Files

### sample-document.txt
A sample legal document in plain text format containing realistic legal document structure and content. This file is used for testing:
- Document upload functionality
- Text extraction and parsing
- Search indexing
- Document retrieval

**Size**: ~3.5 KB
**Format**: Plain text (UTF-8)
**Usage**: Used by k6 test scenarios for document upload testing

### sample-document.pdf
A sample legal document in PDF format.

**Status**: To be created

**How to Create**:

Option 1 - Convert the TXT file:
```bash
# Using LibreOffice (if installed)
libreoffice --headless --convert-to pdf sample-document.txt

# Using online converter
# Visit: https://www.ilovepdf.com/txt_to_pdf
# Upload sample-document.txt and download the PDF
```

Option 2 - Use a Python script:
```python
# Install: pip install reportlab
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_sample_pdf():
    c = canvas.Canvas("sample-document.pdf", pagesize=letter)

    # Read the text file
    with open("sample-document.txt", "r", encoding="utf-8") as f:
        content = f.read()

    # Add text to PDF (simplified - doesn't handle line breaks)
    y = 750
    for line in content.split('\n'):
        if y < 50:  # New page if needed
            c.showPage()
            y = 750
        c.drawString(50, y, line[:80])  # Limit line length
        y -= 15

    c.save()
    print("PDF created successfully!")

if __name__ == "__main__":
    create_sample_pdf()
```

Option 3 - Manual creation:
1. Open sample-document.txt in Microsoft Word or Google Docs
2. File → Save As → PDF
3. Save as `sample-document.pdf`

## Notes

- **Test Data Only**: These files contain fictional data for testing purposes only
- **No Sensitive Data**: Files do not contain any real personal or confidential information
- **Clearly Marked**: All content is marked as "LOAD TEST" or "TEST DATA"
- **Size**: Files are kept small (~3-10 KB) for efficient testing
- **Reusability**: Files can be used repeatedly in load tests without issues

## File Upload Testing

The sample files are referenced in `tests/load/config.js`:

```javascript
testData: {
  sampleDocument: open('./test-files/sample-document.txt', 'b'),
  samplePdf: open('./test-files/sample-document.pdf', 'b'),
}
```

**Note**: Currently, the test scenarios don't use file uploads via the `testData` configuration. They use JSON payloads for document metadata creation. File upload testing can be added in future test scenarios if needed.

## Adding More Test Files

To add additional test files:

1. Create the file in this directory
2. Mark it clearly as test data
3. Update `config.js` to include it:
   ```javascript
   testData: {
     // Existing files
     sampleDocument: open('./test-files/sample-document.txt', 'b'),

     // New file
     yourNewFile: open('./test-files/your-new-file.ext', 'b'),
   }
   ```
4. Use it in test scenarios via `config.testData.yourNewFile`

## Cleanup

These test files should be:
- ✅ Committed to version control (they're test data, not secrets)
- ✅ Small in size (< 1 MB each)
- ✅ Clearly labeled as test data
- ❌ Not used in production environments
