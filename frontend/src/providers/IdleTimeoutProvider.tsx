'use client';

import React, { createContext, useContext, useCallback, useState, useEffect } from 'react';
import { useIdleTimeout } from '@/hooks/useIdleTimeout';
import { IdleTimeoutWarning } from '@/components/IdleTimeoutWarning';
import { logComplianceEvent } from '@/utils/compliance-utils';

interface IdleTimeoutContextType {
  isWarning: boolean;
  remainingSeconds: number;
  resetTimer: () => void;
  isEnabled: boolean;
}

const IdleTimeoutContext = createContext<IdleTimeoutContextType | undefined>(undefined);

export const useIdleTimeoutContext = () => {
  const context = useContext(IdleTimeoutContext);
  if (!context) {
    throw new Error('useIdleTimeoutContext must be used within IdleTimeoutProvider');
  }
  return context;
};

interface IdleTimeoutProviderProps {
  children: React.ReactNode;
  isAuthenticated: boolean;
  onLogout: () => void;
  timeoutMinutes?: number;
  warningMinutes?: number;
}

export const IdleTimeoutProvider: React.FC<IdleTimeoutProviderProps> = ({
  children,
  isAuthenticated,
  onLogout,
  timeoutMinutes = 15,
  warningMinutes = 2,
}) => {
  const [showWarning, setShowWarning] = useState(false);

  const handleWarning = useCallback(() => {
    setShowWarning(true);
    logComplianceEvent('Idle timeout warning shown', {
      timeoutMinutes,
      warningMinutes
    });
  }, [timeoutMinutes, warningMinutes]);

  const handleTimeout = useCallback(() => {
    setShowWarning(false);
    logComplianceEvent('Idle timeout - logging out user');
    onLogout();
  }, [onLogout]);

  const handleActivity = useCallback(() => {
    if (showWarning) {
      setShowWarning(false);
    }
  }, [showWarning]);

  const { isWarning, remainingSeconds, resetTimer } = useIdleTimeout({
    timeoutMinutes,
    warningMinutes,
    onTimeout: handleTimeout,
    onWarning: handleWarning,
    onActivity: handleActivity,
    enabled: isAuthenticated,
  });

  const handleStayLoggedIn = useCallback(() => {
    setShowWarning(false);
    resetTimer();
    logComplianceEvent('User chose to stay logged in');
  }, [resetTimer]);

  const handleLogoutClick = useCallback(() => {
    setShowWarning(false);
    logComplianceEvent('User chose to logout from timeout warning');
    onLogout();
  }, [onLogout]);

  // Sync showWarning with isWarning from hook
  useEffect(() => {
    if (isWarning && !showWarning) {
      setShowWarning(true);
    }
  }, [isWarning, showWarning]);

  const contextValue: IdleTimeoutContextType = {
    isWarning: showWarning,
    remainingSeconds,
    resetTimer,
    isEnabled: isAuthenticated,
  };

  return (
    <IdleTimeoutContext.Provider value={contextValue}>
      {children}
      <IdleTimeoutWarning
        isOpen={showWarning}
        remainingSeconds={remainingSeconds}
        onStayLoggedIn={handleStayLoggedIn}
        onLogout={handleLogoutClick}
      />
    </IdleTimeoutContext.Provider>
  );
};

export default IdleTimeoutProvider;
