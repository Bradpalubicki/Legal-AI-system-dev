import { LegalInterviewAgentTS, agentInstances } from '@/lib/agent_logic';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { sessionId, documentText } = body;

    if (!sessionId || !documentText) {
      return Response.json(
        { error: 'sessionId and documentText are required' },
        { status: 400 }
      );
    }

    // Create new agent instance
    const agent = new LegalInterviewAgentTS(sessionId);
    agentInstances[sessionId] = agent;

    // Deep document analysis
    const analysis = agent.analyzeDocumentDeeply(documentText);

    // Get first intelligent question
    const firstQuestion = agent.getNextIntelligentQuestion();

    return Response.json({
      success: true,
      analysis_summary: analysis.summary,
      firstQuestion,
      estimatedQuestions: agent.maxQuestions,
      initialInsights: agent.brain.insights,
      confidence: 25  // Starting confidence
    });

  } catch (error) {
    console.error('Agent analyze error:', error);
    return Response.json(
      { error: 'Failed to analyze document' },
      { status: 500 }
    );
  }
}
