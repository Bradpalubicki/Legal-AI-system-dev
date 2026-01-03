// src/app/api/unified/route.ts
// Single API that all components use - Proxies to backend unified endpoint

import { NextRequest, NextResponse } from 'next/server';

import { API_CONFIG } from '../../../config/api';
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || API_CONFIG.BASE_URL;

// Simple auth helper - extract user ID from headers/cookies
async function getUser(request: NextRequest) {
  // TODO: Implement proper authentication
  // For now, extract from header or cookie
  const userId = request.headers.get('x-user-id') || request.cookies.get('userId')?.value;

  if (!userId) {
    return null;
  }

  return { id: userId };
}

export async function POST(request: NextRequest) {
  try {
    const user = await getUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { action, sessionId, sessionToken, data } = body;

    // Proxy request to backend unified API
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/unified/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-user-id': user.id,
      },
      body: JSON.stringify({
        sessionId: sessionId || crypto.randomUUID(),
        action,
        data: {
          ...data,
          userId: user.id,
        },
      }),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({}));
      return NextResponse.json(
        { error: errorData.detail || errorData.error || 'Backend request failed' },
        { status: backendResponse.status }
      );
    }

    const result = await backendResponse.json();

    // Add session token for frontend tracking
    return NextResponse.json({
      ...result,
      sessionToken: sessionToken || crypto.randomUUID(),
    });

  } catch (error) {
    console.error('API Error:', error);

    // Handle errors
    if (error instanceof Error) {
      if (error.message.includes('fetch')) {
        return NextResponse.json(
          { error: 'Unable to connect to backend service' },
          { status: 503 }
        );
      }
    }

    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
