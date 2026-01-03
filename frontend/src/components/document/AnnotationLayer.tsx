'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
// TEMPORARILY DISABLED: import { fabric } from 'fabric'
// TEMPORARILY DISABLED: import { v4 as uuidv4 } from 'uuid'
import {
  Annotation,
  AnnotationType,
  AnnotationTool,
  AnnotationPosition,
  AnnotationStyle
} from '../../types/document'

interface AnnotationLayerProps {
  annotations: Annotation[]
  pageNumber: number
  selectedTool: AnnotationTool
  selectedAnnotations: string[]
  onAnnotationCreate?: (annotation: Partial<Annotation>) => void
  onAnnotationSelect?: (annotationId: string) => void
  onAnnotationUpdate?: (id: string, updates: Partial<Annotation>) => void
  onAnnotationDelete?: (id: string) => void
  annotationStyle: AnnotationStyle
  readonly?: boolean
  className?: string
}

export default function AnnotationLayer({
  annotations,
  pageNumber,
  selectedTool,
  selectedAnnotations,
  onAnnotationCreate,
  onAnnotationSelect,
  onAnnotationUpdate,
  onAnnotationDelete,
  annotationStyle,
  readonly = false,
  className = ''
}: AnnotationLayerProps) {
  const [isDrawing, setIsDrawing] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // Filter annotations for current page
  const currentPageAnnotations = annotations.filter(ann => ann.page === pageNumber)

  // Simple placeholder implementation without fabric.js
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (readonly) return
    setIsDrawing(true)
    // Placeholder: would create annotation based on selectedTool
    console.log('Annotation creation started with tool:', selectedTool)
  }, [readonly, selectedTool])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDrawing) return
    // Placeholder: would update annotation during drawing
  }, [isDrawing])

  const handleMouseUp = useCallback(() => {
    if (isDrawing) {
      setIsDrawing(false)
      // Placeholder: would finalize annotation creation
      console.log('Annotation creation completed')
    }
  }, [isDrawing])

  return (
    <div
      ref={containerRef}
      className={`absolute inset-0 pointer-events-auto ${className}`}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Render existing annotations as simple overlays */}
      {currentPageAnnotations.map((annotation) => (
        <div
          key={annotation.id}
          className={`absolute border-2 cursor-pointer ${
            selectedAnnotations.includes(annotation.id)
              ? 'border-blue-500 bg-blue-100'
              : 'border-yellow-400 bg-yellow-100'
          }`}
          style={{
            left: `${annotation.position.x}%`,
            top: `${annotation.position.y}%`,
            width: `${annotation.position.width}%`,
            height: `${annotation.position.height}%`,
            opacity: annotationStyle.opacity || 0.7
          }}
          onClick={() => onAnnotationSelect?.(annotation.id)}
          title={annotation.content}
        >
          {annotation.type === AnnotationType.NOTE && (
            <div className="p-1 text-xs bg-white rounded shadow max-w-48 truncate">
              {annotation.content}
            </div>
          )}
        </div>
      ))}

      {/* Tool cursor indicator */}
      {selectedTool !== AnnotationTool.SELECT && (
        <div className="absolute top-2 left-2 px-2 py-1 bg-black bg-opacity-75 text-white text-xs rounded">
          Tool: {selectedTool}
        </div>
      )}

      {/* Placeholder notice */}
      <div className="absolute bottom-2 right-2 px-2 py-1 bg-gray-800 bg-opacity-75 text-white text-xs rounded">
        Annotation Layer (Simplified)
      </div>
    </div>
  )
}