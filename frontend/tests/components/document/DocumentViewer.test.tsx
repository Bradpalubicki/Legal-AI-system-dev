import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DocumentViewer from '../../../src/components/document/DocumentViewer'
import { mockDocument, createMockFile } from '../../utils/test-utils'
import { AnnotationType } from '../../../src/types/document'

// Mock PDF worker
jest.mock('pdfjs-dist/legacy/build/pdf.worker.min.js', () => ({}))

describe('DocumentViewer', () => {
  const defaultProps = {
    document: mockDocument,
    onAnnotationCreate: jest.fn(),
    onAnnotationUpdate: jest.fn(),
    onAnnotationDelete: jest.fn(),
    onDocumentUpdate: jest.fn()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders document viewer with basic elements', () => {
      render(<DocumentViewer {...defaultProps} />)
      
      expect(screen.getByText(mockDocument.title)).toBeInTheDocument()
      expect(screen.getByText('Page 1 of 1')).toBeInTheDocument()
      expect(screen.getByRole('toolbar')).toBeInTheDocument()
    })

    it('shows loading state when document is loading', () => {
      render(
        <DocumentViewer 
          {...defaultProps} 
          document={{ ...mockDocument, status: 'processing' }}
        />
      )
      
      expect(screen.getByText(/processing/i)).toBeInTheDocument()
    })

    it('displays error state when document fails to load', () => {
      render(
        <DocumentViewer 
          {...defaultProps} 
          document={{ ...mockDocument, status: 'error' }}
        />
      )
      
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })

    it('renders existing annotations', () => {
      render(<DocumentViewer {...defaultProps} />)
      
      // Check if annotation is displayed
      expect(screen.getByText('Important clause')).toBeInTheDocument()
    })
  })

  describe('Toolbar Interactions', () => {
    it('handles zoom controls', async () => {
      const user = userEvent.setup()
      render(<DocumentViewer {...defaultProps} />)
      
      const zoomInButton = screen.getByLabelText(/zoom in/i)
      const zoomOutButton = screen.getByLabelText(/zoom out/i)
      
      await user.click(zoomInButton)
      await user.click(zoomOutButton)
      
      expect(zoomInButton).toBeInTheDocument()
      expect(zoomOutButton).toBeInTheDocument()
    })

    it('switches between annotation tools', async () => {
      const user = userEvent.setup()
      render(<DocumentViewer {...defaultProps} />)
      
      const highlightTool = screen.getByLabelText(/highlight/i)
      const noteTool = screen.getByLabelText(/note/i)
      
      await user.click(highlightTool)
      expect(highlightTool).toHaveClass('bg-yellow-100')
      
      await user.click(noteTool)
      expect(noteTool).toHaveClass('bg-blue-100')
    })

    it('toggles fullscreen mode', async () => {
      const user = userEvent.setup()
      
      // Mock fullscreen API
      document.exitFullscreen = jest.fn()
      HTMLElement.prototype.requestFullscreen = jest.fn()
      
      render(<DocumentViewer {...defaultProps} />)
      
      const fullscreenButton = screen.getByLabelText(/fullscreen/i)
      await user.click(fullscreenButton)
      
      expect(HTMLElement.prototype.requestFullscreen).toHaveBeenCalled()
    })
  })

  describe('Annotation Creation', () => {
    it('creates highlight annotation on text selection', async () => {
      const user = userEvent.setup()
      const mockOnAnnotationCreate = jest.fn()
      
      render(
        <DocumentViewer 
          {...defaultProps} 
          onAnnotationCreate={mockOnAnnotationCreate}
        />
      )
      
      // Simulate text selection
      const textElement = screen.getByText(/mock document content/i)
      await user.selectText(textElement)
      
      // Click highlight tool and create annotation
      const highlightTool = screen.getByLabelText(/highlight/i)
      await user.click(highlightTool)
      
      fireEvent.mouseDown(textElement, { clientX: 100, clientY: 200 })
      fireEvent.mouseUp(textElement, { clientX: 200, clientY: 200 })
      
      await waitFor(() => {
        expect(mockOnAnnotationCreate).toHaveBeenCalledWith(
          expect.objectContaining({
            type: AnnotationType.HIGHLIGHT,
            position: expect.objectContaining({
              x: expect.any(Number),
              y: expect.any(Number)
            })
          })
        )
      })
    })

    it('creates note annotation with text input', async () => {
      const user = userEvent.setup()
      const mockOnAnnotationCreate = jest.fn()
      
      render(
        <DocumentViewer 
          {...defaultProps} 
          onAnnotationCreate={mockOnAnnotationCreate}
        />
      )
      
      // Click note tool
      const noteTool = screen.getByLabelText(/note/i)
      await user.click(noteTool)
      
      // Click on document to place note
      const documentCanvas = screen.getByRole('img', { name: /document page/i })
      fireEvent.click(documentCanvas, { clientX: 150, clientY: 250 })
      
      // Enter note text
      const noteInput = screen.getByLabelText(/note text/i)
      await user.type(noteInput, 'This is a test note')
      
      const saveButton = screen.getByRole('button', { name: /save note/i })
      await user.click(saveButton)
      
      expect(mockOnAnnotationCreate).toHaveBeenCalledWith(
        expect.objectContaining({
          type: AnnotationType.NOTE,
          content: 'This is a test note',
          position: { x: 150, y: 250 }
        })
      )
    })

    it('creates drawing annotation', async () => {
      const user = userEvent.setup()
      const mockOnAnnotationCreate = jest.fn()
      
      render(
        <DocumentViewer 
          {...defaultProps} 
          onAnnotationCreate={mockOnAnnotationCreate}
        />
      )
      
      // Click drawing tool
      const drawingTool = screen.getByLabelText(/drawing/i)
      await user.click(drawingTool)
      
      // Simulate drawing
      const canvas = screen.getByRole('img', { name: /document page/i })
      fireEvent.mouseDown(canvas, { clientX: 100, clientY: 100 })
      fireEvent.mouseMove(canvas, { clientX: 150, clientY: 150 })
      fireEvent.mouseUp(canvas, { clientX: 200, clientY: 200 })
      
      await waitFor(() => {
        expect(mockOnAnnotationCreate).toHaveBeenCalledWith(
          expect.objectContaining({
            type: AnnotationType.DRAWING,
            drawingData: expect.any(String)
          })
        )
      })
    })
  })

  describe('Annotation Management', () => {
    it('updates existing annotation', async () => {
      const user = userEvent.setup()
      const mockOnAnnotationUpdate = jest.fn()
      
      render(
        <DocumentViewer 
          {...defaultProps} 
          onAnnotationUpdate={mockOnAnnotationUpdate}
        />
      )
      
      // Click on existing annotation
      const annotation = screen.getByText('Important clause')
      await user.click(annotation)
      
      // Edit annotation
      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)
      
      const input = screen.getByDisplayValue('Important clause')
      await user.clear(input)
      await user.type(input, 'Updated clause text')
      
      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)
      
      expect(mockOnAnnotationUpdate).toHaveBeenCalledWith(
        'ann1',
        expect.objectContaining({
          content: 'Updated clause text'
        })
      )
    })

    it('deletes annotation', async () => {
      const user = userEvent.setup()
      const mockOnAnnotationDelete = jest.fn()
      
      render(
        <DocumentViewer 
          {...defaultProps} 
          onAnnotationDelete={mockOnAnnotationDelete}
        />
      )
      
      // Click on existing annotation
      const annotation = screen.getByText('Important clause')
      await user.click(annotation)
      
      // Delete annotation
      const deleteButton = screen.getByRole('button', { name: /delete/i })
      await user.click(deleteButton)
      
      // Confirm deletion
      const confirmButton = screen.getByRole('button', { name: /confirm/i })
      await user.click(confirmButton)
      
      expect(mockOnAnnotationDelete).toHaveBeenCalledWith('ann1')
    })

    it('shows annotation details panel', async () => {
      const user = userEvent.setup()
      render(<DocumentViewer {...defaultProps} />)
      
      const annotation = screen.getByText('Important clause')
      await user.click(annotation)
      
      expect(screen.getByText('Annotation Details')).toBeInTheDocument()
      expect(screen.getByText('Test User')).toBeInTheDocument()
      expect(screen.getByText(/Nov 1, 2023/)).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('navigates between pages in multi-page document', async () => {
      const user = userEvent.setup()
      const multiPageDocument = {
        ...mockDocument,
        totalPages: 3
      }
      
      render(<DocumentViewer {...defaultProps} document={multiPageDocument} />)
      
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument()
      
      const nextButton = screen.getByLabelText(/next page/i)
      await user.click(nextButton)
      
      expect(screen.getByText('Page 2 of 3')).toBeInTheDocument()
      
      const prevButton = screen.getByLabelText(/previous page/i)
      await user.click(prevButton)
      
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument()
    })

    it('disables navigation buttons at document boundaries', () => {
      render(<DocumentViewer {...defaultProps} />)
      
      const prevButton = screen.getByLabelText(/previous page/i)
      const nextButton = screen.getByLabelText(/next page/i)
      
      expect(prevButton).toBeDisabled()
      expect(nextButton).toBeDisabled()
    })
  })

  describe('Keyboard Shortcuts', () => {
    it('handles keyboard shortcuts', async () => {
      const user = userEvent.setup()
      render(<DocumentViewer {...defaultProps} />)
      
      // Test zoom shortcuts
      await user.keyboard('{Control>}+{/Control}') // Zoom in
      await user.keyboard('{Control>}-{/Control}') // Zoom out
      
      // Test tool shortcuts
      await user.keyboard('h') // Highlight tool
      await user.keyboard('n') // Note tool
      await user.keyboard('d') // Drawing tool
      
      // Verify tool selection
      expect(screen.getByLabelText(/highlight/i)).toHaveClass('bg-yellow-100')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels and roles', () => {
      render(<DocumentViewer {...defaultProps} />)
      
      expect(screen.getByRole('toolbar')).toHaveAccessibleName()
      expect(screen.getByRole('img', { name: /document page/i })).toBeInTheDocument()
      expect(screen.getByLabelText(/zoom in/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/zoom out/i)).toBeInTheDocument()
    })

    it('supports keyboard navigation', async () => {
      const user = userEvent.setup()
      render(<DocumentViewer {...defaultProps} />)
      
      // Tab through controls
      await user.tab()
      expect(document.activeElement).toHaveAttribute('aria-label', expect.stringContaining('zoom'))
      
      await user.tab()
      expect(document.activeElement).toHaveAttribute('aria-label', expect.stringContaining('zoom'))
    })

    it('announces page changes to screen readers', async () => {
      const user = userEvent.setup()
      const multiPageDocument = {
        ...mockDocument,
        totalPages: 2
      }
      
      render(<DocumentViewer {...defaultProps} document={multiPageDocument} />)
      
      const nextButton = screen.getByLabelText(/next page/i)
      await user.click(nextButton)
      
      const announcement = screen.getByRole('status')
      expect(announcement).toHaveTextContent(/page 2 of 2/i)
    })
  })

  describe('Error Handling', () => {
    it('handles annotation creation errors gracefully', async () => {
      const user = userEvent.setup()
      const mockOnAnnotationCreate = jest.fn().mockRejectedValue(new Error('Failed to create'))
      
      render(
        <DocumentViewer 
          {...defaultProps} 
          onAnnotationCreate={mockOnAnnotationCreate}
        />
      )
      
      // Try to create annotation
      const highlightTool = screen.getByLabelText(/highlight/i)
      await user.click(highlightTool)
      
      const canvas = screen.getByRole('img', { name: /document page/i })
      fireEvent.click(canvas, { clientX: 100, clientY: 100 })
      
      await waitFor(() => {
        expect(screen.getByText(/failed to create annotation/i)).toBeInTheDocument()
      })
    })

    it('shows error message for unsupported file types', () => {
      const unsupportedDocument = {
        ...mockDocument,
        type: 'unsupported',
        status: 'error'
      }
      
      render(<DocumentViewer {...defaultProps} document={unsupportedDocument} />)
      
      expect(screen.getByText(/unsupported file type/i)).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('debounces annotation updates', async () => {
      const user = userEvent.setup()
      const mockOnAnnotationUpdate = jest.fn()
      
      render(
        <DocumentViewer 
          {...defaultProps} 
          onAnnotationUpdate={mockOnAnnotationUpdate}
        />
      )
      
      // Click on annotation and edit rapidly
      const annotation = screen.getByText('Important clause')
      await user.click(annotation)
      
      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)
      
      const input = screen.getByDisplayValue('Important clause')
      
      // Type rapidly
      await user.type(input, 'abc')
      
      // Should debounce updates
      expect(mockOnAnnotationUpdate).not.toHaveBeenCalled()
      
      // Wait for debounce
      await waitFor(() => {
        expect(mockOnAnnotationUpdate).toHaveBeenCalledTimes(1)
      }, { timeout: 1000 })
    })

    it('virtualizes annotations for large documents', () => {
      const documentWithManyAnnotations = {
        ...mockDocument,
        annotations: Array.from({ length: 100 }, (_, i) => ({
          id: `ann${i}`,
          type: 'highlight' as const,
          page: Math.floor(i / 10) + 1,
          position: { x: 100 + i, y: 200 + i },
          content: `Annotation ${i}`,
          author: 'Test User',
          createdAt: new Date().toISOString()
        }))
      }
      
      render(<DocumentViewer {...defaultProps} document={documentWithManyAnnotations} />)
      
      // Should only render visible annotations
      const visibleAnnotations = screen.getAllByText(/annotation \d+/i)
      expect(visibleAnnotations.length).toBeLessThan(50) // Should be virtualized
    })
  })
})