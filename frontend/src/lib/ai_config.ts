/**
 * AI API Configuration
 * Handles authentication for OpenAI and Anthropic APIs
 * Use ONE provider consistently - don't mix authentication methods
 */

export type AIProvider = 'openai' | 'anthropic';

export interface AIConfig {
  provider: AIProvider;
  apiKey: string;
  model: string;
}

/**
 * Get OpenAI headers for API requests
 */
export function getOpenAIHeaders(): HeadersInit {
  const apiKey = process.env.OPENAI_API_KEY;

  if (!apiKey) {
    throw new Error('OPENAI_API_KEY not configured');
  }

  return {
    'Authorization': `Bearer ${apiKey}`,
    'Content-Type': 'application/json'
  };
}

/**
 * Get Anthropic/Claude headers for API requests
 */
export function getAnthropicHeaders(): HeadersInit {
  const apiKey = process.env.ANTHROPIC_API_KEY || process.env.CLAUDE_API_KEY;

  if (!apiKey) {
    throw new Error('ANTHROPIC_API_KEY not configured');
  }

  return {
    'x-api-key': apiKey,
    'anthropic-version': '2023-06-01',
    'Content-Type': 'application/json'
  };
}

/**
 * Get AI configuration based on provider
 */
export function getAIConfig(provider: AIProvider = 'openai'): AIConfig {
  if (provider === 'openai') {
    return {
      provider: 'openai',
      apiKey: process.env.OPENAI_API_KEY || '',
      model: 'gpt-4-turbo-preview'
    };
  } else {
    return {
      provider: 'anthropic',
      apiKey: process.env.ANTHROPIC_API_KEY || process.env.CLAUDE_API_KEY || '',
      model: 'claude-sonnet-4-5-20250929'
    };
  }
}

/**
 * Get headers for the configured AI provider
 */
export function getAIHeaders(provider: AIProvider = 'openai'): HeadersInit {
  if (provider === 'openai') {
    return getOpenAIHeaders();
  } else {
    return getAnthropicHeaders();
  }
}

// Export default provider (can be changed based on needs)
export const DEFAULT_AI_PROVIDER: AIProvider = 'openai';
