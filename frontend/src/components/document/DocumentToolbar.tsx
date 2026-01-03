'use client'

import { useState } from 'react'
import { 
  Document as DocumentType, 
  ViewerState, 
  ViewMode, 
  AnnotationTool,
  ExportFormat 
} from '../../types/document'
import { Button } from '../ui'
import {
  MagnifyingGlassIcon,
  ChatBubbleBottomCenterTextIcon,
  PencilIcon,
  EyeDropperIcon,
  DocumentArrowDownIcon,
  PrinterIcon,
  ShareIcon,
  Cog6ToothIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  RectangleStackIcon,
  QueueListIcon,
  Square2StackIcon,
  SparklesIcon as HighlightIcon
} from '@heroicons/react/24/outline'

interface DocumentToolbarProps {
  document: DocumentType
  viewerState: ViewerState
  onPageChange: (page: number) => void
  onZoomIn: () => void
  onZoomOut: () => void
  onZoomReset: () => void
  onToolChange: (tool: AnnotationTool) => void
  onViewModeChange: (mode: ViewMode) => void
  onFullscreenToggle: () => void
  onToggleAnnotationPanel: () => void
  onSearch?: (term: string) => void
  onExport?: (format: ExportFormat) => void
  onPrint?: () => void
  onShare?: () => void
  readonly?: boolean
}

export default function DocumentToolbar({
  document,
  viewerState,
  onPageChange,
  onZoomIn,
  onZoomOut,
  onZoomReset,
  onToolChange,
  onViewModeChange,
  onFullscreenToggle,
  onToggleAnnotationPanel,
  onSearch,
  onExport,
  onPrint,
  onShare,
  readonly = false
}: DocumentToolbarProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [pageInput, setPageInput] = useState(viewerState.currentPage.toString())

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch?.(searchTerm)
  }

  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPageInput(e.target.value)
  }

  const handlePageInputSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const pageNum = parseInt(pageInput)
    if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= viewerState.totalPages) {
      onPageChange(pageNum)
    } else {
      setPageInput(viewerState.currentPage.toString())
    }
  }

  const getToolIcon = (tool: AnnotationTool) => {
    switch (tool) {
      case AnnotationTool.SELECT:
        return MagnifyingGlassIcon
      case AnnotationTool.HIGHLIGHT:
        return HighlightIcon
      case AnnotationTool.NOTE:
        return ChatBubbleBottomCenterTextIcon
      case AnnotationTool.COMMENT:
        return ChatBubbleBottomCenterTextIcon
      case AnnotationTool.DRAWING:
        return PencilIcon
      case AnnotationTool.REDACTION:
        return EyeDropperIcon
      default:
        return MagnifyingGlassIcon
    }
  }

  const getViewModeIcon = (mode: ViewMode) => {
    switch (mode) {
      case ViewMode.SINGLE_PAGE:
        return RectangleStackIcon
      case ViewMode.TWO_PAGE:
        return Square2StackIcon
      case ViewMode.CONTINUOUS:
        return QueueListIcon
      default:
        return RectangleStackIcon
    }
  }

  return (
    <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-white">
      {/* Left Section - Document Info */}
      <div className="flex items-center space-x-4">
        <div className="flex flex-col">
          <h3 className="text-sm font-medium text-gray-900 truncate max-w-xs">
            {document.title || document.fileName}
          </h3>
          <p className="text-xs text-gray-500">
            {Math.round(document.fileSize / 1024)} KB • {viewerState.totalPages} pages
          </p>
        </div>
      </div>

      {/* Center Section - Navigation and Tools */}
      <div className="flex items-center space-x-2">
        {/* Page Navigation */}
        <div className="flex items-center space-x-2 px-3 py-1 bg-gray-50 rounded-md">
          <form onSubmit={handlePageInputSubmit} className="flex items-center">
            <input
              type="text"
              value={pageInput}
              onChange={handlePageInputChange}
              className="w-12 text-center text-sm border-none bg-transparent focus:outline-none"
              onFocus={(e) => e.target.select()}
            />
          </form>
          <span className="text-sm text-gray-500">/ {viewerState.totalPages}</span>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1">
          <Button variant="ghost" size="sm" onClick={onZoomOut}>
            -
          </Button>
          <Button variant="ghost" size="sm" onClick={onZoomReset} className="min-w-16">
            {Math.round(viewerState.zoom * 100)}%
          </Button>
          <Button variant="ghost" size="sm" onClick={onZoomIn}>
            +
          </Button>
        </div>

        {/* View Mode */}
        <div className="flex items-center border rounded-md">
          {Object.values(ViewMode).map((mode) => {
            const IconComponent = getViewModeIcon(mode)
            return (
              <Button
                key={mode}
                variant={viewerState.viewMode === mode ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => onViewModeChange(mode)}
                className="rounded-none first:rounded-l-md last:rounded-r-md"
                title={mode.replace('_', ' ').toLowerCase()}
              >
                <IconComponent className="w-4 h-4" />
              </Button>
            )
          })}
        </div>

        {/* Annotation Tools */}
        {!readonly && (
          <div className="flex items-center border rounded-md">
            {Object.values(AnnotationTool).map((tool) => {
              const IconComponent = getToolIcon(tool)
              return (
                <Button
                  key={tool}
                  variant={viewerState.selectedTool === tool ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => onToolChange(tool)}
                  className="rounded-none first:rounded-l-md last:rounded-r-md"
                  title={tool.replace('_', ' ').toLowerCase()}
                >
                  <IconComponent className="w-4 h-4" />
                </Button>
              )
            })}
          </div>
        )}

        {/* Search */}
        {onSearch && (
          <form onSubmit={handleSearchSubmit} className="relative">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search in document..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </form>
        )}
      </div>

      {/* Right Section - Actions */}
      <div className="flex items-center space-x-2">
        {/* Annotations Panel Toggle */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleAnnotationPanel}
          title="Toggle annotations panel"
        >
          <ChatBubbleBottomCenterTextIcon className="w-4 h-4" />
        </Button>

        {/* Export Menu */}
        {onExport && (
          <div className="relative">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowExportMenu(!showExportMenu)}
              title="Export document"
            >
              <DocumentArrowDownIcon className="w-4 h-4" />
            </Button>
            
            {showExportMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50">
                <div className="py-1">
                  <button
                    onClick={() => {
                      onExport(ExportFormat.PDF)
                      setShowExportMenu(false)
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Export as PDF
                  </button>
                  <button
                    onClick={() => {
                      onExport(ExportFormat.PNG)
                      setShowExportMenu(false)
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Export as PNG
                  </button>
                  <button
                    onClick={() => {
                      onExport(ExportFormat.DOCX)
                      setShowExportMenu(false)
                    }}
                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    Export as DOCX
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Print */}
        {onPrint && (
          <Button variant="ghost" size="sm" onClick={onPrint} title="Print document">
            <PrinterIcon className="w-4 h-4" />
          </Button>
        )}

        {/* Share */}
        {onShare && (
          <Button variant="ghost" size="sm" onClick={onShare} title="Share document">
            <ShareIcon className="w-4 h-4" />
          </Button>
        )}

        {/* Fullscreen */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onFullscreenToggle}
          title={viewerState.isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
        >
          {viewerState.isFullscreen ? (
            <ArrowsPointingInIcon className="w-4 h-4" />
          ) : (
            <ArrowsPointingOutIcon className="w-4 h-4" />
          )}
        </Button>

        {/* Settings */}
        <Button variant="ghost" size="sm" title="Document settings">
          <Cog6ToothIcon className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}