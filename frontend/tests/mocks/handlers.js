import { rest } from 'msw'

// Mock API responses for testing
export const handlers = [
  // Authentication endpoints
  rest.post('/api/auth/login', (req, res, ctx) => {
    const { email, password } = req.body
    
    if (email === 'test@example.com' && password === 'password123') {
      return res(
        ctx.status(200),
        ctx.json({
          user: {
            id: '1',
            email: 'test@example.com',
            name: 'Test User',
            role: 'attorney'
          },
          token: 'mock-jwt-token'
        })
      )
    }
    
    return res(
      ctx.status(401),
      ctx.json({ message: 'Invalid credentials' })
    )
  }),

  rest.post('/api/auth/logout', (req, res, ctx) => {
    return res(ctx.status(200), ctx.json({ message: 'Logged out successfully' }))
  }),

  // Document endpoints
  rest.get('/api/documents', (req, res, ctx) => {
    const page = req.url.searchParams.get('page') || '1'
    const limit = req.url.searchParams.get('limit') || '10'
    
    return res(
      ctx.status(200),
      ctx.json({
        documents: [
          {
            id: '1',
            title: 'Contract Agreement.pdf',
            type: 'contract',
            size: 2048576,
            uploadedAt: '2023-11-01T10:00:00Z',
            status: 'processed',
            annotations: []
          },
          {
            id: '2',
            title: 'Legal Brief.docx',
            type: 'brief',
            size: 1024768,
            uploadedAt: '2023-11-02T14:30:00Z',
            status: 'processing',
            annotations: []
          }
        ],
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total: 25,
          pages: 3
        }
      })
    )
  }),

  rest.get('/api/documents/:id', (req, res, ctx) => {
    const { id } = req.params
    
    return res(
      ctx.status(200),
      ctx.json({
        id,
        title: 'Contract Agreement.pdf',
        type: 'contract',
        size: 2048576,
        uploadedAt: '2023-11-01T10:00:00Z',
        status: 'processed',
        content: 'Mock document content...',
        analysis: {
          summary: 'This is a standard service agreement...',
          keyTerms: ['payment terms', 'liability', 'termination'],
          risks: ['unlimited liability', 'auto-renewal clause']
        },
        annotations: [
          {
            id: 'ann1',
            type: 'highlight',
            page: 1,
            position: { x: 100, y: 200 },
            content: 'Important clause',
            author: 'Test User',
            createdAt: '2023-11-01T11:00:00Z'
          }
        ]
      })
    )
  }),

  rest.post('/api/documents/upload', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        id: 'new-doc-id',
        title: 'Uploaded Document.pdf',
        status: 'uploaded',
        uploadedAt: new Date().toISOString()
      })
    )
  }),

  rest.post('/api/documents/:id/annotations', (req, res, ctx) => {
    const { id } = req.params
    const annotation = req.body
    
    return res(
      ctx.status(201),
      ctx.json({
        id: 'new-annotation-id',
        ...annotation,
        documentId: id,
        createdAt: new Date().toISOString(),
        author: 'Test User'
      })
    )
  }),

  // Search endpoints
  rest.get('/api/search', (req, res, ctx) => {
    const query = req.url.searchParams.get('q')
    const type = req.url.searchParams.get('type')
    
    if (!query) {
      return res(ctx.status(400), ctx.json({ message: 'Query parameter required' }))
    }
    
    return res(
      ctx.status(200),
      ctx.json({
        results: [
          {
            id: '1',
            title: `Case Law regarding "${query}"`,
            excerpt: 'This case establishes important precedents...',
            type: 'case',
            relevance: 0.95,
            citation: 'Smith v. Johnson, 2023 Fed. Ct. 123',
            jurisdiction: 'Federal'
          },
          {
            id: '2',
            title: `Statute about "${query}"`,
            excerpt: 'Section 15.2 outlines the requirements...',
            type: 'statute',
            relevance: 0.87,
            jurisdiction: 'California'
          }
        ],
        totalResults: 2,
        searchTime: 0.15
      })
    )
  }),

  // Analytics endpoints
  rest.get('/api/analytics/dashboard', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({
        metrics: {
          totalDocuments: 156,
          totalSearches: 1247,
          averageResponseTime: 0.34,
          successRate: 0.967
        },
        trends: {
          documentsOverTime: [
            { date: '2023-10-01', value: 45 },
            { date: '2023-10-02', value: 52 },
            { date: '2023-10-03', value: 48 }
          ],
          searchesOverTime: [
            { date: '2023-10-01', value: 234 },
            { date: '2023-10-02', value: 267 },
            { date: '2023-10-03', value: 245 }
          ]
        }
      })
    )
  }),

  // Notification endpoints
  rest.post('/api/notifications/subscribe', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ message: 'Subscription created successfully' })
    )
  }),

  rest.post('/api/notifications/unsubscribe', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ message: 'Subscription removed successfully' })
    )
  }),

  // Error simulation endpoints
  rest.get('/api/error/500', (req, res, ctx) => {
    return res(ctx.status(500), ctx.json({ message: 'Internal server error' }))
  }),

  rest.get('/api/error/timeout', (req, res, ctx) => {
    return res(ctx.delay(5000), ctx.status(408), ctx.json({ message: 'Request timeout' }))
  }),

  // Default handler for unmatched requests
  rest.all('*', (req, res, ctx) => {
    console.error(`Unhandled ${req.method} request to ${req.url.href}`)
    return res(ctx.status(404), ctx.json({ message: 'API endpoint not found' }))
  })
]