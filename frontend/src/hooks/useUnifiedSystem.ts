/**
 * Unified System Hook
 * Single hook to manage ALL legal system interactions
 * Provides document upload, interviewing, defense building, and chat
 */

import { useState, useCallback, useEffect } from 'react';

import { API_CONFIG } from '../config/api';
interface SystemState {
  state: 'idle' | 'analyzing' | 'interviewing' | 'building' | 'ready' | 'chatting';
  document: string | null;
  documentAnalysis: any;
  currentQuestion: any;
  answers: Record<string, string>;
  defenses: any[];
  chatHistory: ChatMessage[];
  efficiency: {
    aiCalls: number;
    cachedResponses: number;
    processingTime: number;
  };
}

interface ChatMessage {
  type: 'user' | 'ai';
  message: string;
  timestamp?: string;
}

interface UnifiedAPIResponse {
  system_efficiency?: {
    ai_calls: number;
    cached_responses: number;
    processing_time?: number;
    cache_rate?: number;
  };
  [key: string]: any;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || API_CONFIG.BASE_URL;

export function useUnifiedSystem() {
  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substring(7)}`);

  const [systemState, setSystemState] = useState<SystemState>({
    state: 'idle',
    document: null,
    documentAnalysis: null,
    currentQuestion: null,
    answers: {},
    defenses: [],
    chatHistory: [],
    efficiency: {
      aiCalls: 0,
      cachedResponses: 0,
      processingTime: 0
    }
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Single unified API call
  const callUnifiedAPI = useCallback(async (action: string, data?: any): Promise<UnifiedAPIResponse> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/unified/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          action,
          data: data || {}
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result: UnifiedAPIResponse = await response.json();

      // Update efficiency metrics
      if (result.system_efficiency) {
        setSystemState(prev => ({
          ...prev,
          efficiency: {
            aiCalls: result.system_efficiency?.ai_calls || 0,
            cachedResponses: result.system_efficiency?.cached_responses || 0,
            processingTime: result.system_efficiency?.processing_time || 0
          }
        }));
      }

      console.log(`[Unified System] ${action} completed`, {
        aiCalls: result.system_efficiency?.ai_calls,
        cached: result.system_efficiency?.cached_responses,
        cacheRate: result.system_efficiency?.cache_rate
      });

      return result;

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Unified API error:', errorMessage);
      setError(errorMessage);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  // Upload and analyze document
  const uploadDocument = useCallback(async (file: File) => {
    try {
      const text = await extractTextFromFile(file);

      const result = await callUnifiedAPI('upload_document', {
        documentText: text
      });

      setSystemState(prev => ({
        ...prev,
        state: result.first_question ? 'interviewing' : 'ready',
        document: text,
        documentAnalysis: result.document_analysis || result.summary,
        currentQuestion: result.first_question
      }));

      return result;
    } catch (error) {
      console.error('Document upload error:', error);
      throw error;
    }
  }, [callUnifiedAPI]);

  // Answer interview question
  const answerQuestion = useCallback(async (answer: string) => {
    if (!systemState.currentQuestion) {
      throw new Error('No current question to answer');
    }

    try {
      const result = await callUnifiedAPI('answer_question', {
        questionId: systemState.currentQuestion.id,
        answer
      });

      setSystemState(prev => ({
        ...prev,
        answers: {
          ...prev.answers,
          [systemState.currentQuestion?.id]: answer
        },
        currentQuestion: result.next_question,
        state: result.complete ? 'building' : 'interviewing',
        defenses: result.defense_found
          ? [...prev.defenses, result.defense_found]
          : prev.defenses
      }));

      // Auto-build defense if interview complete
      if (result.complete && result.ready_for_defense) {
        setTimeout(() => buildDefense(), 100);
      }

      return result;
    } catch (error) {
      console.error('Answer question error:', error);
      throw error;
    }
  }, [callUnifiedAPI, systemState.currentQuestion]);

  // Build defense strategy
  const buildDefense = useCallback(async () => {
    try {
      setSystemState(prev => ({ ...prev, state: 'building' }));

      const result = await callUnifiedAPI('build_defense');

      setSystemState(prev => ({
        ...prev,
        state: 'ready',
        defenses: result.defenses || []
      }));

      return result;
    } catch (error) {
      console.error('Build defense error:', error);
      setSystemState(prev => ({ ...prev, state: 'interviewing' }));
      throw error;
    }
  }, [callUnifiedAPI]);

  // Send chat message
  const sendChatMessage = useCallback(async (message: string) => {
    try {
      const userMessage: ChatMessage = {
        type: 'user',
        message,
        timestamp: new Date().toISOString()
      };

      // Optimistically add user message
      setSystemState(prev => ({
        ...prev,
        state: 'chatting',
        chatHistory: [...prev.chatHistory, userMessage]
      }));

      const result = await callUnifiedAPI('chat_message', { message });

      const aiMessage: ChatMessage = {
        type: 'ai',
        message: result.response,
        timestamp: new Date().toISOString()
      };

      setSystemState(prev => ({
        ...prev,
        chatHistory: [...prev.chatHistory, aiMessage]
      }));

      return result;
    } catch (error) {
      console.error('Chat message error:', error);
      // Remove optimistic user message on error
      setSystemState(prev => ({
        ...prev,
        chatHistory: prev.chatHistory.slice(0, -1)
      }));
      throw error;
    }
  }, [callUnifiedAPI]);

  // Get current context (for debugging)
  const getContext = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/unified/session/${sessionId}/context`);
      return response.json();
    } catch (error) {
      console.error('Get context error:', error);
      throw error;
    }
  }, [sessionId]);

  // Get system status
  const getStatus = useCallback(async () => {
    try {
      const result = await callUnifiedAPI('get_status');
      return result;
    } catch (error) {
      console.error('Get status error:', error);
      throw error;
    }
  }, [callUnifiedAPI]);

  // Clear session
  const clearSession = useCallback(async () => {
    try {
      await fetch(`${API_BASE_URL}/api/v1/unified/session/${sessionId}`, {
        method: 'DELETE'
      });

      // Reset state
      setSystemState({
        state: 'idle',
        document: null,
        documentAnalysis: null,
        currentQuestion: null,
        answers: {},
        defenses: [],
        chatHistory: [],
        efficiency: {
          aiCalls: 0,
          cachedResponses: 0,
          processingTime: 0
        }
      });
    } catch (error) {
      console.error('Clear session error:', error);
      throw error;
    }
  }, [sessionId]);

  return {
    // State
    systemState,
    loading,
    error,
    sessionId,

    // Actions
    uploadDocument,
    answerQuestion,
    buildDefense,
    sendChatMessage,
    getContext,
    getStatus,
    clearSession,

    // Computed values
    isReady: systemState.state === 'ready',
    hasDocument: !!systemState.document,
    isInterviewing: systemState.state === 'interviewing',
    isChatting: systemState.state === 'chatting',
    questionCount: Object.keys(systemState.answers).length,
    defenseCount: systemState.defenses.length,
    efficiencyScore: systemState.efficiency.cachedResponses /
                     Math.max(systemState.efficiency.aiCalls, 1),

    // Efficiency metrics
    aiCallsCount: systemState.efficiency.aiCalls,
    cachedResponsesCount: systemState.efficiency.cachedResponses,
    totalProcessingTime: systemState.efficiency.processingTime
  };
}

// Helper function to extract text from file
async function extractTextFromFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      const text = e.target?.result as string;
      resolve(text);
    };

    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };

    reader.readAsText(file);
  });
}
