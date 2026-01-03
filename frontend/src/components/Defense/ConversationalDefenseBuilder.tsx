'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card } from '@/components/design-system';
import { Shield, Send, Loader2, CheckCircle, AlertCircle, MessageSquare, Lightbulb, HelpCircle, Swords } from 'lucide-react';

import { API_CONFIG } from '../../config/api';
import AdversarialProgress from './AdversarialProgress';
import CounterArgumentMatrix from './CounterArgumentMatrix';

// Adversarial simulation types
interface AdversarialSimulationState {
  simulationId: string | null;
  status: 'disabled' | 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  counterCount: number;
  estimatedTimeRemaining?: number;
  results: AdversarialResults | null;
}

interface AdversarialResults {
  counter_arguments: any[];
  weaknesses: any[];
  overall_strength: 'weak' | 'moderate' | 'strong';
  recommendations: string[];
  case_type?: string;
}
interface DocumentData {
  id: string;
  fileName: string;
  fileType: string;
  uploadDate: Date;
  text: string;
  summary?: string;
  parties?: string[];
  importantDates?: Array<{ date: string; description: string }>;
  keyFigures?: Array<{ label: string; value: string }>;
  keywords?: string[];
  analysis?: any;
}

export interface Message {
  id: string;
  role: 'ai' | 'user';
  content: string;
  timestamp: Date;
}

export interface DefenseAnalysis {
  situation: string;
  defenses: Array<{
    title: string;
    description: string;
    reasoning?: string;
    strength?: string;
  }>;
  actions: string[];
  evidence: string[];
  suggested_questions?: string[];
  case_type: string;
  analysis_summary: {
    total_defenses: number;
    document_type: string;
    analysis_date: string;
  };
}

interface ConversationalDefenseBuilderProps {
  document: DocumentData;
  sessionId: string;
  messages: Message[];
  onMessagesChange: (messages: Message[]) => void;
  collectedAnswers: string[];
  onCollectedAnswersChange: (answers: string[]) => void;
  conversationPhase: 'intro' | 'questions' | 'analysis' | 'complete';
  onConversationPhaseChange: (phase: 'intro' | 'questions' | 'analysis' | 'complete') => void;
  defenseAnalysis: DefenseAnalysis | null;
  onDefenseAnalysisChange: (analysis: DefenseAnalysis | null) => void;
}

export function ConversationalDefenseBuilder({
  document,
  sessionId,
  messages,
  onMessagesChange,
  collectedAnswers,
  onCollectedAnswersChange,
  conversationPhase,
  onConversationPhaseChange,
  defenseAnalysis,
  onDefenseAnalysisChange
}: ConversationalDefenseBuilderProps) {
  const [userInput, setUserInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const chatInterfaceRef = useRef<HTMLDivElement>(null);

  // Adversarial simulation state
  const [adversarialSimulation, setAdversarialSimulation] = useState<AdversarialSimulationState>({
    simulationId: null,
    status: 'disabled', // Start disabled, will enable when interview starts if user has access
    progress: 0,
    counterCount: 0,
    results: null
  });
  const adversarialPollRef = useRef<NodeJS.Timeout | null>(null);

  // Auto-scroll to bottom of chat (within container only, don't scroll entire page)
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
  }, [messages]);

  // Load defense session from database on mount
  useEffect(() => {
    const loadDefenseSession = async () => {
      if (defenseAnalysis) return;  // Already loaded

      try {
        const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/defense/session/${sessionId}`);
        if (response.ok) {
          const data = await response.json();

          // Restore defense analysis
          if (data.defenses && data.actions) {
            const loadedAnalysis: DefenseAnalysis = {
              situation: data.situation || '',
              defenses: data.defenses || [],
              actions: data.actions || [],
              evidence: data.evidence || [],
              case_type: data.case_type || '',
              analysis_summary: data.analysis_data?.analysis_summary || {
                total_defenses: data.defenses?.length || 0,
                document_type: 'Legal Document',
                analysis_date: data.completed_at || new Date().toISOString()
              }
            };

            onDefenseAnalysisChange(loadedAnalysis);
            onConversationPhaseChange('complete');
            console.log('Loaded defense session from database');
          }
        }
      } catch (error) {
        console.error('Error loading defense session:', error);
      }
    };

    loadDefenseSession();
  }, [sessionId]);

  // Start conversation when component mounts (only if no messages exist and no loaded analysis)
  useEffect(() => {
    if (messages.length === 0 && !defenseAnalysis) {
      startConversation();
    }
  }, [document.id]);

  // Cleanup adversarial polling on unmount
  useEffect(() => {
    return () => {
      if (adversarialPollRef.current) {
        clearInterval(adversarialPollRef.current);
      }
    };
  }, []);

  // Start adversarial simulation
  const startAdversarialSimulation = async (defenseSessionId: string, caseType: string) => {
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/defense/adversarial/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: defenseSessionId,
          case_type: caseType
        })
      });

      if (response.status === 403) {
        // Feature not available - user needs to upgrade
        setAdversarialSimulation(prev => ({
          ...prev,
          status: 'disabled'
        }));
        return;
      }

      if (response.ok) {
        const data = await response.json();
        setAdversarialSimulation(prev => ({
          ...prev,
          simulationId: data.simulation_id,
          status: 'pending',
          progress: 0
        }));

        console.log('Started adversarial simulation:', data.simulation_id);
      }
    } catch (error) {
      console.error('Error starting adversarial simulation:', error);
    }
  };

  // Update adversarial simulation with new facts
  const updateAdversarialSimulation = async (questionKey: string, answer: string) => {
    if (!adversarialSimulation.simulationId || adversarialSimulation.status === 'disabled') return;

    try {
      const response = await fetch(
        `${API_CONFIG.BASE_URL}/api/v1/defense/adversarial/${adversarialSimulation.simulationId}/update`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            new_facts: { [questionKey]: answer },
            question_key: questionKey
          })
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAdversarialSimulation(prev => ({
          ...prev,
          status: data.status === 'running' ? 'running' : prev.status,
          progress: data.progress || prev.progress
        }));
      }
    } catch (error) {
      console.error('Error updating adversarial simulation:', error);
    }
  };

  // Finalize adversarial simulation
  const finalizeAdversarialSimulation = async () => {
    if (!adversarialSimulation.simulationId || adversarialSimulation.status === 'disabled') return;

    try {
      setAdversarialSimulation(prev => ({
        ...prev,
        status: 'running',
        progress: 50
      }));

      const response = await fetch(
        `${API_CONFIG.BASE_URL}/api/v1/defense/adversarial/${adversarialSimulation.simulationId}/finalize`,
        { method: 'POST' }
      );

      if (response.ok) {
        const data = await response.json();
        setAdversarialSimulation(prev => ({
          ...prev,
          status: 'completed',
          progress: 100,
          counterCount: data.counter_arguments?.length || 0,
          results: {
            counter_arguments: data.counter_arguments || [],
            weaknesses: data.weaknesses || [],
            overall_strength: data.overall_strength || 'moderate',
            recommendations: data.recommendations || [],
            case_type: data.case_type
          }
        }));
        console.log('Adversarial simulation completed:', data);
      } else {
        setAdversarialSimulation(prev => ({
          ...prev,
          status: 'failed'
        }));
      }
    } catch (error) {
      console.error('Error finalizing adversarial simulation:', error);
      setAdversarialSimulation(prev => ({
        ...prev,
        status: 'failed'
      }));
    }
  };

  // Poll for adversarial simulation status
  const pollAdversarialStatus = useCallback(async () => {
    if (!adversarialSimulation.simulationId ||
        adversarialSimulation.status === 'completed' ||
        adversarialSimulation.status === 'failed' ||
        adversarialSimulation.status === 'disabled') {
      return;
    }

    try {
      const response = await fetch(
        `${API_CONFIG.BASE_URL}/api/v1/defense/adversarial/${adversarialSimulation.simulationId}/status`
      );

      if (response.ok) {
        const data = await response.json();
        setAdversarialSimulation(prev => ({
          ...prev,
          status: data.status,
          progress: data.progress,
          counterCount: data.counter_count,
          estimatedTimeRemaining: data.estimated_time_remaining
        }));

        // If completed, fetch full results
        if (data.status === 'completed') {
          const resultsResponse = await fetch(
            `${API_CONFIG.BASE_URL}/api/v1/defense/adversarial/${adversarialSimulation.simulationId}/results`
          );
          if (resultsResponse.ok) {
            const results = await resultsResponse.json();
            setAdversarialSimulation(prev => ({
              ...prev,
              results: {
                counter_arguments: results.counter_arguments || [],
                weaknesses: results.weaknesses || [],
                overall_strength: results.overall_strength || 'moderate',
                recommendations: results.recommendations || [],
                case_type: results.case_type
              }
            }));
          }
        }
      }
    } catch (error) {
      console.error('Error polling adversarial status:', error);
    }
  }, [adversarialSimulation.simulationId, adversarialSimulation.status]);

  const startConversation = () => {
    const greeting = {
      id: crypto.randomUUID(),
      role: 'ai' as const,
      content: `Good day. I'm your Senior Defense Counsel, specializing in complex litigation strategy. I've conducted a preliminary review of "${document.fileName}" and I'm prepared to develop a comprehensive defense strategy tailored to your matter.

To construct the most effective legal defense, I need to conduct a strategic intake interview. This will allow me to identify viable defenses, procedural issues, and evidentiary gaps that we can exploit.

**Strategic Question 1:** Factual chronology and your version of events.

Please provide a detailed narrative of the underlying facts from your perspective. Include specific dates, communications, transactions, and any material facts that contradict the plaintiff's allegations. What is your account of what transpired?`,
      timestamp: new Date()
    };

    onMessagesChange([greeting]);
    onConversationPhaseChange('questions');
  };

  const handleSendMessage = async () => {
    if (!userInput.trim() || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: userInput.trim(),
      timestamp: new Date()
    };

    const updatedMessages = [...messages, userMessage];
    onMessagesChange(updatedMessages);
    setUserInput('');
    setIsLoading(true);

    try {
      // If defense is complete, handle as follow-up Q&A
      if (conversationPhase === 'complete') {
        // Call Q&A API with defense context
        const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/qa/ask`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            document_text: document.text,
            document_analysis: document.analysis,
            question: `${userInput.trim()}\n\nContext: This is a follow-up question about the defense strategy for "${document.fileName}". The defense analysis identified ${defenseAnalysis?.defenses.length || 0} defense strategies. Please provide detailed guidance based on the defense context.`,
            session_id: sessionId,
            document_id: document.id
          })
        });

        if (response.ok) {
          const data = await response.json();
          const aiMessage: Message = {
            id: crypto.randomUUID(),
            role: 'ai',
            content: data.answer || 'I need more information to answer that question.',
            timestamp: new Date()
          };
          onMessagesChange([...updatedMessages, aiMessage]);
        } else {
          throw new Error('Failed to get response');
        }
        setIsLoading(false);
        return;
      }

      // Otherwise, continue with interview questions
      const updatedAnswers = [...collectedAnswers, userInput.trim()];
      onCollectedAnswersChange(updatedAnswers);
      const answerCount = updatedAnswers.length;

      // Start adversarial simulation after first answer
      if (answerCount === 1 && !adversarialSimulation.simulationId) {
        // Estimate case type from document
        const docText = (document.text || '').toLowerCase();
        let estimatedCaseType = 'general';
        if (docText.includes('debt') || docText.includes('collection') || docText.includes('creditor')) {
          estimatedCaseType = 'debt_collection';
        } else if (docText.includes('evict') || docText.includes('landlord') || docText.includes('tenant')) {
          estimatedCaseType = 'eviction';
        } else if (docText.includes('foreclose') || docText.includes('mortgage')) {
          estimatedCaseType = 'foreclosure';
        } else if (docText.includes('bankrupt')) {
          estimatedCaseType = 'bankruptcy';
        }

        // Start simulation with session ID
        startAdversarialSimulation(sessionId, estimatedCaseType);
      }

      // Update adversarial simulation with new facts
      const questionKey = `question_${answerCount}`;
      updateAdversarialSimulation(questionKey, userInput.trim());

      if (answerCount < 4) {
        // Ask more questions
        const nextQuestion = getNextQuestion(answerCount, userMessage.content);

        setTimeout(() => {
          const aiMessage: Message = {
            id: crypto.randomUUID(),
            role: 'ai',
            content: nextQuestion,
            timestamp: new Date()
          };
          onMessagesChange([...updatedMessages, aiMessage]);
          setIsLoading(false);
        }, 1000);
      } else {
        // Enough information - analyze and build defense
        onConversationPhaseChange('analysis');

        const analyzingMessage: Message = {
          id: crypto.randomUUID(),
          role: 'ai',
          content: `Thank you for your thorough responses. I now have sufficient information to conduct a comprehensive legal analysis.

I will now cross-reference your testimony against the documentary evidence and pleadings to identify:
• Affirmative defenses and procedural challenges
• Evidentiary weaknesses in the opposing party's case
• Strategic opportunities for dispositive motions
• Settlement leverage points

Conducting strategic analysis...`,
          timestamp: new Date()
        };

        onMessagesChange([...updatedMessages, analyzingMessage]);

        // Call defense analysis API
        await buildDefenseStrategy(updatedMessages, updatedAnswers);
      }
    } catch (error) {
      console.error('Error in conversation:', error);
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'ai',
        content: 'I apologize, but I encountered an error. Please try again.',
        timestamp: new Date()
      };
      onMessagesChange([...updatedMessages, errorMessage]);
      setIsLoading(false);
    }
  };

  const getNextQuestion = (answerNumber: number, previousAnswer: string): string => {
    const questions = [
      `**Strategic Question 2:** Evidentiary foundation and documentation.

What documentary evidence, tangible proof, or witness testimony can you produce to support your factual allegations? This includes:
- Contemporaneous communications (emails, texts, letters)
- Financial records (receipts, bank statements, contracts)
- Physical evidence or expert reports
- Credible witnesses with personal knowledge

Please detail all available evidence, even if incomplete. I'll assess admissibility and strategic value.`,

      `**Strategic Question 3:** Actions taken and procedural posture.

Have you taken any responsive actions since receiving this complaint/notice? Specifically:
- Filed any pleadings or motions with the court?
- Retained other counsel or sought legal advice?
- Made any admissions or statements to opposing parties?
- Engaged in settlement negotiations?
- Missed any critical deadlines?

Your candid disclosure is protected and essential for strategic planning.`,

      `**Strategic Question 4:** Litigation objectives and risk tolerance.

What are your strategic objectives in this matter? Please prioritize:
- Complete dismissal (prevail on merits or procedural grounds)
- Minimize financial exposure (settlement within specific parameters)
- Delay or extend litigation timeline (if strategically advantageous)
- Establish legal precedent or send a message
- Preserve business relationships or reputation

Also indicate your appetite for litigation costs and trial risk versus settlement certainty.`
    ];

    return questions[answerNumber - 1] || questions[questions.length - 1];
  };

  const buildDefenseStrategy = async (currentMessages: Message[], currentAnswers: string[]) => {
    try {
      // Combine conversation context with document
      const conversationSummary = currentAnswers.map((answer, i) =>
        `Q${i+1} Response: ${answer}`
      ).join('\n\n');

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/defense/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_text: `${document.text}\n\n=== INTERVIEW RESPONSES ===\n${conversationSummary}`,
          document_analysis: {
            document_type: document.analysis?.document_type || 'Legal Document',
            summary: document.summary || '',
            parties: document.parties || [],
            key_dates: document.importantDates || [],
            keywords: document.keywords || []
          },
          case_context: {
            fileName: document.fileName,
            interview_responses: currentAnswers
          },
          session_id: sessionId,  // For database persistence
          document_id: document.id  // Link to document in database
        })
      });

      if (!response.ok) {
        throw new Error('Failed to analyze defense');
      }

      const data = await response.json();
      onDefenseAnalysisChange(data);
      onConversationPhaseChange('complete');

      // Finalize adversarial simulation in background
      if (adversarialSimulation.simulationId) {
        finalizeAdversarialSimulation();
      }

      const completionMessage: Message = {
        id: crypto.randomUUID(),
        role: 'ai',
        content: `⚖️ **Legal Analysis Complete**

I have completed my strategic review and compiled a comprehensive defense memorandum. This analysis synthesizes the documentary evidence with your testimony to identify viable legal theories and tactical approaches.

Please review the defense strategies, recommended actions, and evidentiary requirements detailed below. Each defense has been evaluated for legal merit and strategic value.`,
        timestamp: new Date()
      };

      onMessagesChange([...currentMessages, completionMessage]);
      setIsLoading(false);
    } catch (error) {
      console.error('Error building defense:', error);
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'ai',
        content: '❌ I encountered an error building the defense strategy. Please try again.',
        timestamp: new Date()
      };
      onMessagesChange([...currentMessages, errorMessage]);
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="conversational-defense-builder space-y-6">
      {/* Chat Interface */}
      <Card className="p-6" ref={chatInterfaceRef as any}>
          <div className="mb-4">
            <h2 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <MessageSquare className="w-6 h-6 text-teal-600" />
              AI Defense Strategy Interview
            </h2>
            <p className="text-sm text-slate-600 mt-1">
              Answer the AI's questions to build a personalized defense strategy
            </p>
          </div>

        {/* Messages */}
        <div className="bg-slate-50 rounded-lg p-4 mb-4 h-96 overflow-y-auto space-y-4">
          {messages.map(message => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-teal-600 text-white'
                    : 'bg-white border border-slate-200 text-slate-900'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-100' : 'text-slate-500'}`}>
                  {message.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 rounded-lg p-4 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-teal-600" />
                <p className="text-sm text-slate-600">AI is thinking...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Adversarial Simulation Progress - shown during interview */}
        {conversationPhase === 'questions' && (
          <AdversarialProgress
            simulationId={adversarialSimulation.simulationId || undefined}
            isActive={adversarialSimulation.status !== 'disabled' && collectedAnswers.length > 0}
            progress={adversarialSimulation.progress}
            counterCount={adversarialSimulation.counterCount}
            status={adversarialSimulation.status}
            estimatedTimeRemaining={adversarialSimulation.estimatedTimeRemaining}
            isPaidFeature={true}
          />
        )}

        {/* Input - Always show for follow-up questions */}
        <div className="flex gap-2">
          <textarea
            ref={textareaRef}
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder={
              conversationPhase === 'complete'
                ? "Ask a follow-up question about your defense strategy..."
                : "Type your answer here... (Press Enter to send, Shift+Enter for new line)"
            }
            className="flex-1 p-3 border border-slate-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!userInput.trim() || isLoading}
            className="px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:bg-slate-300 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <Send className="w-5 h-5" />
            Send
          </button>
        </div>
      </Card>

      {/* Defense Analysis Results */}
      {defenseAnalysis && conversationPhase === 'complete' && (
        <>
          <Card className="p-6 bg-green-50 border-green-200">
            <div className="flex items-center gap-2 text-green-900 mb-2">
              <CheckCircle className="w-6 h-6" />
              <h2 className="text-2xl font-bold">Defense Strategy Complete</h2>
            </div>
            <p className="text-green-800 mb-2">
              <strong>Case Type:</strong> {defenseAnalysis.case_type}
            </p>
            <p className="text-green-800">
              <strong>Confidence:</strong> Based on {collectedAnswers.length} interview responses + document analysis
            </p>
          </Card>

          {/* Situation Summary */}
          <Card className="p-6">
            <h3 className="text-xl font-bold text-slate-900 mb-3">Situation Analysis</h3>
            <p className="text-slate-700 whitespace-pre-wrap">{defenseAnalysis.situation}</p>
          </Card>

          {/* Defense Strategies */}
          <div className="space-y-4">
            <h3 className="text-xl font-bold text-slate-900">Recommended Defense Strategies</h3>
            {defenseAnalysis.defenses.map((defense, index) => (
              <Card key={index} className="p-6 border-l-4 border-blue-600">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-lg font-bold text-slate-900">{defense.title}</h4>
                  {defense.strength && (
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                      String(defense.strength).toLowerCase() === 'strong' ? 'bg-green-100 text-green-800' :
                      String(defense.strength).toLowerCase() === 'moderate' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-slate-100 text-slate-800'
                    }`}>
                      {defense.strength}
                    </span>
                  )}
                </div>
                <p className="text-slate-700 mb-3">{defense.description}</p>
                {defense.reasoning && (
                  <div className="mt-3 p-3 bg-teal-50 border-l-2 border-blue-400 rounded">
                    <p className="text-sm font-semibold text-navy-800 mb-1">Why This Defense Is Recommended:</p>
                    <p className="text-sm text-navy-700">{defense.reasoning}</p>
                  </div>
                )}
              </Card>
            ))}
          </div>

          {/* Immediate Actions */}
          {defenseAnalysis.actions && defenseAnalysis.actions.length > 0 && (
            <Card className="p-6 bg-teal-50 border-blue-200">
              <h3 className="text-lg font-bold text-navy-800 mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                Next Steps - What to Do Now
              </h3>
              <ol className="list-decimal list-inside space-y-2 text-navy-700">
                {defenseAnalysis.actions.map((action, index) => (
                  <li key={index}>{action}</li>
                ))}
              </ol>
            </Card>
          )}

          {/* Evidence Needed */}
          {defenseAnalysis.evidence && defenseAnalysis.evidence.length > 0 && (
            <Card className="p-6 bg-amber-50 border-amber-200">
              <h3 className="text-lg font-bold text-amber-900 mb-3">Evidence to Gather</h3>
              <ul className="list-disc list-inside space-y-2 text-amber-800">
                {defenseAnalysis.evidence.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </Card>
          )}

          {/* Adversarial Counter-Argument Matrix */}
          {adversarialSimulation.status === 'completed' && adversarialSimulation.results && (
            <CounterArgumentMatrix
              counterArguments={adversarialSimulation.results.counter_arguments}
              weaknesses={adversarialSimulation.results.weaknesses}
              overallStrength={adversarialSimulation.results.overall_strength}
              recommendations={adversarialSimulation.results.recommendations}
              caseType={adversarialSimulation.results.case_type || defenseAnalysis.case_type}
            />
          )}

          {/* Adversarial Progress - show during analysis */}
          {adversarialSimulation.status === 'running' && (
            <AdversarialProgress
              simulationId={adversarialSimulation.simulationId || undefined}
              isActive={true}
              progress={adversarialSimulation.progress}
              counterCount={adversarialSimulation.counterCount}
              status={adversarialSimulation.status}
              estimatedTimeRemaining={adversarialSimulation.estimatedTimeRemaining}
              onComplete={() => {
                // Results will be loaded by the finalize function
              }}
            />
          )}

          {/* Upgrade prompt for free users */}
          {adversarialSimulation.status === 'disabled' && (
            <Card className="p-6 bg-gray-50 border-gray-200">
              <div className="flex items-center gap-3">
                <Swords className="h-6 w-6 text-gray-400" />
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-800">Opposing Counsel Analysis</h3>
                  <p className="text-sm text-gray-600">
                    Upgrade to Basic or higher to see what arguments opposing counsel will make against your case.
                  </p>
                </div>
                <a
                  href="/settings?tab=subscription"
                  className="px-4 py-2 bg-teal-600 text-white text-sm font-medium rounded-lg hover:bg-teal-700"
                >
                  Upgrade
                </a>
              </div>
            </Card>
          )}

          {/* Suggested Follow-Up Questions */}
          {defenseAnalysis.suggested_questions && defenseAnalysis.suggested_questions.length > 0 && (
            <Card className="p-6 bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-300">
              <div className="flex items-center space-x-2 mb-3">
                <Lightbulb className="h-6 w-6 text-purple-600 animate-pulse" />
                <h3 className="text-lg font-bold text-purple-900">
                  Questions About Your Defense Strategy
                </h3>
              </div>
              <p className="text-sm text-purple-700 mb-4">
                Click any question below to learn more about implementing your defense strategies
              </p>
              <div className="grid grid-cols-1 gap-3">
                {defenseAnalysis.suggested_questions.map((question, index) => (
                  <button
                    key={`defense-question-${index}`}
                    onClick={async () => {
                      // Scroll to textarea input (where user will interact)
                      setTimeout(() => {
                        textareaRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        textareaRef.current?.focus();
                      }, 100);

                      // Add user question
                      const userMessage: Message = {
                        id: crypto.randomUUID(),
                        role: 'user',
                        content: question,
                        timestamp: new Date()
                      };
                      const updatedMessages = [...messages, userMessage];
                      onMessagesChange(updatedMessages);

                      // Show loading message
                      const loadingMessage: Message = {
                        id: crypto.randomUUID(),
                        role: 'ai',
                        content: 'Analyzing your defense strategy question...',
                        timestamp: new Date()
                      };
                      onMessagesChange([...updatedMessages, loadingMessage]);

                      try {
                        // Call Q&A API with defense context
                        const response = await fetch(`${API_CONFIG.BASE_URL}/api/v1/qa/ask`, {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            document_text: document.text,
                            document_analysis: document.analysis,
                            question: `${question}\n\nContext: This is a follow-up question about the defense strategy for "${document.fileName}". The defense analysis identified ${defenseAnalysis?.defenses.length || 0} defense strategies. Please provide detailed strategic guidance.`,
                            session_id: sessionId,
                            document_id: document.id
                          })
                        });

                        if (response.ok) {
                          const data = await response.json();
                          const aiMessage: Message = {
                            id: crypto.randomUUID(),
                            role: 'ai',
                            content: data.answer || 'I need more information to answer that question.',
                            timestamp: new Date()
                          };
                          // Replace loading message with actual response
                          onMessagesChange([...updatedMessages, aiMessage]);
                        } else {
                          throw new Error('Failed to get response');
                        }
                      } catch (error) {
                        console.error('Error getting AI response:', error);
                        const errorMessage: Message = {
                          id: crypto.randomUUID(),
                          role: 'ai',
                          content: 'I apologize, but I encountered an error. Please try asking your question again.',
                          timestamp: new Date()
                        };
                        onMessagesChange([...updatedMessages, errorMessage]);
                      }
                    }}
                    className="p-4 bg-white border-2 border-purple-200 rounded-lg hover:border-purple-500 hover:shadow-lg transition-all group cursor-pointer text-left w-full"
                  >
                    <div className="flex items-start space-x-3">
                      <HelpCircle className="h-5 w-5 text-purple-500 mt-0.5 flex-shrink-0 group-hover:text-purple-700" />
                      <span className="text-sm text-purple-900 font-medium group-hover:text-purple-950">
                        {question}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-purple-200">
                <p className="text-xs text-purple-700 italic">
                  💡 <strong>Tip:</strong> These questions are specifically generated based on your defense analysis
                  to help you understand next steps and implementation strategies.
                </p>
              </div>
            </Card>
          )}

          {/* Start Over Button */}
          <div className="flex justify-center">
            <button
              onClick={() => {
                onMessagesChange([]);
                onCollectedAnswersChange([]);
                onDefenseAnalysisChange(null);
                onConversationPhaseChange('intro');
                startConversation();
              }}
              className="px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 flex items-center gap-2"
            >
              <Shield className="w-5 h-5" />
              Start New Defense Interview
            </button>
          </div>
        </>
      )}
    </div>
  );
}
