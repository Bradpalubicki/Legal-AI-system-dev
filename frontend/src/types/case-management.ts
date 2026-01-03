/**
 * Case Management TypeScript Types
 * Mirrors backend models for type safety
 */

// ============================================================================
// ENUMS
// ============================================================================

export enum CaseStatus {
  INTAKE = "intake",
  ACTIVE = "active",
  PENDING = "pending",
  STAYED = "stayed",
  CLOSED = "closed",
  DISMISSED = "dismissed",
  SETTLED = "settled",
  APPEALED = "appealed",
}

export enum CaseType {
  BANKRUPTCY_CH7 = "bankruptcy_ch7",
  BANKRUPTCY_CH11 = "bankruptcy_ch11",
  BANKRUPTCY_CH13 = "bankruptcy_ch13",
  CIVIL_LITIGATION = "civil_litigation",
  DEBT_COLLECTION = "debt_collection",
  FORECLOSURE = "foreclosure",
  EVICTION = "eviction",
  CRIMINAL = "criminal",
  EMPLOYMENT = "employment",
  CONTRACT_DISPUTE = "contract_dispute",
  OTHER = "other",
}

export enum PartyRole {
  PLAINTIFF = "plaintiff",
  DEFENDANT = "defendant",
  DEBTOR = "debtor",
  CREDITOR = "creditor",
  TRUSTEE = "trustee",
  ATTORNEY = "attorney",
  JUDGE = "judge",
  WITNESS = "witness",
  EXPERT = "expert",
  MEDIATOR = "mediator",
  BIDDER = "bidder",
  OTHER = "other",
}

export enum EventType {
  FILING = "filing",
  HEARING = "hearing",
  DEADLINE = "deadline",
  MEETING = "meeting",
  OBJECTION = "objection",
  MOTION = "motion",
  ORDER = "order",
  PAYMENT = "payment",
  AUCTION = "auction",
  CONFIRMATION = "confirmation",
  DISCHARGE = "discharge",
  OTHER = "other",
}

export enum EventStatus {
  SCHEDULED = "scheduled",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
  POSTPONED = "postponed",
  MISSED = "missed",
}

export enum TransactionType {
  PAYMENT = "payment",
  DISTRIBUTION = "distribution",
  FEE = "fee",
  DEPOSIT = "deposit",
  REFUND = "refund",
  BID = "bid",
  TRANSFER = "transfer",
  ESCROW = "escrow",
}

export enum AssetStatus {
  INCLUDED = "included",
  EXCLUDED = "excluded",
  PENDING = "pending",
  SOLD = "sold",
  ABANDONED = "abandoned",
  EXEMPT = "exempt",
}

export enum ObjectionStatus {
  FILED = "filed",
  PENDING = "pending",
  OVERRULED = "overruled",
  SUSTAINED = "sustained",
  WITHDRAWN = "withdrawn",
  RESOLVED = "resolved",
}

// ============================================================================
// CORE INTERFACES
// ============================================================================

export interface LegalCase {
  id: string;
  case_number: string;
  case_name: string;
  case_type: CaseType;
  status: CaseStatus;
  court_name?: string;
  jurisdiction?: string;
  judge_name?: string;
  filing_date?: string;
  status_date?: string;
  close_date?: string;
  description?: string;
  current_phase?: string;
  estimated_completion_date?: string;
  parent_case_id?: string;
  related_case_ids?: string[];
  created_at: string;
  updated_at: string;
  created_by?: string;
  notes?: string;
  tags?: string[];
  custom_fields?: Record<string, any>;
}

export interface Party {
  id: string;
  case_id: string;
  role: PartyRole;
  name: string;
  legal_name?: string;
  party_type?: string;
  email?: string;
  phone?: string;
  address?: string;
  represented_by?: string;
  attorney_firm?: string;
  bar_number?: string;
  claims_held?: any[];
  interest_amount?: number;
  interest_description?: string;
  priority_level?: number;
  authorization_level?: string;
  can_receive_notices?: boolean;
  can_file_documents?: boolean;
  can_bid?: boolean;
  preferred_contact_method?: string;
  language_preference?: string;
  communication_notes?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  notes?: string;
  custom_fields?: Record<string, any>;
}

export interface TimelineEvent {
  id: string;
  case_id: string;
  event_type: EventType;
  title: string;
  description?: string;
  event_date: string;
  end_date?: string;
  is_all_day?: boolean;
  timezone?: string;
  location?: string;
  courtroom?: string;
  virtual_meeting_link?: string;
  status: EventStatus;
  completion_percentage?: number;
  completed_at?: string;
  blocks_event_ids?: string[];
  blocked_by_event_ids?: string[];
  related_event_ids?: string[];
  required_actions?: any[];
  required_documents?: any[];
  required_parties?: any[];
  completion_criteria?: any[];
  deliverables?: any[];
  reminder_dates?: string[];
  notification_sent?: boolean;
  attendees_notified?: boolean;
  outcome?: string;
  minutes_notes?: string;
  orders_issued?: any[];
  created_at: string;
  updated_at: string;
  created_by?: string;
  is_critical_path?: boolean;
  priority_level?: number;
  custom_fields?: Record<string, any>;
}

export interface FinancialTransaction {
  id: string;
  case_id: string;
  transaction_type: TransactionType;
  transaction_date: string;
  effective_date?: string;
  amount: number;
  currency?: string;
  check_number?: string;
  reference_number?: string;
  party_id?: string;
  from_party_id?: string;
  to_party_id?: string;
  description?: string;
  category?: string;
  subcategory?: string;
  requires_approval?: boolean;
  approved_by?: string;
  approval_date?: string;
  approval_status?: string;
  distribution_priority?: number;
  distribution_percentage?: number;
  calculated_amount?: number;
  calculation_method?: string;
  payment_status?: string;
  payment_method?: string;
  cleared_date?: string;
  related_asset_id?: string;
  related_event_id?: string;
  related_document_id?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  notes?: string;
  custom_fields?: Record<string, any>;
}

export interface Asset {
  id: string;
  case_id: string;
  asset_type: string;
  category?: string;
  name: string;
  description?: string;
  location?: string;
  identification_number?: string;
  status: AssetStatus;
  inclusion_reason?: string;
  exclusion_reason?: string;
  estimated_value?: number;
  appraised_value?: number;
  market_value?: number;
  valuation_date?: string;
  valuation_method?: string;
  has_liens?: boolean;
  lien_amount?: number;
  lien_holders?: any[];
  encumbrances?: any[];
  has_contracts?: boolean;
  contract_details?: any[];
  ongoing_obligations?: any[];
  disposition_method?: string;
  disposition_date?: string;
  disposition_amount?: number;
  buyer_party_id?: string;
  minimum_bid?: number;
  current_high_bid?: number;
  reserve_price?: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
  notes?: string;
  custom_fields?: Record<string, any>;
  attachments?: any[];
}

export interface BiddingProcess {
  id: string;
  case_id: string;
  asset_id: string;
  process_name?: string;
  process_type?: string;
  status?: string;
  announcement_date?: string;
  bidding_start_date: string;
  bidding_end_date: string;
  sale_hearing_date?: string;
  qualified_bidder_criteria?: any[];
  requires_approval?: boolean;
  approved_bidders?: any[];
  deposit_required?: boolean;
  deposit_amount?: number;
  deposit_percentage?: number;
  deposit_deadline?: string;
  deposits_received?: any[];
  minimum_bid?: number;
  bid_increment?: number;
  reserve_price?: number;
  allows_credit_bid?: boolean;
  credit_bid_rules?: any;
  breakup_fee?: number;
  expense_reimbursement?: number;
  stalking_horse_bidder_id?: string;
  stalking_horse_protections?: any;
  bids?: Bid[];
  highest_bid_amount?: number;
  highest_bidder_id?: string;
  evaluation_criteria?: any[];
  evaluation_scores?: any[];
  winning_bid_id?: string;
  winner_selected_date?: string;
  sale_approved?: boolean;
  sale_approval_date?: string;
  sale_closing_date?: string;
  final_sale_price?: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
  notes?: string;
  custom_fields?: Record<string, any>;
}

export interface Bid {
  id: string;
  bidder_id: string;
  amount: number;
  timestamp: string;
  notes?: string;
}

export interface Objection {
  id: string;
  case_id: string;
  objection_type: string;
  title: string;
  description?: string;
  grounds?: string;
  filed_by_party_id: string;
  objection_to_party_id?: string;
  affected_parties?: string[];
  filing_date: string;
  response_deadline?: string;
  hearing_date?: string;
  resolution_date?: string;
  status: ObjectionStatus;
  resolution?: string;
  resolution_type?: string;
  impact_on_timeline?: string;
  blocks_event_ids?: string[];
  delays_days?: number;
  responses_required_from?: string[];
  responses_received?: any[];
  response_status?: string;
  related_document_id?: string;
  related_event_id?: string;
  related_asset_id?: string;
  legal_authority?: string;
  precedent_cases?: any[];
  created_at: string;
  updated_at: string;
  created_by?: string;
  notes?: string;
  custom_fields?: Record<string, any>;
}

// ============================================================================
// DASHBOARD & ANALYTICS TYPES
// ============================================================================

export interface CaseDashboard {
  case_info: {
    id: string;
    case_number: string;
    case_name: string;
    status: string;
    current_phase?: string;
  };
  deadlines: {
    upcoming: {
      id: string;
      title: string;
      date: string;
      days_until: number;
    }[];
    at_risk_count: number;
  };
  assets: {
    count: number;
    total_value: number;
  };
  objections: {
    pending_count: number;
  };
}

export interface CriticalPathAnalysis {
  case_id: string;
  total_events: number;
  critical_path_events: CriticalPathEvent[];
  parallel_opportunities: ParallelOpportunity[];
  estimated_completion?: string;
}

export interface CriticalPathEvent extends TimelineEvent {
  earliest_start: string;
  latest_start: string;
  slack_days: number;
  is_critical: boolean;
}

export interface ParallelOpportunity {
  anchor_event: TimelineEvent;
  parallel_events: TimelineEvent[];
  potential_time_savings: number;
}

export interface EventImpact {
  event: {
    id: string;
    title: string;
    event_date: string;
  };
  affected_events: {
    event: TimelineEvent;
    dependency_chain: string[];
    cascade_level: number;
  }[];
  total_impacted: number;
  suggested_buffer_days: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH";
}

export interface StrategicSummary {
  case_overview: {
    case_number: string;
    case_name: string;
    current_phase?: string;
    status: string;
    days_since_filing: number;
  };
  key_upcoming_deadlines: {
    title: string;
    date: string;
    days_until: number;
    priority: number;
  }[];
  decision_points_requiring_input: DecisionPoint[];
  risk_factors_and_mitigation: RiskFactor[];
  alternative_scenarios: Scenario[];
  total_asset_value: number;
  total_parties: number;
  critical_path_events: number;
}

export interface DecisionPoint {
  type: string;
  description: string;
  deadline?: string;
  decisions_needed: string[];
  urgency: "LOW" | "MEDIUM" | "HIGH" | "URGENT" | "CRITICAL";
}

export interface RiskFactor {
  category: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  description: string;
  impact: string;
  mitigation: string[];
}

export interface Scenario {
  name: string;
  probability: string;
  description: string;
  outcomes: string[];
  requirements?: string[];
  risks?: string[];
}

export interface TalkingPoints {
  case_strengths: string[];
  questions_to_ask: string[];
  positions_to_advocate: {
    position: string;
    rationale: string;
    support: string;
  }[];
  objection_responses: {
    objection: string;
    response_strategy: string;
    legal_authority: string;
    settlement_opportunity: string;
  }[];
  negotiation_leverage: {
    leverage_point: string;
    how_to_use: string;
  }[];
}

export interface ActionItem {
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
  category: string;
  task: string;
  description: string;
  due_date?: string;
  hours_remaining?: number;
  required_actions?: string[];
  responsible_party?: string[];
  blockers?: string[];
  estimated_hours?: number;
}

export interface ActionItemsResponse {
  case_id: string;
  generated_at: string;
  total_action_items: number;
  urgent_items: number;
  action_items: ActionItem[];
}

// ============================================================================
// REQUEST/RESPONSE TYPES
// ============================================================================

export interface CreateCaseRequest {
  case_number: string;
  case_name: string;
  case_type: CaseType;
  court_name?: string;
  jurisdiction?: string;
  judge_name?: string;
  filing_date?: string;
  description?: string;
}

export interface UpdateCaseRequest {
  case_name?: string;
  status?: CaseStatus;
  current_phase?: string;
  description?: string;
  notes?: string;
  tags?: string[];
}

export interface CreatePartyRequest {
  case_id: string;
  role: PartyRole;
  name: string;
  party_type?: string;
  email?: string;
  phone?: string;
  address?: string;
}

export interface CreateEventRequest {
  case_id: string;
  event_type: EventType;
  title: string;
  event_date: string;
  description?: string;
  location?: string;
  required_actions?: any[];
}

export interface CreateAssetRequest {
  case_id: string;
  asset_type: string;
  name: string;
  category?: string;
  description?: string;
  estimated_value?: number;
  status?: AssetStatus;
}

export interface CreateBiddingProcessRequest {
  case_id: string;
  asset_id: string;
  process_name: string;
  bidding_start_date: string;
  bidding_end_date: string;
  minimum_bid?: number;
  deposit_required?: boolean;
}

export interface SubmitBidRequest {
  bidder_id: string;
  amount: number;
  notes?: string;
}

export interface CreateObjectionRequest {
  case_id: string;
  objection_type: string;
  title: string;
  grounds: string;
  filed_by_party_id: string;
  filing_date: string;
  response_deadline?: string;
}

export interface CalculationRequest {
  calculation_type: "increment" | "deposit" | "credit_bid";
  params?: {
    current_bid?: number;
    bid_amount?: number;
    claim_amount?: number;
    secured_amount?: number;
  };
}

export interface CalculationResponse {
  calculation_type: string;
  bidding_process_id: string;
  result: {
    current_bid?: number;
    minimum_increment?: number;
    next_minimum_bid?: number;
    bid_amount?: number;
    required_deposit?: number;
    deposit_percentage?: number;
    max_credit_bid?: number;
    secured_claim?: number;
    total_claim?: number;
    asset_value?: number;
    deficiency_claim?: number;
    cash_required?: number;
  };
  calculated_at: string;
}
