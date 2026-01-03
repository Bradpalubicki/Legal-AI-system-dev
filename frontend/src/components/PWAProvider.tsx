'use client'

import { useEffect, useState, createContext, useContext } from 'react'
import { usePWA } from '../hooks/usePWA'
import { usePushNotifications } from '../hooks/usePushNotifications'
import { useBackgroundSync } from '../hooks/useBackgroundSync'
import InstallPrompt from './pwa/InstallPrompt'
import OfflineIndicator from './pwa/OfflineIndicator'

interface PWAContextType {
  // PWA State
  isInstalled: boolean
  isInstallable: boolean
  isOffline: boolean
  isStandalone: boolean
  
  // Notifications
  notificationsEnabled: boolean
  pendingSyncCount: number
  
  // Actions
  installApp: () => Promise<boolean>
  enableNotifications: () => Promise<void>
  forceSync: () => Promise<void>
}

const PWAContext = createContext<PWAContextType | null>(null)

export function usePWAContext() {
  const context = useContext(PWAContext)
  if (!context) {
    throw new Error('usePWAContext must be used within PWAProvider')
  }
  return context
}

interface PWAProviderProps {
  children: React.ReactNode
  config?: {
    showInstallPrompt?: boolean
    showOfflineIndicator?: boolean
    enableAutoSync?: boolean
    installPromptDelay?: number
  }
}

export default function PWAProvider({ 
  children, 
  config = {
    showInstallPrompt: true,
    showOfflineIndicator: true,
    enableAutoSync: true,
    installPromptDelay: 30000
  }
}: PWAProviderProps) {
  const [isInitialized, setIsInitialized] = useState(false)
  
  // PWA hooks
  const { 
    isInstalled, 
    isInstallable, 
    isOffline, 
    isStandalone,
    install 
  } = usePWA()
  
  const { 
    isSubscribed: notificationsEnabled,
    subscribe: enableNotifications 
  } = usePushNotifications()
  
  const { 
    pendingItems,
    forcSync: forceBackgroundSync 
  } = useBackgroundSync()

  // Initialize PWA features
  useEffect(() => {
    const initializePWA = async () => {
      try {
        // Register service worker if not already registered
        if ('serviceWorker' in navigator) {
          const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/'
          })
          
          console.log('Service Worker registered successfully:', registration.scope)
          
          // Handle service worker updates
          registration.addEventListener('updatefound', () => {
            const newWorker = registration.installing
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  // Show update available notification
                  if (window.confirm('A new version is available. Refresh to update?')) {
                    window.location.reload()
                  }
                }
              })
            }
          })
        }
        
        // Add viewport meta tag for mobile optimization
        const viewport = document.querySelector('meta[name="viewport"]')
        if (!viewport) {
          const meta = document.createElement('meta')
          meta.name = 'viewport'
          meta.content = 'width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes, viewport-fit=cover'
          document.head.appendChild(meta)
        }
        
        // Add theme color meta tag
        const themeColor = document.querySelector('meta[name="theme-color"]')
        if (!themeColor) {
          const meta = document.createElement('meta')
          meta.name = 'theme-color'
          meta.content = '#3b82f6'
          document.head.appendChild(meta)
        }
        
        // Add manifest link
        const manifestLink = document.querySelector('link[rel="manifest"]')
        if (!manifestLink) {
          const link = document.createElement('link')
          link.rel = 'manifest'
          link.href = '/manifest.json'
          document.head.appendChild(link)
        }
        
        // Add iOS specific meta tags
        const appleMobile = document.querySelector('meta[name="apple-mobile-web-app-capable"]')
        if (!appleMobile) {
          const meta = document.createElement('meta')
          meta.name = 'apple-mobile-web-app-capable'
          meta.content = 'yes'
          document.head.appendChild(meta)
        }
        
        const appleStatus = document.querySelector('meta[name="apple-mobile-web-app-status-bar-style"]')
        if (!appleStatus) {
          const meta = document.createElement('meta')
          meta.name = 'apple-mobile-web-app-status-bar-style'
          meta.content = 'default'
          document.head.appendChild(meta)
        }
        
        const appleTitle = document.querySelector('meta[name="apple-mobile-web-app-title"]')
        if (!appleTitle) {
          const meta = document.createElement('meta')
          meta.name = 'apple-mobile-web-app-title'
          meta.content = 'Legal AI'
          document.head.appendChild(meta)
        }
        
        setIsInitialized(true)
      } catch (error) {
        console.error('PWA initialization failed:', error)
        setIsInitialized(true) // Still allow app to function
      }
    }

    initializePWA()
  }, [])

  // Context value
  const contextValue: PWAContextType = {
    isInstalled,
    isInstallable,
    isOffline,
    isStandalone,
    notificationsEnabled,
    pendingSyncCount: pendingItems.length,
    installApp: install,
    enableNotifications,
    forceSync: forceBackgroundSync
  }

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing Legal AI...</p>
        </div>
      </div>
    )
  }

  return (
    <PWAContext.Provider value={contextValue}>
      {children}
      
      {/* PWA UI Components */}
      {config.showInstallPrompt && (
        <InstallPrompt 
          autoShow={true}
          showAfterDelay={config.installPromptDelay}
        />
      )}
      
      {config.showOfflineIndicator && (
        <OfflineIndicator position="top" />
      )}
    </PWAContext.Provider>
  )
}

// Utility function to check if app is running as PWA
export function isPWAMode(): boolean {
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    (window.navigator as any).standalone === true ||
    document.referrer.includes('android-app://') ||
    window.location.search.includes('pwa=true')
  )
}

// Utility function to get PWA install readiness score
export function getPWAReadinessScore(): number {
  let score = 0
  const checks = [
    () => 'serviceWorker' in navigator, // 20 points
    () => 'PushManager' in window, // 15 points
    () => 'BackgroundSync' in window, // 15 points
    () => 'Notification' in window, // 10 points
    () => document.querySelector('link[rel="manifest"]'), // 10 points
    () => document.querySelector('meta[name="theme-color"]'), // 10 points
    () => document.querySelector('meta[name="viewport"]'), // 10 points
    () => location.protocol === 'https:', // 10 points
  ]
  
  const weights = [20, 15, 15, 10, 10, 10, 10, 10]
  
  checks.forEach((check, index) => {
    if (check()) {
      score += weights[index]
    }
  })
  
  return score
}