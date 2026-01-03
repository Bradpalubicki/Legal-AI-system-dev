const CACHE_NAME = 'legal-ai-v1.0.0'
const OFFLINE_URL = '/offline'
const FALLBACK_IMAGE = '/icons/icon-192x192.png'

// Cache strategies
const CACHE_STRATEGIES = {
  CACHE_FIRST: 'cache-first',
  NETWORK_FIRST: 'network-first',
  STALE_WHILE_REVALIDATE: 'stale-while-revalidate',
  NETWORK_ONLY: 'network-only',
  CACHE_ONLY: 'cache-only'
}

// Routes configuration
const ROUTES_CONFIG = [
  {
    pattern: /\.(js|css|woff2?|ttf|eot)$/,
    strategy: CACHE_STRATEGIES.CACHE_FIRST,
    cacheName: 'static-assets',
    maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
    maxEntries: 100
  },
  {
    pattern: /\.(png|jpg|jpeg|gif|svg|webp|ico)$/,
    strategy: CACHE_STRATEGIES.CACHE_FIRST,
    cacheName: 'images',
    maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
    maxEntries: 200
  },
  {
    pattern: /^https:\/\/api\.legal-ai\.com\/documents\//,
    strategy: CACHE_STRATEGIES.NETWORK_FIRST,
    cacheName: 'documents-api',
    maxAgeSeconds: 24 * 60 * 60, // 1 day
    maxEntries: 50
  },
  {
    pattern: /^https:\/\/api\.legal-ai\.com\/search/,
    strategy: CACHE_STRATEGIES.NETWORK_FIRST,
    cacheName: 'search-api',
    maxAgeSeconds: 60 * 60, // 1 hour
    maxEntries: 100
  },
  {
    pattern: /^https:\/\/api\.legal-ai\.com\/analytics/,
    strategy: CACHE_STRATEGIES.STALE_WHILE_REVALIDATE,
    cacheName: 'analytics-api',
    maxAgeSeconds: 15 * 60, // 15 minutes
    maxEntries: 50
  }
]

// Essential resources to cache immediately
const ESSENTIAL_RESOURCES = [
  '/',
  '/mobile',
  '/offline',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
]

// Mobile-specific educational content cache
const EDUCATION_CACHE = 'legal-education-v1'

// Sensitive patterns that should NEVER be cached (mobile compliance)
const SENSITIVE_PATTERNS = [
  /\/api\/documents\/.*\/privileged/,
  /\/api\/client\/.*\/confidential/,
  /\/api\/cases\/.*\/attorney-client/,
  /authentication/,
  /login/,
  /oauth/,
  /attorney-client/,
  /work-product/
]

// Background sync queue
let syncQueue = []

// Install event - cache essential resources
self.addEventListener('install', (event) => {
  console.log('Service Worker installing...')
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Caching essential resources')
        return cache.addAll(ESSENTIAL_RESOURCES)
      })
      .then(() => {
        // Skip waiting to activate immediately
        return self.skipWaiting()
      })
  )
})

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...')
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((cacheName) => {
              return cacheName.startsWith('legal-ai-') && cacheName !== CACHE_NAME
            })
            .map((cacheName) => {
              console.log('Deleting old cache:', cacheName)
              return caches.delete(cacheName)
            })
        )
      })
      .then(() => {
        // Take control of all pages
        return self.clients.claim()
      })
  )
})

// Fetch event - handle network requests
self.addEventListener('fetch', (event) => {
  const { request } = event
  const url = new URL(request.url)

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return
  }

  // Skip Chrome extension requests
  if (url.protocol === 'chrome-extension:') {
    return
  }

  // CRITICAL: Never cache sensitive/privileged content (mobile compliance)
  if (SENSITIVE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    console.warn('Skipping cache for sensitive URL:', url.pathname)
    return // Always go to network
  }

  // Handle mobile educational content
  if (url.pathname.includes('/mobile/education') || url.pathname.includes('/education-content')) {
    event.respondWith(handleEducationalContent(request))
    return
  }

  // Find matching route configuration
  const routeConfig = ROUTES_CONFIG.find(config => config.pattern.test(request.url))
  
  if (routeConfig) {
    event.respondWith(handleCacheStrategy(request, routeConfig))
  } else {
    // Default strategy for navigation requests
    if (request.mode === 'navigate') {
      event.respondWith(handleNavigation(request))
    } else {
      event.respondWith(handleDefault(request))
    }
  }
})

// Cache strategies implementation
async function handleCacheStrategy(request, config) {
  const { strategy, cacheName, maxAgeSeconds, maxEntries } = config
  const cache = await caches.open(cacheName || CACHE_NAME)

  switch (strategy) {
    case CACHE_STRATEGIES.CACHE_FIRST:
      return handleCacheFirst(request, cache, maxAgeSeconds)
    
    case CACHE_STRATEGIES.NETWORK_FIRST:
      return handleNetworkFirst(request, cache, maxAgeSeconds)
    
    case CACHE_STRATEGIES.STALE_WHILE_REVALIDATE:
      return handleStaleWhileRevalidate(request, cache, maxAgeSeconds)
    
    case CACHE_STRATEGIES.NETWORK_ONLY:
      return fetch(request)
    
    case CACHE_STRATEGIES.CACHE_ONLY:
      return cache.match(request)
    
    default:
      return handleNetworkFirst(request, cache, maxAgeSeconds)
  }
}

async function handleCacheFirst(request, cache, maxAgeSeconds) {
  const cachedResponse = await cache.match(request)
  
  if (cachedResponse && !isExpired(cachedResponse, maxAgeSeconds)) {
    return cachedResponse
  }
  
  try {
    const networkResponse = await fetch(request)
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone())
    }
    return networkResponse
  } catch (error) {
    return cachedResponse || createErrorResponse()
  }
}

async function handleNetworkFirst(request, cache, maxAgeSeconds) {
  try {
    const networkResponse = await fetch(request)
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone())
    }
    return networkResponse
  } catch (error) {
    const cachedResponse = await cache.match(request)
    if (cachedResponse && !isExpired(cachedResponse, maxAgeSeconds)) {
      return cachedResponse
    }
    return createErrorResponse()
  }
}

async function handleStaleWhileRevalidate(request, cache, maxAgeSeconds) {
  const cachedResponse = await cache.match(request)
  
  const fetchPromise = fetch(request)
    .then((networkResponse) => {
      if (networkResponse.ok) {
        cache.put(request, networkResponse.clone())
      }
      return networkResponse
    })
    .catch(() => null)
  
  if (cachedResponse) {
    // Return cached response immediately, update in background
    fetchPromise.catch(() => {}) // Prevent unhandled promise rejection
    return cachedResponse
  }
  
  // No cached response, wait for network
  try {
    return await fetchPromise
  } catch (error) {
    return createErrorResponse()
  }
}

async function handleNavigation(request) {
  try {
    // Try network first for navigation
    const networkResponse = await fetch(request)
    
    // Cache successful navigation responses
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME)
      cache.put(request, networkResponse.clone())
    }
    
    return networkResponse
  } catch (error) {
    // Return cached page or offline page
    const cache = await caches.open(CACHE_NAME)
    const cachedResponse = await cache.match(request)
    
    if (cachedResponse) {
      return cachedResponse
    }
    
    // Return offline page
    return cache.match(OFFLINE_URL) || createOfflineResponse()
  }
}

async function handleDefault(request) {
  try {
    return await fetch(request)
  } catch (error) {
    const cache = await caches.open(CACHE_NAME)
    const cachedResponse = await cache.match(request)
    
    if (cachedResponse) {
      return cachedResponse
    }
    
    // Return fallback for images
    if (request.destination === 'image') {
      return cache.match(FALLBACK_IMAGE)
    }
    
    return createErrorResponse()
  }
}

// Handle educational content (network first, with offline fallback)
async function handleEducationalContent(request) {
  try {
    // Try network first for fresh content
    const networkResponse = await fetch(request)
    
    if (networkResponse.ok) {
      const cache = await caches.open(EDUCATION_CACHE)
      
      // Only cache public educational content (compliance check)
      const clonedResponse = networkResponse.clone()
      const contentType = clonedResponse.headers.get('content-type')
      
      if (contentType && contentType.includes('json')) {
        try {
          const data = await clonedResponse.json()
          
          // Check if content is safe to cache (no privileged information)
          if (isSafeToCache(data)) {
            cache.put(request, networkResponse.clone())
          } else {
            console.warn('Refusing to cache potentially sensitive educational content')
          }
        } catch (jsonError) {
          // If not JSON, cache as-is (likely safe static content)
          cache.put(request, networkResponse.clone())
        }
      }
      
      return networkResponse
    }
  } catch (error) {
    console.warn('Network failed for educational content, trying cache:', error)
  }

  // Fallback to cache
  const cache = await caches.open(EDUCATION_CACHE)
  const cachedResponse = await cache.match(request)
  if (cachedResponse) {
    // Add offline indicator header
    const headers = new Headers(cachedResponse.headers)
    headers.set('X-Served-From', 'cache')
    headers.set('X-Cache-Date', new Date().toISOString())
    
    return new Response(cachedResponse.body, {
      status: cachedResponse.status,
      statusText: cachedResponse.statusText,
      headers
    })
  }

  // Return offline educational content message
  return new Response(
    JSON.stringify({
      error: 'Content unavailable offline',
      message: 'This educational content requires an internet connection.',
      offline: true,
      disclaimer: 'Educational content cached locally may be outdated. Verify current legal standards when online.'
    }),
    {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    }
  )
}

function isSafeToCache(data) {
  // Check for sensitive content indicators in mobile educational content
  const sensitiveKeys = [
    'privileged',
    'confidential',
    'attorney-client',
    'work-product',
    'client-info',
    'case-sensitive',
    'attorney_client',
    'work_product'
  ]
  
  const jsonString = JSON.stringify(data).toLowerCase()
  return !sensitiveKeys.some(key => jsonString.includes(key))
}

function isExpired(response, maxAgeSeconds) {
  if (!maxAgeSeconds) return false
  
  const dateHeader = response.headers.get('date')
  if (!dateHeader) return false
  
  const responseDate = new Date(dateHeader).getTime()
  const now = Date.now()
  const maxAge = maxAgeSeconds * 1000
  
  return (now - responseDate) > maxAge
}

function createErrorResponse() {
  return new Response('Network error', {
    status: 408,
    statusText: 'Request Timeout',
    headers: { 'Content-Type': 'text/plain' }
  })
}

function createOfflineResponse() {
  return new Response(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Legal AI - Offline</title>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <style>
        body { 
          font-family: system-ui, sans-serif; 
          text-align: center; 
          padding: 2rem; 
          background: #f8fafc; 
        }
        .container { 
          max-width: 400px; 
          margin: 0 auto; 
          background: white; 
          padding: 2rem; 
          border-radius: 8px; 
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
        }
        h1 { color: #3b82f6; margin-bottom: 1rem; }
        p { color: #6b7280; margin-bottom: 1.5rem; }
        .icon { font-size: 4rem; margin-bottom: 1rem; }
        button { 
          background: #3b82f6; 
          color: white; 
          border: none; 
          padding: 0.75rem 1.5rem; 
          border-radius: 6px; 
          cursor: pointer; 
        }
        button:hover { background: #2563eb; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="icon">⚖️</div>
        <h1>You're Offline</h1>
        <p>Legal AI is not available right now. Please check your internet connection and try again.</p>
        <button onclick="window.location.reload()">Try Again</button>
      </div>
    </body>
    </html>
  `, {
    headers: { 'Content-Type': 'text/html' }
  })
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  console.log('Background sync triggered:', event.tag)
  
  if (event.tag === 'document-upload') {
    event.waitUntil(syncDocumentUploads())
  } else if (event.tag === 'annotation-sync') {
    event.waitUntil(syncAnnotations())
  } else if (event.tag === 'search-cache') {
    event.waitUntil(syncSearchQueries())
  }
})

async function syncDocumentUploads() {
  try {
    const queuedUploads = await getQueuedItems('document-uploads')
    
    for (const upload of queuedUploads) {
      try {
        const response = await fetch('/api/documents', {
          method: 'POST',
          body: upload.formData,
          headers: upload.headers
        })
        
        if (response.ok) {
          await removeQueuedItem('document-uploads', upload.id)
          await notifyClient('upload-success', { documentId: upload.id })
        }
      } catch (error) {
        console.error('Failed to sync upload:', error)
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error)
  }
}

async function syncAnnotations() {
  try {
    const queuedAnnotations = await getQueuedItems('annotations')
    
    for (const annotation of queuedAnnotations) {
      try {
        const response = await fetch(`/api/documents/${annotation.documentId}/annotations`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(annotation.data)
        })
        
        if (response.ok) {
          await removeQueuedItem('annotations', annotation.id)
        }
      } catch (error) {
        console.error('Failed to sync annotation:', error)
      }
    }
  } catch (error) {
    console.error('Annotation sync failed:', error)
  }
}

async function syncSearchQueries() {
  // Pre-cache popular search results
  try {
    const popularQueries = await getPopularQueries()
    
    for (const query of popularQueries) {
      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`)
        if (response.ok) {
          const cache = await caches.open('search-api')
          await cache.put(`/api/search?q=${encodeURIComponent(query)}`, response.clone())
        }
      } catch (error) {
        console.error('Failed to pre-cache search:', error)
      }
    }
  } catch (error) {
    console.error('Search cache sync failed:', error)
  }
}

// Push notification handling
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event)
  
  const options = {
    body: 'You have new legal research updates',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    tag: 'legal-ai-notification',
    data: {
      url: '/'
    },
    actions: [
      {
        action: 'view',
        title: 'View Updates',
        icon: '/icons/view-action.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/icons/dismiss-action.png'
      }
    ],
    vibrate: [200, 100, 200],
    requireInteraction: true
  }
  
  if (event.data) {
    try {
      const payload = event.data.json()
      options.body = payload.body || options.body
      options.data.url = payload.url || options.data.url
      options.tag = payload.tag || options.tag
    } catch (error) {
      console.error('Error parsing push data:', error)
    }
  }
  
  event.waitUntil(
    self.registration.showNotification('Legal AI System', options)
  )
})

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event.notification.tag)
  
  event.notification.close()
  
  if (event.action === 'dismiss') {
    return
  }
  
  const url = event.notification.data?.url || '/'
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Check if app is already open
        for (const client of clientList) {
          if (client.url === url && 'focus' in client) {
            return client.focus()
          }
        }
        
        // Open new window
        if (clients.openWindow) {
          return clients.openWindow(url)
        }
      })
  )
})

// Message handling for client communication
self.addEventListener('message', (event) => {
  const { type, payload } = event.data
  
  switch (type) {
    case 'QUEUE_UPLOAD':
      queueItem('document-uploads', payload)
      break
    
    case 'QUEUE_ANNOTATION':
      queueItem('annotations', payload)
      break
    
    case 'GET_CACHE_STATUS':
      getCacheStatus().then(status => {
        event.ports[0].postMessage({ type: 'CACHE_STATUS', payload: status })
      })
      break
    
    case 'CLEAR_CACHE':
      clearAllCaches().then(() => {
        event.ports[0].postMessage({ type: 'CACHE_CLEARED' })
      })
      break
    
    case 'SKIP_WAITING':
      self.skipWaiting()
      break
  }
})

// Utility functions for queue management
async function queueItem(queueName, item) {
  try {
    const stored = await getStoredQueue(queueName)
    stored.push({ ...item, id: Date.now(), timestamp: new Date().toISOString() })
    await setStoredQueue(queueName, stored)
    
    // Request background sync
    if (self.registration.sync) {
      await self.registration.sync.register(queueName === 'document-uploads' ? 'document-upload' : 'annotation-sync')
    }
  } catch (error) {
    console.error('Failed to queue item:', error)
  }
}

async function getQueuedItems(queueName) {
  return await getStoredQueue(queueName)
}

async function removeQueuedItem(queueName, itemId) {
  try {
    const stored = await getStoredQueue(queueName)
    const filtered = stored.filter(item => item.id !== itemId)
    await setStoredQueue(queueName, filtered)
  } catch (error) {
    console.error('Failed to remove queued item:', error)
  }
}

async function getStoredQueue(queueName) {
  try {
    const cache = await caches.open('queue-storage')
    const response = await cache.match(`/queue/${queueName}`)
    if (response) {
      return await response.json()
    }
    return []
  } catch (error) {
    console.error('Failed to get stored queue:', error)
    return []
  }
}

async function setStoredQueue(queueName, items) {
  try {
    const cache = await caches.open('queue-storage')
    const response = new Response(JSON.stringify(items), {
      headers: { 'Content-Type': 'application/json' }
    })
    await cache.put(`/queue/${queueName}`, response)
  } catch (error) {
    console.error('Failed to set stored queue:', error)
  }
}

async function getCacheStatus() {
  try {
    const cacheNames = await caches.keys()
    const status = {}
    
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName)
      const keys = await cache.keys()
      status[cacheName] = keys.length
    }
    
    return status
  } catch (error) {
    console.error('Failed to get cache status:', error)
    return {}
  }
}

async function clearAllCaches() {
  try {
    const cacheNames = await caches.keys()
    await Promise.all(cacheNames.map(name => caches.delete(name)))
  } catch (error) {
    console.error('Failed to clear caches:', error)
  }
}

async function notifyClient(type, payload) {
  try {
    const clients = await self.clients.matchAll()
    clients.forEach(client => {
      client.postMessage({ type, payload })
    })
  } catch (error) {
    console.error('Failed to notify client:', error)
  }
}

async function getPopularQueries() {
  // This would typically come from analytics or user data
  return [
    'contract review',
    'legal precedent',
    'case law search',
    'compliance regulations',
    'intellectual property'
  ]
}