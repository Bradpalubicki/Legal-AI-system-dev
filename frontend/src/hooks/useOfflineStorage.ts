'use client'

import { useState, useEffect, useCallback } from 'react'

interface OfflineStorageConfig {
  storeName: string
  version?: number
  keyPath?: string
  maxItems?: number
  ttl?: number // Time to live in milliseconds
}

interface StoredItem<T> {
  id: string
  data: T
  timestamp: number
  ttl?: number
  metadata?: Record<string, any>
}

interface OfflineStorageHook<T> {
  data: T[]
  isLoading: boolean
  error: string | null
  
  // Basic operations
  getItem: (id: string) => Promise<T | null>
  setItem: (id: string, data: T, metadata?: Record<string, any>) => Promise<void>
  removeItem: (id: string) => Promise<void>
  clear: () => Promise<void>
  
  // Bulk operations
  getAll: () => Promise<T[]>
  setAll: (items: Array<{ id: string; data: T; metadata?: Record<string, any> }>) => Promise<void>
  
  // Search and filter
  find: (predicate: (item: T) => boolean) => Promise<T[]>
  query: (query: Partial<T>) => Promise<T[]>
  
  // Sync operations
  syncItem: (id: string, data: T) => Promise<void>
  syncAll: () => Promise<void>
  getPendingSync: () => Promise<T[]>
  
  // Utility
  getStorageInfo: () => Promise<{ count: number; size: number }>
  cleanup: () => Promise<void>
}

export function useOfflineStorage<T extends Record<string, any>>(
  config: OfflineStorageConfig
): OfflineStorageHook<T> {
  const [data, setData] = useState<T[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [db, setDb] = useState<IDBDatabase | null>(null)

  const { storeName, version = 1, keyPath = 'id', maxItems = 1000, ttl } = config

  // Initialize IndexedDB
  useEffect(() => {
    const initDB = async () => {
      try {
        const request = indexedDB.open(`legal-ai-${storeName}`, version)
        
        request.onupgradeneeded = (event) => {
          const db = (event.target as IDBOpenDBRequest).result
          
          if (!db.objectStoreNames.contains(storeName)) {
            const store = db.createObjectStore(storeName, { keyPath })
            store.createIndex('timestamp', 'timestamp', { unique: false })
            store.createIndex('needsSync', 'metadata.needsSync', { unique: false })
          }
        }
        
        request.onsuccess = (event) => {
          const database = (event.target as IDBOpenDBRequest).result
          setDb(database)
          setIsLoading(false)
          
          // Load initial data
          loadAllData(database)
        }
        
        request.onerror = () => {
          setError('Failed to initialize offline storage')
          setIsLoading(false)
        }
      } catch (err) {
        setError(`Storage initialization error: ${err}`)
        setIsLoading(false)
      }
    }

    initDB()
  }, [storeName, version, keyPath])

  // Load all data from storage
  const loadAllData = useCallback(async (database?: IDBDatabase) => {
    const dbInstance = database || db
    if (!dbInstance) return

    try {
      const transaction = dbInstance.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const request = store.getAll()
      
      request.onsuccess = () => {
        const items = request.result as StoredItem<T>[]
        const validItems = items
          .filter(item => !isExpired(item))
          .map(item => item.data)
        
        setData(validItems)
        
        // Clean up expired items
        cleanupExpired(dbInstance, items)
      }
      
      request.onerror = () => {
        setError('Failed to load offline data')
      }
    } catch (err) {
      setError(`Data loading error: ${err}`)
    }
  }, [db, storeName])

  // Check if item is expired
  const isExpired = (item: StoredItem<T>): boolean => {
    if (!item.ttl && !ttl) return false
    
    const itemTtl = item.ttl || ttl
    if (!itemTtl) return false
    
    return Date.now() - item.timestamp > itemTtl
  }

  // Clean up expired items
  const cleanupExpired = async (database: IDBDatabase, items: StoredItem<T>[]) => {
    const expiredItems = items.filter(item => isExpired(item))
    
    if (expiredItems.length > 0) {
      const transaction = database.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      
      for (const item of expiredItems) {
        store.delete(item.id)
      }
    }
  }

  // Get single item
  const getItem = useCallback(async (id: string): Promise<T | null> => {
    if (!db) return null

    try {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const request = store.get(id)
      
      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          const item = request.result as StoredItem<T> | undefined
          
          if (!item || isExpired(item)) {
            resolve(null)
            return
          }
          
          resolve(item.data)
        }
        
        request.onerror = () => reject(new Error('Failed to get item'))
      })
    } catch (err) {
      setError(`Get item error: ${err}`)
      return null
    }
  }, [db, storeName])

  // Set single item
  const setItem = useCallback(async (
    id: string, 
    itemData: T, 
    metadata?: Record<string, any>
  ): Promise<void> => {
    if (!db) return

    try {
      const storedItem: StoredItem<T> = {
        id,
        data: itemData,
        timestamp: Date.now(),
        ttl,
        metadata
      }
      
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      
      // Check if we're at max capacity
      const count = await getItemCount(store)
      if (count >= maxItems) {
        await removeOldestItems(store, 1)
      }
      
      const request = store.put(storedItem)
      
      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          // Update local state
          setData(prev => {
            const filtered = prev.filter(item => (item as any)[keyPath] !== id)
            return [...filtered, itemData]
          })
          resolve()
        }
        
        request.onerror = () => reject(new Error('Failed to set item'))
      })
    } catch (err) {
      setError(`Set item error: ${err}`)
    }
  }, [db, storeName, keyPath, maxItems, ttl])

  // Remove single item
  const removeItem = useCallback(async (id: string): Promise<void> => {
    if (!db) return

    try {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.delete(id)
      
      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          setData(prev => prev.filter(item => (item as any)[keyPath] !== id))
          resolve()
        }
        
        request.onerror = () => reject(new Error('Failed to remove item'))
      })
    } catch (err) {
      setError(`Remove item error: ${err}`)
    }
  }, [db, storeName, keyPath])

  // Clear all items
  const clear = useCallback(async (): Promise<void> => {
    if (!db) return

    try {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.clear()
      
      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          setData([])
          resolve()
        }
        
        request.onerror = () => reject(new Error('Failed to clear storage'))
      })
    } catch (err) {
      setError(`Clear error: ${err}`)
    }
  }, [db, storeName])

  // Get all items
  const getAll = useCallback(async (): Promise<T[]> => {
    if (!db) return []

    try {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const request = store.getAll()
      
      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          const items = request.result as StoredItem<T>[]
          const validItems = items
            .filter(item => !isExpired(item))
            .map(item => item.data)
          
          resolve(validItems)
        }
        
        request.onerror = () => reject(new Error('Failed to get all items'))
      })
    } catch (err) {
      setError(`Get all error: ${err}`)
      return []
    }
  }, [db, storeName])

  // Set all items
  const setAll = useCallback(async (
    items: Array<{ id: string; data: T; metadata?: Record<string, any> }>
  ): Promise<void> => {
    if (!db) return

    try {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      
      // Clear existing data
      await new Promise<void>((resolve, reject) => {
        const clearRequest = store.clear()
        clearRequest.onsuccess = () => resolve()
        clearRequest.onerror = () => reject(new Error('Failed to clear storage'))
      })
      
      // Add new items
      for (const { id, data: itemData, metadata } of items) {
        const storedItem: StoredItem<T> = {
          id,
          data: itemData,
          timestamp: Date.now(),
          ttl,
          metadata
        }
        
        await new Promise<void>((resolve, reject) => {
          const putRequest = store.put(storedItem)
          putRequest.onsuccess = () => resolve()
          putRequest.onerror = () => reject(new Error('Failed to add item'))
        })
      }
      
      // Update local state
      setData(items.map(item => item.data))
    } catch (err) {
      setError(`Set all error: ${err}`)
    }
  }, [db, storeName, ttl])

  // Find items by predicate
  const find = useCallback(async (predicate: (item: T) => boolean): Promise<T[]> => {
    const allItems = await getAll()
    return allItems.filter(predicate)
  }, [getAll])

  // Query items by partial match
  const query = useCallback(async (queryObj: Partial<T>): Promise<T[]> => {
    return find(item => {
      return Object.entries(queryObj).every(([key, value]) => 
        item[key] === value
      )
    })
  }, [find])

  // Sync item (mark for background sync)
  const syncItem = useCallback(async (id: string, itemData: T): Promise<void> => {
    await setItem(id, itemData, { needsSync: true, syncTimestamp: Date.now() })
    
    // Request background sync if service worker supports it
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      const registration = await navigator.serviceWorker.ready
      await registration.sync.register(`sync-${storeName}`)
    }
  }, [setItem, storeName])

  // Sync all pending items
  const syncAll = useCallback(async (): Promise<void> => {
    if (!db) return

    try {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const index = store.index('needsSync')
      const request = index.getAll(true)
      
      return new Promise((resolve, reject) => {
        request.onsuccess = async () => {
          const items = request.result as StoredItem<T>[]
          
          // Process sync queue
          for (const item of items) {
            try {
              // This would typically make API calls to sync data
              console.log('Syncing item:', item.id)
              
              // Remove sync flag after successful sync
              await setItem(item.id, item.data, { 
                ...item.metadata, 
                needsSync: false 
              })
            } catch (syncError) {
              console.error('Failed to sync item:', item.id, syncError)
            }
          }
          
          resolve()
        }
        
        request.onerror = () => reject(new Error('Failed to get sync items'))
      })
    } catch (err) {
      setError(`Sync all error: ${err}`)
    }
  }, [db, storeName, setItem])

  // Get items pending sync
  const getPendingSync = useCallback(async (): Promise<T[]> => {
    if (!db) return []

    try {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const index = store.index('needsSync')
      const request = index.getAll(true)
      
      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          const items = request.result as StoredItem<T>[]
          resolve(items.map(item => item.data))
        }
        
        request.onerror = () => reject(new Error('Failed to get pending sync items'))
      })
    } catch (err) {
      setError(`Get pending sync error: ${err}`)
      return []
    }
  }, [db, storeName])

  // Get storage information
  const getStorageInfo = useCallback(async (): Promise<{ count: number; size: number }> => {
    if (!db) return { count: 0, size: 0 }

    try {
      const transaction = db.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      
      const countRequest = store.count()
      const allRequest = store.getAll()
      
      return new Promise((resolve, reject) => {
        let count = 0
        let size = 0
        
        countRequest.onsuccess = () => {
          count = countRequest.result
        }
        
        allRequest.onsuccess = () => {
          const items = allRequest.result as StoredItem<T>[]
          size = new Blob([JSON.stringify(items)]).size
          resolve({ count, size })
        }
        
        countRequest.onerror = allRequest.onerror = () => {
          reject(new Error('Failed to get storage info'))
        }
      })
    } catch (err) {
      setError(`Storage info error: ${err}`)
      return { count: 0, size: 0 }
    }
  }, [db, storeName])

  // Clean up expired items
  const cleanup = useCallback(async (): Promise<void> => {
    if (!db) return

    try {
      const transaction = db.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)
      const request = store.getAll()
      
      return new Promise((resolve, reject) => {
        request.onsuccess = async () => {
          const items = request.result as StoredItem<T>[]
          const expiredItems = items.filter(item => isExpired(item))
          
          for (const item of expiredItems) {
            await new Promise<void>((resolveDelete, rejectDelete) => {
              const deleteRequest = store.delete(item.id)
              deleteRequest.onsuccess = () => resolveDelete()
              deleteRequest.onerror = () => rejectDelete(new Error('Failed to delete expired item'))
            })
          }
          
          // Refresh local data
          await loadAllData(db)
          resolve()
        }
        
        request.onerror = () => reject(new Error('Failed to cleanup storage'))
      })
    } catch (err) {
      setError(`Cleanup error: ${err}`)
    }
  }, [db, storeName, loadAllData])

  // Helper function to get item count
  const getItemCount = async (store: IDBObjectStore): Promise<number> => {
    return new Promise((resolve, reject) => {
      const countRequest = store.count()
      countRequest.onsuccess = () => resolve(countRequest.result)
      countRequest.onerror = () => reject(new Error('Failed to get item count'))
    })
  }

  // Helper function to remove oldest items
  const removeOldestItems = async (store: IDBObjectStore, count: number): Promise<void> => {
    return new Promise((resolve, reject) => {
      const index = store.index('timestamp')
      const request = index.openCursor()
      let removed = 0
      
      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result as IDBCursorWithValue
        
        if (cursor && removed < count) {
          cursor.delete()
          removed++
          cursor.continue()
        } else {
          resolve()
        }
      }
      
      request.onerror = () => reject(new Error('Failed to remove oldest items'))
    })
  }

  return {
    data,
    isLoading,
    error,
    getItem,
    setItem,
    removeItem,
    clear,
    getAll,
    setAll,
    find,
    query,
    syncItem,
    syncAll,
    getPendingSync,
    getStorageInfo,
    cleanup
  }
}