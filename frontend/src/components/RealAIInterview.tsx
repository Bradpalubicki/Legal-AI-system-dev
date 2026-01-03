import React, { useState, useEffect, useRef } from 'react';

interface Message {
  type: 'agent' | 'user' | 'system';
  content: string;
  timestamp: Date;
}

interface RealAIInterviewProps {
  documentText: string;
  documentType: string;
}

export function RealAIInterview({ documentText, documentType }: RealAIInterviewProps) {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [messages, setMessages] = useState<Message[]>([]);
  const [phase, setPhase] = useState<'ready' | 'analyzing' | 'interviewing' | 'building' | 'complete'>('ready');
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [textAnswer, setTextAnswer] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [strategy, setStrategy] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    startAIInterview();
  }, []);

  const addMessage = (type: 'agent' | 'user' | 'system', content: string) => {
    setMessages(prev => [...prev, { type, content, timestamp: new Date() }]);
  };

  const startAIInterview = async () => {
    setPhase('analyzing');
    setIsProcessing(true);

    addMessage('system', '🤖 AI Agent starting...');
    addMessage('agent', "Hi! I'm your Real AI Legal Assistant powered by Claude. I'm analyzing your legal document now...");

    try {
      const response = await fetch('/api/ai-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'analyze_document',
          sessionId,
          data: { documentText }
        })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to analyze document');
      }

      setAnalysis(data.analysis);
      setCurrentQuestion(data.firstQuestion);
      setPhase('interviewing');

      addMessage('agent', `✅ I've analyzed your ${data.analysis.case_type} case. I can see the plaintiff is ${data.analysis.plaintiff} and they're claiming ${data.analysis.amount_claimed || 'unspecified damages'}.`);

      setTimeout(() => {
        addMessage('agent', `Now let me ask you some strategic questions to build the strongest defense. ${data.firstQuestion.why_important}`);
        addMessage('agent', data.firstQuestion.question);
      }, 1000);

    } catch (error: any) {
      console.error('Failed to start AI interview:', error);
      addMessage('system', `❌ Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const submitAnswer = async (answer: string) => {
    if (!currentQuestion) return;

    addMessage('user', answer);
    setIsProcessing(true);
    setCurrentQuestion(null);
    setTextAnswer('');

    try {
      const response = await fetch('/api/ai-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'submit_answer',
          sessionId,
          data: {
            question: currentQuestion.question,
            answer
          }
        })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to process answer');
      }

      // Show AI's feedback
      if (data.feedback) {
        setTimeout(() => {
          addMessage('agent', data.feedback);

          if (data.defenseOpportunity) {
            setTimeout(() => {
              addMessage('agent', `💡 Defense Opportunity: ${data.defenseOpportunity}`);
            }, 800);
          }
        }, 500);
      }

      // Check if complete or more questions
      if (data.complete) {
        setTimeout(() => {
          addMessage('agent', "Perfect! I have all the information I need. Let me build your comprehensive defense strategy now...");
          buildDefense();
        }, 1500);
      } else if (data.nextQuestion) {
        setCurrentQuestion(data.nextQuestion);
        setTimeout(() => {
          if (data.nextQuestion.why_important) {
            addMessage('agent', `📌 ${data.nextQuestion.why_important}`);
          }
          addMessage('agent', data.nextQuestion.question);
        }, 1200);
      }

    } catch (error: any) {
      console.error('Failed to process answer:', error);
      addMessage('system', `❌ Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const buildDefense = async () => {
    setPhase('building');
    setIsProcessing(true);

    try {
      const response = await fetch('/api/ai-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'build_defense',
          sessionId
        })
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || 'Failed to build defense');
      }

      setStrategy(data);
      setPhase('complete');

      addMessage('agent', `✅ Defense Strategy Complete! I've identified ${data.primary_defenses?.length || 0} strong defense${data.primary_defenses?.length !== 1 ? 's' : ''} for your case. Check below for the full analysis.`);

    } catch (error: any) {
      console.error('Failed to build defense:', error);
      addMessage('system', `❌ Error: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="real-ai-interview max-w-6xl mx-auto p-4">
      {/* Status Bar */}
      <div className="status-bar bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg shadow-lg p-4 mb-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${isProcessing ? 'bg-yellow-300 animate-pulse' : 'bg-green-300'}`} />
            <span className="font-bold">
              {phase === 'ready' && '🚀 Ready'}
              {phase === 'analyzing' && '🔍 AI Analyzing Document...'}
              {phase === 'interviewing' && '💬 AI Interview in Progress'}
              {phase === 'building' && '🛡️ AI Building Defense...'}
              {phase === 'complete' && '✅ Strategy Complete'}
            </span>
          </div>
          <div className="text-sm opacity-90">
            Powered by Claude AI
          </div>
        </div>
      </div>

      {/* Chat Container */}
      <div className="chat-container bg-white rounded-lg shadow-xl p-6 mb-4 min-h-[500px] max-h-[600px] overflow-y-auto">
        <div className="space-y-4">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.type === 'system' && (
                <div className="w-full text-center">
                  <span className="inline-block bg-gray-100 text-gray-600 text-sm px-4 py-2 rounded-full">
                    {msg.content}
                  </span>
                </div>
              )}

              {msg.type === 'agent' && (
                <div className="flex items-start gap-3 max-w-[80%]">
                  <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                    AI
                  </div>
                  <div className="flex-1">
                    <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 shadow-sm">
                      <p className="text-gray-800 whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                </div>
              )}

              {msg.type === 'user' && (
                <div className="flex items-start gap-3 max-w-[80%] justify-end">
                  <div className="bg-green-500 text-white rounded-lg p-4 shadow-sm">
                    <p>{msg.content}</p>
                  </div>
                  <div className="flex-shrink-0 w-10 h-10 bg-green-500 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                    U
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Options for current question */}
          {currentQuestion && currentQuestion.options && !isProcessing && (
            <div className="flex justify-start">
              <div className="flex items-start gap-3 max-w-[80%]">
                <div className="flex-shrink-0 w-10 h-10" /> {/* Spacer */}
                <div className="flex-1 grid grid-cols-1 gap-2">
                  {currentQuestion.options.map((option: string, index: number) => (
                    <button
                      key={index}
                      onClick={() => submitAnswer(option)}
                      className="text-left p-3 bg-white border-2 border-blue-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all shadow-sm hover:shadow-md"
                    >
                      {option}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Text input for open-ended questions */}
          {currentQuestion && !currentQuestion.options && !isProcessing && (
            <div className="flex justify-start">
              <div className="flex items-start gap-3 max-w-[80%] w-full">
                <div className="flex-shrink-0 w-10 h-10" /> {/* Spacer */}
                <div className="flex-1 flex gap-2">
                  <input
                    type="text"
                    value={textAnswer}
                    onChange={(e) => setTextAnswer(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && textAnswer.trim()) {
                        submitAnswer(textAnswer);
                      }
                    }}
                    placeholder="Type your answer..."
                    className="flex-1 px-4 py-3 border-2 border-blue-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <button
                    onClick={() => textAnswer.trim() && submitAnswer(textAnswer)}
                    disabled={!textAnswer.trim()}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Typing indicator */}
          {isProcessing && (
            <div className="flex justify-start">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold shadow-lg">
                  AI
                </div>
                <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4 shadow-sm">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                    <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                  </div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* AI-Generated Defense Strategy */}
      {strategy && strategy.primary_defenses && (
        <div className="defense-strategy mt-6">
          <h2 className="text-3xl font-bold text-gray-900 mb-6 flex items-center gap-3">
            <span className="text-4xl">🛡️</span>
            AI-Generated Defense Strategy
          </h2>

          {strategy.primary_defenses.map((defense: any, index: number) => (
            <div key={index} className="defense-card bg-white rounded-xl shadow-2xl border-2 border-gray-200 p-8 mb-6 hover:shadow-3xl transition-shadow">
              <div className="flex justify-between items-start mb-6">
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{defense.name}</h3>
                  <p className="text-gray-600 text-lg">{defense.description}</p>
                </div>
                <div className="text-right ml-6">
                  <div className="text-5xl font-bold text-green-600">{defense.strength}%</div>
                  {defense.strength_level && (
                    <div className={`text-sm font-bold px-4 py-2 rounded-full inline-block mt-2 ${
                      defense.strength_level === 'VERY STRONG' || defense.strength_level === 'STRONG' ? 'bg-green-100 text-green-800' :
                      defense.strength_level === 'MODERATE' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {defense.strength_level}
                    </div>
                  )}
                </div>
              </div>

              {defense.detailed_explanation && (
                <div className="mb-6 p-6 bg-blue-50 rounded-lg border-l-4 border-blue-500">
                  <h4 className="font-bold text-blue-900 mb-3">📋 Detailed Explanation</h4>
                  <div className="text-gray-800 whitespace-pre-wrap">{defense.detailed_explanation}</div>
                </div>
              )}

              {defense.how_to_assert && (
                <div className="mb-6 p-6 bg-green-50 rounded-lg border-l-4 border-green-500">
                  <h4 className="font-bold text-green-900 mb-3">⚖️ How to Assert This Defense</h4>
                  <div className="text-gray-800 whitespace-pre-wrap">{defense.how_to_assert}</div>
                </div>
              )}

              {defense.winning_scenarios && defense.winning_scenarios.length > 0 && (
                <div className="mb-6 p-6 bg-purple-50 rounded-lg border-l-4 border-purple-500">
                  <h4 className="font-bold text-purple-900 mb-3">✅ Winning Scenarios</h4>
                  <ul className="list-disc list-inside space-y-2 text-gray-800">
                    {defense.winning_scenarios.map((scenario: string, i: number) => (
                      <li key={i}>{scenario}</li>
                    ))}
                  </ul>
                </div>
              )}

              {defense.risks_to_avoid && defense.risks_to_avoid.length > 0 && (
                <div className="p-6 bg-red-50 rounded-lg border-l-4 border-red-500">
                  <h4 className="font-bold text-red-900 mb-3">⚠️ Risks to Avoid</h4>
                  <ul className="list-disc list-inside space-y-2 text-red-800">
                    {defense.risks_to_avoid.map((risk: string, i: number) => (
                      <li key={i}>{risk}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}

          {strategy.immediate_actions && strategy.immediate_actions.length > 0 && (
            <div className="actions-card bg-yellow-50 border-2 border-yellow-300 rounded-xl p-6 mb-6">
              <h3 className="text-xl font-bold text-yellow-900 mb-4">📋 Immediate Actions Required</h3>
              <div className="space-y-3">
                {strategy.immediate_actions.map((action: any, index: number) => (
                  <div key={index} className="flex items-start gap-4 p-4 bg-white rounded-lg">
                    <div className={`px-3 py-1 rounded-full text-xs font-bold ${
                      action.priority === 'CRITICAL' ? 'bg-red-100 text-red-800' :
                      action.priority === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {action.priority}
                    </div>
                    <div className="flex-1">
                      <div className="font-bold text-gray-900">{action.action}</div>
                      <div className="text-sm text-gray-600 mt-1">{action.details}</div>
                      {action.deadline && (
                        <div className="text-sm text-red-600 font-medium mt-1">Deadline: {action.deadline}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
