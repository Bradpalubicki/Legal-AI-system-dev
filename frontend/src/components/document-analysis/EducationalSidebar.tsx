'use client';

import React, { useState } from 'react';
import {
  BookOpen,
  Scale,
  HelpCircle,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Lightbulb,
  AlertTriangle,
  Shield,
  Users,
  Calendar,
  DollarSign,
  X,
  Info,
  FileText,
  Phone,
  Globe
} from 'lucide-react';

interface EducationalTopic {
  id: string;
  title: string;
  description: string;
  content: string;
  category: 'legal-basics' | 'document-types' | 'procedures' | 'rights' | 'resources';
  icon: React.ReactNode;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  readingTime: number;
}

interface EducationalSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  documentType?: string;
  analysisData?: any;
}

const EducationalSidebar: React.FC<EducationalSidebarProps> = ({
  isOpen,
  onClose,
  documentType,
  analysisData
}) => {
  const [activeCategory, setActiveCategory] = useState<string>('legal-basics');
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const educationalTopics: EducationalTopic[] = [
    // Legal Basics
    {
      id: 'contract-basics',
      title: 'Understanding Legal Contracts',
      description: 'Learn the fundamental elements that make a contract legally binding',
      content: `A contract is a legally binding agreement between two or more parties. For a contract to be valid, it must have:

**Essential Elements:**
• **Offer and Acceptance**: One party makes an offer, the other accepts it
• **Consideration**: Something of value is exchanged (money, services, promises)
• **Legal Capacity**: All parties must be legally able to enter contracts
• **Legal Purpose**: The contract must be for a lawful purpose

**Common Contract Types:**
• Service agreements (like consulting or employment)
• Sales contracts (buying/selling goods)
• Lease agreements (renting property)
• Non-disclosure agreements (protecting confidential information)

**Key Things to Look For:**
• Clear terms about what each party must do
• Specific payment amounts and due dates
• How the contract can be ended
• What happens if someone breaks the contract
• Which state's laws apply

Remember: A contract creates legal obligations. If you don't follow the terms, you could face legal consequences.`,
      category: 'legal-basics',
      icon: <FileText className="h-4 w-4" />,
      difficulty: 'beginner',
      readingTime: 3
    },
    {
      id: 'legal-terms',
      title: 'Common Legal Terminology',
      description: 'Decode legal jargon with plain English explanations',
      content: `Legal documents often use technical terms that can be confusing. Here are common terms explained in plain English:

**Contract Terms:**
• **Party**: A person or organization involved in the contract
• **Consideration**: What each side gives or gets (payment, services, etc.)
• **Breach**: When someone doesn't do what the contract says they must do
• **Termination**: Ending the contract before its natural expiration
• **Liability**: Legal responsibility for damages or obligations

**Legal Protections:**
• **Indemnification**: Protection from being held responsible for certain problems
• **Confidentiality**: Keeping information secret
• **Force Majeure**: Unforeseeable events that prevent contract performance (like natural disasters)

**Procedural Terms:**
• **Jurisdiction**: Which court has authority over disputes
• **Governing Law**: Which state or country's laws apply
• **Arbitration**: Resolving disputes outside of court
• **Counterparts**: Separate copies of the contract signed by different parties

Understanding these terms helps you know what you're agreeing to and what your rights and responsibilities are.`,
      category: 'legal-basics',
      icon: <BookOpen className="h-4 w-4" />,
      difficulty: 'beginner',
      readingTime: 4
    },
    {
      id: 'service-agreements',
      title: 'Service Agreements Explained',
      description: 'Everything you need to know about service contracts',
      content: `A service agreement is a contract where one party (the service provider) agrees to perform specific services for another party (the client) in exchange for payment.

**Key Components:**
• **Scope of Work**: Exactly what services will be provided
• **Payment Terms**: How much, when, and how payment is made
• **Timeline**: When services start, end, and key milestones
• **Deliverables**: What the client will receive
• **Responsibilities**: What each party must do

**Important Clauses to Review:**
• **Liability Limitations**: How much the service provider could owe if something goes wrong
• **Termination Clauses**: How either party can end the contract
• **Intellectual Property**: Who owns work created during the contract
• **Confidentiality**: Protection of sensitive information
• **Dispute Resolution**: How disagreements will be handled

**Red Flags to Watch For:**
• Vague service descriptions
• Unclear payment terms
• One-sided liability protections
• Automatic renewal clauses
• Excessive penalties for termination

**Questions to Ask:**
• What exactly am I paying for?
• What happens if the work isn't satisfactory?
• How can I end this contract if needed?
• What are my rights if something goes wrong?`,
      category: 'document-types',
      icon: <Scale className="h-4 w-4" />,
      difficulty: 'intermediate',
      readingTime: 5
    },
    {
      id: 'your-rights',
      title: 'Know Your Rights and Obligations',
      description: 'Understanding what you can expect and what\'s expected of you',
      content: `When you enter into a legal agreement, you gain certain rights and take on specific obligations. Understanding both is crucial for protecting yourself.

**Your Rights:**
• **Right to Performance**: The other party must do what they promised
• **Right to Payment**: If you're owed money, you can demand it according to the contract terms
• **Right to Information**: You may be entitled to updates, reports, or access to information
• **Right to Termination**: Many contracts allow you to end them under certain conditions
• **Right to Legal Remedy**: If the other party breaks the contract, you can seek legal remedies

**Your Obligations:**
• **Payment Obligations**: Pay what you owe, when you owe it
• **Cooperation**: Provide necessary information or access the other party needs
• **Confidentiality**: Keep sensitive information secret if required
• **Compliance**: Follow all terms and conditions in the agreement
• **Notice Requirements**: Inform the other party of problems or changes as required

**Protecting Your Rights:**
• Read everything carefully before signing
• Ask questions about anything you don't understand
• Keep copies of all documents and communications
• Document any problems or disputes
• Know your state's laws regarding contracts

**When Things Go Wrong:**
• Try to resolve issues directly with the other party first
• Document all communications about the problem
• Understand your options (modification, termination, legal action)
• Consider mediation or arbitration if available
• Consult with an attorney for serious disputes`,
      category: 'rights',
      icon: <Shield className="h-4 w-4" />,
      difficulty: 'intermediate',
      readingTime: 4
    },
    {
      id: 'when-attorney',
      title: 'When to Consult an Attorney',
      description: 'Recognizing situations that require professional legal help',
      content: `While many legal documents can be understood with some effort, certain situations require professional legal advice. Here's when you should consult an attorney:

**Definitely Consult an Attorney When:**
• The contract involves significant money (generally more than you can afford to lose)
• You're being asked to personally guarantee a business obligation
• The contract contains complex liability, indemnification, or insurance clauses
• You're entering a long-term commitment that's hard to exit
• The other party is represented by an attorney
• You're facing a lawsuit or legal dispute
• The contract affects your fundamental rights (employment, housing, etc.)

**Consider Consulting an Attorney When:**
• You don't understand key terms or clauses
• The contract seems heavily one-sided
• There are unusual or non-standard provisions
• You're being pressured to sign quickly
• The contract automatically renews or extends
• It involves intellectual property or confidential information

**How to Choose an Attorney:**
• Look for someone who specializes in the relevant area of law
• Check their credentials and experience
• Ask about fees upfront
• Get recommendations from trusted sources
• Many attorneys offer brief consultations to assess your needs

**What to Bring:**
• All relevant documents
• A list of your questions and concerns
• Information about deadlines or time constraints
• Details about your goals and priorities

**Cost Considerations:**
• Many attorneys offer flat fees for document review
• Brief consultations are often reasonably priced
• The cost of prevention is usually less than the cost of fixing problems later
• Some legal insurance plans cover basic contract review

Remember: It's always better to ask questions before signing than to deal with problems after.`,
      category: 'resources',
      icon: <Users className="h-4 w-4" />,
      difficulty: 'beginner',
      readingTime: 4
    }
  ];

  const categories = [
    {
      id: 'legal-basics',
      name: 'Legal Basics',
      icon: <BookOpen className="h-4 w-4" />,
      description: 'Fundamental legal concepts everyone should know'
    },
    {
      id: 'document-types',
      name: 'Document Types',
      icon: <FileText className="h-4 w-4" />,
      description: 'Understanding different kinds of legal documents'
    },
    {
      id: 'rights',
      name: 'Rights & Responsibilities',
      icon: <Shield className="h-4 w-4" />,
      description: 'Know what you can expect and what\'s expected of you'
    },
    {
      id: 'resources',
      name: 'Getting Help',
      icon: <HelpCircle className="h-4 w-4" />,
      description: 'When and how to get professional legal assistance'
    }
  ];

  const filteredTopics = educationalTopics.filter(
    topic =>
      topic.category === activeCategory &&
      (searchQuery === '' ||
       topic.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
       topic.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-800';
      case 'intermediate': return 'bg-yellow-100 text-yellow-800';
      case 'advanced': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={onClose} />

      {/* Sidebar */}
      <div className="absolute right-0 top-0 h-full w-full max-w-2xl bg-white shadow-xl overflow-hidden">
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-blue-50">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Lightbulb className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Legal Education Center</h2>
                <p className="text-sm text-gray-600">Learn about legal concepts and your rights</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Search */}
          <div className="p-4 border-b border-gray-200">
            <input
              type="text"
              placeholder="Search educational topics..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex-1 flex overflow-hidden">
            {/* Categories */}
            <div className="w-64 bg-gray-50 border-r border-gray-200 overflow-y-auto">
              <div className="p-3">
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                  Categories
                </h3>
                <nav className="space-y-1">
                  {categories.map((category) => (
                    <button
                      key={category.id}
                      onClick={() => {
                        setActiveCategory(category.id);
                        setActiveTopic(null);
                      }}
                      className={`w-full flex items-start space-x-3 px-3 py-3 text-sm rounded-lg transition-colors ${
                        activeCategory === category.id
                          ? 'bg-blue-100 text-blue-900 border border-blue-200'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      <div className="flex-shrink-0 text-gray-400">
                        {category.icon}
                      </div>
                      <div className="flex-1 text-left">
                        <div className="font-medium">{category.name}</div>
                        <div className="text-xs text-gray-500 mt-1">{category.description}</div>
                      </div>
                    </button>
                  ))}
                </nav>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {activeTopic ? (
                // Topic Content View
                <div className="p-6">
                  <button
                    onClick={() => setActiveTopic(null)}
                    className="flex items-center text-sm text-blue-600 hover:text-blue-800 mb-4"
                  >
                    <ChevronRight className="h-4 w-4 mr-1 transform rotate-180" />
                    Back to topics
                  </button>

                  {(() => {
                    const topic = educationalTopics.find(t => t.id === activeTopic);
                    if (!topic) return null;

                    return (
                      <div>
                        <div className="flex items-start space-x-3 mb-4">
                          <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
                            {topic.icon}
                          </div>
                          <div className="flex-1">
                            <h1 className="text-xl font-bold text-gray-900 mb-2">
                              {topic.title}
                            </h1>
                            <p className="text-gray-600 mb-3">{topic.description}</p>
                            <div className="flex items-center space-x-3">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(topic.difficulty)}`}>
                                {topic.difficulty}
                              </span>
                              <span className="text-sm text-gray-500 flex items-center">
                                <Clock className="h-3 w-3 mr-1" />
                                {topic.readingTime} min read
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="prose prose-blue max-w-none">
                          {topic.content.split('\n\n').map((paragraph, index) => {
                            if (paragraph.startsWith('**') && paragraph.endsWith('**')) {
                              return (
                                <h3 key={index} className="text-lg font-semibold text-gray-900 mt-6 mb-3">
                                  {paragraph.slice(2, -2)}
                                </h3>
                              );
                            }
                            if (paragraph.startsWith('•')) {
                              const items = paragraph.split('\n• ').map(item => item.replace(/^•\s*/, ''));
                              return (
                                <ul key={index} className="list-disc list-inside space-y-1 mb-4">
                                  {items.map((item, itemIndex) => (
                                    <li key={itemIndex} className="text-gray-700">
                                      {item.includes('**') ? (
                                        <>
                                          <strong>{item.match(/\*\*(.*?)\*\*/)?.[1]}</strong>
                                          {item.replace(/\*\*(.*?)\*\*:\s*/, '')}
                                        </>
                                      ) : item}
                                    </li>
                                  ))}
                                </ul>
                              );
                            }
                            return (
                              <p key={index} className="text-gray-700 mb-4 leading-relaxed">
                                {paragraph}
                              </p>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })()}
                </div>
              ) : (
                // Topics List View
                <div className="p-6">
                  <div className="mb-6">
                    <h2 className="text-lg font-semibold text-gray-900 mb-2">
                      {categories.find(c => c.id === activeCategory)?.name}
                    </h2>
                    <p className="text-gray-600">
                      {categories.find(c => c.id === activeCategory)?.description}
                    </p>
                  </div>

                  <div className="space-y-4">
                    {filteredTopics.map((topic) => (
                      <button
                        key={topic.id}
                        onClick={() => setActiveTopic(topic.id)}
                        className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors"
                      >
                        <div className="flex items-start space-x-3">
                          <div className="p-2 bg-gray-100 rounded-lg text-gray-600">
                            {topic.icon}
                          </div>
                          <div className="flex-1">
                            <h3 className="font-medium text-gray-900 mb-1">
                              {topic.title}
                            </h3>
                            <p className="text-sm text-gray-600 mb-2">
                              {topic.description}
                            </p>
                            <div className="flex items-center space-x-3">
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(topic.difficulty)}`}>
                                {topic.difficulty}
                              </span>
                              <span className="text-xs text-gray-500 flex items-center">
                                <Clock className="h-3 w-3 mr-1" />
                                {topic.readingTime} min read
                              </span>
                            </div>
                          </div>
                          <ChevronRight className="h-4 w-4 text-gray-400" />
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="border-t border-gray-200 bg-gray-50 p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-gray-600">
                <p className="font-medium text-gray-800 mb-1">Educational Content Only</p>
                <p>
                  This information is for educational purposes and does not constitute legal advice.
                  Always consult with a qualified attorney for specific legal guidance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EducationalSidebar;