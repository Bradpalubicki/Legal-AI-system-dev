'use client'

/**
 * Case Search Component
 *
 * Provides interface for searching case law across legal databases.
 * Supports filtering by court, date range, and jurisdiction.
 */

import { useState, useEffect } from 'react'
import { researchApi } from '@/lib/api/research'
import type {
  CaseSearchRequest,
  CaseSearchResult,
  Court
} from '@/types/research'

interface CaseSearchProps {
  onCaseSelect?: (caseResult: CaseSearchResult) => void
  initialQuery?: string
}

export default function CaseSearch({ onCaseSelect, initialQuery }: CaseSearchProps) {
  const [query, setQuery] = useState(initialQuery || '')
  const [court, setCourt] = useState<string>('')
  const [dateAfter, setDateAfter] = useState<string>('')
  const [dateBefore, setDateBefore] = useState<string>('')
  const [jurisdiction, setJurisdiction] = useState<string>('')
  const [limit, setLimit] = useState<number>(20)

  const [results, setResults] = useState<CaseSearchResult[]>([])
  const [totalResults, setTotalResults] = useState<number>(0)
  const [providersUsed, setProvidersUsed] = useState<string[]>([])
  const [courts, setCourts] = useState<Court[]>([])

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load available courts on mount
  useEffect(() => {
    loadCourts()
  }, [])

  const loadCourts = async () => {
    try {
      const response = await researchApi.getCourts()
      setCourts(response.courts)
    } catch (err) {
      console.error('Failed to load courts:', err)
    }
  }

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const request: CaseSearchRequest = {
        query: query.trim(),
        court: court || undefined,
        date_filed_after: dateAfter || undefined,
        date_filed_before: dateBefore || undefined,
        jurisdiction: jurisdiction || undefined,
        limit
      }

      const response = await researchApi.searchCases(request)

      setResults(response.results)
      setTotalResults(response.total_results)
      setProvidersUsed(response.providers_used)

      if (response.results.length === 0) {
        setError('No cases found matching your search criteria')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to search cases. Please try again.')
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }

  const clearFilters = () => {
    setCourt('')
    setDateAfter('')
    setDateBefore('')
    setJurisdiction('')
    setLimit(20)
  }

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <form onSubmit={handleSearch} className="bg-white rounded-lg shadow p-6 space-y-4">
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
            Search Query *
          </label>
          <input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., fair use copyright, negligence medical malpractice"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter keywords, legal concepts, or issues to search for relevant case law
          </p>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label htmlFor="court" className="block text-sm font-medium text-gray-700 mb-2">
              Court
            </label>
            <select
              id="court"
              value={court}
              onChange={(e) => setCourt(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            >
              <option value="">All Courts</option>
              {courts.map((c) => (
                <option key={c.code} value={c.code}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="dateAfter" className="block text-sm font-medium text-gray-700 mb-2">
              Filed After
            </label>
            <input
              id="dateAfter"
              type="date"
              value={dateAfter}
              onChange={(e) => setDateAfter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="dateBefore" className="block text-sm font-medium text-gray-700 mb-2">
              Filed Before
            </label>
            <input
              id="dateBefore"
              type="date"
              value={dateBefore}
              onChange={(e) => setDateBefore(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="limit" className="block text-sm font-medium text-gray-700 mb-2">
              Max Results
            </label>
            <select
              id="limit"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value))}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Searching...' : 'Search Cases'}
          </button>
          <button
            type="button"
            onClick={clearFilters}
            disabled={loading}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 transition-colors"
          >
            Clear Filters
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

      {/* Results Summary */}
      {!loading && results.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-blue-800">
              Found <strong>{totalResults}</strong> case{totalResults !== 1 ? 's' : ''} matching "{query}"
            </p>
            {providersUsed.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-blue-600">Sources:</span>
                {providersUsed.map((provider) => (
                  <span
                    key={provider}
                    className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                  >
                    {provider}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Results List */}
      {!loading && results.length > 0 && (
        <div className="space-y-4">
          {results.map((result, index) => (
            <div
              key={`${result.case_id}-${index}`}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6 cursor-pointer"
              onClick={() => onCaseSelect?.(result)}
            >
              <div className="space-y-3">
                {/* Case Name and Citation */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 hover:text-blue-600">
                    {result.case_name}
                  </h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {result.citation} • {result.court}
                  </p>
                </div>

                {/* Snippet */}
                {result.snippet && (
                  <p className="text-sm text-gray-700 line-clamp-3">
                    {result.snippet}
                  </p>
                )}

                {/* Metadata */}
                <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    {formatDate(result.date_filed)}
                  </span>

                  {result.docket_number && (
                    <span>Docket: {result.docket_number}</span>
                  )}

                  {result.relevance_score && (
                    <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded">
                      {Math.round(result.relevance_score * 100)}% relevant
                    </span>
                  )}

                  <span className="ml-auto px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                    {result.provider}
                  </span>
                </div>

                {/* Judges */}
                {result.judges && result.judges.length > 0 && (
                  <div className="text-xs text-gray-600">
                    Judges: {result.judges.join(', ')}
                  </div>
                )}

                {/* URL */}
                {result.url && (
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-xs text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1"
                  >
                    View Full Case
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </a>
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
            <p className="mt-4 text-gray-600">Searching legal databases...</p>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && results.length === 0 && query && (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No results found</h3>
          <p className="mt-2 text-sm text-gray-500">
            Try adjusting your search query or filters to find more cases
          </p>
        </div>
      )}
    </div>
  )
}
