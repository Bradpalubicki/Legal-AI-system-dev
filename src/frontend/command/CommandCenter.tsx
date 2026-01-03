'use client'

import React, { useState, useEffect, useRef } from 'react'
import {
  Search,
  Upload,
  FileText,
  MessageSquare,
  Settings,
  Download,
  Share,
  Plus,
  Clock,
  Star,
  Zap,
  Command,
  ArrowRight,
  X,
  Filter,
  Calendar,
  User,
  Briefcase
} from 'lucide-react'

interface QuickAction {
  id: string
  title: string
  description: string
  icon: React.ComponentType
  shortcut?: string
  category: 'documents' | 'analysis' | 'qa' | 'cases' | 'reports' | 'settings'
  action: () => void
  favorite?: boolean
}

interface RecentItem {
  id: string
  title: string
  type: 'document' | 'case' | 'analysis' | 'qa_session'
  timestamp: string
  metadata?: Record<string, any>
}

interface CommandCenterProps {
  onClose?: () => void
}

export const CommandCenter: React.FC<CommandCenterProps> = ({ onClose }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [recentItems, setRecentItems] = useState<RecentItem[]>([])
  const [favorites, setFavorites] = useState<string[]>([])
  const [filteredActions, setFilteredActions] = useState<QuickAction[]>([])

  const searchInputRef = useRef<HTMLInputElement>(null)

  const quickActions: QuickAction[] = [
    // Document actions
    {
      id: 'upload-document',
      title: 'Upload Document',
      description: 'Upload a new legal document for analysis',
      icon: Upload,
      shortcut: 'Ctrl+U',
      category: 'documents',
      action: () => console.log('Upload document')
    },
    {
      id: 'create-document',
      title: 'Create Document',
      description: 'Create a new document from template',
      icon: FileText,
      shortcut: 'Ctrl+N',
      category: 'documents',
      action: () => console.log('Create document')
    },
    {
      id: 'bulk-upload',
      title: 'Bulk Upload',
      description: 'Upload multiple documents at once',
      icon: Upload,
      category: 'documents',
      action: () => console.log('Bulk upload')
    },

    // Analysis actions
    {
      id: 'start-analysis',
      title: 'Start AI Analysis',
      description: 'Begin AI analysis on selected documents',
      icon: Zap,
      shortcut: 'Ctrl+A',
      category: 'analysis',
      action: () => console.log('Start analysis')
    },
    {
      id: 'view-insights',
      title: 'View Insights',
      description: 'Review AI-generated insights and recommendations',
      icon: Zap,
      category: 'analysis',
      action: () => console.log('View insights')
    },

    // Q&A actions
    {
      id: 'ask-question',
      title: 'Ask Question',
      description: 'Ask AI a question about your cases',
      icon: MessageSquare,
      shortcut: 'Ctrl+Q',
      category: 'qa',
      action: () => console.log('Ask question')
    },
    {
      id: 'view-qa-history',
      title: 'Q&A History',
      description: 'Review previous Q&A sessions',
      icon: MessageSquare,
      category: 'qa',
      action: () => console.log('View Q&A history')
    },

    // Case actions
    {
      id: 'create-case',
      title: 'Create New Case',
      description: 'Set up a new legal case',
      icon: Briefcase,
      shortcut: 'Ctrl+C',
      category: 'cases',
      action: () => console.log('Create case')
    },
    {
      id: 'view-timeline',
      title: 'Case Timeline',
      description: 'View chronological case events',
      icon: Calendar,
      category: 'cases',
      action: () => console.log('View timeline')
    },
    {
      id: 'schedule-deadline',
      title: 'Schedule Deadline',
      description: 'Add important case deadline',
      icon: Clock,
      category: 'cases',
      action: () => console.log('Schedule deadline')
    },

    // Report actions
    {
      id: 'generate-report',
      title: 'Generate Report',
      description: 'Create comprehensive case report',
      icon: FileText,
      category: 'reports',
      action: () => console.log('Generate report')
    },
    {
      id: 'export-data',
      title: 'Export Data',
      description: 'Export case data and analytics',
      icon: Download,
      shortcut: 'Ctrl+E',
      category: 'reports',
      action: () => console.log('Export data')
    },
    {
      id: 'share-dashboard',
      title: 'Share Dashboard',
      description: 'Share dashboard with team members',
      icon: Share,
      category: 'reports',
      action: () => console.log('Share dashboard')
    },

    // Settings actions
    {
      id: 'user-settings',
      title: 'User Settings',
      description: 'Manage your account and preferences',
      icon: Settings,
      category: 'settings',
      action: () => console.log('User settings')
    },
    {
      id: 'system-settings',
      title: 'System Settings',
      description: 'Configure system-wide settings',
      icon: Settings,
      category: 'settings',
      action: () => console.log('System settings')
    }
  ]

  const categories = [
    { id: 'all', label: 'All Actions', count: quickActions.length },
    { id: 'documents', label: 'Documents', count: quickActions.filter(a => a.category === 'documents').length },
    { id: 'analysis', label: 'Analysis', count: quickActions.filter(a => a.category === 'analysis').length },
    { id: 'qa', label: 'Q&A', count: quickActions.filter(a => a.category === 'qa').length },
    { id: 'cases', label: 'Cases', count: quickActions.filter(a => a.category === 'cases').length },
    { id: 'reports', label: 'Reports', count: quickActions.filter(a => a.category === 'reports').length },
    { id: 'settings', label: 'Settings', count: quickActions.filter(a => a.category === 'settings').length }
  ]

  const generateRecentItems = (): RecentItem[] => {
    return [
      {
        id: '1',
        title: 'Contract Analysis v2.pdf',
        type: 'document',
        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        metadata: { size: '2.4 MB', status: 'analyzed' }
      },
      {
        id: '2',
        title: 'Case #2024-CV-123',
        type: 'case',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        metadata: { status: 'active', priority: 'high' }
      },
      {
        id: '3',
        title: 'Q&A Session - Statute of Limitations',
        type: 'qa_session',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        metadata: { questions: 5, responses: 5 }
      },
      {
        id: '4',
        title: 'Risk Assessment Report',
        type: 'analysis',
        timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
        metadata: { confidence: 0.89, risks: 3 }
      }
    ]
  }

  const filterActions = () => {
    let filtered = quickActions

    // Filter by category
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(action => action.category === selectedCategory)
    }

    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(action =>
        action.title.toLowerCase().includes(query) ||
        action.description.toLowerCase().includes(query) ||
        action.category.includes(query)
      )
    }

    // Sort favorites first
    filtered = filtered.sort((a, b) => {
      const aIsFavorite = favorites.includes(a.id)
      const bIsFavorite = favorites.includes(b.id)
      if (aIsFavorite && !bIsFavorite) return -1
      if (!aIsFavorite && bIsFavorite) return 1
      return a.title.localeCompare(b.title)
    })

    setFilteredActions(filtered)
  }

  const toggleFavorite = (actionId: string) => {
    setFavorites(prev =>
      prev.includes(actionId)
        ? prev.filter(id => id !== actionId)
        : [...prev, actionId]
    )
  }

  const executeAction = (action: QuickAction) => {
    action.action()
    setIsOpen(false)
    onClose?.()
  }

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date()
    const time = new Date(timestamp)
    const diffInMinutes = Math.floor((now.getTime() - time.getTime()) / (1000 * 60))

    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    return `${Math.floor(diffInMinutes / 1440)}d ago`
  }

  const getItemIcon = (type: RecentItem['type']) => {
    switch (type) {
      case 'document': return <FileText className="w-4 h-4" />
      case 'case': return <Briefcase className="w-4 h-4" />
      case 'analysis': return <Zap className="w-4 h-4" />
      case 'qa_session': return <MessageSquare className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  // Initialize data
  useEffect(() => {
    setRecentItems(generateRecentItems())
    setFavorites(['upload-document', 'ask-question', 'start-analysis'])
  }, [])

  // Filter actions when dependencies change
  useEffect(() => {
    filterActions()
  }, [searchQuery, selectedCategory, favorites])

  // Focus search input when opened
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus()
    }
  }, [isOpen])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Open command center with Ctrl+K or Cmd+K
      if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault()
        setIsOpen(true)
      }

      // Close with Escape
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false)
        onClose?.()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center space-x-2 px-4 py-2 bg-gray-800 text-white rounded-lg hover:bg-gray-700 transition-colors"
        title="Open Command Center (Ctrl+K)"
      >
        <Command className="w-4 h-4" />
        <span>Command Center</span>
        <div className="hidden sm:flex items-center space-x-1 text-xs text-gray-400">
          <kbd className="px-1 py-0.5 bg-gray-700 rounded">Ctrl</kbd>
          <kbd className="px-1 py-0.5 bg-gray-700 rounded">K</kbd>
        </div>
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-start justify-center pt-16 z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[80vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center space-x-3">
                <Command className="w-6 h-6 text-gray-700" />
                <h2 className="text-xl font-semibold text-gray-900">Command Center</h2>
              </div>
              <button
                onClick={() => { setIsOpen(false); onClose?.() }}
                className="p-2 hover:bg-gray-100 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex flex-1 min-h-0">
              {/* Sidebar */}
              <div className="w-64 border-r border-gray-200 p-4">
                <div className="space-y-4">
                  {/* Search */}
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      ref={searchInputRef}
                      type="text"
                      placeholder="Search actions..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {/* Categories */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Categories</h3>
                    <div className="space-y-1">
                      {categories.map((category) => (
                        <button
                          key={category.id}
                          onClick={() => setSelectedCategory(category.id)}
                          className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded-lg transition-colors ${
                            selectedCategory === category.id
                              ? 'bg-blue-100 text-blue-700'
                              : 'text-gray-600 hover:bg-gray-100'
                          }`}
                        >
                          <span>{category.label}</span>
                          <span className="text-xs text-gray-400">{category.count}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Recent Items */}
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Recent Items</h3>
                    <div className="space-y-1">
                      {recentItems.slice(0, 5).map((item) => (
                        <div
                          key={item.id}
                          className="flex items-start space-x-2 p-2 hover:bg-gray-50 rounded-lg cursor-pointer"
                        >
                          <div className="text-gray-400 mt-0.5">
                            {getItemIcon(item.type)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-gray-900 truncate">{item.title}</p>
                            <p className="text-xs text-gray-500">{formatTimeAgo(item.timestamp)}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Main Content */}
              <div className="flex-1 p-6 overflow-auto">
                <div className="space-y-4">
                  {/* Quick Actions Grid */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-lg font-medium text-gray-900">
                        {selectedCategory === 'all' ? 'All Actions' : categories.find(c => c.id === selectedCategory)?.label}
                      </h3>
                      <div className="text-sm text-gray-500">
                        {filteredActions.length} action{filteredActions.length !== 1 ? 's' : ''}
                      </div>
                    </div>

                    {filteredActions.length === 0 ? (
                      <div className="text-center py-12">
                        <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-gray-900 mb-2">No actions found</h3>
                        <p className="text-gray-500">Try adjusting your search or category filter</p>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {filteredActions.map((action) => (
                          <div
                            key={action.id}
                            className="group relative bg-white border border-gray-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer"
                            onClick={() => executeAction(action)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex items-start space-x-3 flex-1">
                                <div className="bg-blue-100 p-2 rounded-lg">
                                  <action.icon className="w-5 h-5 text-blue-600" />
                                </div>
                                <div className="flex-1 min-w-0">
                                  <h4 className="text-base font-medium text-gray-900 mb-1">
                                    {action.title}
                                  </h4>
                                  <p className="text-sm text-gray-600 mb-2">
                                    {action.description}
                                  </p>
                                  {action.shortcut && (
                                    <div className="flex items-center space-x-1">
                                      {action.shortcut.split('+').map((key, index) => (
                                        <React.Fragment key={key}>
                                          {index > 0 && <span className="text-xs text-gray-400">+</span>}
                                          <kbd className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                                            {key}
                                          </kbd>
                                        </React.Fragment>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>

                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleFavorite(action.id)
                                  }}
                                  className={`p-1 rounded hover:bg-gray-100 ${
                                    favorites.includes(action.id) ? 'text-yellow-500' : 'text-gray-400'
                                  }`}
                                >
                                  <Star className={`w-4 h-4 ${favorites.includes(action.id) ? 'fill-current' : ''}`} />
                                </button>
                                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-blue-500 transition-colors" />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}