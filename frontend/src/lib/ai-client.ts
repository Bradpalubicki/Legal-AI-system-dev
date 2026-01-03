// src/lib/ai-client.ts
// ONE AI client for ALL components - no duplicate AI calls

import { Anthropic } from '@anthropic-ai/sdk';

// Types specific to AI analysis (different from document.ts types)
export interface DocumentAnalysis {
  case_type: string;
  plaintiff: {
    name: string;
    type: 'original_creditor' | 'debt_buyer' | 'landlord' | string;
    attorney: string;
  };
  defendant: {
    name: string;
  };
  amounts: {
    principal: number;
    interest: number;
    fees: number;
    total: number;
  };
  dates: {
    filed: string;
    served: string;
    response_deadline: string;
    incident_date: string;
  };
  claims: string[];
  missing_documents: string[];
  potential_defenses: string[];
  deadlines: Array<{
    date: string;
    description: string;
    type: string;
    priority: string;
  }>;
  red_flags: string[];
  strengths: string[];
  questions_needed: string[];
}

export interface InterviewQuestion {
  question: string;
  why_important: string;
  options: string[] | null;
  type: 'critical' | 'important' | 'clarifying';
}

export interface DefenseStrategy {
  primary_defenses: Array<{
    name: string;
    description: string;
    strength: 'Strong' | 'Medium' | 'Weak';
    requirements: string[];
    how_to_assert: string;
  }>;
  secondary_defenses: Array<{
    name: string;
    description: string;
    strength: 'Strong' | 'Medium' | 'Weak';
    requirements: string[];
    how_to_assert: string;
  }>;
  immediate_actions: string[];
  evidence_needed: string[];
  success_probability: string;
  negotiation_position: string;
}

export class AIClient {
  private client: Anthropic;
  private cache: Map<string, any> = new Map();

  constructor() {
    // CRITICAL SECURITY CHECK: Prevent client-side instantiation
    if (typeof window !== 'undefined') {
      throw new Error(
        '🚨 SECURITY ERROR: AIClient cannot be instantiated on the client-side. ' +
        'API keys must never be exposed to browsers. ' +
        'Use API routes in /app/api/ instead.'
      );
    }

    // Validate API key exists
    if (!process.env.ANTHROPIC_API_KEY) {
      throw new Error(
        'ANTHROPIC_API_KEY environment variable is required. ' +
        'Set it in your .env file (never commit .env to git).'
      );
    }

    // Validate API key format
    if (!process.env.ANTHROPIC_API_KEY.startsWith('sk-ant-')) {
      throw new Error(
        'Invalid ANTHROPIC_API_KEY format. ' +
        'Expected format: sk-ant-...'
      );
    }

    this.client = new Anthropic({
      apiKey: process.env.ANTHROPIC_API_KEY!
    });
  }

  // Analyze document ONCE for all components
  async analyzeDocument(text: string): Promise<DocumentAnalysis> {
    // Check cache first
    const cacheKey = `doc_${text.substring(0, 100)}`;
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }

    const response = await this.client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 1500,
      messages: [{
        role: 'user',
        content: `Analyze this legal document completely. Extract ALL information needed for case tracking, defense building, and Q&A.

Document: ${text}

Return comprehensive JSON with:
{
  "case_type": "specific type",
  "plaintiff": {
    "name": "",
    "type": "original_creditor/debt_buyer/landlord",
    "attorney": ""
  },
  "defendant": {"name": ""},
  "amounts": {
    "principal": 0,
    "interest": 0,
    "fees": 0,
    "total": 0
  },
  "dates": {
    "filed": "",
    "served": "",
    "response_deadline": "",
    "incident_date": ""
  },
  "claims": [],
  "missing_documents": [],
  "potential_defenses": [],
  "deadlines": [
    {"date": "", "description": "", "type": "", "priority": ""}
  ],
  "red_flags": [],
  "strengths": [],
  "questions_needed": []
}`
      }]
    });

    const firstContent = response.content[0];
    if (firstContent.type !== 'text') {
      throw new Error('Expected text response from AI');
    }
    const analysis = JSON.parse(firstContent.text);
    this.cache.set(cacheKey, analysis);
    return analysis;
  }

  // Generate interview questions based on analysis
  async generateQuestion(
    analysis: DocumentAnalysis,
    previousAnswers: Record<string, string>
  ): Promise<InterviewQuestion> {
    const response = await this.client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 500,
      messages: [{
        role: 'user',
        content: `Based on this case analysis, generate the NEXT most important question.

Analysis: ${JSON.stringify(analysis)}
Previous Answers: ${JSON.stringify(previousAnswers)}

Consider:
- What's missing for statute of limitations defense?
- What would challenge standing?
- What would dispute the amount?

Return JSON:
{
  "question": "the question",
  "why_important": "why this matters",
  "options": ["option1", "option2"] or null,
  "type": "critical/important/clarifying"
}`
      }]
    });

    const firstContent = response.content[0];
    if (firstContent.type !== 'text') {
      throw new Error('Expected text response from AI');
    }
    return JSON.parse(firstContent.text);
  }

  // Build defense strategy using ALL information
  async buildDefenseStrategy(
    analysis: DocumentAnalysis,
    answers: Record<string, string>
  ): Promise<DefenseStrategy> {
    const response = await this.client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 2000,
      messages: [{
        role: 'user',
        content: `Build comprehensive defense strategy.

Document Analysis: ${JSON.stringify(analysis)}
Interview Answers: ${JSON.stringify(answers)}

Create detailed strategy with:
{
  "primary_defenses": [
    {
      "name": "",
      "description": "",
      "strength": "Strong/Medium/Weak",
      "requirements": [],
      "how_to_assert": ""
    }
  ],
  "secondary_defenses": [],
  "immediate_actions": [],
  "evidence_needed": [],
  "success_probability": "",
  "negotiation_position": ""
}`
      }]
    });

    const firstContent = response.content[0];
    if (firstContent.type !== 'text') {
      throw new Error('Expected text response from AI');
    }
    return JSON.parse(firstContent.text);
  }

  // Answer questions using context
  async answerQuestion(
    question: string,
    analysis?: DocumentAnalysis,
    strategy?: DefenseStrategy
  ): Promise<string> {
    // Quick answers for common questions
    const quickAnswers: Record<string, string> = {
      'deadline': 'Check your summons for the response deadline, typically 20-30 days from service.',
      'lawyer': 'Consider consulting an attorney for complex cases. Many offer free consultations.',
      'ignore': 'Never ignore a lawsuit. You must respond by the deadline or face default judgment.'
    };

    const q = question.toLowerCase();
    for (const [key, answer] of Object.entries(quickAnswers)) {
      if (q.includes(key)) {
        return answer;
      }
    }

    // Use AI for complex questions
    const response = await this.client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 150,
      messages: [{
        role: 'user',
        content: `Answer this legal question concisely (max 50 words).

Question: ${question}
Context: ${analysis ? `Case type: ${analysis.case_type}` : 'General legal question'}

Provide practical answer:`
      }]
    });

    const firstContent = response.content[0];
    if (firstContent.type !== 'text') {
      throw new Error('Expected text response from AI');
    }
    return firstContent.text;
  }
}
