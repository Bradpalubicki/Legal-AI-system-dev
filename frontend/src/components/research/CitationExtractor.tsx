'use client'

/**
 * Citation Extraction Component
 *
 * Extracts and validates legal citations from text.
 * Supports case law, statutes, regulations, and constitutional citations.
 */

import { useState } from 'react'
import { researchApi } from '@/lib/api/research'
import type {
  CitationExtractionRequest,
  ExtractedCitation,
  CitationType,
  CitationStatus
} from '@/types/research'

interface CitationExtractorProps {
  onCitationSelect?: (citation: ExtractedCitation) => void
  initialText?: string
}

export default function CitationExtractor({ onCitationSelect, initialText }: CitationExtractorProps) {
  const [text, setText] = useState(initialText || '')
  const [validate, setValidate] = useState(true)
  const [filterType, setFilterType] = useState<string>('')

  const [citations, setCitations] = useState<ExtractedCitation[]>([])
  const [totalCitations, setTotalCitations] = useState<number>(0)
  const [byType, setByType] = useState<Record<string, number>>({})
  const [byStatus, setByStatus] = useState<Record<string, number>>({})
  const [validationRate, setValidationRate] = useState<number>(0)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedCitation, setSelectedCitation] = useState<ExtractedCitation | null>(null)

  const handleExtract = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!text.trim()) {
      setError('Please enter text to extract citations from')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const request: CitationExtractionRequest = {
        text: text.trim(),
        validate,
        citation_types: filterType ? [filterType] : undefined
      }

      const response = await researchApi.extractCitations(request)

      setCitations(response.citations)
      setTotalCitations(response.total_citations)
      setByType(response.by_type)
      setByStatus(response.by_status)
      setValidationRate(response.validation_rate)

      if (response.citations.length === 0) {
        setError('No citations found in the provided text')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to extract citations. Please try again.')
      console.error('Extraction error:', err)
    } finally {
      setLoading(false)
    }
  }

  const getCitationTypeColor = (type: CitationType | string) => {
    const typeStr = typeof type === 'string' ? type : type
    switch (typeStr) {
      case CitationType.CASE:
      case 'case':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case CitationType.STATUTE:
      case 'statute':
        return 'bg-green-100 text-green-800 border-green-200'
      case CitationType.REGULATION:
      case 'regulation':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case CitationType.CONSTITUTIONAL:
      case 'constitutional':
        return 'bg-red-100 text-red-800 border-red-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getCitationStatusColor = (status: CitationStatus | string) => {
    const statusStr = typeof status === 'string' ? status : status
    switch (statusStr) {
      case CitationStatus.VALID:
      case 'valid':
        return 'bg-green-50 border-green-200 text-green-700'
      case CitationStatus.INVALID:
      case 'invalid':
        return 'bg-red-50 border-red-200 text-red-700'
      case CitationStatus.AMBIGUOUS:
      case 'ambiguous':
        return 'bg-yellow-50 border-yellow-200 text-yellow-700'
      default:
        return 'bg-gray-50 border-gray-200 text-gray-700'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const highlightCitationsInText = () => {
    if (!text || citations.length === 0) return text

    const parts: JSX.Element[] = []
    let lastIndex = 0

    // Sort citations by position
    const sortedCitations = [...citations].sort((a, b) => a.span[0] - b.span[0])

    sortedCitations.forEach((citation, idx) => {
      const [start, end] = citation.span

      // Add text before citation
      if (start > lastIndex) {
        parts.push(
          <span key={`text-${idx}`}>
            {text.substring(lastIndex, start)}
          </span>
        )
      }

      // Add highlighted citation
      parts.push(
        <span
          key={`cite-${idx}`}
          className={`${getCitationTypeColor(citation.type)} px-1 py-0.5 rounded cursor-pointer hover:opacity-80`}
          onClick={() => setSelectedCitation(citation)}
          title={`${citation.type} - ${citation.status} (${Math.round(citation.confidence * 100)}% confidence)`}
        >
          {text.substring(start, end)}
        </span>
      )

      lastIndex = end
    })

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(
        <span key="text-end">
          {text.substring(lastIndex)}
        </span>
      )
    }

    return parts
  }

  return (
    <div className="space-y-6">
      {/* Input Form */}
      <form onSubmit={handleExtract} className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <label htmlFor="text" className="block text-sm font-medium text-gray-700 mb-2">
            Legal Text *
          </label>
          <textarea
            id="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste legal document text here to extract citations..."
            rows={10}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            disabled={loading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter text containing legal citations (cases, statutes, regulations, etc.)
          </p>
        </div>

        {/* Options */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={validate}
                onChange={(e) => setValidate(e.target.checked)}
                disabled={loading}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">Validate citations against legal databases</span>
            </label>
          </div>

          <div>
            <label htmlFor="filterType" className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Type
            </label>
            <select
              id="filterType"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            >
              <option value="">All Types</option>
              <option value="case">Case Law</option>
              <option value="statute">Statutes</option>
              <option value="regulation">Regulations</option>
              <option value="constitutional">Constitutional</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading || !text.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Extracting...' : 'Extract Citations'}
          </button>
          <button
            type="button"
            onClick={() => {
              setText('')
              setCitations([])
              setError(null)
              setSelectedCitation(null)
            }}
            disabled={loading}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 transition-colors"
          >
            Clear
          </button>
        </div>
      </form>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-600 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Summary Statistics */}
      {!loading && citations.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Total Citations</p>
            <p className="text-2xl font-bold text-gray-900">{totalCitations}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Validation Rate</p>
            <p className="text-2xl font-bold text-green-600">{Math.round(validationRate * 100)}%</p>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600 mb-2">By Type</p>
            <div className="space-y-1">
              {Object.entries(byType).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between text-xs">
                  <span className="capitalize">{type}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600 mb-2">By Status</p>
            <div className="space-y-1">
              {Object.entries(byStatus).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between text-xs">
                  <span className="capitalize">{status}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Highlighted Text View */}
      {!loading && citations.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Highlighted Citations
          </h3>
          <div className="prose max-w-none">
            <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
              {highlightCitationsInText()}
            </div>
          </div>
          <p className="mt-4 text-xs text-gray-500">
            Click on a highlighted citation to view details
          </p>
        </div>
      )}

      {/* Citations List */}
      {!loading && citations.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">
            Extracted Citations ({citations.length})
          </h3>

          {citations.map((citation, index) => (
            <div
              key={index}
              className={`bg-white rounded-lg shadow p-4 cursor-pointer transition-all ${
                selectedCitation === citation ? 'ring-2 ring-blue-500' : ''
              }`}
              onClick={() => {
                setSelectedCitation(citation)
                onCitationSelect?.(citation)
              }}
            >
              <div className="space-y-3">
                {/* Citation Text and Badges */}
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-mono text-sm text-gray-900 mb-2">
                      {citation.text}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded border ${getCitationTypeColor(citation.type)}`}>
                        {citation.type}
                      </span>
                      <span className={`px-2 py-1 text-xs font-medium rounded border ${getCitationStatusColor(citation.status)}`}>
                        {citation.status}
                      </span>
                      <span className={`px-2 py-1 text-xs font-medium ${getConfidenceColor(citation.confidence)}`}>
                        {Math.round(citation.confidence * 100)}% confident
                      </span>
                    </div>
                  </div>
                </div>

                {/* Citation Details */}
                {(citation.case_name || citation.full_case_name || citation.title) && (
                  <div className="space-y-2 text-sm">
                    {(citation.case_name || citation.full_case_name) && (
                      <div>
                        <span className="font-medium text-gray-700">Case: </span>
                        <span className="text-gray-900">{citation.full_case_name || citation.case_name}</span>
                      </div>
                    )}

                    {citation.court && (
                      <div>
                        <span className="font-medium text-gray-700">Court: </span>
                        <span className="text-gray-900">{citation.court}</span>
                      </div>
                    )}

                    {citation.year && (
                      <div>
                        <span className="font-medium text-gray-700">Year: </span>
                        <span className="text-gray-900">{citation.year}</span>
                      </div>
                    )}

                    {citation.title && (
                      <div>
                        <span className="font-medium text-gray-700">Title: </span>
                        <span className="text-gray-900">{citation.title}</span>
                      </div>
                    )}

                    {citation.section && (
                      <div>
                        <span className="font-medium text-gray-700">Section: </span>
                        <span className="text-gray-900">{citation.section}</span>
                      </div>
                    )}

                    {citation.jurisdiction && (
                      <div>
                        <span className="font-medium text-gray-700">Jurisdiction: </span>
                        <span className="text-gray-900">{citation.jurisdiction}</span>
                      </div>
                    )}

                    {citation.bluebook && (
                      <div>
                        <span className="font-medium text-gray-700">Bluebook: </span>
                        <span className="text-gray-900 font-mono text-xs">{citation.bluebook}</span>
                      </div>
                    )}

                    {citation.url && (
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1 text-xs"
                      >
                        View Source
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Extracting citations...</p>
          </div>
        </div>
      )}
    </div>
  )
}
