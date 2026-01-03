/**
 * MyCasesDashboard Component
 * Dashboard for viewing and managing monitored cases
 */
import React, { useState } from 'react';
import { useRouter } from 'next/router';
import {
  Eye,
  Bell,
  BellOff,
  Calendar,
  FileText,
  Download,
  Settings,
  ExternalLink,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { useMyCases, useCancelCaseAccess, useUpdateNotifications } from '@/hooks/useCaseAccess';
import { useAuth } from '@/hooks/useAuth';

export function MyCasesDashboard() {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();
  const { data: cases, isLoading, error } = useMyCases();
  const cancelAccess = useCancelCaseAccess();
  const updateNotifications = useUpdateNotifications();

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <Card>
        <CardContent className="pt-12 pb-12 text-center">
          <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Login Required</h3>
          <p className="text-gray-600 mb-6">
            Please log in to view your monitored cases.
          </p>
          <Button onClick={() => router.push('/login')}>
            Log In
          </Button>
        </CardContent>
      </Card>
    );
  }

  const handleToggleNotifications = async (caseAccessId: number, currentState: boolean) => {
    try {
      await updateNotifications.mutateAsync({
        caseAccessId,
        enabled: !currentState,
      });
    } catch (err) {
      console.error('Failed to update notifications:', err);
    }
  };

  const handleCancelAccess = async (caseAccessId: number) => {
    if (confirm('Are you sure you want to cancel access to this case?')) {
      try {
        await cancelAccess.mutateAsync(caseAccessId);
      } catch (err) {
        console.error('Failed to cancel access:', err);
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Failed to load cases</h3>
            <p className="text-sm text-red-700 mt-1">
              {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!cases || cases.length === 0) {
    return (
      <Card>
        <CardContent className="pt-12 pb-12 text-center">
          <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Monitored Cases</h3>
          <p className="text-gray-600 mb-6">
            You're not currently monitoring any cases. Start by finding a case and purchasing access.
          </p>
          <Button onClick={() => router.push('/pacer')}>
            Search Cases
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">My Monitored Cases</h2>
          <p className="text-gray-600 mt-1">
            You're monitoring {cases.length} {cases.length === 1 ? 'case' : 'cases'}
          </p>
        </div>
      </div>

      {/* Cases Grid */}
      <div className="grid gap-6">
        {cases.map((caseAccess) => (
          <CaseAccessCard
            key={caseAccess.id}
            caseAccess={caseAccess}
            onToggleNotifications={handleToggleNotifications}
            onCancelAccess={handleCancelAccess}
            onViewCase={() => router.push(`/cases/${caseAccess.case_id}`)}
          />
        ))}
      </div>
    </div>
  );
}

/**
 * Individual case access card
 */
function CaseAccessCard({
  caseAccess,
  onToggleNotifications,
  onCancelAccess,
  onViewCase,
}: {
  caseAccess: any;
  onToggleNotifications: (id: number, current: boolean) => void;
  onCancelAccess: (id: number) => void;
  onViewCase: () => void;
}) {
  const [showSettings, setShowSettings] = useState(false);

  const getAccessTypeBadge = () => {
    switch (caseAccess.access_type) {
      case 'one_time':
        return <Badge className="bg-blue-500">One-Time Access</Badge>;
      case 'monthly':
        return <Badge className="bg-purple-500">Monthly</Badge>;
      case 'subscription':
        return <Badge className="bg-green-500">Subscription</Badge>;
      default:
        return <Badge>{caseAccess.access_type}</Badge>;
    }
  };

  const getExpirationInfo = () => {
    if (!caseAccess.expires_at) {
      return (
        <span className="text-sm text-green-600 font-medium">
          Active until case closes
        </span>
      );
    }

    if (caseAccess.days_remaining !== null) {
      if (caseAccess.days_remaining === 0) {
        return <span className="text-sm text-red-600 font-medium">Expired</span>;
      } else if (caseAccess.days_remaining < 7) {
        return (
          <span className="text-sm text-orange-600 font-medium">
            Expires in {caseAccess.days_remaining} days
          </span>
        );
      } else {
        return (
          <span className="text-sm text-gray-600">
            {caseAccess.days_remaining} days remaining
          </span>
        );
      }
    }

    return null;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <CardTitle className="text-lg">{caseAccess.case_name}</CardTitle>
              {getAccessTypeBadge()}
            </div>
            <CardDescription className="flex items-center gap-4">
              <span>Case No. {caseAccess.case_number}</span>
              {caseAccess.is_active && (
                <Badge variant="outline" className="text-green-600 border-green-600">
                  Active
                </Badge>
              )}
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <FileText className="h-5 w-5 text-gray-600 mx-auto mb-1" />
            <p className="text-sm text-gray-600">Documents</p>
            <p className="font-semibold">--</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Calendar className="h-5 w-5 text-gray-600 mx-auto mb-1" />
            <p className="text-sm text-gray-600">Events</p>
            <p className="font-semibold">--</p>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <Bell className="h-5 w-5 text-gray-600 mx-auto mb-1" />
            <p className="text-sm text-gray-600">Alerts</p>
            <p className="font-semibold">--</p>
          </div>
        </div>

        {/* Access Info */}
        <div className="flex items-center justify-between py-2 border-t">
          <span className="text-sm text-gray-600">Access Status:</span>
          {getExpirationInfo()}
        </div>

        {caseAccess.granted_at && (
          <div className="flex items-center justify-between py-2">
            <span className="text-sm text-gray-600">Monitoring Since:</span>
            <span className="text-sm font-medium">
              {new Date(caseAccess.granted_at).toLocaleDateString()}
            </span>
          </div>
        )}

        {/* Settings Panel */}
        {showSettings && (
          <div className="border-t pt-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {caseAccess.notifications_enabled ? (
                  <Bell className="h-4 w-4 text-gray-600" />
                ) : (
                  <BellOff className="h-4 w-4 text-gray-400" />
                )}
                <span className="text-sm font-medium">Email Notifications</span>
              </div>
              <Switch
                checked={caseAccess.notifications_enabled}
                onCheckedChange={() =>
                  onToggleNotifications(
                    caseAccess.id,
                    caseAccess.notifications_enabled
                  )
                }
              />
            </div>

            <Button
              variant="outline"
              size="sm"
              className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
              onClick={() => onCancelAccess(caseAccess.id)}
            >
              Cancel Access
            </Button>
          </div>
        )}
      </CardContent>

      <CardFooter className="flex gap-2">
        <Button onClick={onViewCase} className="flex-1">
          <Eye className="mr-2 h-4 w-4" />
          View Case
        </Button>
        <Button variant="outline">
          <Download className="mr-2 h-4 w-4" />
          Documents
        </Button>
      </CardFooter>
    </Card>
  );
}

/**
 * Compact widget showing monitored cases count
 */
export function MonitoredCasesWidget() {
  const { isAuthenticated } = useAuth();
  const { data: cases } = useMyCases();
  const router = useRouter();

  // Don't show widget if not authenticated
  if (!isAuthenticated) {
    return null;
  }

  const activeCases = cases?.filter(c => c.is_active) || [];

  return (
    <Card className="cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => router.push('/my-cases')}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Monitored Cases</CardTitle>
          <Eye className="h-5 w-5 text-purple-600" />
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold">{activeCases.length}</p>
        <p className="text-sm text-gray-600 mt-1">Active cases</p>
      </CardContent>
    </Card>
  );
}
