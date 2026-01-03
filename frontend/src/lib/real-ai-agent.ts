import Anthropic from '@anthropic-ai/sdk';

interface DocumentAnalysis {
  case_type: string;
  plaintiff: string;
  defendant: string;
  amount_claimed: string | null;
  key_dates: {
    filing_date?: string;
    response_deadline?: string;
    incident_date?: string;
  };
  claims: string[];
  missing_documents: string[];
  red_flags: string[];
  critical_missing_info: string[];
  potential_defenses: string[];
}

interface QuestionData {
  question: string;
  why_important: string;
  options?: string[] | null;
  follow_up_if?: Record<string, string> | null;
}

interface AnswerImpact {
  defense_impact: string;
  new_defense_opportunity?: string | null;
  need_follow_up: boolean;
  follow_up_question?: string | null;
}

export class RealLegalAIAgent {
  private ai: Anthropic;
  private documentText: string = '';
  private documentAnalysis: DocumentAnalysis | null = null;
  private questionsAsked: string[] = [];
  private answers: Record<string, string> = {};
  private sessionId: string;

  constructor(sessionId: string) {
    // CRITICAL SECURITY CHECK: Prevent client-side instantiation
    if (typeof window !== 'undefined') {
      throw new Error(
        '🚨 SECURITY ERROR: RealLegalAIAgent cannot be instantiated on the client-side. ' +
        'API keys must never be exposed to browsers. ' +
        'Use API routes in /app/api/ instead.'
      );
    }

    this.sessionId = sessionId;

    // Validate API key exists
    const apiKey = process.env.ANTHROPIC_API_KEY || process.env.CLAUDE_API_KEY;
    if (!apiKey) {
      throw new Error(
        'ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable is required. ' +
        'Set it in your .env file (never commit .env to git).'
      );
    }

    // Validate API key format
    if (!apiKey.startsWith('sk-ant-')) {
      throw new Error(
        'Invalid API key format. Expected format: sk-ant-...'
      );
    }

    // Initialize real AI client
    this.ai = new Anthropic({ apiKey });
  }

  async analyzeDocument(documentText: string): Promise<DocumentAnalysis> {
    this.documentText = documentText;

    console.log('🤖 Calling Claude AI to analyze document...');

    // ACTUAL AI CALL to understand document
    const response = await this.ai.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 1500,
      messages: [{
        role: 'user',
        content: `You are a legal expert. Analyze this legal document completely and provide a detailed analysis.

DOCUMENT:
${documentText}

Provide a detailed JSON analysis with the following structure:
{
  "case_type": "specific type (debt_collection, eviction, landlord_tenant, breach_of_contract, etc)",
  "plaintiff": "name and type of plaintiff",
  "defendant": "name of defendant",
  "amount_claimed": "dollar amount as string or null if not applicable",
  "key_dates": {
    "filing_date": "date if available",
    "response_deadline": "deadline to respond if mentioned",
    "incident_date": "date of incident/claim if mentioned"
  },
  "claims": ["list of specific legal claims being made"],
  "missing_documents": ["documents that should be attached but aren't mentioned"],
  "red_flags": ["issues or problems that could help the defense"],
  "critical_missing_info": ["important information we need to ask the defendant about"],
  "potential_defenses": ["potential defenses based on the document alone"]
}

Return ONLY valid JSON, no other text.`
      }]
    });

    const content = response.content[0];
    const jsonText = content.type === 'text' ? content.text : '';

    try {
      this.documentAnalysis = JSON.parse(jsonText);
      console.log('✅ Document analysis complete:', this.documentAnalysis);
      return this.documentAnalysis!;
    } catch (error) {
      console.error('Failed to parse AI response:', jsonText);
      throw new Error('AI returned invalid JSON');
    }
  }

  async generateNextQuestion(): Promise<QuestionData> {
    if (!this.documentAnalysis) {
      throw new Error('Must analyze document first');
    }

    console.log(`🤖 Calling Claude AI to generate question ${this.questionsAsked.length + 1}...`);

    // ACTUAL AI CALL to generate intelligent question
    const response = await this.ai.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 800,
      messages: [{
        role: 'user',
        content: `Based on this legal case analysis, generate the NEXT most important question to ask the defendant.

DOCUMENT ANALYSIS:
${JSON.stringify(this.documentAnalysis, null, 2)}

QUESTIONS ALREADY ASKED:
${JSON.stringify(this.questionsAsked)}

ANSWERS COLLECTED SO FAR:
${JSON.stringify(this.answers, null, 2)}

Generate ONE strategic question that will help build the strongest defense. Consider:
- What critical information is missing?
- What would establish statute of limitations?
- What would challenge plaintiff's standing or ownership?
- What would dispute the amount or validity?
- What evidence does the defendant have?

If this is a debt collection case, prioritize questions about:
1. Last payment date (for statute of limitations)
2. Recognition of debt (for standing/validity)
3. Amount accuracy
4. Documentation received

Return ONLY valid JSON with this exact structure:
{
  "question": "the specific question to ask",
  "why_important": "brief explanation of why this matters for the defense",
  "options": ["option 1", "option 2", "option 3"] or null for open-ended,
  "follow_up_if": {"specific answer": "follow up question"} or null
}

Return ONLY the JSON, no other text.`
      }]
    });

    const content = response.content[0];
    const jsonText = content.type === 'text' ? content.text : '';

    try {
      const questionData: QuestionData = JSON.parse(jsonText);
      this.questionsAsked.push(questionData.question);
      console.log('✅ Question generated:', questionData.question);
      return questionData;
    } catch (error) {
      console.error('Failed to parse AI response:', jsonText);
      throw new Error('AI returned invalid JSON for question');
    }
  }

  async processAnswer(question: string, answer: string): Promise<AnswerImpact> {
    this.answers[question] = answer;

    console.log('🤖 Calling Claude AI to analyze answer impact...');

    // AI processes the answer constructively
    const response = await this.ai.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 500,
      messages: [{
        role: 'user',
        content: `Process the defendant's answer and determine next steps.

CASE ANALYSIS:
${JSON.stringify(this.documentAnalysis, null, 2)}

QUESTION ASKED:
${question}

DEFENDANT'S ANSWER:
${answer}

ALL ANSWERS SO FAR:
${JSON.stringify(this.answers, null, 2)}

Acknowledge the answer constructively and determine if follow-up is needed. Return ONLY valid JSON:
{
  "defense_impact": "brief, neutral acknowledgment of the information received (1-2 sentences, supportive and factual tone)",
  "new_defense_opportunity": "if this answer creates a specific defense opportunity, explain it briefly" or null,
  "need_follow_up": true or false,
  "follow_up_question": "specific follow-up question if clarification or more detail would be helpful" or null
}

IMPORTANT GUIDELINES:
- Keep feedback brief, neutral, and supportive
- Do NOT criticize brief, simple, or yes/no answers
- Do NOT use words like "vague", "weak", "problematic", "concerning", or "inadequate"
- Simply acknowledge what was learned and determine if more information would be useful
- Focus on gathering facts, not judging the quality of responses
- For yes/no answers, acknowledge the response and only ask follow-up if truly needed for the case

Return ONLY the JSON, no other text.`
      }]
    });

    const content = response.content[0];
    const jsonText = content.type === 'text' ? content.text : '';

    try {
      const impact: AnswerImpact = JSON.parse(jsonText);
      console.log('✅ Answer impact analyzed');
      return impact;
    } catch (error) {
      console.error('Failed to parse AI response:', jsonText);
      throw new Error('AI returned invalid JSON for impact analysis');
    }
  }

  async buildDefenseStrategy(): Promise<any> {
    if (!this.documentAnalysis) {
      throw new Error('Must analyze document first');
    }

    console.log('🤖 Calling Claude AI to build comprehensive defense strategy...');

    // ACTUAL AI CALL to build comprehensive defense
    const response = await this.ai.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 4000,
      messages: [{
        role: 'user',
        content: `Build a comprehensive legal defense strategy based on the document analysis and interview answers.

ORIGINAL DOCUMENT TEXT:
${this.documentText.slice(0, 2000)}

DOCUMENT ANALYSIS:
${JSON.stringify(this.documentAnalysis, null, 2)}

INTERVIEW ANSWERS (CRITICAL FOR DEFENSE JUSTIFICATION):
${JSON.stringify(this.answers, null, 2)}

Create a HIGHLY DETAILED defense strategy. For EACH defense, you MUST:

1. **WHY THIS DEFENSE IS RECOMMENDED**: Explicitly reference specific facts from:
   - The document (e.g., "The complaint states X, but lacks Y")
   - Red flags identified (e.g., "Missing proof of assignment creates standing issue")
   - Interview answers (e.g., "Defendant stated last payment was 7 years ago, beyond statute")
   - Missing documents (e.g., "No original contract attached, required to prove terms")

2. **DOCUMENT-BASED JUSTIFICATION**: For each defense, cite:
   - What the plaintiff claims in the document
   - What evidence they failed to provide
   - How the defendant's answers contradict or challenge the claims
   - Specific dates, amounts, or facts that support this defense

3. **CONCRETE LEGAL REASONING**: Explain the legal principle and how the facts support it

Return valid JSON with this structure:
{
  "primary_defenses": [
    {
      "name": "Defense Name",
      "strength": 85,
      "strength_level": "STRONG" or "MODERATE" or "WEAK",
      "description": "brief 1-sentence description",
      "why_recommended": "DETAILED explanation citing specific document facts, red flags, missing documents, and interview answers that justify this defense (3-5 sentences minimum)",
      "document_evidence": {
        "plaintiff_claims": "what plaintiff claimed in the document",
        "missing_from_complaint": ["specific items missing from the complaint"],
        "defendant_answers_support": "how defendant's answers support this defense",
        "specific_facts": ["specific dates, amounts, or facts from document/interview"]
      },
      "detailed_explanation": "comprehensive legal explanation with reasoning (2-3 sentences)",
      "how_to_assert": "exact steps and language to use in Answer (2-3 specific steps)",
      "evidence_needed": ["specific evidence required"],
      "winning_scenarios": ["specific scenarios where this wins"],
      "risks_to_avoid": ["what not to do"]
    }
  ],
  "immediate_actions": [
    {
      "action": "specific action to take",
      "deadline": "when to do it",
      "priority": "CRITICAL" or "HIGH" or "MEDIUM",
      "details": "how to do it",
      "why_important": "explanation based on document facts"
    }
  ],
  "evidence_needed": ["overall evidence needed with explanations"],
  "estimated_success_rate": "percentage based on defenses",
  "strategy_basis": "summary of how document analysis and answers shaped this strategy"
}

IMPORTANT: The "why_recommended" field MUST explicitly reference:
- Specific claims from the complaint document
- Red flags identified (e.g., "${this.documentAnalysis.red_flags.join(', ')}")
- Missing documents (e.g., "${this.documentAnalysis.missing_documents.join(', ')}")
- Interview answers that create opportunities
- Critical missing info that weakens plaintiff's case

Be EXTREMELY specific and detailed. Connect every defense recommendation to concrete facts. Return ONLY the JSON, no other text.`
      }]
    });

    const content = response.content[0];
    const jsonText = content.type === 'text' ? content.text : '';

    try {
      const strategy = JSON.parse(jsonText);
      console.log('✅ Defense strategy built with AI');
      return strategy;
    } catch (error) {
      console.error('Failed to parse AI response:', jsonText);
      throw new Error('AI returned invalid JSON for strategy');
    }
  }

  getSessionData() {
    return {
      sessionId: this.sessionId,
      documentAnalysis: this.documentAnalysis,
      questionsAsked: this.questionsAsked,
      answers: this.answers
    };
  }
}
