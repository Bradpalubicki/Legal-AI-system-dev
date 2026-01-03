'use client';

import { useState, useEffect, useCallback, useContext, createContext } from 'react';
import { User, LoginRequest, LoginResponse, AuthContextType } from '@/types/legal-compliance';
import { 
  buildApiUrl, 
  getErrorMessage, 
  logComplianceEvent, 
  logComplianceError,
  clearComplianceCache,
  setComplianceCookie,
  getComplianceCookie
} from '@/utils/compliance-utils';
import axios from 'axios';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const useAuthProvider = (): AuthContextType => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const isAuthenticated = Boolean(user);

  const login = useCallback(async (credentials: LoginRequest) => {
    setIsLoading(true);
    setError(null);

    try {
      logComplianceEvent('Attempting login', { email: credentials.email });

      // Backend only accepts email and password (no MFA support yet)
      const loginPayload = {
        email: credentials.email,
        password: credentials.password
      };

      const response = await axios.post(buildApiUrl('/api/v1/auth/login'), loginPayload);

      // Backend returns data directly: { access_token, refresh_token, user, ... }
      const loginData = response.data;

      // Store tokens
      localStorage.setItem('accessToken', loginData.access_token);
      localStorage.setItem('refreshToken', loginData.refresh_token);

      // Set compliance cookies
      setComplianceCookie('session_active', 'true', 1);
      setComplianceCookie('user_id', loginData.user.id, 1);

      // Set user state
      setUser(loginData.user);

      logComplianceEvent('Login successful', {
        userId: loginData.user.id,
        role: loginData.user.role
      });

      // Return loginData so caller can access new_filings
      return loginData;
    } catch (err: any) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      logComplianceError('Login failed', err);
      
      // Clear any existing tokens on login failure
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      setUser(null);
      
      throw err; // Re-throw so component can handle it
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async (redirectToHome: boolean = true) => {
    try {
      logComplianceEvent('Logging out', { userId: user?.id });

      // Call logout endpoint BEFORE clearing tokens
      const token = localStorage.getItem('accessToken');
      if (token) {
        try {
          await axios.post(buildApiUrl('/api/v1/auth/logout'), {}, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
        } catch (err) {
          logComplianceError('Server logout failed', err);
          // Continue with client-side logout even if server call fails
        }
      }

      // Clear tokens and user state
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      setUser(null);
      setError(null);

      // Clear session storage (new filings data, etc.) - prevents data carryover between users
      sessionStorage.clear();

      // Clear compliance cache
      clearComplianceCache();

      // Clear compliance cookies
      setComplianceCookie('session_active', '', -1);
      setComplianceCookie('user_id', '', -1);

      logComplianceEvent('Logout completed');

      // Redirect to landing page after logout
      if (redirectToHome && typeof window !== 'undefined') {
        window.location.href = '/';
      }

    } catch (err: any) {
      logComplianceError('Logout error', err);
    }
  }, [user?.id]);

  const refreshToken = useCallback(async () => {
    const refreshTokenValue = localStorage.getItem('refreshToken');
    if (!refreshTokenValue) {
      logout();
      return;
    }

    try {
      logComplianceEvent('Refreshing access token');
      
      const response = await axios.post(buildApiUrl('/api/v1/auth/refresh'), {
        refresh_token: refreshTokenValue
      });

      // Backend returns tokens directly
      const { access_token, refresh_token: newRefreshToken, user: updatedUser } = response.data;

      // Update tokens
      localStorage.setItem('accessToken', access_token);
      if (newRefreshToken) {
        localStorage.setItem('refreshToken', newRefreshToken);
      }

      // Update user if provided
      if (updatedUser) {
        setUser(updatedUser);
      }

      logComplianceEvent('Token refresh successful');
    } catch (err: any) {
      logComplianceError('Token refresh failed', err);
      logout(); // Force logout if refresh fails
    }
  }, [logout]);

  const getCurrentUser = useCallback(async () => {
    const token = localStorage.getItem('accessToken');
    if (!token) return;

    try {
      setIsLoading(true);
      
      const response = await axios.get(buildApiUrl('/api/v1/auth/me'), {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      // Backend returns user data directly
      const userData = response.data;
      setUser(userData);
      logComplianceEvent('Current user loaded', { userId: userData.id });
    } catch (err: any) {
      logComplianceError('Failed to get current user', err);
      // If unauthorized, logout
      if (err.response?.status === 401) {
        logout();
      }
    } finally {
      setIsLoading(false);
    }
  }, [logout]);

  // Initialize auth state on mount
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    const sessionActive = getComplianceCookie('session_active');

    if (token && sessionActive === 'true') {
      getCurrentUser();
    } else {
      setIsLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  // Set up token refresh interval
  useEffect(() => {
    if (!isAuthenticated) return;

    // Refresh token every 14 minutes (assuming 15 min expiry)
    const interval = setInterval(() => {
      refreshToken();
    }, 14 * 60 * 1000);

    return () => clearInterval(interval);
  }, [isAuthenticated, refreshToken]);

  // Set up axios interceptor for automatic token refresh
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // Don't retry auth endpoints - they should fail immediately
        // This prevents double-counting failed login attempts
        const isAuthEndpoint = originalRequest?.url?.includes('/auth/login') ||
                               originalRequest?.url?.includes('/auth/register') ||
                               originalRequest?.url?.includes('/auth/refresh');

        if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
          originalRequest._retry = true;
          
          try {
            await refreshToken();
            // Retry the original request with new token
            const token = localStorage.getItem('accessToken');
            originalRequest.headers['Authorization'] = `Bearer ${token}`;
            return axios(originalRequest);
          } catch (refreshError) {
            logout();
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, [refreshToken, logout]);

  return {
    user,
    login,
    logout,
    refreshToken,
    isAuthenticated,
    isLoading,
    error
  };
};

export { AuthContext };
