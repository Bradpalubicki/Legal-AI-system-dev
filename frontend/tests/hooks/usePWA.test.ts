import { renderHook, act, waitFor } from '@testing-library/react'
import { usePWA } from '../../src/hooks/usePWA'

// Mock service worker registration
const mockRegistration = {
  installing: null,
  waiting: null,
  active: {
    postMessage: jest.fn()
  },
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  update: jest.fn(),
  unregister: jest.fn(() => Promise.resolve(true))
}

// Mock install prompt event
const mockInstallPrompt = {
  prompt: jest.fn(() => Promise.resolve()),
  userChoice: Promise.resolve({ outcome: 'accepted', platform: 'web' }),
  preventDefault: jest.fn()
}

describe('usePWA', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Reset service worker mock
    Object.defineProperty(navigator, 'serviceWorker', {
      writable: true,
      value: {
        register: jest.fn(() => Promise.resolve(mockRegistration)),
        ready: Promise.resolve(mockRegistration),
        controller: null,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      }
    })
    
    // Reset online status
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true
    })
    
    // Mock matchMedia for standalone detection
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: jest.fn(() => ({
        matches: false,
        media: '(display-mode: standalone)',
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      }))
    })
  })

  describe('Initialization', () => {
    it('detects PWA support', () => {
      const { result } = renderHook(() => usePWA())
      
      expect(result.current.isSupported).toBe(true)
    })

    it('detects when PWA is not supported', () => {
      // Remove service worker support
      delete (navigator as any).serviceWorker
      
      const { result } = renderHook(() => usePWA())
      
      expect(result.current.isSupported).toBe(false)
    })

    it('registers service worker on initialization', async () => {
      renderHook(() => usePWA())
      
      await waitFor(() => {
        expect(navigator.serviceWorker.register).toHaveBeenCalledWith('/sw.js', {
          scope: '/'
        })
      })
    })

    it('detects standalone mode', () => {
      // Mock standalone display mode
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn(() => ({
          matches: true,
          media: '(display-mode: standalone)',
          addEventListener: jest.fn(),
          removeEventListener: jest.fn()
        }))
      })
      
      const { result } = renderHook(() => usePWA())
      
      expect(result.current.isStandalone).toBe(true)
    })
  })

  describe('Installation', () => {
    it('detects when app is installable', async () => {
      const { result } = renderHook(() => usePWA())
      
      // Simulate beforeinstallprompt event
      act(() => {
        const event = new Event('beforeinstallprompt') as any
        event.prompt = mockInstallPrompt.prompt
        event.userChoice = mockInstallPrompt.userChoice
        event.preventDefault = mockInstallPrompt.preventDefault
        
        window.dispatchEvent(event)
      })
      
      await waitFor(() => {
        expect(result.current.isInstallable).toBe(true)
      })
    })

    it('installs the app successfully', async () => {
      const { result } = renderHook(() => usePWA())
      
      // Make app installable
      act(() => {
        const event = new Event('beforeinstallprompt') as any
        event.prompt = mockInstallPrompt.prompt
        event.userChoice = Promise.resolve({ outcome: 'accepted' })
        event.preventDefault = mockInstallPrompt.preventDefault
        
        window.dispatchEvent(event)
      })
      
      await waitFor(() => {
        expect(result.current.isInstallable).toBe(true)
      })
      
      // Install the app
      let installResult: boolean = false
      
      await act(async () => {
        installResult = await result.current.install()
      })
      
      expect(installResult).toBe(true)
      expect(mockInstallPrompt.prompt).toHaveBeenCalled()
    })

    it('handles installation rejection', async () => {
      const { result } = renderHook(() => usePWA())
      
      // Make app installable
      act(() => {
        const event = new Event('beforeinstallprompt') as any
        event.prompt = mockInstallPrompt.prompt
        event.userChoice = Promise.resolve({ outcome: 'dismissed' })
        event.preventDefault = mockInstallPrompt.preventDefault
        
        window.dispatchEvent(event)
      })
      
      await waitFor(() => {
        expect(result.current.isInstallable).toBe(true)
      })
      
      // Try to install
      let installResult: boolean = true
      
      await act(async () => {
        installResult = await result.current.install()
      })
      
      expect(installResult).toBe(false)
    })

    it('handles installation errors', async () => {
      const { result } = renderHook(() => usePWA())
      
      // Make app installable with error
      act(() => {
        const event = new Event('beforeinstallprompt') as any
        event.prompt = jest.fn(() => Promise.reject(new Error('Installation failed')))
        event.userChoice = Promise.resolve({ outcome: 'accepted' })
        event.preventDefault = mockInstallPrompt.preventDefault
        
        window.dispatchEvent(event)
      })
      
      await waitFor(() => {
        expect(result.current.isInstallable).toBe(true)
      })
      
      // Try to install
      let installResult: boolean = true
      
      await act(async () => {
        installResult = await result.current.install()
      })
      
      expect(installResult).toBe(false)
    })

    it('detects when app is already installed', async () => {
      // Mock getInstalledRelatedApps
      Object.defineProperty(navigator, 'getInstalledRelatedApps', {
        writable: true,
        value: jest.fn(() => Promise.resolve([{ id: 'legal-ai-app' }]))
      })
      
      const { result } = renderHook(() => usePWA())
      
      await waitFor(() => {
        expect(result.current.isInstalled).toBe(true)
      })
    })
  })

  describe('Service Worker Management', () => {
    it('handles service worker updates', async () => {
      const { result } = renderHook(() => usePWA())
      
      // Simulate service worker update
      const mockNewWorker = {
        state: 'installed',
        addEventListener: jest.fn((event, callback) => {
          if (event === 'statechange') {
            setTimeout(callback, 100)
          }
        })
      }
      
      const updatedRegistration = {
        ...mockRegistration,
        installing: mockNewWorker
      }
      
      act(() => {
        const updateEvent = {
          type: 'updatefound',
          target: updatedRegistration
        }
        
        const addEventListener = mockRegistration.addEventListener as jest.Mock
        const updateCallback = addEventListener.mock.calls.find(call => call[0] === 'updatefound')?.[1]
        
        if (updateCallback) {
          updateCallback(updateEvent)
        }
      })
      
      await waitFor(() => {
        expect(result.current.needsRefresh).toBe(true)
      })
    })

    it('refreshes app with new service worker', async () => {
      const mockReload = jest.fn()
      Object.defineProperty(window.location, 'reload', {
        writable: true,
        value: mockReload
      })
      
      const { result } = renderHook(() => usePWA())
      
      // Set up service worker with waiting worker
      act(() => {
        result.current.refreshApp()
      })
      
      expect(mockRegistration.waiting?.postMessage || mockRegistration.active.postMessage)
        .toHaveBeenCalledWith({ type: 'SKIP_WAITING' })
    })

    it('clears cache successfully', async () => {
      const { result } = renderHook(() => usePWA())
      
      await act(async () => {
        await result.current.clearCache()
      })
      
      expect(mockRegistration.active.postMessage).toHaveBeenCalledWith(
        { type: 'CLEAR_CACHE' },
        expect.any(Array)
      )
    })

    it('gets cache status', async () => {
      const { result } = renderHook(() => usePWA())
      
      // Mock message channel response
      const mockMessageChannel = {
        port1: {
          onmessage: null,
          postMessage: jest.fn()
        },
        port2: {}
      }
      
      global.MessageChannel = jest.fn(() => mockMessageChannel)
      
      act(() => {
        result.current.getCacheStatus().then(status => {
          expect(status).toBeDefined()
        })
        
        // Simulate response
        if (mockMessageChannel.port1.onmessage) {
          mockMessageChannel.port1.onmessage({
            data: {
              type: 'CACHE_STATUS',
              payload: { 'cache-v1': 25, 'documents': 12 }
            }
          })
        }
      })
    })
  })

  describe('Online/Offline Detection', () => {
    it('detects online status', () => {
      const { result } = renderHook(() => usePWA())
      
      expect(result.current.isOffline).toBe(false)
    })

    it('detects offline status', () => {
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      })
      
      const { result } = renderHook(() => usePWA())
      
      expect(result.current.isOffline).toBe(true)
    })

    it('updates status when going offline', async () => {
      const { result } = renderHook(() => usePWA())
      
      expect(result.current.isOffline).toBe(false)
      
      act(() => {
        Object.defineProperty(navigator, 'onLine', {
          writable: true,
          value: false
        })
        
        window.dispatchEvent(new Event('offline'))
      })
      
      await waitFor(() => {
        expect(result.current.isOffline).toBe(true)
      })
    })

    it('updates status when going online', async () => {
      // Start offline
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      })
      
      const { result } = renderHook(() => usePWA())
      
      expect(result.current.isOffline).toBe(true)
      
      act(() => {
        Object.defineProperty(navigator, 'onLine', {
          writable: true,
          value: true
        })
        
        window.dispatchEvent(new Event('online'))
      })
      
      await waitFor(() => {
        expect(result.current.isOffline).toBe(false)
      })
    })
  })

  describe('Install Banner', () => {
    it('shows install banner', () => {
      const { result } = renderHook(() => usePWA())
      
      act(() => {
        result.current.showInstallBanner()
      })
      
      // Check if banner was added to DOM
      const banner = document.querySelector('[data-pwa-banner]')
      expect(banner).toBeInTheDocument()
    })

    it('hides install banner', () => {
      const { result } = renderHook(() => usePWA())
      
      // First show the banner
      act(() => {
        result.current.showInstallBanner()
      })
      
      // Then hide it
      act(() => {
        result.current.hideInstallBanner()
      })
      
      const banner = document.querySelector('[data-pwa-banner]')
      expect(banner).not.toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles service worker registration failure', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      
      // Mock registration failure
      Object.defineProperty(navigator, 'serviceWorker', {
        writable: true,
        value: {
          register: jest.fn(() => Promise.reject(new Error('Registration failed'))),
          ready: Promise.reject(new Error('Not ready')),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn()
        }
      })
      
      renderHook(() => usePWA())
      
      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith(
          'Service worker registration failed:',
          expect.any(Error)
        )
      })
      
      consoleSpy.mockRestore()
    })

    it('handles installation when no prompt is available', async () => {
      const { result } = renderHook(() => usePWA())
      
      // Try to install without setting up install prompt
      let installResult: boolean = true
      
      await act(async () => {
        installResult = await result.current.install()
      })
      
      expect(installResult).toBe(false)
    })
  })

  describe('Cleanup', () => {
    it('removes event listeners on unmount', () => {
      const removeEventListenerSpy = jest.spyOn(window, 'removeEventListener')
      
      const { unmount } = renderHook(() => usePWA())
      
      unmount()
      
      expect(removeEventListenerSpy).toHaveBeenCalledWith('beforeinstallprompt', expect.any(Function))
      expect(removeEventListenerSpy).toHaveBeenCalledWith('appinstalled', expect.any(Function))
      expect(removeEventListenerSpy).toHaveBeenCalledWith('online', expect.any(Function))
      expect(removeEventListenerSpy).toHaveBeenCalledWith('offline', expect.any(Function))
      
      removeEventListenerSpy.mockRestore()
    })
  })
})