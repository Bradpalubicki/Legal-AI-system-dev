import React, { useState, useEffect } from 'react';

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
  requirements?: string[];
  how_to_assert?: string;
}

interface Action {
  action: string;
  deadline: string;
  priority: string;
  details: string;
  how_to?: string;
}

interface DefenseStrategy {
  primary_defenses: Defense[];
  secondary_defenses: Defense[];
  immediate_actions: Action[];
  evidence_needed: string[];
  negotiation_leverage?: string;
  estimated_success_rate: string;
}

interface AgentState {
  phase: 'analyzing' | 'interviewing' | 'building' | 'complete';
  currentQuestion: Question | null;
  questionNumber: number;
  totalQuestions: number;
  answers: Array<{ question: string; answer: string; insight?: string }>;
  insights: string[];
  defenseStrategy: DefenseStrategy | null;
  confidenceScore: number;
}

interface IntelligentLegalAgentProps {
  document?: {
    text: string;
    type: string;
  };
}

export function IntelligentLegalAgent({ document }: IntelligentLegalAgentProps) {
  const [agentState, setAgentState] = useState<AgentState>({
    phase: 'analyzing',
    currentQuestion: null,
    questionNumber: 0,
    totalQuestions: 0,
    answers: [],
    insights: [],
    defenseStrategy: null,
    confidenceScore: 0
  });

  const [sessionId] = useState(() => crypto.randomUUID());
  const [isThinking, setIsThinking] = useState(false);
  const [textAnswer, setTextAnswer] = useState('');

  // Start intelligent interview
  useEffect(() => {
    if (document) {
      startIntelligentInterview();
    }
  }, [document]);

  const startIntelligentInterview = async () => {
    setIsThinking(true);
    setAgentState(prev => ({ ...prev, phase: 'analyzing' }));

    try {
      const response = await fetch('/api/agent/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          documentText: document?.text,
          documentType: document?.type
        })
      });

      const data = await response.json();

      // Agent has analyzed and prepared first question
      setAgentState({
        phase: 'interviewing',
        currentQuestion: data.firstQuestion,
        questionNumber: 1,
        totalQuestions: data.estimatedQuestions || 10,
        answers: [],
        insights: data.initialInsights || [],
        defenseStrategy: null,
        confidenceScore: data.confidence || 0
      });
    } catch (error) {
      console.error('Failed to start interview:', error);
    } finally {
      setIsThinking(false);
    }
  };

  const handleAnswer = async (answer: string) => {
    setIsThinking(true);

    try {
      // Send answer to agent
      const response = await fetch('/api/agent/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          questionId: agentState.currentQuestion?.id,
          answer
        })
      });

      const data = await response.json();

      // Update state with agent's response
      setAgentState(prev => ({
        ...prev,
        answers: [...prev.answers, {
          question: prev.currentQuestion?.question || '',
          answer,
          insight: data.insight,
          feedback: data.feedback  // Add feedback to answers
        }],
        insights: [...prev.insights, ...(data.newInsights || [])],
        confidenceScore: data.confidenceScore || prev.confidenceScore
      }));

      // Check if agent has follow-up or next question
      if (data.followUpQuestion) {
        // Agent wants to dig deeper
        setAgentState(prev => ({
          ...prev,
          currentQuestion: data.followUpQuestion,
          questionNumber: prev.questionNumber + 1
        }));
      } else if (data.nextQuestion) {
        // Move to next strategic question
        setAgentState(prev => ({
          ...prev,
          currentQuestion: data.nextQuestion,
          questionNumber: prev.questionNumber + 1
        }));
      } else {
        // Interview complete, ready to build defense
        setAgentState(prev => ({
          ...prev,
          phase: 'building',
          currentQuestion: null
        }));

        // Auto-trigger defense building
        setTimeout(() => buildDetailedDefense(), 1000);
      }
    } catch (error) {
      console.error('Failed to process answer:', error);
    } finally {
      setIsThinking(false);
      setTextAnswer('');
    }
  };

  const buildDetailedDefense = async () => {
    setIsThinking(true);
    setAgentState(prev => ({ ...prev, phase: 'building' }));

    try {
      const response = await fetch('/api/agent/build-defense', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId })
      });

      const strategy = await response.json();

      setAgentState(prev => ({
        ...prev,
        phase: 'complete',
        defenseStrategy: strategy
      }));
    } catch (error) {
      console.error('Failed to build defense:', error);
    } finally {
      setIsThinking(false);
    }
  };

  return (
    <div className='intelligent-legal-agent max-w-6xl mx-auto p-6'>
      {/* Agent Status Bar */}
      <div className='agent-status bg-white rounded-lg shadow-md p-6 mb-6'>
        <div className='status-header flex justify-between items-center mb-4'>
          <h2 className='text-2xl font-bold text-gray-900'>🤖 Legal Defense AI Agent</h2>
          <div className='confidence-meter flex items-center gap-3'>
            <span className='text-sm font-medium text-gray-700'>Confidence:</span>
            <div className='w-32 h-2 bg-gray-200 rounded-full overflow-hidden'>
              <div
                className='h-full bg-blue-600 transition-all duration-500'
                style={{ width: `${agentState.confidenceScore}%` }}
              />
            </div>
            <span className='text-sm font-bold text-blue-600'>{agentState.confidenceScore}%</span>
          </div>
        </div>

        <div className='phase-indicator flex gap-4'>
          <div className={`phase-step flex-1 p-3 rounded-lg text-center ${agentState.phase === 'analyzing' ? 'bg-blue-100 text-blue-700 font-semibold' : 'bg-gray-100 text-gray-500'}`}>
            📄 Analyzing
          </div>
          <div className={`phase-step flex-1 p-3 rounded-lg text-center ${agentState.phase === 'interviewing' ? 'bg-blue-100 text-blue-700 font-semibold' : 'bg-gray-100 text-gray-500'}`}>
            💬 Interviewing
          </div>
          <div className={`phase-step flex-1 p-3 rounded-lg text-center ${agentState.phase === 'building' ? 'bg-blue-100 text-blue-700 font-semibold' : 'bg-gray-100 text-gray-500'}`}>
            🔨 Building Defense
          </div>
          <div className={`phase-step flex-1 p-3 rounded-lg text-center ${agentState.phase === 'complete' ? 'bg-green-100 text-green-700 font-semibold' : 'bg-gray-100 text-gray-500'}`}>
            ✅ Complete
          </div>
        </div>
      </div>

      {/* Insights Panel */}
      {agentState.insights.length > 0 && (
        <div className='insights-panel bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6'>
          <h3 className='text-lg font-bold text-yellow-900 mb-3'>🔍 Agent Insights</h3>
          <ul className='space-y-2'>
            {agentState.insights.map((insight, i) => (
              <li key={i} className='insight-item text-yellow-800'>
                💡 {insight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Interview Section */}
      {agentState.phase === 'interviewing' && agentState.currentQuestion && (
        <div className='interview-card bg-white rounded-lg shadow-md p-6 mb-6'>
          <div className='question-header flex justify-between items-center mb-4'>
            <span className='question-number text-sm font-medium text-gray-600'>
              Question {agentState.questionNumber} of ~{agentState.totalQuestions}
            </span>
            <div className='flex gap-2'>
              {agentState.currentQuestion.type === 'follow_up' && (
                <span className='follow-up-badge px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold'>
                  Follow-up
                </span>
              )}
              {agentState.currentQuestion.importance === 'CRITICAL' && (
                <span className='critical-badge px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-semibold'>
                  ⚠️ Critical
                </span>
              )}
            </div>
          </div>

          <h3 className='question-text text-xl font-semibold text-gray-900 mb-3'>
            {agentState.currentQuestion.question}
          </h3>

          {agentState.currentQuestion.reason && (
            <p className='question-reason text-sm text-gray-600 mb-4 p-3 bg-blue-50 rounded-lg'>
              <strong>Why this matters:</strong> {agentState.currentQuestion.reason}
            </p>
          )}

          {agentState.currentQuestion.options ? (
            <div className='answer-options grid grid-cols-1 md:grid-cols-2 gap-3'>
              {agentState.currentQuestion.options.map(option => (
                <button
                  key={option}
                  onClick={() => handleAnswer(option)}
                  disabled={isThinking}
                  className='option-button p-4 text-left border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
                >
                  {option}
                </button>
              ))}
            </div>
          ) : (
            <div className='flex gap-2'>
              <input
                type='text'
                value={textAnswer}
                onChange={(e) => setTextAnswer(e.target.value)}
                placeholder='Type your answer...'
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && textAnswer) {
                    handleAnswer(textAnswer);
                  }
                }}
                disabled={isThinking}
                className='flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
              />
              <button
                onClick={() => textAnswer && handleAnswer(textAnswer)}
                disabled={isThinking || !textAnswer}
                className='px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed'
              >
                Submit
              </button>
            </div>
          )}
        </div>
      )}

      {/* Previous Answers with Feedback */}
      {agentState.answers.length > 0 && (
        <div className='previous-answers mb-6'>
          <h3 className='text-lg font-bold text-gray-900 mb-3'>📝 Your Responses</h3>
          <div className='space-y-3'>
            {agentState.answers.map((item, index) => (
              <div key={index} className='answer-card bg-gray-50 rounded-lg p-4 border border-gray-200'>
                <div className='flex items-start gap-3'>
                  <div className='flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center font-bold text-sm'>
                    {index + 1}
                  </div>
                  <div className='flex-1'>
                    <p className='text-sm text-gray-600 mb-1'>{item.question}</p>
                    <p className='font-semibold text-gray-900 mb-2'>→ {item.answer}</p>
                    {item.feedback && (
                      <div className='feedback-box mt-2 p-3 bg-white border-l-4 border-blue-500 rounded'>
                        <p className='text-sm text-gray-700'>{item.feedback}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Building Defense */}
      {agentState.phase === 'building' && (
        <div className='building-card bg-white rounded-lg shadow-md p-8 text-center'>
          <div className='building-animation'>
            <h3 className='text-2xl font-bold text-gray-900 mb-3'>🔨 Building Your Comprehensive Defense Strategy...</h3>
            <p className='text-gray-600 mb-4'>Analyzing {agentState.answers.length} answers and document details...</p>
            <div className='spinner inline-block w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin' />
          </div>
        </div>
      )}

      {/* Detailed Defense Strategy */}
      {agentState.defenseStrategy && (
        <div className='defense-strategy space-y-6'>
          <div className='strategy-overview bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6'>
            <h2 className='text-2xl font-bold text-gray-900 mb-3'>⚖️ Your Comprehensive Defense Strategy</h2>
            <div className='success-rate'>
              <strong className='text-gray-700'>Estimated Success Rate:</strong>
              <span className='rate ml-2 text-2xl font-bold text-blue-600'>{agentState.defenseStrategy.estimated_success_rate}</span>
            </div>
          </div>

          {/* Primary Defenses */}
          <div className='primary-defenses'>
            <h3 className='text-xl font-bold text-gray-900 mb-4'>🛡️ Primary Defense Strategies</h3>
            {agentState.defenseStrategy.primary_defenses.map((defense, i) => (
              <div key={i} className='defense-detail bg-white rounded-lg shadow-lg border-2 border-gray-200 p-6 mb-6'>
                <div className='defense-header flex justify-between items-start mb-4'>
                  <div className='flex-1'>
                    <h4 className='text-xl font-bold text-gray-900 mb-2'>{i + 1}. {defense.name}</h4>
                    {defense.strength_level && (
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                        defense.strength_level === 'VERY STRONG' ? 'bg-green-100 text-green-800' :
                        defense.strength_level === 'STRONG' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {defense.strength_level}
                      </span>
                    )}
                  </div>
                  <span className={`strength-badge px-4 py-2 rounded-lg text-lg font-bold ${
                    defense.strength >= 90 ? 'bg-green-500 text-white' :
                    defense.strength >= 70 ? 'bg-blue-500 text-white' :
                    'bg-yellow-500 text-white'
                  }`}>
                    {defense.strength}%
                  </span>
                </div>

                <p className='defense-description text-lg text-gray-700 mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded'>
                  {defense.description}
                </p>

                {defense.detailed_explanation && (
                  <details className='mb-6' open>
                    <summary className='cursor-pointer text-lg font-bold text-blue-700 hover:text-blue-800 mb-3'>
                      📋 Complete Defense Analysis
                    </summary>
                    <div className='detailed-explanation mt-3 p-5 bg-gradient-to-br from-gray-50 to-blue-50 rounded-lg border border-gray-200'>
                      <div className='prose prose-sm max-w-none text-gray-700 markdown-content'>
                        {defense.detailed_explanation.split('\n').map((line, idx) => {
                          if (line.startsWith('##')) {
                            return <h3 key={idx} className='text-xl font-bold text-gray-900 mt-4 mb-2'>{line.replace('##', '')}</h3>;
                          } else if (line.startsWith('###')) {
                            return <h4 key={idx} className='text-lg font-semibold text-gray-800 mt-3 mb-2'>{line.replace('###', '')}</h4>;
                          } else if (line.startsWith('**') && line.endsWith('**')) {
                            return <p key={idx} className='font-bold text-gray-900 mt-2'>{line.replace(/\*\*/g, '')}</p>;
                          } else if (line.startsWith('- ')) {
                            return <li key={idx} className='ml-4 text-gray-700'>{line.substring(2)}</li>;
                          } else if (line.trim()) {
                            return <p key={idx} className='text-gray-700 mt-2'>{line}</p>;
                          }
                          return <br key={idx} />;
                        })}
                      </div>
                    </div>
                  </details>
                )}

                {defense.requirements && defense.requirements.length > 0 && (
                  <div className='requirements mb-6 p-4 bg-purple-50 border border-purple-200 rounded-lg'>
                    <strong className='text-lg text-purple-900 block mb-3'>📝 What You Need:</strong>
                    <ul className='space-y-2'>
                      {defense.requirements.map((req, j) => (
                        <li key={j} className='flex items-start gap-2 text-gray-700'>
                          <span className='text-purple-600 mt-1'>✓</span>
                          <span>{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {defense.how_to_assert && (
                  <details className='mb-4'>
                    <summary className='cursor-pointer text-lg font-bold text-green-700 hover:text-green-800 mb-2'>
                      ⚖️ How to Assert This Defense
                    </summary>
                    <div className='how-to-assert mt-3 p-5 bg-green-50 border border-green-200 rounded-lg'>
                      <pre className='whitespace-pre-wrap font-mono text-sm text-green-900'>{defense.how_to_assert}</pre>
                    </div>
                  </details>
                )}

                {defense.winning_scenarios && defense.winning_scenarios.length > 0 && (
                  <details className='mb-4'>
                    <summary className='cursor-pointer text-lg font-bold text-blue-700 hover:text-blue-800'>
                      ✅ Winning Scenarios
                    </summary>
                    <div className='mt-3 p-4 bg-blue-50 border border-blue-200 rounded-lg'>
                      <ul className='space-y-2'>
                        {defense.winning_scenarios.map((scenario, j) => (
                          <li key={j} className='flex items-start gap-2 text-gray-700'>
                            <span className='text-green-600 mt-1'>🎯</span>
                            <span>{scenario}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </details>
                )}

                {defense.risks_to_avoid && defense.risks_to_avoid.length > 0 && (
                  <details className='mb-4'>
                    <summary className='cursor-pointer text-lg font-bold text-red-700 hover:text-red-800'>
                      ⚠️ Risks to Avoid
                    </summary>
                    <div className='mt-3 p-4 bg-red-50 border border-red-200 rounded-lg'>
                      <ul className='space-y-2'>
                        {defense.risks_to_avoid.map((risk, j) => (
                          <li key={j} className='flex items-start gap-2 text-gray-700'>
                            <span className='text-red-600 mt-1'>⚠</span>
                            <span>{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </details>
                )}

                {defense.case_law_support && defense.case_law_support.length > 0 && (
                  <details>
                    <summary className='cursor-pointer text-lg font-bold text-gray-700 hover:text-gray-800'>
                      📚 Legal Support
                    </summary>
                    <div className='mt-3 p-4 bg-gray-100 border border-gray-300 rounded-lg'>
                      <ul className='space-y-2'>
                        {defense.case_law_support.map((law, j) => (
                          <li key={j} className='flex items-start gap-2 text-gray-700'>
                            <span className='text-gray-600 mt-1'>⚖️</span>
                            <span className='italic'>{law}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </details>
                )}
              </div>
            ))}
          </div>

          {/* Secondary Defenses */}
          {agentState.defenseStrategy.secondary_defenses.length > 0 && (
            <div className='secondary-defenses'>
              <h3 className='text-xl font-bold text-gray-900 mb-4'>🔰 Additional Defense Options</h3>
              <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
                {agentState.defenseStrategy.secondary_defenses.map((defense, i) => (
                  <div key={i} className='defense-summary bg-white border border-gray-200 rounded-lg p-4'>
                    <h4 className='font-bold text-gray-900 mb-2'>{defense.name}</h4>
                    <p className='text-sm text-gray-700'>{defense.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Plan */}
          <div className='action-plan bg-white rounded-lg shadow-md p-6'>
            <h3 className='text-xl font-bold text-gray-900 mb-4'>📋 Immediate Action Plan</h3>
            {agentState.defenseStrategy.immediate_actions.map((action, i) => (
              <div key={i} className='action-item mb-4 pb-4 border-b last:border-b-0'>
                <div className='action-header flex justify-between items-start mb-2'>
                  <strong className='text-lg text-gray-900'>{action.action}</strong>
                  <span className={`priority px-3 py-1 rounded-full text-xs font-semibold ${
                    action.priority === 'CRITICAL' ? 'bg-red-100 text-red-700' :
                    action.priority === 'HIGH' ? 'bg-orange-100 text-orange-700' :
                    'bg-yellow-100 text-yellow-700'
                  }`}>
                    {action.priority}
                  </span>
                </div>
                <p className='text-sm text-gray-600 mb-1'><strong>Deadline:</strong> {action.deadline}</p>
                <p className='text-gray-700 mb-2'>{action.details}</p>
                {action.how_to && (
                  <details>
                    <summary className='cursor-pointer font-semibold text-blue-600 hover:text-blue-700 text-sm'>
                      Step-by-Step Instructions
                    </summary>
                    <pre className='mt-2 p-3 bg-gray-50 rounded-lg text-xs text-gray-700 whitespace-pre-wrap'>
                      {action.how_to}
                    </pre>
                  </details>
                )}
              </div>
            ))}
          </div>

          {/* Evidence Needed */}
          <div className='evidence-needed bg-white rounded-lg shadow-md p-6'>
            <h3 className='text-xl font-bold text-gray-900 mb-4'>📁 Evidence to Gather</h3>
            <ul className='space-y-2'>
              {agentState.defenseStrategy.evidence_needed.map((item, i) => (
                <li key={i} className='flex items-start gap-2'>
                  <span className='text-blue-600 mt-1'>▸</span>
                  <span className='text-gray-700'>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Negotiation Position */}
          {agentState.defenseStrategy.negotiation_leverage && (
            <div className='negotiation bg-green-50 border border-green-200 rounded-lg p-6'>
              <h3 className='text-xl font-bold text-green-900 mb-3'>💰 Settlement Negotiation Position</h3>
              <p className='text-green-800'>{agentState.defenseStrategy.negotiation_leverage}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
