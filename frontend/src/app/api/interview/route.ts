import { API_CONFIG } from '../../../config/api';

/**
 * Interview API Route - ONLY for interview questions
 * Manages question flow and answer collection
 */

export async function POST(request: Request) {
  try {
    const { sessionId, stage, answer, action } = await request.json();

    if (!sessionId) {
      return Response.json(
        { error: 'Session ID is required' },
        { status: 400 }
      );
    }

    const backendUrl = process.env.NEXT_PUBLIC_API_URL || API_CONFIG.BASE_URL;

    // Handle different interview actions
    if (action === 'start') {
      // Start interview with document
      const { documentText } = await request.json();

      const response = await fetch(`${backendUrl}/api/defense-flow/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sessionId, documentText }),
      });

      if (!response.ok) {
        throw new Error('Failed to start interview');
      }

      return Response.json(await response.json());

    } else if (action === 'answer') {
      // Submit answer to interview question
      const response = await fetch(`${backendUrl}/api/defense-flow/answer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sessionId, answer }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit answer');
      }

      return Response.json(await response.json());

    } else if (action === 'status') {
      // Get interview status
      const response = await fetch(`${backendUrl}/api/defense-flow/status/${sessionId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get status');
      }

      return Response.json(await response.json());

    } else {
      return Response.json(
        { error: 'Invalid action. Use: start, answer, or status' },
        { status: 400 }
      );
    }

  } catch (error) {
    console.error('Interview error:', error);
    return Response.json(
      { error: 'Failed to process interview request' },
      { status: 500 }
    );
  }
}
