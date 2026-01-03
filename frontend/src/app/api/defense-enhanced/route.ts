import { NextRequest, NextResponse } from 'next/server';
import { RealLegalAIAgent } from '@/lib/real-ai-agent';

const sessions = new Map<string, RealLegalAIAgent>();

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { documentText, documentType, documentAnalysis, sessionId } = body;

    // Create or get agent instance
    let agent = sessions.get(sessionId);
    if (!agent) {
      agent = new RealLegalAIAgent(sessionId);
      sessions.set(sessionId, agent);
    }

    // Use real AI to analyze and build strategy
    await agent.analyzeDocument(documentText);

    // Build defense strategy with AI
    const strategy = await agent.buildDefenseStrategy();

    // Format response for the main page
    const formattedResponse = {
      analysis_summary: {
        total_defenses: strategy.primary_defenses.length + (strategy.secondary_defenses?.length || 0),
        strong_defenses: strategy.primary_defenses.filter((d: any) => d.strength >= 70).length,
        document_type: documentType || documentAnalysis?.document_type || 'Legal Document'
      },
      defenses: strategy.primary_defenses.map((defense: any) => ({
        name: defense.name,
        description: defense.description,
        strength: defense.strength / 100, // Convert to 0-1 scale
        strength_level: defense.strength_level,
        detailed_explanation: defense.detailed_explanation,
        requirements: defense.requirements,
        how_to_assert: defense.how_to_assert,
        winning_scenarios: defense.winning_scenarios,
        risks_to_avoid: defense.risks_to_avoid,
        case_law_support: defense.case_law_support,
        evidence_needed: defense.requirements || [],
        time_sensitivity: 'File answer within 20-30 days of service',
        risks: defense.risks_to_avoid || []
      })),
      action_items: strategy.immediate_actions.map((action: any) => ({
        action: action.action,
        priority: action.priority,
        deadline: action.deadline,
        description: action.details,
        how_to: action.how_to
      })),
      evidence_needed: strategy.evidence_needed,
      estimated_success_rate: strategy.estimated_success_rate
    };

    return NextResponse.json(formattedResponse);
  } catch (error) {
    console.error('Enhanced defense analysis error:', error);
    return NextResponse.json(
      { error: 'Failed to analyze defenses' },
      { status: 500 }
    );
  }
}
