import React, { useState, useEffect, useRef } from 'react';

interface Message {
  type: 'agent' | 'user';
  content: string;
  feedback?: string;
  questionId?: string;
  options?: string[];
}

interface Question {
  id: string;
  question: string;
  options?: string[];
  type?: string;
  importance?: string;
  reason?: string;
}

interface Defense {
  name: string;
  strength: number;
  description: string;
  detailed_explanation?: string;
  strength_level?: string;
  requirements?: string[];
  how_to_assert?: string;
  winning_scenarios?: string[];
  risks_to_avoid?: string[];
}

interface DefenseStrategy {
  primary_defenses: Defense[];
  secondary_defenses: Defense[];
  immediate_actions: any[];
  evidence_needed: string[];
  estimated_success_rate: string;
}

interface ConversationalAgentProps {
  documentText: string;
  documentType: string;
}

export function ConversationalAgent({ documentText, documentType }: ConversationalAgentProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [sessionId] = useState(() => crypto.randomUUID());
  const [isThinking, setIsThinking] = useState(false);
  const [phase, setPhase] = useState<'analyzing' | 'interviewing' | 'building' | 'complete'>('analyzing');
  const [defenseStrategy, setDefenseStrategy] = useState<DefenseStrategy | null>(null);
  const [confidence, setConfidence] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    startConversation();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startConversation = async () => {
    setIsThinking(true);
    setPhase('analyzing');

    // Initial greeting
    setMessages([
      {
        type: 'agent',
        content: "👋 Hi! I'm your Legal Defense AI. I've analyzed your document and I'm here to help build your defense strategy. Let me ask you a few important questions to understand your situation better."
      }
    ]);

    try {
      const response = await fetch('/api/agent/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          documentText,
          documentType
        })
      });

      const data = await response.json();

      setCurrentQuestion(data.firstQuestion);
      setPhase('interviewing');
      setConfidence(data.confidence || 0);

      // Add first question as agent message
      setMessages(prev => [...prev, {
        type: 'agent',
        content: data.firstQuestion.question,
        questionId: data.firstQuestion.id,
        options: data.firstQuestion.options
      }]);
    } catch (error) {
      console.error('Failed to start conversation:', error);
      setMessages(prev => [...prev, {
        type: 'agent',
        content: "I encountered an error starting our conversation. Please try refreshing the page."
      }]);
    } finally {
      setIsThinking(false);
    }
  };

  const handleAnswer = async (answer: string) => {
    if (!currentQuestion) return;

    // Add user's answer to messages
    setMessages(prev => [...prev, {
      type: 'user',
      content: answer
    }]);

    setIsThinking(true);

    try {
      const response = await fetch('/api/agent/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          questionId: currentQuestion.id,
          answer
        })
      });

      const data = await response.json();

      // Add feedback if available
      if (data.feedback) {
        setMessages(prev => [...prev, {
          type: 'agent',
          content: data.feedback
        }]);
      }

      setConfidence(data.confidenceScore || confidence);

      // Check for next question
      if (data.nextQuestion) {
        setCurrentQuestion(data.nextQuestion);

        // Add next question as agent message
        setTimeout(() => {
          setMessages(prev => [...prev, {
            type: 'agent',
            content: data.nextQuestion.question,
            questionId: data.nextQuestion.id,
            options: data.nextQuestion.options
          }]);
        }, 500);
      } else if (data.complete) {
        // Interview complete
        setCurrentQuestion(null);
        setPhase('building');

        setMessages(prev => [...prev, {
          type: 'agent',
          content: "🎯 Perfect! I have all the information I need. Let me build your personalized defense strategy now..."
        }]);

        // Build defense
        setTimeout(() => buildDefense(), 1000);
      }
    } catch (error) {
      console.error('Failed to process answer:', error);
    } finally {
      setIsThinking(false);
    }
  };

  const buildDefense = async () => {
    setIsThinking(true);
    setPhase('building');

    try {
      const response = await fetch('/api/agent/build-defense', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId })
      });

      const strategy = await response.json();

      setDefenseStrategy(strategy);
      setPhase('complete');
      setConfidence(95);

      // Add completion message
      setMessages(prev => [...prev, {
        type: 'agent',
        content: `✅ Defense strategy complete! I've identified **${strategy.primary_defenses.length} strong defense${strategy.primary_defenses.length > 1 ? 's' : ''}** for your case. Scroll down to see the full analysis.`
      }]);
    } catch (error) {
      console.error('Failed to build defense:', error);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className='conversational-agent max-w-5xl mx-auto p-4'>
      {/* Status Bar */}
      <div className='status-bar bg-white rounded-lg shadow-md p-4 mb-4 flex justify-between items-center'>
        <div className='flex items-center gap-4'>
          <div className='flex gap-2'>
            <div className={`status-dot w-3 h-3 rounded-full ${phase === 'analyzing' ? 'bg-blue-500 animate-pulse' : phase === 'interviewing' ? 'bg-green-500' : phase === 'building' ? 'bg-yellow-500 animate-pulse' : 'bg-purple-500'}`} />
            <span className='text-sm font-medium text-gray-700'>
              {phase === 'analyzing' && '📄 Analyzing...'}
              {phase === 'interviewing' && '💬 Interviewing'}
              {phase === 'building' && '🔨 Building Defense...'}
              {phase === 'complete' && '✅ Complete'}
            </span>
          </div>
        </div>

        <div className='flex items-center gap-3'>
          <span className='text-sm text-gray-600'>Confidence:</span>
          <div className='w-32 h-2 bg-gray-200 rounded-full overflow-hidden'>
            <div
              className='h-full bg-gradient-to-r from-blue-500 to-green-500 transition-all duration-500'
              style={{ width: `${confidence}%` }}
            />
          </div>
          <span className='text-sm font-bold text-blue-600'>{confidence}%</span>
        </div>
      </div>

      {/* Chat Messages */}
      <div className='chat-container bg-white rounded-lg shadow-md p-6 mb-4 h-[500px] overflow-y-auto'>
        <div className='space-y-4'>
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`max-w-[80%] ${msg.type === 'user' ? 'order-2' : 'order-1'}`}>
                {msg.type === 'agent' && (
                  <div className='flex items-start gap-2 mb-1'>
                    <div className='w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold'>
                      AI
                    </div>
                    <div className='flex-1'>
                      <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
                        <p className='text-gray-800 whitespace-pre-wrap'>{msg.content}</p>
                      </div>

                      {/* Options for current question */}
                      {msg.options && msg.questionId === currentQuestion?.id && !isThinking && (
                        <div className='mt-3 grid grid-cols-1 gap-2'>
                          {msg.options.map(option => (
                            <button
                              key={option}
                              onClick={() => handleAnswer(option)}
                              className='text-left p-3 bg-white border-2 border-blue-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all'
                            >
                              {option}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {msg.type === 'user' && (
                  <div className='flex items-start gap-2 mb-1 justify-end'>
                    <div className='bg-green-500 text-white rounded-lg p-4'>
                      <p>{msg.content}</p>
                    </div>
                    <div className='w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white font-bold'>
                      U
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {isThinking && (
            <div className='flex justify-start'>
              <div className='flex items-start gap-2'>
                <div className='w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold'>
                  AI
                </div>
                <div className='bg-blue-50 border border-blue-200 rounded-lg p-4'>
                  <div className='flex gap-2'>
                    <div className='w-2 h-2 bg-blue-500 rounded-full animate-bounce' />
                    <div className='w-2 h-2 bg-blue-500 rounded-full animate-bounce' style={{ animationDelay: '0.1s' }} />
                    <div className='w-2 h-2 bg-blue-500 rounded-full animate-bounce' style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Defense Strategy Display */}
      {defenseStrategy && (
        <div className='defense-strategy mt-6'>
          <h2 className='text-2xl font-bold text-gray-900 mb-4'>🛡️ Your Defense Strategy</h2>

          {defenseStrategy.primary_defenses.map((defense, index) => (
            <div key={index} className='defense-card bg-white rounded-lg shadow-lg border-2 border-gray-200 p-6 mb-6'>
              <div className='flex justify-between items-start mb-4'>
                <div>
                  <h3 className='text-xl font-bold text-gray-900'>{defense.name}</h3>
                  <p className='text-gray-600 mt-1'>{defense.description}</p>
                </div>
                <div className='text-right'>
                  <div className='text-3xl font-bold text-green-600'>{defense.strength}%</div>
                  {defense.strength_level && (
                    <div className={`text-sm font-semibold px-3 py-1 rounded-full inline-block mt-1 ${
                      defense.strength_level === 'VERY STRONG' ? 'bg-green-100 text-green-800' :
                      defense.strength_level === 'STRONG' ? 'bg-blue-100 text-blue-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {defense.strength_level}
                    </div>
                  )}
                </div>
              </div>

              {defense.detailed_explanation && (
                <div className='mt-4 prose prose-sm max-w-none'>
                  <div className='bg-blue-50 p-4 rounded-lg border border-blue-200'>
                    {defense.detailed_explanation.split('\n').map((line, i) => (
                      <p key={i} className='mb-2'>{line}</p>
                    ))}
                  </div>
                </div>
              )}

              {defense.winning_scenarios && defense.winning_scenarios.length > 0 && (
                <div className='mt-4'>
                  <h4 className='font-semibold text-gray-900 mb-2'>✅ Winning Scenarios:</h4>
                  <ul className='list-disc list-inside space-y-1 text-gray-700'>
                    {defense.winning_scenarios.map((scenario, i) => (
                      <li key={i}>{scenario}</li>
                    ))}
                  </ul>
                </div>
              )}

              {defense.risks_to_avoid && defense.risks_to_avoid.length > 0 && (
                <div className='mt-4'>
                  <h4 className='font-semibold text-red-900 mb-2'>⚠️ Risks to Avoid:</h4>
                  <ul className='list-disc list-inside space-y-1 text-red-700'>
                    {defense.risks_to_avoid.map((risk, i) => (
                      <li key={i}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
