// Custom Hooks Export Index

// Existing hooks
export * from './useApi';

// Compliance hooks
export { useAuth, useAuthProvider, AuthContext } from './useAuth';
export { useCompliance } from './useCompliance';
export { useDisclaimers } from './useDisclaimers';
export { useTermsAcceptance } from './useTermsAcceptance';
export { useDisclaimerAcknowledgments } from './useDisclaimerAcknowledgments';
export { useAdminDisclaimers } from './useAdminDisclaimers';

// Idle timeout hook
export { useIdleTimeout } from './useIdleTimeout';
export type { IdleTimeoutConfig, IdleTimeoutState } from './useIdleTimeout';

export type {
  AuthContextType,
  UseComplianceReturn,
  UseDisclaimersReturn,
  UseTermsAcceptanceReturn
} from '../types/legal-compliance';
