'use client';

import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Clock, 
  ArrowLeft, 
  ArrowRight,
  CheckCircle,
  Star,
  Share2,
  Bookmark,
  User,
  Calendar,
  Tag,
  AlertTriangle,
  ExternalLink
} from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useAuth, useCompliance } from '@/hooks';
import { DisclaimerBanner } from '@/components/compliance';
import { UserRole, DisclaimerType } from '@/types/legal-compliance';
import { formatDistanceToNow } from 'date-fns';

interface ContentSection {
  title: string;
  content: string;
  level: number;
  estimated_read_time: number;
  prerequisites: string[];
  related_topics: string[];
}

interface TopicDetail {
  id: string;
  title: string;
  category: string;
  description: string;
  difficulty_level: number;
  sections: ContentSection[];
  keywords: string[];
  last_updated: string;
}

interface RelatedTopic {
  id: string;
  title: string;
  category: string;
  description: string;
  estimated_read_time: number;
}

const TopicDetailPage = () => {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const { complianceStatus } = useCompliance();

  const [topic, setTopic] = useState<TopicDetail | null>(null);
  const [relatedTopics, setRelatedTopics] = useState<RelatedTopic[]>([]);
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [readingProgress, setReadingProgress] = useState(0);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [showTableOfContents, setShowTableOfContents] = useState(false);

  const topicId = params.topicId as string;

  // Mock data - replace with actual API calls
  useEffect(() => {
    const loadTopicData = async () => {
      setIsLoading(true);
      
      // Simulate API call
      setTimeout(() => {
        // Mock topic data based on topicId
        const mockTopic: TopicDetail = {
          id: topicId,
          title: topicId === 'bankruptcy_basics' 
            ? 'Bankruptcy Law Fundamentals'
            : topicId === 'civil_litigation' 
              ? 'Civil Litigation Overview'
              : 'Family Law Fundamentals',
          category: topicId.replace('_', ' '),
          description: `Comprehensive guide to ${topicId.replace('_', ' ')} concepts and procedures`,
          difficulty_level: 2,
          sections: [
            {
              title: "Introduction and Overview",
              content: `
                <p>Welcome to this comprehensive guide on ${topicId.replace('_', ' ')}. This educational material 
                is designed to help you understand the fundamental concepts, key procedures, and important 
                considerations in this area of law.</p>
                
                <h3>What You'll Learn</h3>
                <ul>
                  <li>Core legal concepts and terminology</li>
                  <li>Step-by-step procedures and processes</li>
                  <li>Common challenges and how to address them</li>
                  <li>Important deadlines and requirements</li>
                  <li>When to seek professional legal assistance</li>
                </ul>
                
                <h3>Important Notice</h3>
                <div style="background-color: #fef3cd; border: 1px solid #fde68a; padding: 12px; border-radius: 6px; margin: 16px 0;">
                  <strong>⚠️ Educational Purpose Only:</strong> This content is for educational purposes only and 
                  does not constitute legal advice. Every legal situation is unique and requires individualized 
                  attention from a qualified attorney.
                </div>
                
                <p>Before we begin, it's important to understand that while this guide provides valuable information 
                about legal concepts and procedures, it cannot replace personalized legal counsel from a licensed attorney 
                who can evaluate your specific circumstances.</p>
              `,
              level: 1,
              estimated_read_time: 5,
              prerequisites: [],
              related_topics: []
            },
            {
              title: "Key Legal Concepts",
              content: `
                <p>Understanding the fundamental legal concepts is crucial for navigating any legal matter effectively. 
                This section covers the core principles and terminology you need to know.</p>
                
                <h3>Essential Terminology</h3>
                <div style="margin: 16px 0;">
                  <h4>Legal Standing</h4>
                  <p>The right of a party to challenge the conduct of another party in court. You must have legal 
                  standing to bring a lawsuit or participate in legal proceedings.</p>
                  
                  <h4>Burden of Proof</h4>
                  <p>The obligation to prove your case. In civil matters, this is typically "preponderance of the evidence" 
                  (more likely than not), while criminal cases require proof "beyond a reasonable doubt."</p>
                  
                  <h4>Statute of Limitations</h4>
                  <p>The time limit within which legal action must be taken. Missing this deadline can result in 
                  losing your right to pursue your case.</p>
                </div>
                
                <h3>Legal Process Overview</h3>
                <ol>
                  <li><strong>Initial Consultation:</strong> Meet with an attorney to discuss your situation</li>
                  <li><strong>Case Evaluation:</strong> Assess the merits and viability of your case</li>
                  <li><strong>Strategy Development:</strong> Create a plan for achieving your legal objectives</li>
                  <li><strong>Documentation:</strong> Gather and organize relevant evidence and paperwork</li>
                  <li><strong>Filing:</strong> Submit necessary legal documents to initiate proceedings</li>
                  <li><strong>Discovery:</strong> Exchange information with other parties (if applicable)</li>
                  <li><strong>Resolution:</strong> Achieve resolution through settlement or trial</li>
                </ol>
                
                <div style="background-color: #e0f2fe; border: 1px solid #81d4fa; padding: 12px; border-radius: 6px; margin: 16px 0;">
                  <strong>💡 Professional Tip:</strong> Even if you're handling some aspects of your legal matter yourself, 
                  consulting with an attorney at key stages can help you avoid costly mistakes and ensure you're 
                  protecting your interests effectively.
                </div>
              `,
              level: 2,
              estimated_read_time: 12,
              prerequisites: ["Introduction and Overview"],
              related_topics: ["legal_terminology", "court_procedures"]
            },
            {
              title: "Practical Steps and Procedures",
              content: `
                <p>This section provides practical guidance on the steps and procedures commonly involved in 
                ${topicId.replace('_', ' ')} matters.</p>
                
                <h3>Before You Begin</h3>
                <div style="background-color: #fff3cd; border: 1px solid #fde68a; padding: 12px; border-radius: 6px; margin: 16px 0;">
                  <strong>⚠️ Important:</strong> Before taking any legal action, consider whether you need professional 
                  legal representation. Some matters are complex and mistakes can have serious consequences.
                </div>
                
                <h3>Step-by-Step Process</h3>
                <div style="margin: 16px 0;">
                  <h4>Step 1: Assessment and Preparation</h4>
                  <ul>
                    <li>Gather all relevant documents and evidence</li>
                    <li>Create a timeline of important events</li>
                    <li>Identify all parties involved</li>
                    <li>Research applicable laws and deadlines</li>
                    <li>Consider your desired outcome and realistic expectations</li>
                  </ul>
                  
                  <h4>Step 2: Documentation and Filing</h4>
                  <ul>
                    <li>Complete required forms accurately and thoroughly</li>
                    <li>Attach all necessary supporting documents</li>
                    <li>Pay applicable fees</li>
                    <li>File within deadline requirements</li>
                    <li>Keep copies of all submitted materials</li>
                  </ul>
                  
                  <h4>Step 3: Service and Response</h4>
                  <ul>
                    <li>Properly serve other parties as required by law</li>
                    <li>Track service dates and methods</li>
                    <li>Monitor for responses from other parties</li>
                    <li>Respond appropriately to any counter-filings</li>
                    <li>Maintain communication records</li>
                  </ul>
                </div>
                
                <h3>Common Deadlines and Requirements</h3>
                <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                  <thead>
                    <tr style="background-color: #f9fafb;">
                      <th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Action</th>
                      <th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Typical Deadline</th>
                      <th style="border: 1px solid #d1d5db; padding: 8px; text-align: left;">Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td style="border: 1px solid #d1d5db; padding: 8px;">Initial Filing</td>
                      <td style="border: 1px solid #d1d5db; padding: 8px;">Varies by statute</td>
                      <td style="border: 1px solid #d1d5db; padding: 8px;">Check specific requirements</td>
                    </tr>
                    <tr style="background-color: #f9fafb;">
                      <td style="border: 1px solid #d1d5db; padding: 8px;">Response to Service</td>
                      <td style="border: 1px solid #d1d5db; padding: 8px;">20-30 days</td>
                      <td style="border: 1px solid #d1d5db; padding: 8px;">Varies by jurisdiction</td>
                    </tr>
                    <tr>
                      <td style="border: 1px solid #d1d5db; padding: 8px;">Discovery Requests</td>
                      <td style="border: 1px solid #d1d5db; padding: 8px;">30 days to respond</td>
                      <td style="border: 1px solid #d1d5db; padding: 8px;">Extensions may be available</td>
                    </tr>
                  </tbody>
                </table>
                
                <div style="background-color: #fef2f2; border: 1px solid #fca5a5; padding: 12px; border-radius: 6px; margin: 16px 0;">
                  <strong>🚨 Critical Warning:</strong> Missing legal deadlines can result in losing your rights or 
                  facing severe penalties. Always verify specific deadlines for your jurisdiction and case type, 
                  and consider setting earlier internal deadlines to ensure compliance.
                </div>
              `,
              level: 2,
              estimated_read_time: 15,
              prerequisites: ["Key Legal Concepts"],
              related_topics: ["deadlines", "document_preparation", "legal_forms"]
            },
            {
              title: "When to Seek Professional Help",
              content: `
                <p>While educational resources can help you understand legal concepts and procedures, there are 
                many situations where professional legal assistance is not just recommended—it's essential for 
                protecting your rights and interests.</p>
                
                <h3>Signs You Need Professional Legal Help</h3>
                <div style="margin: 16px 0;">
                  <h4>🔴 Immediate Professional Assistance Required:</h4>
                  <ul style="color: #dc2626;">
                    <li><strong>Criminal charges:</strong> Any criminal matter requires immediate legal representation</li>
                    <li><strong>Significant financial exposure:</strong> Cases involving substantial money or assets</li>
                    <li><strong>Constitutional rights:</strong> When your fundamental rights are at stake</li>
                    <li><strong>Complex legal issues:</strong> Multiple areas of law or complicated legal questions</li>
                    <li><strong>Opposing party has counsel:</strong> When the other side is represented by an attorney</li>
                  </ul>
                  
                  <h4>🟡 Strong Recommendation for Professional Help:</h4>
                  <ul style="color: #d97706;">
                    <li><strong>Unfamiliar procedures:</strong> When you're unsure about legal requirements or deadlines</li>
                    <li><strong>Emotional involvement:</strong> When emotions might cloud your judgment</li>
                    <li><strong>Limited time:</strong> When you don't have time to properly handle the matter</li>
                    <li><strong>Precedent-setting issues:</strong> Cases that could set important precedents</li>
                    <li><strong>Appeals or complex motions:</strong> Advanced legal procedures require expertise</li>
                  </ul>
                  
                  <h4>🟢 Consider Professional Consultation:</h4>
                  <ul style="color: #059669;">
                    <li><strong>Initial case evaluation:</strong> To understand your rights and options</li>
                    <li><strong>Document review:</strong> Before signing important legal documents</li>
                    <li><strong>Strategy planning:</strong> To develop an effective approach to your case</li>
                    <li><strong>Settlement negotiations:</strong> To ensure fair and enforceable agreements</li>
                    <li><strong>Periodic check-ins:</strong> Even if handling some aspects yourself</li>
                  </ul>
                </div>
                
                <h3>Types of Legal Professionals</h3>
                <div style="margin: 16px 0;">
                  <h4>Attorneys/Lawyers</h4>
                  <p>Licensed legal professionals who can represent you in court, provide legal advice, and handle 
                  all aspects of your case. Choose an attorney with relevant experience in your type of case.</p>
                  
                  <h4>Legal Aid Organizations</h4>
                  <p>Non-profit organizations that provide free or low-cost legal services to qualifying individuals. 
                  These are valuable resources if you meet their income guidelines.</p>
                  
                  <h4>Bar Association Referral Services</h4>
                  <p>Most state and local bar associations offer attorney referral services that can connect you 
                  with qualified attorneys in your area who handle your type of case.</p>
                  
                  <h4>Specialized Legal Clinics</h4>
                  <p>Many communities have specialized clinics that focus on specific areas of law or serve 
                  particular populations (veterans, seniors, immigrants, etc.).</p>
                </div>
                
                <h3>Questions to Ask Potential Attorneys</h3>
                <ol>
                  <li>How much experience do you have with cases like mine?</li>
                  <li>What are your fees and payment arrangements?</li>
                  <li>What is your assessment of my case?</li>
                  <li>What are the potential outcomes and timelines?</li>
                  <li>How will you communicate with me about case progress?</li>
                  <li>Are there any conflicts of interest?</li>
                  <li>Can you provide references from past clients?</li>
                </ol>
                
                <div style="background-color: #ecfdf5; border: 1px solid #86efac; padding: 12px; border-radius: 6px; margin: 16px 0;">
                  <strong>✅ Remember:</strong> Even a brief consultation with an attorney can help you understand 
                  your situation better and make more informed decisions. Many attorneys offer initial consultations 
                  at reduced rates or sometimes for free.
                </div>
                
                <h3>Cost Considerations</h3>
                <p>Legal representation is an investment in protecting your rights and interests. Consider:</p>
                <ul>
                  <li><strong>Hourly rates vs. flat fees:</strong> Understand how you'll be charged</li>
                  <li><strong>Contingency arrangements:</strong> Some cases can be handled on a "no win, no fee" basis</li>
                  <li><strong>Limited scope representation:</strong> Attorneys can help with specific aspects of your case</li>
                  <li><strong>Legal insurance:</strong> Some insurance policies or employee benefits include legal coverage</li>
                  <li><strong>Payment plans:</strong> Many attorneys offer payment arrangements</li>
                </ul>
                
                <p>Remember, the cost of competent legal representation is often far less than the cost of legal 
                mistakes or unfavorable outcomes that could result from proceeding without proper guidance.</p>
              `,
              level: 1,
              estimated_read_time: 10,
              prerequisites: [],
              related_topics: ["finding_attorney", "legal_costs", "legal_aid"]
            }
          ],
          keywords: ['legal education', 'legal procedures', 'attorney consultation', 'legal basics'],
          last_updated: '2024-01-08T12:00:00Z'
        };

        setTopic(mockTopic);

        // Mock related topics
        setRelatedTopics([
          {
            id: 'legal_terminology',
            title: 'Legal Terminology Guide',
            category: 'basics',
            description: 'Comprehensive glossary of common legal terms and concepts',
            estimated_read_time: 20
          },
          {
            id: 'court_procedures',
            title: 'Understanding Court Procedures',
            category: 'procedures',
            description: 'Step-by-step guide to court processes and what to expect',
            estimated_read_time: 25
          }
        ]);

        setIsLoading(false);
      }, 1000);
    };

    if (topicId) {
      loadTopicData();
    }
  }, [topicId]);

  // Simulate reading progress
  useEffect(() => {
    const handleScroll = () => {
      const scrollTop = window.pageYOffset;
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = (scrollTop / docHeight) * 100;
      setReadingProgress(Math.min(100, Math.max(0, progress)));
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const getDifficultyLabel = (level: number) => {
    switch(level) {
      case 1: return 'Beginner';
      case 2: return 'Intermediate';
      case 3: return 'Advanced';
      default: return 'Unknown';
    }
  };

  const getDifficultyColor = (level: number) => {
    switch(level) {
      case 1: return 'bg-green-100 text-green-800';
      case 2: return 'bg-yellow-100 text-yellow-800';
      case 3: return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const handleSectionNavigation = (direction: 'prev' | 'next') => {
    if (!topic) return;
    
    if (direction === 'prev' && currentSectionIndex > 0) {
      setCurrentSectionIndex(currentSectionIndex - 1);
    } else if (direction === 'next' && currentSectionIndex < topic.sections.length - 1) {
      setCurrentSectionIndex(currentSectionIndex + 1);
    }
    
    // Scroll to top of content
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading educational content...</p>
        </div>
      </div>
    );
  }

  if (!topic) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Topic Not Found</h2>
          <p className="text-gray-600 mb-4">The requested educational topic could not be found.</p>
          <Link
            href="/education"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Education Hub
          </Link>
        </div>
      </div>
    );
  }

  const currentSection = topic.sections[currentSectionIndex];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Reading Progress Bar */}
      <div className="fixed top-0 left-0 w-full h-1 bg-gray-200 z-50">
        <div 
          className="h-full bg-primary-600 transition-all duration-300"
          style={{ width: `${readingProgress}%` }}
        />
      </div>

      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link
                href="/education"
                className="flex items-center text-gray-600 hover:text-gray-900 mr-4"
              >
                <ArrowLeft className="h-5 w-5 mr-2" />
                Back to Education
              </Link>
              <div className="flex items-center">
                <BookOpen className="h-6 w-6 text-primary-600 mr-2" />
                <span className="text-sm text-gray-600">Educational Content</span>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setIsBookmarked(!isBookmarked)}
                className={`p-2 rounded-full ${isBookmarked ? 'text-yellow-600 bg-yellow-50' : 'text-gray-400 hover:text-gray-600'}`}
              >
                <Bookmark className="h-5 w-5" fill={isBookmarked ? 'currentColor' : 'none'} />
              </button>
              <button className="p-2 rounded-full text-gray-400 hover:text-gray-600">
                <Share2 className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Educational Disclaimer */}
        <div className="mb-8">
          <DisclaimerBanner
            disclaimer={{
              id: 'topic-disclaimer',
              type: DisclaimerType.EDUCATIONAL_CONTENT,
              title: 'Educational Content - Not Legal Advice',
              content: 'This educational content is for informational purposes only and does not constitute legal advice. Consult with a qualified attorney for specific legal matters.',
              displayFormat: 'header_banner' as any,
              isRequired: false,
              showForRoles: [UserRole.CLIENT, UserRole.ATTORNEY],
              context: ['education'],
              priority: 1,
              isActive: true,
              requiresAcknowledgment: false,
              dismissible: true
            }}
          />
        </div>

        {/* Topic Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-8">
          <div className="p-8">
            <div className="flex items-center justify-between mb-4">
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getDifficultyColor(topic.difficulty_level)}`}>
                {getDifficultyLabel(topic.difficulty_level)}
              </span>
              <div className="flex items-center text-sm text-gray-500">
                <Calendar className="h-4 w-4 mr-1" />
                Updated {formatDistanceToNow(new Date(topic.last_updated), { addSuffix: true })}
              </div>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              {topic.title}
            </h1>
            <p className="text-lg text-gray-600 mb-6">
              {topic.description}
            </p>
            
            {/* Topic Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
              <div className="flex items-center text-sm text-gray-600">
                <BookOpen className="h-4 w-4 mr-2" />
                {topic.sections.length} sections
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <Clock className="h-4 w-4 mr-2" />
                {topic.sections.reduce((sum, s) => sum + s.estimated_read_time, 0)} min read
              </div>
              <div className="flex items-center text-sm text-gray-600">
                <Tag className="h-4 w-4 mr-2" />
                {topic.category.replace('_', ' ')}
              </div>
            </div>

            {/* Keywords */}
            <div className="flex flex-wrap gap-2">
              {topic.keywords.map((keyword) => (
                <span key={keyword} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Table of Contents */}
          <div className="lg:col-span-1">
            <div className="sticky top-24">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Table of Contents</h3>
                <nav className="space-y-2">
                  {topic.sections.map((section, index) => (
                    <button
                      key={index}
                      onClick={() => setCurrentSectionIndex(index)}
                      className={`w-full text-left p-2 rounded-md text-sm transition-colors ${
                        index === currentSectionIndex 
                          ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-600' 
                          : 'text-gray-600 hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{section.title}</span>
                        {index === currentSectionIndex && (
                          <CheckCircle className="h-4 w-4" />
                        )}
                      </div>
                      <div className="flex items-center text-xs text-gray-500 mt-1">
                        <Clock className="h-3 w-3 mr-1" />
                        {section.estimated_read_time} min
                      </div>
                    </button>
                  ))}
                </nav>
              </div>

              {/* Related Topics */}
              {relatedTopics.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Related Topics</h3>
                  <div className="space-y-3">
                    {relatedTopics.map((relatedTopic) => (
                      <Link
                        key={relatedTopic.id}
                        href={`/education/topics/${relatedTopic.id}`}
                        className="block p-3 rounded-lg border border-gray-200 hover:border-primary-300 hover:bg-primary-50 transition-colors"
                      >
                        <h4 className="font-medium text-gray-900 text-sm">
                          {relatedTopic.title}
                        </h4>
                        <p className="text-xs text-gray-600 mt-1">
                          {relatedTopic.description}
                        </p>
                        <div className="flex items-center text-xs text-gray-500 mt-2">
                          <Clock className="h-3 w-3 mr-1" />
                          {relatedTopic.estimated_read_time} min
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              {/* Section Header */}
              <div className="border-b border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">
                    {currentSection.title}
                  </h2>
                  <span className="text-sm text-gray-500">
                    Section {currentSectionIndex + 1} of {topic.sections.length}
                  </span>
                </div>
                
                <div className="flex items-center space-x-4 text-sm text-gray-600">
                  <div className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    {currentSection.estimated_read_time} min read
                  </div>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(currentSection.level)}`}>
                    Level {currentSection.level}
                  </span>
                </div>

                {/* Prerequisites */}
                {currentSection.prerequisites.length > 0 && (
                  <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <div className="flex items-start">
                      <AlertTriangle className="h-4 w-4 text-blue-600 mt-0.5 mr-2" />
                      <div>
                        <h4 className="text-sm font-medium text-blue-800">Prerequisites</h4>
                        <p className="text-sm text-blue-700 mt-1">
                          It's recommended to read: {currentSection.prerequisites.join(', ')}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Section Content */}
              <div className="p-6">
                <div 
                  className="prose prose-gray max-w-none"
                  dangerouslySetInnerHTML={{ __html: currentSection.content }}
                />
              </div>

              {/* Section Navigation */}
              <div className="border-t border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => handleSectionNavigation('prev')}
                    disabled={currentSectionIndex === 0}
                    className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md ${
                      currentSectionIndex === 0 
                        ? 'text-gray-400 cursor-not-allowed' 
                        : 'text-primary-600 hover:text-primary-500'
                    }`}
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Previous Section
                  </button>

                  <span className="text-sm text-gray-500">
                    {currentSectionIndex + 1} / {topic.sections.length}
                  </span>

                  <button
                    onClick={() => handleSectionNavigation('next')}
                    disabled={currentSectionIndex === topic.sections.length - 1}
                    className={`inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md ${
                      currentSectionIndex === topic.sections.length - 1
                        ? 'text-gray-400 cursor-not-allowed' 
                        : 'text-primary-600 hover:text-primary-500'
                    }`}
                  >
                    Next Section
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Legal Notice */}
        <div className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 mr-3" />
            <div>
              <h4 className="text-sm font-semibold text-amber-800">
                Important Legal Notice
              </h4>
              <p className="mt-1 text-sm text-amber-700">
                This educational content is provided for informational purposes only and does not constitute 
                legal advice. Each legal situation is unique and requires individualized attention from a qualified attorney. 
                Always consult with a licensed attorney before making any legal decisions or taking any legal action.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TopicDetailPage;