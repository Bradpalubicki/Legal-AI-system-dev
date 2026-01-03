'use client'

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { HelpCircle, X, MessageCircle, Lightbulb, BookOpen, Zap } from 'lucide-react'

// Types
type HelpTriggerType = 'hover' | 'click' | 'focus' | 'error' | 'first_time' | 'context_change' | 'idle' | 'request'
type HelpContentType = 'tooltip' | 'popover' | 'modal' | 'spotlight' | 'tour_step' | 'inline' | 'video' | 'interactive'
type HelpPriority = 'low' | 'medium' | 'high' | 'critical'

interface HelpContent {
  content_id: string
  title: string
  content: string
  content_type: HelpContentType
  trigger_type: HelpTriggerType
  priority: HelpPriority
  target_roles: string[]
  target_experience_levels: string[]
  prerequisites: string[]
  tags: string[]
  media_url?: string
  duration_estimate?: number
  interaction_required: boolean
  auto_dismiss_timeout?: number
  show_count_limit?: number
  metadata: Record<string, any>
}

interface HelpPosition {
  x: number
  y: number
  element?: HTMLElement
  placement?: 'top' | 'bottom' | 'left' | 'right'
}

interface ContextualHelpContextValue {
  showHelp: (
    elementId: string,
    triggerType?: HelpTriggerType,
    context?: Record<string, any>
  ) => Promise<void>
  hideHelp: () => void
  recordInteraction: (
    contentId: string,
    interactionType: string,
    helpfulRating?: number
  ) => Promise<void>
  isHelpVisible: boolean
  helpContent: HelpContent | null
  position: HelpPosition | null
}

const ContextualHelpContext = createContext<ContextualHelpContextValue | null>(null)

interface ContextualHelpProviderProps {
  children: ReactNode
  userId: string
  userRole: string
  experienceLevel: string
  apiBaseUrl?: string
}

export function ContextualHelpProvider({
  children,
  userId,
  userRole,
  experienceLevel,
  apiBaseUrl = '/api'
}: ContextualHelpProviderProps) {
  const [isHelpVisible, setIsHelpVisible] = useState(false)
  const [helpContent, setHelpContent] = useState<HelpContent | null>(null)
  const [position, setPosition] = useState<HelpPosition | null>(null)
  const [dismissTimer, setDismissTimer] = useState<NodeJS.Timeout | null>(null)

  const hideHelp = useCallback(() => {
    setIsHelpVisible(false)
    setHelpContent(null)
    setPosition(null)
    if (dismissTimer) {
      clearTimeout(dismissTimer)
      setDismissTimer(null)
    }
  }, [dismissTimer])

  const showHelp = useCallback(async (
    elementId: string,
    triggerType: HelpTriggerType = 'hover',
    context: Record<string, any> = {}
  ) => {
    try {
      // Get the target element
      const element = document.querySelector(`[data-help-id="${elementId}"]`) as HTMLElement
      if (!element) {
        console.warn(`Help element with id "${elementId}" not found`)
        return
      }

      // Get help content from API
      const response = await fetch(`${apiBaseUrl}/contextual-help/get-help/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          element_id: elementId,
          page_url: window.location.pathname,
          trigger_type: triggerType,
          context: {
            user_role: userRole,
            experience_level: experienceLevel,
            ...context
          }
        })
      })

      if (!response.ok) {
        console.error('Failed to fetch help content')
        return
      }

      const helpContents: HelpContent[] = await response.json()

      if (helpContents.length === 0) {
        return // No help content available
      }

      const content = helpContents[0] // Use the first (most relevant) help content

      // Calculate position relative to the element
      const rect = element.getBoundingClientRect()
      const placement = determineOptimalPlacement(rect)

      setHelpContent(content)
      setPosition({
        x: rect.left + rect.width / 2,
        y: rect.top,
        element,
        placement
      })
      setIsHelpVisible(true)

      // Record interaction
      await recordInteraction(content.content_id, 'viewed')

      // Set auto-dismiss timer if specified
      if (content.auto_dismiss_timeout) {
        const timer = setTimeout(() => {
          hideHelp()
          recordInteraction(content.content_id, 'auto_dismissed')
        }, content.auto_dismiss_timeout * 1000)
        setDismissTimer(timer)
      }

    } catch (error) {
      console.error('Error showing contextual help:', error)
    }
  }, [userId, userRole, experienceLevel, apiBaseUrl])

  const recordInteraction = useCallback(async (
    contentId: string,
    interactionType: string,
    helpfulRating?: number
  ) => {
    try {
      await fetch(`${apiBaseUrl}/contextual-help/interaction/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          content_id: contentId,
          interaction_type: interactionType,
          element_id: position?.element?.getAttribute('data-help-id'),
          context: {
            page_url: window.location.pathname,
            user_role: userRole,
            experience_level: experienceLevel
          },
          helpful_rating: helpfulRating
        })
      })
    } catch (error) {
      console.error('Error recording help interaction:', error)
    }
  }, [userId, apiBaseUrl, userRole, experienceLevel, position])

  const contextValue: ContextualHelpContextValue = {
    showHelp,
    hideHelp,
    recordInteraction,
    isHelpVisible,
    helpContent,
    position
  }

  return (
    <ContextualHelpContext.Provider value={contextValue}>
      {children}
      <HelpRenderer />
    </ContextualHelpContext.Provider>
  )
}

function determineOptimalPlacement(rect: DOMRect): 'top' | 'bottom' | 'left' | 'right' {
  const viewportHeight = window.innerHeight
  const viewportWidth = window.innerWidth

  // Prefer top if there's space, otherwise bottom
  if (rect.top > 200) {
    return 'top'
  } else if (rect.bottom < viewportHeight - 200) {
    return 'bottom'
  } else if (rect.left > 300) {
    return 'left'
  } else {
    return 'right'
  }
}

function HelpRenderer() {
  const context = useContext(ContextualHelpContext)
  if (!context) return null

  const { isHelpVisible, helpContent, position, hideHelp, recordInteraction } = context

  if (!isHelpVisible || !helpContent || !position) {
    return null
  }

  const handleDismiss = () => {
    recordInteraction(helpContent.content_id, 'dismissed')
    hideHelp()
  }

  const handleRate = (rating: number) => {
    recordInteraction(helpContent.content_id, 'rated', rating)
  }

  return (
    <AnimatePresence>
      {isHelpVisible && (
        <>
          {/* Backdrop for modal/spotlight */}
          {(helpContent.content_type === 'modal' || helpContent.content_type === 'spotlight') && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40"
              onClick={helpContent.content_type === 'modal' ? handleDismiss : undefined}
            />
          )}

          {/* Help Content */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 10 }}
            style={{
              position: 'fixed',
              left: getHelpPositionX(position, helpContent.content_type),
              top: getHelpPositionY(position, helpContent.content_type),
              zIndex: helpContent.content_type === 'modal' ? 50 : 30
            }}
            className={getHelpClassName(helpContent)}
          >
            <HelpContentRenderer
              content={helpContent}
              onDismiss={handleDismiss}
              onRate={handleRate}
            />
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

function getHelpPositionX(position: HelpPosition, contentType: HelpContentType): number {
  if (contentType === 'modal') {
    return window.innerWidth / 2 - 200 // Center modal
  }

  switch (position.placement) {
    case 'left':
      return position.x - 320
    case 'right':
      return position.x + 20
    default:
      return position.x - 150 // Center for top/bottom
  }
}

function getHelpPositionY(position: HelpPosition, contentType: HelpContentType): number {
  if (contentType === 'modal') {
    return window.innerHeight / 2 - 150 // Center modal
  }

  switch (position.placement) {
    case 'top':
      return position.y - 120
    case 'bottom':
      return position.y + 40
    case 'left':
    case 'right':
      return position.y - 60
    default:
      return position.y - 60
  }
}

function getHelpClassName(content: HelpContent): string {
  const baseClasses = "bg-white border border-gray-200 shadow-lg rounded-lg"

  switch (content.content_type) {
    case 'tooltip':
      return `${baseClasses} px-3 py-2 text-sm max-w-xs`
    case 'popover':
      return `${baseClasses} px-4 py-3 max-w-sm`
    case 'modal':
      return `${baseClasses} px-6 py-4 max-w-md w-96`
    case 'spotlight':
      return `${baseClasses} px-4 py-3 max-w-sm border-yellow-300 bg-yellow-50`
    default:
      return `${baseClasses} px-4 py-3 max-w-sm`
  }
}

interface HelpContentRendererProps {
  content: HelpContent
  onDismiss: () => void
  onRate: (rating: number) => void
}

function HelpContentRenderer({ content, onDismiss, onRate }: HelpContentRendererProps) {
  const getIcon = () => {
    switch (content.content_type) {
      case 'tooltip':
        return <HelpCircle className="w-4 h-4 text-blue-500" />
      case 'popover':
        return <MessageCircle className="w-5 h-5 text-blue-500" />
      case 'modal':
        return <BookOpen className="w-5 h-5 text-blue-500" />
      case 'spotlight':
        return <Lightbulb className="w-5 h-5 text-yellow-600" />
      case 'tour_step':
        return <Zap className="w-5 h-5 text-purple-500" />
      default:
        return <HelpCircle className="w-4 h-4 text-blue-500" />
    }
  }

  const showRating = content.content_type !== 'tooltip' && !content.auto_dismiss_timeout

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          {getIcon()}
          <h3 className="font-medium text-gray-900 text-sm">
            {content.title}
          </h3>
        </div>
        <button
          onClick={onDismiss}
          className="text-gray-400 hover:text-gray-600 p-1"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div
        className="text-sm text-gray-700 mb-3"
        dangerouslySetInnerHTML={{ __html: content.content }}
      />

      {/* Media */}
      {content.media_url && (
        <div className="mb-3">
          {content.media_url.endsWith('.mp4') ? (
            <video
              src={content.media_url}
              controls
              className="w-full rounded border"
              style={{ maxHeight: '200px' }}
            />
          ) : (
            <img
              src={content.media_url}
              alt={content.title}
              className="w-full rounded border"
              style={{ maxHeight: '200px', objectFit: 'cover' }}
            />
          )}
        </div>
      )}

      {/* Duration estimate */}
      {content.duration_estimate && (
        <div className="text-xs text-gray-500 mb-2">
          Estimated time: {Math.ceil(content.duration_estimate / 60)} min
        </div>
      )}

      {/* Rating */}
      {showRating && (
        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
          <span className="text-xs text-gray-500">Was this helpful?</span>
          <div className="flex gap-1">
            {[1, 2, 3, 4, 5].map((rating) => (
              <button
                key={rating}
                onClick={() => onRate(rating)}
                className="w-6 h-6 text-xs bg-gray-100 hover:bg-blue-100
                         text-gray-600 hover:text-blue-600 rounded border"
              >
                {rating}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// Hook for using contextual help
export function useContextualHelp() {
  const context = useContext(ContextualHelpContext)
  if (!context) {
    throw new Error('useContextualHelp must be used within ContextualHelpProvider')
  }
  return context
}

// HOC for adding help to components
interface WithHelpProps {
  helpId?: string
  helpTrigger?: HelpTriggerType
  helpContext?: Record<string, any>
}

export function withHelp<P extends object>(
  WrappedComponent: React.ComponentType<P>
) {
  return function HelpEnabledComponent(props: P & WithHelpProps) {
    const { helpId, helpTrigger = 'hover', helpContext, ...componentProps } = props
    const { showHelp } = useContextualHelp()

    const handleHelp = () => {
      if (helpId) {
        showHelp(helpId, helpTrigger, helpContext)
      }
    }

    return (
      <div
        data-help-id={helpId}
        onMouseEnter={helpTrigger === 'hover' ? handleHelp : undefined}
        onClick={helpTrigger === 'click' ? handleHelp : undefined}
        onFocus={helpTrigger === 'focus' ? handleHelp : undefined}
      >
        <WrappedComponent {...(componentProps as P)} />
      </div>
    )
  }
}

// Helper component for help triggers
interface HelpTriggerProps {
  id: string
  trigger?: HelpTriggerType
  context?: Record<string, any>
  children: ReactNode
  className?: string
}

export function HelpTrigger({
  id,
  trigger = 'hover',
  context,
  children,
  className = ''
}: HelpTriggerProps) {
  const { showHelp } = useContextualHelp()

  const handleTrigger = () => {
    showHelp(id, trigger, context)
  }

  return (
    <div
      data-help-id={id}
      className={className}
      onMouseEnter={trigger === 'hover' ? handleTrigger : undefined}
      onClick={trigger === 'click' ? handleTrigger : undefined}
      onFocus={trigger === 'focus' ? handleTrigger : undefined}
    >
      {children}
    </div>
  )
}