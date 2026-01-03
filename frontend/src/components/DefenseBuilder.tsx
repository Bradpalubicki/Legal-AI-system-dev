import React, { useState } from 'react';

import { API_CONFIG } from '../config/api';
interface DefenseBuilderProps {
  documentData?: string;
  interviewAnswers?: Record<string, string>;
  sessionId: string;
}

interface Defense {
  name: string;
  description: string;
  strength: string;
  action?: string;
  requirements?: string[];
}

export function DefenseBuilder({ documentData, interviewAnswers, sessionId }: DefenseBuilderProps) {
  const [defenses, setDefenses] = useState<Defense[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const buildDefenses = async () => {
    setLoading(true);
    setError(null);

    try {
      // Call DEFENSE endpoint, not Q&A
      const response = await fetch(`${API_CONFIG.BASE_URL}/api/defense-flow/build`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId: sessionId
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Defense building failed');
      }

      const data = await response.json();
      setDefenses(data.defenses || []);

    } catch (error) {
      console.error('Defense building failed:', error);
      setError(error instanceof Error ? error.message : 'Failed to build defenses');

      // Use fallback defenses
      setDefenses([
        {
          name: 'Statute of Limitations',
          description: 'Debt may be too old to collect',
          strength: 'STRONG',
          action: 'Check your last payment date'
        },
        {
          name: 'Lack of Standing',
          description: 'Plaintiff must prove ownership',
          strength: 'MEDIUM',
          action: 'Request chain of title'
        },
        {
          name: 'Incorrect Amount',
          description: 'Verify the amount claimed',
          strength: 'MEDIUM',
          action: 'Request itemized statement'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="defense-builder-section max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Defense Strategy Builder</h2>
        <p className="text-gray-600 mb-6">Based on your document and interview answers</p>

        <button
          onClick={buildDefenses}
          disabled={loading || !interviewAnswers}
          className={`w-full py-3 px-6 rounded-lg font-semibold text-white transition-colors ${
            loading || !interviewAnswers
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {loading ? 'Building Your Defense...' : 'Build My Defense Strategy'}
        </button>

        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {!interviewAnswers && (
          <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-yellow-800 text-sm">
              ⚠️ Please complete the interview first before building your defense strategy.
            </p>
          </div>
        )}
      </div>

      {defenses.length > 0 && (
        <div className="defense-list mt-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Your Defense Options:</h3>
          <div className="space-y-4">
            {defenses.map((defense, i) => (
              <div key={i} className="defense-card bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
                <h4 className="text-lg font-bold text-gray-900 mb-2">
                  {i + 1}. {defense.name}
                </h4>
                <p className="text-gray-700 mb-3">{defense.description}</p>
                <div className="flex items-center gap-4 text-sm">
                  <p className={`strength font-semibold ${
                    defense.strength === 'STRONG' ? 'text-green-600' : 'text-yellow-600'
                  }`}>
                    Strength: {defense.strength}
                  </p>
                </div>
                {defense.action && (
                  <div className="mt-3 p-3 bg-blue-50 rounded">
                    <p className="text-sm text-blue-900">
                      <span className="font-semibold">Action:</span> {defense.action}
                    </p>
                  </div>
                )}
                {defense.requirements && defense.requirements.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm font-semibold text-gray-700 mb-1">Requirements:</p>
                    <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                      {defense.requirements.map((req, idx) => (
                        <li key={idx}>{req}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
