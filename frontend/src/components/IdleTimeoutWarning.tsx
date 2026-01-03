'use client';

import React from 'react';
import * as AlertDialog from '@radix-ui/react-alert-dialog';

interface IdleTimeoutWarningProps {
  isOpen: boolean;
  remainingSeconds: number;
  onStayLoggedIn: () => void;
  onLogout: () => void;
}

export const IdleTimeoutWarning: React.FC<IdleTimeoutWarningProps> = ({
  isOpen,
  remainingSeconds,
  onStayLoggedIn,
  onLogout,
}) => {
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins > 0) {
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    return `${secs} seconds`;
  };

  return (
    <AlertDialog.Root open={isOpen}>
      <AlertDialog.Portal>
        <AlertDialog.Overlay className="fixed inset-0 bg-black/50 z-50" />
        <AlertDialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg shadow-xl p-6 w-full max-w-md z-50">
          <AlertDialog.Title className="text-lg font-semibold text-gray-900">
            Session Timeout Warning
          </AlertDialog.Title>
          <AlertDialog.Description className="mt-3 text-sm text-gray-600">
            <p>
              Your session is about to expire due to inactivity. You will be
              automatically logged out in{' '}
              <span className="font-semibold text-red-600">
                {formatTime(remainingSeconds)}
              </span>
              .
            </p>
            <p className="mt-2">
              Click &quot;Stay Logged In&quot; to continue your session, or &quot;Log Out&quot; to
              end your session now.
            </p>
          </AlertDialog.Description>

          <div className="mt-6 flex justify-end gap-3">
            <AlertDialog.Cancel asChild>
              <button
                onClick={onLogout}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
              >
                Log Out
              </button>
            </AlertDialog.Cancel>
            <AlertDialog.Action asChild>
              <button
                onClick={onStayLoggedIn}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
              >
                Stay Logged In
              </button>
            </AlertDialog.Action>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-red-500 h-2 rounded-full transition-all duration-1000"
                style={{
                  width: `${Math.max(0, (remainingSeconds / 120) * 100)}%`,
                }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              For security purposes, sessions expire after periods of inactivity.
            </p>
          </div>
        </AlertDialog.Content>
      </AlertDialog.Portal>
    </AlertDialog.Root>
  );
};

export default IdleTimeoutWarning;
