/**
 * Enhanced Jest Setup Configuration
 * 
 * Comprehensive test setup and configuration for the Legal AI System frontend tests
 * with 95% coverage target support and advanced testing utilities.
 */
import '@testing-library/jest-dom'
import { configure } from '@testing-library/react'
import { server } from './mocks/server'
import { TextEncoder, TextDecoder } from 'util'

// Configure testing library
configure({ 
  testIdAttribute: 'data-testid',
  asyncUtilTimeout: 5000,
  getElementError: (message, container) => {
    const error = new Error(message)
    error.name = 'TestingLibraryElementError'
    error.stack = null
    return error
  }
})

// Add missing globals for Node.js environment
global.TextEncoder = TextEncoder
global.TextDecoder = TextDecoder

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor(cb) {
    this.cb = cb
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  }))
})

// Mock navigator
Object.defineProperty(navigator, 'onLine', {
  writable: true,
  value: true
})

// Mock service worker
Object.defineProperty(navigator, 'serviceWorker', {
  writable: true,
  value: {
    register: jest.fn(() => Promise.resolve({
      update: jest.fn(),
      unregister: jest.fn(() => Promise.resolve())
    })),
    ready: Promise.resolve({
      showNotification: jest.fn(),
      pushManager: {
        subscribe: jest.fn(),
        getSubscription: jest.fn(() => Promise.resolve(null))
      },
      sync: {
        register: jest.fn()
      }
    }),
    controller: null,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn()
  }
})

// Mock Notification API
global.Notification = class Notification {
  static permission = 'granted'
  static requestPermission = jest.fn(() => Promise.resolve('granted'))
  
  constructor(title, options) {
    this.title = title
    this.body = options?.body
    this.icon = options?.icon
  }
  
  close() {}
}

// Mock Web Speech API
global.webkitSpeechRecognition = class SpeechRecognition {
  constructor() {
    this.continuous = false
    this.interimResults = false
    this.lang = 'en-US'
    this.onresult = null
    this.onerror = null
    this.onend = null
  }
  
  start() {
    setTimeout(() => {
      if (this.onresult) {
        this.onresult({
          results: [{
            0: { transcript: 'test speech' }
          }]
        })
      }
    }, 100)
  }
  
  stop() {}
}

// Mock IndexedDB
const FDBFactory = require('fake-indexeddb/lib/FDBFactory')
const FDBKeyRange = require('fake-indexeddb/lib/FDBKeyRange')

global.indexedDB = new FDBFactory()
global.IDBKeyRange = FDBKeyRange

// Mock Canvas API for chart testing
HTMLCanvasElement.prototype.getContext = jest.fn(() => ({
  fillRect: jest.fn(),
  clearRect: jest.fn(),
  getImageData: jest.fn(() => ({ data: new Array(4) })),
  putImageData: jest.fn(),
  createImageData: jest.fn(() => ({ data: new Array(4) })),
  setTransform: jest.fn(),
  drawImage: jest.fn(),
  save: jest.fn(),
  fillText: jest.fn(),
  restore: jest.fn(),
  beginPath: jest.fn(),
  moveTo: jest.fn(),
  lineTo: jest.fn(),
  closePath: jest.fn(),
  stroke: jest.fn(),
  translate: jest.fn(),
  scale: jest.fn(),
  rotate: jest.fn(),
  arc: jest.fn(),
  fill: jest.fn(),
  measureText: jest.fn(() => ({ width: 0 })),
  transform: jest.fn(),
  rect: jest.fn(),
  clip: jest.fn()
}))

// Mock HTMLCanvasElement.toDataURL
HTMLCanvasElement.prototype.toDataURL = jest.fn(() => 'data:image/png;base64,mock')

// Mock file reading
global.FileReader = class FileReader {
  constructor() {
    this.readyState = 0
    this.result = null
    this.error = null
  }
  
  readAsDataURL = jest.fn(function() {
    this.readyState = 2
    this.result = 'data:image/png;base64,mock'
    if (this.onload) this.onload({ target: this })
  })
  
  readAsText = jest.fn(function() {
    this.readyState = 2
    this.result = 'mock file content'
    if (this.onload) this.onload({ target: this })
  })
}

// Mock window.open
global.open = jest.fn()

// Mock console methods for clean test output
const originalError = console.error
const originalWarn = console.warn

beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return
    }
    originalError(...args)
  }
  
  console.warn = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('componentWillReceiveProps has been renamed')
    ) {
      return
    }
    originalWarn(...args)
  }
})

afterAll(() => {
  console.error = originalError
  console.warn = originalWarn
})

// Setup MSW server
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

// =============================================================================
// ENHANCED CLEANUP AND UTILITIES
// =============================================================================

// Global test utilities
global.testUtils = {
  // Debug helper to log component props/state
  debug: (component, label = 'Component Debug') => {
    console.log(`🐛 ${label}:`, component)
  },
  
  // Helper to wait for async operations
  waitFor: async (fn, timeout = 5000) => {
    const start = Date.now()
    while (Date.now() - start < timeout) {
      try {
        const result = await fn()
        if (result) return result
      } catch (e) {
        // Continue waiting
      }
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    throw new Error(`waitFor timeout after ${timeout}ms`)
  },
  
  // Mock API response helper
  mockApiResponse: (data, status = 200) => ({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
  }),
  
  // Generate test IDs
  generateTestId: (prefix = 'test') => `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

// Custom matchers for better assertions
expect.extend({
  toBeValidApiResponse(received) {
    const pass = received && 
                  typeof received === 'object' &&
                  (received.data !== undefined || received.error !== undefined)
    
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid API response`,
        pass: true,
      }
    } else {
      return {
        message: () => `expected ${received} to be a valid API response with data or error property`,
        pass: false,
      }
    }
  },
  
  toBeValidComponent(received) {
    const pass = received && 
                  typeof received === 'object' &&
                  received.$$typeof !== undefined
    
    if (pass) {
      return {
        message: () => `expected ${received} not to be a valid React component`,
        pass: true,
      }
    } else {
      return {
        message: () => `expected ${received} to be a valid React component`,
        pass: false,
      }
    }
  }
})

// Track slow tests for performance monitoring
const SLOW_TEST_THRESHOLD = 2000 // 2 seconds
const originalIt = global.it
global.it = (name, fn, timeout) => {
  return originalIt(name, async (...args) => {
    const start = Date.now()
    const result = await fn(...args)
    const duration = Date.now() - start
    
    if (duration > SLOW_TEST_THRESHOLD) {
      console.warn(`⚠️  Slow test detected: "${name}" took ${duration}ms`)
    }
    
    return result
  }, timeout)
}

// Enhanced cleanup after each test
afterEach(() => {
  jest.clearAllMocks()
  jest.clearAllTimers()
  jest.restoreAllMocks()
  localStorage.clear()
  sessionStorage.clear()
  
  // Clear DOM
  document.body.innerHTML = ''
  document.head.innerHTML = ''
  
  // Reset any global state
  if (global.fetch && global.fetch.mockClear) {
    global.fetch.mockClear()
  }
})

// Global test timeout
jest.setTimeout(30000)

// Environment variables for tests
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_WS_URL = 'ws://localhost:8000'
process.env.NODE_ENV = 'test'

console.log('🧪 Enhanced Jest setup completed for Legal AI System frontend tests')