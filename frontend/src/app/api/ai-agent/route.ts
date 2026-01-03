import { NextRequest, NextResponse } from 'next/server';
import { RealLegalAIAgent } from '@/lib/real-ai-agent';

// Store agent sessions in memory
const agentSessions = new Map<string, RealLegalAIAgent>();

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, sessionId, data } = body;

    if (!sessionId) {
      return NextResponse.json(
        { error: 'sessionId is required' },
        { status: 400 }
      );
    }

    // Get or create agent
    let agent = agentSessions.get(sessionId);
    if (!agent) {
      agent = new RealLegalAIAgent(sessionId);
      agentSessions.set(sessionId, agent);
      console.log(`✅ Created new AI agent session: ${sessionId}`);
    }

    switch (action) {
      case 'analyze_document': {
        console.log('📄 Action: Analyze Document');
        const analysis = await agent.analyzeDocument(data.documentText);
        const firstQuestion = await agent.generateNextQuestion();

        return NextResponse.json({
          success: true,
          analysis,
          firstQuestion: {
            id: 'q1',
            question: firstQuestion.question,
            why_important: firstQuestion.why_important,
            options: firstQuestion.options,
            questionNumber: 1
          },
          status: 'interviewing'
        });
      }

      case 'submit_answer': {
        console.log(`💬 Action: Submit Answer - Q: "${data.question}"`);
        const impact = await agent.processAnswer(data.question, data.answer);

        const sessionData = agent.getSessionData();
        const questionsAsked = sessionData.questionsAsked.length;

        // Determine if we should ask more questions (max 6-7 strategic questions)
        const shouldContinue = questionsAsked < 6 && !impact.need_follow_up;

        if (shouldContinue || impact.need_follow_up) {
          let nextQuestion;

          if (impact.follow_up_question) {
            // Use AI's suggested follow-up
            nextQuestion = {
              id: `q${questionsAsked + 1}`,
              question: impact.follow_up_question,
              why_important: 'Follow-up to previous answer',
              options: null,
              questionNumber: questionsAsked + 1
            };
          } else {
            // Generate next strategic question
            const aiQuestion = await agent.generateNextQuestion();
            nextQuestion = {
              id: `q${questionsAsked + 1}`,
              question: aiQuestion.question,
              why_important: aiQuestion.why_important,
              options: aiQuestion.options,
              questionNumber: questionsAsked + 1
            };
          }

          return NextResponse.json({
            success: true,
            feedback: impact.defense_impact,
            defenseOpportunity: impact.new_defense_opportunity,
            nextQuestion,
            questionNumber: questionsAsked
          });
        } else {
          // Interview complete
          return NextResponse.json({
            success: true,
            feedback: impact.defense_impact,
            defenseOpportunity: impact.new_defense_opportunity,
            complete: true,
            readyForDefense: true,
            totalQuestions: questionsAsked
          });
        }
      }

      case 'build_defense': {
        console.log('🛡️ Action: Build Defense Strategy');
        const strategy = await agent.buildDefenseStrategy();

        return NextResponse.json({
          success: true,
          ...strategy
        });
      }

      case 'get_session': {
        const sessionData = agent.getSessionData();
        return NextResponse.json({
          success: true,
          ...sessionData
        });
      }

      default:
        return NextResponse.json(
          { error: `Unknown action: ${action}` },
          { status: 400 }
        );
    }
  } catch (error: any) {
    console.error('❌ AI Agent Error:', error);
    return NextResponse.json(
      {
        error: 'AI processing failed',
        details: error.message,
        stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
      },
      { status: 500 }
    );
  }
}
