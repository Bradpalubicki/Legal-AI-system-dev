'use client'

import { useState } from 'react'
import { Card } from './ui'
import {
  ExclamationTriangleIcon,
  AcademicCapIcon,
  QuestionMarkCircleIcon,
  InformationCircleIcon,
  UserGroupIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  LightBulbIcon,
  BookOpenIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline'

// Educational questionnaire types
interface EducationalQuestion {
  id: string
  category: string
  question: string
  educational_context: string
  learning_objective: string
  attorney_connection: string
  follow_up_questions: string[]
}

interface QuestionnaireSection {
  title: string
  educational_purpose: string
  questions: EducationalQuestion[]
  educational_summary: string
}

interface EducationalQuestionnaireProps {
  onClose: () => void
}

// Educational questionnaire data with proper language patterns
const educationalSections: QuestionnaireSection[] = [
  {
    title: "Document Type Learning (Educational)",
    educational_purpose: "This section helps people learn about different types of legal documents and what they typically mean in general legal education.",
    questions: [
      {
        id: "doc-type-1",
        category: "Document Classification",
        question: "For educational learning purposes, what type of document do people typically encounter in situations like this?",
        educational_context: "Educational materials show that legal documents typically fall into categories like contracts, motions, pleadings, or correspondence. Understanding document types helps people learn about legal processes.",
        learning_objective: "Learn to identify common legal document categories and understand what each type typically represents in legal education.",
        attorney_connection: "Attorneys typically ask clients to identify document types to understand the legal context and determine appropriate responses.",
        follow_up_questions: [
          "What do educational materials typically say about this document type?",
          "How do people typically respond to documents of this type?",
          "What timelines do documents like this typically have?"
        ]
      },
      {
        id: "doc-type-2",
        category: "Document Purpose",
        question: "In educational terms, what do documents like this typically aim to accomplish?",
        educational_context: "Educational information shows that legal documents typically serve specific purposes: requesting action, providing notice, establishing agreements, or documenting events.",
        learning_objective: "Understand the typical purposes that different legal documents serve in general legal education.",
        attorney_connection: "Legal professionals typically need to understand document purposes to provide appropriate guidance about responses and obligations.",
        follow_up_questions: [
          "What actions do documents with this purpose typically require?",
          "What educational resources exist about responding to this type of document?",
          "What questions do people typically ask attorneys about documents with this purpose?"
        ]
      }
    ],
    educational_summary: "Understanding document types and purposes typically helps people prepare better questions for legal consultations and understand general legal processes."
  },
  {
    title: "Timeline and Process Education",
    educational_purpose: "This section provides educational information about legal timelines and processes that people often encounter.",
    questions: [
      {
        id: "timeline-1",
        category: "Educational Timelines",
        question: "For learning purposes, what timelines do people typically face with documents like this?",
        educational_context: "Legal education shows that documents typically have response deadlines, hearing dates, or other time-sensitive requirements. Understanding timelines helps people learn about legal urgency.",
        learning_objective: "Learn about typical legal timelines and why time-sensitivity is often important in legal matters.",
        attorney_connection: "Attorneys typically emphasize deadlines because missing them can typically have serious consequences in legal proceedings.",
        follow_up_questions: [
          "What happens typically when people miss deadlines with documents like this?",
          "How do people typically track important legal dates?",
          "What do attorneys typically recommend about managing legal deadlines?"
        ]
      },
      {
        id: "timeline-2",
        category: "Response Planning",
        question: "In educational terms, what steps do people typically take when they receive documents like this?",
        educational_context: "Educational materials typically outline systematic approaches: reading carefully, identifying deadlines, gathering information, and consulting professionals.",
        learning_objective: "Learn about systematic approaches that people typically use when handling legal documents.",
        attorney_connection: "Legal professionals typically appreciate when clients have organized their information and identified key questions before consultations.",
        follow_up_questions: [
          "What information do attorneys typically need about situations like this?",
          "What documents do people typically gather before legal consultations?",
          "What preparation typically makes legal consultations more effective?"
        ]
      }
    ],
    educational_summary: "Learning about typical timelines and processes helps people understand legal urgency and prepare more effectively for professional consultations."
  },
  {
    title: "Attorney Consultation Preparation (Educational)",
    educational_purpose: "This section teaches what information legal professionals typically need and what questions people often find helpful to ask.",
    questions: [
      {
        id: "attorney-1",
        category: "Information Gathering",
        question: "What information do attorneys typically need to understand situations involving documents like this?",
        educational_context: "Educational resources typically show that attorneys need background information, relevant documents, timeline details, and specific goals or concerns.",
        learning_objective: "Learn what information typically helps legal professionals provide effective guidance.",
        attorney_connection: "Organized information typically helps attorneys understand cases more quickly and provide more focused advice during consultations.",
        follow_up_questions: [
          "What background details do attorneys typically find most helpful?",
          "What documents do legal professionals typically want to review?",
          "What questions help attorneys understand client priorities and concerns?"
        ]
      },
      {
        id: "attorney-2",
        category: "Professional Questions",
        question: "What questions do people typically find most helpful to ask attorneys about situations like this?",
        educational_context: "Educational materials suggest that effective questions typically focus on options, consequences, timelines, costs, and realistic outcomes.",
        learning_objective: "Learn to formulate questions that typically lead to helpful legal guidance.",
        attorney_connection: "Well-prepared questions typically help clients get more value from legal consultations and understand their situations better.",
        follow_up_questions: [
          "What questions help people understand their legal options?",
          "How do people typically ask about costs and fee structures?",
          "What questions help people understand realistic timelines and outcomes?"
        ]
      }
    ],
    educational_summary: "Understanding what attorneys typically need and learning effective questions typically helps people prepare for more productive legal consultations."
  }
]

export default function EducationalQuestionnaire({ onClose }: EducationalQuestionnaireProps) {
  const [currentSection, setCurrentSection] = useState(0)
  const [answers, setAnswers] = useState<{[key: string]: string}>({})
  const [selectedFollowUps, setSelectedFollowUps] = useState<string[]>([])
  const [showSummary, setShowSummary] = useState(false)

  const handleAnswerChange = (questionId: string, answer: string) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: answer
    }))
  }

  const handleFollowUpToggle = (question: string) => {
    setSelectedFollowUps(prev =>
      prev.includes(question)
        ? prev.filter(q => q !== question)
        : [...prev, question]
    )
  }

  const generateEducationalSummary = () => {
    const totalQuestions = educationalSections.reduce((sum, section) => sum + section.questions.length, 0)
    const answeredQuestions = Object.keys(answers).length

    return {
      questions_explored: answeredQuestions,
      total_available: totalQuestions,
      learning_areas: educationalSections.map(section => section.title),
      follow_up_questions: selectedFollowUps,
      educational_next_steps: [
        "People typically benefit from reviewing the educational information provided",
        "Consulting qualified legal professionals is typically the next step for specific situations",
        "Organizing the follow-up questions typically helps prepare for attorney consultations",
        "People often find it helpful to gather relevant documents before legal meetings"
      ]
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Educational Header */}
        <div className="bg-blue-50 border-b-2 border-blue-200 p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <BookOpenIcon className="w-8 h-8 text-blue-600 flex-shrink-0" />
              <div>
                <h2 className="text-xl font-bold text-blue-800">
                  📚 EDUCATIONAL LEGAL CONCEPTS QUESTIONNAIRE
                </h2>
                <p className="text-sm text-blue-700 font-medium">
                  General educational information - Not personalized legal advice
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-blue-600 hover:text-blue-800 text-2xl font-bold"
            >
              ×
            </button>
          </div>
        </div>

        {/* Critical Educational Disclaimer */}
        <div className="bg-yellow-50 border-b border-yellow-200 p-4">
          <div className="flex items-center space-x-2 mb-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />
            <span className="font-bold text-yellow-800">EDUCATIONAL INFORMATION ONLY</span>
          </div>
          <p className="text-sm text-yellow-700">
            This questionnaire provides general educational information about legal concepts and processes.
            Responses generate educational content only, not personalized legal advice. People typically need
            qualified legal counsel for their specific situations.
          </p>
        </div>

        <div className="p-6">
          {!showSummary ? (
            <>
              {/* Section Navigation */}
              <div className="mb-6">
                <div className="flex space-x-2 overflow-x-auto pb-2">
                  {educationalSections.map((section, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentSection(index)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap ${
                        currentSection === index
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {section.title}
                    </button>
                  ))}
                </div>
              </div>

              {/* Current Section */}
              <Card className="p-6 mb-6">
                <div className="bg-purple-50 p-3 rounded mb-4">
                  <div className="flex items-center space-x-1 mb-2">
                    <ExclamationTriangleIcon className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-medium text-purple-800">Educational Information Only</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 mb-4">
                  <AcademicCapIcon className="w-6 h-6 text-purple-600" />
                  <h3 className="text-lg font-semibold text-gray-900">
                    {educationalSections[currentSection].title}
                  </h3>
                </div>

                <p className="text-gray-600 text-sm mb-6">
                  {educationalSections[currentSection].educational_purpose}
                </p>

                {/* Questions in Current Section */}
                <div className="space-y-8">
                  {educationalSections[currentSection].questions.map((question) => (
                    <div key={question.id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start space-x-2 mb-3">
                        <QuestionMarkCircleIcon className="w-5 h-5 text-orange-500 mt-0.5 flex-shrink-0" />
                        <h4 className="font-medium text-gray-900">{question.question}</h4>
                      </div>

                      {/* Educational Context */}
                      <div className="bg-blue-50 p-3 rounded mb-4">
                        <div className="flex items-start space-x-2 mb-2">
                          <InformationCircleIcon className="w-4 h-4 text-blue-600 mt-0.5" />
                          <span className="text-sm font-medium text-blue-800">Educational Context:</span>
                        </div>
                        <p className="text-blue-700 text-sm">{question.educational_context}</p>
                      </div>

                      {/* Learning Objective */}
                      <div className="bg-green-50 p-3 rounded mb-4">
                        <div className="flex items-start space-x-2 mb-2">
                          <LightBulbIcon className="w-4 h-4 text-green-600 mt-0.5" />
                          <span className="text-sm font-medium text-green-800">Learning Objective:</span>
                        </div>
                        <p className="text-green-700 text-sm">{question.learning_objective}</p>
                      </div>

                      {/* Answer Input */}
                      <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Your Educational Response (Optional):
                        </label>
                        <textarea
                          value={answers[question.id] || ''}
                          onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                          placeholder="This space is for learning purposes - write your thoughts about this educational topic..."
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows={3}
                        />
                      </div>

                      {/* Attorney Connection */}
                      <div className="bg-indigo-50 p-3 rounded mb-4">
                        <div className="flex items-start space-x-2 mb-2">
                          <UserGroupIcon className="w-4 h-4 text-indigo-600 mt-0.5" />
                          <span className="text-sm font-medium text-indigo-800">What Attorneys Typically Need:</span>
                        </div>
                        <p className="text-indigo-700 text-sm">{question.attorney_connection}</p>
                      </div>

                      {/* Follow-up Questions */}
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="flex items-center space-x-2 mb-3">
                          <ClipboardDocumentListIcon className="w-4 h-4 text-gray-600" />
                          <span className="text-sm font-medium text-gray-800">Questions People Often Ask Attorneys:</span>
                        </div>
                        <div className="space-y-2">
                          {question.follow_up_questions.map((followUp, index) => (
                            <div key={index} className="flex items-start space-x-2">
                              <input
                                type="checkbox"
                                id={`${question.id}-followup-${index}`}
                                checked={selectedFollowUps.includes(followUp)}
                                onChange={() => handleFollowUpToggle(followUp)}
                                className="mt-1"
                              />
                              <label
                                htmlFor={`${question.id}-followup-${index}`}
                                className="text-gray-700 text-sm cursor-pointer"
                              >
                                {followUp}
                              </label>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Section Summary */}
                <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
                  <div className="flex items-center space-x-2 mb-2">
                    <DocumentTextIcon className="w-5 h-5 text-yellow-600" />
                    <span className="font-medium text-yellow-800">Educational Summary:</span>
                  </div>
                  <p className="text-yellow-700 text-sm">
                    {educationalSections[currentSection].educational_summary}
                  </p>
                </div>
              </Card>

              {/* Navigation Buttons */}
              <div className="flex justify-between items-center">
                <button
                  onClick={() => setCurrentSection(Math.max(0, currentSection - 1))}
                  disabled={currentSection === 0}
                  className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous Section
                </button>

                <span className="text-sm text-gray-600">
                  Section {currentSection + 1} of {educationalSections.length}
                </span>

                {currentSection < educationalSections.length - 1 ? (
                  <button
                    onClick={() => setCurrentSection(currentSection + 1)}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Next Section
                  </button>
                ) : (
                  <button
                    onClick={() => setShowSummary(true)}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    View Learning Summary
                  </button>
                )}
              </div>
            </>
          ) : (
            // Educational Summary View
            <div className="space-y-6">
              <Card className="p-6">
                <div className="bg-green-50 p-3 rounded mb-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-600" />
                    <span className="font-bold text-green-800">Educational Learning Summary</span>
                  </div>
                </div>

                <div className="space-y-4">
                  {(() => {
                    const summary = generateEducationalSummary()
                    return (
                      <>
                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Learning Progress:</h4>
                          <p className="text-gray-600">
                            Explored {summary.questions_explored} out of {summary.total_available} educational topics
                          </p>
                        </div>

                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Educational Areas Covered:</h4>
                          <ul className="list-disc list-inside text-gray-600 space-y-1">
                            {summary.learning_areas.map((area, index) => (
                              <li key={index}>{area}</li>
                            ))}
                          </ul>
                        </div>

                        {summary.follow_up_questions.length > 0 && (
                          <div>
                            <h4 className="font-medium text-gray-700 mb-2">
                              Questions Selected for Attorney Consultation ({summary.follow_up_questions.length}):
                            </h4>
                            <ul className="list-disc list-inside text-gray-600 space-y-1">
                              {summary.follow_up_questions.map((question, index) => (
                                <li key={index} className="text-sm">{question}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        <div>
                          <h4 className="font-medium text-gray-700 mb-2">Educational Next Steps:</h4>
                          <ul className="list-disc list-inside text-gray-600 space-y-1">
                            {summary.educational_next_steps.map((step, index) => (
                              <li key={index} className="text-sm">{step}</li>
                            ))}
                          </ul>
                        </div>
                      </>
                    )
                  })()}
                </div>
              </Card>

              {/* Final Educational Reminder */}
              <Card className="bg-red-50 border-red-200 p-6">
                <div className="flex items-center space-x-2 mb-3">
                  <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                  <h4 className="text-lg font-bold text-red-800">Final Educational Reminder</h4>
                </div>
                <div className="space-y-2 text-red-700 text-sm">
                  <p>• This questionnaire provided general educational information, not personalized legal advice</p>
                  <p>• People typically need qualified legal professionals for their specific situations</p>
                  <p>• Selected questions can typically help prepare for attorney consultations</p>
                  <p>• Legal requirements typically vary by jurisdiction and individual circumstances</p>
                  <p>• Educational materials cannot substitute for professional legal counsel</p>
                </div>
              </Card>

              {/* Action Buttons */}
              <div className="flex justify-between">
                <button
                  onClick={() => setShowSummary(false)}
                  className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                >
                  Continue Learning
                </button>
                <button
                  onClick={onClose}
                  className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Close Educational Questionnaire
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}