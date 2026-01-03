/**
 * Credit System Types
 *
 * Types for user credit management and PACER document purchases
 */

export type TransactionType =
  | 'credit_purchase'      // User buys credits
  | 'document_purchase'    // User buys PACER document
  | 'refund'               // Credit refund
  | 'admin_adjustment'     // Admin adds/removes credits
  | 'bonus';               // Promotional bonus credits

export interface UserCredits {
  id: number;
  user_id: number;
  username: string;
  balance: number;          // Current credit balance (1 credit = $1.00)
  total_purchased: number;  // Lifetime total credits purchased
  total_spent: number;      // Lifetime total credits spent
  created_at: string;
  updated_at: string;
}

export interface CreditTransaction {
  id: number;
  user_credits_id: number;
  transaction_type: TransactionType;
  amount: number;           // Positive for additions, negative for deductions
  balance_after: number;    // Balance after transaction
  description: string | null;
  extra_data: string | null;  // JSON string for additional data
  payment_method: string | null;
  payment_id: string | null;
  document_purchase_id: number | null;
  created_at: string;
}

export type PurchaseStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface DocumentPurchase {
  id: number;
  user_credits_id: number;
  document_id: string | null;
  docket_id: string | null;
  court: string | null;
  case_number: string | null;
  document_number: number | null;
  cost_credits: number;
  pacer_cost: number | null;
  page_count: number | null;
  status: PurchaseStatus;
  recap_fetch_id: number | null;
  file_path: string | null;
  file_size: number | null;
  description: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

// API Request/Response types
export interface AddCreditsRequest {
  user_id: number;
  username: string;
  amount: number;
  payment_method: string;
  payment_id: string;
}

export interface PurchaseDocumentRequest {
  document_id: string;
  docket_id: string;
  court: string;
  case_number: string;
  document_number: number;
  estimated_cost: number;
}

export interface CreditStats {
  balance: number;
  total_purchased: number;
  total_spent: number;
  transaction_count: number;
  purchase_count: number;
  pending_purchases: number;
}
