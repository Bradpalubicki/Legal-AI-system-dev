'use client';

import React from 'react';
import Link from 'next/link';
import CreditsDashboard from '@/components/PACER/CreditsDashboard';
import { useAuth } from '@/hooks/useAuth';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { AlertCircle, ArrowLeft, Home, Scale } from 'lucide-react';

export default function CreditsPage() {
  const { user } = useAuth();

  // For development/testing, use a default user if not authenticated
  const userId = user?.id ? Number(user.id) : 1;
  const username = user?.username || 'test_user';

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Navigation Bar */}
      <div className="mb-6 flex items-center gap-3">
        <Link href="/">
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            <Home className="h-4 w-4" />
            Dashboard
          </Button>
        </Link>
        <Link href="/?tab=pacer">
          <Button variant="outline" size="sm" className="flex items-center gap-2">
            <Scale className="h-4 w-4" />
            PACER Search
          </Button>
        </Link>
      </div>

      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Credits Management</h1>
        <p className="text-gray-600">
          Manage your credits for purchasing PACER documents and other services
        </p>
      </div>

      {!user && (
        <Card className="mb-6 p-4 bg-yellow-50 border-yellow-200">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div className="text-sm text-yellow-900">
              <p className="font-medium mb-1">Development Mode</p>
              <p className="text-yellow-700">
                You are viewing credits for a test account. In production, you must be logged in to
                manage credits.
              </p>
            </div>
          </div>
        </Card>
      )}

      <CreditsDashboard userId={userId} username={username} />
    </div>
  );
}
