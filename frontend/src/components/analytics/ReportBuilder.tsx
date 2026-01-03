'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Card, CardHeader, CardBody } from '../ui'
import { 
  ReportTemplate, 
  ReportSection, 
  ReportSchedule, 
  ExportFormat, 
  DashboardWidget,
  WidgetType 
} from '../../types/analytics'
import {
  DocumentTextIcon,
  PlusIcon,
  TrashIcon,
  ClockIcon,
  ArrowDownTrayIcon,
  Cog6ToothIcon,
  CalendarIcon,
  UsersIcon
} from '@heroicons/react/24/outline'

interface ReportBuilderProps {
  availableWidgets: DashboardWidget[]
  onSaveTemplate?: (template: ReportTemplate) => void
  onGenerateReport?: (template: ReportTemplate) => void
  existingTemplate?: ReportTemplate
  className?: string
}

export default function ReportBuilder({
  availableWidgets,
  onSaveTemplate,
  onGenerateReport,
  existingTemplate,
  className = ''
}: ReportBuilderProps) {
  const [template, setTemplate] = useState<ReportTemplate>(existingTemplate || {
    id: '',
    name: '',
    description: '',
    sections: [],
    recipients: [],
    format: ExportFormat.PDF
  })

  const [showScheduleModal, setShowScheduleModal] = useState(false)
  const [activeSection, setActiveSection] = useState<string | null>(null)

  const updateTemplate = useCallback((updates: Partial<ReportTemplate>) => {
    setTemplate(prev => ({ ...prev, ...updates }))
  }, [])

  const addSection = () => {
    const newSection: ReportSection = {
      id: Date.now().toString(),
      title: 'New Section',
      description: '',
      widgets: [],
      pageBreak: false
    }
    
    updateTemplate({
      sections: [...template.sections, newSection]
    })
    setActiveSection(newSection.id)
  }

  const updateSection = (sectionId: string, updates: Partial<ReportSection>) => {
    updateTemplate({
      sections: template.sections.map(section =>
        section.id === sectionId ? { ...section, ...updates } : section
      )
    })
  }

  const removeSection = (sectionId: string) => {
    updateTemplate({
      sections: template.sections.filter(section => section.id !== sectionId)
    })
    if (activeSection === sectionId) {
      setActiveSection(null)
    }
  }

  const addWidgetToSection = (sectionId: string, widgetId: string) => {
    const section = template.sections.find(s => s.id === sectionId)
    if (section && !section.widgets.includes(widgetId)) {
      updateSection(sectionId, {
        widgets: [...section.widgets, widgetId]
      })
    }
  }

  const removeWidgetFromSection = (sectionId: string, widgetId: string) => {
    const section = template.sections.find(s => s.id === sectionId)
    if (section) {
      updateSection(sectionId, {
        widgets: section.widgets.filter(id => id !== widgetId)
      })
    }
  }

  const handleScheduleChange = (schedule: ReportSchedule) => {
    updateTemplate({ schedule })
    setShowScheduleModal(false)
  }

  const getWidgetById = (widgetId: string) => {
    return availableWidgets.find(w => w.id === widgetId)
  }

  const getWidgetTypeIcon = (type: WidgetType) => {
    // Return appropriate icon based on widget type
    return <DocumentTextIcon className="w-4 h-4" />
  }

  return (
    <div className={`max-w-6xl mx-auto space-y-6 ${className}`}>
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Report Builder</h2>
              <p className="text-sm text-gray-600 mt-1">
                Create custom reports with analytics widgets and data visualizations
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={() => onGenerateReport?.(template)}
                disabled={!template.name || template.sections.length === 0}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                <ArrowDownTrayIcon className="w-4 h-4 mr-2" />
                Generate Report
              </button>
              
              <button
                onClick={() => onSaveTemplate?.(template)}
                disabled={!template.name}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                Save Template
              </button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Settings */}
          <Card>
            <CardHeader>
              <h3 className="text-lg font-medium">Report Settings</h3>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Report Name
                  </label>
                  <input
                    type="text"
                    value={template.name}
                    onChange={(e) => updateTemplate({ name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter report name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={template.description}
                    onChange={(e) => updateTemplate({ description: e.target.value })}
                    rows={3}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Describe the purpose of this report"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Export Format
                    </label>
                    <select
                      value={template.format}
                      onChange={(e) => updateTemplate({ format: e.target.value as ExportFormat })}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value={ExportFormat.PDF}>PDF</option>
                      <option value={ExportFormat.EXCEL}>Excel</option>
                      <option value={ExportFormat.PNG}>PNG</option>
                      <option value={ExportFormat.CSV}>CSV</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Schedule
                    </label>
                    <button
                      onClick={() => setShowScheduleModal(true)}
                      className="w-full flex items-center justify-center px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                    >
                      <ClockIcon className="w-4 h-4 mr-2" />
                      {template.schedule ? `${template.schedule.frequency}` : 'Set Schedule'}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Recipients
                  </label>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {template.recipients.map((email, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs"
                      >
                        {email}
                        <button
                          onClick={() => updateTemplate({
                            recipients: template.recipients.filter((_, i) => i !== index)
                          })}
                          className="ml-1 hover:bg-blue-200 rounded-full p-0.5"
                        >
                          <TrashIcon className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                  <input
                    type="email"
                    placeholder="Add recipient email"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.currentTarget.value) {
                        const email = e.currentTarget.value.trim()
                        if (email && !template.recipients.includes(email)) {
                          updateTemplate({
                            recipients: [...template.recipients, email]
                          })
                          e.currentTarget.value = ''
                        }
                      }
                    }}
                  />
                </div>
              </div>
            </CardBody>
          </Card>

          {/* Report Sections */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Report Sections</h3>
                <button
                  onClick={addSection}
                  className="flex items-center px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                >
                  <PlusIcon className="w-4 h-4 mr-1" />
                  Add Section
                </button>
              </div>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <AnimatePresence>
                  {template.sections.map((section, index) => (
                    <motion.div
                      key={section.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      className={`border rounded-lg p-4 ${
                        activeSection === section.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <input
                            type="text"
                            value={section.title}
                            onChange={(e) => updateSection(section.id, { title: e.target.value })}
                            className="text-lg font-medium bg-transparent border-none p-0 focus:ring-0 focus:outline-none w-full"
                            placeholder="Section title"
                          />
                          <textarea
                            value={section.description}
                            onChange={(e) => updateSection(section.id, { description: e.target.value })}
                            rows={2}
                            className="text-sm text-gray-600 bg-transparent border-none p-0 focus:ring-0 focus:outline-none w-full mt-1 resize-none"
                            placeholder="Section description"
                          />
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => setActiveSection(activeSection === section.id ? null : section.id)}
                            className="p-1 text-gray-400 hover:text-gray-600"
                          >
                            <Cog6ToothIcon className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => removeSection(section.id)}
                            className="p-1 text-red-400 hover:text-red-600"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </div>

                      {/* Section Widgets */}
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium text-gray-700">Widgets ({section.widgets.length})</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {section.widgets.map(widgetId => {
                            const widget = getWidgetById(widgetId)
                            return widget ? (
                              <div
                                key={widgetId}
                                className="flex items-center justify-between p-2 bg-white border border-gray-200 rounded"
                              >
                                <div className="flex items-center space-x-2">
                                  {getWidgetTypeIcon(widget.type)}
                                  <span className="text-sm">{widget.title}</span>
                                </div>
                                <button
                                  onClick={() => removeWidgetFromSection(section.id, widgetId)}
                                  className="p-1 text-red-400 hover:text-red-600"
                                >
                                  <TrashIcon className="w-3 h-3" />
                                </button>
                              </div>
                            ) : null
                          })}
                        </div>
                      </div>

                      {/* Section Options */}
                      {activeSection === section.id && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-4 pt-4 border-t border-gray-200"
                        >
                          <label className="flex items-center">
                            <input
                              type="checkbox"
                              checked={section.pageBreak}
                              onChange={(e) => updateSection(section.id, { pageBreak: e.target.checked })}
                              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                            />
                            <span className="ml-2 text-sm text-gray-700">Start on new page</span>
                          </label>
                        </motion.div>
                      )}
                    </motion.div>
                  ))}
                </AnimatePresence>

                {template.sections.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <DocumentTextIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
                    <p>No sections added yet. Click "Add Section" to get started.</p>
                  </div>
                )}
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Available Widgets Sidebar */}
        <div>
          <Card>
            <CardHeader>
              <h3 className="text-lg font-medium">Available Widgets</h3>
              <p className="text-sm text-gray-600">
                Drag widgets to sections or click to add
              </p>
            </CardHeader>
            <CardBody>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {availableWidgets.map(widget => (
                  <div
                    key={widget.id}
                    className="p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                    onClick={() => {
                      if (activeSection) {
                        addWidgetToSection(activeSection, widget.id)
                      }
                    }}
                  >
                    <div className="flex items-start space-x-2">
                      {getWidgetTypeIcon(widget.type)}
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-gray-900 truncate">
                          {widget.title}
                        </h4>
                        <p className="text-xs text-gray-500 mt-1">
                          {widget.description || `${widget.type.replace('_', ' ')} visualization`}
                        </p>
                        <span className="inline-block mt-1 px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                          {widget.type.replace('_', ' ')}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>
      </div>

      {/* Schedule Modal */}
      <AnimatePresence>
        {showScheduleModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="bg-white rounded-lg p-6 w-full max-w-md"
            >
              <h3 className="text-lg font-medium mb-4">Schedule Report</h3>
              <ScheduleForm
                initialSchedule={template.schedule}
                onSave={handleScheduleChange}
                onCancel={() => setShowScheduleModal(false)}
              />
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Schedule form component
interface ScheduleFormProps {
  initialSchedule?: ReportSchedule
  onSave: (schedule: ReportSchedule) => void
  onCancel: () => void
}

function ScheduleForm({ initialSchedule, onSave, onCancel }: ScheduleFormProps) {
  const [schedule, setSchedule] = useState<ReportSchedule>(initialSchedule || {
    frequency: 'weekly',
    time: '09:00',
    timezone: 'America/New_York',
    enabled: true
  })

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Frequency
        </label>
        <select
          value={schedule.frequency}
          onChange={(e) => setSchedule(prev => ({ ...prev, frequency: e.target.value as any }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Time
        </label>
        <input
          type="time"
          value={schedule.time}
          onChange={(e) => setSchedule(prev => ({ ...prev, time: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Timezone
        </label>
        <select
          value={schedule.timezone}
          onChange={(e) => setSchedule(prev => ({ ...prev, timezone: e.target.value }))}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="America/New_York">Eastern Time</option>
          <option value="America/Chicago">Central Time</option>
          <option value="America/Denver">Mountain Time</option>
          <option value="America/Los_Angeles">Pacific Time</option>
          <option value="UTC">UTC</option>
        </select>
      </div>

      <label className="flex items-center">
        <input
          type="checkbox"
          checked={schedule.enabled}
          onChange={(e) => setSchedule(prev => ({ ...prev, enabled: e.target.checked }))}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <span className="ml-2 text-sm text-gray-700">Enable automatic reports</span>
      </label>

      <div className="flex justify-end space-x-3 pt-4 border-t">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={() => onSave(schedule)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Save Schedule
        </button>
      </div>
    </div>
  )
}