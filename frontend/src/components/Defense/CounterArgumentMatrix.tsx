'use client';

import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  Shield,
  Swords,
  Target,
  FileText,
  Lightbulb
} from 'lucide-react';

interface CounterRebuttal {
  id: string;
  counter_text: string;
  your_response: string;
}

interface Rebuttal {
  id: string;
  rebuttal_text: string;
  evidence_needed: string[];
  strength: 'strong' | 'moderate' | 'weak';
  counter_rebuttals: CounterRebuttal[];
}

interface CounterArgument {
  id: string;
  argument_title: string;
  argument_description: string;
  legal_basis?: string;
  likelihood: 'high' | 'medium' | 'low';
  likelihood_score: number;
  likelihood_reasoning?: string;
  category: 'procedural' | 'substantive' | 'evidentiary' | 'credibility';
  evidence_to_support?: string[];
  rebuttals: Rebuttal[];
}

interface Weakness {
  title: string;
  description: string;
  category: string;
  severity: 'critical' | 'significant' | 'minor';
  remedy: string;
}

interface CounterArgumentMatrixProps {
  counterArguments: CounterArgument[];
  weaknesses?: Weakness[];
  overallStrength?: 'weak' | 'moderate' | 'strong';
  recommendations?: string[];
  caseType?: string;
}

const CounterArgumentMatrix: React.FC<CounterArgumentMatrixProps> = ({
  counterArguments,
  weaknesses = [],
  overallStrength = 'moderate',
  recommendations = [],
  caseType
}) => {
  const [expandedArguments, setExpandedArguments] = useState<Set<string>>(new Set());
  const [expandedRebuttals, setExpandedRebuttals] = useState<Set<string>>(new Set());

  const toggleArgument = (id: string) => {
    const newExpanded = new Set(expandedArguments);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedArguments(newExpanded);
  };

  const toggleRebuttal = (id: string) => {
    const newExpanded = new Set(expandedRebuttals);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRebuttals(newExpanded);
  };

  const getLikelihoodColor = (likelihood: string) => {
    switch (likelihood) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getLikelihoodIcon = (likelihood: string) => {
    switch (likelihood) {
      case 'high':
        return <AlertTriangle className="h-4 w-4" />;
      case 'medium':
        return <AlertCircle className="h-4 w-4" />;
      case 'low':
        return <CheckCircle className="h-4 w-4" />;
      default:
        return null;
    }
  };

  const getStrengthBadge = (strength: string) => {
    switch (strength) {
      case 'strong':
        return <span className="px-2 py-0.5 text-xs font-medium bg-green-100 text-green-700 rounded-full">Strong</span>;
      case 'moderate':
        return <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-700 rounded-full">Moderate</span>;
      case 'weak':
        return <span className="px-2 py-0.5 text-xs font-medium bg-red-100 text-red-700 rounded-full">Weak</span>;
      default:
        return null;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'procedural':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'substantive':
        return <Swords className="h-4 w-4 text-purple-500" />;
      case 'evidentiary':
        return <Target className="h-4 w-4 text-orange-500" />;
      case 'credibility':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const getOverallStrengthDisplay = () => {
    switch (overallStrength) {
      case 'strong':
        return {
          color: 'bg-green-100 text-green-800 border-green-300',
          icon: <Shield className="h-5 w-5" />,
          text: 'Strong Defense Position'
        };
      case 'moderate':
        return {
          color: 'bg-yellow-100 text-yellow-800 border-yellow-300',
          icon: <AlertCircle className="h-5 w-5" />,
          text: 'Moderate Defense Position'
        };
      case 'weak':
        return {
          color: 'bg-red-100 text-red-800 border-red-300',
          icon: <AlertTriangle className="h-5 w-5" />,
          text: 'Vulnerable Defense Position'
        };
      default:
        return {
          color: 'bg-gray-100 text-gray-800 border-gray-300',
          icon: <Shield className="h-5 w-5" />,
          text: 'Defense Position Analysis'
        };
    }
  };

  const strengthDisplay = getOverallStrengthDisplay();

  // Group arguments by likelihood
  const highLikelihood = counterArguments.filter(a => a.likelihood === 'high');
  const mediumLikelihood = counterArguments.filter(a => a.likelihood === 'medium');
  const lowLikelihood = counterArguments.filter(a => a.likelihood === 'low');

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-navy-800 to-navy-600 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Swords className="h-6 w-6 text-white" />
            <h2 className="text-lg font-semibold text-white">Opposing Counsel Analysis</h2>
          </div>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${strengthDisplay.color}`}>
            {strengthDisplay.icon}
            <span className="text-sm font-medium">{strengthDisplay.text}</span>
          </div>
        </div>
        {caseType && (
          <p className="text-navy-200 text-sm mt-1">Case Type: {caseType.replace('_', ' ').toUpperCase()}</p>
        )}
      </div>

      {/* Counter Arguments */}
      <div className="divide-y divide-gray-200">
        {/* High Likelihood Section */}
        {highLikelihood.length > 0 && (
          <div className="p-4">
            <h3 className="text-sm font-semibold text-red-700 flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4" />
              HIGH LIKELIHOOD ARGUMENTS ({highLikelihood.length})
            </h3>
            <div className="space-y-3">
              {highLikelihood.map(arg => (
                <CounterArgumentCard
                  key={arg.id}
                  argument={arg}
                  isExpanded={expandedArguments.has(arg.id)}
                  onToggle={() => toggleArgument(arg.id)}
                  expandedRebuttals={expandedRebuttals}
                  onToggleRebuttal={toggleRebuttal}
                  getLikelihoodColor={getLikelihoodColor}
                  getLikelihoodIcon={getLikelihoodIcon}
                  getStrengthBadge={getStrengthBadge}
                  getCategoryIcon={getCategoryIcon}
                />
              ))}
            </div>
          </div>
        )}

        {/* Medium Likelihood Section */}
        {mediumLikelihood.length > 0 && (
          <div className="p-4">
            <h3 className="text-sm font-semibold text-yellow-700 flex items-center gap-2 mb-3">
              <AlertCircle className="h-4 w-4" />
              MEDIUM LIKELIHOOD ARGUMENTS ({mediumLikelihood.length})
            </h3>
            <div className="space-y-3">
              {mediumLikelihood.map(arg => (
                <CounterArgumentCard
                  key={arg.id}
                  argument={arg}
                  isExpanded={expandedArguments.has(arg.id)}
                  onToggle={() => toggleArgument(arg.id)}
                  expandedRebuttals={expandedRebuttals}
                  onToggleRebuttal={toggleRebuttal}
                  getLikelihoodColor={getLikelihoodColor}
                  getLikelihoodIcon={getLikelihoodIcon}
                  getStrengthBadge={getStrengthBadge}
                  getCategoryIcon={getCategoryIcon}
                />
              ))}
            </div>
          </div>
        )}

        {/* Low Likelihood Section */}
        {lowLikelihood.length > 0 && (
          <div className="p-4">
            <h3 className="text-sm font-semibold text-green-700 flex items-center gap-2 mb-3">
              <CheckCircle className="h-4 w-4" />
              LOW LIKELIHOOD ARGUMENTS ({lowLikelihood.length})
            </h3>
            <div className="space-y-3">
              {lowLikelihood.map(arg => (
                <CounterArgumentCard
                  key={arg.id}
                  argument={arg}
                  isExpanded={expandedArguments.has(arg.id)}
                  onToggle={() => toggleArgument(arg.id)}
                  expandedRebuttals={expandedRebuttals}
                  onToggleRebuttal={toggleRebuttal}
                  getLikelihoodColor={getLikelihoodColor}
                  getLikelihoodIcon={getLikelihoodIcon}
                  getStrengthBadge={getStrengthBadge}
                  getCategoryIcon={getCategoryIcon}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Weaknesses Section */}
      {weaknesses.length > 0 && (
        <div className="border-t border-gray-200 p-4 bg-red-50">
          <h3 className="text-sm font-semibold text-red-800 flex items-center gap-2 mb-3">
            <Target className="h-4 w-4" />
            GAPS IN YOUR CASE ({weaknesses.length})
          </h3>
          <ul className="space-y-2">
            {weaknesses.map((weakness, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm">
                <span className={`mt-0.5 h-2 w-2 rounded-full ${
                  weakness.severity === 'critical' ? 'bg-red-500' :
                  weakness.severity === 'significant' ? 'bg-yellow-500' : 'bg-blue-500'
                }`} />
                <div>
                  <span className="font-medium text-gray-800">{weakness.title}:</span>{' '}
                  <span className="text-gray-600">{weakness.description}</span>
                  <p className="text-xs text-green-700 mt-0.5">
                    <strong>Fix:</strong> {weakness.remedy}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations Section */}
      {recommendations.length > 0 && (
        <div className="border-t border-gray-200 p-4 bg-teal-50">
          <h3 className="text-sm font-semibold text-teal-800 flex items-center gap-2 mb-3">
            <Lightbulb className="h-4 w-4" />
            RECOMMENDATIONS
          </h3>
          <ul className="space-y-2">
            {recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-teal-900">
                <span className="text-teal-500 font-bold">{idx + 1}.</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

// Sub-component for individual counter argument cards
interface CounterArgumentCardProps {
  argument: CounterArgument;
  isExpanded: boolean;
  onToggle: () => void;
  expandedRebuttals: Set<string>;
  onToggleRebuttal: (id: string) => void;
  getLikelihoodColor: (likelihood: string) => string;
  getLikelihoodIcon: (likelihood: string) => React.ReactNode;
  getStrengthBadge: (strength: string) => React.ReactNode;
  getCategoryIcon: (category: string) => React.ReactNode;
}

const CounterArgumentCard: React.FC<CounterArgumentCardProps> = ({
  argument,
  isExpanded,
  onToggle,
  expandedRebuttals,
  onToggleRebuttal,
  getLikelihoodColor,
  getLikelihoodIcon,
  getStrengthBadge,
  getCategoryIcon
}) => {
  return (
    <div className={`border rounded-lg ${getLikelihoodColor(argument.likelihood)}`}>
      {/* Argument Header */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <span className={`flex items-center gap-1 ${
            argument.likelihood === 'high' ? 'text-red-600' :
            argument.likelihood === 'medium' ? 'text-yellow-600' : 'text-green-600'
          }`}>
            {getLikelihoodIcon(argument.likelihood)}
          </span>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-medium text-gray-900">{argument.argument_title}</h4>
              {getCategoryIcon(argument.category)}
            </div>
            {!isExpanded && (
              <p className="text-sm text-gray-600 line-clamp-1">{argument.argument_description}</p>
            )}
          </div>
        </div>
        {isExpanded ? (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-400" />
        )}
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-current border-opacity-20">
          {/* Description */}
          <p className="text-sm text-gray-700 mt-3">{argument.argument_description}</p>

          {/* Legal Basis */}
          {argument.legal_basis && (
            <div className="mt-3">
              <h5 className="text-xs font-semibold text-gray-500 uppercase">Legal Basis</h5>
              <p className="text-sm text-gray-700">{argument.legal_basis}</p>
            </div>
          )}

          {/* Likelihood Reasoning */}
          {argument.likelihood_reasoning && (
            <div className="mt-3">
              <h5 className="text-xs font-semibold text-gray-500 uppercase">Why This Is Likely</h5>
              <p className="text-sm text-gray-700">{argument.likelihood_reasoning}</p>
            </div>
          )}

          {/* Evidence They'll Use */}
          {argument.evidence_to_support && argument.evidence_to_support.length > 0 && (
            <div className="mt-3">
              <h5 className="text-xs font-semibold text-gray-500 uppercase">Evidence They May Use</h5>
              <ul className="text-sm text-gray-700 list-disc list-inside">
                {argument.evidence_to_support.map((evidence, idx) => (
                  <li key={idx}>{evidence}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Rebuttals */}
          {argument.rebuttals && argument.rebuttals.length > 0 && (
            <div className="mt-4">
              <h5 className="text-xs font-semibold text-teal-700 uppercase flex items-center gap-1">
                <Shield className="h-3 w-3" />
                YOUR REBUTTALS ({argument.rebuttals.length})
              </h5>
              <div className="mt-2 space-y-2">
                {argument.rebuttals.map(rebuttal => (
                  <div key={rebuttal.id} className="bg-white bg-opacity-50 rounded-lg border border-teal-200">
                    <button
                      onClick={() => onToggleRebuttal(rebuttal.id)}
                      className="w-full px-3 py-2 flex items-center justify-between text-left"
                    >
                      <div className="flex items-center gap-2">
                        {getStrengthBadge(rebuttal.strength)}
                        <span className="text-sm text-gray-800">{rebuttal.rebuttal_text}</span>
                      </div>
                      {expandedRebuttals.has(rebuttal.id) ? (
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-gray-400" />
                      )}
                    </button>

                    {expandedRebuttals.has(rebuttal.id) && (
                      <div className="px-3 pb-3 border-t border-teal-100">
                        {/* Evidence Needed */}
                        {rebuttal.evidence_needed && rebuttal.evidence_needed.length > 0 && (
                          <div className="mt-2">
                            <h6 className="text-xs font-medium text-gray-500">Evidence Needed:</h6>
                            <ul className="text-xs text-gray-600 list-disc list-inside">
                              {rebuttal.evidence_needed.map((e, idx) => (
                                <li key={idx}>{e}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Counter-Rebuttals (Level 3) */}
                        {rebuttal.counter_rebuttals && rebuttal.counter_rebuttals.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-gray-200">
                            <h6 className="text-xs font-medium text-orange-600 flex items-center gap-1">
                              <Swords className="h-3 w-3" />
                              Their Response & Your Counter
                            </h6>
                            {rebuttal.counter_rebuttals.map(cr => (
                              <div key={cr.id} className="mt-1 text-xs">
                                <p className="text-red-700">
                                  <strong>They'll say:</strong> {cr.counter_text}
                                </p>
                                <p className="text-green-700 mt-0.5">
                                  <strong>You respond:</strong> {cr.your_response}
                                </p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CounterArgumentMatrix;
