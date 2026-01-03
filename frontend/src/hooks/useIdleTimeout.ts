'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export interface IdleTimeoutConfig {
  timeoutMinutes: number;
  warningMinutes: number;
  onTimeout: () => void;
  onWarning?: () => void;
  onActivity?: () => void;
  enabled?: boolean;
}

export interface IdleTimeoutState {
  isIdle: boolean;
  isWarning: boolean;
  remainingSeconds: number;
  resetTimer: () => void;
}

const ACTIVITY_EVENTS = [
  'mousedown',
  'mousemove',
  'keydown',
  'scroll',
  'touchstart',
  'click',
  'wheel',
] as const;

const STORAGE_KEY = 'lastActivityTime';

export const useIdleTimeout = ({
  timeoutMinutes,
  warningMinutes,
  onTimeout,
  onWarning,
  onActivity,
  enabled = true,
}: IdleTimeoutConfig): IdleTimeoutState => {
  const [isIdle, setIsIdle] = useState(false);
  const [isWarning, setIsWarning] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(timeoutMinutes * 60);

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const warningRef = useRef<NodeJS.Timeout | null>(null);
  const countdownRef = useRef<NodeJS.Timeout | null>(null);
  const lastActivityRef = useRef<number>(Date.now());

  const timeoutMs = timeoutMinutes * 60 * 1000;
  const warningMs = warningMinutes * 60 * 1000;
  const warningStartMs = timeoutMs - warningMs;

  const clearAllTimers = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (warningRef.current) {
      clearTimeout(warningRef.current);
      warningRef.current = null;
    }
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
  }, []);

  const startCountdown = useCallback(() => {
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
    }

    const startTime = Date.now();
    const endTime = lastActivityRef.current + timeoutMs;

    countdownRef.current = setInterval(() => {
      const now = Date.now();
      const remaining = Math.max(0, Math.ceil((endTime - now) / 1000));
      setRemainingSeconds(remaining);

      if (remaining <= 0) {
        if (countdownRef.current) {
          clearInterval(countdownRef.current);
        }
      }
    }, 1000);
  }, [timeoutMs]);

  const resetTimer = useCallback(() => {
    if (!enabled) return;

    const now = Date.now();
    lastActivityRef.current = now;

    // Store activity time for cross-tab sync
    try {
      localStorage.setItem(STORAGE_KEY, now.toString());
    } catch (e) {
      // Ignore storage errors
    }

    clearAllTimers();
    setIsIdle(false);
    setIsWarning(false);
    setRemainingSeconds(timeoutMinutes * 60);

    // Set warning timer
    warningRef.current = setTimeout(() => {
      setIsWarning(true);
      onWarning?.();
      startCountdown();
    }, warningStartMs);

    // Set timeout timer
    timeoutRef.current = setTimeout(() => {
      setIsIdle(true);
      clearAllTimers();
      onTimeout();
    }, timeoutMs);

    onActivity?.();
  }, [
    enabled,
    timeoutMinutes,
    timeoutMs,
    warningStartMs,
    clearAllTimers,
    startCountdown,
    onTimeout,
    onWarning,
    onActivity,
  ]);

  // Handle activity events
  useEffect(() => {
    if (!enabled) return;

    // Throttle activity detection to avoid excessive updates
    let throttleTimeout: NodeJS.Timeout | null = null;
    const throttleMs = 1000; // 1 second throttle

    const handleActivity = () => {
      if (throttleTimeout) return;

      throttleTimeout = setTimeout(() => {
        throttleTimeout = null;
      }, throttleMs);

      // Only reset if not already in timeout state
      if (!isIdle) {
        resetTimer();
      }
    };

    // Add event listeners
    ACTIVITY_EVENTS.forEach((event) => {
      window.addEventListener(event, handleActivity, { passive: true });
    });

    // Initialize timer
    resetTimer();

    return () => {
      ACTIVITY_EVENTS.forEach((event) => {
        window.removeEventListener(event, handleActivity);
      });
      clearAllTimers();
      if (throttleTimeout) {
        clearTimeout(throttleTimeout);
      }
    };
  }, [enabled, isIdle, resetTimer, clearAllTimers]);

  // Cross-tab synchronization
  useEffect(() => {
    if (!enabled) return;

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY && e.newValue) {
        const otherTabActivity = parseInt(e.newValue, 10);
        if (otherTabActivity > lastActivityRef.current) {
          // Another tab had more recent activity, sync our timer
          lastActivityRef.current = otherTabActivity;
          if (!isIdle) {
            resetTimer();
          }
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [enabled, isIdle, resetTimer]);

  // Handle visibility change (user switches tabs/windows)
  useEffect(() => {
    if (!enabled) return;

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        // Check if we should have timed out while tab was hidden
        const now = Date.now();
        const elapsed = now - lastActivityRef.current;

        if (elapsed >= timeoutMs) {
          setIsIdle(true);
          clearAllTimers();
          onTimeout();
        } else if (elapsed >= warningStartMs) {
          setIsWarning(true);
          onWarning?.();
          startCountdown();
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [enabled, timeoutMs, warningStartMs, clearAllTimers, startCountdown, onTimeout, onWarning]);

  return {
    isIdle,
    isWarning,
    remainingSeconds,
    resetTimer,
  };
};

export default useIdleTimeout;
