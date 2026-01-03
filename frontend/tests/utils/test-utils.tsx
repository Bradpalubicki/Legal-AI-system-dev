import React from 'react'
import { render, RenderOptions, RenderResult } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider } from 'next-themes'
import PWAProvider from '../../src/components/PWAProvider'

// Mock user for testing
export const mockUser = {
  id: '1',
  email: 'test@example.com',
  name: 'Test User',
  role: 'attorney',
  avatar: 'https://example.com/avatar.jpg'
}

// Mock document for testing
export const mockDocument = {
  id: '1',
  title: 'Contract Agreement.pdf',
  type: 'contract' as const,
  size: 2048576,
  uploadedAt: '2023-11-01T10:00:00Z',
  status: 'processed' as const,
  content: 'Mock document content...',
  analysis: {
    summary: 'This is a standard service agreement...',
    keyTerms: ['payment terms', 'liability', 'termination'],
    risks: ['unlimited liability', 'auto-renewal clause']
  },
  annotations: [
    {
      id: 'ann1',
      type: 'highlight' as const,
      page: 1,
      position: { x: 100, y: 200 },
      content: 'Important clause',
      author: 'Test User',
      createdAt: '2023-11-01T11:00:00Z'
    }
  ]
}

// Mock search results
export const mockSearchResults = [
  {
    id: '1',
    title: 'Case Law Example',
    excerpt: 'This case establishes important precedents...',
    type: 'case' as const,
    relevance: 0.95,
    citation: 'Smith v. Johnson, 2023 Fed. Ct. 123',
    jurisdiction: 'Federal'
  },
  {
    id: '2',
    title: 'Relevant Statute',
    excerpt: 'Section 15.2 outlines the requirements...',
    type: 'statute' as const,
    relevance: 0.87,
    jurisdiction: 'California'
  }
]

// Mock analytics data
export const mockAnalyticsData = {
  metrics: {
    totalDocuments: 156,
    totalSearches: 1247,
    averageResponseTime: 0.34,
    successRate: 0.967
  },
  chartData: [
    { category: 'Contract', value: 45 },
    { category: 'Brief', value: 32 },
    { category: 'Motion', value: 28 },
    { category: 'Other', value: 15 }
  ],
  timeSeriesData: [
    { date: '2023-10-01', value: 45 },
    { date: '2023-10-02', value: 52 },
    { date: '2023-10-03', value: 48 }
  ]
}

// Create test query client
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

// Test wrapper component
interface TestWrapperProps {
  children: React.ReactNode
  initialRoute?: string
  queryClient?: QueryClient
  user?: typeof mockUser | null
}

function TestWrapper({ 
  children, 
  initialRoute = '/', 
  queryClient = createTestQueryClient(),
  user = mockUser 
}: TestWrapperProps) {
  // Mock router history
  if (initialRoute !== '/') {
    window.history.pushState({}, 'Test page', initialRoute)
  }

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider attribute="class" defaultTheme="light">
          <PWAProvider config={{ 
            showInstallPrompt: false, 
            showOfflineIndicator: false 
          }}>
            <div data-testid="test-wrapper">
              {children}
            </div>
          </PWAProvider>
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

// Custom render function
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialRoute?: string
  queryClient?: QueryClient
  user?: typeof mockUser | null
}

export function renderWithProviders(
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
): RenderResult {
  const {
    initialRoute = '/',
    queryClient = createTestQueryClient(),
    user = mockUser,
    ...renderOptions
  } = options

  const Wrapper = ({ children }: { children: React.ReactNode }) => (
    <TestWrapper 
      initialRoute={initialRoute} 
      queryClient={queryClient}
      user={user}
    >
      {children}
    </TestWrapper>
  )

  return render(ui, { wrapper: Wrapper, ...renderOptions })
}

// Utility functions for testing
export const waitForLoadingToFinish = () =>
  new Promise(resolve => setTimeout(resolve, 0))

export function createMockFile(name = 'test.pdf', type = 'application/pdf', size = 1024) {
  const file = new File(['mock content'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

export function createMockEvent(eventInit: Partial<Event> = {}) {
  return {
    preventDefault: jest.fn(),
    stopPropagation: jest.fn(),
    target: { value: '' },
    currentTarget: { value: '' },
    ...eventInit
  } as any
}

export function createMockFormData() {
  const formData = {
    append: jest.fn(),
    delete: jest.fn(),
    get: jest.fn(),
    getAll: jest.fn(),
    has: jest.fn(),
    set: jest.fn(),
    entries: jest.fn(() => []),
    keys: jest.fn(() => []),
    values: jest.fn(() => [])
  }
  return formData as any
}

// Mock intersection observer entry
export function createMockIntersectionObserverEntry(
  isIntersecting = true,
  intersectionRatio = 1
) {
  return {
    isIntersecting,
    intersectionRatio,
    boundingClientRect: {
      bottom: 0,
      height: 0,
      left: 0,
      right: 0,
      top: 0,
      width: 0,
      x: 0,
      y: 0,
      toJSON: jest.fn()
    },
    intersectionRect: {
      bottom: 0,
      height: 0,
      left: 0,
      right: 0,
      top: 0,
      width: 0,
      x: 0,
      y: 0,
      toJSON: jest.fn()
    },
    rootBounds: null,
    target: document.createElement('div'),
    time: Date.now()
  }
}

// Mock canvas context
export function createMockCanvasContext() {
  return {
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
    clip: jest.fn(),
    canvas: {
      width: 800,
      height: 600,
      toDataURL: jest.fn(() => 'data:image/png;base64,mock')
    }
  }
}

// Utility for testing async operations
export async function waitFor(
  callback: () => void | Promise<void>,
  { timeout = 5000, interval = 50 } = {}
): Promise<void> {
  let elapsed = 0
  
  while (elapsed < timeout) {
    try {
      await callback()
      return
    } catch (error) {
      await new Promise(resolve => setTimeout(resolve, interval))
      elapsed += interval
    }
  }
  
  throw new Error(`Timeout after ${timeout}ms`)
}

// Mock localStorage
export const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn()
}

// Mock sessionStorage  
export const mockSessionStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
  length: 0,
  key: jest.fn()
}

// Common test assertions
export const commonAssertions = {
  toBeVisibleAndAccessible: (element: HTMLElement) => {
    expect(element).toBeVisible()
    expect(element).not.toHaveAttribute('aria-hidden', 'true')
  },
  
  toHaveLoadingState: (element: HTMLElement) => {
    expect(
      element.querySelector('[data-testid="loading"]') ||
      element.querySelector('.animate-spin') ||
      element.textContent?.includes('Loading')
    ).toBeTruthy()
  },
  
  toHaveErrorState: (element: HTMLElement, errorMessage?: string) => {
    const errorElement = element.querySelector('[data-testid="error"]') ||
                        element.querySelector('.text-red-') ||
                        element.querySelector('[role="alert"]')
    expect(errorElement).toBeTruthy()
    
    if (errorMessage) {
      expect(element).toHaveTextContent(errorMessage)
    }
  }
}

// Re-export everything from testing library
export * from '@testing-library/react'
export * from '@testing-library/jest-dom'
export * from '@testing-library/user-event'

// Default export
export { renderWithProviders as render }