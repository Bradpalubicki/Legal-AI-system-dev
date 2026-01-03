// PWA Components
export { default as InstallPrompt, ManualInstallPrompt } from './InstallPrompt'
export { default as OfflineIndicator, CompactOfflineIndicator, SyncStatusWidget } from './OfflineIndicator'

// Hooks
export { usePWA } from '../../hooks/usePWA'
export { usePushNotifications, NotificationTemplates } from '../../hooks/usePushNotifications'
export { useBackgroundSync, SyncActions } from '../../hooks/useBackgroundSync'
export { useOfflineStorage } from '../../hooks/useOfflineStorage'

// Types
export interface PWAConfig {
  enableInstallPrompt?: boolean
  enablePushNotifications?: boolean
  enableBackgroundSync?: boolean
  offlineStrategy?: 'cache-first' | 'network-first' | 'stale-while-revalidate'
  syncRetryAttempts?: number
  installPromptDelay?: number
}