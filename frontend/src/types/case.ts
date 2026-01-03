// Case Management Types

export interface Case {
  id: string;
  case_number: string;
  case_name: string;
  case_type: string;
  client_id: string;
  client_name: string;
  status: CaseStatus;
  priority: CasePriority;
  filed_date?: string;
  response_deadline?: string;
  court?: string;
  judge?: string;
  plaintiff?: string;
  defendant?: string;
  description?: string;
  amount_claimed?: number;
  defense_strategy?: DefenseStrategy;
  documents: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by: string;
  assigned_to?: string;
}

export enum CaseStatus {
  NEW = 'new',
  IN_PROGRESS = 'in_progress',
  AWAITING_RESPONSE = 'awaiting_response',
  DISCOVERY = 'discovery',
  MOTION_FILED = 'motion_filed',
  SETTLEMENT = 'settlement',
  TRIAL = 'trial',
  CLOSED = 'closed',
  DISMISSED = 'dismissed',
}

export enum CasePriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent',
}

export interface DefenseStrategy {
  primary_defenses: Defense[];
  secondary_defenses: Defense[];
  immediate_actions: string[];
  evidence_needed: string[];
  success_probability: string;
  negotiation_position: string;
  created_at: string;
  updated_at: string;
}

export interface Defense {
  name: string;
  description: string;
  strength: 'Strong' | 'Medium' | 'Weak';
  requirements: string[];
  how_to_assert: string;
}
