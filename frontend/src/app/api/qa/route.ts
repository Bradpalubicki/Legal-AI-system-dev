/**
 * Q&A API Route - ONLY for answering questions
 * Does NOT build defenses - only provides information
 */

export async function POST(request: Request) {
  try {
    const { message, sessionId } = await request.json();

    if (!message) {
      return Response.json(
        { error: 'Message is required' },
        { status: 400 }
      );
    }

    // Simple Q&A responses only - NO defense building
    const qaResponses: Record<string, string> = {
      'type': 'Check the summons for case type. Common types: debt collection, eviction, foreclosure.',
      'deadline': 'Usually 20-30 days from service. Check your summons for exact date.',
      'amount': 'Listed in the complaint document under "damages" or "amount claimed".',
      'next': 'File an answer by the deadline. Deny false claims. Assert defenses.',
      'lawyer': 'Legal aid offers free help if you qualify. Bar association has referrals.',
      'court': 'Arrive 15 minutes early. Dress professionally. Bring all documents.',
      'documents': 'Bring summons, complaint, any correspondence, payment records, and evidence.',
      'respond': 'File a written answer. Admit or deny each claim. Assert defenses.',
      'sued': 'Respond by deadline. Request evidence. Don\'t ignore court papers.',
      'debt': 'Check if over 4 years old. Request validation. Dispute incorrect amounts.',
      'eviction': 'You have 5 days to respond. Document repairs needed. Pay or move.',
      'default': 'Check your court documents for this information. Act before deadline.'
    };

    let answer = 'Check your court documents for this information. Act before deadline.';

    // Find matching response
    const messageLower = message.toLowerCase();
    for (const [key, response] of Object.entries(qaResponses)) {
      if (messageLower.includes(key)) {
        answer = response;
        break;
      }
    }

    // For defense questions, redirect to Defense Builder
    if (messageLower.includes('defense') || messageLower.includes('defenses')) {
      answer = 'Complete the interview first. Then use Defense Builder to see your specific defenses.';
    }

    return Response.json({
      response: answer,
      word_count: answer.split(' ').length,
      model: 'hardcoded_qa',
      has_question: answer.includes('?')
    });

  } catch (error) {
    console.error('Q&A error:', error);
    return Response.json(
      { error: 'Failed to process question' },
      { status: 500 }
    );
  }
}
