/**
 * Unified Legal Interface
 * Single component that handles the entire legal assistance workflow
 * Automatically manages state transitions and minimizes API calls
 */

import React, { useState } from 'react';
import { useUnifiedSystem } from '@/hooks/useUnifiedSystem';

export function UnifiedLegalInterface() {
  const {
    systemState,
    loading,
    error,
    uploadDocument,
    answerQuestion,
    buildDefense,
    sendChatMessage,
    efficiencyScore,
    aiCallsCount,
    cachedResponsesCount,
    hasDocument,
    isReady,
    isInterviewing,
    questionCount,
    defenseCount
  } = useUnifiedSystem();

  const [chatInput, setChatInput] = useState('');
  const [fileError, setFileError] = useState<string | null>(null);

  // Handle file upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file
    if (file.size > 10 * 1024 * 1024) {
      setFileError('File must be less than 10MB');
      return;
    }

    if (!file.name.match(/\.(txt|pdf|doc|docx)$/i)) {
      setFileError('Only .txt, .pdf, .doc, or .docx files are supported');
      return;
    }

    setFileError(null);

    try {
      await uploadDocument(file);
    } catch (err) {
      setFileError(err instanceof Error ? err.message : 'Upload failed');
    }
  };

  // Handle answer selection
  const handleAnswer = async (answer: string) => {
    try {
      await answerQuestion(answer);
    } catch (err) {
      console.error('Answer error:', err);
    }
  };

  // Handle chat message
  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || loading) return;

    const message = chatInput;
    setChatInput('');

    try {
      await sendChatMessage(message);
    } catch (err) {
      console.error('Chat error:', err);
    }
  };

  // Handle defense building
  const handleBuildDefense = async () => {
    try {
      await buildDefense();
    } catch (err) {
      console.error('Defense build error:', err);
    }
  };

  return (
    <div className="unified-interface max-w-4xl mx-auto p-6 space-y-6">
      {/* Efficiency Monitor */}
      <div className="efficiency-bar bg-gray-100 dark:bg-gray-800 p-4 rounded-lg flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            efficiencyScore > 0.5
              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
              : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
          }`}>
            System Efficiency: {(efficiencyScore * 100).toFixed(0)}%
          </div>

          <div className="flex space-x-4 text-sm text-gray-600 dark:text-gray-400">
            <span>AI Calls: <strong>{aiCallsCount}</strong></span>
            <span>Cached: <strong>{cachedResponsesCount}</strong></span>
            <span>Questions: <strong>{questionCount}</strong></span>
            {defenseCount > 0 && <span>Defenses: <strong>{defenseCount}</strong></span>}
          </div>
        </div>

        <div className="text-sm text-gray-500">
          State: <strong className="text-blue-600 dark:text-blue-400">{systemState.state}</strong>
        </div>
      </div>

      {/* Error Display */}
      {(error || fileError) && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-lg">
          <p className="text-red-800 dark:text-red-200 text-sm">{error || fileError}</p>
        </div>
      )}

      {/* Main Interface - State-based rendering */}
      {systemState.state === 'idle' && (
        <div className="card bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
          <h2 className="text-2xl font-bold mb-4">Upload Your Legal Document</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Upload a summons, complaint, or legal notice to get started.
          </p>

          <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center">
            <input
              type="file"
              multiple
              onChange={handleFileUpload}
              disabled={loading}
              accept=".txt,.pdf,.doc,.docx"
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className={`cursor-pointer inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 ${
                loading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {loading ? 'Analyzing...' : 'Choose File'}
            </label>
            <p className="mt-2 text-sm text-gray-500">
              Supported: .txt, .pdf, .doc, .docx (max 10MB)
            </p>
          </div>
        </div>
      )}

      {systemState.state === 'analyzing' && (
        <div className="card bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
          <h3 className="text-xl font-bold mb-4">Analyzing Document...</h3>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
          </div>
        </div>
      )}

      {isInterviewing && systemState.currentQuestion && (
        <div className="card bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
          <div className="mb-4">
            <span className="text-sm text-gray-500">Question {questionCount + 1}</span>
          </div>

          <h3 className="text-xl font-semibold mb-6">{systemState.currentQuestion.text}</h3>

          <div className="options grid grid-cols-1 md:grid-cols-2 gap-3">
            {systemState.currentQuestion.options?.map((option: string) => (
              <button
                key={option}
                onClick={() => handleAnswer(option)}
                disabled={loading}
                className="px-6 py-3 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/40
                           text-blue-900 dark:text-blue-100 rounded-lg font-medium transition-colors
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {option}
              </button>
            ))}
          </div>

          {systemState.currentQuestion.priority === 1 && (
            <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                ⚠️ Critical for defense strategy
              </p>
            </div>
          )}
        </div>
      )}

      {systemState.state === 'building' && (
        <div className="card bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
          <h3 className="text-xl font-bold mb-4">Ready to Build Your Defense</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            I've analyzed your document and collected {questionCount} key answers.
          </p>

          <button
            onClick={handleBuildDefense}
            disabled={loading}
            className="px-8 py-3 bg-green-600 hover:bg-green-700 text-white font-bold rounded-lg
                       disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Building Strategy...' : 'Build Defense Strategy'}
          </button>
        </div>
      )}

      {isReady && systemState.defenses.length > 0 && (
        <div className="card bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
          <h3 className="text-2xl font-bold mb-6">Your Defense Strategy</h3>

          <div className="space-y-4">
            {systemState.defenses.map((defense: any, i: number) => (
              <div
                key={i}
                className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-400 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="text-lg font-semibold text-blue-900 dark:text-blue-100">
                    {i + 1}. {defense.name}
                  </h4>
                  {defense.strength && (
                    <span className={`px-2 py-1 text-xs rounded ${
                      defense.strength === 'Very Strong'
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                        : defense.strength === 'Strong'
                        ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                    }`}>
                      {defense.strength}
                    </span>
                  )}
                </div>

                {defense.description && (
                  <p className="text-gray-700 dark:text-gray-300 mb-2">{defense.description}</p>
                )}

                {defense.action && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    <strong>Action:</strong> {defense.action}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Q&A Chat - Available after document upload */}
      {hasDocument && (
        <div className="card bg-white dark:bg-gray-800 p-6 rounded-lg shadow-lg">
          <h3 className="text-xl font-bold mb-4">Ask Questions</h3>

          <div className="chat-history mb-4 space-y-3 max-h-96 overflow-y-auto">
            {systemState.chatHistory.map((msg, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg ${
                  msg.type === 'user'
                    ? 'bg-blue-50 dark:bg-blue-900/20 ml-8'
                    : 'bg-gray-50 dark:bg-gray-700/50 mr-8'
                }`}
              >
                <div className="text-xs text-gray-500 mb-1">
                  {msg.type === 'user' ? 'You' : 'AI Assistant'}
                </div>
                <p className="text-gray-800 dark:text-gray-200">{msg.message}</p>
              </div>
            ))}
          </div>

          <form onSubmit={handleChatSubmit} className="flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask about your case..."
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                         bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !chatInput.trim()}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg
                         disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
