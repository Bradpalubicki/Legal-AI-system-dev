// src/components/CaseTracking/CaseTracker.tsx

import { useState, useEffect } from 'react';
import { UnifiedDefenseBuilder } from './UnifiedDefenseBuilder';
import { useSession } from '@/hooks/useSession';
import { Case } from '@/types/case';

export function CaseTracker() {
  const [cases, setCases] = useState<Case[]>([]);
  const [selectedCase, setSelectedCase] = useState<Case | null>(null);
  const [view, setView] = useState<'list' | 'detail' | 'defense'>('list');
  const { createSession } = useSession();

  useEffect(() => {
    fetchCases();
  }, []);

  const fetchCases = async () => {
    const response = await fetch('/api/cases');
    const data = await response.json();
    setCases(data);
  };

  const startDefenseBuilder = async (caseItem: Case) => {
    // Create session linked to this case
    const session = await createSession(caseItem.id);
    setSelectedCase(caseItem);
    setView('defense');
  };

  return (
    <div className="case-tracker">
      {view === 'list' && (
        <div className="cases-grid">
          {cases.map(caseItem => (
            <div key={caseItem.id} className="case-card">
              <h3>{caseItem.case_name}</h3>
              <p>#{caseItem.case_number}</p>
              <p>Client: {caseItem.client_name}</p>

              <div className="case-actions">
                <button onClick={() => {
                  setSelectedCase(caseItem);
                  setView('detail');
                }}>
                  View Details
                </button>

                {!caseItem.defense_strategy && (
                  <button
                    onClick={() => startDefenseBuilder(caseItem)}
                    className="btn-primary"
                  >
                    Build Defense
                  </button>
                )}

                {caseItem.defense_strategy && (
                  <span className="badge">✓ Defense Ready</span>
                )}
              </div>

              {caseItem.response_deadline && (
                <div className="deadline-alert">
                  Response due: {new Date(caseItem.response_deadline).toLocaleDateString()}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {view === 'defense' && selectedCase && (
        <UnifiedDefenseBuilder
          caseId={selectedCase.id}
          onComplete={() => {
            fetchCases(); // Refresh to show defense is complete
            setView('list');
          }}
        />
      )}
    </div>
  );
}
