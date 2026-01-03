'use client'

import { useState, useEffect, useCallback } from 'react'

interface NotificationOptions {
  title: string
  body: string
  icon?: string
  badge?: string
  image?: string
  tag?: string
  data?: any
  actions?: Array<{
    action: string
    title: string
    icon?: string
  }>
  requireInteraction?: boolean
  silent?: boolean
  vibrate?: number[]
  timestamp?: number
}

interface PushSubscription {
  endpoint: string
  keys: {
    p256dh: string
    auth: string
  }
}

interface PushNotificationHook {
  isSupported: boolean
  permission: NotificationPermission
  isSubscribed: boolean
  subscription: PushSubscription | null
  
  // Actions
  requestPermission: () => Promise<NotificationPermission>
  subscribe: () => Promise<PushSubscription | null>
  unsubscribe: () => Promise<boolean>
  showNotification: (options: NotificationOptions) => Promise<void>
  
  // Utilities
  checkSupport: () => boolean
  getSubscription: () => Promise<PushSubscription | null>
}

export function usePushNotifications(): PushNotificationHook {
  const [isSupported, setIsSupported] = useState(false)
  const [permission, setPermission] = useState<NotificationPermission>('default')
  const [isSubscribed, setIsSubscribed] = useState(false)
  const [subscription, setSubscription] = useState<PushSubscription | null>(null)
  const [serviceWorkerRegistration, setServiceWorkerRegistration] = useState<ServiceWorkerRegistration | null>(null)

  // VAPID public key (in production, this should come from your server)
  const VAPID_PUBLIC_KEY = 'BEl62iUYgUivxIkv69yViEuiBIa40HI8YD4j4pFsRRZz7wJaFhJaW2BW2k8HJ7J8wM5QjV1vMN8YfZqj9sHpRtM'

  // Check if push notifications are supported
  const checkSupport = useCallback(() => {
    const supported = 'serviceWorker' in navigator && 
                     'PushManager' in window && 
                     'Notification' in window
    setIsSupported(supported)
    return supported
  }, [])

  // Initialize push notifications
  useEffect(() => {
    const initialize = async () => {
      if (!checkSupport()) return

      try {
        // Get service worker registration
        const registration = await navigator.serviceWorker.ready
        setServiceWorkerRegistration(registration)

        // Check current permission
        setPermission(Notification.permission)

        // Check existing subscription
        const existingSubscription = await registration.pushManager.getSubscription()
        if (existingSubscription) {
          const subscriptionData = {
            endpoint: existingSubscription.endpoint,
            keys: {
              p256dh: arrayBufferToBase64(existingSubscription.getKey('p256dh')!),
              auth: arrayBufferToBase64(existingSubscription.getKey('auth')!)
            }
          }
          setSubscription(subscriptionData)
          setIsSubscribed(true)
        }
      } catch (error) {
        console.error('Push notification initialization failed:', error)
      }
    }

    initialize()
  }, [checkSupport])

  // Request notification permission
  const requestPermission = useCallback(async (): Promise<NotificationPermission> => {
    if (!isSupported) {
      throw new Error('Push notifications are not supported')
    }

    try {
      const result = await Notification.requestPermission()
      setPermission(result)
      return result
    } catch (error) {
      console.error('Permission request failed:', error)
      throw error
    }
  }, [isSupported])

  // Subscribe to push notifications
  const subscribe = useCallback(async (): Promise<PushSubscription | null> => {
    if (!serviceWorkerRegistration) {
      throw new Error('Service worker not available')
    }

    if (permission !== 'granted') {
      const newPermission = await requestPermission()
      if (newPermission !== 'granted') {
        throw new Error('Push notifications permission denied')
      }
    }

    try {
      const pushSubscription = await serviceWorkerRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
      })

      const subscriptionData: PushSubscription = {
        endpoint: pushSubscription.endpoint,
        keys: {
          p256dh: arrayBufferToBase64(pushSubscription.getKey('p256dh')!),
          auth: arrayBufferToBase64(pushSubscription.getKey('auth')!)
        }
      }

      setSubscription(subscriptionData)
      setIsSubscribed(true)

      // Send subscription to server
      await sendSubscriptionToServer(subscriptionData)

      return subscriptionData
    } catch (error) {
      console.error('Subscription failed:', error)
      throw error
    }
  }, [serviceWorkerRegistration, permission, requestPermission])

  // Unsubscribe from push notifications
  const unsubscribe = useCallback(async (): Promise<boolean> => {
    if (!serviceWorkerRegistration) {
      return false
    }

    try {
      const pushSubscription = await serviceWorkerRegistration.pushManager.getSubscription()
      if (pushSubscription) {
        const success = await pushSubscription.unsubscribe()
        
        if (success) {
          setSubscription(null)
          setIsSubscribed(false)
          
          // Remove subscription from server
          if (subscription) {
            await removeSubscriptionFromServer(subscription)
          }
        }
        
        return success
      }
      
      return true
    } catch (error) {
      console.error('Unsubscribe failed:', error)
      return false
    }
  }, [serviceWorkerRegistration, subscription])

  // Show local notification
  const showNotification = useCallback(async (options: NotificationOptions): Promise<void> => {
    if (!serviceWorkerRegistration) {
      throw new Error('Service worker not available')
    }

    if (permission !== 'granted') {
      throw new Error('Notification permission not granted')
    }

    try {
      await serviceWorkerRegistration.showNotification(options.title, {
        body: options.body,
        icon: options.icon || '/icons/icon-192x192.png',
        badge: options.badge || '/icons/icon-72x72.png',
        image: options.image,
        tag: options.tag,
        data: options.data,
        actions: options.actions,
        requireInteraction: options.requireInteraction || false,
        silent: options.silent || false,
        vibrate: options.vibrate || [200, 100, 200],
        timestamp: options.timestamp || Date.now()
      })
    } catch (error) {
      console.error('Show notification failed:', error)
      throw error
    }
  }, [serviceWorkerRegistration, permission])

  // Get current subscription
  const getSubscription = useCallback(async (): Promise<PushSubscription | null> => {
    if (!serviceWorkerRegistration) {
      return null
    }

    try {
      const pushSubscription = await serviceWorkerRegistration.pushManager.getSubscription()
      if (pushSubscription) {
        return {
          endpoint: pushSubscription.endpoint,
          keys: {
            p256dh: arrayBufferToBase64(pushSubscription.getKey('p256dh')!),
            auth: arrayBufferToBase64(pushSubscription.getKey('auth')!)
          }
        }
      }
      return null
    } catch (error) {
      console.error('Get subscription failed:', error)
      return null
    }
  }, [serviceWorkerRegistration])

  return {
    isSupported,
    permission,
    isSubscribed,
    subscription,
    requestPermission,
    subscribe,
    unsubscribe,
    showNotification,
    checkSupport,
    getSubscription
  }
}

// Utility functions
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - base64String.length % 4) % 4)
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/')

  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer)
  let binary = ''
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i])
  }
  return window.btoa(binary)
}

async function sendSubscriptionToServer(subscription: PushSubscription): Promise<void> {
  try {
    const response = await fetch('/api/notifications/subscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(subscription)
    })

    if (!response.ok) {
      throw new Error('Failed to send subscription to server')
    }
  } catch (error) {
    console.error('Failed to send subscription to server:', error)
    // Don't throw here as the subscription still works locally
  }
}

async function removeSubscriptionFromServer(subscription: PushSubscription): Promise<void> {
  try {
    const response = await fetch('/api/notifications/unsubscribe', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ endpoint: subscription.endpoint })
    })

    if (!response.ok) {
      throw new Error('Failed to remove subscription from server')
    }
  } catch (error) {
    console.error('Failed to remove subscription from server:', error)
    // Don't throw here as the local unsubscription was successful
  }
}

// Predefined notification templates for legal use cases
export const NotificationTemplates = {
  documentReady: (documentTitle: string): NotificationOptions => ({
    title: 'Document Analysis Complete',
    body: `Analysis for "${documentTitle}" is ready for review`,
    icon: '/icons/document-icon.png',
    tag: 'document-ready',
    actions: [
      { action: 'view', title: 'View Document', icon: '/icons/view-icon.png' },
      { action: 'dismiss', title: 'Dismiss' }
    ],
    requireInteraction: true,
    vibrate: [200, 100, 200]
  }),

  caseUpdate: (caseTitle: string, status: string): NotificationOptions => ({
    title: 'Case Status Update',
    body: `${caseTitle} status changed to: ${status}`,
    icon: '/icons/case-icon.png',
    tag: 'case-update',
    actions: [
      { action: 'view', title: 'View Case', icon: '/icons/view-icon.png' },
      { action: 'dismiss', title: 'Dismiss' }
    ],
    requireInteraction: false,
    vibrate: [100, 50, 100]
  }),

  deadlineReminder: (task: string, timeLeft: string): NotificationOptions => ({
    title: 'Deadline Reminder',
    body: `${task} is due in ${timeLeft}`,
    icon: '/icons/deadline-icon.png',
    tag: 'deadline-reminder',
    actions: [
      { action: 'view', title: 'View Task', icon: '/icons/view-icon.png' },
      { action: 'snooze', title: 'Snooze 1h', icon: '/icons/snooze-icon.png' },
      { action: 'dismiss', title: 'Dismiss' }
    ],
    requireInteraction: true,
    vibrate: [300, 100, 300, 100, 300]
  }),

  researchComplete: (query: string, resultsCount: number): NotificationOptions => ({
    title: 'Research Complete',
    body: `Found ${resultsCount} results for "${query}"`,
    icon: '/icons/research-icon.png',
    tag: 'research-complete',
    actions: [
      { action: 'view', title: 'View Results', icon: '/icons/view-icon.png' },
      { action: 'dismiss', title: 'Dismiss' }
    ],
    requireInteraction: false,
    vibrate: [200, 100, 200]
  }),

  collaborationUpdate: (documentTitle: string, collaborator: string): NotificationOptions => ({
    title: 'New Collaboration Activity',
    body: `${collaborator} commented on "${documentTitle}"`,
    icon: '/icons/collaboration-icon.png',
    tag: 'collaboration-update',
    actions: [
      { action: 'view', title: 'View Comment', icon: '/icons/view-icon.png' },
      { action: 'dismiss', title: 'Dismiss' }
    ],
    requireInteraction: false,
    vibrate: [100, 50, 100]
  })
}