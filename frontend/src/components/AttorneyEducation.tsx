'use client'

import { useState } from 'react'
import { Card } from './ui'
import {
  ExclamationTriangleIcon,
  AcademicCapIcon,
  UserGroupIcon,
  ClipboardDocumentCheckIcon,
  QuestionMarkCircleIcon,
  InformationCircleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline'

interface AttorneyEducationProps {
  onClose: () => void
}

interface EducationalStandard {
  category: string
  standards: string[]
  questions_to_ask: string[]
  red_flags: string[]
}

const educationalStandards: EducationalStandard[] = [
  {
    category: "Communication Standards (Educational)",
    standards: [
      "Generally, attorneys should return calls within 24-48 hours",
      "Clients typically expect regular updates on case progress",
      "Important developments are usually communicated promptly",
      "Fee arrangements should be clearly explained in writing"
    ],
    questions_to_ask: [
      "What is your typical response time for returning calls?",
      "How often will you update me on my case progress?",
      "Will you explain all fees and costs upfront?",
      "What is your preferred method of communication?"
    ],
    red_flags: [
      "Not returning calls for weeks without explanation",
      "Refusing to explain fees or billing practices",
      "Making unrealistic promises about case outcomes",
      "Pressuring you to sign agreements without time to review"
    ]
  },
  {
    category: "Professional Competence (Educational)",
    standards: [
      "Attorneys are expected to be knowledgeable in their practice areas",
      "Continuing legal education is typically required to maintain licenses",
      "Research and preparation are standard professional expectations",
      "Consulting with other attorneys when needed shows good practice"
    ],
    questions_to_ask: [
      "How long have you practiced in this area of law?",
      "How many similar cases have you handled?",
      "Will you personally handle my case or delegate to others?",
      "What is your track record with cases like mine?"
    ],
    red_flags: [
      "Cannot answer basic questions about your type of case",
      "Has no experience in the relevant area of law",
      "Makes guarantees about specific outcomes",
      "Seems unprepared or disorganized during meetings"
    ]
  },
  {
    category: "Ethical Obligations (Educational)",
    standards: [
      "Client confidentiality is a fundamental ethical requirement",
      "Conflicts of interest must be disclosed and managed",
      "Client funds must be kept in separate trust accounts",
      "Honest representation of costs and likely outcomes is expected"
    ],
    questions_to_ask: [
      "Do you have any conflicts of interest with my case?",
      "How do you handle confidential information?",
      "Where are client funds kept?",
      "What are the realistic possible outcomes of my case?"
    ],
    red_flags: [
      "Discussing other clients' confidential matters",
      "Asking for large upfront payments without clear fee agreement",
      "Suggesting dishonest or illegal strategies",
      "Not disclosing potential conflicts of interest"
    ]
  }
]

export default function AttorneyEducation({ onClose }: AttorneyEducationProps) {
  const [selectedCategory, setSelectedCategory] = useState(0)
  const [checkedQuestions, setCheckedQuestions] = useState<string[]>([])

  const handleQuestionCheck = (question: string) => {
    if (checkedQuestions.includes(question)) {
      setCheckedQuestions(checkedQuestions.filter(q => q !== question))
    } else {
      setCheckedQuestions([...checkedQuestions, question])
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        {/* Educational Header */}
        <div className="bg-blue-50 border-b-2 border-blue-200 p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <AcademicCapIcon className="w-8 h-8 text-blue-600 flex-shrink-0" />
              <div>
                <h2 className="text-xl font-bold text-blue-800">
                  📚 ATTORNEY ACCOUNTABILITY EDUCATION
                </h2>
                <p className="text-sm text-blue-700 font-medium">
                  Educational information about attorney standards and client expectations
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
            <span className="font-bold text-yellow-800">FOR EDUCATIONAL PURPOSES ONLY</span>
          </div>
          <p className="text-sm text-yellow-700">
            This information is for educational purposes only and does not constitute legal advice.
            State bar associations and legal ethics rules vary by jurisdiction. Always consult your
            state bar association for specific ethical requirements and attorney standards.
          </p>
        </div>

        <div className="p-6">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Educational Scope</h3>
            <p className="text-gray-600">
              This educational tool teaches general concepts about what clients might typically expect
              from attorneys and what questions could be valuable to ask. This helps you become a more
              informed consumer of legal services.
            </p>
          </div>

          {/* Category Tabs */}
          <div className="flex flex-wrap border-b border-gray-200 mb-6">
            {educationalStandards.map((category, index) => (
              <button
                key={index}
                onClick={() => setSelectedCategory(index)}
                className={`px-4 py-2 font-medium text-sm border-b-2 ${
                  selectedCategory === index
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {category.category}
              </button>
            ))}
          </div>

          {/* Selected Category Content */}
          <div className="space-y-6">
            {/* Standards Section */}
            <Card className="p-6">
              <div className="flex items-center space-x-2 mb-4">
                <ClipboardDocumentCheckIcon className="w-6 h-6 text-green-600" />
                <h4 className="text-lg font-semibold text-gray-900">
                  General Standards (Educational)
                </h4>
              </div>
              <ul className="space-y-2">
                {educationalStandards[selectedCategory].standards.map((standard, index) => (
                  <li key={index} className="flex items-start space-x-3">
                    <CheckCircleIcon className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700">{standard}</span>
                  </li>
                ))}
              </ul>
            </Card>

            {/* Questions to Ask Section */}
            <Card className="p-6">
              <div className="flex items-center space-x-2 mb-4">
                <QuestionMarkCircleIcon className="w-6 h-6 text-blue-600" />
                <h4 className="text-lg font-semibold text-gray-900">
                  Educational Questions to Consider Asking
                </h4>
              </div>
              <p className="text-gray-600 text-sm mb-4">
                These are examples of questions that informed clients often ask attorneys:
              </p>
              <div className="space-y-3">
                {educationalStandards[selectedCategory].questions_to_ask.map((question, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      id={`q${selectedCategory}-${index}`}
                      checked={checkedQuestions.includes(question)}
                      onChange={() => handleQuestionCheck(question)}
                      className="mt-1"
                    />
                    <label
                      htmlFor={`q${selectedCategory}-${index}`}
                      className="text-gray-700 cursor-pointer"
                    >
                      {question}
                    </label>
                  </div>
                ))}
              </div>
              {checkedQuestions.length > 0 && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                  <p className="text-blue-800 text-sm">
                    ✓ You've selected {checkedQuestions.length} questions to potentially ask attorneys.
                    These can help you make informed decisions when choosing legal representation.
                  </p>
                </div>
              )}
            </Card>

            {/* Red Flags Section */}
            <Card className="p-6 bg-red-50 border-red-200">
              <div className="flex items-center space-x-2 mb-4">
                <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                <h4 className="text-lg font-semibold text-red-800">
                  Educational Red Flags (General Warning Signs)
                </h4>
              </div>
              <p className="text-red-700 text-sm mb-4">
                Educational information about warning signs that informed clients often watch for:
              </p>
              <ul className="space-y-2">
                {educationalStandards[selectedCategory].red_flags.map((flag, index) => (
                  <li key={index} className="flex items-start space-x-3">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                    <span className="text-red-700">{flag}</span>
                  </li>
                ))}
              </ul>
            </Card>

            {/* Additional Educational Resources */}
            <Card className="p-6 bg-gray-50">
              <div className="flex items-center space-x-2 mb-4">
                <InformationCircleIcon className="w-6 h-6 text-gray-600" />
                <h4 className="text-lg font-semibold text-gray-900">
                  Additional Educational Resources
                </h4>
              </div>
              <div className="space-y-3 text-sm text-gray-700">
                <p>• <strong>State Bar Associations:</strong> Most states have client resources and attorney directories</p>
                <p>• <strong>Legal Aid Organizations:</strong> May provide free or low-cost legal assistance</p>
                <p>• <strong>Attorney Disciplinary Records:</strong> Many states allow public searches of attorney discipline</p>
                <p>• <strong>Continuing Education:</strong> Attorneys are typically required to complete ongoing education</p>
                <p>• <strong>Fee Agreements:</strong> Should be in writing and clearly explain all costs</p>
                <p>• <strong>Second Opinions:</strong> It's often appropriate to seek multiple attorney consultations</p>
              </div>
            </Card>

            {/* Educational Summary */}
            <Card className="p-6 bg-blue-50 border-blue-200">
              <div className="flex items-center space-x-2 mb-4">
                <UserGroupIcon className="w-6 h-6 text-blue-600" />
                <h4 className="text-lg font-semibold text-blue-800">
                  Educational Summary: Being an Informed Client
                </h4>
              </div>
              <div className="space-y-3 text-blue-700">
                <p>• <strong>Ask Questions:</strong> Informed clients typically ask detailed questions about experience, fees, and process</p>
                <p>• <strong>Get Written Agreements:</strong> Fee arrangements and scope of work should generally be in writing</p>
                <p>• <strong>Understand Your Rights:</strong> Clients have rights regarding communication, billing, and case handling</p>
                <p>• <strong>Stay Involved:</strong> Active participation in your case often leads to better outcomes</p>
                <p>• <strong>Seek Help if Needed:</strong> State bar associations often provide guidance for client concerns</p>
              </div>
            </Card>

            {/* Critical Disclaimer */}
            <Card className="p-6 bg-red-50 border-red-200">
              <div className="flex items-center space-x-2 mb-3">
                <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
                <h4 className="text-lg font-bold text-red-800">Important Educational Disclaimer</h4>
              </div>
              <div className="space-y-2 text-red-700 text-sm">
                <p>• This is general educational information, not legal advice about your specific situation</p>
                <p>• Attorney standards and ethical rules vary significantly by state and jurisdiction</p>
                <p>• No attorney-client relationship is created by viewing this educational content</p>
                <p>• For specific concerns about attorney conduct, contact your state bar association</p>
                <p>• Always verify information independently with qualified legal counsel</p>
              </div>
            </Card>

            {/* Close Button */}
            <div className="flex justify-center pt-4">
              <button
                onClick={onClose}
                className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
              >
                Close Educational Content
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}