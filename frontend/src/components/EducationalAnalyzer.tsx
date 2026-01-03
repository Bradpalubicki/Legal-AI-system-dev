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

// Educational Analysis Types
interface EducationalAnalysis {
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

interface EducationalAnalyzerProps {
  documentName: string
  onClose: () => void
}

// Educational document analyzer function
const analyzeDocument = async (file: File): Promise<EducationalAnalysis> => {
  // Simulate API call for educational analysis
  await new Promise(resolve => setTimeout(resolve, 2000))

  return {
    document_type: 'This appears to be a Motion for Relief from Stay',
    educational_explanation: 'In bankruptcy education, this type of document typically means a creditor is asking the court for permission to proceed with collection actions despite the automatic stay that protects debtors in bankruptcy.',

    information_found: {
      parties_mentioned: ['First National Bank', 'ABC Company LLC', 'Trustee'],
      dates_mentioned: ['Filing deadline: 14 days from service', 'Hearing date: January 30, 2025'],
      amounts_mentioned: ['$45,000 outstanding loan balance', '$2,500 monthly payments']
    },

    general_education: {
      what_this_document_type_means: 'In general legal education, a Motion for Relief from Stay is a formal request to the bankruptcy court asking for permission to continue collection efforts against property that would normally be protected by the automatic stay.',
      typical_timeline: 'Documents like this typically have a 14-day response deadline, followed by a hearing within 30 days. The debtor usually has the right to respond and object.',
      common_responses: 'People in similar educational scenarios often consider: filing an objection, negotiating with the creditor, seeking attorney consultation, or modifying their bankruptcy plan.',
      general_options: 'Educational information shows possible paths may include: objecting to the motion, negotiating a payment plan, surrendering the property, or seeking modification of the bankruptcy plan. Each situation is unique.'
    },

    educational_questions: [
      'To better understand your situation for educational purposes, are you the debtor or creditor in this matter?',
      'For educational context, do you have an attorney helping you with this bankruptcy case?',
      'What would you like to learn about motions for relief from stay?',
      'Are you seeking to understand the process or timeline for educational purposes?'
    ],

    disclaimers: {
      primary: 'This is educational information only, not legal advice',
      no_attorney_client: 'No attorney-client relationship exists or is created by this analysis',
      consult_attorney: 'Always consult a qualified attorney for your specific situation',
      verify_independently: 'All information should be verified independently with legal counsel',
      no_guarantees: 'No guarantees about accuracy, completeness, or applicability to your situation'
    }
  }
}

export default function EducationalAnalyzer({ documentName, onClose }: EducationalAnalyzerProps) {
  const [analysis, setAnalysis] = useState<EducationalAnalysis | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedQuestions, setSelectedQuestions] = useState<string[]>([])

  const handleAnalyze = async () => {
    setIsLoading(true)
    try {
      // Create a mock file for educational analysis
      const mockFile = new File([''], documentName, { type: 'application/pdf' })
      const result = await analyzeDocument(mockFile)
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
        {/* Educational Header with Critical Disclaimer */}
        <div className="bg-red-50 border-b-2 border-red-200 p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <ExclamationTriangleIcon className="w-8 h-8 text-red-600 flex-shrink-0" />
              <div>
                <h2 className="text-xl font-bold text-red-800">
                  📚 FOR EDUCATIONAL PURPOSES ONLY
                </h2>
                <p className="text-sm text-red-700 font-medium">
                  This is NOT legal advice - Educational content only
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
                Analyze "{documentName}" for educational learning purposes only
              </p>
              <button
                onClick={handleAnalyze}
                disabled={isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {isLoading ? 'Analyzing for Education...' : 'Start Educational Analysis'}
              </button>

              {/* Pre-analysis Disclaimer */}
              <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
                <div className="flex items-center space-x-2 mb-2">
                  <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />
                  <span className="font-medium text-yellow-800">Educational Disclaimer</span>
                </div>
                <p className="text-sm text-yellow-700">
                  This analysis provides general educational information about document types and legal concepts.
                  It does not constitute legal advice and cannot replace consultation with a qualified attorney.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Critical Disclaimers Section */}
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

              {/* Educational Classification */}
              <Card className="p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <DocumentTextIcon className="w-6 h-6 text-blue-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Educational Classification</h3>
                </div>
                <div className="space-y-3">
                  <div>
                    <span className="font-medium text-gray-700">Document Type (Educational): </span>
                    <span className="text-gray-900">{analysis.document_type}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Educational Explanation: </span>
                    <p className="text-gray-900 mt-1">{analysis.educational_explanation}</p>
                  </div>
                </div>
              </Card>

              {/* Information Found (Educational) */}
              <Card className="p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <InformationCircleIcon className="w-6 h-6 text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Information Found (Educational Purpose)</h3>
                </div>

                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <div className="flex items-center space-x-1 mb-2">
                      <UserGroupIcon className="w-4 h-4 text-gray-600" />
                      <span className="font-medium text-gray-700">Parties Mentioned:</span>
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
                      <span className="font-medium text-gray-700">Dates Mentioned:</span>
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
                      <span className="font-medium text-gray-700">Amounts Mentioned:</span>
                    </div>
                    <ul className="text-sm text-gray-600 space-y-1">
                      {analysis.information_found.amounts_mentioned.map((amount, index) => (
                        <li key={index}>• {amount}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </Card>

              {/* General Education Section */}
              <Card className="p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <AcademicCapIcon className="w-6 h-6 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900">General Educational Context</h3>
                </div>

                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-1">What This Document Type Means (General Education):</h4>
                    <p className="text-gray-600 text-sm">{analysis.general_education.what_this_document_type_means}</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-1">Typical Timeline (Educational):</h4>
                    <p className="text-gray-600 text-sm">{analysis.general_education.typical_timeline}</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-1">Common Responses (Educational):</h4>
                    <p className="text-gray-600 text-sm">{analysis.general_education.common_responses}</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-1">General Options (Educational):</h4>
                    <p className="text-gray-600 text-sm">{analysis.general_education.general_options}</p>
                  </div>
                </div>
              </Card>

              {/* Educational Q&A Section */}
              <Card className="p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <QuestionMarkCircleIcon className="w-6 h-6 text-orange-600" />
                  <h3 className="text-lg font-semibold text-gray-900">Educational Questions for Learning</h3>
                </div>

                <p className="text-gray-600 text-sm mb-4">
                  These questions help you learn more about your situation (for educational purposes only):
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
                      These are excellent questions to discuss with a qualified attorney for your specific situation.
                    </p>
                  </div>
                )}
              </Card>

              {/* Attorney Consultation Reminder */}
              <Card className="bg-blue-50 border-blue-200 p-6">
                <div className="flex items-center space-x-2 mb-3">
                  <InformationCircleIcon className="w-6 h-6 text-blue-600" />
                  <h3 className="text-lg font-semibold text-blue-800">Next Steps for Real Situations</h3>
                </div>
                <div className="space-y-2 text-blue-700">
                  <p>• <strong>Consult an Attorney:</strong> For your specific situation, consult with a qualified bankruptcy attorney</p>
                  <p>• <strong>Verify Deadlines:</strong> Have an attorney verify all deadlines and requirements</p>
                  <p>• <strong>Review Options:</strong> Discuss all available options with legal counsel</p>
                  <p>• <strong>Don't Delay:</strong> Legal deadlines are strict - seek help promptly if this is a real case</p>
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