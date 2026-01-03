import { agentInstances } from '@/lib/agent_logic';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { sessionId, questionId, answer } = body;

    if (!sessionId || !questionId || !answer) {
      return Response.json(
        { error: 'sessionId, questionId, and answer are required' },
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

    // Process answer intelligently
    const result = agent.processAnswerIntelligently(questionId, answer);

    // Get next question
    const nextQuestion = agent.getNextIntelligentQuestion();

    // Calculate confidence
    const confidence = Math.min(
      25 + (agent.questionCount * 7),
      95
    );

    if (nextQuestion) {
      return Response.json({
        ...result,
        feedback: result.feedback,  // Include feedback
        nextQuestion,
        followUpQuestion: result.follow_up_needed ? agent.followUpNeeded[0] : null,
        confidenceScore: confidence,
        newInsights: result.insights || []
      });
    } else {
      // Interview complete
      return Response.json({
        ...result,
        feedback: result.feedback,  // Include feedback
        complete: true,
        readyForDefense: true,
        confidenceScore: confidence,
        newInsights: result.insights || []
      });
    }

  } catch (error) {
    console.error('Agent answer error:', error);
    return Response.json(
      { error: 'Failed to process answer' },
      { status: 500 }
    );
  }
}
