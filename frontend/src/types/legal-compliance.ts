// Legal Compliance TypeScript Types for Frontend

export interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  role: UserRole | string;
  isActive?: boolean;
  isVerified?: boolean;
  createdAt?: string;
  lastLoginAt?: string;
  profileData?: UserProfile;
  // Backend snake_case properties (optional for compatibility)
  username?: string | null;
  full_name?: string | null;
  is_active?: boolean;
  is_verified?: boolean;
  is_admin?: boolean;
  created_at?: string;
  last_login_at?: string;
}

export interface UserProfile {
  barNumber?: string;
  jurisdiction: string;
  practiceAreas: string[];
  firmName?: string;
  phoneNumber?: string;
  address?: Address;
  licenseStatus: LicenseStatus;
  professionalCertifications: string[];
}

export interface Address {
  street: string;
  city: string;
  state: string;
  zipCode: string;
  country: string;
}

export enum UserRole {
  ATTORNEY = 'attorney',
  PARALEGAL = 'paralegal',
  CLIENT = 'client',
  PRO_SE = 'pro_se',
  ADMIN = 'admin'
}

export enum LicenseStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  RETIRED = 'retired',
  NOT_APPLICABLE = 'not_applicable'
}

// Disclaimer System Types
export enum DisclaimerType {
  NO_LEGAL_ADVICE = 'no_legal_advice',
  NO_ATTORNEY_CLIENT = 'no_attorney_client',
  JURISDICTION_WARNING = 'jurisdiction_warning',
  AI_LIMITATION = 'ai_limitation',
  ACCURACY_WARNING = 'accuracy_warning',
  PROFESSIONAL_REVIEW = 'professional_review',
  CONFIDENTIALITY_WARNING = 'confidentiality_warning',
  UPL_WARNING = 'upl_warning',
  DATA_SECURITY = 'data_security',
  BETA_DISCLAIMER = 'beta_disclaimer',
  THIRD_PARTY_CONTENT = 'third_party_content',
  TIME_SENSITIVE = 'time_sensitive',
  EMERGENCY_DISCLAIMER = 'emergency_disclaimer',
  COMPETENCE_REQUIREMENT = 'competence_requirement',
  PROFESSIONAL_RESPONSIBILITY = 'professional_responsibility',
  BILLING_TRANSPARENCY = 'billing_transparency',
  CLIENT_CONSENT = 'client_consent',
  AUDIT_TRAIL = 'audit_trail',
  GENERAL_WARNING = 'general_warning',
  EDUCATIONAL_CONTENT = 'educational_content'
}

export enum DisclaimerDisplayFormat {
  MODAL = 'modal',
  HEADER_BANNER = 'header_banner',
  FOOTER_BANNER = 'footer_banner',
  INLINE_TEXT = 'inline_text',
  TOOLTIP = 'tooltip',
  SIDEBAR_BANNER = 'sidebar_banner',
  POPUP = 'popup',
  WATERMARK = 'watermark'
}

export interface DisclaimerConfig {
  id: string;
  type: DisclaimerType;
  title: string;
  content: string;
  displayFormat: DisclaimerDisplayFormat;
  isRequired: boolean;
  showForRoles: UserRole[];
  context: string[];
  priority: number;
  isActive: boolean;
  requiresAcknowledgment: boolean;
  acknowledgeButtonText?: string;
  dismissible: boolean;
}

export interface DisclaimerAcknowledgment {
  id: string;
  userId: string;
  disclaimerId: string;
  acknowledgedAt: string;
  ipAddress: string;
  userAgent: string;
  context: string;
}

// Terms Acceptance Types
export enum DocumentType {
  TERMS_OF_SERVICE = 'terms_of_service',
  PRIVACY_POLICY = 'privacy_policy',
  ACCEPTABLE_USE_POLICY = 'acceptable_use_policy',
  DATA_PROCESSING_AGREEMENT = 'data_processing_agreement',
  PROFESSIONAL_SERVICES_AGREEMENT = 'professional_services_agreement'
}

export interface LegalDocument {
  id: string;
  type: DocumentType;
  title: string;
  content: string;
  version: string;
  effectiveDate: string;
  isActive: boolean;
  requiresAcceptance: boolean;
  previousVersions: LegalDocumentVersion[];
}

export interface LegalDocumentVersion {
  version: string;
  effectiveDate: string;
  content: string;
  changesSummary: string;
}

export interface TermsAcceptance {
  id: string;
  userId: string;
  documentId: string;
  documentVersion: string;
  acceptedAt: string;
  ipAddress: string;
  userAgent: string;
  isForced: boolean;
  acceptanceMethod: AcceptanceMethod;
}

export enum AcceptanceMethod {
  CLICK_THROUGH = 'click_through',
  ELECTRONIC_SIGNATURE = 'electronic_signature',
  FORCED_ACCEPTANCE = 'forced_acceptance',
  API_ACCEPTANCE = 'api_acceptance'
}

// Privilege Protection Types
export enum PrivilegeType {
  ATTORNEY_CLIENT = 'attorney_client',
  WORK_PRODUCT = 'work_product',
  COMMON_INTEREST = 'common_interest',
  SELF_EVALUATION = 'self_evaluation'
}

export interface PrivilegeAssertion {
  id: string;
  documentId: string;
  privilegeType: PrivilegeType;
  assertedBy: string;
  assertedAt: string;
  isActive: boolean;
  basis: string;
  relatedMatter?: string;
  confidentialityLevel: ConfidentialityLevel;
}

export enum ConfidentialityLevel {
  PUBLIC = 'public',
  INTERNAL = 'internal',
  CONFIDENTIAL = 'confidential',
  HIGHLY_CONFIDENTIAL = 'highly_confidential',
  ATTORNEY_EYES_ONLY = 'attorney_eyes_only'
}

// Authentication Types
export interface LoginRequest {
  email: string;
  password: string;
  mfaToken?: string;
}

export interface LoginResponse {
  accessToken: string;
  refreshToken: string;
  user: User;
  requiresMfa: boolean;
  complianceStatus: ComplianceStatus;
}

export interface ComplianceStatus {
  hasAcceptedTerms: boolean;
  hasAcceptedPrivacy: boolean;
  hasCompletedOnboarding: boolean;
  requiredActions: ComplianceAction[];
  lastComplianceCheck: string;
}

export interface ComplianceAction {
  type: ComplianceActionType;
  description: string;
  isBlocking: boolean;
  dueDate?: string;
  priority: ComplianceActionPriority;
}

export enum ComplianceActionType {
  ACCEPT_TERMS = 'accept_terms',
  ACCEPT_PRIVACY = 'accept_privacy',
  COMPLETE_PROFILE = 'complete_profile',
  VERIFY_CREDENTIALS = 'verify_credentials',
  ACKNOWLEDGE_DISCLAIMER = 'acknowledge_disclaimer',
  COMPLETE_TRAINING = 'complete_training'
}

export enum ComplianceActionPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// Attorney Verification Types
export interface AttorneyVerificationRequest {
  barNumber: string;
  jurisdiction: string;
  licenseYear: number;
  fullName: string;
  firmName?: string;
}

export interface AttorneyVerificationResponse {
  isVerified: boolean;
  verificationStatus: VerificationStatus;
  licenseStatus: LicenseStatus;
  disciplinaryStatus: DisciplinaryStatus;
  verifiedAt: string;
  expiresAt: string;
}

export enum VerificationStatus {
  PENDING = 'pending',
  VERIFIED = 'verified',
  FAILED = 'failed',
  EXPIRED = 'expired',
  MANUAL_REVIEW = 'manual_review'
}

export enum DisciplinaryStatus {
  GOOD_STANDING = 'good_standing',
  DISCIPLINARY_ACTION = 'disciplinary_action',
  SUSPENSION = 'suspension',
  DISBARRED = 'disbarred',
  UNKNOWN = 'unknown'
}

// Component Props Types
export interface DisclaimerBannerProps {
  disclaimer: DisclaimerConfig;
  onAcknowledge?: (disclaimerId: string) => void;
  onDismiss?: (disclaimerId: string) => void;
  className?: string;
}

export interface LegalWarningModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAccept: () => void;
  title: string;
  content: string;
  acceptButtonText?: string;
  severity: 'warning' | 'error' | 'info';
  isBlocking?: boolean;
}

export interface TermsAcceptanceModalProps {
  isOpen: boolean;
  documents: LegalDocument[];
  onAccept: (documentIds: string[]) => void;
  onDecline: () => void;
  isForced?: boolean;
}

export interface AttorneyVerificationFormProps {
  onSubmit: (data: AttorneyVerificationRequest) => void;
  onSkip?: () => void;
  isLoading?: boolean;
  error?: string;
}

// Hook Types
export interface UseComplianceReturn {
  complianceStatus: ComplianceStatus | null;
  isCompliant: boolean;
  pendingActions: ComplianceAction[];
  checkCompliance: () => Promise<void>;
  markActionComplete: (actionType: ComplianceActionType) => Promise<void>;
  isLoading: boolean;
  error: string | null;
}

export interface UseDisclaimersReturn {
  disclaimers: DisclaimerConfig[];
  acknowledgeDisclaimer: (disclaimerId: string, context?: string) => Promise<void>;
  getDisclaimersForContext: (context: string) => DisclaimerConfig[];
  isLoading: boolean;
  error: string | null;
}

export interface UseTermsAcceptanceReturn {
  documents: LegalDocument[];
  acceptTerms: (documentIds: string[]) => Promise<void>;
  checkAcceptanceStatus: (documentId: string) => boolean;
  forceAcceptanceCheck: () => Promise<ComplianceStatus>;
  isLoading: boolean;
  error: string | null;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  meta?: ApiMeta;
}

export interface ApiMeta {
  page?: number;
  limit?: number;
  total?: number;
  hasNext?: boolean;
  hasPrev?: boolean;
}

export interface ComplianceCheckResponse {
  userId: string;
  complianceStatus: ComplianceStatus;
  requiredActions: ComplianceAction[];
  blockedFeatures: string[];
  nextCheckDue: string;
}

// Form Validation Types
export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

export interface FormState<T> {
  data: T;
  errors: ValidationError[];
  isSubmitting: boolean;
  isValid: boolean;
  isDirty: boolean;
}

// Audit Trail Types
export interface AuditEvent {
  id: string;
  userId: string;
  eventType: AuditEventType;
  resourceType: string;
  resourceId: string;
  description: string;
  metadata: Record<string, any>;
  ipAddress: string;
  userAgent: string;
  timestamp: string;
}

export enum AuditEventType {
  LOGIN = 'login',
  LOGOUT = 'logout',
  TERMS_ACCEPTED = 'terms_accepted',
  DISCLAIMER_ACKNOWLEDGED = 'disclaimer_acknowledged',
  ATTORNEY_VERIFIED = 'attorney_verified',
  DOCUMENT_ACCESSED = 'document_accessed',
  PRIVILEGE_ASSERTED = 'privilege_asserted',
  COMPLIANCE_CHECK = 'compliance_check'
}

// Context Types for React
export interface AuthContextType {
  user: User | null;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: (redirectToHome?: boolean) => Promise<void>;
  refreshToken: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface ComplianceContextType {
  complianceStatus: ComplianceStatus | null;
  isCompliant: boolean;
  checkCompliance: () => Promise<void>;
  forceComplianceCheck: () => Promise<void>;
  isLoading: boolean;
  error: string | null;
}