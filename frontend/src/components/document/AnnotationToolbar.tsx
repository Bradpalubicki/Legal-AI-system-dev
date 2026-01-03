'use client'

import { useState } from 'react'
import { SketchPicker } from 'react-color'
import { AnnotationTool, AnnotationType, AnnotationStyle } from '../../types/document'
import { Button } from '../ui'
import {
  CursorArrowRaysIcon,
  ChatBubbleBottomCenterTextIcon,
  PencilIcon,
  EyeDropperIcon,
  RectangleStackIcon,
  SwatchIcon,
  AdjustmentsHorizontalIcon,
  SparklesIcon as HighlightIcon
} from '@heroicons/react/24/outline'

interface AnnotationToolbarProps {
  selectedTool: AnnotationTool
  annotationStyle: AnnotationStyle
  onToolChange: (tool: AnnotationTool) => void
  onStyleChange: (style: Partial<AnnotationStyle>) => void
  readonly?: boolean
  className?: string
}

const ANNOTATION_TOOLS = [
  { tool: AnnotationTool.SELECT, icon: CursorArrowRaysIcon, label: 'Select', shortcut: 'V' },
  { tool: AnnotationTool.HIGHLIGHT, icon: HighlightIcon, label: 'Highlight', shortcut: 'H' },
  { tool: AnnotationTool.NOTE, icon: ChatBubbleBottomCenterTextIcon, label: 'Note', shortcut: 'N' },
  { tool: AnnotationTool.COMMENT, icon: ChatBubbleBottomCenterTextIcon, label: 'Comment', shortcut: 'C' },
  { tool: AnnotationTool.DRAWING, icon: PencilIcon, label: 'Draw', shortcut: 'D' },
  { tool: AnnotationTool.REDACTION, icon: EyeDropperIcon, label: 'Redact', shortcut: 'R' }
]

const PRESET_COLORS = [
  '#FFEB3B', // Yellow
  '#4CAF50', // Green
  '#2196F3', // Blue
  '#FF9800', // Orange
  '#E91E63', // Pink
  '#9C27B0', // Purple
  '#F44336', // Red
  '#607D8B', // Blue Grey
  '#795548', // Brown
  '#000000'  // Black
]

export default function AnnotationToolbar({
  selectedTool,
  annotationStyle,
  onToolChange,
  onStyleChange,
  readonly = false,
  className = ''
}: AnnotationToolbarProps) {
  const [showColorPicker, setShowColorPicker] = useState(false)
  const [showStylePanel, setShowStylePanel] = useState(false)

  if (readonly) return null

  const handleToolSelect = (tool: AnnotationTool) => {
    onToolChange(tool)
  }

  const handleColorChange = (color: any) => {
    onStyleChange({
      color: color.hex,
      backgroundColor: selectedTool === AnnotationTool.HIGHLIGHT ? color.hex : annotationStyle.backgroundColor
    })
  }

  const handlePresetColorSelect = (color: string) => {
    onStyleChange({
      color,
      backgroundColor: selectedTool === AnnotationTool.HIGHLIGHT ? color : annotationStyle.backgroundColor
    })
    setShowColorPicker(false)
  }

  const handleOpacityChange = (opacity: number) => {
    onStyleChange({ opacity })
  }

  const handleStrokeWidthChange = (strokeWidth: number) => {
    onStyleChange({ strokeWidth })
  }

  return (
    <div className={`flex items-center space-x-2 p-3 bg-white border border-gray-200 rounded-lg shadow-lg ${className}`}>
      {/* Tool Buttons */}
      <div className="flex items-center space-x-1 pr-3 border-r border-gray-200">
        {ANNOTATION_TOOLS.map(({ tool, icon: Icon, label, shortcut }) => (
          <Button
            key={tool}
            variant={selectedTool === tool ? 'primary' : 'ghost'}
            size="sm"
            onClick={() => handleToolSelect(tool)}
            className="relative group"
            title={`${label} (${shortcut})`}
          >
            <Icon className="w-4 h-4" />
            
            {/* Tooltip */}
            <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-900 text-white text-xs rounded py-1 px-2 whitespace-nowrap">
              {label} ({shortcut})
            </div>
          </Button>
        ))}
      </div>

      {/* Color Picker */}
      <div className="relative">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowColorPicker(!showColorPicker)}
          className="flex items-center space-x-1"
          title="Change color"
        >
          <div
            className="w-4 h-4 rounded border border-gray-300"
            style={{ backgroundColor: annotationStyle.color }}
          />
          <SwatchIcon className="w-4 h-4" />
        </Button>

        {showColorPicker && (
          <div className="absolute top-full mt-2 z-50">
            <div 
              className="fixed inset-0 bg-transparent"
              onClick={() => setShowColorPicker(false)}
            />
            <div className="relative bg-white rounded-lg shadow-lg p-4 border border-gray-200">
              {/* Preset Colors */}
              <div className="mb-4">
                <p className="text-xs font-medium text-gray-700 mb-2">Preset Colors</p>
                <div className="grid grid-cols-5 gap-2">
                  {PRESET_COLORS.map((color) => (
                    <button
                      key={color}
                      className={`w-8 h-8 rounded border-2 hover:scale-110 transition-transform ${
                        annotationStyle.color === color ? 'border-blue-500' : 'border-gray-300'
                      }`}
                      style={{ backgroundColor: color }}
                      onClick={() => handlePresetColorSelect(color)}
                    />
                  ))}
                </div>
              </div>

              {/* Color Picker */}
              <SketchPicker
                color={annotationStyle.color}
                onChange={handleColorChange}
                disableAlpha={false}
                presetColors={[]}
                width="200px"
              />
            </div>
          </div>
        )}
      </div>

      {/* Style Controls */}
      <div className="relative">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowStylePanel(!showStylePanel)}
          title="Style options"
        >
          <AdjustmentsHorizontalIcon className="w-4 h-4" />
        </Button>

        {showStylePanel && (
          <div className="absolute top-full mt-2 right-0 z-50">
            <div 
              className="fixed inset-0 bg-transparent"
              onClick={() => setShowStylePanel(false)}
            />
            <div className="relative bg-white rounded-lg shadow-lg p-4 border border-gray-200 w-64">
              <h4 className="text-sm font-medium text-gray-900 mb-3">Style Options</h4>
              
              {/* Opacity */}
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Opacity: {Math.round(annotationStyle.opacity * 100)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={annotationStyle.opacity}
                  onChange={(e) => handleOpacityChange(parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
              </div>

              {/* Stroke Width (for drawing tool) */}
              {selectedTool === AnnotationTool.DRAWING && (
                <div className="mb-4">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Stroke Width: {annotationStyle.strokeWidth || 2}px
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    step="1"
                    value={annotationStyle.strokeWidth || 2}
                    onChange={(e) => handleStrokeWidthChange(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>
              )}

              {/* Font Size (for text annotations) */}
              {(selectedTool === AnnotationTool.NOTE || selectedTool === AnnotationTool.COMMENT) && (
                <div className="mb-4">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Font Size: {annotationStyle.fontSize || 12}px
                  </label>
                  <input
                    type="range"
                    min="8"
                    max="24"
                    step="1"
                    value={annotationStyle.fontSize || 12}
                    onChange={(e) => onStyleChange({ fontSize: parseInt(e.target.value) })}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>
              )}

              {/* Border Width */}
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-700 mb-1">
                  Border Width: {annotationStyle.borderWidth || 0}px
                </label>
                <input
                  type="range"
                  min="0"
                  max="5"
                  step="1"
                  value={annotationStyle.borderWidth || 0}
                  onChange={(e) => onStyleChange({ borderWidth: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                />
              </div>

              {/* Border Color */}
              {(annotationStyle.borderWidth || 0) > 0 && (
                <div className="mb-4">
                  <label className="block text-xs font-medium text-gray-700 mb-1">
                    Border Color
                  </label>
                  <div className="flex items-center space-x-2">
                    <div
                      className="w-6 h-6 rounded border border-gray-300 cursor-pointer"
                      style={{ backgroundColor: annotationStyle.borderColor || '#000000' }}
                      onClick={() => {
                        // Could open another color picker for border color
                      }}
                    />
                    <input
                      type="color"
                      value={annotationStyle.borderColor || '#000000'}
                      onChange={(e) => onStyleChange({ borderColor: e.target.value })}
                      className="w-8 h-8 border border-gray-300 rounded cursor-pointer"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="flex items-center space-x-1 pl-3 border-l border-gray-200">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onStyleChange({ opacity: 0.5 })}
          title="50% opacity"
        >
          50%
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onStyleChange({ opacity: 1.0 })}
          title="100% opacity"
        >
          100%
        </Button>
      </div>
    </div>
  )
}