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
  ClockIcon,
  BookOpenIcon,
  BuildingLibraryIcon,
  ScaleIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline'

interface EducationalResourcesProps {
  onClose: () => void
}

interface BankruptcyType {
  chapter: string
  name: string
  description: string
  typical_timeline: string
  general_eligibility: string
  common_outcomes: string
}

interface TimelineExample {
  process_type: string
  typical_steps: Array<{
    step: string
    timeframe: string
    description: string
  }>
  important_note: string
}

interface GlossaryTerm {
  term: string
  definition: string
  example: string
}

interface AttorneyQuestion {
  category: string
  questions: string[]
}

const bankruptcyTypes: BankruptcyType[] = [
  {
    chapter: "Chapter 7",
    name: "Liquidation Bankruptcy (Educational)",
    description: "Educational information: Chapter 7 is often called 'liquidation' bankruptcy. In general legal education, this process typically involves the liquidation of non-exempt assets to pay creditors.",
    typical_timeline: "Educational timeline: The process typically takes 4-6 months from filing to discharge in most cases.",
    general_eligibility: "Educational criteria: Generally requires passing a means test. People often must show their income is below certain thresholds.",
    common_outcomes: "Educational outcomes: Most qualifying unsecured debts are typically discharged, meaning people generally no longer owe those debts."
  },
  {
    chapter: "Chapter 13",
    name: "Reorganization Bankruptcy (Educational)",
    description: "Educational information: Chapter 13 is often called 'reorganization' bankruptcy. In general legal education, this process typically involves creating a repayment plan over 3-5 years.",
    typical_timeline: "Educational timeline: The process typically involves a 3-5 year repayment plan, with discharge after completion.",
    general_eligibility: "Educational criteria: Generally for people with regular income who want to keep their assets. People often choose this to catch up on mortgage or car payments.",
    common_outcomes: "Educational outcomes: People typically keep their property while making payments according to the court-approved plan."
  },
  {
    chapter: "Chapter 11",
    name: "Business Reorganization (Educational)",
    description: "Educational information: Chapter 11 is typically used by businesses or individuals with substantial assets/debts. In general legal education, this process typically allows continued operation while reorganizing debts.",
    typical_timeline: "Educational timeline: The process can typically take 1-2 years or longer, depending on complexity.",
    general_eligibility: "Educational criteria: Generally no debt limits, but requires court approval of reorganization plan. Often used by businesses or high-asset individuals.",
    common_outcomes: "Educational outcomes: Businesses typically continue operating while paying creditors according to the reorganized plan."
  }
]

const timelineExamples: TimelineExample[] = [
  {
    process_type: "Typical Bankruptcy Filing Process (Educational Example)",
    typical_steps: [
      {
        step: "Pre-Filing Education",
        timeframe: "Before filing",
        description: "Credit counseling is typically required within 180 days before filing"
      },
      {
        step: "Filing Petition",
        timeframe: "Day 1",
        description: "Bankruptcy petition and supporting documents are typically filed with the court"
      },
      {
        step: "Automatic Stay",
        timeframe: "Immediately upon filing",
        description: "Collection actions typically stop automatically when the case is filed"
      },
      {
        step: "Meeting of Creditors",
        timeframe: "20-40 days after filing",
        description: "Debtor typically meets with trustee and any creditors who choose to attend"
      },
      {
        step: "Discharge",
        timeframe: "60-90 days after meeting",
        description: "In Chapter 7, qualifying debts are typically discharged if no issues arise"
      }
    ],
    important_note: "These are general educational timelines. Actual timelines vary significantly based on individual circumstances, court schedules, and case complexity."
  },
  {
    process_type: "Typical Civil Lawsuit Process (Educational Example)",
    typical_steps: [
      {
        step: "Filing Complaint",
        timeframe: "Day 1",
        description: "Plaintiff typically files a complaint stating their claims"
      },
      {
        step: "Service and Response",
        timeframe: "30-60 days",
        description: "Defendant is typically served and has time to respond"
      },
      {
        step: "Discovery Phase",
        timeframe: "3-12 months",
        description: "Parties typically exchange information and evidence"
      },
      {
        step: "Settlement Negotiations",
        timeframe: "Throughout process",
        description: "Parties often attempt to settle without going to trial"
      },
      {
        step: "Trial",
        timeframe: "1-2 years from filing",
        description: "If no settlement, the case typically goes to trial"
      }
    ],
    important_note: "These are general educational timelines. Actual litigation timelines vary dramatically based on court congestion, case complexity, and many other factors."
  }
]

const glossaryTerms: GlossaryTerm[] = [
  {
    term: "Automatic Stay",
    definition: "A legal protection that typically goes into effect immediately when someone files for bankruptcy. It generally stops most collection actions, lawsuits, and foreclosures.",
    example: "If someone is facing foreclosure and files for bankruptcy, the automatic stay typically stops the foreclosure process temporarily."
  },
  {
    term: "Discharge",
    definition: "The legal elimination of debts. When debts are discharged in bankruptcy, people typically no longer owe those debts.",
    example: "After a successful Chapter 7 bankruptcy, qualifying credit card debts are typically discharged."
  },
  {
    term: "Exemptions",
    definition: "Property that people can typically keep in bankruptcy. Each state generally has its own exemption laws.",
    example: "A homestead exemption typically allows people to keep some equity in their primary residence."
  },
  {
    term: "Trustee",
    definition: "A court-appointed person who typically oversees the bankruptcy case and ensures proper procedures are followed.",
    example: "The trustee typically reviews financial documents and conducts the meeting of creditors."
  },
  {
    term: "Means Test",
    definition: "A calculation used to determine if someone typically qualifies for Chapter 7 bankruptcy based on their income and expenses.",
    example: "People whose income is below the median for their state typically pass the means test automatically."
  },
  {
    term: "Motion",
    definition: "A formal request to the court asking for a specific action or ruling. Lawyers typically file motions to ask the court to do something.",
    example: "A motion to dismiss typically asks the court to throw out a case for legal reasons."
  },
  {
    term: "Discovery",
    definition: "The process where parties in a lawsuit typically exchange information and evidence before trial.",
    example: "During discovery, parties typically request documents and take depositions of witnesses."
  },
  {
    term: "Jurisdiction",
    definition: "The authority of a court to hear a particular case. Courts typically only have jurisdiction over certain types of cases or geographic areas.",
    example: "Federal bankruptcy courts typically have jurisdiction over bankruptcy cases nationwide."
  }
]

const attorneyQuestions: AttorneyQuestion[] = [
  {
    category: "Experience and Expertise Questions",
    questions: [
      "How long have you been practicing bankruptcy law?",
      "How many Chapter 7/13 cases have you handled?",
      "What percentage of your practice involves bankruptcy?",
      "Are you board certified in bankruptcy law?",
      "Do you handle cases in this particular court regularly?",
      "What is your success rate with cases similar to mine?",
      "Have you handled any cases involving my specific type of debt/situation?"
    ]
  },
  {
    category: "Process and Timeline Questions",
    questions: [
      "What is the typical timeline for my type of case?",
      "What are the major steps in the process?",
      "What documents will you need from me?",
      "How much time will I need to invest in this process?",
      "What happens if complications arise?",
      "How long after filing until I get a discharge?",
      "What should I expect at the meeting of creditors?"
    ]
  },
  {
    category: "Fees and Costs Questions",
    questions: [
      "What are your total fees for this type of case?",
      "What costs are included/not included in your fee?",
      "What are the court filing fees?",
      "Do you offer payment plans?",
      "When do I need to pay your fees?",
      "What happens if my case becomes more complicated?",
      "Are there any additional costs I should expect?"
    ]
  },
  {
    category: "Communication and Service Questions",
    questions: [
      "How will we communicate throughout the process?",
      "How quickly do you typically return calls or emails?",
      "Who else in your office might work on my case?",
      "Will you personally attend all court hearings?",
      "How will you keep me updated on my case progress?",
      "What should I do if I have urgent questions?",
      "Do you provide written summaries of our meetings?"
    ]
  }
]

export default function EducationalResources({ onClose }: EducationalResourcesProps) {
  const [selectedSection, setSelectedSection] = useState(0)
  const [expandedTerms, setExpandedTerms] = useState<string[]>([])
  const [checkedQuestions, setCheckedQuestions] = useState<string[]>([])

  const sections = [
    "Bankruptcy Types",
    "Process Timelines",
    "Legal Glossary",
    "Attorney Questions",
    "Referral Services",
    "Self-Help Resources"
  ]

  const toggleTerm = (term: string) => {
    if (expandedTerms.includes(term)) {
      setExpandedTerms(expandedTerms.filter(t => t !== term))
    } else {
      setExpandedTerms([...expandedTerms, term])
    }
  }

  const handleQuestionCheck = (question: string) => {
    if (checkedQuestions.includes(question)) {
      setCheckedQuestions(checkedQuestions.filter(q => q !== question))
    } else {
      setCheckedQuestions([...checkedQuestions, question])
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        {/* Educational Header */}
        <div className="bg-blue-50 border-b-2 border-blue-200 p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <BookOpenIcon className="w-8 h-8 text-blue-600 flex-shrink-0" />
              <div>
                <h2 className="text-xl font-bold text-blue-800">
                  📚 EDUCATIONAL LEGAL RESOURCES
                </h2>
                <p className="text-sm text-blue-700 font-medium">
                  General educational information about legal processes and resources
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
            This information is for general educational purposes only and does not constitute legal advice.
            Laws and procedures vary by state and individual circumstances. Always consult with qualified
            legal counsel for your specific situation.
          </p>
        </div>

        <div className="p-6">
          {/* Section Navigation */}
          <div className="flex flex-wrap border-b border-gray-200 mb-6">
            {sections.map((section, index) => (
              <button
                key={index}
                onClick={() => setSelectedSection(index)}
                className={`px-4 py-2 font-medium text-sm border-b-2 ${
                  selectedSection === index
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {section}
              </button>
            ))}
          </div>

          {/* Section Content */}
          <div className="space-y-6">
            {/* Bankruptcy Types Section */}
            {selectedSection === 0 && (
              <div className="space-y-6">
                <Card className="p-6 bg-blue-50 border-blue-200">
                  <div className="flex items-center space-x-2 mb-4">
                    <ScaleIcon className="w-6 h-6 text-blue-600" />
                    <h3 className="text-lg font-semibold text-blue-800">
                      General Bankruptcy Education
                    </h3>
                  </div>
                  <p className="text-blue-700 mb-4">
                    This section provides general educational information about different types of bankruptcy.
                    Each type has different purposes, requirements, and typical outcomes. This is educational
                    content to help you understand the general concepts.
                  </p>
                </Card>

                {bankruptcyTypes.map((type, index) => (
                  <Card key={index} className="p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-3">
                      {type.chapter}: {type.name}
                    </h4>
                    <div className="space-y-3">
                      <div>
                        <span className="font-medium text-gray-700">Description: </span>
                        <p className="text-gray-900 mt-1">{type.description}</p>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Typical Timeline: </span>
                        <p className="text-gray-900 mt-1">{type.typical_timeline}</p>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">General Eligibility: </span>
                        <p className="text-gray-900 mt-1">{type.general_eligibility}</p>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Common Outcomes: </span>
                        <p className="text-gray-900 mt-1">{type.common_outcomes}</p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}

            {/* Process Timelines Section */}
            {selectedSection === 1 && (
              <div className="space-y-6">
                <Card className="p-6 bg-purple-50 border-purple-200">
                  <div className="flex items-center space-x-2 mb-4">
                    <ClockIcon className="w-6 h-6 text-purple-600" />
                    <h3 className="text-lg font-semibold text-purple-800">
                      Educational Timeline Examples
                    </h3>
                  </div>
                  <p className="text-purple-700 mb-4">
                    These are general educational examples of typical legal process timelines.
                    Actual timelines vary significantly based on many factors including court schedules,
                    case complexity, and individual circumstances.
                  </p>
                </Card>

                {timelineExamples.map((timeline, index) => (
                  <Card key={index} className="p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">
                      {timeline.process_type}
                    </h4>
                    <div className="space-y-4">
                      {timeline.typical_steps.map((step, stepIndex) => (
                        <div key={stepIndex} className="flex items-start space-x-4">
                          <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">
                            {stepIndex + 1}
                          </div>
                          <div className="flex-grow">
                            <div className="flex items-center space-x-2 mb-1">
                              <h5 className="font-medium text-gray-900">{step.step}</h5>
                              <span className="text-sm text-gray-500">({step.timeframe})</span>
                            </div>
                            <p className="text-gray-700 text-sm">{step.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                      <p className="text-yellow-800 text-sm">
                        <strong>Important Educational Note:</strong> {timeline.important_note}
                      </p>
                    </div>
                  </Card>
                ))}
              </div>
            )}

            {/* Legal Glossary Section */}
            {selectedSection === 2 && (
              <div className="space-y-6">
                <Card className="p-6 bg-green-50 border-green-200">
                  <div className="flex items-center space-x-2 mb-4">
                    <BookOpenIcon className="w-6 h-6 text-green-600" />
                    <h3 className="text-lg font-semibold text-green-800">
                      Legal Terms Glossary (Educational)
                    </h3>
                  </div>
                  <p className="text-green-700 mb-4">
                    These are general definitions of common legal terms explained in plain English
                    for educational purposes. Click on any term to see the definition and example.
                  </p>
                </Card>

                <Card className="p-6">
                  <div className="grid gap-4">
                    {glossaryTerms.map((term, index) => (
                      <div key={index} className="border border-gray-200 rounded-lg">
                        <button
                          onClick={() => toggleTerm(term.term)}
                          className="w-full p-4 text-left flex items-center justify-between hover:bg-gray-50"
                        >
                          <span className="font-medium text-gray-900">{term.term}</span>
                          <span className="text-gray-500">
                            {expandedTerms.includes(term.term) ? '−' : '+'}
                          </span>
                        </button>
                        {expandedTerms.includes(term.term) && (
                          <div className="px-4 pb-4">
                            <p className="text-gray-700 mb-2">{term.definition}</p>
                            <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                              <p className="text-blue-800 text-sm">
                                <strong>Educational Example:</strong> {term.example}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )}

            {/* Attorney Questions Section */}
            {selectedSection === 3 && (
              <div className="space-y-6">
                <Card className="p-6 bg-orange-50 border-orange-200">
                  <div className="flex items-center space-x-2 mb-4">
                    <QuestionMarkCircleIcon className="w-6 h-6 text-orange-600" />
                    <h3 className="text-lg font-semibold text-orange-800">
                      Sample Questions to Ask Attorneys
                    </h3>
                  </div>
                  <p className="text-orange-700 mb-4">
                    These are examples of questions that informed clients typically ask when
                    interviewing attorneys. Use these as educational guidance to help you
                    prepare for attorney consultations.
                  </p>
                </Card>

                {attorneyQuestions.map((category, index) => (
                  <Card key={index} className="p-6">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">
                      {category.category}
                    </h4>
                    <div className="space-y-3">
                      {category.questions.map((question, qIndex) => (
                        <div key={qIndex} className="flex items-start space-x-3">
                          <input
                            type="checkbox"
                            id={`q${index}-${qIndex}`}
                            checked={checkedQuestions.includes(question)}
                            onChange={() => handleQuestionCheck(question)}
                            className="mt-1"
                          />
                          <label
                            htmlFor={`q${index}-${qIndex}`}
                            className="text-gray-700 cursor-pointer text-sm"
                          >
                            {question}
                          </label>
                        </div>
                      ))}
                    </div>
                  </Card>
                ))}

                {checkedQuestions.length > 0 && (
                  <Card className="p-4 bg-blue-50 border-blue-200">
                    <p className="text-blue-800 text-sm">
                      ✓ You've selected {checkedQuestions.length} questions. These can help you
                      have more productive conversations with attorneys during consultations.
                    </p>
                  </Card>
                )}
              </div>
            )}

            {/* Referral Services Section */}
            {selectedSection === 4 && (
              <div className="space-y-6">
                <Card className="p-6 bg-indigo-50 border-indigo-200">
                  <div className="flex items-center space-x-2 mb-4">
                    <BuildingLibraryIcon className="w-6 h-6 text-indigo-600" />
                    <h3 className="text-lg font-semibold text-indigo-800">
                      Bar Association Referral Services
                    </h3>
                  </div>
                  <p className="text-indigo-700 mb-4">
                    Most state bar associations provide attorney referral services to help connect
                    people with qualified attorneys. These services typically screen attorneys
                    for good standing and relevant experience.
                  </p>
                </Card>

                <Card className="p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">
                    How Bar Referral Services Typically Work
                  </h4>
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">1</div>
                      <div>
                        <h5 className="font-medium text-gray-900">Contact Your State Bar</h5>
                        <p className="text-gray-700 text-sm">Search online for "[Your State] Bar Association Attorney Referral" or call your state bar directly.</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">2</div>
                      <div>
                        <h5 className="font-medium text-gray-900">Describe Your Legal Need</h5>
                        <p className="text-gray-700 text-sm">Staff typically ask about your type of legal issue to match you with appropriate attorneys.</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">3</div>
                      <div>
                        <h5 className="font-medium text-gray-900">Receive Referrals</h5>
                        <p className="text-gray-700 text-sm">You typically receive contact information for 1-3 attorneys who handle your type of case.</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium">4</div>
                      <div>
                        <h5 className="font-medium text-gray-900">Initial Consultation</h5>
                        <p className="text-gray-700 text-sm">Many referral programs include a reduced-fee initial consultation (often $25-50 for 30 minutes).</p>
                      </div>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">
                    Other Attorney Finding Resources
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <h5 className="font-medium text-gray-700">Legal Aid Organizations</h5>
                      <p className="text-gray-600 text-sm">For low-income individuals, legal aid organizations typically provide free or low-cost legal services. Search for "[Your Area] Legal Aid."</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-700">Pro Bono Programs</h5>
                      <p className="text-gray-600 text-sm">Many bar associations coordinate pro bono (free) legal services for qualifying individuals.</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-700">Attorney Directories</h5>
                      <p className="text-gray-600 text-sm">Online directories like Martindale-Hubbell, Avvo, and state bar websites typically allow you to search for attorneys by practice area and location.</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-700">Court Self-Help Centers</h5>
                      <p className="text-gray-600 text-sm">Many courts have self-help centers that can provide information about local attorney resources and legal procedures.</p>
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* Self-Help Resources Section */}
            {selectedSection === 5 && (
              <div className="space-y-6">
                <Card className="p-6 bg-green-50 border-green-200">
                  <div className="flex items-center space-x-2 mb-4">
                    <GlobeAltIcon className="w-6 h-6 text-green-600" />
                    <h3 className="text-lg font-semibold text-green-800">
                      Court Self-Help Resources
                    </h3>
                  </div>
                  <p className="text-green-700 mb-4">
                    Many courts and government agencies provide self-help resources and educational
                    materials for people representing themselves or seeking to understand legal processes.
                  </p>
                </Card>

                <Card className="p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">
                    Federal Court Resources
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <h5 className="font-medium text-gray-700">U.S. Bankruptcy Courts</h5>
                      <p className="text-gray-600 text-sm">Most federal bankruptcy courts have self-help sections on their websites with forms, local rules, and educational materials about bankruptcy procedures.</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-700">Administrative Office of U.S. Courts</h5>
                      <p className="text-gray-600 text-sm">Provides general information about federal court procedures and the court system structure.</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-700">PACER System</h5>
                      <p className="text-gray-600 text-sm">Public Access to Court Electronic Records - allows you to view federal court documents online (fees typically apply).</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">
                    State and Local Court Resources
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <h5 className="font-medium text-gray-700">Court Self-Help Centers</h5>
                      <p className="text-gray-600 text-sm">Many local courts have physical self-help centers where staff can provide information about procedures, forms, and local rules.</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-700">Online Form Libraries</h5>
                      <p className="text-gray-600 text-sm">Most courts provide downloadable forms and instructions for common legal procedures on their websites.</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-700">Local Bar Association Resources</h5>
                      <p className="text-gray-600 text-sm">Many local bar associations provide educational seminars, legal clinics, and self-help materials for the public.</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6">
                  <h4 className="text-lg font-semibold text-gray-900 mb-4">
                    Educational and Non-Profit Resources
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <h5 className="font-medium text-gray-700">American Bar Association</h5>
                      <p className="text-gray-600 text-sm">Provides general legal education materials and consumer information about various areas of law.</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-700">Law Libraries</h5>
                      <p className="text-gray-600 text-sm">Many law libraries are open to the public and have librarians who can help you find legal resources and information.</p>
                    </div>
                    <div>
                      <h5 className="font-medium text-gray-700">Non-Profit Legal Organizations</h5>
                      <p className="text-gray-600 text-sm">Organizations focusing on specific legal areas often provide educational materials and resources on their websites.</p>
                    </div>
                  </div>
                </Card>

                <Card className="p-6 bg-yellow-50 border-yellow-200">
                  <div className="flex items-center space-x-2 mb-3">
                    <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600" />
                    <h4 className="text-lg font-semibold text-yellow-800">Important Self-Help Limitations</h4>
                  </div>
                  <div className="space-y-2 text-yellow-700 text-sm">
                    <p>• Court staff typically cannot provide legal advice, only procedural information</p>
                    <p>• Self-help resources are educational but cannot replace personalized legal counsel</p>
                    <p>• Complex legal matters typically require professional attorney assistance</p>
                    <p>• Always verify that forms and procedures are current and applicable to your jurisdiction</p>
                    <p>• Consider consulting with an attorney even if you plan to represent yourself</p>
                  </div>
                </Card>
              </div>
            )}
          </div>

          {/* Critical Disclaimer */}
          <Card className="p-6 bg-red-50 border-red-200 mt-8">
            <div className="flex items-center space-x-2 mb-3">
              <ExclamationTriangleIcon className="w-6 h-6 text-red-600" />
              <h4 className="text-lg font-bold text-red-800">Important Educational Disclaimer</h4>
            </div>
            <div className="space-y-2 text-red-700 text-sm">
              <p>• This is general educational information, not legal advice about your specific situation</p>
              <p>• Laws, procedures, and resources vary significantly by state and jurisdiction</p>
              <p>• No attorney-client relationship is created by viewing this educational content</p>
              <p>• Always verify information independently and consult qualified legal counsel</p>
              <p>• Timelines, costs, and outcomes vary greatly based on individual circumstances</p>
              <p>• When in doubt, seek professional legal assistance rather than proceeding alone</p>
            </div>
          </Card>

          {/* Close Button */}
          <div className="flex justify-center pt-6">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Close Educational Resources
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}