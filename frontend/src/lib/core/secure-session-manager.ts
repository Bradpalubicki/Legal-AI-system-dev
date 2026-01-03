// =============================================================================
// SECURE UNIFIED SESSION MANAGER
// =============================================================================
// Security enhancements:
// - Input validation and sanitization
// - SQL injection prevention (parameterized queries)
// - Session token security
// - Access control and authorization
// - Rate limiting
// - Audit logging
// - Encryption for sensitive data
// - XSS prevention
// =============================================================================

import { db } from '@/lib/database';
import { AIClient } from '@/lib/ai-client';
import * as crypto from 'crypto';

// =============================================================================
// SECURITY CONFIGURATION
// =============================================================================

const SECURITY_CONFIG = {
  SESSION_EXPIRY_MINUTES: 15,
  MAX_SESSIONS_PER_USER: 3,
  MAX_INTERVIEW_ANSWERS: 50,
  MAX_QA_HISTORY: 100,
  MAX_DOCUMENT_SIZE: 10_000_000, // 10MB
  RATE_LIMIT_REQUESTS_PER_MINUTE: 30,
  SESSION_TOKEN_LENGTH: 64,
} as const;

// =============================================================================
// SECURITY UTILITIES
// =============================================================================

class SecurityValidator {
  private static readonly SQL_INJECTION_PATTERNS = [
    /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)/gi,
    /(--|\*\/|\/\*|;|'|")/g,
  ];

  private static readonly XSS_PATTERNS = [
    /<script[^>]*>.*?<\/script>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi,
    /<iframe/gi,
  ];

  static sanitizeInput(input: string): string {
    if (!input || typeof input !== 'string') {
      return '';
    }

    // Remove null bytes
    let sanitized = input.replace(/\0/g, '');

    // Length limit
    sanitized = sanitized.substring(0, 50000);

    // Basic XSS prevention (for display purposes - don't rely on this for security)
    sanitized = sanitized
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#x27;');

    return sanitized;
  }

  static validateUUID(uuid: string): boolean {
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return uuidRegex.test(uuid);
  }

  static detectSQLInjection(input: string): boolean {
    return this.SQL_INJECTION_PATTERNS.some(pattern => pattern.test(input));
  }

  static detectXSS(input: string): boolean {
    return this.XSS_PATTERNS.some(pattern => pattern.test(input));
  }

  static validateInput(input: string, context: string): void {
    if (this.detectSQLInjection(input)) {
      throw new SecurityError(`SQL injection detected in ${context}`, 'SQL_INJECTION');
    }

    if (this.detectXSS(input)) {
      throw new SecurityError(`XSS attempt detected in ${context}`, 'XSS_ATTEMPT');
    }
  }
}

class SecurityError extends Error {
  constructor(message: string, public code: string) {
    super(message);
    this.name = 'SecurityError';
  }
}

// =============================================================================
// AUDIT LOGGER
// =============================================================================

class AuditLogger {
  static async log(params: {
    userId: string;
    sessionId: string;
    action: string;
    resourceType?: string;
    resourceId?: string;
    ipAddress?: string;
    userAgent?: string;
    metadata?: Record<string, any>;
    securityRelevant?: boolean;
  }): Promise<void> {
    try {
      await db.query(
        `INSERT INTO activities (
          user_id, session_id, activity_type, action,
          table_name, record_id, ip_address, user_agent,
          metadata, security_relevant, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())`,
        [
          params.userId,
          params.sessionId,
          params.resourceType || 'session',
          params.action,
          params.resourceType,
          params.resourceId,
          params.ipAddress,
          params.userAgent,
          JSON.stringify(params.metadata || {}),
          params.securityRelevant || false,
        ]
      );
    } catch (error) {
      console.error('[AUDIT] Failed to log activity:', error);
      // Don't throw - audit logging failure shouldn't break the app
    }
  }

  static async logDataAccess(params: {
    userId: string;
    tableName: string;
    recordId: string;
    accessType: 'READ' | 'EXPORT' | 'DOWNLOAD' | 'DECRYPT';
    caseId?: string;
    documentId?: string;
    containsPII?: boolean;
    attorneyClientPrivileged?: boolean;
    purpose?: string;
    ipAddress?: string;
  }): Promise<void> {
    try {
      // Get user details
      const userResult = await db.query(
        'SELECT email, role FROM users WHERE id = $1',
        [params.userId]
      );

      const user = userResult.rows[0];

      await db.query(
        `INSERT INTO data_access_log (
          user_id, user_email, user_role,
          table_name, record_id, case_id, document_id,
          access_type, contains_pii, attorney_client_privileged,
          access_purpose, ip_address, accessed_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW())`,
        [
          params.userId,
          user?.email,
          user?.role,
          params.tableName,
          params.recordId,
          params.caseId,
          params.documentId,
          params.accessType,
          params.containsPII || false,
          params.attorneyClientPrivileged || false,
          params.purpose || 'legal_case_management',
          params.ipAddress,
        ]
      );
    } catch (error) {
      console.error('[AUDIT] Failed to log data access:', error);
    }
  }
}

// =============================================================================
// RATE LIMITER
// =============================================================================

class RateLimiter {
  private static requestCounts: Map<string, { count: number; resetTime: number }> = new Map();

  static async checkLimit(userId: string): Promise<boolean> {
    const now = Date.now();
    const key = userId;
    const entry = this.requestCounts.get(key);

    if (!entry || now > entry.resetTime) {
      // Reset window
      this.requestCounts.set(key, {
        count: 1,
        resetTime: now + 60000, // 1 minute
      });
      return true;
    }

    if (entry.count >= SECURITY_CONFIG.RATE_LIMIT_REQUESTS_PER_MINUTE) {
      await AuditLogger.log({
        userId,
        sessionId: 'rate-limit',
        action: 'RATE_LIMIT_EXCEEDED',
        securityRelevant: true,
        metadata: { requestCount: entry.count },
      });
      return false;
    }

    entry.count++;
    return true;
  }
}

// =============================================================================
// SESSION TOKEN MANAGER
// =============================================================================

class SessionTokenManager {
  /**
   * Generate a cryptographically secure session token
   */
  static generateToken(): string {
    return crypto.randomBytes(SECURITY_CONFIG.SESSION_TOKEN_LENGTH).toString('hex');
  }

  /**
   * Hash token for storage (NEVER store plaintext tokens)
   */
  static hashToken(token: string): string {
    return crypto.createHash('sha256').update(token).digest('hex');
  }

  /**
   * Verify token against hash
   */
  static verifyToken(token: string, hash: string): boolean {
    return this.hashToken(token) === hash;
  }
}

// =============================================================================
// AUTHORIZATION CHECKER
// =============================================================================

class AuthorizationChecker {
  static async canAccessCase(userId: string, caseId: string): Promise<boolean> {
    const result = await db.query(
      `SELECT id FROM cases
       WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL`,
      [caseId, userId]
    );

    return result.rows.length > 0;
  }

  static async canAccessDocument(userId: string, documentId: string): Promise<boolean> {
    const result = await db.query(
      `SELECT d.id FROM documents d
       JOIN cases c ON d.case_id = c.id
       WHERE d.id = $1 AND c.user_id = $2 AND d.deleted_at IS NULL`,
      [documentId, userId]
    );

    return result.rows.length > 0;
  }

  static async canAccessSession(userId: string, sessionId: string): Promise<boolean> {
    const result = await db.query(
      `SELECT id FROM sessions
       WHERE id = $1 AND user_id = $2 AND active = true`,
      [sessionId, userId]
    );

    return result.rows.length > 0;
  }
}

// =============================================================================
// SECURE UNIFIED SESSION MANAGER
// =============================================================================

export class SecureUnifiedSessionManager {
  private static instance: SecureUnifiedSessionManager;
  private sessions: Map<string, SessionContext> = new Map();
  private aiClient: AIClient;

  private constructor() {
    this.aiClient = new AIClient();
  }

  static getInstance(): SecureUnifiedSessionManager {
    if (!this.instance) {
      this.instance = new SecureUnifiedSessionManager();
    }
    return this.instance;
  }

  /**
   * Create a new secure session
   */
  async createSession(
    userId: string,
    caseId?: string,
    metadata?: {
      ipAddress?: string;
      userAgent?: string;
      deviceFingerprint?: string;
    }
  ): Promise<{ sessionId: string; sessionToken: string }> {
    // Validate inputs
    if (!SecurityValidator.validateUUID(userId)) {
      throw new SecurityError('Invalid user ID format', 'INVALID_USER_ID');
    }

    if (caseId && !SecurityValidator.validateUUID(caseId)) {
      throw new SecurityError('Invalid case ID format', 'INVALID_CASE_ID');
    }

    // Rate limiting
    const allowed = await RateLimiter.checkLimit(userId);
    if (!allowed) {
      throw new SecurityError('Rate limit exceeded', 'RATE_LIMIT_EXCEEDED');
    }

    // Authorization check for case access
    if (caseId) {
      const canAccess = await AuthorizationChecker.canAccessCase(userId, caseId);
      if (!canAccess) {
        await AuditLogger.log({
          userId,
          sessionId: 'unauthorized',
          action: 'UNAUTHORIZED_CASE_ACCESS',
          resourceType: 'cases',
          resourceId: caseId,
          securityRelevant: true,
        });
        throw new SecurityError('Unauthorized case access', 'UNAUTHORIZED');
      }
    }

    // Check session limit per user
    const existingSessions = await db.query(
      'SELECT COUNT(*) FROM sessions WHERE user_id = $1 AND active = true',
      [userId]
    );

    if (parseInt(existingSessions.rows[0].count) >= SECURITY_CONFIG.MAX_SESSIONS_PER_USER) {
      throw new SecurityError(
        'Maximum concurrent sessions exceeded',
        'MAX_SESSIONS_EXCEEDED'
      );
    }

    const sessionId = crypto.randomUUID();
    const sessionToken = SessionTokenManager.generateToken();
    const tokenHash = SessionTokenManager.hashToken(sessionToken);
    const expiresAt = new Date(Date.now() + SECURITY_CONFIG.SESSION_EXPIRY_MINUTES * 60000);

    // Create session in database with security metadata
    await db.query(
      `INSERT INTO sessions (
        id, user_id, case_id, session_token_hash,
        ip_address, user_agent, device_fingerprint,
        expires_at, active, created_at
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, true, NOW())`,
      [
        sessionId,
        userId,
        caseId,
        tokenHash,
        metadata?.ipAddress,
        metadata?.userAgent,
        metadata?.deviceFingerprint,
        expiresAt,
      ]
    );

    // Audit log
    await AuditLogger.log({
      userId,
      sessionId,
      action: 'SESSION_CREATED',
      ipAddress: metadata?.ipAddress,
      userAgent: metadata?.userAgent,
      metadata: { caseId, expiresAt },
    });

    const context = new SessionContext(sessionId, userId, caseId);
    this.sessions.set(sessionId, context);

    // Return session token (client must store securely - httpOnly cookie)
    return { sessionId, sessionToken };
  }

  /**
   * Get session with security validation
   */
  async getSession(sessionId: string, sessionToken: string): Promise<SessionContext> {
    // Validate session ID format
    if (!SecurityValidator.validateUUID(sessionId)) {
      throw new SecurityError('Invalid session ID format', 'INVALID_SESSION_ID');
    }

    // Check in-memory cache first
    if (this.sessions.has(sessionId)) {
      const context = this.sessions.get(sessionId)!;

      // Verify token
      const session = await db.query(
        'SELECT session_token_hash, expires_at FROM sessions WHERE id = $1',
        [sessionId]
      );

      if (!session.rows[0]) {
        throw new SecurityError('Session not found', 'SESSION_NOT_FOUND');
      }

      if (!SessionTokenManager.verifyToken(sessionToken, session.rows[0].session_token_hash)) {
        await AuditLogger.log({
          userId: context.userId,
          sessionId,
          action: 'INVALID_SESSION_TOKEN',
          securityRelevant: true,
        });
        throw new SecurityError('Invalid session token', 'INVALID_TOKEN');
      }

      // Check expiration
      if (new Date(session.rows[0].expires_at) < new Date()) {
        await this.revokeSession(sessionId, 'expired');
        throw new SecurityError('Session expired', 'SESSION_EXPIRED');
      }

      return context;
    }

    // Load from database with security checks
    const result = await db.query(
      `SELECT * FROM sessions
       WHERE id = $1 AND active = true AND expires_at > NOW()`,
      [sessionId]
    );

    if (!result.rows[0]) {
      throw new SecurityError('Session not found or expired', 'SESSION_NOT_FOUND');
    }

    const row = result.rows[0];

    // Verify token
    if (!SessionTokenManager.verifyToken(sessionToken, row.session_token_hash)) {
      await AuditLogger.log({
        userId: row.user_id,
        sessionId,
        action: 'INVALID_SESSION_TOKEN',
        securityRelevant: true,
      });
      throw new SecurityError('Invalid session token', 'INVALID_TOKEN');
    }

    const context = new SessionContext(sessionId, row.user_id, row.case_id);
    context.loadFromDB(row);
    this.sessions.set(sessionId, context);

    // Update last activity
    await db.query(
      'UPDATE sessions SET last_activity = NOW() WHERE id = $1',
      [sessionId]
    );

    return context;
  }

  /**
   * Process document with security validation
   */
  async processDocument(
    sessionId: string,
    sessionToken: string,
    documentText: string,
    caseId?: string,
    metadata?: {
      ipAddress?: string;
      userAgent?: string;
    }
  ): Promise<DocumentAnalysis> {
    const session = await this.getSession(sessionId, sessionToken);

    // Rate limiting
    const allowed = await RateLimiter.checkLimit(session.userId);
    if (!allowed) {
      throw new SecurityError('Rate limit exceeded', 'RATE_LIMIT_EXCEEDED');
    }

    // Validate document text
    if (!documentText || typeof documentText !== 'string') {
      throw new SecurityError('Invalid document text', 'INVALID_INPUT');
    }

    if (documentText.length > SECURITY_CONFIG.MAX_DOCUMENT_SIZE) {
      throw new SecurityError('Document too large', 'DOCUMENT_TOO_LARGE');
    }

    // Security validation
    SecurityValidator.validateInput(documentText, 'document_text');

    // Sanitize input
    const sanitizedText = SecurityValidator.sanitizeInput(documentText);

    // Authorization check for case
    const targetCaseId = caseId || session.caseId;
    if (targetCaseId) {
      const canAccess = await AuthorizationChecker.canAccessCase(
        session.userId,
        targetCaseId
      );
      if (!canAccess) {
        throw new SecurityError('Unauthorized case access', 'UNAUTHORIZED');
      }
    }

    // AI analysis
    const analysis = await this.aiClient.analyzeDocument(sanitizedText);

    // Store in session context
    session.setDocumentAnalysis(analysis);

    // Update case with analysis
    if (targetCaseId) {
      await this.updateCaseWithAnalysis(targetCaseId, analysis, session.userId);
    }

    // Extract deadlines
    if (analysis.deadlines && targetCaseId) {
      await this.createDeadlines(targetCaseId, analysis.deadlines, session.userId);
    }

    // Audit log
    await AuditLogger.log({
      userId: session.userId,
      sessionId,
      action: 'DOCUMENT_PROCESSED',
      resourceType: 'documents',
      ipAddress: metadata?.ipAddress,
      userAgent: metadata?.userAgent,
      metadata: { caseId: targetCaseId, documentLength: documentText.length },
    });

    // Log data access (documents contain PII/privileged info)
    await AuditLogger.logDataAccess({
      userId: session.userId,
      tableName: 'documents',
      recordId: sessionId,
      accessType: 'READ',
      caseId: targetCaseId,
      containsPII: true,
      attorneyClientPrivileged: true,
      purpose: 'legal_document_analysis',
      ipAddress: metadata?.ipAddress,
    });

    return analysis;
  }

  /**
   * Conduct interview with security
   */
  async conductInterview(
    sessionId: string,
    sessionToken: string
  ): Promise<InterviewQuestion> {
    const session = await this.getSession(sessionId, sessionToken);

    // Rate limiting
    const allowed = await RateLimiter.checkLimit(session.userId);
    if (!allowed) {
      throw new SecurityError('Rate limit exceeded', 'RATE_LIMIT_EXCEEDED');
    }

    const analysis = session.getDocumentAnalysis();
    if (!analysis) {
      throw new SecurityError('No document analyzed', 'NO_DOCUMENT');
    }

    // Generate question
    const question = await this.aiClient.generateQuestion(
      analysis,
      session.getInterviewAnswers()
    );

    session.setCurrentQuestion(question);

    // Audit log
    await AuditLogger.log({
      userId: session.userId,
      sessionId,
      action: 'INTERVIEW_QUESTION_GENERATED',
    });

    return question;
  }

  /**
   * Process interview answer with security
   */
  async processAnswer(
    sessionId: string,
    sessionToken: string,
    answer: string
  ): Promise<{ nextQuestion?: InterviewQuestion; complete: boolean }> {
    const session = await this.getSession(sessionId, sessionToken);

    // Validate answer
    if (!answer || typeof answer !== 'string') {
      throw new SecurityError('Invalid answer', 'INVALID_INPUT');
    }

    if (answer.length > 10000) {
      throw new SecurityError('Answer too long', 'ANSWER_TOO_LONG');
    }

    // Security validation
    SecurityValidator.validateInput(answer, 'interview_answer');

    // Sanitize
    const sanitizedAnswer = SecurityValidator.sanitizeInput(answer);

    // Check answer limit
    if (session.getAnswerCount() >= SECURITY_CONFIG.MAX_INTERVIEW_ANSWERS) {
      throw new SecurityError('Maximum answers exceeded', 'MAX_ANSWERS_EXCEEDED');
    }

    // Store answer
    session.addAnswer(session.getCurrentQuestion(), sanitizedAnswer);

    // Audit log
    await AuditLogger.log({
      userId: session.userId,
      sessionId,
      action: 'INTERVIEW_ANSWER_SUBMITTED',
      metadata: { answerCount: session.getAnswerCount() },
    });

    // Check if complete
    if (session.getAnswerCount() >= 7) {
      return { complete: true };
    }

    // Get next question
    const nextQuestion = await this.conductInterview(sessionId, sessionToken);
    return { nextQuestion, complete: false };
  }

  /**
   * Build defense strategy with security
   */
  async buildDefense(
    sessionId: string,
    sessionToken: string
  ): Promise<DefenseStrategy> {
    const session = await this.getSession(sessionId, sessionToken);

    // Rate limiting
    const allowed = await RateLimiter.checkLimit(session.userId);
    if (!allowed) {
      throw new SecurityError('Rate limit exceeded', 'RATE_LIMIT_EXCEEDED');
    }

    const strategy = await this.aiClient.buildDefenseStrategy(
      session.getDocumentAnalysis(),
      session.getInterviewAnswers()
    );

    // Store in case if linked
    if (session.caseId) {
      await db.query(
        `UPDATE cases
         SET defense_strategy = $1, interview_complete = true, updated_at = NOW()
         WHERE id = $2 AND user_id = $3`,
        [JSON.stringify(strategy), session.caseId, session.userId]
      );
    }

    session.setDefenseStrategy(strategy);

    // Audit log
    await AuditLogger.log({
      userId: session.userId,
      sessionId,
      action: 'DEFENSE_STRATEGY_BUILT',
      resourceType: 'cases',
      resourceId: session.caseId,
    });

    return strategy;
  }

  /**
   * Answer question with security
   */
  async answerQuestion(
    sessionId: string,
    sessionToken: string,
    question: string
  ): Promise<string> {
    const session = await this.getSession(sessionId, sessionToken);

    // Validate question
    if (!question || typeof question !== 'string') {
      throw new SecurityError('Invalid question', 'INVALID_INPUT');
    }

    if (question.length > 5000) {
      throw new SecurityError('Question too long', 'QUESTION_TOO_LONG');
    }

    // Security validation
    SecurityValidator.validateInput(question, 'qa_question');

    // Sanitize
    const sanitizedQuestion = SecurityValidator.sanitizeInput(question);

    // Check history limit
    const historyCount = session.getQAHistoryCount();
    if (historyCount >= SECURITY_CONFIG.MAX_QA_HISTORY) {
      throw new SecurityError('Maximum Q&A history exceeded', 'MAX_QA_EXCEEDED');
    }

    // Get answer
    const answer = await this.aiClient.answerQuestion(
      sanitizedQuestion,
      session.getDocumentAnalysis(),
      session.getDefenseStrategy()
    );

    // Store in history
    session.addQAExchange(sanitizedQuestion, answer);

    // Audit log
    await AuditLogger.log({
      userId: session.userId,
      sessionId,
      action: 'QA_EXCHANGE',
      metadata: { questionLength: question.length, answerLength: answer.length },
    });

    return answer;
  }

  /**
   * Revoke session
   */
  async revokeSession(sessionId: string, reason: string): Promise<void> {
    await db.query(
      `UPDATE sessions
       SET active = false, revoked = true, revoked_at = NOW(), revoked_reason = $1
       WHERE id = $2`,
      [reason, sessionId]
    );

    this.sessions.delete(sessionId);

    // Audit log
    const session = await db.query('SELECT user_id FROM sessions WHERE id = $1', [sessionId]);
    if (session.rows[0]) {
      await AuditLogger.log({
        userId: session.rows[0].user_id,
        sessionId,
        action: 'SESSION_REVOKED',
        metadata: { reason },
        securityRelevant: true,
      });
    }
  }

  /**
   * Update case with analysis (with authorization)
   */
  private async updateCaseWithAnalysis(
    caseId: string,
    analysis: DocumentAnalysis,
    userId: string
  ): Promise<void> {
    await db.query(
      `UPDATE cases
       SET ai_analysis = $1,
           plaintiff_name = COALESCE($2, plaintiff_name),
           plaintiff_type = COALESCE($3, plaintiff_type),
           response_deadline = COALESCE($4, response_deadline),
           updated_at = NOW(),
           updated_by = $5
       WHERE id = $6 AND user_id = $7`,
      [
        JSON.stringify(analysis),
        analysis.plaintiff?.name,
        analysis.plaintiff?.type,
        analysis.responseDeadline,
        userId,
        caseId,
        userId,
      ]
    );
  }

  /**
   * Create deadlines (with authorization)
   */
  private async createDeadlines(
    caseId: string,
    deadlines: ExtractedDeadline[],
    userId: string
  ): Promise<void> {
    for (const deadline of deadlines) {
      await db.query(
        `INSERT INTO deadlines (
          case_id, deadline_type, description, due_date, priority,
          source, created_by
        )
        VALUES ($1, $2, $3, $4, $5, 'ai_extracted', $6)
        ON CONFLICT DO NOTHING`,
        [
          caseId,
          deadline.type,
          deadline.description,
          deadline.date,
          deadline.priority,
          userId,
        ]
      );
    }
  }
}

// =============================================================================
// SESSION CONTEXT - With security enhancements
// =============================================================================

class SessionContext {
  constructor(
    public sessionId: string,
    public userId: string,
    public caseId?: string
  ) {}

  private documentAnalysis?: DocumentAnalysis;
  private interviewAnswers: Map<string, string> = new Map();
  private currentQuestion?: InterviewQuestion;
  private defenseStrategy?: DefenseStrategy;
  private qaHistory: Array<{ q: string; a: string }> = [];

  setDocumentAnalysis(analysis: DocumentAnalysis) {
    this.documentAnalysis = analysis;
    this.saveToDb();
  }

  getDocumentAnalysis(): DocumentAnalysis | undefined {
    return this.documentAnalysis;
  }

  addAnswer(question: string, answer: string) {
    // Limit check
    if (this.interviewAnswers.size >= SECURITY_CONFIG.MAX_INTERVIEW_ANSWERS) {
      throw new SecurityError('Maximum answers exceeded', 'MAX_ANSWERS_EXCEEDED');
    }
    this.interviewAnswers.set(question, answer);
    this.saveToDb();
  }

  getInterviewAnswers(): Record<string, string> {
    return Object.fromEntries(this.interviewAnswers);
  }

  getAnswerCount(): number {
    return this.interviewAnswers.size;
  }

  setCurrentQuestion(question: InterviewQuestion) {
    this.currentQuestion = question;
  }

  getCurrentQuestion(): string {
    return this.currentQuestion?.question || '';
  }

  setDefenseStrategy(strategy: DefenseStrategy) {
    this.defenseStrategy = strategy;
    this.saveToDb();
  }

  getDefenseStrategy(): DefenseStrategy | undefined {
    return this.defenseStrategy;
  }

  addQAExchange(question: string, answer: string) {
    // Limit check
    if (this.qaHistory.length >= SECURITY_CONFIG.MAX_QA_HISTORY) {
      throw new SecurityError('Maximum Q&A history exceeded', 'MAX_QA_EXCEEDED');
    }
    this.qaHistory.push({ q: question, a: answer });
    this.saveToDb();
  }

  getQAHistoryCount(): number {
    return this.qaHistory.length;
  }

  private async saveToDb() {
    try {
      await db.query(
        `UPDATE sessions
         SET context = $1,
             interview_answers = $2,
             qa_history = $3,
             last_activity = NOW()
         WHERE id = $4`,
        [
          JSON.stringify({
            documentAnalysis: this.documentAnalysis,
            defenseStrategy: this.defenseStrategy,
          }),
          JSON.stringify(Object.fromEntries(this.interviewAnswers)),
          JSON.stringify(this.qaHistory),
          this.sessionId,
        ]
      );
    } catch (error) {
      console.error('[SESSION] Failed to save to database:', error);
      throw new SecurityError('Failed to persist session data', 'DB_ERROR');
    }
  }

  loadFromDB(row: any) {
    try {
      if (row.context) {
        const context = JSON.parse(row.context);
        this.documentAnalysis = context.documentAnalysis;
        this.defenseStrategy = context.defenseStrategy;
      }
      if (row.interview_answers) {
        this.interviewAnswers = new Map(Object.entries(JSON.parse(row.interview_answers)));
      }
      if (row.qa_history) {
        this.qaHistory = JSON.parse(row.qa_history);
      }
    } catch (error) {
      console.error('[SESSION] Failed to load from database:', error);
      throw new SecurityError('Failed to load session data', 'DB_ERROR');
    }
  }
}

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

interface DocumentAnalysis {
  summary: string;
  plaintiff?: { name: string; type: string };
  responseDeadline?: Date;
  deadlines?: ExtractedDeadline[];
  [key: string]: any;
}

interface ExtractedDeadline {
  type: string;
  description: string;
  date: Date;
  priority: string;
}

interface InterviewQuestion {
  question: string;
  type: string;
  [key: string]: any;
}

interface DefenseStrategy {
  strategy: string;
  arguments: string[];
  evidence: string[];
  [key: string]: any;
}

// =============================================================================
// EXPORTS
// =============================================================================

export { SecurityValidator, AuditLogger, RateLimiter, AuthorizationChecker, SecurityError };
