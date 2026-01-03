'use client';

import React from 'react';
import { useAuthProvider, AuthContext } from '@/hooks/useAuth';
import { IdleTimeoutProvider } from './IdleTimeoutProvider';

interface AuthProviderProps {
  children: React.ReactNode;
  idleTimeoutMinutes?: number;
  idleWarningMinutes?: number;
}

const AuthProvider: React.FC<AuthProviderProps> = ({
  children,
  idleTimeoutMinutes = 15,
  idleWarningMinutes = 2,
}) => {
  const authValue = useAuthProvider();

  return (
    <AuthContext.Provider value={authValue}>
      <IdleTimeoutProvider
        isAuthenticated={authValue.isAuthenticated}
        onLogout={authValue.logout}
        timeoutMinutes={idleTimeoutMinutes}
        warningMinutes={idleWarningMinutes}
      >
        {children}
      </IdleTimeoutProvider>
    </AuthContext.Provider>
  );
};

export { AuthProvider };
