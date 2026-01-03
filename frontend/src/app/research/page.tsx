'use client'

/**
 * Legal Research Page
 *
 * Main page for legal research features including:
 * - Case law search
 * - Citation extraction and validation
 * - Research provider management
 */

import { useState } from 'react'
import Layout from '@/components/layout/Layout'
import CaseSearch from '@/components/research/CaseSearch'
import CitationExtractor from '@/components/research/CitationExtractor'
import type { CaseSearchResult, ExtractedCitation } from '@/types/research'

type ResearchTab = 'case-search' | 'citation-extraction' | 'case-details'

export default function ResearchPage() {
  const [activeTab, setActiveTab] = useState<ResearchTab>('case-search')
  const [selectedCase, setSelectedCase] = useState<CaseSearchResult | null>(null)
  const [selectedCitation, setSelectedCitation] = useState<ExtractedCitation | null>(null)

  const handleCaseSelect = (caseResult: CaseSearchResult) => {
    setSelectedCase(caseResult)
    setActiveTab('case-details')
  }

  const handleCitationSelect = (citation: ExtractedCitation) => {
    setSelectedCitation(citation)
  }

  return (
    <Layout title="Legal Research">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Legal Research</h1>
              <p className="mt-1 text-sm text-gray-600">
                Search case law and extract citations from legal documents
              </p>
            </div>

            {/* Educational Disclaimer */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 max-w-md">
              <div className="flex items-start">
                <svg className="w-5 h-5 text-amber-600 mt-0.5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <div>
                  <h3 className="text-sm font-semibold text-amber-900">
                    Educational Tool
                  </h3>
                  <p className="text-xs text-amber-800 mt-1">
                    Research results are for educational purposes only. Always verify citations and case law independently.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow">
          <div className="border-b border-gray-200">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('case-search')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'case-search'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  Case Law Search
                </div>
              </button>

              <button
                onClick={() => setActiveTab('citation-extraction')}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'citation-extraction'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Citation Extraction
                </div>
              </button>

              {selectedCase && (
                <button
                  onClick={() => setActiveTab('case-details')}
                  className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === 'case-details'
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Case Details
                  </div>
                </button>
              )}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'case-search' && (
              <CaseSearch onCaseSelect={handleCaseSelect} />
            )}

            {activeTab === 'citation-extraction' && (
              <CitationExtractor onCitationSelect={handleCitationSelect} />
            )}

            {activeTab === 'case-details' && selectedCase && (
              <div className="space-y-6">
                {/* Case Header */}
                <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6">
                  <h2 className="text-xl font-bold text-gray-900 mb-2">
                    {selectedCase.case_name}
                  </h2>
                  <p className="text-sm text-gray-700 mb-4">
                    {selectedCase.citation} • {selectedCase.court}
                  </p>
                  <div className="flex flex-wrap gap-3">
                    <span className="px-3 py-1 bg-white rounded-full text-sm">
                      Filed: {new Date(selectedCase.date_filed).toLocaleDateString()}
                    </span>
                    {selectedCase.docket_number && (
                      <span className="px-3 py-1 bg-white rounded-full text-sm">
                        Docket: {selectedCase.docket_number}
                      </span>
                    )}
                    <span className="px-3 py-1 bg-white rounded-full text-sm">
                      Source: {selectedCase.provider}
                    </span>
                  </div>
                </div>

                {/* Case Content */}
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Overview</h3>
                  {selectedCase.snippet && (
                    <p className="text-gray-700 leading-relaxed mb-4">
                      {selectedCase.snippet}
                    </p>
                  )}

                  {selectedCase.judges && selectedCase.judges.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-semibold text-gray-900 mb-2">Judges</h4>
                      <p className="text-sm text-gray-700">
                        {selectedCase.judges.join(', ')}
                      </p>
                    </div>
                  )}

                  {selectedCase.url && (
                    <div className="mt-6">
                      <a
                        href={selectedCase.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                        </svg>
                        View Full Case on {selectedCase.provider}
                      </a>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    onClick={() => {
                      setActiveTab('case-search')
                      setSelectedCase(null)
                    }}
                    className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    Back to Search
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Research Tips */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="text-sm font-semibold text-blue-900 mb-3">Research Tips</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-blue-800">
            <div>
              <h4 className="font-semibold mb-1">Case Law Search:</h4>
              <ul className="list-disc list-inside space-y-1">
                <li>Use specific legal concepts and keywords</li>
                <li>Filter by court to narrow results</li>
                <li>Use date ranges for recent precedents</li>
                <li>Check multiple sources for comprehensiveness</li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-1">Citation Extraction:</h4>
              <ul className="list-disc list-inside space-y-1">
                <li>Paste document text to find all citations</li>
                <li>Enable validation to verify citations</li>
                <li>Filter by type for specific citation categories</li>
                <li>Use Bluebook format for proper citation</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
