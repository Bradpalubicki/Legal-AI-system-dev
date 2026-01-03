import { API_CONFIG } from '../../../../config/api';

/**
 * Defense Building API Route - ONLY for building defense strategies
 * Requires document and interview answers
 */

export async function POST(request: Request) {
  try {
    const { sessionId, document, answers } = await request.json();

    if (!sessionId) {
      return Response.json(
        { error: 'Session ID is required' },
        { status: 400 }
      );
    }

    // Forward to backend API
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || API_CONFIG.BASE_URL;
    const response = await fetch(`${backendUrl}/api/defense-flow/build`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ sessionId }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      return Response.json(
        { error: errorData.detail || 'Defense building failed' },
        { status: response.status }
      );
    }

    const data = await response.json();

    // Fallback defenses if backend returns empty
    if (!data.defenses || data.defenses.length === 0) {
      data.defenses = [
        {
          name: 'Statute of Limitations',
          description: 'If debt is over 4 years old, it may be time-barred.',
          strength: 'STRONG',
          action: 'Check last payment date. Assert in answer if applicable.',
          requirements: ['Last payment date', 'State statute period']
        },
        {
          name: 'Lack of Standing',
          description: 'Plaintiff must prove they own the debt.',
          strength: 'MEDIUM',
          action: 'Request proof of ownership and chain of title.',
          requirements: ['Original contract', 'Assignment documents']
        },
        {
          name: 'Procedural Errors',
          description: 'Improper service or filing errors.',
          strength: 'MEDIUM',
          action: 'Review summons for service defects.',
          requirements: ['Service documents', 'Filing dates']
        }
      ];
    }

    return Response.json(data);

  } catch (error) {
    console.error('Defense building error:', error);
    return Response.json(
      { error: 'Failed to build defenses' },
      { status: 500 }
    );
  }
}
