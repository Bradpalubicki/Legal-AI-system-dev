export class QASanitizer {
  // List of words that should NEVER appear in Q&A responses
  private static FORBIDDEN_WORDS = [
    'DEFENSE OPTIONS',
    'TO BUILD YOUR DEFENSE',
    'Statute of Limitations',
    'Lack of Evidence',
    'Procedural Errors',
    'defense strategy',
    'Your defenses are',
    'BUILD A DEFENSE',
    'defense builder',
    'legal defenses',
    'affirmative defense',
    'counterclaim'
  ];

  static sanitizeResponse(text: string): string {
    // Remove any defense-related content
    let cleaned = text;

    for (const forbidden of this.FORBIDDEN_WORDS) {
      cleaned = cleaned.replace(new RegExp(forbidden, 'gi'), '');
    }

    // If the response is now empty or broken, return safe default
    if (cleaned.trim().length < 10 || cleaned.includes('**')) {
      return 'I can answer questions about deadlines, amounts, and procedures. What would you like to know?';
    }

    return cleaned.trim();
  }

  static isDefenseContent(text: string): boolean {
    const lower = text.toLowerCase();

    // Check if any forbidden words appear
    for (const forbidden of this.FORBIDDEN_WORDS) {
      if (lower.includes(forbidden.toLowerCase())) {
        return true;
      }
    }

    // Check for defense-building patterns
    const defensePatterns = [
      /defense\s+option/i,
      /build.*defense/i,
      /your.*defense/i,
      /statute.*limitation/i,
      /lack.*evidence/i,
      /procedural.*error/i,
      /affirmative.*defense/i,
      /counterclaim/i
    ];

    for (const pattern of defensePatterns) {
      if (pattern.test(text)) {
        return true;
      }
    }

    return false;
  }

  static getCleanAnswer(text: string): string {
    // First check if it contains defense content
    if (this.isDefenseContent(text)) {
      return 'For defense strategies, please use the Defense Builder feature. I can answer other questions about your case.';
    }

    // Otherwise sanitize and return
    return this.sanitizeResponse(text);
  }
}
