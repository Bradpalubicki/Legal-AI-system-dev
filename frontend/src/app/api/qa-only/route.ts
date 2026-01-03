import Anthropic from '@anthropic-ai/sdk';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || process.env.CLAUDE_API_KEY || '',
});

// AI-POWERED Q&A - Uses Claude to analyze document and answer questions
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const question = body.message || body.question || '';
    const documentContext = body.documentContext || '';
    const documentAnalysis = body.documentAnalysis || {};
    const sessionId = body.sessionId || '';

    if (!question.trim()) {
      return new Response(JSON.stringify({
        response: 'Please ask a question about your legal document.',
        type: 'answer',
        confidence: 100
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // Use Claude AI to answer the question based on full document context and analysis
    const answer = await getAIAnswer(question, documentContext, documentAnalysis);

    return new Response(JSON.stringify({
      response: answer,
      type: 'answer',
      confidence: 95,
      sessionId
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Q&A error:', error);
    return new Response(JSON.stringify({
      response: 'I encountered an error processing your question. Please try rephrasing it.',
      type: 'answer'
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function getAIAnswer(question: string, documentContext: string, documentAnalysis: any = {}): Promise<string> {
  try {
    // Check for defense-related questions and redirect
    const lowerQuestion = question.toLowerCase();
    if (lowerQuestion.includes('defense') || lowerQuestion.includes('strategy') ||
        lowerQuestion.includes('fight this') || lowerQuestion.includes('beat this')) {
      return 'For defense strategies and legal options, please use the AI Agent Interview tab or Defense Strategies tab. I can answer factual questions about your document, deadlines, amounts, parties involved, and procedural requirements.';
    }

    // Build comprehensive document analysis context
    const analysisContext = `
DOCUMENT ANALYSIS:
- Document Type: ${documentAnalysis.document_type || 'Unknown'}
- Case Number: ${documentAnalysis.case_number || 'Not specified'}
- Court: ${documentAnalysis.court || 'Not specified'}
- Amount Claimed: ${documentAnalysis.amount_claimed || 'Not specified'}
- Parties Involved: ${documentAnalysis.parties?.join(', ') || 'Not specified'}
- Legal Claims/Allegations: ${documentAnalysis.legal_claims?.join('; ') || 'Not specified'}

SUMMARY:
${documentAnalysis.summary || 'No summary available'}

KEY DATES:
${documentAnalysis.key_dates?.map((d: any) => `- ${d.date}: ${d.description}`).join('\n') || 'None listed'}

DEADLINES:
${documentAnalysis.deadlines?.map((d: any) => `- ${d.date}: ${d.description}`).join('\n') || 'None listed'}

KEY TERMS:
${documentAnalysis.key_terms?.join(', ') || 'None listed'}
`;

    const prompt = `You are a legal document Q&A assistant with complete knowledge of the uploaded document. Answer the user's question based on the comprehensive document analysis and full text provided.

${analysisContext}

FULL DOCUMENT TEXT:
${documentContext.slice(0, 6000)}

IMPORTANT RULES:
1. Provide DETAILED, COMPREHENSIVE answers (3-5 sentences minimum)
2. Reference specific information from the document analysis above
3. Explain legal terms and procedures clearly in educational terms
4. Use the structured data (case number, court, parties, claims, amounts) to give precise answers
5. If the document doesn't contain the answer, say so clearly
6. DO NOT provide defense strategies or legal advice - only answer factual and educational questions
7. Be thorough and educational in your explanations

USER QUESTION:
${question}

Provide a detailed, informative answer that helps the user understand their document and situation:`;

    const response = await anthropic.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 800,
      temperature: 0.3,
      messages: [{
        role: 'user',
        content: prompt
      }]
    });

    const answer = response.content[0].type === 'text' ? response.content[0].text : '';

    // Sanitize to ensure no defense building
    if (answer.toLowerCase().includes('you should assert') ||
        answer.toLowerCase().includes('file this defense') ||
        answer.toLowerCase().includes('your best defense is')) {
      return 'I can provide information about your document, but for defense strategies, please use the Defense Builder feature. What factual information would you like to know about your case?';
    }

    return answer.trim();

  } catch (error) {
    console.error('AI answer error:', error);

    // Provide a helpful fallback based on question keywords
    const q = question.toLowerCase();

    if (q.includes('deadline') || q.includes('respond') || q.includes('when')) {
      return 'Based on your document, you typically have 20-30 days from the date of service to file a response. The exact deadline should be clearly stated in your summons or complaint. This is a critical deadline - missing it could result in a default judgment against you. I recommend checking the exact date on your legal papers and marking it on your calendar immediately.';
    }

    if (q.includes('amount') || q.includes('how much') || q.includes('money')) {
      return 'The amount being claimed should be specified in the complaint, typically in a section called "Prayer for Relief" or "Amount Due". This represents what the plaintiff is asking the court to award them. Look for dollar amounts in the main body of the complaint and any attachments. If you can\'t find it, the amount may be listed as "to be determined" or similar language.';
    }

    if (q.includes('what type') || q.includes('kind of case')) {
      return 'To determine the type of case, look at the caption (top of the document) and the claims listed in the complaint. Common types include debt collection, contract disputes, personal injury, or property matters. The complaint should state the specific legal claims being made against you. Understanding the case type helps determine applicable laws and procedures.';
    }

    return 'I can help answer questions about your legal document, including information about deadlines, amounts claimed, parties involved, and procedural requirements. Please try asking your question in a different way, or ask about specific aspects of the document you\'d like to understand better.';
  }
}
