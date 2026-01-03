/**
 * TypeScript Types for Bankruptcy Document Analysis
 */

// Alert types
export interface Alert {
  level: 'CRITICAL' | 'WARNING' | 'INFO';
  type: string;
  message: string;
  details?: string;
}

// Financial types
export interface SettlementOverpayment {
  payment: number;
  original: number;
  premium: number;
  excess: number;
  is_suspicious: boolean;
}

export interface ClaimsBreakdown {
  secured: ClaimTypeData;
  unsecured: ClaimTypeData;
  priority: ClaimTypeData;
  general: ClaimTypeData;
}

export interface ClaimTypeData {
  total: number;
  count: number;
  claims: any[];
}

export interface FinancialSummary {
  total_claims: number;
  total_settlements: number;
  largest_amount: number;
  smallest_amount: number;
  total_amounts_found: number;
  settlement_overpayments: SettlementOverpayment[];
  claims_breakdown: ClaimsBreakdown;
}

// Ownership types
export interface ControlDisparity {
  entity: string;
  voting: number;
  economic: number;
  gap: number;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface OwnershipAnalysis {
  control_structure: Record<string, number>;
  economic_structure: Record<string, number>;
  disparities: ControlDisparity[];
  has_control_issues: boolean;
}

// Legal types
export interface PrecedentViolation {
  case_name: string;
  citation: string;
  violation_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  context_preview: string;
}

export interface AuthorityIssue {
  limitation: string;
  context_preview: string;
}

export interface StatutoryReference {
  citation: string;
  title: string;
  section: string;
}

export interface LegalConcerns {
  precedent_violations: PrecedentViolation[];
  authority_issues: AuthorityIssue[];
  statutory_references: StatutoryReference[];
  total_issues: number;
}

// Fraud types
export interface PreferentialTreatment {
  beneficiary: string;
  premium: number;
  payment: number;
  original: number;
  excess: number;
  is_fraud: boolean;
  severity: 'CRITICAL' | 'WARNING';
}

export interface FraudulentConveyance {
  amount: number;
  red_flags: string[];
  risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  context_preview: string;
}

export interface FraudIndicators {
  total_indicators: number;
  preferential_treatments: PreferentialTreatment[];
  fraudulent_conveyances: FraudulentConveyance[];
  has_fraud_indicators: boolean;
}

// Recovery types
export interface RecoveryByClass {
  class: string;
  total_claims: number;
  claim_count: number;
  estimated_recovery: number;
  recovery_rate: number;
  expected_rate: number;
  difference: number;
  is_favorable: boolean;
  is_unfavorable: boolean;
}

export interface RecoveryInequity {
  class: string;
  actual_rate: number;
  expected_rate: number;
  difference: number;
  is_favored: boolean;
}

export interface OverallRecovery {
  total_claims: number;
  total_payments: number;
  overall_rate: number;
  expected_rate: number;
  is_suspicious: boolean;
  excess_recovery: number;
}

export interface CreditorRecovery {
  by_class: RecoveryByClass[];
  inequities: RecoveryInequity[];
  overall: OverallRecovery;
}

// Alerts types
export interface AlertsData {
  critical: Alert[];
  warnings: Alert[];
  info: Alert[];
  total_count: number;
  has_critical: boolean;
}

// Extraction stats
export interface ExtractionStats {
  amounts_extracted: number;
  unique_amounts: number;
  claims_extracted: number;
  settlements_extracted: number;
  legal_citations: number;
  completeness_score: number;
  extraction_complete: boolean;
  ai_backup_used: boolean;
}

// Overall assessment
export interface OverallAssessment {
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  total_red_flags: number;
  requires_immediate_attention: boolean;
  summary: string;
}

// Metadata
export interface DocumentMetadata {
  filename: string;
  processed_at: string;
  file_size: number;
  text_length: number;
}

// Main UI Display type
export interface BankruptcyUIDisplay {
  financial_summary: FinancialSummary;
  ownership_analysis: OwnershipAnalysis;
  legal_concerns: LegalConcerns;
  fraud_indicators: FraudIndicators;
  alerts: AlertsData;
  creditor_recovery: CreditorRecovery;
  extraction_stats: ExtractionStats;
  overall_assessment: OverallAssessment;
  metadata: DocumentMetadata;
}

// Complete API Response
export interface BankruptcyAnalysisResponse {
  success: boolean;
  filename: string;
  file_size: number;
  text_length: number;
  processed_at: string;
  financial: any; // Raw financial data
  ownership: any; // Raw ownership data
  legal: any; // Raw legal data
  metrics: any; // Raw metrics
  creditor_recovery: any; // Raw creditor recovery
  fraudulent_conveyances: any[]; // Raw fraudulent conveyances
  extraction_stats: any; // Raw extraction stats
  alerts: Alert[]; // Raw alerts
  ui_display: BankruptcyUIDisplay; // Formatted for UI
}
