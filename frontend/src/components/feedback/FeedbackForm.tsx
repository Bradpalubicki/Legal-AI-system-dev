'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/Input'
import { toast } from '@/components/ui/use-toast'
import { Loader2, Star, AlertTriangle, ThumbsUp, MessageSquare } from 'lucide-react'

interface FeedbackFormProps {
  contentId: string
  contentType: 'document_analysis' | 'legal_research' | 'citation_check' | 'contract_review'
  onClose?: () => void
}

type FeedbackType = 'accuracy' | 'usefulness' | 'error' | 'suggestion'

const accuracyRatings = [
  { value: 'EXCELLENT', label: 'Excellent', description: 'Completely accurate and reliable' },
  { value: 'GOOD', label: 'Good', description: 'Mostly accurate with minor issues' },
  { value: 'FAIR', label: 'Fair', description: 'Some accuracy concerns' },
  { value: 'POOR', label: 'Poor', description: 'Several inaccuracies found' },
  { value: 'VERY_POOR', label: 'Very Poor', description: 'Significantly inaccurate' }
]

const usefulnessRatings = [
  { value: 'VERY_USEFUL', label: 'Very Useful', description: 'Highly valuable and actionable' },
  { value: 'USEFUL', label: 'Useful', description: 'Generally helpful' },
  { value: 'SOMEWHAT_USEFUL', label: 'Somewhat Useful', description: 'Limited value' },
  { value: 'NOT_USEFUL', label: 'Not Useful', description: 'No practical value' }
]

const commonIssues = [
  { id: 'incorrect_facts', label: 'Incorrect facts or data' },
  { id: 'outdated_info', label: 'Outdated information' },
  { id: 'missing_context', label: 'Missing important context' },
  { id: 'wrong_jurisdiction', label: 'Wrong jurisdiction cited' },
  { id: 'bad_citations', label: 'Incorrect or invalid citations' },
  { id: 'unclear_language', label: 'Unclear or confusing language' }
]

const errorTypes = [
  { value: 'factual', label: 'Factual Error' },
  { value: 'legal', label: 'Legal Error' },
  { value: 'citation', label: 'Citation Error' },
  { value: 'formatting', label: 'Formatting Issue' },
  { value: 'ui', label: 'User Interface Problem' },
  { value: 'performance', label: 'Performance Issue' }
]

const errorSeverities = [
  { value: 'low', label: 'Low', description: 'Minor inconvenience' },
  { value: 'medium', label: 'Medium', description: 'Affects usability' },
  { value: 'high', label: 'High', description: 'Blocks important tasks' },
  { value: 'critical', label: 'Critical', description: 'System failure or data loss' }
]

export function FeedbackForm({ contentId, contentType, onClose }: FeedbackFormProps) {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('accuracy')
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  // Accuracy feedback state
  const [accuracyRating, setAccuracyRating] = useState('')
  const [accuracyComment, setAccuracyComment] = useState('')
  const [selectedIssues, setSelectedIssues] = useState<string[]>([])
  
  // Usefulness feedback state
  const [usefulnessRating, setUsefulnessRating] = useState('')
  const [usefulnessComment, setUsefulnessComment] = useState('')
  const [improvements, setImprovements] = useState('')
  
  // Error report state
  const [errorType, setErrorType] = useState('')
  const [errorSeverity, setErrorSeverity] = useState('medium')
  const [errorDescription, setErrorDescription] = useState('')
  const [expectedBehavior, setExpectedBehavior] = useState('')
  const [actualBehavior, setActualBehavior] = useState('')
  const [reproductionSteps, setReproductionSteps] = useState('')
  
  // Suggestion state
  const [suggestionTitle, setSuggestionTitle] = useState('')
  const [suggestionDescription, setSuggestionDescription] = useState('')
  const [suggestionCategory, setSuggestionCategory] = useState('general')
  
  const handleIssueChange = (issueId: string, checked: boolean) => {
    if (checked) {
      setSelectedIssues([...selectedIssues, issueId])
    } else {
      setSelectedIssues(selectedIssues.filter(id => id !== issueId))
    }
  }

  const submitAccuracyFeedback = async () => {
    const response = await fetch('/api/feedback/accuracy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'current_user', // TODO: Get from auth context
        content_id: contentId,
        rating: accuracyRating,
        comment: accuracyComment || null,
        specific_issues: selectedIssues
      })
    })
    
    if (!response.ok) {
      throw new Error('Failed to submit accuracy feedback')
    }
    
    const result = await response.json()
    return result
  }

  const submitUsefulnessFeedback = async () => {
    const improvementsList = improvements 
      ? improvements.split('\n').filter(item => item.trim())
      : []
    
    const response = await fetch('/api/feedback/usefulness', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'current_user', // TODO: Get from auth context
        content_id: contentId,
        rating: usefulnessRating,
        comment: usefulnessComment || null,
        improvement_suggestions: improvementsList
      })
    })
    
    if (!response.ok) {
      throw new Error('Failed to submit usefulness feedback')
    }
    
    return response.json()
  }

  const submitErrorReport = async () => {
    const steps = reproductionSteps 
      ? reproductionSteps.split('\n').filter(step => step.trim())
      : []
    
    const response = await fetch('/api/feedback/report-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'current_user', // TODO: Get from auth context
        content_id: contentId,
        error_type: errorType,
        description: errorDescription,
        severity: errorSeverity,
        steps_to_reproduce: steps,
        expected_behavior: expectedBehavior || null,
        actual_behavior: actualBehavior || null
      })
    })
    
    if (!response.ok) {
      throw new Error('Failed to submit error report')
    }
    
    return response.json()
  }

  const submitSuggestion = async () => {
    const response = await fetch('/api/feedback/suggestion', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: 'current_user', // TODO: Get from auth context
        title: suggestionTitle,
        description: suggestionDescription,
        category: suggestionCategory,
        priority: 'medium'
      })
    })
    
    if (!response.ok) {
      throw new Error('Failed to submit suggestion')
    }
    
    return response.json()
  }

  const handleSubmit = async () => {
    if (isSubmitting) return
    
    try {
      setIsSubmitting(true)
      
      let result
      switch (feedbackType) {
        case 'accuracy':
          if (!accuracyRating) {
            toast({
              title: 'Rating Required',
              description: 'Please select an accuracy rating',
              variant: 'destructive'
            })
            return
          }
          result = await submitAccuracyFeedback()
          break
        case 'usefulness':
          if (!usefulnessRating) {
            toast({
              title: 'Rating Required', 
              description: 'Please select a usefulness rating',
              variant: 'destructive'
            })
            return
          }
          result = await submitUsefulnessFeedback()
          break
        case 'error':
          if (!errorType || !errorDescription) {
            toast({
              title: 'Required Fields Missing',
              description: 'Please select error type and provide description',
              variant: 'destructive'
            })
            return
          }
          result = await submitErrorReport()
          break
        case 'suggestion':
          if (!suggestionTitle || !suggestionDescription) {
            toast({
              title: 'Required Fields Missing',
              description: 'Please provide title and description for your suggestion',
              variant: 'destructive'
            })
            return
          }
          result = await submitSuggestion()
          break
      }
      
      toast({
        title: 'Feedback Submitted',
        description: result.message || 'Thank you for your feedback!',
      })
      
      // Reset form
      setAccuracyRating('')
      setAccuracyComment('')
      setSelectedIssues([])
      setUsefulnessRating('')
      setUsefulnessComment('')
      setImprovements('')
      setErrorType('')
      setErrorDescription('')
      setExpectedBehavior('')
      setActualBehavior('')
      setReproductionSteps('')
      setSuggestionTitle('')
      setSuggestionDescription('')
      
      if (onClose) {
        onClose()
      }
      
    } catch (error) {
      toast({
        title: 'Submission Failed',
        description: error instanceof Error ? error.message : 'Please try again',
        variant: 'destructive'
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const renderFeedbackTypeSelector = () => (
    <div className="flex space-x-2 mb-6">
      <Button
        variant={feedbackType === 'accuracy' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setFeedbackType('accuracy')}
        className="flex items-center gap-1"
      >
        <Star className="h-4 w-4" />
        Accuracy
      </Button>
      <Button
        variant={feedbackType === 'usefulness' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setFeedbackType('usefulness')}
        className="flex items-center gap-1"
      >
        <ThumbsUp className="h-4 w-4" />
        Usefulness
      </Button>
      <Button
        variant={feedbackType === 'error' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setFeedbackType('error')}
        className="flex items-center gap-1"
      >
        <AlertTriangle className="h-4 w-4" />
        Report Error
      </Button>
      <Button
        variant={feedbackType === 'suggestion' ? 'default' : 'outline'}
        size="sm"
        onClick={() => setFeedbackType('suggestion')}
        className="flex items-center gap-1"
      >
        <MessageSquare className="h-4 w-4" />
        Suggest
      </Button>
    </div>
  )

  const renderAccuracyForm = () => (
    <div className="space-y-6">
      <div>
        <Label className="text-base font-medium">How accurate was this content?</Label>
        <RadioGroup value={accuracyRating} onValueChange={setAccuracyRating} className="mt-2">
          {accuracyRatings.map((rating) => (
            <div key={rating.value} className="flex items-start space-x-2">
              <RadioGroupItem value={rating.value} id={rating.value} className="mt-1" />
              <div>
                <Label htmlFor={rating.value} className="font-medium cursor-pointer">
                  {rating.label}
                </Label>
                <p className="text-sm text-muted-foreground">{rating.description}</p>
              </div>
            </div>
          ))}
        </RadioGroup>
      </div>

      {accuracyRating && ['FAIR', 'POOR', 'VERY_POOR'].includes(accuracyRating) && (
        <div>
          <Label className="text-base font-medium">What specific issues did you find?</Label>
          <div className="mt-2 space-y-2">
            {commonIssues.map((issue) => (
              <div key={issue.id} className="flex items-center space-x-2">
                <Checkbox
                  id={issue.id}
                  checked={selectedIssues.includes(issue.id)}
                  onCheckedChange={(checked) => handleIssueChange(issue.id, !!checked)}
                />
                <Label htmlFor={issue.id} className="cursor-pointer">
                  {issue.label}
                </Label>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <Label htmlFor="accuracy-comment">Additional Comments (Optional)</Label>
        <Textarea
          id="accuracy-comment"
          value={accuracyComment}
          onChange={(e) => setAccuracyComment(e.target.value)}
          placeholder="Provide specific details about accuracy issues or what was done well..."
          rows={3}
        />
      </div>
    </div>
  )

  const renderUsefulnessForm = () => (
    <div className="space-y-6">
      <div>
        <Label className="text-base font-medium">How useful was this content?</Label>
        <RadioGroup value={usefulnessRating} onValueChange={setUsefulnessRating} className="mt-2">
          {usefulnessRatings.map((rating) => (
            <div key={rating.value} className="flex items-start space-x-2">
              <RadioGroupItem value={rating.value} id={rating.value} className="mt-1" />
              <div>
                <Label htmlFor={rating.value} className="font-medium cursor-pointer">
                  {rating.label}
                </Label>
                <p className="text-sm text-muted-foreground">{rating.description}</p>
              </div>
            </div>
          ))}
        </RadioGroup>
      </div>

      <div>
        <Label htmlFor="usefulness-comment">What made it useful or not useful?</Label>
        <Textarea
          id="usefulness-comment"
          value={usefulnessComment}
          onChange={(e) => setUsefulnessComment(e.target.value)}
          placeholder="Describe how this content helped (or didn't help) with your task..."
          rows={3}
        />
      </div>

      <div>
        <Label htmlFor="improvements">Suggestions for improvement (one per line)</Label>
        <Textarea
          id="improvements"
          value={improvements}
          onChange={(e) => setImprovements(e.target.value)}
          placeholder="More detailed analysis&#10;Better organization&#10;Include more examples"
          rows={4}
        />
      </div>
    </div>
  )

  const renderErrorForm = () => (
    <div className="space-y-6">
      <div>
        <Label className="text-base font-medium">What type of error did you encounter?</Label>
        <RadioGroup value={errorType} onValueChange={setErrorType} className="mt-2">
          {errorTypes.map((type) => (
            <div key={type.value} className="flex items-center space-x-2">
              <RadioGroupItem value={type.value} id={type.value} />
              <Label htmlFor={type.value} className="cursor-pointer">
                {type.label}
              </Label>
            </div>
          ))}
        </RadioGroup>
      </div>

      <div>
        <Label className="text-base font-medium">How severe is this error?</Label>
        <RadioGroup value={errorSeverity} onValueChange={setErrorSeverity} className="mt-2">
          {errorSeverities.map((severity) => (
            <div key={severity.value} className="flex items-start space-x-2">
              <RadioGroupItem value={severity.value} id={severity.value} className="mt-1" />
              <div>
                <Label htmlFor={severity.value} className="font-medium cursor-pointer">
                  {severity.label}
                </Label>
                <p className="text-sm text-muted-foreground">{severity.description}</p>
              </div>
            </div>
          ))}
        </RadioGroup>
      </div>

      <div>
        <Label htmlFor="error-description">Describe the error *</Label>
        <Textarea
          id="error-description"
          value={errorDescription}
          onChange={(e) => setErrorDescription(e.target.value)}
          placeholder="Provide a clear description of what went wrong..."
          rows={3}
        />
      </div>

      <div>
        <Label htmlFor="expected-behavior">What did you expect to happen?</Label>
        <Textarea
          id="expected-behavior"
          value={expectedBehavior}
          onChange={(e) => setExpectedBehavior(e.target.value)}
          placeholder="Describe the expected behavior..."
          rows={2}
        />
      </div>

      <div>
        <Label htmlFor="actual-behavior">What actually happened?</Label>
        <Textarea
          id="actual-behavior"
          value={actualBehavior}
          onChange={(e) => setActualBehavior(e.target.value)}
          placeholder="Describe what actually occurred..."
          rows={2}
        />
      </div>

      <div>
        <Label htmlFor="reproduction-steps">Steps to reproduce (one per line)</Label>
        <Textarea
          id="reproduction-steps"
          value={reproductionSteps}
          onChange={(e) => setReproductionSteps(e.target.value)}
          placeholder="1. Upload document&#10;2. Click analyze button&#10;3. Error appears"
          rows={4}
        />
      </div>
    </div>
  )

  const renderSuggestionForm = () => (
    <div className="space-y-6">
      <div>
        <Label htmlFor="suggestion-title">Suggestion Title *</Label>
        <Input
          id="suggestion-title"
          value={suggestionTitle}
          onChange={(e) => setSuggestionTitle(e.target.value)}
          placeholder="Brief title for your suggestion..."
        />
      </div>

      <div>
        <Label htmlFor="suggestion-category">Category</Label>
        <RadioGroup value={suggestionCategory} onValueChange={setSuggestionCategory} className="mt-2">
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="general" id="general" />
            <Label htmlFor="general">General</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="feature" id="feature" />
            <Label htmlFor="feature">New Feature</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="ui" id="ui" />
            <Label htmlFor="ui">User Interface</Label>
          </div>
          <div className="flex items-center space-x-2">
            <RadioGroupItem value="performance" id="performance" />
            <Label htmlFor="performance">Performance</Label>
          </div>
        </RadioGroup>
      </div>

      <div>
        <Label htmlFor="suggestion-description">Detailed Description *</Label>
        <Textarea
          id="suggestion-description"
          value={suggestionDescription}
          onChange={(e) => setSuggestionDescription(e.target.value)}
          placeholder="Provide a detailed description of your suggestion, including the problem it solves and how it would help..."
          rows={5}
        />
      </div>
    </div>
  )

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Provide Feedback</CardTitle>
        <CardDescription>
          Help us improve by sharing your experience with this {contentType.replace('_', ' ')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {renderFeedbackTypeSelector()}

        {feedbackType === 'accuracy' && renderAccuracyForm()}
        {feedbackType === 'usefulness' && renderUsefulnessForm()}
        {feedbackType === 'error' && renderErrorForm()}
        {feedbackType === 'suggestion' && renderSuggestionForm()}

        <div className="flex justify-end space-x-2 mt-8">
          {onClose && (
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
          )}
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Submit Feedback
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}