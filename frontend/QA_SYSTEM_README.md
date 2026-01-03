# Legal Q&A System - User Guide

## ✅ System Status: WORKING

The Q&A system is fully functional and ready to use!

## 🚀 How to Access

### Option 1: Demo Page (Recommended)
Visit: **http://localhost:3000/qa-demo**

This page includes:
- Interactive Q&A interface
- Suggested questions
- Clear instructions
- Educational disclaimers

### Option 2: API Endpoint
Direct API access: `POST http://localhost:3000/api/qa-only`

```javascript
fetch('/api/qa-only', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: 'What is my deadline?'
  })
})
```

## 💬 How It Works

### 1. Ask Questions
Type your question or click a suggested question:
- What is my deadline to respond?
- How much money is being claimed?
- What happens if I ignore this?
- Should I get a lawyer?
- What is an answer?

### 2. Get Instant Answers
Receive clear, factual answers about:
- ✅ Response deadlines
- ✅ Amount claims
- ✅ Case types
- ✅ Next steps
- ✅ Legal terminology
- ✅ Court procedures

### 3. No Defense Building
The Q&A system provides **information only**, NOT defense strategies.

## 🔒 What This System Does

✅ **Answers Questions:**
- Explains legal deadlines
- Clarifies amounts and claims
- Describes court procedures
- Defines legal terms

✅ **Provides Information:**
- Factual responses only
- Educational content
- Procedural guidance

✅ **Redirects Defense Queries:**
- Defense-related questions → Redirected to Defense Builder
- Strategy questions → Redirected appropriately

## ❌ What This System Does NOT Do

❌ Build defense strategies
❌ Suggest specific legal defenses
❌ Provide legal advice
❌ Replace attorney consultation
❌ Output defense content (filtered by sanitizer)

## 🛡️ Security Features

### Content Sanitization
All responses are filtered to remove:
- DEFENSE OPTIONS
- TO BUILD YOUR DEFENSE
- Statute of Limitations (as defense)
- Lack of Evidence
- Procedural Errors
- Defense strategies
- Affirmative defenses

### Safe Redirects
Defense-related questions automatically redirect users to:
> "For defense strategies, please use the Defense Builder feature after completing the document interview."

## 🧪 Testing

### Run Tests
```bash
cd frontend
node test_qa.js
```

### Expected Results
```
✅ Correct: Answer without defense content
✅ Correct: Type is "answer"
```

### Sample Q&A
**Q:** What is my deadline?
**A:** Your response deadline is typically printed on the summons - usually 20-30 days from when you were served. Check the date on your papers.

**Q:** Tell me about defenses
**A:** For defense strategies, please use the Defense Builder feature. I can answer other questions about your case.

## 📁 File Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   └── qa-only/
│   │   │       └── route.ts        # Q&A API endpoint
│   │   └── qa-demo/
│   │       └── page.tsx             # Demo page
│   ├── components/
│   │   └── QASection.tsx           # Q&A UI component
│   └── utils/
│       └── qa_sanitizer.ts         # Content sanitizer
└── test_qa.js                      # Test script
```

## 🔧 Component Usage

### In Your Page
```tsx
import { QASection } from '@/components/QASection';

export default function MyPage() {
  return (
    <QASection
      sessionId="your-session-id"
      documentContext="Optional context"
    />
  );
}
```

## 🎯 Key Features

1. **Hardcoded Responses** - Fast, reliable answers
2. **No AI Required** - Works without API keys
3. **Content Filtering** - Double-layer defense prevention
4. **Clean UI** - Modern, accessible design
5. **Real-time** - Instant responses
6. **Sanitized** - All content checked for defense material

## 📊 API Response Format

```json
{
  "response": "Your deadline is typically 20-30 days...",
  "type": "answer",
  "confidence": 100
}
```

## 🚨 Troubleshooting

### Issue: No response
- ✅ Check dev server is running: `npm run dev`
- ✅ Verify endpoint at: http://localhost:3000/api/qa-only

### Issue: Defense content appears
- ✅ Check sanitizer in `qa_sanitizer.ts`
- ✅ Verify forbidden words list is complete
- ✅ Run test: `node test_qa.js`

### Issue: Component not showing
- ✅ Visit demo page: http://localhost:3000/qa-demo
- ✅ Check component import path
- ✅ Verify TypeScript compilation

## 📝 Educational Disclaimer

**IMPORTANT:** This Q&A system is for educational purposes only and does not constitute legal advice. Users should:
- Consult with a licensed attorney for legal advice
- Use Defense Builder for strategy development
- Understand this provides information, not counsel

## ✅ Status Check

Current Status: **✅ FULLY OPERATIONAL**

- [x] API endpoint working
- [x] UI component functional
- [x] Demo page available
- [x] Content sanitization active
- [x] Tests passing
- [x] No defense content leaking

Visit: **http://localhost:3000/qa-demo** to try it now!
