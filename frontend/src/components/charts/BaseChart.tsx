'use client'

import React, { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Card, CardHeader, CardBody } from '../ui'
import { ChartConfig, ExportConfig, ExportFormat } from '../../types/analytics'
import {
  ArrowDownTrayIcon,
  ArrowsPointingOutIcon,
  Cog6ToothIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'

interface BaseChartProps {
  title?: string
  subtitle?: string
  description?: string
  children: React.ReactNode
  config?: ChartConfig
  loading?: boolean
  error?: string
  onExport?: (config: ExportConfig) => void
  onConfigChange?: (config: Partial<ChartConfig>) => void
  className?: string
  actions?: React.ReactNode
}

export default function BaseChart({
  title,
  subtitle,
  description,
  children,
  config,
  loading = false,
  error,
  onExport,
  onConfigChange,
  className = '',
  actions
}: BaseChartProps) {
  const [showExportMenu, setShowExportMenu] = useState(false)
  const [showConfigPanel, setShowConfigPanel] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const chartRef = useRef<HTMLDivElement>(null)

  const handleExport = (format: ExportFormat) => {
    onExport?.({
      format,
      filename: title ? `${title.toLowerCase().replace(/\s+/g, '_')}_chart` : 'chart'
    })
    setShowExportMenu(false)
  }

  const toggleFullscreen = () => {
    if (!isFullscreen && chartRef.current) {
      chartRef.current.requestFullscreen?.()
      setIsFullscreen(true)
    } else if (document.fullscreenElement) {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  // Listen for fullscreen changes
  React.useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  return (
    <div 
      ref={chartRef}
      className={`relative ${isFullscreen ? 'bg-white p-8' : ''} ${className}`}
    >
      <Card className="h-full">
        {/* Header */}
        {(title || subtitle || actions) && (
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                {title && (
                  <h3 className={`font-medium text-gray-900 ${isFullscreen ? 'text-2xl' : 'text-lg'}`}>
                    {title}
                  </h3>
                )}
                {subtitle && (
                  <p className={`text-gray-600 ${isFullscreen ? 'text-lg mt-2' : 'text-sm mt-1'}`}>
                    {subtitle}
                  </p>
                )}
                {description && (
                  <div className="flex items-start mt-2">
                    <InformationCircleIcon className="w-4 h-4 text-gray-400 mt-0.5 mr-1 flex-shrink-0" />
                    <p className="text-xs text-gray-500">{description}</p>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2 ml-4">
                {actions}
                
                {onExport && (
                  <div className="relative">
                    <button
                      onClick={() => setShowExportMenu(!showExportMenu)}
                      className="p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100"
                      title="Export chart"
                    >
                      <ArrowDownTrayIcon className="w-4 h-4" />
                    </button>
                    
                    {showExportMenu && (
                      <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg ring-1 ring-black ring-opacity-5 z-50">
                        <div className="py-1">
                          <button
                            onClick={() => handleExport(ExportFormat.PNG)}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Export as PNG
                          </button>
                          <button
                            onClick={() => handleExport(ExportFormat.PDF)}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Export as PDF
                          </button>
                          <button
                            onClick={() => handleExport(ExportFormat.SVG)}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Export as SVG
                          </button>
                          <hr className="my-1" />
                          <button
                            onClick={() => handleExport(ExportFormat.CSV)}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Export Data (CSV)
                          </button>
                          <button
                            onClick={() => handleExport(ExportFormat.JSON)}
                            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                          >
                            Export Data (JSON)
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <button
                  onClick={toggleFullscreen}
                  className="p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100"
                  title="Fullscreen"
                >
                  <ArrowsPointingOutIcon className="w-4 h-4" />
                </button>

                {onConfigChange && (
                  <button
                    onClick={() => setShowConfigPanel(!showConfigPanel)}
                    className="p-1 text-gray-400 hover:text-gray-600 rounded hover:bg-gray-100"
                    title="Chart settings"
                  >
                    <Cog6ToothIcon className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </CardHeader>
        )}

        {/* Content */}
        <CardBody className={`relative ${isFullscreen ? 'p-6' : 'p-4'}`}>
          {/* Loading State */}
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-75 z-10">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <p className="text-sm text-gray-600">Loading chart...</p>
              </div>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="flex items-center justify-center h-48 text-center">
              <div>
                <div className="text-red-500 mb-2">
                  <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-gray-900 mb-1">Failed to load chart</p>
                <p className="text-xs text-gray-500">{error}</p>
              </div>
            </div>
          )}

          {/* Chart Content */}
          {!loading && !error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={isFullscreen ? 'h-full' : ''}
            >
              {children}
            </motion.div>
          )}
        </CardBody>
      </Card>

      {/* Configuration Panel */}
      {showConfigPanel && onConfigChange && config && (
        <div className="absolute top-full right-0 mt-2 w-64 bg-white rounded-md shadow-lg border border-gray-200 z-50">
          <div className="p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Chart Settings</h4>
            
            <div className="space-y-3">
              {/* Animation */}
              <div className="flex items-center justify-between">
                <label className="text-xs text-gray-700">Animation</label>
                <input
                  type="checkbox"
                  checked={config.animate !== false}
                  onChange={(e) => onConfigChange({ animate: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>

              {/* Legend */}
              <div className="flex items-center justify-between">
                <label className="text-xs text-gray-700">Show Legend</label>
                <input
                  type="checkbox"
                  checked={config.showLegend !== false}
                  onChange={(e) => onConfigChange({ showLegend: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>

              {/* Grid */}
              <div className="flex items-center justify-between">
                <label className="text-xs text-gray-700">Show Grid</label>
                <input
                  type="checkbox"
                  checked={config.showGrid !== false}
                  onChange={(e) => onConfigChange({ showGrid: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </div>

              {/* Theme */}
              <div>
                <label className="text-xs text-gray-700 block mb-1">Theme</label>
                <select
                  value={config.theme || 'light'}
                  onChange={(e) => onConfigChange({ theme: e.target.value as 'light' | 'dark' })}
                  className="w-full text-xs border border-gray-300 rounded px-2 py-1"
                >
                  <option value="light">Light</option>
                  <option value="dark">Dark</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end mt-4">
              <button
                onClick={() => setShowConfigPanel(false)}
                className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fullscreen overlay to close config panel */}
      {showExportMenu || showConfigPanel ? (
        <div 
          className="fixed inset-0 z-40"
          onClick={() => {
            setShowExportMenu(false)
            setShowConfigPanel(false)
          }}
        />
      ) : null}
    </div>
  )
}