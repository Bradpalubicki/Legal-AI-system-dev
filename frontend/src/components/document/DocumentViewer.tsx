'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
// TEMPORARILY DISABLED: import { Document, Page, pdfjs } from 'react-pdf'
// TEMPORARILY DISABLED: import 'react-pdf/dist/esm/Page/AnnotationLayer.css'
// TEMPORARILY DISABLED: import 'react-pdf/dist/esm/Page/TextLayer.css'
import { 
  Document as DocumentType, 
  ViewerState, 
  ViewMode, 
  AnnotationTool,
  Annotation 
} from '../../types/document'
// TEMPORARILY DISABLED: import DocumentToolbar from './DocumentToolbar'
// TEMPORARILY DISABLED: import AnnotationPanel from './AnnotationPanel'
// TEMPORARILY DISABLED: import AnnotationLayer from './AnnotationLayer'
import { Card } from '../ui'
import { 
  ChevronLeftIcon, 
  ChevronRightIcon,
  MagnifyingGlassMinusIcon,
  MagnifyingGlassPlusIcon
} from '@heroicons/react/24/outline'

// TEMPORARILY DISABLED: Configure PDF.js worker
// pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/legacy/build/pdf.worker.min.js`

interface DocumentViewerProps {
  document: DocumentType
  annotations?: Annotation[]
  onAnnotationCreate?: (annotation: Partial<Annotation>) => void
  onAnnotationUpdate?: (id: string, updates: Partial<Annotation>) => void
  onAnnotationDelete?: (id: string) => void
  onExport?: (format?: any) => void
  onPrint?: () => void
  onShare?: () => void
  readonly?: boolean
  showAnnotations?: boolean
  showToolbar?: boolean
  className?: string
}

export default function DocumentViewer({
  document,
  annotations = [],
  onAnnotationCreate,
  onAnnotationUpdate,
  onAnnotationDelete,
  readonly = false,
  showAnnotations = true,
  showToolbar = true,
  className = ''
}: DocumentViewerProps) {
  const [viewerState, setViewerState] = useState<ViewerState>({
    currentPage: 1,
    totalPages: 0,
    zoom: 1.0,
    rotation: 0,
    viewMode: ViewMode.SINGLE_PAGE,
    isFullscreen: false,
    selectedTool: AnnotationTool.SELECT,
    selectedAnnotations: [],
    searchTerm: '',
    searchResults: [],
    currentSearchIndex: 0
  })

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showAnnotationPanel, setShowAnnotationPanel] = useState(false)
  
  const containerRef = useRef<HTMLDivElement>(null)
  const documentRef = useRef<HTMLDivElement>(null)

  const onDocumentLoadSuccess = useCallback((pdf: any) => {
    setViewerState(prev => ({
      ...prev,
      totalPages: document.pageCount || 5 // Use document.pageCount or default to 5
    }))
    setIsLoading(false)
    setError(null)
  }, [document.pageCount])

  const onDocumentLoadError = useCallback((error: Error) => {
    setError(error.message)
    setIsLoading(false)
  }, [])

  const handlePageChange = useCallback((pageNumber: number) => {
    setViewerState(prev => ({
      ...prev,
      currentPage: Math.max(1, Math.min(pageNumber, prev.totalPages))
    }))
  }, [])

  const handleZoomIn = useCallback(() => {
    setViewerState(prev => ({
      ...prev,
      zoom: Math.min(prev.zoom * 1.2, 3.0)
    }))
  }, [])

  const handleZoomOut = useCallback(() => {
    setViewerState(prev => ({
      ...prev,
      zoom: Math.max(prev.zoom / 1.2, 0.3)
    }))
  }, [])

  const handleZoomReset = useCallback(() => {
    setViewerState(prev => ({ ...prev, zoom: 1.0 }))
  }, [])

  const handleToolChange = useCallback((tool: AnnotationTool) => {
    setViewerState(prev => ({ ...prev, selectedTool: tool }))
  }, [])

  const handleViewModeChange = useCallback((mode: ViewMode) => {
    setViewerState(prev => ({ ...prev, viewMode: mode }))
  }, [])

  const handleFullscreenToggle = useCallback(() => {
    setViewerState(prev => ({ ...prev, isFullscreen: !prev.isFullscreen }))
  }, [])

  const handleAnnotationSelect = useCallback((annotationId: string) => {
    setViewerState(prev => ({
      ...prev,
      selectedAnnotations: prev.selectedAnnotations.includes(annotationId)
        ? prev.selectedAnnotations.filter(id => id !== annotationId)
        : [...prev.selectedAnnotations, annotationId]
    }))
  }, [])

  const getCurrentPageAnnotations = useCallback(() => {
    return annotations.filter(annotation => annotation.page === viewerState.currentPage)
  }, [annotations, viewerState.currentPage])

  // Simulate document loading since PDF rendering is disabled
  useEffect(() => {
    if (document) {
      setIsLoading(true)
      setTimeout(() => {
        onDocumentLoadSuccess({ numPages: document.pageCount || 5 })
      }, 1000) // Simulate loading delay
    }
  }, [document, onDocumentLoadSuccess])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }

      switch (e.key) {
        case 'ArrowLeft':
        case 'PageUp':
          e.preventDefault()
          handlePageChange(viewerState.currentPage - 1)
          break
        case 'ArrowRight':
        case 'PageDown':
          e.preventDefault()
          handlePageChange(viewerState.currentPage + 1)
          break
        case '=':
        case '+':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault()
            handleZoomIn()
          }
          break
        case '-':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault()
            handleZoomOut()
          }
          break
        case '0':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault()
            handleZoomReset()
          }
          break
        case 'f':
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault()
            // Focus search input
          }
          break
        case 'Escape':
          if (viewerState.isFullscreen) {
            handleFullscreenToggle()
          }
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [viewerState.currentPage, viewerState.isFullscreen, handlePageChange, handleZoomIn, handleZoomOut, handleZoomReset, handleFullscreenToggle])

  if (error) {
    return (
      <Card className="p-8 text-center">
        <div className="text-red-600 mb-4">
          <svg className="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to Load Document</h3>
          <p className="text-gray-600">{error}</p>
        </div>
      </Card>
    )
  }

  return (
    <div 
      ref={containerRef}
      className={`document-viewer ${viewerState.isFullscreen ? 'fixed inset-0 z-50 bg-white' : ''} ${className}`}
    >
      {showToolbar && (
        <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-white">
          <div className="flex items-center space-x-4">
            <div className="text-sm font-medium text-gray-900">
              Document Toolbar Placeholder
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowAnnotationPanel(!showAnnotationPanel)}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Toggle Annotations
            </button>
            <button
              onClick={handleFullscreenToggle}
              className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              {viewerState.isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            </button>
          </div>
        </div>
      )}

      <div className="flex h-full">
        <div className="flex-1 relative overflow-auto bg-gray-100">
          {/* Loading State */}
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading document...</p>
              </div>
            </div>
          )}

          {/* Document Container */}
          <div 
            ref={documentRef}
            className="relative"
            style={{
              transform: `scale(${viewerState.zoom}) rotate(${viewerState.rotation}deg)`,
              transformOrigin: 'top center',
              transition: 'transform 0.3s ease'
            }}
          >
            {/* TEMPORARILY DISABLED: PDF Rendering - Using placeholder */}
            <div className="flex flex-col items-center">
              <div className="bg-white shadow-lg p-8 text-center max-w-md">
                <div className="text-gray-400 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Document Viewer</h3>
                <p className="text-gray-600 text-sm mb-4">
                  {document.fileName || document.title}
                </p>
                <p className="text-xs text-gray-500">
                  PDF rendering temporarily disabled for testing
                </p>
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-600">
                    <strong>File:</strong> {document.fileName}<br/>
                    <strong>Size:</strong> {Math.round(document.fileSize / 1024)} KB<br/>
                    <strong>Pages:</strong> {document.pageCount || 'Unknown'}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Page Navigation */}
          {viewerState.viewMode === ViewMode.SINGLE_PAGE && (
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex items-center space-x-2 bg-white rounded-lg shadow-lg px-4 py-2">
              <button
                onClick={() => handlePageChange(viewerState.currentPage - 1)}
                disabled={viewerState.currentPage <= 1}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeftIcon className="w-5 h-5" />
              </button>
              
              <span className="text-sm font-medium px-3">
                {viewerState.currentPage} / {viewerState.totalPages}
              </span>
              
              <button
                onClick={() => handlePageChange(viewerState.currentPage + 1)}
                disabled={viewerState.currentPage >= viewerState.totalPages}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRightIcon className="w-5 h-5" />
              </button>
            </div>
          )}

          {/* Zoom Controls */}
          <div className="absolute bottom-4 right-4 flex flex-col space-y-2 bg-white rounded-lg shadow-lg p-2">
            <button
              onClick={handleZoomIn}
              className="p-2 rounded hover:bg-gray-100"
              title="Zoom In"
            >
              <MagnifyingGlassPlusIcon className="w-4 h-4" />
            </button>
            <button
              onClick={handleZoomReset}
              className="p-2 rounded hover:bg-gray-100 text-xs font-medium"
              title="Reset Zoom"
            >
              {Math.round(viewerState.zoom * 100)}%
            </button>
            <button
              onClick={handleZoomOut}
              className="p-2 rounded hover:bg-gray-100"
              title="Zoom Out"
            >
              <MagnifyingGlassMinusIcon className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Annotation Panel */}
        {showAnnotations && showAnnotationPanel && (
          <div className="w-80 bg-white border-l border-gray-200 flex flex-col h-full">
            <div className="p-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">Annotation Panel Placeholder</h3>
                <button
                  onClick={() => setShowAnnotationPanel(false)}
                  className="px-2 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Close
                </button>
              </div>
            </div>
            <div className="flex-1 p-4">
              <p className="text-gray-600">Annotations would appear here.</p>
              <p className="text-xs text-gray-500 mt-2">
                Current page: {viewerState.currentPage}<br/>
                Total annotations: {annotations.length}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}