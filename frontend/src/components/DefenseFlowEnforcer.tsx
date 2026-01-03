/**
 * Defense Flow Enforcer
 * ENFORCES interview completion before defense building
 * Shows clear stage progression and blocks defense until ready
 */

import React, { useState } from 'react';

import { API_CONFIG } from '../config/api';
interface FlowState {
  stage: 'upload' | 'interview' | 'ready_for_defense' | 'defense_built';
  currentQuestion: any;
  questionNumber: number;
  totalQuestions: number;
  answers: string[];
  defenses: any[];
  canBuildDefense: boolean;
  loading: boolean;
  error: string | null;
}

interface QAMessage {
  type: 'question' | 'answer';
  text: string;
}

export function DefenseFlowEnforcer() {
  const [flowState, setFlowState] = useState<FlowState>({
    stage: 'upload',
    currentQuestion: null,
    questionNumber: 0,
    totalQuestions: 0,
    answers: [],
    defenses: [],
    canBuildDefense: false,
    loading: false,
    error: null
  });

  const [sessionId] = useState(() => `session_${Date.now()}_${Math.random().toString(36).substring(7)}`);
  const [qaMessage, setQaMessage] = useState('');
  const [qaResponses, setQaResponses] = useState<QAMessage[]>([]);

  // Start defense flow with document
  const handleDocumentUpload = async (file: File) => {
    setFlowState({ ...flowState, loading: true, error: null });

    try {
      const text = await file.text();

      const response = await fetch(`${API_CONFIG.BASE_URL}/api/defense-flow/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          documentText: text
        })
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const data = await response.json();

      // FORCE move to interview stage
      setFlowState({
        ...flowState,
        stage: 'interview',
        currentQuestion: data.current_question,
        questionNumber: data.question_number,
        totalQuestions: data.total_questions,
        canBuildDefense: false,  // BLOCKED
        loading: false,
        error: null
      });
    } catch (error) {
      setFlowState({
        ...flowState,
        loading: false,
        error: error instanceof Error ? error.message : 'Upload failed'
      });
    }
  };

  // Handle interview answer
  const handleAnswer = async (answer: string) => {
    setFlowState({ ...flowState, loading: true, error: null });

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/defense-flow/answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          answer
        })
      });

      if (!response.ok) {
        throw new Error(`Answer failed: ${response.status}`);
      }

      const data = await response.json();

      if (data.action === 'INTERVIEW_COMPLETE') {
        // Interview done - can now build defense
        setFlowState({
          ...flowState,
          stage: 'ready_for_defense',
          canBuildDefense: true,
          currentQuestion: null,
          answers: [...flowState.answers, answer],
          loading: false
        });
      } else {
        // Next question
        setFlowState({
          ...flowState,
          currentQuestion: data.current_question,
          questionNumber: data.question_number,
          answers: [...flowState.answers, answer],
          loading: false
        });
      }
    } catch (error) {
      setFlowState({
        ...flowState,
        loading: false,
        error: error instanceof Error ? error.message : 'Answer failed'
      });
    }
  };

  // Build defense (ONLY after interview)
  const buildDefense = async () => {
    if (!flowState.canBuildDefense) {
      alert('⚠️ Please complete the interview first!');
      return;
    }

    setFlowState({ ...flowState, loading: true, error: null });

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/defense-flow/build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || 'Defense building blocked');
      }

      const data = await response.json();

      setFlowState({
        ...flowState,
        stage: 'defense_built',
        defenses: data.defenses,
        loading: false
      });
    } catch (error) {
      setFlowState({
        ...flowState,
        loading: false,
        error: error instanceof Error ? error.message : 'Defense building failed'
      });
    }
  };

  // Q&A handler (separate from interview)
  const handleQA = async () => {
    if (!qaMessage.trim()) return;

    const userMessage = qaMessage;
    setQaMessage('');

    // Optimistically add user message
    setQaResponses([
      ...qaResponses,
      { type: 'question', text: userMessage }
    ]);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/defense-flow/qa/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          sessionId
        })
      });

      const data = await response.json();

      setQaResponses([
        ...qaResponses,
        { type: 'question', text: userMessage },
        { type: 'answer', text: data.response }
      ]);
    } catch (error) {
      setQaResponses([
        ...qaResponses,
        { type: 'question', text: userMessage },
        { type: 'answer', text: 'Error: Could not get response' }
      ]);
    }
  };

  return (
    <div className="defense-flow-enforcer max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold text-center mb-8">Legal Defense Builder</h1>

      {/* Stage indicator */}
      <div className="stage-indicator flex justify-between mb-8">
        <div className={`flex-1 text-center p-3 rounded ${flowState.stage === 'upload' ? 'bg-blue-500 text-white font-bold' : 'bg-gray-200'}`}>
          1. Upload Document
        </div>
        <div className={`flex-1 text-center p-3 rounded mx-2 ${flowState.stage === 'interview' ? 'bg-blue-500 text-white font-bold' : 'bg-gray-200'}`}>
          2. Answer Questions ({flowState.questionNumber}/{flowState.totalQuestions})
        </div>
        <div className={`flex-1 text-center p-3 rounded mx-2 ${flowState.stage === 'ready_for_defense' ? 'bg-blue-500 text-white font-bold' : 'bg-gray-200'}`}>
          3. Build Defense
        </div>
        <div className={`flex-1 text-center p-3 rounded ${flowState.stage === 'defense_built' ? 'bg-blue-500 text-white font-bold' : 'bg-gray-200'}`}>
          4. View Strategy
        </div>
      </div>

      {/* Error display */}
      {flowState.error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {flowState.error}
        </div>
      )}

      {/* Upload stage */}
      {flowState.stage === 'upload' && (
        <div className="upload-section bg-white p-8 rounded-lg shadow-lg">
          <h2 className="text-2xl font-semibold mb-4">Upload Your Legal Document</h2>
          <p className="text-gray-600 mb-6">Upload a summons, complaint, or legal notice to get started.</p>

          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              type="file"
              multiple
              onChange={(e) => e.target.files?.[0] && handleDocumentUpload(e.target.files[0])}
              accept=".txt,.pdf,.doc,.docx"
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="cursor-pointer inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              {flowState.loading ? 'Analyzing...' : 'Choose File'}
            </label>
            <p className="mt-2 text-sm text-gray-500">
              Supported: .txt, .pdf, .doc, .docx
            </p>
          </div>
        </div>
      )}

      {/* Interview stage - FORCED */}
      {flowState.stage === 'interview' && flowState.currentQuestion && (
        <div className="interview-section bg-white p-8 rounded-lg shadow-lg">
          <div className="mb-4">
            <span className="text-sm text-gray-500">Question {flowState.questionNumber} of {flowState.totalQuestions}</span>
            {flowState.currentQuestion.critical && (
              <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">CRITICAL</span>
            )}
          </div>

          <h2 className="text-2xl font-semibold mb-6">{flowState.currentQuestion.text}</h2>

          <div className="answer-options grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
            {flowState.currentQuestion.options?.map((option: string) => (
              <button
                key={option}
                onClick={() => handleAnswer(option)}
                disabled={flowState.loading}
                className="px-6 py-3 bg-blue-50 hover:bg-blue-100 text-blue-900 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {option}
              </button>
            ))}
          </div>

          <div className="custom-answer">
            <input
              type="text"
              placeholder="Or type your answer and press Enter..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={flowState.loading}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && (e.target as HTMLInputElement).value) {
                  handleAnswer((e.target as HTMLInputElement).value);
                  (e.target as HTMLInputElement).value = '';
                }
              }}
            />
          </div>

          <div className="blocked-notice mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-sm text-yellow-800">
              ⚠️ You must answer all questions before building defense
            </p>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all"
                style={{ width: `${(flowState.questionNumber / flowState.totalQuestions) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      )}

      {/* Ready for defense - UNLOCKED */}
      {flowState.stage === 'ready_for_defense' && (
        <div className="defense-ready-section bg-white p-8 rounded-lg shadow-lg text-center">
          <div className="mb-6">
            <svg className="mx-auto h-16 w-16 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <h2 className="text-2xl font-semibold mb-4">Interview Complete!</h2>
          <p className="text-gray-600 mb-6">I have all the information needed to build your defense.</p>

          <button
            onClick={buildDefense}
            disabled={!flowState.canBuildDefense || flowState.loading}
            className="px-8 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg text-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {flowState.loading ? 'Building...' : 'BUILD MY DEFENSE STRATEGY'}
          </button>
        </div>
      )}

      {/* Defense built */}
      {flowState.stage === 'defense_built' && (
        <div className="defense-display bg-white p-8 rounded-lg shadow-lg">
          <h2 className="text-2xl font-semibold mb-6">Your Defense Strategy</h2>

          <div className="space-y-4">
            {flowState.defenses.map((defense, i) => (
              <div key={i} className="defense-card p-6 border border-gray-200 rounded-lg hover:border-blue-400 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-xl font-semibold text-blue-900">
                    {i + 1}. {defense.name}
                  </h3>
                  {defense.strength && (
                    <span className={`px-3 py-1 text-sm rounded ${
                      defense.strength === 'STRONG' || defense.strength === 'Very Strong'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {defense.strength}
                    </span>
                  )}
                </div>

                <p className="text-gray-700 mb-3">{defense.description}</p>

                {defense.requirements && (
                  <p className="text-sm text-gray-600 mb-2">
                    <strong>Requirements:</strong> {defense.requirements}
                  </p>
                )}

                {defense.action && (
                  <p className="text-sm font-medium text-blue-700 bg-blue-50 p-3 rounded">
                    <strong>Action:</strong> {defense.action}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Q&A Section - Always available but separate */}
      <div className="qa-section bg-white p-6 rounded-lg shadow-lg">
        <h3 className="text-xl font-semibold mb-4">Quick Questions</h3>
        <p className="text-sm text-gray-600 mb-4">Ask general legal questions (separate from defense building)</p>

        <div className="flex gap-2 mb-4">
          <input
            type="text"
            value={qaMessage}
            onChange={(e) => setQaMessage(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => e.key === 'Enter' && handleQA()}
          />
          <button
            onClick={handleQA}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
          >
            Ask
          </button>
        </div>

        <div className="qa-responses space-y-3 max-h-96 overflow-y-auto">
          {qaResponses.map((msg, i) => (
            <div
              key={i}
              className={`p-3 rounded-lg ${
                msg.type === 'question'
                  ? 'bg-blue-50 text-blue-900 ml-8'
                  : 'bg-gray-50 text-gray-900 mr-8'
              }`}
            >
              <div className="text-xs text-gray-500 mb-1">
                {msg.type === 'question' ? 'You' : 'AI Assistant'}
              </div>
              {msg.text}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
