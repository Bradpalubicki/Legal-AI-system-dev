// UnifiedDefenseBuilder - Main defense strategy builder component

import { useState, useEffect } from 'react';
import { useSession } from '@/hooks/useSession';
import { DefenseStrategy } from '@/types/case';

interface UnifiedDefenseBuilderProps {
  caseId: string;
  onComplete: () => void;
}

export function UnifiedDefenseBuilder({ caseId, onComplete }: UnifiedDefenseBuilderProps) {
  const [step, setStep] = useState<'upload' | 'interview' | 'review'>('upload');
  const [documentText, setDocumentText] = useState('');
  const [analysis, setAnalysis] = useState<any>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [strategy, setStrategy] = useState<DefenseStrategy | null>(null);
  const { sessionData, createSession, callApi, isLoading } = useSession();

  useEffect(() => {
    if (caseId && !sessionData) {
      createSession(caseId);
    }
  }, [caseId, sessionData, createSession]);

  const handleDocumentUpload = async (text: string) => {
    setDocumentText(text);

    try {
      const result = await callApi('analyze_document', {
        documentText: text,
        caseId,
      });

      setAnalysis(result.analysis);
      setStep('interview');

      // Start interview
      const questionResult = await callApi('start_interview');
      setCurrentQuestion(questionResult.question);
    } catch (error) {
      console.error('Document analysis failed:', error);
    }
  };

  const handleAnswerSubmit = async (answer: string) => {
    const questionText = currentQuestion.question;
    setAnswers({ ...answers, [questionText]: answer });

    try {
      const result = await callApi('submit_answer', { answer });

      if (result.nextQuestion) {
        setCurrentQuestion(result.nextQuestion);
      } else {
        // Interview complete, build defense
        setStep('review');
        const strategyResult = await callApi('build_defense');
        setStrategy(strategyResult.strategy);
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const handleComplete = async () => {
    // Save strategy to case
    await fetch(`/api/cases/${caseId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ defense_strategy: strategy }),
    });

    onComplete();
  };

  return (
    <div className="defense-builder">
      <div className="progress-steps">
        <div className={`step ${step === 'upload' ? 'active' : 'complete'}`}>
          1. Upload Document
        </div>
        <div className={`step ${step === 'interview' ? 'active' : step === 'review' ? 'complete' : ''}`}>
          2. Interview
        </div>
        <div className={`step ${step === 'review' ? 'active' : ''}`}>
          3. Review Strategy
        </div>
      </div>

      {step === 'upload' && (
        <div className="upload-section">
          <h2>Upload Legal Document</h2>
          <textarea
            placeholder="Paste document text here..."
            value={documentText}
            onChange={(e) => setDocumentText(e.target.value)}
            rows={10}
            className="w-full p-4 border rounded"
          />
          <button
            onClick={() => handleDocumentUpload(documentText)}
            disabled={!documentText || isLoading}
            className="btn-primary mt-4"
          >
            {isLoading ? 'Analyzing...' : 'Analyze Document'}
          </button>
        </div>
      )}

      {step === 'interview' && currentQuestion && (
        <div className="interview-section">
          <h2>Defense Interview</h2>

          {analysis && (
            <div className="analysis-summary mb-4 p-4 bg-gray-50 rounded">
              <h3>Case Summary</h3>
              <p><strong>Type:</strong> {analysis.case_type}</p>
              <p><strong>Plaintiff:</strong> {analysis.plaintiff?.name}</p>
              <p><strong>Amount:</strong> ${analysis.amounts?.total?.toLocaleString()}</p>
            </div>
          )}

          <div className="question-card p-6 border rounded">
            <div className="question-header mb-4">
              <span className="badge">{currentQuestion.type}</span>
            </div>
            <h3 className="text-xl mb-2">{currentQuestion.question}</h3>
            <p className="text-gray-600 mb-4">{currentQuestion.why_important}</p>

            {currentQuestion.options ? (
              <div className="options space-y-2">
                {currentQuestion.options.map((option: string) => (
                  <button
                    key={option}
                    onClick={() => handleAnswerSubmit(option)}
                    className="option-btn w-full p-3 text-left border rounded hover:bg-gray-50"
                    disabled={isLoading}
                  >
                    {option}
                  </button>
                ))}
              </div>
            ) : (
              <div>
                <textarea
                  placeholder="Your answer..."
                  className="w-full p-3 border rounded"
                  rows={4}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.ctrlKey) {
                      handleAnswerSubmit(e.currentTarget.value);
                    }
                  }}
                />
                <button
                  onClick={(e) => {
                    const textarea = e.currentTarget.previousElementSibling as HTMLTextAreaElement;
                    handleAnswerSubmit(textarea.value);
                  }}
                  className="btn-primary mt-2"
                  disabled={isLoading}
                >
                  Submit Answer
                </button>
              </div>
            )}
          </div>

          <div className="answers-log mt-4">
            <h4>Previous Answers:</h4>
            <ul>
              {Object.entries(answers).map(([q, a]) => (
                <li key={q} className="mb-2">
                  <strong>Q:</strong> {q}<br />
                  <strong>A:</strong> {a}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {step === 'review' && strategy && (
        <div className="strategy-review">
          <h2>Defense Strategy</h2>

          <div className="strategy-section mb-6">
            <h3 className="text-xl font-bold mb-3">Primary Defenses</h3>
            {strategy.primary_defenses.map((defense, idx) => (
              <div key={idx} className="defense-card p-4 border rounded mb-3">
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-bold">{defense.name}</h4>
                  <span className={`badge badge-${defense.strength.toLowerCase()}`}>
                    {defense.strength}
                  </span>
                </div>
                <p className="mb-2">{defense.description}</p>
                <div className="requirements mb-2">
                  <strong>Requirements:</strong>
                  <ul className="list-disc ml-5">
                    {defense.requirements.map((req, i) => (
                      <li key={i}>{req}</li>
                    ))}
                  </ul>
                </div>
                <div>
                  <strong>How to Assert:</strong>
                  <p>{defense.how_to_assert}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="strategy-section mb-6">
            <h3 className="text-xl font-bold mb-3">Immediate Actions</h3>
            <ul className="list-disc ml-5">
              {strategy.immediate_actions.map((action, idx) => (
                <li key={idx} className="mb-1">{action}</li>
              ))}
            </ul>
          </div>

          <div className="strategy-section mb-6">
            <h3 className="text-xl font-bold mb-3">Evidence Needed</h3>
            <ul className="list-disc ml-5">
              {strategy.evidence_needed.map((evidence, idx) => (
                <li key={idx} className="mb-1">{evidence}</li>
              ))}
            </ul>
          </div>

          <div className="strategy-footer p-4 bg-teal-50 rounded">
            <p><strong>Success Probability:</strong> {strategy.success_probability}</p>
            <p><strong>Negotiation Position:</strong> {strategy.negotiation_position}</p>
          </div>

          <div className="actions mt-6 flex gap-4">
            <button onClick={handleComplete} className="btn-primary">
              Save Strategy
            </button>
            <button onClick={() => setStep('interview')} className="btn-secondary">
              Back to Interview
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
