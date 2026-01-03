import { agentInstances } from '@/lib/agent_logic';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { sessionId } = body;

    if (!sessionId) {
      return Response.json(
        { error: 'sessionId is required' },
        { status: 400 }
      );
    }

    // Get agent instance
    const agent = agentInstances[sessionId];
    if (!agent) {
      return Response.json(
        { error: 'No active agent session found' },
        { status: 404 }
      );
    }

    // Build comprehensive defense strategy
    const strategy = agent.buildComprehensiveDefenseStrategy();

    return Response.json(strategy);

  } catch (error) {
    console.error('Agent build-defense error:', error);
    return Response.json(
      { error: 'Failed to build defense strategy' },
      { status: 500 }
    );
  }
}
