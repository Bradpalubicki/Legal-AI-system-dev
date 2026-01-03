/**
 * Offline Manager for Legal AI System Mobile Interface
 * Handles caching of educational content, disclaimer acknowledgments, 
 * and document upload queuing with legal compliance requirements
 */

interface CacheItem {
  id: string;
  data: any;
  timestamp: number;
  expiresAt?: number;
  privilegeLevel?: 'public' | 'confidential' | 'attorney_client' | 'work_product';
  requiresEncryption?: boolean;
}

interface QueuedUpload {
  id: string;
  file: File;
  metadata: {
    privilegeLevel: string;
    clientId?: string;
    caseId?: string;
    documentType: string;
    confidentialityAgreement: boolean;
  };
  timestamp: number;
  retryCount: number;
  maxRetries: number;
}

interface DisclaimerAcknowledgment {
  type: string;
  timestamp: number;
  sessionId: string;
  userAgent: string;
  ipHash?: string; // Hashed for privacy
}

class OfflineManager {
  private static instance: OfflineManager;
  private cacheName = 'legal-ai-mobile-v1';
  private educationCacheName = 'legal-education-v1';
  private dbName = 'LegalAIOffline';
  private dbVersion = 1;
  private db: IDBDatabase | null = null;

  private constructor() {
    this.initializeDatabase();
    this.registerServiceWorker();
  }

  static getInstance(): OfflineManager {
    if (!OfflineManager.instance) {
      OfflineManager.instance = new OfflineManager();
    }
    return OfflineManager.instance;
  }

  private async initializeDatabase(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Educational content store
        if (!db.objectStoreNames.contains('education')) {
          const educationStore = db.createObjectStore('education', { keyPath: 'id' });
          educationStore.createIndex('category', 'category', { unique: false });
          educationStore.createIndex('level', 'level', { unique: false });
          educationStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Disclaimer acknowledgments store
        if (!db.objectStoreNames.contains('disclaimers')) {
          const disclaimerStore = db.createObjectStore('disclaimers', { keyPath: 'id', autoIncrement: true });
          disclaimerStore.createIndex('type', 'type', { unique: false });
          disclaimerStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Upload queue store
        if (!db.objectStoreNames.contains('uploadQueue')) {
          const uploadStore = db.createObjectStore('uploadQueue', { keyPath: 'id' });
          uploadStore.createIndex('timestamp', 'timestamp', { unique: false });
          uploadStore.createIndex('privilegeLevel', 'metadata.privilegeLevel', { unique: false });
        }

        // User progress store
        if (!db.objectStoreNames.contains('progress')) {
          const progressStore = db.createObjectStore('progress', { keyPath: 'id' });
          progressStore.createIndex('type', 'type', { unique: false });
        }

        // Settings store
        if (!db.objectStoreNames.contains('settings')) {
          db.createObjectStore('settings', { keyPath: 'key' });
        }
      };
    });
  }

  private async registerServiceWorker(): Promise<void> {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered:', registration);
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  }

  // Educational Content Caching
  async cacheEducationalContent(content: any[]): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['education'], 'readwrite');
    const store = transaction.objectStore('education');

    for (const item of content) {
      const cacheItem: CacheItem = {
        id: item.id,
        data: item,
        timestamp: Date.now(),
        expiresAt: Date.now() + (7 * 24 * 60 * 60 * 1000), // 7 days
        privilegeLevel: 'public', // Educational content is generally public
        requiresEncryption: false
      };

      await this.putItem(store, cacheItem);
    }

    // Also cache in browser cache for quick access
    const cache = await caches.open(this.educationCacheName);
    const contentBlob = new Blob([JSON.stringify(content)], { type: 'application/json' });
    const response = new Response(contentBlob);
    await cache.put('/education-content', response);
  }

  async getCachedEducationalContent(): Promise<any[]> {
    // Try browser cache first for speed
    try {
      const cache = await caches.open(this.educationCacheName);
      const response = await cache.match('/education-content');
      if (response) {
        return await response.json();
      }
    } catch (error) {
      console.warn('Browser cache failed, trying IndexedDB:', error);
    }

    // Fallback to IndexedDB
    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['education'], 'readonly');
    const store = transaction.objectStore('education');
    const request = store.getAll();

    return new Promise((resolve) => {
      request.onsuccess = () => {
        const items = request.result
          .filter((item: CacheItem) => !item.expiresAt || item.expiresAt > Date.now())
          .map((item: CacheItem) => item.data);
        resolve(items);
      };
      request.onerror = () => resolve([]);
    });
  }

  // Disclaimer Acknowledgments
  async storeDisclaimerAcknowledgment(type: string, additionalData?: any): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const acknowledgment: DisclaimerAcknowledgment = {
      type,
      timestamp: Date.now(),
      sessionId: this.generateSessionId(),
      userAgent: navigator.userAgent,
      ...additionalData
    };

    const transaction = this.db!.transaction(['disclaimers'], 'readwrite');
    const store = transaction.objectStore('disclaimers');
    await this.putItem(store, acknowledgment);

    // Also store in localStorage for quick access
    const key = `disclaimer-${type}`;
    localStorage.setItem(key, 'true');
    localStorage.setItem(`${key}-timestamp`, acknowledgment.timestamp.toString());
  }

  async getDisclaimerAcknowledgment(type: string): Promise<DisclaimerAcknowledgment | null> {
    // Quick check in localStorage first
    const quickCheck = localStorage.getItem(`disclaimer-${type}`);
    if (quickCheck !== 'true') return null;

    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['disclaimers'], 'readonly');
    const store = transaction.objectStore('disclaimers');
    const index = store.index('type');
    const request = index.getAll(type);

    return new Promise((resolve) => {
      request.onsuccess = () => {
        const results = request.result;
        if (results.length > 0) {
          // Return the most recent acknowledgment
          const latest = results.sort((a, b) => b.timestamp - a.timestamp)[0];
          resolve(latest);
        } else {
          resolve(null);
        }
      };
      request.onerror = () => resolve(null);
    });
  }

  // Document Upload Queue
  async queueDocumentUpload(file: File, metadata: QueuedUpload['metadata']): Promise<string> {
    if (!this.db) await this.initializeDatabase();

    const uploadId = this.generateUploadId();
    const queuedUpload: QueuedUpload = {
      id: uploadId,
      file,
      metadata,
      timestamp: Date.now(),
      retryCount: 0,
      maxRetries: 3
    };

    // Store file in IndexedDB (for offline capability)
    const transaction = this.db!.transaction(['uploadQueue'], 'readwrite');
    const store = transaction.objectStore('uploadQueue');
    
    // Convert file to ArrayBuffer for storage
    const fileBuffer = await file.arrayBuffer();
    const queuedUploadWithBuffer = {
      ...queuedUpload,
      file: {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
        buffer: fileBuffer
      }
    };

    await this.putItem(store, queuedUploadWithBuffer);

    // Trigger immediate upload attempt if online
    if (navigator.onLine) {
      this.processUploadQueue();
    }

    return uploadId;
  }

  async getUploadQueue(): Promise<QueuedUpload[]> {
    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['uploadQueue'], 'readonly');
    const store = transaction.objectStore('uploadQueue');
    const request = store.getAll();

    return new Promise((resolve) => {
      request.onsuccess = () => {
        const items = request.result.map((item: any) => ({
          ...item,
          file: new File([item.file.buffer], item.file.name, {
            type: item.file.type,
            lastModified: item.file.lastModified
          })
        }));
        resolve(items);
      };
      request.onerror = () => resolve([]);
    });
  }

  async processUploadQueue(): Promise<void> {
    const queue = await this.getUploadQueue();
    
    for (const upload of queue) {
      try {
        // Simulate upload API call
        const success = await this.uploadDocument(upload);
        
        if (success) {
          await this.removeFromUploadQueue(upload.id);
        } else {
          await this.incrementRetryCount(upload.id);
        }
      } catch (error) {
        console.error(`Failed to upload ${upload.id}:`, error);
        await this.incrementRetryCount(upload.id);
      }
    }
  }

  private async uploadDocument(upload: QueuedUpload): Promise<boolean> {
    // In a real implementation, this would make an API call
    const formData = new FormData();
    formData.append('file', upload.file);
    formData.append('metadata', JSON.stringify(upload.metadata));

    try {
      // Simulate API call
      return new Promise((resolve) => {
        setTimeout(() => {
          // Simulate 80% success rate
          resolve(Math.random() > 0.2);
        }, 1000);
      });
    } catch (error) {
      return false;
    }
  }

  private async removeFromUploadQueue(uploadId: string): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['uploadQueue'], 'readwrite');
    const store = transaction.objectStore('uploadQueue');
    await this.deleteItem(store, uploadId);
  }

  private async incrementRetryCount(uploadId: string): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['uploadQueue'], 'readwrite');
    const store = transaction.objectStore('uploadQueue');
    const getRequest = store.get(uploadId);

    getRequest.onsuccess = () => {
      const upload = getRequest.result;
      if (upload) {
        upload.retryCount++;
        if (upload.retryCount >= upload.maxRetries) {
          // Mark as failed or remove from queue
          console.error(`Upload ${uploadId} exceeded max retries`);
          this.deleteItem(store, uploadId);
        } else {
          this.putItem(store, upload);
        }
      }
    };
  }

  // User Progress and Settings
  async storeUserProgress(type: string, data: any): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const progressItem = {
      id: `${type}-${Date.now()}`,
      type,
      data,
      timestamp: Date.now()
    };

    const transaction = this.db!.transaction(['progress'], 'readwrite');
    const store = transaction.objectStore('progress');
    await this.putItem(store, progressItem);
  }

  async getUserProgress(type: string): Promise<any[]> {
    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['progress'], 'readonly');
    const store = transaction.objectStore('progress');
    const index = store.index('type');
    const request = index.getAll(type);

    return new Promise((resolve) => {
      request.onsuccess = () => {
        resolve(request.result.map(item => item.data));
      };
      request.onerror = () => resolve([]);
    });
  }

  async storeSetting(key: string, value: any): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const setting = { key, value, timestamp: Date.now() };
    const transaction = this.db!.transaction(['settings'], 'readwrite');
    const store = transaction.objectStore('settings');
    await this.putItem(store, setting);
  }

  async getSetting(key: string): Promise<any> {
    if (!this.db) await this.initializeDatabase();

    const transaction = this.db!.transaction(['settings'], 'readonly');
    const store = transaction.objectStore('settings');
    const request = store.get(key);

    return new Promise((resolve) => {
      request.onsuccess = () => {
        const result = request.result;
        resolve(result ? result.value : null);
      };
      request.onerror = () => resolve(null);
    });
  }

  // Network Status and Sync
  async syncWhenOnline(): Promise<void> {
    if (navigator.onLine) {
      await this.processUploadQueue();
      // Sync other data as needed
    }
  }

  // Data Management
  async clearExpiredCache(): Promise<void> {
    if (!this.db) await this.initializeDatabase();

    const stores = ['education', 'disclaimers', 'progress'];
    const now = Date.now();

    for (const storeName of stores) {
      const transaction = this.db!.transaction([storeName], 'readwrite');
      const store = transaction.objectStore('store');
      const request = store.getAll();

      request.onsuccess = () => {
        const items = request.result;
        items.forEach((item: CacheItem) => {
          if (item.expiresAt && item.expiresAt < now) {
            this.deleteItem(store, item.id);
          }
        });
      };
    }
  }

  // Compliance and Security
  async clearPrivilegedData(): Promise<void> {
    console.warn('Clearing privileged data for compliance');
    
    if (!this.db) await this.initializeDatabase();

    // Clear privileged uploads from queue
    const uploadTransaction = this.db!.transaction(['uploadQueue'], 'readwrite');
    const uploadStore = uploadTransaction.objectStore('uploadQueue');
    const uploadRequest = uploadStore.getAll();

    uploadRequest.onsuccess = () => {
      const uploads = uploadRequest.result;
      uploads.forEach((upload: QueuedUpload) => {
        if (upload.metadata.privilegeLevel === 'attorney_client' || 
            upload.metadata.privilegeLevel === 'work_product') {
          this.deleteItem(uploadStore, upload.id);
        }
      });
    };

    // Clear browser caches
    const cacheNames = await caches.keys();
    await Promise.all(
      cacheNames.map(name => caches.delete(name))
    );
  }

  // Utility Methods
  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateUploadId(): string {
    return `upload-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private putItem(store: IDBObjectStore, item: any): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = store.put(item);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  private deleteItem(store: IDBObjectStore, key: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = store.delete(key);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}

// Initialize offline capabilities on app load
let offlineManager: OfflineManager;

if (typeof window !== 'undefined') {
  offlineManager = OfflineManager.getInstance();

  // Set up online/offline event listeners
  window.addEventListener('online', () => {
    console.log('Back online - syncing data');
    offlineManager.syncWhenOnline();
  });

  window.addEventListener('offline', () => {
    console.log('Gone offline - caching enabled');
  });

  // Periodic cleanup of expired cache
  setInterval(() => {
    offlineManager.clearExpiredCache();
  }, 60 * 60 * 1000); // Every hour
}

export default OfflineManager;