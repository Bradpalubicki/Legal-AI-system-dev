'use client'

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Document as DocumentType, 
  Annotation, 
  AnnotationType, 
  AnnotationReply 
} from '../../types/document'
import { Button, Input } from '../ui'
import {
  XMarkIcon,
  ChatBubbleBottomCenterTextIcon,
  PencilIcon,
  EyeDropperIcon,
  TrashIcon,
  CheckIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  UserCircleIcon,
  ArrowUturnLeftIcon as ReplyIcon,
  SparklesIcon as HighlightIcon
} from '@heroicons/react/24/outline'

interface AnnotationPanelProps {
  document: DocumentType
  annotations: Annotation[]
  selectedAnnotations: string[]
  currentPage: number
  onAnnotationUpdate?: (id: string, updates: Partial<Annotation>) => void
  onAnnotationDelete?: (id: string) => void
  onAnnotationSelect?: (id: string) => void
  onPageChange?: (page: number) => void
  onClose: () => void
  readonly?: boolean
}

export default function AnnotationPanel({
  document,
  annotations,
  selectedAnnotations,
  currentPage,
  onAnnotationUpdate,
  onAnnotationDelete,
  onAnnotationSelect,
  onPageChange,
  onClose,
  readonly = false
}: AnnotationPanelProps) {
  const [filterType, setFilterType] = useState<AnnotationType | 'all'>('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState<'date' | 'page' | 'author'>('date')
  const [showResolved, setShowResolved] = useState(false)
  const [editingAnnotation, setEditingAnnotation] = useState<string | null>(null)
  const [replyingTo, setReplyingTo] = useState<string | null>(null)
  const [replyContent, setReplyContent] = useState('')

  const filteredAndSortedAnnotations = useMemo(() => {
    let filtered = annotations.filter(annotation => {
      // Type filter
      if (filterType !== 'all' && annotation.type !== filterType) return false
      
      // Search filter
      if (searchTerm && !annotation.content.toLowerCase().includes(searchTerm.toLowerCase())) return false
      
      // Resolved filter
      if (!showResolved && annotation.isResolved) return false
      
      return true
    })

    // Sort annotations
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'page':
          return a.page - b.page
        case 'author':
          return a.userName.localeCompare(b.userName)
        case 'date':
        default:
          return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      }
    })

    return filtered
  }, [annotations, filterType, searchTerm, sortBy, showResolved])

  const getAnnotationIcon = (type: AnnotationType) => {
    switch (type) {
      case AnnotationType.HIGHLIGHT:
        return HighlightIcon
      case AnnotationType.NOTE:
      case AnnotationType.COMMENT:
        return ChatBubbleBottomCenterTextIcon
      case AnnotationType.DRAWING:
        return PencilIcon
      case AnnotationType.REDACTION:
        return EyeDropperIcon
      default:
        return ChatBubbleBottomCenterTextIcon
    }
  }

  const getAnnotationColor = (type: AnnotationType) => {
    switch (type) {
      case AnnotationType.HIGHLIGHT:
        return 'text-yellow-600 bg-yellow-100'
      case AnnotationType.NOTE:
        return 'text-blue-600 bg-blue-100'
      case AnnotationType.COMMENT:
        return 'text-green-600 bg-green-100'
      case AnnotationType.DRAWING:
        return 'text-purple-600 bg-purple-100'
      case AnnotationType.REDACTION:
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 1) return 'Just now'
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`
    if (diffInMinutes < 10080) return `${Math.floor(diffInMinutes / 1440)}d ago`
    
    return date.toLocaleDateString()
  }

  const handleAnnotationClick = (annotation: Annotation) => {
    onAnnotationSelect?.(annotation.id)
    onPageChange?.(annotation.page)
  }

  const handleUpdateAnnotation = (id: string, updates: Partial<Annotation>) => {
    onAnnotationUpdate?.(id, updates)
    setEditingAnnotation(null)
  }

  const handleResolveToggle = (annotation: Annotation) => {
    onAnnotationUpdate?.(annotation.id, { isResolved: !annotation.isResolved })
  }

  const handleAddReply = (annotationId: string) => {
    if (!replyContent.trim()) return

    const newReply: AnnotationReply = {
      id: `reply-${Date.now()}`,
      userId: 'current-user',
      userName: 'Current User',
      content: replyContent,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }

    const annotation = annotations.find(a => a.id === annotationId)
    if (annotation) {
      onAnnotationUpdate?.(annotationId, {
        replies: [...annotation.replies, newReply]
      })
    }

    setReplyContent('')
    setReplyingTo(null)
  }

  return (
    <div className="w-80 bg-white border-l border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Annotations</h3>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <XMarkIcon className="w-4 h-4" />
          </Button>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search annotations..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-2 mb-3">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value as AnnotationType | 'all')}
            className="flex-1 text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">All Types</option>
            <option value={AnnotationType.HIGHLIGHT}>Highlights</option>
            <option value={AnnotationType.NOTE}>Notes</option>
            <option value={AnnotationType.COMMENT}>Comments</option>
            <option value={AnnotationType.DRAWING}>Drawings</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'date' | 'page' | 'author')}
            className="flex-1 text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="date">Sort by Date</option>
            <option value="page">Sort by Page</option>
            <option value="author">Sort by Author</option>
          </select>
        </div>

        {/* Show Resolved Toggle */}
        <div className="flex items-center">
          <input
            type="checkbox"
            id="showResolved"
            checked={showResolved}
            onChange={(e) => setShowResolved(e.target.checked)}
            className="mr-2"
          />
          <label htmlFor="showResolved" className="text-sm text-gray-600">
            Show resolved
          </label>
        </div>
      </div>

      {/* Annotations List */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence>
          {filteredAndSortedAnnotations.map((annotation) => {
            const IconComponent = getAnnotationIcon(annotation.type)
            const isSelected = selectedAnnotations.includes(annotation.id)
            const isEditing = editingAnnotation === annotation.id

            return (
              <motion.div
                key={annotation.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  isSelected ? 'bg-blue-50 border-blue-200' : ''
                } ${annotation.isResolved ? 'opacity-60' : ''}`}
                onClick={() => handleAnnotationClick(annotation)}
              >
                <div className="flex items-start space-x-3">
                  {/* Icon */}
                  <div className={`p-1 rounded ${getAnnotationColor(annotation.type)}`}>
                    <IconComponent className="w-3 h-3" />
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <div className="flex items-center space-x-1">
                          {annotation.userAvatar ? (
                            <img
                              src={annotation.userAvatar}
                              alt={annotation.userName}
                              className="w-4 h-4 rounded-full"
                            />
                          ) : (
                            <UserCircleIcon className="w-4 h-4 text-gray-400" />
                          )}
                          <span className="text-xs font-medium text-gray-900">
                            {annotation.userName}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          Page {annotation.page}
                        </span>
                      </div>
                      
                      <div className="flex items-center space-x-1">
                        {!readonly && (
                          <>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleResolveToggle(annotation)
                              }}
                              className={`p-1 ${annotation.isResolved ? 'text-green-600' : 'text-gray-400'}`}
                              title={annotation.isResolved ? 'Mark as unresolved' : 'Mark as resolved'}
                            >
                              <CheckIcon className="w-3 h-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                onAnnotationDelete?.(annotation.id)
                              }}
                              className="p-1 text-red-400 hover:text-red-600"
                              title="Delete annotation"
                            >
                              <TrashIcon className="w-3 h-3" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Content */}
                    <div className="mb-2">
                      {isEditing ? (
                        <div className="space-y-2">
                          <textarea
                            defaultValue={annotation.content}
                            className="w-full p-2 text-sm border border-gray-300 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={3}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' && e.ctrlKey) {
                                handleUpdateAnnotation(annotation.id, {
                                  content: e.currentTarget.value,
                                  updatedAt: new Date().toISOString()
                                })
                              } else if (e.key === 'Escape') {
                                setEditingAnnotation(null)
                              }
                            }}
                            onBlur={(e) => {
                              handleUpdateAnnotation(annotation.id, {
                                content: e.target.value,
                                updatedAt: new Date().toISOString()
                              })
                            }}
                            autoFocus
                          />
                        </div>
                      ) : (
                        <p
                          className="text-sm text-gray-700 cursor-text"
                          onClick={(e) => {
                            e.stopPropagation()
                            if (!readonly) setEditingAnnotation(annotation.id)
                          }}
                        >
                          {annotation.content}
                        </p>
                      )}
                    </div>

                    {/* Replies */}
                    {annotation.replies.length > 0 && (
                      <div className="space-y-2 mt-3 pt-3 border-t border-gray-100">
                        {annotation.replies.map((reply) => (
                          <div key={reply.id} className="flex items-start space-x-2">
                            {reply.userAvatar ? (
                              <img
                                src={reply.userAvatar}
                                alt={reply.userName}
                                className="w-3 h-3 rounded-full"
                              />
                            ) : (
                              <UserCircleIcon className="w-3 h-3 text-gray-400 flex-shrink-0" />
                            )}
                            <div className="flex-1">
                              <div className="flex items-center space-x-1 mb-1">
                                <span className="text-xs font-medium text-gray-700">
                                  {reply.userName}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {formatDate(reply.createdAt)}
                                </span>
                              </div>
                              <p className="text-xs text-gray-600">{reply.content}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Reply Input */}
                    {replyingTo === annotation.id ? (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="space-y-2">
                          <textarea
                            value={replyContent}
                            onChange={(e) => setReplyContent(e.target.value)}
                            placeholder="Add a reply..."
                            className="w-full p-2 text-xs border border-gray-300 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={2}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' && e.ctrlKey) {
                                handleAddReply(annotation.id)
                              } else if (e.key === 'Escape') {
                                setReplyingTo(null)
                                setReplyContent('')
                              }
                            }}
                          />
                          <div className="flex justify-end space-x-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setReplyingTo(null)
                                setReplyContent('')
                              }}
                              className="text-xs"
                            >
                              Cancel
                            </Button>
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleAddReply(annotation.id)}
                              disabled={!replyContent.trim()}
                              className="text-xs"
                            >
                              Reply
                            </Button>
                          </div>
                        </div>
                      </div>
                    ) : !readonly && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            setReplyingTo(annotation.id)
                          }}
                          className="text-xs text-gray-500 p-0 h-auto"
                        >
                          <ReplyIcon className="w-3 h-3 mr-1" />
                          Reply
                        </Button>
                      </div>
                    )}

                    {/* Footer */}
                    <div className="flex items-center justify-between mt-3 text-xs text-gray-500">
                      <span>{formatDate(annotation.createdAt)}</span>
                      {annotation.updatedAt !== annotation.createdAt && (
                        <span>edited</span>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>

        {filteredAndSortedAnnotations.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <ChatBubbleBottomCenterTextIcon className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p className="text-sm">
              {annotations.length === 0
                ? 'No annotations yet'
                : 'No annotations match your filters'}
            </p>
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-xs text-gray-600 text-center">
          {filteredAndSortedAnnotations.length} of {annotations.length} annotations
        </div>
      </div>
    </div>
  )
}