'use client'

import { useState, useEffect, useRef } from 'react'
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd'

export interface GridItem {
  id: string
  component: React.ComponentType<any>
  props?: any
  title: string
  size: 'small' | 'medium' | 'large' | 'xlarge'
  minWidth?: number
  minHeight?: number
  priority?: number // Higher priority items show first on mobile
}

interface ResponsiveGridProps {
  items: GridItem[]
  onItemsReorder?: (items: GridItem[]) => void
  enableDragDrop?: boolean
  gap?: number
  minItemWidth?: number
}

const sizeClasses = {
  small: 'col-span-1 row-span-1',
  medium: 'col-span-1 md:col-span-2 row-span-1',
  large: 'col-span-1 md:col-span-2 lg:col-span-3 row-span-2',
  xlarge: 'col-span-1 md:col-span-2 lg:col-span-4 row-span-2'
}

const sizeDimensions = {
  small: { width: 1, height: 1 },
  medium: { width: 2, height: 1 },
  large: { width: 3, height: 2 },
  xlarge: { width: 4, height: 2 }
}

export default function ResponsiveGrid({
  items,
  onItemsReorder,
  enableDragDrop = true,
  gap = 4,
  minItemWidth = 280
}: ResponsiveGridProps) {
  const [orderedItems, setOrderedItems] = useState(items)
  const [containerWidth, setContainerWidth] = useState(0)
  const [columns, setColumns] = useState(1)
  const containerRef = useRef<HTMLDivElement>(null)

  // Calculate optimal number of columns based on container width
  useEffect(() => {
    const updateColumns = () => {
      if (containerRef.current) {
        const width = containerRef.current.offsetWidth
        setContainerWidth(width)
        
        // Calculate columns based on minimum item width and gap
        const availableWidth = width - (gap * 16) // Convert gap from Tailwind units
        const possibleColumns = Math.floor(availableWidth / minItemWidth)
        setColumns(Math.max(1, Math.min(possibleColumns, 6))) // Max 6 columns
      }
    }

    updateColumns()
    window.addEventListener('resize', updateColumns)
    
    // Use ResizeObserver for more accurate container size tracking
    const resizeObserver = new ResizeObserver(updateColumns)
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }

    return () => {
      window.removeEventListener('resize', updateColumns)
      resizeObserver.disconnect()
    }
  }, [gap, minItemWidth])

  // Update items when props change
  useEffect(() => {
    // Sort items by priority on mobile/tablet
    if (columns <= 2) {
      const sortedItems = [...items].sort((a, b) => (b.priority || 0) - (a.priority || 0))
      setOrderedItems(sortedItems)
    } else {
      setOrderedItems(items)
    }
  }, [items, columns])

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination || !enableDragDrop) return

    const newItems = Array.from(orderedItems)
    const [reorderedItem] = newItems.splice(result.source.index, 1)
    newItems.splice(result.destination.index, 0, reorderedItem)

    setOrderedItems(newItems)
    onItemsReorder?.(newItems)
  }

  const getGridClasses = () => {
    const baseClasses = 'grid auto-rows-max'
    const gapClass = `gap-${gap}`
    
    // Responsive grid columns
    if (columns === 1) {
      return `${baseClasses} grid-cols-1 ${gapClass}`
    } else if (columns === 2) {
      return `${baseClasses} grid-cols-1 md:grid-cols-2 ${gapClass}`
    } else if (columns === 3) {
      return `${baseClasses} grid-cols-1 md:grid-cols-2 lg:grid-cols-3 ${gapClass}`
    } else if (columns === 4) {
      return `${baseClasses} grid-cols-1 md:grid-cols-2 lg:grid-cols-4 ${gapClass}`
    } else if (columns === 5) {
      return `${baseClasses} grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 ${gapClass}`
    } else {
      return `${baseClasses} grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 ${gapClass}`
    }
  }

  const getItemClasses = (item: GridItem) => {
    // On mobile/small screens, all items take full width
    if (columns <= 1) {
      return 'col-span-1 row-span-1'
    }
    
    // On larger screens, use size classes but constrain by available columns
    const size = sizeDimensions[item.size]
    const constrainedWidth = Math.min(size.width, columns)
    const constrainedHeight = columns >= 3 ? size.height : 1 // Limit height on smaller grids
    
    return `col-span-${constrainedWidth} row-span-${constrainedHeight}`
  }

  if (!enableDragDrop) {
    return (
      <div ref={containerRef} className={getGridClasses()}>
        {orderedItems.map((item, index) => (
          <div
            key={item.id}
            className={`${getItemClasses(item)} transition-all duration-300 hover:z-10`}
            style={{ 
              minWidth: item.minWidth,
              minHeight: item.minHeight 
            }}
          >
            <GridItemWrapper item={item} />
          </div>
        ))}
      </div>
    )
  }

  return (
    <DragDropContext onDragEnd={handleDragEnd}>
      <Droppable droppableId="dashboard-grid">
        {(provided, snapshot) => (
          <div
            ref={(el) => {
              containerRef.current = el
              provided.innerRef(el)
            }}
            {...provided.droppableProps}
            className={`${getGridClasses()} ${
              snapshot.isDraggingOver ? 'bg-gray-50 rounded-lg' : ''
            } transition-colors duration-200`}
          >
            {orderedItems.map((item, index) => (
              <Draggable key={item.id} draggableId={item.id} index={index}>
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.draggableProps}
                    className={`${getItemClasses(item)} transition-all duration-300 ${
                      snapshot.isDragging 
                        ? 'rotate-2 scale-105 shadow-xl z-50' 
                        : 'hover:z-10'
                    }`}
                    style={{
                      ...provided.draggableProps.style,
                      minWidth: item.minWidth,
                      minHeight: item.minHeight
                    }}
                  >
                    <GridItemWrapper 
                      item={item} 
                      dragHandleProps={provided.dragHandleProps}
                      isDragging={snapshot.isDragging}
                    />
                  </div>
                )}
              </Draggable>
            ))}
            {provided.placeholder}
          </div>
        )}
      </Droppable>
    </DragDropContext>
  )
}

interface GridItemWrapperProps {
  item: GridItem
  dragHandleProps?: any
  isDragging?: boolean
}

function GridItemWrapper({ item, dragHandleProps, isDragging = false }: GridItemWrapperProps) {
  const Component = item.component
  
  return (
    <div 
      className={`h-full transition-all duration-200 ${
        isDragging ? 'opacity-90' : ''
      }`}
    >
      <div className="relative h-full group">
        {/* Drag handle */}
        {dragHandleProps && (
          <div
            {...dragHandleProps}
            className="absolute top-2 right-2 p-2 opacity-0 group-hover:opacity-100 transition-opacity cursor-move z-10 bg-white rounded-md shadow-sm border border-gray-200"
            title="Drag to reorder"
          >
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
            </svg>
          </div>
        )}
        
        {/* Component content */}
        <Component {...(item.props || {})} />
      </div>
    </div>
  )
}

// Hook for managing grid state
export function useResponsiveGrid(initialItems: GridItem[]) {
  const [items, setItems] = useState(initialItems)

  const addItem = (item: GridItem) => {
    setItems(prev => [...prev, item])
  }

  const removeItem = (id: string) => {
    setItems(prev => prev.filter(item => item.id !== id))
  }

  const updateItem = (id: string, updates: Partial<GridItem>) => {
    setItems(prev => prev.map(item => 
      item.id === id ? { ...item, ...updates } : item
    ))
  }

  const reorderItems = (newItems: GridItem[]) => {
    setItems(newItems)
  }

  const resetToDefault = () => {
    setItems(initialItems)
  }

  return {
    items,
    addItem,
    removeItem,
    updateItem,
    reorderItems,
    resetToDefault
  }
}