'use client'

import { useState } from 'react'
import { Card } from './ui'
import {
  ExclamationTriangleIcon,
  AcademicCapIcon,
  InformationCircleIcon,
  QuestionMarkCircleIcon,
  UserGroupIcon,
  DocumentTextIcon,
  CalendarDaysIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline'

// Educational Analysis Types with enhanced language patterns
interface EnhancedEducationalAnalysis {
  document_type: string
  educational_explanation: string
  information_found: {
    parties_mentioned: string[]
    dates_mentioned: string[]
    amounts_mentioned: string[]
  }
  general_education: {
    what_this_document_type_means: string
    typical_timeline: string
    common_responses: string
    general_options: string
  }
  educational_questions: string[]
  disclaimers: {
    primary: string
    no_attorney_client: string
    consult_attorney: string
    verify_independently: string
    no_guarantees: string
  }
}

interface EnhancedEducationalAnalyzerProps {
  documentName: string
  onClose: () => void
}

// Enhanced educational document analyzer with proper language patterns
const analyzeDocumentEducationally = async (file: File): Promise<EnhancedEducationalAnalysis> => {
  // Simulate API call for educational analysis
  await new Promise(resolve => setTimeout(resolve, 2000))

  return {
    document_type: 'EDUCATIONAL INFORMATION: This type of document typically appears to be a Motion for Relief from Stay',
    educational_explanation: 'In legal education, documents of this type typically mean that creditors often request court permission to proceed with collection actions despite automatic stay protections that bankruptcy typically provides to debtors.',

    information_found: {
      parties_mentioned: ['First National Bank', 'ABC Company LLC', 'Trustee'],
      dates_mentioned: ['Filing deadline: 14 days from service', 'Hearing date: January 30, 2025'],
      amounts_mentioned: ['$45,000 outstanding loan balance', '$2,500 monthly payments']
    },

    general_education: {
      what_this_document_type_means: 'EDUCATIONAL INFORMATION: In general legal education, a Motion for Relief from Stay typically represents a formal request that creditors often file with bankruptcy courts. People often use these motions to ask for permission to continue collection efforts against property that automatic stays typically protect.',
      typical_timeline: 'Educational materials show that documents like this typically have 14-day response deadlines. Courts often schedule hearings within 30 days. Debtors typically have rights to respond and object to these motions.',
      common_responses: 'In educational scenarios, people often consider several typical approaches: filing objections, negotiating with creditors, consulting attorneys, or modifying bankruptcy plans. Legal education shows these are common paths people often explore.',
      general_options: 'Educational materials typically show that people often have several paths available: objecting to motions, negotiating payment plans, surrendering property, or seeking bankruptcy plan modifications. Legal education emphasizes that each situation typically has unique factors.'
    },

    educational_questions: [
      'For educational understanding, what is the typical role of debtors versus creditors in these situations?',
      'What do educational materials typically say about having legal representation in bankruptcy cases?',
      'What would be helpful to learn about how motions for relief from stay typically work?',
      'What educational information about typical timelines and processes would be useful?'
    ],

    disclaimers: {
      primary: 'EDUCATIONAL INFORMATION ONLY - This is not legal advice for any specific situation',
      no_attorney_client: 'No attorney-client relationship exists or is created by viewing this educational content',
      consult_attorney: 'People typically need to consult qualified attorneys for their specific legal situations',
      verify_independently: 'Educational information should typically be verified independently with legal counsel',
      no_guarantees: 'No guarantees about accuracy, completeness, or applicability - educational purposes only'
    }
  }
}

export default function EnhancedEducationalAnalyzer({ documentName, onClose }: EnhancedEducationalAnalyzerProps) {
  const [analysis, setAnalysis] = useState<EnhancedEducationalAnalysis | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([])

  const handleAnalyze = async () => {
    setIsLoading(true)
    try {
      // Create a mock file for educational analysis
      const mockFile = new File([''], documentName, { type: 'application/pdf' })
      const result = await analyzeDocumentEducationally(mockFile)
      setAnalysis(result)
    } catch (error) {
      console.error('Educational analysis error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Enhanced Educational Header with Critical Disclaimer */}
        <div className="bg-red-50 border-b-2 border-red-200 p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-600 flex-shrink-0" />
              <div>
                <h2 className="text-xl font-bold text-red-800">
                  📚 EDUCATIONAL INFORMATION ONLY
                </h2>
                <p className="text-sm text-red-700 font-medium">
                  This is NOT legal advice - General educational content about document types
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-red-600 hover:text-red-800 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6">
          {!analysis ? (
            <div className="text-center">
              <AcademicCapIcon className="w-16 h-16 text-blue-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Educational Document Analysis
              </h3>
              <p className="text-gray-600 mb-6">
                Learn about "{documentName}" - Educational information about what this type of document typically means
              </p>
              <button
                onClick={handleAnalyze}
                disabled={isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? 'Analyzing for Educational Purposes...' : 'Start Educational Analysis'}
              </button>

              {/* Enhanced Pre-analysis Disclaimer */}
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
                <div className="flex items-center space-x-2 mb-2">
                  <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />
                  <span className="font-medium text-yellow-800">Educational Disclaimer</span>
                </div>
                <p className="text-sm text-yellow-700">
                  This educational analysis provides general information about what document types typically mean in legal education.
                  This is not legal advice for any specific situation. People typically need to consult qualified attorneys for their individual circumstances.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Enhanced Critical Disclaimers Section */}
              <Card className="bg-red-50 border-red-200 p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                  <h3 className="text-lg font-bold text-red-800">CRITICAL DISCLAIMERS</h3>
                </div>
                <div className="space-y-2 text-sm">
                  <p className="text-red-700 font-medium">• {analysis.disclaimers.primary}</p>
                  <p className="text-red-700">• {analysis.disclaimers.no_attorney_client}</p>
                  <p className="text-red-700 font-medium">• {analysis.disclaimers.consult_attorney}</p>
                  <p className="text-red-700">• {analysis.disclaimers.verify_independently}</p>
                  <p className="text-red-700">• {analysis.disclaimers.no_guarantees}</p>
                </div>
              </Card>

              {/* Enhanced Educational Classification */}
              <Card className="p-6">
                <div className="bg-blue-50 p-3 rounded mb-4">
                  <div className="flex items-center space-x-1 mb-2">
                    <ExclamationTriangleIcon className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-800">Educational Information Only</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2 mb-4">
                  <DocumentTextIcon className="w-6 h-6 text-blue-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Educational Classification</h3>
                </div>
                <div className="space-y-3">
                  <div>
                    <span className="font-medium text-gray-700">Educational Classification: </span>
                    <span className="text-gray-900">{analysis.document_type}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">What This Type Typically Means: </span>
                    <p className="text-gray-900 mt-1">{analysis.educational_explanation}</p>
                  </div>
                </div>
              </Card>

              {/* Enhanced Information Found Section */}
              <Card className="p-6">
                <div className="bg-green-50 p-3 rounded mb-4">
                  <div className="flex items-center space-x-1 mb-2">
                    <ExclamationTriangleIcon className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800">Educational Information Only</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2 mb-4">
                  <InformationCircleIcon className="w-6 h-6 text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Information Typically Found in These Documents</h3>
                </div>

                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <div className="flex items-center space-x-1 mb-2">
                      <UserGroupIcon className="w-4 h-4 text-gray-600" />
                      <span className="font-medium text-gray-700">Parties Often Mentioned:</span>
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {analysis.information_found.parties_mentioned.map((party, index) => {
                        const partyText = typeof party === 'string'
                          ? party
                          : (party as any)?.name || String(party);
                        return <li key={index}>• {partyText}</li>;
                      })}
                    </ul>
                  </div>

                  <div>
                    <div className="flex items-center space-x-1 mb-2">
                      <CalendarDaysIcon className="w-4 h-4 text-gray-600" />
                      <span className="font-medium text-gray-700">Dates Typically Found:</span>
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {analysis.information_found.dates_mentioned.map((date, index) => (
                        <li key={index}>• {date}</li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <div className="flex items-center space-x-1 mb-2">
                      <CurrencyDollarIcon className="w-4 h-4 text-gray-600" />
                      <span className="font-medium text-gray-700">Amounts Often Listed:</span>
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {analysis.information_found.amounts_mentioned.map((amount, index) => (
                        <li key={index}>• {amount}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </Card>

              {/* Enhanced General Education Section */}
              <Card className="p-6">
                <div className="bg-purple-50 p-3 rounded mb-4">
                  <div className="flex items-center space-x-1 mb-2">
                    <ExclamationTriangleIcon className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-medium text-purple-800">Educational Information Only - Not Advice for Your Situation</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2 mb-4">
                  <AcademicCapIcon className="w-6 h-6 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900">What This Document Type Typically Means (Educational)</h3>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-1">What Documents Like This Typically Mean:</h4>
                    <p className="text-gray-600 text-sm">{analysis.general_education.what_this_document_type_means}</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-1">Typical Timelines People Often Encounter:</h4>
                    <p className="text-gray-600 text-sm">{analysis.general_education.typical_timeline}</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-1">Responses People Often Consider:</h4>
                    <p className="text-gray-600 text-sm">{analysis.general_education.common_responses}</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-1">Options People Typically Have Available:</h4>
                    <p className="text-gray-600 text-sm">{analysis.general_education.general_options}</p>
                  </div>
                </div>
              </Card>

              {/* Enhanced Educational Q&A Section */}
              <Card className="p-6">
                <div className="bg-orange-50 p-3 rounded mb-4">
                  <div className="flex items-center space-x-1 mb-2">
                    <ExclamationTriangleIcon className="w-4 h-4 text-orange-600" />
                    <span className="text-sm font-medium text-orange-800">Educational Information Only - For Learning Purposes</span>
                  </div>
                </div>
                <div className="flex items-center space-x-2 mb-4">
                  <QuestionMarkCircleIcon className="w-6 h-6 text-orange-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Questions People Often Ask Attorneys</h3>
                </div>

                <p className="text-gray-600 text-sm mb-4">
                  Educational information about questions people typically find helpful to discuss with qualified legal counsel:
                </p>

                <div className="space-y-3">
                  {analysis.educational_questions.map((question, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <input
                        type="checkbox"
                        id={`q${index}`}
                        className="mt-1"
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedQuestions([...selectedQuestions, question])
                          } else {
                            setSelectedQuestions(selectedQuestions.filter(q => q !== question))
                          }
                        }}
                      />
                      <label htmlFor={`q${index}`} className="text-gray-700 text-sm cursor-pointer">
                        {question}
                      </label>
                    </div>
                  ))}
                </div>

                {selectedQuestions.length > 0 && (
                  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                    <p className="text-blue-800 text-sm font-medium">
                      Educational Information: These are questions people often find helpful to discuss with qualified attorneys about their individual situations.
                    </p>
                  </div>
                )}
              </Card>

              {/* Enhanced Next Steps Section */}
              <Card className="bg-blue-50 border-blue-200 p-6">
                <div className="flex items-center space-x-2 mb-3">
                  <InformationCircleIcon className="w-6 h-6 text-blue-600" />
                  <h3 className="text-lg font-semibold text-blue-800">What People Typically Do Next (Educational)</h3>
                </div>
                <div className="space-y-2 text-blue-700">
                  <p>• <strong>Attorney Consultation:</strong> People typically consult qualified attorneys about their individual situations</p>
                  <p>• <strong>Deadline Verification:</strong> People often have attorneys verify deadlines and requirements for their specific cases</p>
                  <p>• <strong>Options Review:</strong> People typically discuss available options with legal counsel</p>
                  <p>• <strong>Timely Action:</strong> Educational materials emphasize that legal deadlines are typically strict - people often seek help promptly for real cases</p>
                </div>
              </Card>

              {/* Enhanced Final Disclaimer */}
              <Card className="bg-red-50 border-red-200 p-6">
                <div className="flex items-center space-x-2 mb-3">
                  <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                  <h4 className="text-lg font-bold text-red-800">Final Educational Reminder</h4>
                </div>
                <div className="space-y-2 text-red-700 text-sm">
                  <p>• This is general educational information about document types, not legal advice for specific situations</p>
                  <p>• Legal requirements and processes typically vary by state, court, and individual circumstances</p>
                  <p>• People typically need qualified legal counsel to understand their specific rights and options</p>
                  <p>• Educational materials cannot substitute for professional legal advice about individual cases</p>
                  <p>• Always verify educational information independently with qualified attorneys</p>
                </div>
              </Card>

              {/* Close Button */}
              <div className="flex justify-center pt-4">
                <button
                  onClick={onClose}
                  className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Close Educational Analysis
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}