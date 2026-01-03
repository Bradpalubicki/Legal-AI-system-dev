// Custom hook for managing unified API sessions

import { useState, useCallback } from 'react';

interface SessionData {
  sessionId: string;
  sessionToken: string;
}

export function useSession() {
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createSession = useCallback(async (caseId?: string): Promise<SessionData> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/unified', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'analyze_document',
          data: { caseId },
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }

      const data = await response.json();
      const session = {
        sessionId: data.sessionId,
        sessionToken: data.sessionToken,
      };

      setSessionData(session);
      return session;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const callApi = useCallback(
    async <T = any>(action: string, data?: any): Promise<T> => {
      if (!sessionData) {
        throw new Error('No active session');
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/unified', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            action,
            sessionId: sessionData.sessionId,
            sessionToken: sessionData.sessionToken,
            data,
          }),
        });

        if (!response.ok) {
          throw new Error(`API call failed: ${response.statusText}`);
        }

        const result = await response.json();
        return result as T;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [sessionData]
  );

  const clearSession = useCallback(() => {
    setSessionData(null);
    setError(null);
  }, []);

  return {
    sessionData,
    isLoading,
    error,
    createSession,
    callApi,
    clearSession,
  };
}
