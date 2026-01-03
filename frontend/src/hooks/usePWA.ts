'use client'

import { useState, useEffect, useCallback } from 'react'

interface PWAInstallPrompt {
  prompt(): Promise<{ outcome: 'accepted' | 'dismissed' }>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed', platform: string }>
}

interface PWAState {
  isInstalled: boolean
  isInstallable: boolean
  isOffline: boolean
  isStandalone: boolean
  isSupported: boolean
  needsRefresh: boolean
}

interface PWAActions {
  install: () => Promise<boolean>
  refreshApp: () => void
  showInstallBanner: () => void
  hideInstallBanner: () => void
  clearCache: () => Promise<void>
  getCacheStatus: () => Promise<Record<string, number>>
}

declare global {
  interface WindowEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent
  }
}

export function usePWA(): PWAState & PWAActions {
  const [isInstalled, setIsInstalled] = useState(false)
  const [isInstallable, setIsInstallable] = useState(false)
  const [isOffline, setIsOffline] = useState(false)
  const [isStandalone, setIsStandalone] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [needsRefresh, setNeedsRefresh] = useState(false)
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [serviceWorkerRegistration, setServiceWorkerRegistration] = useState<ServiceWorkerRegistration | null>(null)

  // Check if PWA is supported
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setIsSupported('serviceWorker' in navigator && 'PushManager' in window)
      setIsStandalone(window.matchMedia('(display-mode: standalone)').matches || 
                     (window.navigator as any).standalone === true)
    }
  }, [])

  // Register service worker
  useEffect(() => {
    if (!isSupported) return

    const registerSW = async () => {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/'
        })
        
        setServiceWorkerRegistration(registration)
        
        // Listen for service worker updates
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing
          if (newWorker) {
            newWorker.addEventListener('statechange', () => {
              if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                setNeedsRefresh(true)
              }
            })
          }
        })

        // Check if app is already installed
        if ('getInstalledRelatedApps' in navigator) {
          const relatedApps = await (navigator as any).getInstalledRelatedApps()
          setIsInstalled(relatedApps.length > 0)
        }

      } catch (error) {
        console.error('Service worker registration failed:', error)
      }
    }

    registerSW()
  }, [isSupported])

  // Listen for install prompt
  useEffect(() => {
    const handleBeforeInstallPrompt = (e: BeforeInstallPromptEvent) => {
      e.preventDefault()
      setDeferredPrompt(e)
      setIsInstallable(true)
    }

    const handleAppInstalled = () => {
      setIsInstalled(true)
      setIsInstallable(false)
      setDeferredPrompt(null)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    window.addEventListener('appinstalled', handleAppInstalled)

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
      window.removeEventListener('appinstalled', handleAppInstalled)
    }
  }, [])

  // Monitor online/offline status
  useEffect(() => {
    const updateOnlineStatus = () => {
      setIsOffline(!navigator.onLine)
    }

    updateOnlineStatus()
    window.addEventListener('online', updateOnlineStatus)
    window.addEventListener('offline', updateOnlineStatus)

    return () => {
      window.removeEventListener('online', updateOnlineStatus)
      window.removeEventListener('offline', updateOnlineStatus)
    }
  }, [])

  // Install app
  const install = useCallback(async (): Promise<boolean> => {
    if (!deferredPrompt) return false

    try {
      await deferredPrompt.prompt()
      const choiceResult = await deferredPrompt.userChoice
      
      if (choiceResult.outcome === 'accepted') {
        setIsInstalled(true)
        setIsInstallable(false)
        setDeferredPrompt(null)
        return true
      }
      
      return false
    } catch (error) {
      console.error('Installation failed:', error)
      return false
    }
  }, [deferredPrompt])

  // Refresh app to use new service worker
  const refreshApp = useCallback(() => {
    if (serviceWorkerRegistration?.waiting) {
      serviceWorkerRegistration.waiting.postMessage({ type: 'SKIP_WAITING' })
      window.location.reload()
    }
  }, [serviceWorkerRegistration])

  // Show install banner (for custom UI)
  const showInstallBanner = useCallback(() => {
    if (deferredPrompt) {
      // Custom install banner logic
      const banner = document.createElement('div')
      banner.innerHTML = `
        <div style="
          position: fixed; 
          top: 0; 
          left: 0; 
          right: 0; 
          background: #3b82f6; 
          color: white; 
          padding: 12px 16px; 
          text-align: center;
          z-index: 10000;
        ">
          <span>Install Legal AI for offline access and better performance</span>
          <button onclick="this.parentElement.remove()" style="
            background: none; 
            border: 1px solid white; 
            color: white; 
            padding: 4px 8px; 
            margin-left: 12px;
            cursor: pointer;
          ">Install</button>
          <button onclick="this.parentElement.parentElement.remove()" style="
            background: none; 
            border: none; 
            color: white; 
            padding: 4px 8px; 
            margin-left: 8px;
            cursor: pointer;
          ">×</button>
        </div>
      `
      document.body.appendChild(banner)
    }
  }, [deferredPrompt])

  // Hide install banner
  const hideInstallBanner = useCallback(() => {
    const banner = document.querySelector('[data-pwa-banner]')
    if (banner) {
      banner.remove()
    }
  }, [])

  // Clear all caches
  const clearCache = useCallback(async () => {
    if (serviceWorkerRegistration) {
      const messageChannel = new MessageChannel()
      
      return new Promise<void>((resolve) => {
        messageChannel.port1.onmessage = (event) => {
          if (event.data.type === 'CACHE_CLEARED') {
            resolve()
          }
        }
        
        serviceWorkerRegistration.active?.postMessage(
          { type: 'CLEAR_CACHE' },
          [messageChannel.port2]
        )
      })
    }
  }, [serviceWorkerRegistration])

  // Get cache status
  const getCacheStatus = useCallback(async (): Promise<Record<string, number>> => {
    if (serviceWorkerRegistration) {
      const messageChannel = new MessageChannel()
      
      return new Promise<Record<string, number>>((resolve) => {
        messageChannel.port1.onmessage = (event) => {
          if (event.data.type === 'CACHE_STATUS') {
            resolve(event.data.payload)
          }
        }
        
        serviceWorkerRegistration.active?.postMessage(
          { type: 'GET_CACHE_STATUS' },
          [messageChannel.port2]
        )
      })
    }
    
    return {}
  }, [serviceWorkerRegistration])

  return {
    // State
    isInstalled,
    isInstallable,
    isOffline,
    isStandalone,
    isSupported,
    needsRefresh,
    
    // Actions
    install,
    refreshApp,
    showInstallBanner,
    hideInstallBanner,
    clearCache,
    getCacheStatus
  }
}