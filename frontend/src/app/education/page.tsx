'use client';

import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Video, 
  CheckCircle, 
  Clock, 
  Users, 
  ArrowRight,
  Search,
  Filter,
  Star,
  PlayCircle,
  FileText,
  HelpCircle,
  Award,
  Lightbulb
} from 'lucide-react';
import Link from 'next/link';
import { useAuth, useCompliance, useDisclaimers } from '@/hooks';
import { DisclaimerBanner } from '@/components/compliance';
import { UserRole, DisclaimerType } from '@/types/legal-compliance';

interface EducationTopic {
  id: string;
  title: string;
  category: string;
  description: string;
  difficulty_level: number;
  section_count: number;
  estimated_read_time: number;
  keywords: string[];
  last_updated: string;
}

interface VideoSeries {
  id: string;
  title: string;
  description: string;
  category: string;
  videos: string[];
  total_duration: number;
  difficulty_progression: boolean;
  completion_certificate: boolean;
  prerequisites: string[];
  learning_path: string;
}

interface InteractiveGuide {
  id: string;
  title: string;
  category: string;
  description: string;
  difficulty_level: number;
  estimated_completion_time: number;
  prerequisites: string[];
  tags: string[];
  last_updated: string;
}

const EducationHub = () => {
  const { user } = useAuth();
  const { complianceStatus } = useCompliance();
  const { disclaimers } = useDisclaimers(user?.role as UserRole | undefined);

  const [topics, setTopics] = useState<EducationTopic[]>([]);
  const [videoSeries, setVideoSeries] = useState<VideoSeries[]>([]);
  const [guides, setGuides] = useState<InteractiveGuide[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');

  // Mock data - replace with actual API calls
  useEffect(() => {
    const loadEducationData = async () => {
      setIsLoading(true);
      
      // Simulate API calls
      setTimeout(() => {
        setTopics([
          {
            id: 'bankruptcy_basics',
            title: 'Bankruptcy Law Fundamentals',
            category: 'bankruptcy',
            description: 'Comprehensive guide to U.S. bankruptcy law including Chapters 7, 11, 13, and Subchapter V',
            difficulty_level: 2,
            section_count: 5,
            estimated_read_time: 45,
            keywords: ['bankruptcy', 'chapter 7', 'chapter 11', 'chapter 13', 'subchapter v', 'discharge'],
            last_updated: '2024-01-08T12:00:00Z'
          },
          {
            id: 'civil_litigation',
            title: 'Civil Litigation Overview',
            category: 'civil_litigation',
            description: 'Comprehensive guide to the civil litigation process from filing to judgment',
            difficulty_level: 2,
            section_count: 3,
            estimated_read_time: 32,
            keywords: ['civil litigation', 'pleadings', 'discovery', 'trial', 'motions'],
            last_updated: '2024-01-08T12:00:00Z'
          },
          {
            id: 'family_law',
            title: 'Family Law Fundamentals',
            category: 'family_law',
            description: 'Essential concepts in family law including divorce, custody, and support',
            difficulty_level: 2,
            section_count: 2,
            estimated_read_time: 18,
            keywords: ['family law', 'divorce', 'child custody', 'child support', 'alimony'],
            last_updated: '2024-01-08T12:00:00Z'
          }
        ]);

        setVideoSeries([
          {
            id: 'case_types_fundamentals',
            title: 'Understanding Your Case Type',
            description: 'Comprehensive series covering different types of legal cases and their unique characteristics',
            category: 'case_types',
            videos: ['understanding_civil_cases', 'criminal_case_basics', 'family_court_process'],
            total_duration: 4500,
            difficulty_progression: true,
            completion_certificate: true,
            prerequisites: [],
            learning_path: 'Provides foundation for understanding different areas of law and court procedures'
          },
          {
            id: 'court_process_explained',
            title: 'Court Process Explained',
            description: 'Step-by-step guide through various court procedures and what to expect',
            category: 'court_process',
            videos: ['family_court_process'],
            total_duration: 1800,
            difficulty_progression: false,
            completion_certificate: true,
            prerequisites: ['case_types_fundamentals'],
            learning_path: 'Guides users through understanding court procedures and what to expect at each stage'
          }
        ]);

        setGuides([
          {
            id: 'filing_civil_lawsuit',
            title: 'How to File a Civil Lawsuit',
            category: 'court_procedures',
            description: 'Step-by-step guide to initiating civil litigation',
            difficulty_level: 2,
            estimated_completion_time: 240,
            prerequisites: ['understanding_civil_litigation'],
            tags: ['civil litigation', 'complaint', 'filing', 'procedure'],
            last_updated: '2024-01-08T12:00:00Z'
          },
          {
            id: 'responding_to_lawsuit',
            title: 'How to Respond to a Lawsuit',
            category: 'court_procedures',
            description: 'Guide for defendants on responding to civil complaints',
            difficulty_level: 2,
            estimated_completion_time: 180,
            prerequisites: ['understanding_civil_litigation'],
            tags: ['civil litigation', 'answer', 'motion to dismiss', 'defense'],
            last_updated: '2024-01-08T12:00:00Z'
          }
        ]);

        setIsLoading(false);
      }, 1000);
    };

    loadEducationData();
  }, []);

  const filteredTopics = topics.filter(topic => {
    const matchesSearch = topic.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         topic.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         topic.keywords.some(keyword => keyword.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === 'all' || topic.category === selectedCategory;
    const matchesDifficulty = selectedDifficulty === 'all' || topic.difficulty_level.toString() === selectedDifficulty;
    
    return matchesSearch && matchesCategory && matchesDifficulty;
  });

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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <BookOpen className="h-8 w-8 text-legal-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">
                Legal Education Hub
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Learn at your own pace
              </span>
              <Link
                href="/education/progress"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                <Award className="h-4 w-4 mr-2" />
                My Progress
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Educational Disclaimer */}
        <div className="mb-8">
          <DisclaimerBanner
            disclaimer={{
              id: 'education-disclaimer',
              type: DisclaimerType.EDUCATIONAL_CONTENT,
              title: 'Educational Content - Not Legal Advice',
              content: 'The educational materials provided are for informational purposes only and do not constitute legal advice. Always consult with a qualified attorney for specific legal matters.',
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

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <BookOpen className="h-8 w-8 text-blue-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Topics Available
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {topics.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Video className="h-8 w-8 text-purple-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Video Series
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {videoSeries.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <HelpCircle className="h-8 w-8 text-green-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Interactive Guides
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {guides.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Clock className="h-8 w-8 text-orange-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Avg. Reading Time
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {Math.round(topics.reduce((sum, t) => sum + t.estimated_read_time, 0) / topics.length) || 0} min
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Featured Video Series */}
        <div className="mb-8">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-lg overflow-hidden">
            <div className="px-8 py-6 text-white">
              <h2 className="text-2xl font-bold mb-2">Featured Learning Path</h2>
              <p className="text-blue-100 mb-4">
                Start with our comprehensive "Understanding Your Case Type" series
              </p>
              <div className="flex items-center space-x-6 mb-4">
                <div className="flex items-center">
                  <Video className="h-5 w-5 mr-2" />
                  <span>{videoSeries[0]?.videos.length || 0} Videos</span>
                </div>
                <div className="flex items-center">
                  <Clock className="h-5 w-5 mr-2" />
                  <span>{Math.floor((videoSeries[0]?.total_duration || 0) / 60)} minutes</span>
                </div>
                <div className="flex items-center">
                  <Award className="h-5 w-5 mr-2" />
                  <span>Certificate Available</span>
                </div>
              </div>
              <Link
                href={`/education/videos/${videoSeries[0]?.id}`}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-blue-600 bg-white hover:bg-gray-50 transition-colors"
              >
                <PlayCircle className="h-5 w-5 mr-2" />
                Start Learning
              </Link>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="mb-8 bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search topics, guides, or videos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All Categories</option>
              <option value="bankruptcy">Bankruptcy Law</option>
              <option value="civil_litigation">Civil Litigation</option>
              <option value="criminal_procedure">Criminal Procedure</option>
              <option value="family_law">Family Law</option>
              <option value="real_estate">Real Estate</option>
              <option value="business_formation">Business Formation</option>
            </select>
            <select
              value={selectedDifficulty}
              onChange={(e) => setSelectedDifficulty(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All Difficulty Levels</option>
              <option value="1">Beginner</option>
              <option value="2">Intermediate</option>
              <option value="3">Advanced</option>
            </select>
          </div>
        </div>

        {/* Content Sections */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Educational Topics */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900 flex items-center">
                  <FileText className="h-6 w-6 text-blue-600 mr-2" />
                  Educational Topics
                </h2>
                <p className="text-sm text-gray-600 mt-1">
                  In-depth articles on legal concepts and procedures
                </p>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 gap-6">
                  {filteredTopics.map((topic) => (
                    <div key={topic.id} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h3 className="text-lg font-semibold text-gray-900">
                              {topic.title}
                            </h3>
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDifficultyColor(topic.difficulty_level)}`}>
                              {getDifficultyLabel(topic.difficulty_level)}
                            </span>
                          </div>
                          <p className="text-gray-600 mb-4">
                            {topic.description}
                          </p>
                          <div className="flex items-center text-sm text-gray-500 space-x-4">
                            <div className="flex items-center">
                              <FileText className="h-4 w-4 mr-1" />
                              {topic.section_count} sections
                            </div>
                            <div className="flex items-center">
                              <Clock className="h-4 w-4 mr-1" />
                              {topic.estimated_read_time} min read
                            </div>
                          </div>
                          <div className="flex flex-wrap gap-1 mt-3">
                            {topic.keywords.slice(0, 3).map((keyword) => (
                              <span key={keyword} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
                                {keyword}
                              </span>
                            ))}
                            {topic.keywords.length > 3 && (
                              <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
                                +{topic.keywords.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="ml-4">
                          <Link
                            href={`/education/topics/${topic.id}`}
                            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-primary-600 bg-primary-50 hover:bg-primary-100"
                          >
                            Read More
                            <ArrowRight className="h-4 w-4 ml-2" />
                          </Link>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Interactive Guides */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <HelpCircle className="h-5 w-5 text-green-600 mr-2" />
                  Interactive Guides
                </h3>
              </div>
              <div className="p-6 space-y-4">
                {guides.map((guide) => (
                  <div key={guide.id} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">
                      {guide.title}
                    </h4>
                    <p className="text-sm text-gray-600 mb-3">
                      {guide.description}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                      <span className="flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {guide.estimated_completion_time} min
                      </span>
                      <span className={`px-2 py-1 rounded-full ${getDifficultyColor(guide.difficulty_level)}`}>
                        {getDifficultyLabel(guide.difficulty_level)}
                      </span>
                    </div>
                    <Link
                      href={`/education/guides/${guide.id}`}
                      className="text-sm text-primary-600 hover:text-primary-500 font-medium"
                    >
                      Start Guide →
                    </Link>
                  </div>
                ))}
                <Link
                  href="/education/guides"
                  className="block text-center text-sm text-primary-600 hover:text-primary-500 font-medium"
                >
                  View All Guides
                </Link>
              </div>
            </div>

            {/* Video Series */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                  <Video className="h-5 w-5 text-purple-600 mr-2" />
                  Video Learning
                </h3>
              </div>
              <div className="p-6 space-y-4">
                {videoSeries.map((series) => (
                  <div key={series.id} className="border border-gray-200 rounded-lg p-4">
                    <h4 className="font-medium text-gray-900 mb-2">
                      {series.title}
                    </h4>
                    <p className="text-sm text-gray-600 mb-3">
                      {series.description}
                    </p>
                    <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                      <span className="flex items-center">
                        <PlayCircle className="h-3 w-3 mr-1" />
                        {series.videos.length} videos
                      </span>
                      <span className="flex items-center">
                        <Clock className="h-3 w-3 mr-1" />
                        {Math.floor(series.total_duration / 60)} min
                      </span>
                    </div>
                    {series.completion_certificate && (
                      <div className="flex items-center text-xs text-green-600 mb-3">
                        <Award className="h-3 w-3 mr-1" />
                        Certificate Available
                      </div>
                    )}
                    <Link
                      href={`/education/videos/${series.id}`}
                      className="text-sm text-primary-600 hover:text-primary-500 font-medium"
                    >
                      Watch Series →
                    </Link>
                  </div>
                ))}
                <Link
                  href="/education/videos"
                  className="block text-center text-sm text-primary-600 hover:text-primary-500 font-medium"
                >
                  Browse All Videos
                </Link>
              </div>
            </div>

            {/* Quick Tools */}
            <div className="bg-legal-50 border border-legal-200 rounded-lg">
              <div className="px-6 py-4 border-b border-legal-200">
                <h3 className="text-lg font-semibold text-legal-900 flex items-center">
                  <Lightbulb className="h-5 w-5 text-legal-600 mr-2" />
                  Quick Tools
                </h3>
              </div>
              <div className="p-6 space-y-3">
                <Link
                  href="/education/glossary"
                  className="flex items-center p-3 rounded-lg hover:bg-legal-100 transition-colors"
                >
                  <BookOpen className="h-5 w-5 text-legal-600 mr-3" />
                  <div>
                    <div className="font-medium text-legal-900">Legal Glossary</div>
                    <div className="text-sm text-legal-700">Look up legal terms</div>
                  </div>
                </Link>
                <Link
                  href="/education/deadlines"
                  className="flex items-center p-3 rounded-lg hover:bg-legal-100 transition-colors"
                >
                  <Clock className="h-5 w-5 text-legal-600 mr-3" />
                  <div>
                    <div className="font-medium text-legal-900">Deadline Calculator</div>
                    <div className="text-sm text-legal-700">Calculate legal deadlines</div>
                  </div>
                </Link>
                <Link
                  href="/education/checklists"
                  className="flex items-center p-3 rounded-lg hover:bg-legal-100 transition-colors"
                >
                  <CheckCircle className="h-5 w-5 text-legal-600 mr-3" />
                  <div>
                    <div className="font-medium text-legal-900">Document Checklists</div>
                    <div className="text-sm text-legal-700">Preparation guides</div>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Educational Notice */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <BookOpen className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
            <div>
              <h4 className="text-sm font-semibold text-blue-800">
                Educational Purpose Notice
              </h4>
              <p className="mt-1 text-sm text-blue-700">
                All educational content is provided for informational purposes only and should not be considered 
                legal advice. Each legal situation is unique and requires individualized attention from a qualified attorney. 
                This material is designed to help you understand general legal concepts and procedures.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EducationHub;