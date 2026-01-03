'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import {
  User,
  LogOut,
  Settings,
  HelpCircle,
  Star,
  BookOpen
} from 'lucide-react';
import { RatingModal } from '@/components/ratings';
import { NotificationBell } from '@/components/notifications/NotificationBell';

interface ToolbarProps {
  className?: string;
  showNotifications?: boolean;
  showSettings?: boolean;
  showHelp?: boolean;
}

export default function Toolbar({
  className = '',
  showNotifications = true,
  showSettings = true,
  showHelp = true
}: ToolbarProps) {
  const router = useRouter();
  const [showRatingModal, setShowRatingModal] = useState(false);
  const { user, logout, isAuthenticated } = useAuth();

  const handleStartTour = () => {
    // Dispatch event to restart the guided tour
    window.dispatchEvent(new CustomEvent('restartGuidedTour'));
  };

  const handleLogout = async () => {
    await logout();  // Logout function handles redirect to landing page
  };

  const handleLogin = () => {
    router.push('/auth/login');
  };

  const handleOpenHelp = () => {
    // Dispatch custom event to open the HelpAgent component
    window.dispatchEvent(new CustomEvent('openHelpAgent'));
  };

  const getUserInitials = () => {
    if (!user) return 'U';
    const nameParts = user.full_name?.split(' ') || [];
    if (nameParts.length >= 2) {
      return nameParts[0][0] + nameParts[1][0];
    }
    return user.full_name?.[0] || user.email?.[0] || 'U';
  };

  // Show login button if not authenticated
  if (!isAuthenticated) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        {/* Rate App Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowRatingModal(true)}
          className="text-yellow-500 hover:text-yellow-600 hover:bg-yellow-50"
          title="Rate This App"
        >
          <Star className="w-5 h-5" />
        </Button>

        {/* Help Button */}
        {showHelp && (
          <Button
            variant="ghost"
            size="sm"
            onClick={handleOpenHelp}
            className="text-gray-600 hover:text-gray-900"
            title="Help & Documentation"
          >
            <HelpCircle className="w-5 h-5" />
          </Button>
        )}

        {/* Login Button */}
        <Button
          variant="default"
          size="sm"
          onClick={handleLogin}
          className="bg-teal-600 hover:bg-teal-700 text-white"
          title="Log In"
        >
          <User className="w-4 h-4 mr-2" />
          <span>Login</span>
        </Button>

        {/* Rating Modal */}
        <RatingModal
          open={showRatingModal}
          onOpenChange={setShowRatingModal}
        />
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {/* Rate App Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setShowRatingModal(true)}
        className="text-yellow-500 hover:text-yellow-600 hover:bg-yellow-50"
        title="Rate This App"
      >
        <Star className="w-5 h-5" />
      </Button>

      {/* Help Button */}
      {showHelp && (
        <Button
          variant="ghost"
          size="sm"
          onClick={handleOpenHelp}
          className="text-gray-600 hover:text-gray-900"
          title="Help & Documentation"
        >
          <HelpCircle className="w-5 h-5" />
        </Button>
      )}

      {/* Guided Tour Button */}
      <Button
        variant="ghost"
        size="sm"
        onClick={handleStartTour}
        className="text-blue-600 hover:text-blue-700 hover:bg-blue-50"
        title="Take a Guided Tour"
      >
        <BookOpen className="w-5 h-5" />
      </Button>

      {/* Notifications Button */}
      {showNotifications && user?.id && (
        <NotificationBell
          userId={user.id}
          className="text-slate-300 hover:text-white hover:bg-slate-700"
        />
      )}

      {/* Settings Button */}
      {showSettings && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/settings')}
          className="text-slate-300 hover:text-white hover:bg-slate-700"
          title="Settings"
        >
          <Settings className="w-5 h-5" />
        </Button>
      )}

      {/* User Profile Dropdown */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors">
        <div className="w-8 h-8 bg-green-600 rounded-full flex items-center justify-center">
          <span className="text-sm font-semibold text-white">✓</span>
        </div>
        <div className="hidden md:block text-left">
          <p className="text-sm font-semibold text-gray-900 leading-none">
            Logged in
          </p>
          <p className="text-xs text-green-600 capitalize leading-none mt-0.5">
            Verified
          </p>
        </div>
      </div>

      {/* Logout Button */}
      <Button
        variant="outline"
        size="sm"
        onClick={handleLogout}
        className="text-red-600 border-red-200 hover:bg-red-50 hover:border-red-300"
        title="Log Out"
      >
        <LogOut className="w-4 h-4 mr-2" />
        <span>Logout</span>
      </Button>

      {/* Rating Modal */}
      <RatingModal
        open={showRatingModal}
        onOpenChange={setShowRatingModal}
      />
    </div>
  );
}
