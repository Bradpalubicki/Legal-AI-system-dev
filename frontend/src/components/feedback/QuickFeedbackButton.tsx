'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog'
import { MessageCircle, Star, ThumbsUp, ThumbsDown } from 'lucide-react'
import { FeedbackForm } from './FeedbackForm'
import { toast } from '@/components/ui/use-toast'

interface QuickFeedbackButtonProps {
  contentId: string
  contentType: 'document_analysis' | 'legal_research' | 'citation_check' | 'contract_review'
  variant?: 'default' | 'outline' | 'ghost' | 'floating'
  size?: 'sm' | 'default' | 'lg'
  showQuickActions?: boolean
  className?: string
}

export function QuickFeedbackButton({ 
  contentId, 
  contentType, 
  variant = 'outline',
  size = 'sm',
  showQuickActions = true,
  className = ''
}: QuickFeedbackButtonProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const submitQuickRating = async (rating: 'positive' | 'negative') => {
    if (isSubmitting) return
    
    try {
      setIsSubmitting(true)
      
      // Submit as accuracy feedback
      const response = await fetch('/api/feedback/accuracy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current_user', // TODO: Get from auth context
          content_id: contentId,
          rating: rating === 'positive' ? 'GOOD' : 'FAIR',
          comment: `Quick ${rating} rating`,
          specific_issues: []
        })
      })
      
      if (!response.ok) {
        throw new Error('Failed to submit rating')
      }
      
      toast({
        title: 'Thank you!',
        description: `Your ${rating} rating has been recorded.`,
      })
      
    } catch (error) {
      toast({
        title: 'Rating Failed',
        description: 'Please try again or use detailed feedback',
        variant: 'destructive'
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (variant === 'floating') {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Dialog open={isOpen} onOpenChange={setIsOpen}>
          <DialogTrigger asChild>
            <Button
              size="lg"
              className="rounded-full shadow-lg hover:shadow-xl transition-shadow"
            >
              <MessageCircle className="h-5 w-5 mr-2" />
              Feedback
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <FeedbackForm 
              contentId={contentId}
              contentType={contentType}
              onClose={() => setIsOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>
    )
  }

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {showQuickActions && (
        <>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => submitQuickRating('positive')}
            disabled={isSubmitting}
            className="text-green-600 hover:text-green-700 hover:bg-green-50"
            title="This was helpful"
          >
            <ThumbsUp className="h-4 w-4" />
          </Button>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => submitQuickRating('negative')}
            disabled={isSubmitting}
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
            title="This needs improvement"
          >
            <ThumbsDown className="h-4 w-4" />
          </Button>
          
          <div className="w-px h-4 bg-gray-300" />
        </>
      )}
      
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogTrigger asChild>
          <Button variant={variant} size={size}>
            <MessageCircle className="h-4 w-4 mr-2" />
            Detailed Feedback
          </Button>
        </DialogTrigger>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <FeedbackForm 
            contentId={contentId}
            contentType={contentType}
            onClose={() => setIsOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  )
}

// Simplified version for inline use
export function InlineFeedbackButtons({ 
  contentId, 
  contentType 
}: { 
  contentId: string
  contentType: 'document_analysis' | 'legal_research' | 'citation_check' | 'contract_review'
}) {
  const [ratings, setRatings] = useState<{ thumbsUp?: boolean; thumbsDown?: boolean }>({})

  const handleQuickRating = async (type: 'up' | 'down') => {
    try {
      await fetch('/api/feedback/accuracy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'current_user', // TODO: Get from auth context
          content_id: contentId,
          rating: type === 'up' ? 'GOOD' : 'FAIR',
          comment: `Quick ${type === 'up' ? 'positive' : 'negative'} rating`
        })
      })
      
      setRatings({ [type === 'up' ? 'thumbsUp' : 'thumbsDown']: true })
      
      toast({
        title: 'Rating recorded',
        description: 'Thank you for your feedback!'
      })
    } catch (error) {
      toast({
        title: 'Failed to record rating',
        description: 'Please try again',
        variant: 'destructive'
      })
    }
  }

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleQuickRating('up')}
        disabled={!!ratings.thumbsUp}
        className={`h-6 px-2 ${ratings.thumbsUp ? 'text-green-600 bg-green-50' : 'text-muted-foreground hover:text-green-600'}`}
      >
        <ThumbsUp className="h-3 w-3" />
        {ratings.thumbsUp && <span className="ml-1 text-xs">✓</span>}
      </Button>
      
      <Button
        variant="ghost"
        size="sm"
        onClick={() => handleQuickRating('down')}
        disabled={!!ratings.thumbsDown}
        className={`h-6 px-2 ${ratings.thumbsDown ? 'text-red-600 bg-red-50' : 'text-muted-foreground hover:text-red-600'}`}
      >
        <ThumbsDown className="h-3 w-3" />
        {ratings.thumbsDown && <span className="ml-1 text-xs">✓</span>}
      </Button>
    </div>
  )
}