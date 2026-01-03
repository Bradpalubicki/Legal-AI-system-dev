// =============================================================================
// SECURE AI CLIENT
// =============================================================================
// Security enhancements:
// - Prompt injection prevention
// - Input sanitization
// - Output validation
// - Rate limiting
// - Cost tracking
// - AI safety monitoring
// - Disclaimer injection
// - Audit logging
// - Cache poisoning prevention
// =============================================================================

import { Anthropic } from '@anthropic-ai/sdk';
import crypto from 'crypto';

// =============================================================================
// SECURITY CONFIGURATION
// =============================================================================

const AI_SECURITY_CONFIG = {
  MAX_INPUT_LENGTH: 50000,
  MAX_OUTPUT_TOKENS: 2000,
  MAX_CACHE_SIZE: 100,
  CACHE_TTL_MINUTES: 60,
  MAX_REQUESTS_PER_MINUTE: 20,
  ENABLE_SAFETY_MONITORING: true,
  REQUIRE_DISCLAIMERS: true,
} as const;

// Legal disclaimer to inject in ALL AI outputs
const LEGAL_DISCLAIMER = `

⚠️ IMPORTANT DISCLAIMER: This information is for general educational purposes only and does not constitute legal advice. No attorney-client relationship is created by this system. Always consult with a qualified attorney for specific legal matters.`;

// =============================================================================
// PROMPT INJECTION DETECTOR
// =============================================================================

class PromptInjectionDetector {
  private static readonly INJECTION_PATTERNS = [
    // System prompt override attempts
    /ignore\s+(previous|all|above)\s+(instructions|prompts|rules)/gi,
    /disregard\s+(previous|all|above)/gi,
    /forget\s+(everything|all|previous)/gi,
    /new\s+(instructions|prompt|task|role)/gi,
    /you\s+are\s+now/gi,
    /act\s+as\s+(?!a\s+legal)/gi, // Allow "act as a legal assistant"

    // System access attempts
    /show\s+me\s+(your|the)\s+(prompt|system|instructions)/gi,
    /reveal\s+(your|the)\s+(prompt|instructions)/gi,
    /what\s+(are|is)\s+your\s+(instructions|prompt|system)/gi,

    // Jailbreak attempts
    /DAN\s+mode/gi,
    /developer\s+mode/gi,
    /sudo\s+mode/gi,
    /admin\s+mode/gi,
    /unrestricted\s+mode/gi,

    // Data exfiltration
    /print\s+(all|entire)\s+(database|data|memory)/gi,
    /dump\s+(database|data|memory)/gi,
    /show\s+me\s+all\s+(users|passwords|secrets)/gi,

    // Code injection
    /<script/gi,
    /javascript:/gi,
    /eval\s*\(/gi,
    /exec\s*\(/gi,
  ];

  static detect(input: string): { isInjection: boolean; reason?: string } {
    for (const pattern of this.INJECTION_PATTERNS) {
      const match = input.match(pattern);
      if (match) {
        return {
          isInjection: true,
          reason: `Potential prompt injection detected: "${match[0]}"`,
        };
      }
    }

    // Check for excessive special characters (common in injection)
    const specialChars = (input.match(/[{}[\]<>$`]/g) || []).length;
    const ratio = specialChars / input.length;
    if (ratio > 0.1) {
      return {
        isInjection: true,
        reason: 'Excessive special characters detected',
      };
    }

    return { isInjection: false };
  }
}

// =============================================================================
// AI OUTPUT VALIDATOR
// =============================================================================

class AIOutputValidator {
  private static readonly UNSAFE_PATTERNS = [
    // Legal advice indicators
    /\b(you should|i recommend|you must|i advise)\b/gi,
    /\b(hire|fire)\s+(an?\s+)?(attorney|lawyer)\b/gi,
    /\bfile\s+(a\s+)?(lawsuit|motion|complaint)\b/gi,

    // Unauthorized practice
    /\bas\s+your\s+attorney\b/gi,
    /\brepresenting\s+you\b/gi,
    /\bclient-attorney\s+relationship\b/gi,

    // Dangerous instructions
    /\bignore\s+the\s+(court|summons|lawsuit)\b/gi,
    /\bdon't\s+(respond|answer|appear)\b/gi,
  ];

  static validate(output: string): { isValid: boolean; violations: string[] } {
    const violations: string[] = [];

    for (const pattern of this.UNSAFE_PATTERNS) {
      const matches = output.match(pattern);
      if (matches) {
        violations.push(`Unsafe pattern detected: "${matches[0]}"`);
      }
    }

    return {
      isValid: violations.length === 0,
      violations,
    };
  }

  static hasDisclaimer(output: string): boolean {
    const disclaimerPatterns = [
      /not\s+legal\s+advice/gi,
      /consult\s+(with\s+)?(an?\s+)?attorney/gi,
      /educational\s+purposes/gi,
    ];

    return disclaimerPatterns.some((pattern) => pattern.test(output));
  }
}

// =============================================================================
// RATE LIMITER FOR AI CALLS
// =============================================================================

class AIRateLimiter {
  private static requests: Map<string, { count: number; resetTime: number }> = new Map();

  static async checkLimit(userId: string): Promise<{ allowed: boolean; retryAfter?: number }> {
    const now = Date.now();
    const key = `ai_${userId}`;
    const entry = this.requests.get(key);

    if (!entry || now > entry.resetTime) {
      // Reset window
      this.requests.set(key, {
        count: 1,
        resetTime: now + 60000, // 1 minute
      });
      return { allowed: true };
    }

    if (entry.count >= AI_SECURITY_CONFIG.MAX_REQUESTS_PER_MINUTE) {
      const retryAfter = Math.ceil((entry.resetTime - now) / 1000);
      return { allowed: false, retryAfter };
    }

    entry.count++;
    return { allowed: true };
  }
}

// =============================================================================
// COST TRACKER
// =============================================================================

class CostTracker {
  private static costs: Map<string, number> = new Map();

  // Approximate costs per 1K tokens (as of 2024)
  private static readonly PRICING = {
    'claude-3-5-haiku-20241022': { input: 0.00025, output: 0.00125 },
    'claude-sonnet-4-5-20250929': { input: 0.003, output: 0.015 },
  };

  static trackUsage(
    userId: string,
    model: string,
    inputTokens: number,
    outputTokens: number
  ): number {
    const pricing = this.PRICING[model as keyof typeof this.PRICING];
    if (!pricing) return 0;

    const cost =
      (inputTokens / 1000) * pricing.input + (outputTokens / 1000) * pricing.output;

    const currentCost = this.costs.get(userId) || 0;
    this.costs.set(userId, currentCost + cost);

    return cost;
  }

  static getTotalCost(userId: string): number {
    return this.costs.get(userId) || 0;
  }

  static resetCosts(userId: string): void {
    this.costs.delete(userId);
  }
}

// =============================================================================
// SECURE CACHE
// =============================================================================

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  hash: string;
}

class SecureCache<T> {
  private cache: Map<string, CacheEntry<T>> = new Map();
  private readonly maxSize: number;
  private readonly ttlMs: number;

  constructor(maxSize: number = 100, ttlMinutes: number = 60) {
    this.maxSize = maxSize;
    this.ttlMs = ttlMinutes * 60 * 1000;
  }

  set(key: string, data: T): void {
    // Prevent cache poisoning by hashing the data
    const hash = crypto.createHash('sha256').update(JSON.stringify(data)).digest('hex');

    // Clean expired entries if cache is full
    if (this.cache.size >= this.maxSize) {
      this.cleanup();
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      hash,
    });
  }

  get(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    // Check TTL
    if (Date.now() - entry.timestamp > this.ttlMs) {
      this.cache.delete(key);
      return null;
    }

    // Verify data integrity
    const currentHash = crypto.createHash('sha256').update(JSON.stringify(entry.data)).digest('hex');
    if (currentHash !== entry.hash) {
      // Cache poisoning detected!
      console.error('[SECURITY] Cache poisoning detected, removing entry');
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  private cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now - entry.timestamp > this.ttlMs) {
        this.cache.delete(key);
      }
    }

    // If still full, remove oldest entry
    if (this.cache.size >= this.maxSize) {
      const oldestKey = Array.from(this.cache.entries()).sort(
        (a, b) => a[1].timestamp - b[1].timestamp
      )[0][0];
      this.cache.delete(oldestKey);
    }
  }

  clear(): void {
    this.cache.clear();
  }
}

// =============================================================================
// AUDIT LOGGER FOR AI USAGE
// =============================================================================

class AIAuditLogger {
  static async log(params: {
    userId: string;
    action: string;
    model: string;
    inputLength: number;
    outputLength: number;
    cost: number;
    containsViolations: boolean;
    violations?: string[];
    cached: boolean;
  }): Promise<void> {
    try {
      // In production, send to audit database
      console.log('[AI_AUDIT]', {
        timestamp: new Date().toISOString(),
        ...params,
      });

      // Track suspicious patterns
      if (params.containsViolations) {
        console.warn('[AI_SECURITY]', {
          userId: params.userId,
          violations: params.violations,
          action: params.action,
        });
      }
    } catch (error) {
      console.error('[AI_AUDIT] Failed to log:', error);
    }
  }
}

// =============================================================================
// SECURE AI CLIENT
// =============================================================================

export class SecureAIClient {
  private client: Anthropic;
  private cache: SecureCache<any>;

  constructor() {
    // CRITICAL SECURITY CHECK: Prevent client-side instantiation
    if (typeof window !== 'undefined') {
      throw new Error(
        '🚨 SECURITY ERROR: SecureAIClient cannot be instantiated on the client-side. ' +
        'API keys must NEVER be exposed to browsers. ' +
        'This class should ONLY be used in server-side code (API routes, server components, etc.). ' +
        'For client-side AI features, call API routes that use this class server-side.'
      );
    }

    const apiKey = process.env.ANTHROPIC_API_KEY;

    if (!apiKey) {
      throw new Error(
        'ANTHROPIC_API_KEY environment variable is required. ' +
        'Set it in your .env file (never commit .env to git).'
      );
    }

    if (apiKey.startsWith('sk-ant-') === false) {
      throw new Error(
        'Invalid ANTHROPIC_API_KEY format. Expected format: sk-ant-...'
      );
    }

    this.client = new Anthropic({ apiKey });
    this.cache = new SecureCache(
      AI_SECURITY_CONFIG.MAX_CACHE_SIZE,
      AI_SECURITY_CONFIG.CACHE_TTL_MINUTES
    );
  }

  /**
   * Analyze document with security validation
   */
  async analyzeDocument(
    text: string,
    userId: string
  ): Promise<DocumentAnalysis> {
    // Rate limiting
    const rateLimit = await AIRateLimiter.checkLimit(userId);
    if (!rateLimit.allowed) {
      throw new Error(`Rate limit exceeded. Retry after ${rateLimit.retryAfter} seconds`);
    }

    // Input validation
    if (!text || typeof text !== 'string') {
      throw new Error('Invalid document text');
    }

    if (text.length > AI_SECURITY_CONFIG.MAX_INPUT_LENGTH) {
      throw new Error(
        `Document too large (max ${AI_SECURITY_CONFIG.MAX_INPUT_LENGTH} characters)`
      );
    }

    // Prompt injection detection
    const injectionCheck = PromptInjectionDetector.detect(text);
    if (injectionCheck.isInjection) {
      await AIAuditLogger.log({
        userId,
        action: 'ANALYZE_DOCUMENT',
        model: 'BLOCKED',
        inputLength: text.length,
        outputLength: 0,
        cost: 0,
        containsViolations: true,
        violations: [injectionCheck.reason!],
        cached: false,
      });
      throw new Error('Security violation detected in input');
    }

    // Check cache (cache key based on sanitized input hash)
    const cacheKey = `doc_${crypto.createHash('sha256').update(text).digest('hex').substring(0, 32)}`;
    const cached = this.cache.get(cacheKey);
    if (cached) {
      await AIAuditLogger.log({
        userId,
        action: 'ANALYZE_DOCUMENT',
        model: 'CACHED',
        inputLength: text.length,
        outputLength: JSON.stringify(cached).length,
        cost: 0,
        containsViolations: false,
        cached: true,
      });
      return cached;
    }

    // Sanitize input (remove excessive whitespace, normalize)
    const sanitizedText = text
      .replace(/\s+/g, ' ')
      .trim()
      .substring(0, AI_SECURITY_CONFIG.MAX_INPUT_LENGTH);

    // Call AI with safety instructions
    const response = await this.client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: AI_SECURITY_CONFIG.MAX_OUTPUT_TOKENS,
      messages: [
        {
          role: 'user',
          content: `IMPORTANT INSTRUCTIONS:
- You are a legal document analysis assistant
- Provide ONLY factual information extraction
- DO NOT give legal advice
- DO NOT recommend specific actions
- DO NOT make legal conclusions
- Include disclaimer that this is for informational purposes only

Analyze this legal document and extract structured information:

Document: ${sanitizedText}

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
}`,
        },
      ],
    });

    const outputText = response.content[0].text;

    // Validate output
    const validation = AIOutputValidator.validate(outputText);
    if (!validation.isValid && AI_SECURITY_CONFIG.ENABLE_SAFETY_MONITORING) {
      await AIAuditLogger.log({
        userId,
        action: 'ANALYZE_DOCUMENT',
        model: 'claude-3-5-haiku-20241022',
        inputLength: text.length,
        outputLength: outputText.length,
        cost: 0,
        containsViolations: true,
        violations: validation.violations,
        cached: false,
      });
      throw new Error('AI output contains unsafe content');
    }

    // Parse JSON
    let analysis: DocumentAnalysis;
    try {
      analysis = JSON.parse(outputText);
    } catch (error) {
      throw new Error('Failed to parse AI response as JSON');
    }

    // Add disclaimer if required
    if (AI_SECURITY_CONFIG.REQUIRE_DISCLAIMERS) {
      analysis._disclaimer = LEGAL_DISCLAIMER;
    }

    // Track cost
    const cost = CostTracker.trackUsage(
      userId,
      'claude-3-5-haiku-20241022',
      response.usage.input_tokens,
      response.usage.output_tokens
    );

    // Audit log
    await AIAuditLogger.log({
      userId,
      action: 'ANALYZE_DOCUMENT',
      model: 'claude-3-5-haiku-20241022',
      inputLength: text.length,
      outputLength: outputText.length,
      cost,
      containsViolations: false,
      cached: false,
    });

    // Cache result
    this.cache.set(cacheKey, analysis);

    return analysis;
  }

  /**
   * Generate interview question with security
   */
  async generateQuestion(
    analysis: DocumentAnalysis,
    previousAnswers: Record<string, string>,
    userId: string
  ): Promise<InterviewQuestion> {
    // Rate limiting
    const rateLimit = await AIRateLimiter.checkLimit(userId);
    if (!rateLimit.allowed) {
      throw new Error(`Rate limit exceeded. Retry after ${rateLimit.retryAfter} seconds`);
    }

    // Validate previous answers for injection
    for (const answer of Object.values(previousAnswers)) {
      const injectionCheck = PromptInjectionDetector.detect(answer);
      if (injectionCheck.isInjection) {
        throw new Error('Security violation in previous answers');
      }
    }

    const response = await this.client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 500,
      messages: [
        {
          role: 'user',
          content: `Generate the NEXT most important interview question for legal case preparation.

IMPORTANT:
- Ask factual questions only
- Do not provide legal advice
- Focus on gathering information

Analysis: ${JSON.stringify(analysis)}
Previous Answers: ${JSON.stringify(previousAnswers)}

Return JSON:
{
  "question": "the question",
  "why_important": "why this matters",
  "options": ["option1", "option2"] or null,
  "type": "critical/important/clarifying"
}`,
        },
      ],
    });

    const outputText = response.content[0].text;

    // Validate output
    const validation = AIOutputValidator.validate(outputText);
    if (!validation.isValid) {
      throw new Error('AI output contains unsafe content');
    }

    const question: InterviewQuestion = JSON.parse(outputText);

    // Track cost
    CostTracker.trackUsage(
      userId,
      'claude-3-5-haiku-20241022',
      response.usage.input_tokens,
      response.usage.output_tokens
    );

    return question;
  }

  /**
   * Build defense strategy with security
   */
  async buildDefenseStrategy(
    analysis: DocumentAnalysis,
    answers: Record<string, string>,
    userId: string
  ): Promise<DefenseStrategy> {
    // Rate limiting
    const rateLimit = await AIRateLimiter.checkLimit(userId);
    if (!rateLimit.allowed) {
      throw new Error(`Rate limit exceeded. Retry after ${rateLimit.retryAfter} seconds`);
    }

    // Validate inputs
    for (const answer of Object.values(answers)) {
      const injectionCheck = PromptInjectionDetector.detect(answer);
      if (injectionCheck.isInjection) {
        throw new Error('Security violation in answers');
      }
    }

    const response = await this.client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: AI_SECURITY_CONFIG.MAX_OUTPUT_TOKENS,
      messages: [
        {
          role: 'user',
          content: `Build a defense strategy outline based on case information.

IMPORTANT:
- This is for informational purposes only
- Not legal advice
- User should consult with an attorney
- Provide factual analysis of potential defenses

Document Analysis: ${JSON.stringify(analysis)}
Interview Answers: ${JSON.stringify(answers)}

Create strategy outline:
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
  "negotiation_position": "",
  "disclaimer": "This is general information only. Consult with a licensed attorney."
}`,
        },
      ],
    });

    const outputText = response.content[0].text;

    // Validate output
    const validation = AIOutputValidator.validate(outputText);
    if (!validation.isValid) {
      await AIAuditLogger.log({
        userId,
        action: 'BUILD_DEFENSE',
        model: 'claude-3-5-haiku-20241022',
        inputLength: JSON.stringify({ analysis, answers }).length,
        outputLength: outputText.length,
        cost: 0,
        containsViolations: true,
        violations: validation.violations,
        cached: false,
      });
      throw new Error('AI output contains unsafe content');
    }

    const strategy: DefenseStrategy = JSON.parse(outputText);

    // Force disclaimer injection
    if (!strategy.disclaimer) {
      strategy.disclaimer = LEGAL_DISCLAIMER;
    }

    // Track cost
    const cost = CostTracker.trackUsage(
      userId,
      'claude-3-5-haiku-20241022',
      response.usage.input_tokens,
      response.usage.output_tokens
    );

    await AIAuditLogger.log({
      userId,
      action: 'BUILD_DEFENSE',
      model: 'claude-3-5-haiku-20241022',
      inputLength: JSON.stringify({ analysis, answers }).length,
      outputLength: outputText.length,
      cost,
      containsViolations: false,
      cached: false,
    });

    return strategy;
  }

  /**
   * Answer question with security and disclaimers
   */
  async answerQuestion(
    question: string,
    analysis: DocumentAnalysis | undefined,
    strategy: DefenseStrategy | undefined,
    userId: string
  ): Promise<string> {
    // Rate limiting
    const rateLimit = await AIRateLimiter.checkLimit(userId);
    if (!rateLimit.allowed) {
      throw new Error(`Rate limit exceeded. Retry after ${rateLimit.retryAfter} seconds`);
    }

    // Input validation
    if (!question || typeof question !== 'string') {
      throw new Error('Invalid question');
    }

    if (question.length > 5000) {
      throw new Error('Question too long');
    }

    // Prompt injection detection
    const injectionCheck = PromptInjectionDetector.detect(question);
    if (injectionCheck.isInjection) {
      throw new Error('Security violation detected in question');
    }

    // Quick safe answers for common questions
    const quickAnswers: Record<string, string> = {
      deadline: `Check your summons for the response deadline, typically 20-30 days from service.${LEGAL_DISCLAIMER}`,
      lawyer: `Consider consulting an attorney for complex cases. Many offer free consultations.${LEGAL_DISCLAIMER}`,
      ignore: `Never ignore a lawsuit. You must respond by the deadline or face default judgment.${LEGAL_DISCLAIMER}`,
    };

    const q = question.toLowerCase();
    for (const [key, answer] of Object.entries(quickAnswers)) {
      if (q.includes(key)) {
        await AIAuditLogger.log({
          userId,
          action: 'ANSWER_QUESTION',
          model: 'QUICK_ANSWER',
          inputLength: question.length,
          outputLength: answer.length,
          cost: 0,
          containsViolations: false,
          cached: true,
        });
        return answer;
      }
    }

    // Use AI for complex questions
    const response = await this.client.messages.create({
      model: 'claude-3-5-haiku-20241022',
      max_tokens: 300,
      messages: [
        {
          role: 'user',
          content: `Answer this legal question with the following constraints:

IMPORTANT RULES:
- Maximum 100 words
- Provide general information only
- DO NOT give specific legal advice
- DO NOT use phrases like "you should" or "I recommend"
- Include disclaimer at the end
- If question requires legal advice, suggest consulting an attorney

Question: ${question}
Context: ${analysis ? `Case type: ${analysis.case_type}` : 'General legal question'}

Provide informational answer:`,
        },
      ],
    });

    let answer = response.content[0].text;

    // Validate output
    const validation = AIOutputValidator.validate(answer);
    if (!validation.isValid) {
      throw new Error('AI generated unsafe content');
    }

    // Ensure disclaimer is present
    if (!AIOutputValidator.hasDisclaimer(answer)) {
      answer += LEGAL_DISCLAIMER;
    }

    // Track cost
    const cost = CostTracker.trackUsage(
      userId,
      'claude-3-5-haiku-20241022',
      response.usage.input_tokens,
      response.usage.output_tokens
    );

    await AIAuditLogger.log({
      userId,
      action: 'ANSWER_QUESTION',
      model: 'claude-3-5-haiku-20241022',
      inputLength: question.length,
      outputLength: answer.length,
      cost,
      containsViolations: false,
      cached: false,
    });

    return answer;
  }

  /**
   * Get user's AI usage stats
   */
  getUserStats(userId: string) {
    return {
      totalCost: CostTracker.getTotalCost(userId),
      requestsRemaining: AI_SECURITY_CONFIG.MAX_REQUESTS_PER_MINUTE,
    };
  }

  /**
   * Clear user cache (for privacy/GDPR)
   */
  clearUserCache(): void {
    this.cache.clear();
  }
}

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

interface DocumentAnalysis {
  case_type: string;
  plaintiff?: { name: string; type: string; attorney?: string };
  defendant?: { name: string };
  amounts?: { principal: number; interest: number; fees: number; total: number };
  dates?: {
    filed?: string;
    served?: string;
    response_deadline?: string;
    incident_date?: string;
  };
  claims?: string[];
  missing_documents?: string[];
  potential_defenses?: string[];
  deadlines?: Array<{
    date: string;
    description: string;
    type: string;
    priority: string;
  }>;
  red_flags?: string[];
  strengths?: string[];
  questions_needed?: string[];
  _disclaimer?: string;
}

interface InterviewQuestion {
  question: string;
  why_important: string;
  options?: string[] | null;
  type: 'critical' | 'important' | 'clarifying';
}

interface DefenseStrategy {
  primary_defenses: Array<{
    name: string;
    description: string;
    strength: string;
    requirements: string[];
    how_to_assert: string;
  }>;
  secondary_defenses?: any[];
  immediate_actions?: string[];
  evidence_needed?: string[];
  success_probability?: string;
  negotiation_position?: string;
  disclaimer?: string;
}

// =============================================================================
// EXPORTS
// =============================================================================

export {
  PromptInjectionDetector,
  AIOutputValidator,
  AIRateLimiter,
  CostTracker,
  AIAuditLogger,
};
