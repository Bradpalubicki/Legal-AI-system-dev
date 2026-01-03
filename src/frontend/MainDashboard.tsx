'use client'

import React, { useState } from 'react'
import { UnifiedDashboard } from './dashboard/UnifiedDashboard'
import { CaseTimeline } from './timeline/CaseTimeline'
import { CommandCenter } from './command/CommandCenter'
import { LayoutGrid, Timeline, Command, Settings } from 'lucide-react'

type ViewMode = 'dashboard' | 'timeline' | 'hybrid'

export const MainDashboard: React.FC = () => {
  const [currentView, setCurrentView] = useState<ViewMode>('dashboard')
  const [selectedCase, setSelectedCase] = useState<string | null>(null)

  const renderContent = () => {
    switch (currentView) {
      case 'dashboard':
        return <UnifiedDashboard />

      case 'timeline':
        return (
          <CaseTimeline
            caseId={selectedCase || undefined}
            showAllCases={!selectedCase}
          />
        )

      case 'hybrid':
        return (
          <div className="h-full grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-full">
              <UnifiedDashboard />
            </div>
            <div className="h-full">
              <CaseTimeline
                caseId={selectedCase || undefined}
                showAllCases={!selectedCase}
              />
            </div>
          </div>
        )

      default:
        return <UnifiedDashboard />
    }
  }

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Top Navigation */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-bold text-gray-900">Legal AI Intelligence Platform</h1>

            {/* View Toggle */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setCurrentView('dashboard')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  currentView === 'dashboard'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <LayoutGrid className="w-4 h-4" />
                <span>Dashboard</span>
              </button>

              <button
                onClick={() => setCurrentView('timeline')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  currentView === 'timeline'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Timeline className="w-4 h-4" />
                <span>Timeline</span>
              </button>

              <button
                onClick={() => setCurrentView('hybrid')}
                className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  currentView === 'hybrid'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <Settings className="w-4 h-4" />
                <span>Hybrid</span>
              </button>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Case Selector */}
            <select
              value={selectedCase || ''}
              onChange={(e) => setSelectedCase(e.target.value || null)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Cases</option>
              <option value="case_1">Case #2024-CV-001</option>
              <option value="case_2">Case #2024-CV-002</option>
              <option value="case_3">Case #2024-CV-003</option>
              <option value="case_4">Case #2024-CV-004</option>
              <option value="case_5">Case #2024-CV-005</option>
            </select>

            {/* Command Center */}
            <CommandCenter />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-hidden">
        {renderContent()}
      </div>
    </div>
  )
}