import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { CheckCircle, Circle, Clock, ArrowRight, BookOpen, Target, Users, MessageSquare } from 'lucide-react';

interface OnboardingStage {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  completed: boolean;
  timeEstimate: string;
  nextAction?: string;
}

interface BetaOnboardingProps {
  betaUserId: string;
  onStageComplete?: (stageId: string) => void;
}

export const BetaOnboarding: React.FC<BetaOnboardingProps> = ({
  betaUserId,
  onStageComplete
}) => {
  const router = useRouter();
  const [currentStage, setCurrentStage] = useState(0);
  const [stages, setStages] = useState<OnboardingStage[]>([
    {
      id: 'welcome',
      title: 'Welcome to Legal AI Beta',
      description: 'Learn about the beta program and what to expect',
      icon: <Users className="h-6 w-6" />,
      completed: false,
      timeEstimate: '5 minutes',
      nextAction: 'Start Welcome Tour'
    },
    {
      id: 'training',
      title: 'Complete Training Modules',
      description: 'Interactive training on platform features and best practices',
      icon: <BookOpen className="h-6 w-6" />,
      completed: false,
      timeEstimate: '45 minutes',
      nextAction: 'Begin Training'
    },
    {
      id: 'first_document',
      title: 'Process Your First Document',
      description: 'Upload and analyze your first legal document with AI assistance',
      icon: <Target className="h-6 w-6" />,
      completed: false,
      timeEstimate: '15 minutes',
      nextAction: 'Upload Document'
    },
    {
      id: 'legal_research',
      title: 'Try Legal Research',
      description: 'Explore AI-powered legal research capabilities',
      icon: <BookOpen className="h-6 w-6" />,
      completed: false,
      timeEstimate: '20 minutes',
      nextAction: 'Start Research'
    },
    {
      id: 'feedback_collection',
      title: 'Share Your Feedback',
      description: 'Help us improve by sharing your initial impressions',
      icon: <MessageSquare className="h-6 w-6" />,
      completed: false,
      timeEstimate: '10 minutes',
      nextAction: 'Provide Feedback'
    }
  ]);

  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Load onboarding progress from API
    loadOnboardingProgress();
  }, [betaUserId]);

  const loadOnboardingProgress = async () => {
    try {
      const response = await fetch('/api/v1/beta/onboarding/progress', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const progress = await response.json();
        updateStagesFromProgress(progress);
      }
    } catch (error) {
      console.error('Failed to load onboarding progress:', error);
    }
  };

  const updateStagesFromProgress = (progress: any[]) => {
    const updatedStages = stages.map(stage => {
      const progressItem = progress.find(p => p.stage === stage.id);
      return {
        ...stage,
        completed: progressItem?.completed || false
      };
    });

    setStages(updatedStages);

    // Find current stage (first incomplete stage)
    const currentIndex = updatedStages.findIndex(stage => !stage.completed);
    setCurrentStage(currentIndex >= 0 ? currentIndex : updatedStages.length - 1);
  };

  const completeStage = async (stageId: string) => {
    setIsLoading(true);

    try {
      const response = await fetch('/api/v1/beta/onboarding/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          stage: stageId,
          completed: true,
          time_spent_minutes: 0 // This would be tracked in real implementation
        })
      });

      if (response.ok) {
        // Update local state
        const updatedStages = stages.map(stage =>
          stage.id === stageId ? { ...stage, completed: true } : stage
        );
        setStages(updatedStages);

        // Move to next stage
        const completedIndex = stages.findIndex(stage => stage.id === stageId);
        if (completedIndex < stages.length - 1) {
          setCurrentStage(completedIndex + 1);
        }

        onStageComplete?.(stageId);
      }
    } catch (error) {
      console.error('Failed to update onboarding progress:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getProgressPercentage = () => {
    const completedCount = stages.filter(stage => stage.completed).length;
    return (completedCount / stages.length) * 100;
  };

  const handleStageAction = (stage: OnboardingStage) => {
    switch (stage.id) {
      case 'welcome':
        // Start welcome tour
        startWelcomeTour();
        break;
      case 'training':
        router.push('/beta/training');
        break;
      case 'first_document':
        router.push('/documents/upload?beta=true');
        break;
      case 'legal_research':
        router.push('/research?beta=true');
        break;
      case 'feedback_collection':
        router.push('/beta/feedback');
        break;
    }
  };

  const startWelcomeTour = () => {
    // Simulate welcome tour completion
    setTimeout(() => {
      completeStage('welcome');
    }, 2000);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Welcome to Legal AI Beta Program
        </h1>
        <p className="text-lg text-gray-600 mb-4">
          You're part of an exclusive group shaping the future of legal AI
        </p>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div
            className="bg-blue-600 h-3 rounded-full transition-all duration-500"
            style={{ width: `${getProgressPercentage()}%` }}
          />
        </div>

        <p className="text-sm text-gray-500">
          {stages.filter(s => s.completed).length} of {stages.length} steps completed
        </p>
      </div>

      {/* Beta Program Overview */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
        <h2 className="text-xl font-semibold text-blue-900 mb-3">
          🎯 Your Beta Mission
        </h2>
        <div className="grid md:grid-cols-3 gap-4 text-blue-800">
          <div>
            <h3 className="font-medium mb-1">Explore Features</h3>
            <p className="text-sm">Test AI-powered legal tools and workflows</p>
          </div>
          <div>
            <h3 className="font-medium mb-1">Share Feedback</h3>
            <p className="text-sm">Help us improve with your expert insights</p>
          </div>
          <div>
            <h3 className="font-medium mb-1">Shape the Future</h3>
            <p className="text-sm">Influence features and functionality</p>
          </div>
        </div>
      </div>

      {/* Legal Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-8">
        <h3 className="font-medium text-amber-900 mb-2">⚠️ Important Disclaimer</h3>
        <p className="text-sm text-amber-800">
          This system is for educational and informational purposes only. All content provided
          is for learning about legal processes and does not constitute legal advice.
        </p>
      </div>

      {/* Onboarding Steps */}
      <div className="space-y-4">
        {stages.map((stage, index) => (
          <div
            key={stage.id}
            className={`border rounded-lg p-6 transition-all duration-200 ${
              stage.completed
                ? 'border-green-200 bg-green-50'
                : index === currentStage
                ? 'border-blue-300 bg-blue-50 shadow-md'
                : 'border-gray-200 bg-gray-50'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start space-x-4">
                {/* Stage Icon */}
                <div
                  className={`p-2 rounded-full ${
                    stage.completed
                      ? 'bg-green-100 text-green-600'
                      : index === currentStage
                      ? 'bg-blue-100 text-blue-600'
                      : 'bg-gray-100 text-gray-400'
                  }`}
                >
                  {stage.completed ? (
                    <CheckCircle className="h-6 w-6" />
                  ) : (
                    stage.icon
                  )}
                </div>

                {/* Stage Content */}
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    <h3
                      className={`text-lg font-semibold ${
                        stage.completed
                          ? 'text-green-900'
                          : index === currentStage
                          ? 'text-blue-900'
                          : 'text-gray-600'
                      }`}
                    >
                      {stage.title}
                    </h3>

                    <div className="flex items-center text-sm text-gray-500">
                      <Clock className="h-4 w-4 mr-1" />
                      {stage.timeEstimate}
                    </div>
                  </div>

                  <p
                    className={`text-sm mb-3 ${
                      stage.completed
                        ? 'text-green-700'
                        : index === currentStage
                        ? 'text-blue-700'
                        : 'text-gray-600'
                    }`}
                  >
                    {stage.description}
                  </p>

                  {/* Action Button */}
                  {!stage.completed && index === currentStage && (
                    <button
                      onClick={() => handleStageAction(stage)}
                      disabled={isLoading}
                      className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                    >
                      {isLoading ? (
                        'Loading...'
                      ) : (
                        <>
                          {stage.nextAction}
                          <ArrowRight className="h-4 w-4 ml-2" />
                        </>
                      )}
                    </button>
                  )}

                  {stage.completed && (
                    <div className="flex items-center text-sm text-green-700">
                      <CheckCircle className="h-4 w-4 mr-1" />
                      Completed
                    </div>
                  )}
                </div>
              </div>

              {/* Step Number */}
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  stage.completed
                    ? 'bg-green-100 text-green-800'
                    : index === currentStage
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {index + 1}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Support Section */}
      <div className="mt-8 bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-3">
          Need Help? We're Here for You!
        </h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-gray-800 mb-1">Beta Support Chat</h4>
            <p className="text-sm text-gray-600 mb-2">
              Get instant help from our beta support team
            </p>
            <button className="text-blue-600 text-sm font-medium hover:text-blue-700">
              Open Support Chat →
            </button>
          </div>
          <div>
            <h4 className="font-medium text-gray-800 mb-1">Weekly Office Hours</h4>
            <p className="text-sm text-gray-600 mb-2">
              Join our team every Tuesday 2-3 PM EST
            </p>
            <button className="text-blue-600 text-sm font-medium hover:text-blue-700">
              Schedule Calendar →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};