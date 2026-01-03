/**
 * Bankruptcy Analysis Dashboard
 *
 * Displays comprehensive bankruptcy document analysis with:
 * - Financial summary
 * - Fraud indicators
 * - Legal violations
 * - Settlement metrics
 * - Ownership structure
 * - Critical alerts
 */

import React from 'react';
import { Card } from './ui/card';

// Type definitions
interface BankruptcyAnalysisProps {
  data: any; // Will be replaced with proper types
}

interface Alert {
  level: 'CRITICAL' | 'WARNING' | 'INFO';
  type: string;
  message: string;
  details?: string;
}

interface FinancialSummary {
  total_claims: number;
  total_settlements: number;
  largest_amount: number;
  settlement_overpayments: Array<{
    payment: number;
    original: number;
    premium: number;
    excess: number;
    is_suspicious: boolean;
  }>;
  claims_breakdown: any;
}

// Main Dashboard Component
export default function BankruptcyAnalysisDashboard({ data }: BankruptcyAnalysisProps) {
  if (!data?.ui_display) {
    return (
      <div className="p-6 text-center text-gray-500">
        No analysis data available
      </div>
    );
  }

  const display = data.ui_display;

  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-6">
      {/* Overall Risk Assessment */}
      <OverallRiskCard assessment={display.overall_assessment} />

      {/* Critical Alerts */}
      {display.alerts.has_critical && (
        <CriticalAlertsSection alerts={display.alerts} />
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Financial Summary */}
        <FinancialSummaryCard summary={display.financial_summary} />

        {/* Fraud Indicators */}
        {display.fraud_indicators.has_fraud_indicators && (
          <FraudIndicatorsCard indicators={display.fraud_indicators} />
        )}
      </div>

      {/* Settlement Metrics */}
      {display.financial_summary.settlement_overpayments?.length > 0 && (
        <SettlementMetricsCard
          settlements={display.financial_summary.settlement_overpayments}
          recovery={display.creditor_recovery}
        />
      )}

      {/* Legal Concerns */}
      {display.legal_concerns.total_issues > 0 && (
        <LegalConcernsCard concerns={display.legal_concerns} />
      )}

      {/* Ownership Analysis */}
      {display.ownership_analysis.has_control_issues && (
        <OwnershipAnalysisCard analysis={display.ownership_analysis} />
      )}

      {/* Extraction Stats */}
      <ExtractionStatsCard stats={display.extraction_stats} />
    </div>
  );
}

// Overall Risk Assessment Card
function OverallRiskCard({ assessment }: { assessment: any }) {
  const riskColors = {
    CRITICAL: 'bg-red-900 border-red-700',
    HIGH: 'bg-orange-900 border-orange-700',
    MEDIUM: 'bg-yellow-900 border-yellow-700',
    LOW: 'bg-green-900 border-green-700'
  };

  const riskColor = riskColors[assessment.risk_level as keyof typeof riskColors] || riskColors.MEDIUM;

  return (
    <Card className={`p-6 border-2 ${riskColor}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h2 className="text-2xl font-bold text-white">
              Overall Risk Assessment
            </h2>
            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
              assessment.risk_level === 'CRITICAL' ? 'bg-red-600' :
              assessment.risk_level === 'HIGH' ? 'bg-orange-600' :
              assessment.risk_level === 'MEDIUM' ? 'bg-yellow-600' :
              'bg-green-600'
            } text-white`}>
              {assessment.risk_level}
            </span>
          </div>
          <p className="text-gray-200 text-lg mb-4">
            {assessment.summary}
          </p>
          <div className="flex items-center space-x-6 text-sm">
            <div>
              <span className="text-gray-400">Total Red Flags:</span>
              <span className="ml-2 text-white font-semibold text-lg">
                {assessment.total_red_flags}
              </span>
            </div>
            {assessment.requires_immediate_attention && (
              <div className="flex items-center space-x-2 text-red-400 font-semibold">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <span>REQUIRES IMMEDIATE ATTENTION</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}

// Critical Alerts Section
function CriticalAlertsSection({ alerts }: { alerts: any }) {
  return (
    <Card className="p-6 bg-red-950 border-2 border-red-700">
      <h3 className="text-xl font-bold text-white mb-4 flex items-center">
        <svg className="w-6 h-6 mr-2 text-red-400" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
        Critical Alerts ({alerts.critical.length})
      </h3>
      <div className="space-y-3">
        {alerts.critical.map((alert: Alert, index: number) => (
          <div key={index} className="bg-red-900/50 p-4 rounded-lg border border-red-700">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <span className="inline-block px-2 py-1 text-xs font-semibold bg-red-600 text-white rounded">
                  {alert.type}
                </span>
              </div>
              <div className="ml-3 flex-1">
                <p className="text-white font-medium">{alert.message}</p>
                {alert.details && (
                  <p className="mt-1 text-sm text-gray-300">{alert.details}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// Financial Summary Card
function FinancialSummaryCard({ summary }: { summary: FinancialSummary }) {
  return (
    <Card className="p-6">
      <h3 className="text-xl font-bold mb-4">Financial Summary</h3>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Claims</p>
            <p className="text-2xl font-bold">${summary.total_claims.toLocaleString()}</p>
          </div>
          <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Settlements</p>
            <p className="text-2xl font-bold">${summary.total_settlements.toLocaleString()}</p>
          </div>
        </div>

        {summary.settlement_overpayments?.length > 0 && (
          <div className="mt-4">
            <h4 className="font-semibold mb-2 text-orange-600 dark:text-orange-400">
              Settlement Overpayments ({summary.settlement_overpayments.length})
            </h4>
            {summary.settlement_overpayments.map((settlement, index) => (
              <div key={index} className="bg-orange-50 dark:bg-orange-950 p-3 rounded-lg mb-2">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium">${settlement.payment.toLocaleString()} payment</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Original: ${settlement.original.toLocaleString()}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className={`font-bold ${settlement.is_suspicious ? 'text-red-600' : 'text-orange-600'}`}>
                      {settlement.premium.toFixed(2)}x premium
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      +${settlement.excess.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Claims Breakdown */}
        {summary.claims_breakdown && (
          <div className="mt-4">
            <h4 className="font-semibold mb-2">Claims by Type</h4>
            <div className="space-y-2">
              {Object.entries(summary.claims_breakdown).map(([type, data]: [string, any]) => (
                data.count > 0 && (
                  <div key={type} className="flex justify-between items-center bg-gray-50 dark:bg-gray-800 p-2 rounded">
                    <span className="capitalize">{type}</span>
                    <div className="text-right">
                      <span className="font-semibold">${data.total.toLocaleString()}</span>
                      <span className="text-sm text-gray-500 ml-2">({data.count} claims)</span>
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

// Fraud Indicators Card
function FraudIndicatorsCard({ indicators }: { indicators: any }) {
  return (
    <Card className="p-6 border-2 border-red-600">
      <h3 className="text-xl font-bold mb-4 flex items-center text-red-600 dark:text-red-400">
        <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M13.477 14.89A6 6 0 015.11 6.524l8.367 8.368zm1.414-1.414L6.524 5.11a6 6 0 018.367 8.367zM18 10a8 8 0 11-16 0 8 8 0 0116 0z" clipRule="evenodd" />
        </svg>
        Fraud Indicators ({indicators.total_indicators})
      </h3>

      <div className="space-y-4">
        {/* Preferential Treatments */}
        {indicators.preferential_treatments?.length > 0 && (
          <div>
            <h4 className="font-semibold mb-2">Preferential Treatments</h4>
            {indicators.preferential_treatments.map((treatment: any, index: number) => (
              <div key={index} className={`p-3 rounded-lg mb-2 ${
                treatment.is_fraud ? 'bg-red-100 dark:bg-red-950 border border-red-600' : 'bg-orange-50 dark:bg-orange-950'
              }`}>
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{treatment.beneficiary}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      ${treatment.payment.toLocaleString()} (original: ${treatment.original.toLocaleString()})
                    </p>
                  </div>
                  <div className="text-right">
                    <span className={`font-bold ${treatment.is_fraud ? 'text-red-600' : 'text-orange-600'}`}>
                      {treatment.premium.toFixed(2)}x
                    </span>
                    {treatment.is_fraud && (
                      <p className="text-xs text-red-600 font-semibold mt-1">POTENTIAL FRAUD</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Fraudulent Conveyances */}
        {indicators.fraudulent_conveyances?.length > 0 && (
          <div>
            <h4 className="font-semibold mb-2 text-red-600">Fraudulent Conveyances</h4>
            {indicators.fraudulent_conveyances.map((conveyance: any, index: number) => (
              <div key={index} className="bg-red-100 dark:bg-red-950 p-3 rounded-lg mb-2 border border-red-600">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="font-medium text-red-900 dark:text-red-200">
                      ${conveyance.amount.toLocaleString()}
                    </p>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {conveyance.red_flags.map((flag: string, i: number) => (
                        <span key={i} className="px-2 py-1 text-xs bg-red-200 dark:bg-red-900 text-red-900 dark:text-red-200 rounded">
                          {flag.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                  <span className="px-2 py-1 text-xs font-semibold bg-red-600 text-white rounded">
                    {conveyance.risk_level}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}

// Settlement Metrics Card
function SettlementMetricsCard({ settlements, recovery }: { settlements: any[], recovery: any }) {
  return (
    <Card className="p-6">
      <h3 className="text-xl font-bold mb-4">Settlement & Recovery Analysis</h3>

      {/* Overall Recovery */}
      {recovery?.overall && (
        <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-lg mb-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Claims</p>
              <p className="text-lg font-bold">${recovery.overall.total_claims.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Payments</p>
              <p className="text-lg font-bold">${recovery.overall.total_payments.toLocaleString()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Recovery Rate</p>
              <p className={`text-lg font-bold ${recovery.overall.is_suspicious ? 'text-red-600' : ''}`}>
                {(recovery.overall.overall_rate * 100).toFixed(1)}%
              </p>
            </div>
          </div>
          {recovery.overall.is_suspicious && (
            <div className="mt-3 p-2 bg-red-100 dark:bg-red-950 rounded text-sm text-red-900 dark:text-red-200">
              WARNING: Recovery rate exceeds 100% - mathematically impossible in legitimate bankruptcy
            </div>
          )}
        </div>
      )}

      {/* Recovery by Class */}
      {recovery?.by_class?.length > 0 && (
        <div>
          <h4 className="font-semibold mb-2">Recovery by Creditor Class</h4>
          <div className="space-y-2">
            {recovery.by_class.map((classData: any, index: number) => (
              <div key={index} className="flex justify-between items-center bg-gray-50 dark:bg-gray-800 p-3 rounded">
                <div>
                  <p className="font-medium capitalize">{classData.class}</p>
                  <p className="text-sm text-gray-500">
                    ${classData.total_claims.toLocaleString()} ({classData.claim_count} claims)
                  </p>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${
                    classData.is_favorable ? 'text-green-600' :
                    classData.is_unfavorable ? 'text-red-600' :
                    ''
                  }`}>
                    {(classData.recovery_rate * 100).toFixed(1)}%
                  </p>
                  <p className="text-xs text-gray-500">
                    Expected: {(classData.expected_rate * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

// Legal Concerns Card
function LegalConcernsCard({ concerns }: { concerns: any }) {
  return (
    <Card className="p-6">
      <h3 className="text-xl font-bold mb-4">Legal Concerns ({concerns.total_issues})</h3>

      {/* Precedent Violations */}
      {concerns.precedent_violations?.length > 0 && (
        <div className="mb-4">
          <h4 className="font-semibold mb-2 text-red-600 dark:text-red-400">Precedent Violations</h4>
          {concerns.precedent_violations.map((violation: any, index: number) => (
            <div key={index} className="bg-red-50 dark:bg-red-950 p-3 rounded-lg mb-2">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="font-medium text-red-900 dark:text-red-200">{violation.case_name}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{violation.citation}</p>
                  <p className="text-sm mt-2">
                    <span className="font-semibold">Type:</span> {violation.violation_type.replace(/_/g, ' ')}
                  </p>
                </div>
                <span className="px-2 py-1 text-xs bg-red-600 text-white rounded font-semibold">
                  {violation.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Authority Issues */}
      {concerns.authority_issues?.length > 0 && (
        <div>
          <h4 className="font-semibold mb-2">Authority Limitations</h4>
          {concerns.authority_issues.map((issue: any, index: number) => (
            <div key={index} className="bg-yellow-50 dark:bg-yellow-950 p-3 rounded-lg mb-2">
              <p className="font-medium">{issue.limitation}</p>
            </div>
          ))}
        </div>
      )}

      {/* Statutory References */}
      {concerns.statutory_references?.length > 0 && (
        <div className="mt-4">
          <h4 className="font-semibold mb-2 text-sm text-gray-600">Statutory References</h4>
          <div className="flex flex-wrap gap-2">
            {concerns.statutory_references.map((ref: any, index: number) => (
              <span key={index} className="px-2 py-1 text-xs bg-gray-200 dark:bg-gray-700 rounded">
                {ref.citation}
              </span>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

// Ownership Analysis Card
function OwnershipAnalysisCard({ analysis }: { analysis: any }) {
  return (
    <Card className="p-6">
      <h3 className="text-xl font-bold mb-4">Ownership & Control Analysis</h3>

      {/* Control Disparities */}
      {analysis.disparities?.length > 0 && (
        <div>
          <h4 className="font-semibold mb-2 text-orange-600 dark:text-orange-400">Control Disparities</h4>
          {analysis.disparities.map((disparity: any, index: number) => (
            <div key={index} className={`p-4 rounded-lg mb-3 border-2 ${
              disparity.severity === 'HIGH' ? 'bg-red-50 dark:bg-red-950 border-red-600' :
              disparity.severity === 'MEDIUM' ? 'bg-orange-50 dark:bg-orange-950 border-orange-600' :
              'bg-yellow-50 dark:bg-yellow-950 border-yellow-600'
            }`}>
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="font-medium text-lg">{disparity.entity}</p>
                  <div className="mt-2 space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span>Voting Control:</span>
                      <span className="font-semibold">{disparity.voting}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Economic Ownership:</span>
                      <span className="font-semibold">{disparity.economic}%</span>
                    </div>
                    <div className="flex justify-between border-t pt-1">
                      <span className="font-semibold">Disparity:</span>
                      <span className="font-bold text-red-600">{disparity.gap}%</span>
                    </div>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs font-semibold rounded ${
                  disparity.severity === 'HIGH' ? 'bg-red-600 text-white' :
                  disparity.severity === 'MEDIUM' ? 'bg-orange-600 text-white' :
                  'bg-yellow-600 text-white'
                }`}>
                  {disparity.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}

// Extraction Stats Card
function ExtractionStatsCard({ stats }: { stats: any }) {
  const getCompletenessColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <Card className="p-6">
      <h3 className="text-xl font-bold mb-4">Extraction Statistics</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center">
          <p className="text-3xl font-bold">{stats.amounts_extracted}</p>
          <p className="text-sm text-gray-500">Amounts Found</p>
        </div>
        <div className="text-center">
          <p className="text-3xl font-bold">{stats.claims_extracted}</p>
          <p className="text-sm text-gray-500">Claims Extracted</p>
        </div>
        <div className="text-center">
          <p className="text-3xl font-bold">{stats.settlements_extracted}</p>
          <p className="text-sm text-gray-500">Settlements</p>
        </div>
        <div className="text-center">
          <p className={`text-3xl font-bold ${getCompletenessColor(stats.completeness_score)}`}>
            {stats.completeness_score.toFixed(0)}%
          </p>
          <p className="text-sm text-gray-500">Completeness</p>
        </div>
      </div>
      {stats.ai_backup_used && (
        <div className="mt-4 p-2 bg-blue-50 dark:bg-blue-950 rounded text-sm text-blue-900 dark:text-blue-200 text-center">
          AI backup extraction was used to enhance results
        </div>
      )}
    </Card>
  );
}
