"""
AI Help Agent API - Provides contextual assistance to users within the app.

This endpoint powers an in-app AI assistant that helps users navigate the system,
understand features, and get answers to questions about using the Legal AI platform.
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import os
from openai import OpenAI

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None


class HelpMessage(BaseModel):
    """Single message in help chat"""
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")


class HelpRequest(BaseModel):
    """Request for help from the AI agent"""
    question: str = Field(..., min_length=1, description="User's question or help request")
    current_page: Optional[str] = Field(None, description="Current page/route user is on")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context about user's current state")
    chat_history: List[HelpMessage] = Field(default_factory=list, description="Previous chat messages")


# Application context that the AI can reference
APP_CONTEXT = """
You are a helpful AI assistant embedded in the Legal AI Defense System application. Your role is to help users understand and navigate the application.

## Application Overview
The Legal AI Defense System is a comprehensive platform for legal professionals that combines AI-powered document analysis, federal court research, and case management.

## Main Features:

### 1. Documents Tab
- Upload legal documents (PDF, DOCX, TXT)
- AI automatically extracts: parties, dates, key figures, keywords
- Documents are analyzed and saved for use in other features
- Supports bankruptcy forms (Schedule A/B, I, J) and general legal documents

### 2. Q&A Assistant Tab
- Ask questions about uploaded documents or general legal topics
- AI provides intelligent answers based on document context
- Works with or without uploaded documents
- Chat history is preserved during the session

### 3. Defense Builder Tab
- AI-guided conversational defense strategy builder
- Requires an uploaded document to work
- AI asks relevant questions based on the document
- Generates comprehensive defense analysis and recommendations

### 4. Case Tracking Tab
- Track all legal cases in one place
- Monitor case progress, deadlines, and documents
- Create and manage cases
- Link documents to specific cases

### 5. PACER Search Tab (Detailed UI Guide)
**Overview**: Search federal court records via CourtListener (FREE)

**Search Fields & Best Practices**:
- **Case Title** field:
  - Use this to search for BUSINESS NAMES (e.g., "ABC Corporation", "XYZ LLC")
  - Use this to search for PERSON NAMES (e.g., "John Smith", "Jane Doe")
  - This is the PRIMARY search field for finding cases by parties involved
  - Example: Enter "Tesla Motors" in Case Title to find all cases involving Tesla
  - Example: Enter "John Smith" in Case Title to find cases with that person

- **Case Number** field:
  - Use when you have the specific docket number (e.g., "20-12345")
  - Format: Usually YY-NNNNN (year-number)

- **Court** dropdown:
  - Select specific bankruptcy court (e.g., "nvb" for Nevada Bankruptcy)
  - Select district or circuit court
  - Leave blank to search all courts

- **Court Type** tabs:
  - Bankruptcy: Chapter 7, 11, 13 cases
  - District: Civil and criminal cases
  - Circuit: Appeals cases

- **Date Filters**:
  - Filed After: Cases filed after this date
  - Filed Before: Cases filed before this date
  - Use YYYY-MM-DD format

**Search Strategy Tips**:
1. **Finding a company's cases**: Enter company name in "Case Title" field
2. **Finding a person's cases**: Enter person's full or partial name in "Case Title" field
3. **Finding a specific case**: Use exact case number in "Case Number" field
4. **Narrowing results**: Combine Case Title + Court + Date range

**After Search Results**:
- Click "View Details" to see case information
- Review available documents (some are FREE in RECAP)
- Purchase documents with credits (check if free first!)
- Monitor case for future updates/filings

**Document Purchase**:
- System automatically checks if document is FREE before charging
- If free in RECAP Archive, downloads at no cost
- Otherwise, costs credits based on page count (~$0.10/page)
- View credit balance in header or visit Credits page

**IMPORTANT TROUBLESHOOTING - If Documents Don't Show Up**:
If documents aren't appearing in the app after a search, here's the workaround:
1. Go to the case you're monitoring in the app
2. Click "View on CourtListener" button (opens CourtListener website)
3. On CourtListener's website, you can:
   - See ALL available documents for the case
   - Manually download FREE documents from RECAP
   - Purchase documents directly through PACER if needed
4. After downloading documents from CourtListener:
   - Return to the Legal AI app
   - Go to Documents tab
   - Upload the downloaded documents into the app
   - Now you can use them in Q&A, Defense Builder, etc.

This manual workflow is a reliable fallback when automated document retrieval has issues.

### 6. Credits System
- Purchase credits for PACER document downloads
- 1 credit = $1.00 USD
- Track spending and transaction history
- Access via sidebar "Credits" link or from PACER page
- Documents may be FREE if available in RECAP Archive

## Navigation
- **Sidebar**: Main navigation on the left
- **Tab-based interface**: Documents, Q&A, Defense, Cases, PACER on main page
- **Credits page**: Separate page accessible from sidebar
- Use `?tab=pacer` URL parameters to link to specific tabs

## Common Workflows:

**Document Analysis Workflow:**
1. Go to Documents tab
2. Upload a legal document
3. AI analyzes and extracts key information
4. Use Q&A tab to ask questions about it
5. Use Defense Builder for strategy

**PACER Research Workflow:**
1. Go to PACER Search tab
2. Choose your search approach:
   - **By Business/Person**: Enter name in "Case Title" field
   - **By Case Number**: Enter docket number in "Case Number" field
3. Optional: Select specific court and date range to narrow results
4. Click "Search" - it's FREE via CourtListener
5. Review results and click "View Details" on relevant cases
6. Check if documents are FREE (system auto-checks RECAP)
7. Purchase documents with credits if not free
8. Optional: Monitor cases for new filings/updates

**IMPORTANT**: When searching for a business or person, always use the "Case Title" field, NOT the case number field!

**Troubleshooting Document Access**:
If documents aren't showing up in search results or purchase attempts fail:
1. Find the case in your monitored cases or search results
2. Click "View on CourtListener" to open the case on CourtListener's website
3. On CourtListener, you can manually:
   - Download FREE RECAP documents
   - Purchase documents through PACER directly
4. Download the documents to your computer
5. Return to the app and upload them in the Documents tab
6. Use the uploaded documents in Q&A, Defense Builder, or other features

This manual method is the most reliable way to get documents when automated features have issues.

**Case Management Workflow:**
1. Go to Case Tracking tab
2. Create a new case
3. Upload or link documents to the case
4. Track deadlines and progress
5. Add notes and updates

## Important Notes:
- All content is for EDUCATIONAL PURPOSES ONLY
- Does NOT constitute legal advice
- Always consult a qualified attorney for legal counsel
- Document uploads are processed by AI for analysis
- PACER searches are FREE, document downloads cost credits
- Some CourtListener features require paid API access

## Technical Details:
- Backend: FastAPI (Python) at localhost:8000
- Frontend: Next.js at localhost:3000
- AI Models: OpenAI GPT-4 and Anthropic Claude
- Document storage: Local file system
- Credits: SQLite database tracking

When answering questions:
1. Be concise and helpful
2. Reference specific tabs/features by name
3. Provide step-by-step instructions when appropriate
4. If user is on a specific page, provide contextual help for that page
5. Suggest relevant features they might not know about
6. Always maintain the educational disclaimer
"""


@router.post("/ask")
async def ask_help_agent(request: HelpRequest):
    """
    Get help from the AI assistant.

    Provides contextual assistance based on user's question, current page,
    and chat history.
    """
    try:
        if not client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI help agent is not configured. Please set OPENAI_API_KEY."
            )

        # Build context string
        context_parts = [APP_CONTEXT]

        if request.current_page:
            context_parts.append(f"\nUser is currently on: {request.current_page}")

        if request.context:
            context_parts.append(f"\nAdditional context: {request.context}")

        system_prompt = "\n".join(context_parts)

        # Build message history for OpenAI
        messages = [{"role": "system", "content": system_prompt}]

        for msg in request.chat_history[-10:]:  # Keep last 10 messages for context
            messages.append({
                "role": msg.role if msg.role != "assistant" else "assistant",
                "content": msg.content
            })

        # Add current question
        messages.append({
            "role": "user",
            "content": request.question
        })

        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=1024,
            temperature=0.7
        )

        assistant_message = response.choices[0].message.content

        logger.info(f"Help agent answered question: {request.question[:50]}...")

        return {
            "success": True,
            "answer": assistant_message,
            "current_page": request.current_page
        }

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Help agent error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get help: {str(e)}"
        )


@router.get("/quick-tips")
async def get_quick_tips(page: Optional[str] = None):
    """
    Get quick tips for the current page.

    Returns helpful tips based on which page the user is viewing.
    """
    tips_by_page = {
        "documents": [
            "💡 Upload documents to enable Q&A and Defense Builder features",
            "📄 Supported formats: PDF, DOCX, TXT, RTF",
            "🔍 AI automatically extracts key information from your documents",
            "💾 Documents are saved and can be used across all features"
        ],
        "qa": [
            "💬 Ask questions about uploaded documents or general legal topics",
            "🎯 Be specific for better AI responses",
            "📚 Chat history is preserved during your session",
            "🆓 Works with or without uploaded documents"
        ],
        "defense": [
            "🛡️ Upload a document first to use Defense Builder",
            "🤖 AI will guide you through relevant questions",
            "📊 Receive comprehensive defense analysis",
            "💡 Answer questions thoughtfully for best results"
        ],
        "cases": [
            "📁 Track all your legal cases in one place",
            "📅 Monitor deadlines and important dates",
            "🔗 Link documents to specific cases",
            "📝 Add notes and updates as cases progress"
        ],
        "pacer": [
            "🔍 Search federal courts for FREE via CourtListener",
            "💰 Purchase documents using credits",
            "🎉 Some documents are FREE in RECAP Archive",
            "👀 Monitor cases for new filings and updates",
            "💳 Check your credit balance in the header or Credits page"
        ],
        "credits": [
            "💳 1 credit = $1.00 USD",
            "📊 View transaction and purchase history",
            "➕ Add credits via payment integration",
            "💰 Credits are used for PACER document purchases",
            "🎁 FREE documents don't cost any credits"
        ]
    }

    tips = tips_by_page.get(page, [
        "🏠 Use the sidebar to navigate between features",
        "📄 Start by uploading documents in the Documents tab",
        "🔍 Search federal courts for free in PACER Search",
        "💬 Get instant answers in the Q&A Assistant",
        "❓ Click the help icon anytime for assistance"
    ])

    return {
        "success": True,
        "page": page or "home",
        "tips": tips
    }
# force reload
