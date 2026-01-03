'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';

import { API_CONFIG } from '../config/api';
interface RateLimitStatus {
  redis_available: boolean;
  rate_limited: boolean;
  attempts: number;
  max_attempts: number;
  remaining_attempts: number;
  reset_in_seconds: number;
  window_seconds: number;
  message?: string;
  error?: string;
}

export default function PACERRateLimitMonitor() {
  const [status, setStatus] = useState<RateLimitStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clearingLimit, setClearingLimit] = useState(false);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/monitoring/rate-limit`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch rate limit status');
      }

      const data = await response.json();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch status');
    } finally {
      setLoading(false);
    }
  };

  const clearRateLimit = async () => {
    if (!confirm('Are you sure you want to clear the rate limit?')) {
      return;
    }

    try {
      setClearingLimit(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/pacer/monitoring/rate-limit/clear`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to clear rate limit');
      }

      const data = await response.json();
      if (data.success) {
        alert('Rate limit cleared successfully!');
        await fetchStatus();
      } else {
        throw new Error(data.error || 'Failed to clear rate limit');
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to clear rate limit');
    } finally {
      setClearingLimit(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Rate Limit Monitor</h3>
        <p className="text-gray-500">Loading...</p>
      </Card>
    );
  }

  if (error && !status) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Rate Limit Monitor</h3>
        <div className="bg-red-50 border border-red-200 rounded p-3">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
        <button
          onClick={fetchStatus}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Retry
        </button>
      </Card>
    );
  }

  if (!status) {
    return null;
  }

  // Handle Redis unavailable
  if (!status.redis_available) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Rate Limit Monitor</h3>
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
          <p className="text-yellow-800 text-sm">
            {status.message || 'Rate limiting is not active (Redis unavailable)'}
          </p>
        </div>
      </Card>
    );
  }

  // Calculate percentage
  const percentage = status.max_attempts > 0
    ? (status.attempts / status.max_attempts) * 100
    : 0;

  // Determine color based on status
  const getColorClasses = () => {
    if (status.rate_limited) {
      return {
        bg: 'bg-red-50',
        border: 'border-red-200',
        text: 'text-red-800',
        bar: 'bg-red-500',
      };
    } else if (percentage >= 60) {
      return {
        bg: 'bg-yellow-50',
        border: 'border-yellow-200',
        text: 'text-yellow-800',
        bar: 'bg-yellow-500',
      };
    }
    return {
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-800',
      bar: 'bg-green-500',
    };
  };

  const colors = getColorClasses();

  const formatTime = (seconds: number) => {
    if (seconds <= 0) return '0s';
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    }
    return `${secs}s`;
  };

  return (
    <Card className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Rate Limit Monitor</h3>
        <button
          onClick={fetchStatus}
          className="text-sm text-gray-600 hover:text-gray-900"
          title="Refresh status"
        >
          Refresh
        </button>
      </div>

      <div className={`rounded-lg p-4 ${colors.bg} border ${colors.border}`}>
        {/* Status Header */}
        <div className="flex justify-between items-center mb-3">
          <div>
            <p className={`font-semibold ${colors.text}`}>
              {status.rate_limited ? 'Rate Limited' : 'Active'}
            </p>
            <p className="text-sm text-gray-600">
              Authentication Attempts
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">
              {status.attempts}/{status.max_attempts}
            </p>
            <p className="text-sm text-gray-600">
              {status.remaining_attempts} remaining
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${colors.bar}`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
        </div>

        {/* Details */}
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-gray-600">Window:</span>
            <span className="ml-2 font-medium">
              {formatTime(status.window_seconds)}
            </span>
          </div>
          {status.reset_in_seconds > 0 && (
            <div>
              <span className="text-gray-600">Resets in:</span>
              <span className="ml-2 font-medium">
                {formatTime(status.reset_in_seconds)}
              </span>
            </div>
          )}
        </div>

        {/* Rate Limited Message */}
        {status.rate_limited && (
          <div className="mt-3 pt-3 border-t border-red-300">
            <p className="text-sm text-red-800 mb-2">
              Too many failed authentication attempts. Please wait for the rate limit to reset or contact support.
            </p>
            <button
              onClick={clearRateLimit}
              disabled={clearingLimit}
              className="w-full px-3 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
            >
              {clearingLimit ? 'Clearing...' : 'Clear Rate Limit'}
            </button>
          </div>
        )}

        {/* Warning Message */}
        {!status.rate_limited && percentage >= 60 && (
          <div className="mt-3 pt-3 border-t border-yellow-300">
            <p className="text-sm text-yellow-800">
              Warning: You're approaching the rate limit. Please ensure you're using correct credentials.
            </p>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="mt-4 text-xs text-gray-500">
        <p>
          Rate limiting protects against brute force attacks by limiting authentication attempts.
          The limit resets automatically after the window period.
        </p>
      </div>
    </Card>
  );
}
