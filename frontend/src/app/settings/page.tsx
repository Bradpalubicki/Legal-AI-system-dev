'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/providers/ThemeProvider';
import { useUserPreferences } from '@/hooks/useUserPreferences';
import { toast } from 'sonner';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Button,
  Input,
  Alert,
} from '@/components/design-system';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Home,
  User,
  Bell,
  Shield,
  Palette,
  Key,
  Save,
  Settings,
  Check,
  Loader2,
  FileText,
  CreditCard,
  TrendingUp,
  FileStack,
  Eye,
} from 'lucide-react';
import { useUserTier, useFeatureUsage } from '@/hooks/useFeatureAccess';

// Simple toggle switch component with full accessibility support
const Toggle = ({
  checked,
  onChange,
  id,
  label
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  id?: string;
  label?: string;
}) => (
  <button
    id={id}
    type="button"
    role="switch"
    aria-checked={checked}
    aria-label={label || (checked ? 'Enabled' : 'Disabled')}
    onClick={() => onChange(!checked)}
    onKeyDown={(e) => {
      // Allow toggling with Space or Enter key
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        onChange(!checked);
      }
    }}
    className={`
      relative inline-flex h-6 w-11 items-center rounded-full transition-colors
      focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2
      ${checked ? 'bg-teal-600' : 'bg-slate-200 dark:bg-slate-600'}
    `}
  >
    <span
      className={`
        inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm
        ${checked ? 'translate-x-6' : 'translate-x-1'}
      `}
    />
  </button>
);

export default function SettingsPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();
  const { darkMode, setDarkMode } = useTheme();
  const {
    preferences,
    loading: prefsLoading,
    saving: prefsSaving,
    updatePreference,
    updatePreferences
  } = useUserPreferences();
  const [saving, setSaving] = useState(false);

  // Subscription data
  const { data: tierInfo, isLoading: tierLoading } = useUserTier();
  const { data: creditsUsage, isLoading: creditsLoading } = useFeatureUsage('document_credits');
  const { data: monitoringUsage, isLoading: monitoringLoading } = useFeatureUsage('case_monitoring');

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login?redirect=/settings');
    }
  }, [isLoading, isAuthenticated, router]);

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
          <p className="text-slate-500">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render if not authenticated (will redirect)
  if (!isAuthenticated) {
    return null;
  }

  // Handle notification toggle changes
  const handleToggleChange = async (key: keyof typeof preferences, value: boolean) => {
    const success = await updatePreference(key, value);
    if (success) {
      toast.success('Preference saved', { duration: 2000 });
    } else {
      toast.error('Failed to save preference');
    }
  };

  const handleSave = async () => {
    setSaving(true);
    // Simulate save for profile fields (TODO: implement profile update)
    await new Promise(resolve => setTimeout(resolve, 1000));
    setSaving(false);
    toast.success('Profile updated');
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="max-w-content mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-navy-800 dark:text-slate-100 flex items-center gap-3">
                <div className="p-2 bg-teal-50 dark:bg-slate-700 rounded-lg">
                  <Settings className="w-6 h-6 text-teal-600 dark:text-teal-400" />
                </div>
                Settings
              </h1>
              <p className="text-slate-500 dark:text-slate-400 mt-2">
                Manage your account settings and preferences
              </p>
            </div>
            <Link href="/">
              <Button variant="outline" leftIcon={<Home className="w-4 h-4" />}>
                Home
              </Button>
            </Link>
          </div>
        </div>

        {!user && (
          <Alert variant="warning" title="Not Logged In" className="mb-6">
            Please <Link href="/auth/login" className="underline font-medium">log in</Link> to access all settings.
          </Alert>
        )}

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 bg-white dark:bg-slate-800 rounded-lg p-1 shadow-sm border border-slate-200 dark:border-slate-700">
            <TabsTrigger value="profile" className="flex items-center gap-2 data-[state=active]:bg-navy-50 dark:data-[state=active]:bg-slate-700 data-[state=active]:text-navy-800 dark:data-[state=active]:text-slate-100 dark:text-slate-400 rounded-md transition-colors">
              <User className="h-4 w-4" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="notifications" className="flex items-center gap-2 data-[state=active]:bg-navy-50 dark:data-[state=active]:bg-slate-700 data-[state=active]:text-navy-800 dark:data-[state=active]:text-slate-100 dark:text-slate-400 rounded-md transition-colors">
              <Bell className="h-4 w-4" />
              Notifications
            </TabsTrigger>
            <TabsTrigger value="security" className="flex items-center gap-2 data-[state=active]:bg-navy-50 dark:data-[state=active]:bg-slate-700 data-[state=active]:text-navy-800 dark:data-[state=active]:text-slate-100 dark:text-slate-400 rounded-md transition-colors">
              <Shield className="h-4 w-4" />
              Security
            </TabsTrigger>
            <TabsTrigger value="appearance" className="flex items-center gap-2 data-[state=active]:bg-navy-50 dark:data-[state=active]:bg-slate-700 data-[state=active]:text-navy-800 dark:data-[state=active]:text-slate-100 dark:text-slate-400 rounded-md transition-colors">
              <Palette className="h-4 w-4" />
              Appearance
            </TabsTrigger>
            <TabsTrigger value="subscription" className="flex items-center gap-2 data-[state=active]:bg-navy-50 dark:data-[state=active]:bg-slate-700 data-[state=active]:text-navy-800 dark:data-[state=active]:text-slate-100 dark:text-slate-400 rounded-md transition-colors">
              <CreditCard className="h-4 w-4" />
              Subscription
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle icon={<User className="w-5 h-5" />}>
                  Profile Information
                </CardTitle>
                <CardDescription>
                  Update your account profile information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="First Name"
                    id="firstName"
                    defaultValue={user?.full_name?.split(' ')[0] || ''}
                    placeholder="Enter first name"
                  />
                  <Input
                    label="Last Name"
                    id="lastName"
                    defaultValue={user?.full_name?.split(' ')[1] || ''}
                    placeholder="Enter last name"
                  />
                </div>
                <Input
                  label="Email"
                  id="email"
                  type="email"
                  defaultValue={user?.email || ''}
                  placeholder="Enter email"
                />
                <Input
                  label="Phone Number"
                  id="phone"
                  type="tel"
                  placeholder="Enter phone number"
                />
                <Button
                  onClick={handleSave}
                  disabled={saving}
                  isLoading={saving}
                  leftIcon={!saving ? <Save className="w-4 h-4" /> : undefined}
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Notifications Tab */}
          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle icon={<Bell className="w-5 h-5" />}>
                  Notification Preferences
                </CardTitle>
                <CardDescription>
                  Choose how you want to be notified
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {prefsLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
                    <span className="ml-2 text-slate-500">Loading preferences...</span>
                  </div>
                ) : (
                  <>
                    {/* New Filing Notifications on Login - NEW */}
                    <div className="flex items-center justify-between p-4 bg-teal-50 dark:bg-teal-900/30 rounded-lg border-2 border-teal-200 dark:border-teal-700">
                      <div className="space-y-0.5">
                        <p className="font-medium text-navy-800 dark:text-slate-100 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-teal-600 dark:text-teal-400" />
                          New Filing Notifications on Login
                        </p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          Show a popup with new court filings when you log in
                        </p>
                      </div>
                      <Toggle
                        checked={preferences.show_new_filing_notifications}
                        onChange={(value) => handleToggleChange('show_new_filing_notifications', value)}
                        label="Toggle new filing notifications on login"
                      />
                    </div>

                    <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                      <div className="space-y-0.5">
                        <p className="font-medium text-navy-800 dark:text-slate-100">Email Notifications</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">Receive email updates about your account</p>
                      </div>
                      <Toggle
                        checked={preferences.email_notifications}
                        onChange={(value) => handleToggleChange('email_notifications', value)}
                        label="Toggle email notifications"
                      />
                    </div>
                    <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                      <div className="space-y-0.5">
                        <p className="font-medium text-navy-800 dark:text-slate-100">Case Alerts</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">Get notified when there are updates to your cases</p>
                      </div>
                      <Toggle
                        checked={preferences.case_alerts}
                        onChange={(value) => handleToggleChange('case_alerts', value)}
                        label="Toggle case alerts"
                      />
                    </div>
                    <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                      <div className="space-y-0.5">
                        <p className="font-medium text-navy-800 dark:text-slate-100">Document Alerts</p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">Get notified when new documents are available</p>
                      </div>
                      <Toggle
                        checked={preferences.document_alerts}
                        onChange={(value) => handleToggleChange('document_alerts', value)}
                        label="Toggle document alerts"
                      />
                    </div>

                    {prefsSaving && (
                      <div className="flex items-center gap-2 text-sm text-teal-600">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Saving...
                      </div>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security">
            <Card>
              <CardHeader>
                <CardTitle icon={<Shield className="w-5 h-5" />}>
                  Security Settings
                </CardTitle>
                <CardDescription>
                  Manage your password and security options
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <h3 className="font-medium text-navy-800 flex items-center gap-2">
                    <Key className="h-4 w-4 text-teal-600" />
                    Change Password
                  </h3>
                  <Input
                    label="Current Password"
                    id="currentPassword"
                    type="password"
                    placeholder="Enter current password"
                  />
                  <Input
                    label="New Password"
                    id="newPassword"
                    type="password"
                    placeholder="Enter new password"
                  />
                  <Input
                    label="Confirm New Password"
                    id="confirmPassword"
                    type="password"
                    placeholder="Confirm new password"
                  />
                  <Button variant="outline" leftIcon={<Key className="w-4 h-4" />}>
                    Update Password
                  </Button>
                </div>
                <hr className="border-slate-200" />
                <div className="space-y-4">
                  <h3 className="font-medium text-navy-800 flex items-center gap-2">
                    <Shield className="h-4 w-4 text-teal-600" />
                    Two-Factor Authentication
                  </h3>
                  <p className="text-sm text-slate-500">
                    Add an extra layer of security to your account by enabling two-factor authentication.
                  </p>
                  <Button variant="outline">Enable 2FA</Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Appearance Tab */}
          <TabsContent value="appearance">
            <Card>
              <CardHeader>
                <CardTitle icon={<Palette className="w-5 h-5" />}>
                  Appearance
                </CardTitle>
                <CardDescription>
                  Customize how the application looks
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                  <div className="space-y-0.5">
                    <p className="font-medium text-navy-800 dark:text-slate-100">Dark Mode</p>
                    <p className="text-sm text-slate-500 dark:text-slate-400">Use dark theme across the application</p>
                  </div>
                  <Toggle
                    checked={darkMode}
                    onChange={setDarkMode}
                    label="Toggle dark mode"
                  />
                </div>
                <Alert variant="info" title="Coming Soon">
                  More appearance options will be available in future updates.
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Subscription Tab */}
          <TabsContent value="subscription">
            <div className="space-y-6">
              {/* Current Plan Card */}
              <Card>
                <CardHeader>
                  <CardTitle icon={<CreditCard className="w-5 h-5" />}>
                    Current Plan
                  </CardTitle>
                  <CardDescription>
                    Your subscription details and usage
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {tierLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <Loader2 className="w-6 h-6 animate-spin text-teal-600" />
                      <span className="ml-2 text-slate-500">Loading subscription...</span>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {/* Plan Name */}
                      <div className="p-4 bg-gradient-to-r from-teal-50 to-blue-50 dark:from-teal-900/30 dark:to-blue-900/30 rounded-lg border border-teal-200 dark:border-teal-700">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-sm text-slate-500 dark:text-slate-400">Current Plan</p>
                            <p className="text-2xl font-bold text-navy-800 dark:text-slate-100 capitalize">
                              {tierInfo?.tier_name || tierInfo?.tier || 'Free'}
                            </p>
                          </div>
                          <div className="p-3 bg-teal-100 dark:bg-teal-800 rounded-full">
                            <TrendingUp className="w-6 h-6 text-teal-600 dark:text-teal-300" />
                          </div>
                        </div>
                      </div>

                      {/* Usage Stats Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Document Credits */}
                        <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                          <div className="flex items-center gap-2 mb-3">
                            <FileStack className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                            <p className="font-medium text-navy-800 dark:text-slate-100">Document Credits</p>
                          </div>
                          {creditsLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                          ) : (
                            <>
                              <div className="flex items-baseline gap-1 mb-2">
                                <span className="text-3xl font-bold text-navy-800 dark:text-slate-100">
                                  {creditsUsage?.remaining ?? creditsUsage?.limit ?? tierInfo?.limits?.document_credits ?? 0}
                                </span>
                                <span className="text-slate-500 dark:text-slate-400">
                                  / {creditsUsage?.limit ?? tierInfo?.limits?.document_credits ?? 0} remaining
                                </span>
                              </div>
                              <div className="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2">
                                <div
                                  className="bg-blue-600 h-2 rounded-full transition-all"
                                  style={{
                                    width: `${Math.max(0, Math.min(100,
                                      ((creditsUsage?.remaining ?? creditsUsage?.limit ?? 0) /
                                       (creditsUsage?.limit ?? tierInfo?.limits?.document_credits ?? 1)) * 100
                                    ))}%`
                                  }}
                                />
                              </div>
                              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                                {creditsUsage?.used ?? 0} credits used this month
                              </p>
                            </>
                          )}
                        </div>

                        {/* Case Monitoring */}
                        <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                          <div className="flex items-center gap-2 mb-3">
                            <Eye className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                            <p className="font-medium text-navy-800 dark:text-slate-100">Case Monitoring</p>
                          </div>
                          {monitoringLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin text-slate-400" />
                          ) : (
                            <>
                              <div className="flex items-baseline gap-1 mb-2">
                                <span className="text-3xl font-bold text-navy-800 dark:text-slate-100">
                                  {monitoringUsage?.used ?? 0}
                                </span>
                                <span className="text-slate-500 dark:text-slate-400">
                                  / {monitoringUsage?.limit ?? tierInfo?.limits?.case_monitoring ?? 1} slots used
                                </span>
                              </div>
                              <div className="w-full bg-slate-200 dark:bg-slate-600 rounded-full h-2">
                                <div
                                  className="bg-purple-600 h-2 rounded-full transition-all"
                                  style={{
                                    width: `${Math.max(0, Math.min(100,
                                      ((monitoringUsage?.used ?? 0) /
                                       (monitoringUsage?.limit ?? tierInfo?.limits?.case_monitoring ?? 1)) * 100
                                    ))}%`
                                  }}
                                />
                              </div>
                              <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                                Active case monitors
                              </p>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Upgrade CTA */}
                      <div className="p-4 bg-gradient-to-r from-navy-50 to-teal-50 dark:from-navy-900/30 dark:to-teal-900/30 rounded-lg border border-navy-200 dark:border-navy-700">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-navy-800 dark:text-slate-100">Need more credits or monitoring slots?</p>
                            <p className="text-sm text-slate-500 dark:text-slate-400">
                              Upgrade your plan to unlock additional features and higher limits.
                            </p>
                          </div>
                          <Link href="/pricing">
                            <Button leftIcon={<TrendingUp className="w-4 h-4" />}>
                              Upgrade Plan
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Plan Features Card */}
              <Card>
                <CardHeader>
                  <CardTitle icon={<Check className="w-5 h-5" />}>
                    Plan Features
                  </CardTitle>
                  <CardDescription>
                    Features included in your current plan
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {tierLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <Loader2 className="w-5 h-5 animate-spin text-teal-600" />
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {tierInfo?.features?.map((feature, index) => (
                        <div key={index} className="flex items-center gap-2 p-2">
                          <Check className="w-4 h-4 text-teal-600 dark:text-teal-400 flex-shrink-0" />
                          <span className="text-sm text-slate-700 dark:text-slate-300">
                            {feature.description || feature.feature}
                            {feature.limit && feature.limit > 0 && (
                              <span className="ml-1 text-slate-500">({feature.limit})</span>
                            )}
                          </span>
                        </div>
                      )) || (
                        <>
                          <div className="flex items-center gap-2 p-2">
                            <Check className="w-4 h-4 text-teal-600 flex-shrink-0" />
                            <span className="text-sm text-slate-700 dark:text-slate-300">Unlimited case search</span>
                          </div>
                          <div className="flex items-center gap-2 p-2">
                            <Check className="w-4 h-4 text-teal-600 flex-shrink-0" />
                            <span className="text-sm text-slate-700 dark:text-slate-300">Document preview</span>
                          </div>
                          <div className="flex items-center gap-2 p-2">
                            <Check className="w-4 h-4 text-teal-600 flex-shrink-0" />
                            <span className="text-sm text-slate-700 dark:text-slate-300">Basic court information</span>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
