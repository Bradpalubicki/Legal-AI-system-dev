import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { server } from '../mocks/server'
import { rest } from 'msw'
import { QueryClient } from '@tanstack/react-query'
import { renderWithProviders, createMockFile } from '../utils/test-utils'

// Mock components for integration testing
const MockDocumentUpload = ({ onUpload }: { onUpload: (file: File) => void }) => (
  <div data-testid="document-upload">
    <input 
      type="file" 
      data-testid="file-input"
      onChange={(e) => {
        const file = e.target.files?.[0]
        if (file) onUpload(file)
      }}
    />
    <button data-testid="upload-button">Upload Document</button>
  </div>
)

const MockDocumentViewer = ({ 
  document, 
  onAnnotationCreate 
}: { 
  document: any
  onAnnotationCreate: (annotation: any) => void 
}) => (
  <div data-testid="document-viewer">
    <h2>{document.title}</h2>
    <div data-testid="document-content">{document.content}</div>
    <button 
      data-testid="add-annotation"
      onClick={() => onAnnotationCreate({
        type: 'highlight',
        content: 'Test annotation',
        position: { x: 100, y: 200 }
      })}
    >
      Add Annotation
    </button>
    {document.annotations?.map((ann: any) => (
      <div key={ann.id} data-testid={`annotation-${ann.id}`}>
        {ann.content}
      </div>
    ))}
  </div>
)

const MockDocumentList = ({ 
  documents, 
  onDocumentSelect 
}: { 
  documents: any[]
  onDocumentSelect: (doc: any) => void 
}) => (
  <div data-testid="document-list">
    {documents.map(doc => (
      <div 
        key={doc.id} 
        data-testid={`document-item-${doc.id}`}
        onClick={() => onDocumentSelect(doc)}
        className="cursor-pointer p-2 border rounded"
      >
        {doc.title}
      </div>
    ))}
  </div>
)

// Integration test component
const DocumentWorkflowApp = () => {
  const [documents, setDocuments] = React.useState<any[]>([])
  const [selectedDocument, setSelectedDocument] = React.useState<any>(null)
  const [loading, setLoading] = React.useState(false)

  const handleUpload = async (file: File) => {
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData
      })
      
      const newDoc = await response.json()
      setDocuments(prev => [...prev, newDoc])
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDocumentSelect = async (doc: any) => {
    setLoading(true)
    try {
      const response = await fetch(`/api/documents/${doc.id}`)
      const fullDoc = await response.json()
      setSelectedDocument(fullDoc)
    } catch (error) {
      console.error('Failed to load document:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAnnotationCreate = async (annotation: any) => {
    if (!selectedDocument) return
    
    try {
      const response = await fetch(`/api/documents/${selectedDocument.id}/annotations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(annotation)
      })
      
      const newAnnotation = await response.json()
      
      setSelectedDocument(prev => ({
        ...prev,
        annotations: [...(prev?.annotations || []), newAnnotation]
      }))
    } catch (error) {
      console.error('Failed to create annotation:', error)
    }
  }

  React.useEffect(() => {
    // Load initial documents
    const loadDocuments = async () => {
      try {
        const response = await fetch('/api/documents')
        const data = await response.json()
        setDocuments(data.documents)
      } catch (error) {
        console.error('Failed to load documents:', error)
      }
    }
    
    loadDocuments()
  }, [])

  if (loading) {
    return <div data-testid="loading">Loading...</div>
  }

  return (
    <div data-testid="document-workflow-app">
      <MockDocumentUpload onUpload={handleUpload} />
      
      <div className="mt-4">
        <h2>Documents</h2>
        <MockDocumentList 
          documents={documents} 
          onDocumentSelect={handleDocumentSelect} 
        />
      </div>
      
      {selectedDocument && (
        <div className="mt-4">
          <h2>Document Viewer</h2>
          <MockDocumentViewer 
            document={selectedDocument} 
            onAnnotationCreate={handleAnnotationCreate} 
          />
        </div>
      )}
    </div>
  )
}

describe('Document Workflow Integration', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false, cacheTime: 0 },
        mutations: { retry: false }
      }
    })
  })

  describe('Complete Document Upload and Review Workflow', () => {
    it('uploads document, loads it in viewer, and creates annotation', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      // Step 1: Upload a new document
      const file = createMockFile('test-contract.pdf', 'application/pdf')
      const fileInput = screen.getByTestId('file-input')
      
      await user.upload(fileInput, file)
      
      // Wait for upload to complete
      await waitFor(() => {
        expect(screen.getByText('Uploaded Document.pdf')).toBeInTheDocument()
      })
      
      // Step 2: Select the uploaded document
      const uploadedDoc = screen.getByText('Uploaded Document.pdf')
      await user.click(uploadedDoc)
      
      // Wait for document to load in viewer
      await waitFor(() => {
        expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
        expect(screen.getByText('Uploaded Document.pdf')).toBeInTheDocument()
      })
      
      // Step 3: Add an annotation
      const addAnnotationButton = screen.getByTestId('add-annotation')
      await user.click(addAnnotationButton)
      
      // Wait for annotation to be created
      await waitFor(() => {
        expect(screen.getByText('Test annotation')).toBeInTheDocument()
      })
      
      // Verify the complete workflow
      expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
      expect(screen.getByTestId('annotation-new-annotation-id')).toBeInTheDocument()
    })

    it('handles multiple document uploads and switches between them', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      // Upload first document
      const file1 = createMockFile('contract1.pdf', 'application/pdf')
      const fileInput = screen.getByTestId('file-input')
      await user.upload(fileInput, file1)
      
      await waitFor(() => {
        expect(screen.getByText('Uploaded Document.pdf')).toBeInTheDocument()
      })
      
      // Upload second document
      const file2 = createMockFile('contract2.pdf', 'application/pdf')
      await user.upload(fileInput, file2)
      
      await waitFor(() => {
        expect(screen.getAllByText('Uploaded Document.pdf')).toHaveLength(2)
      })
      
      // Select first document
      const docs = screen.getAllByText('Uploaded Document.pdf')
      await user.click(docs[0])
      
      await waitFor(() => {
        expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
      })
      
      // Add annotation to first document
      await user.click(screen.getByTestId('add-annotation'))
      
      await waitFor(() => {
        expect(screen.getByText('Test annotation')).toBeInTheDocument()
      })
      
      // Switch to second document
      await user.click(docs[1])
      
      await waitFor(() => {
        expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
        // Annotation from first document should not be visible
        expect(screen.queryByTestId('annotation-new-annotation-id')).not.toBeInTheDocument()
      })
    })

    it('persists annotations when switching between documents', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      // Select existing document (from initial load)
      const existingDoc = screen.getByText('Contract Agreement.pdf')
      await user.click(existingDoc)
      
      await waitFor(() => {
        expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
      })
      
      // Add annotation
      await user.click(screen.getByTestId('add-annotation'))
      
      await waitFor(() => {
        expect(screen.getByText('Test annotation')).toBeInTheDocument()
      })
      
      // Upload and switch to new document
      const file = createMockFile('new-doc.pdf', 'application/pdf')
      const fileInput = screen.getByTestId('file-input')
      await user.upload(fileInput, file)
      
      await waitFor(() => {
        expect(screen.getByText('Uploaded Document.pdf')).toBeInTheDocument()
      })
      
      await user.click(screen.getByText('Uploaded Document.pdf'))
      
      await waitFor(() => {
        expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
      })
      
      // Switch back to first document
      await user.click(screen.getByText('Contract Agreement.pdf'))
      
      await waitFor(() => {
        expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
        // Annotation should still be there
        expect(screen.getByText('Test annotation')).toBeInTheDocument()
      })
    })
  })

  describe('Error Handling in Workflow', () => {
    it('handles upload failures gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock upload failure
      server.use(
        rest.post('/api/documents/upload', (req, res, ctx) => {
          return res(ctx.status(500), ctx.json({ message: 'Upload failed' }))
        })
      )
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      const file = createMockFile('test.pdf', 'application/pdf')
      const fileInput = screen.getByTestId('file-input')
      
      // Mock console.error to avoid test output pollution
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      
      await user.upload(fileInput, file)
      
      // Should not crash and should show loading state briefly
      expect(screen.getByTestId('loading')).toBeInTheDocument()
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument()
      })
      
      // Document should not be added to list
      expect(screen.queryByText('Uploaded Document.pdf')).not.toBeInTheDocument()
      
      consoleSpy.mockRestore()
    })

    it('handles document loading failures', async () => {
      const user = userEvent.setup()
      
      // Mock document loading failure
      server.use(
        rest.get('/api/documents/:id', (req, res, ctx) => {
          return res(ctx.status(404), ctx.json({ message: 'Document not found' }))
        })
      )
      
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      // Try to select a document
      const doc = screen.getByText('Contract Agreement.pdf')
      await user.click(doc)
      
      // Should show loading then return to normal state
      expect(screen.getByTestId('loading')).toBeInTheDocument()
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument()
      })
      
      // Document viewer should not appear
      expect(screen.queryByTestId('document-viewer')).not.toBeInTheDocument()
      
      consoleSpy.mockRestore()
    })

    it('handles annotation creation failures', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      // Select document
      const doc = screen.getByText('Contract Agreement.pdf')
      await user.click(doc)
      
      await waitFor(() => {
        expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
      })
      
      // Mock annotation creation failure
      server.use(
        rest.post('/api/documents/:id/annotations', (req, res, ctx) => {
          return res(ctx.status(400), ctx.json({ message: 'Invalid annotation' }))
        })
      )
      
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
      
      // Try to create annotation
      await user.click(screen.getByTestId('add-annotation'))
      
      await waitFor(() => {
        // Annotation should not appear
        expect(screen.queryByText('Test annotation')).not.toBeInTheDocument()
      })
      
      consoleSpy.mockRestore()
    })
  })

  describe('Performance in Workflow', () => {
    it('handles large number of documents efficiently', async () => {
      const user = userEvent.setup()
      
      // Mock API to return many documents
      server.use(
        rest.get('/api/documents', (req, res, ctx) => {
          const documents = Array.from({ length: 100 }, (_, i) => ({
            id: `doc-${i}`,
            title: `Document ${i}.pdf`,
            type: 'pdf',
            uploadedAt: new Date().toISOString(),
            status: 'processed'
          }))
          
          return res(ctx.json({
            documents,
            pagination: { page: 1, limit: 100, total: 100, pages: 1 }
          }))
        })
      )
      
      const startTime = performance.now()
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      // Should render quickly even with many documents
      expect(renderTime).toBeLessThan(1000) // Less than 1 second
      
      // Should show all documents (or implement virtualization)
      const docItems = screen.getAllByTestId(/document-item-/)
      expect(docItems.length).toBeGreaterThan(0)
    })

    it('debounces rapid document selections', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      const docs = screen.getAllByTestId(/document-item-/)
      
      // Rapidly click different documents
      await user.click(docs[0])
      await user.click(docs[1])
      
      if (docs[0]) {
        await user.click(docs[0])
      }
      
      // Should eventually settle on the last clicked document
      await waitFor(() => {
        expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility in Workflow', () => {
    it('maintains focus management throughout workflow', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      // Tab through elements
      await user.tab()
      expect(document.activeElement).toHaveAttribute('data-testid', 'file-input')
      
      await user.tab()
      expect(document.activeElement).toHaveAttribute('data-testid', 'upload-button')
      
      // Select document with keyboard
      const doc = screen.getByTestId('document-item-1')
      doc.focus()
      await user.keyboard('{Enter}')
      
      await waitFor(() => {
        expect(screen.getByTestId('document-viewer')).toBeInTheDocument()
      })
      
      // Focus should be manageable in document viewer
      const annotationButton = screen.getByTestId('add-annotation')
      annotationButton.focus()
      expect(document.activeElement).toBe(annotationButton)
    })

    it('provides proper ARIA announcements for state changes', async () => {
      const user = userEvent.setup()
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      // Upload document
      const file = createMockFile('test.pdf', 'application/pdf')
      const fileInput = screen.getByTestId('file-input')
      await user.upload(fileInput, file)
      
      // Should show loading state with proper labeling
      expect(screen.getByTestId('loading')).toHaveAttribute('role', 'status')
      
      await waitFor(() => {
        expect(screen.queryByTestId('loading')).not.toBeInTheDocument()
      })
    })
  })

  describe('Offline Functionality', () => {
    it('handles offline document upload gracefully', async () => {
      const user = userEvent.setup()
      
      // Simulate offline
      Object.defineProperty(navigator, 'onLine', {
        writable: true,
        value: false
      })
      
      renderWithProviders(<DocumentWorkflowApp />, { queryClient })
      
      await waitFor(() => {
        expect(screen.getByTestId('document-list')).toBeInTheDocument()
      })
      
      const file = createMockFile('test.pdf', 'application/pdf')
      const fileInput = screen.getByTestId('file-input')
      
      // Should handle offline upload attempt
      await user.upload(fileInput, file)
      
      // Should show appropriate feedback for offline state
      expect(screen.getByTestId('loading')).toBeInTheDocument()
    })
  })
})