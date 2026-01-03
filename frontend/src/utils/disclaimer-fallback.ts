/**
 * DISCLAIMER FALLBACK SYSTEM
 * 
 * Provides hardcoded disclaimers when disclaimer service is unavailable.
 * CRITICAL: This ensures disclaimers are ALWAYS present regardless of service status.
 */

export interface DisclaimerData {
  title: string;
  content: string[];
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  icon: string;
  color: string;
}

export interface DisclaimerResponse {
  disclaimer: DisclaimerData;
  metadata: {
    service_timestamp: string;
    page_path: string;
    disclaimer_type: string;
    service_healthy: boolean;
    fallback_used: boolean;
  };
  compliance: {
    mandatory: boolean;
    not_legal_advice: boolean;
    attorney_consultation_required: boolean;
    disclaimer_version: string;
  };
}

/**
 * FALLBACK DISCLAIMER TEMPLATES
 * These are hardcoded to ensure availability even if service fails
 */
const FALLBACK_DISCLAIMERS: Record<string, DisclaimerData> = {
  global: {
    title: 'IMPORTANT LEGAL NOTICE',
    content: [
      '⚖️ This system provides general information only and does NOT constitute legal advice.',
      '🚫 No attorney-client relationship is created by using this system.',
      '👨‍⚖️ Always consult with a qualified attorney licensed in your jurisdiction.',
      '📋 Laws vary by state and change frequently - verify current law with legal counsel.'
    ],
    severity: 'CRITICAL',
    icon: '⚠️',
    color: 'border-red-200 bg-red-50'
  },

  research: {
    title: 'Legal Research Disclaimer',
    content: [
      'Legal research is for informational purposes only and does NOT constitute legal advice.',
      'Information provided may be outdated, incomplete, or jurisdiction-specific.',
      'This is NOT a substitute for attorney consultation or professional legal research.',
      'Always verify legal information with qualified legal counsel before relying on it.'
    ],
    severity: 'HIGH',
    icon: '📚',
    color: 'border-blue-200 bg-blue-50'
  },

  contracts: {
    title: 'Contract Analysis Disclaimer',
    content: [
      'Contract analysis does NOT constitute legal review or legal advice.',
      'AI analysis may miss critical terms, obligations, or legal implications.',
      'Consult a qualified attorney before signing ANY legal agreement.',
      'Contract interpretation varies by jurisdiction and specific circumstances.'
    ],
    severity: 'CRITICAL',
    icon: '📋',
    color: 'border-orange-200 bg-orange-50'
  },

  dashboard: {
    title: 'Dashboard Information Disclaimer',
    content: [
      'Dashboard information is NOT legal advice and is for informational purposes only.',
      'Deadlines shown are estimates - always verify actual deadlines with the court.',
      'Case status information may be delayed or incomplete.',
      'Consult your attorney for official case status and deadline confirmations.'
    ],
    severity: 'HIGH',
    icon: '📊',
    color: 'border-red-200 bg-red-50'
  },

  analyze: {
    title: 'Document Analysis Disclaimer',
    content: [
      'Document analysis is for informational purposes only and is NOT legal advice.',
      'AI analysis may not identify all issues, risks, or legal implications.',
      'Results should not be relied upon for legal decisions or strategy.',
      'Always have important documents reviewed by qualified legal counsel.'
    ],
    severity: 'HIGH',
    icon: '🔍',
    color: 'border-purple-200 bg-purple-50'
  },

  'client-portal': {
    title: 'Client Portal Disclaimer',
    content: [
      'The client portal is for information sharing only and does NOT constitute legal advice.',
      'No attorney-client relationship is established through portal use.',
      'Communications through this portal are NOT privileged or confidential.',
      'Consult directly with qualified legal counsel for privileged attorney-client communications.'
    ],
    severity: 'HIGH',
    icon: '👥',
    color: 'border-blue-200 bg-blue-50'
  },

  admin: {
    title: 'Administrative Interface Disclaimer',
    content: [
      'Administrative functions are for system management only.',
      'Administrative access does NOT create attorney-client relationships or legal obligations.',
      'System data and analytics are for informational purposes only.',
      'Consult with qualified legal counsel regarding any legal matters or compliance issues.'
    ],
    severity: 'MEDIUM',
    icon: '⚙️',
    color: 'border-gray-200 bg-gray-50'
  },

  education: {
    title: 'Educational Content Disclaimer',
    content: [
      'Educational content is for general information only and does NOT constitute legal advice.',
      'Legal education materials may be outdated or not applicable to your jurisdiction.',
      'Educational content is NOT a substitute for formal legal education or attorney consultation.',
      'Always verify legal information with qualified legal counsel before making any legal decisions.'
    ],
    severity: 'MEDIUM',
    icon: '📖',
    color: 'border-purple-200 bg-purple-50'
  },

  mobile: {
    title: 'Mobile Application Disclaimer',
    content: [
      'Mobile access provides general information only and does NOT constitute legal advice.',
      'Mobile features are for convenience and do NOT create attorney-client relationships.',
      'Legal information on mobile may have limited functionality or outdated content.',
      'Always consult with qualified legal counsel for legal matters requiring professional advice.'
    ],
    severity: 'HIGH',
    icon: '📱',
    color: 'border-blue-200 bg-blue-50'
  },

  emergency: {
    title: '🚨 CRITICAL LEGAL DISCLAIMER',
    content: [
      '🚨 LEGAL NOTICE: This content is for informational purposes only and does NOT constitute legal advice.',
      '🚫 NO ATTORNEY-CLIENT RELATIONSHIP is created by accessing this information.',
      '⚖️ ALWAYS consult with a qualified attorney for legal advice specific to your situation.',
      '📋 This system provides general information only - not legal advice.'
    ],
    severity: 'CRITICAL',
    icon: '🚨',
    color: 'border-red-500 bg-red-100'
  }
};

/**
 * Determine disclaimer type from page path
 */
function determineDisclaimerType(pathname: string): string {
  const path = pathname.toLowerCase();
  
  if (path.includes('/research')) return 'research';
  if (path.includes('/contract')) return 'contracts';
  if (path.includes('/dashboard')) return 'dashboard';
  if (path.includes('/analy')) return 'analyze';
  if (path.includes('/client-portal')) return 'client-portal';
  if (path.includes('/admin')) return 'admin';
  if (path.includes('/education')) return 'education';
  if (path.includes('/mobile')) return 'mobile';
  
  return 'global';
}

/**
 * Get disclaimer from service with fallback
 */
export async function getDisclaimer(
  pathname: string = '/',
  disclaimerType?: string
): Promise<DisclaimerResponse> {
  
  const finalType = disclaimerType || determineDisclaimerType(pathname);
  
  try {
    // Try to get from disclaimer service first
    const response = await fetch(`http://localhost:8001/disclaimer/${finalType}?page_path=${encodeURIComponent(pathname)}`);
    
    if (response.ok) {
      const data = await response.json();
      console.log('[DISCLAIMER] Retrieved from service:', finalType);
      return data;
    } else {
      throw new Error(`Service returned ${response.status}`);
    }
    
  } catch (error) {
    console.warn('[DISCLAIMER] Service unavailable, using fallback:', error);
    
    // Use fallback disclaimer
    const disclaimerData = FALLBACK_DISCLAIMERS[finalType] || FALLBACK_DISCLAIMERS.emergency;
    
    return {
      disclaimer: disclaimerData,
      metadata: {
        service_timestamp: new Date().toISOString(),
        page_path: pathname,
        disclaimer_type: finalType,
        service_healthy: false,
        fallback_used: true
      },
      compliance: {
        mandatory: true,
        not_legal_advice: true,
        attorney_consultation_required: true,
        disclaimer_version: '2.1-fallback'
      }
    };
  }
}

/**
 * Health check for disclaimer service
 */
export async function checkDisclaimerServiceHealth(): Promise<{
  healthy: boolean;
  status: string;
  error?: string;
}> {
  try {
    const response = await fetch('http://localhost:8001/health', {
      method: 'GET',
      timeout: 5000
    } as RequestInit);
    
    if (response.ok) {
      const health = await response.json();
      return {
        healthy: true,
        status: health.status || 'unknown'
      };
    } else {
      return {
        healthy: false,
        status: 'service_error',
        error: `HTTP ${response.status}`
      };
    }
    
  } catch (error) {
    return {
      healthy: false,
      status: 'unavailable',
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

/**
 * Get all available disclaimers (with fallback)
 */
export async function getAllDisclaimers(): Promise<Record<string, DisclaimerData>> {
  try {
    const response = await fetch('http://localhost:8001/disclaimers/all');
    
    if (response.ok) {
      const data = await response.json();
      return data.disclaimers || FALLBACK_DISCLAIMERS;
    } else {
      throw new Error(`Service returned ${response.status}`);
    }
    
  } catch (error) {
    console.warn('[DISCLAIMER] Using fallback disclaimers due to service error:', error);
    return FALLBACK_DISCLAIMERS;
  }
}

/**
 * Emergency disclaimer for critical situations
 */
export function getEmergencyDisclaimer(): DisclaimerResponse {
  return {
    disclaimer: FALLBACK_DISCLAIMERS.emergency,
    metadata: {
      service_timestamp: new Date().toISOString(),
      page_path: '/emergency',
      disclaimer_type: 'emergency',
      service_healthy: false,
      fallback_used: true
    },
    compliance: {
      mandatory: true,
      not_legal_advice: true,
      attorney_consultation_required: true,
      disclaimer_version: '2.1-emergency'
    }
  };
}

/**
 * Validate that a disclaimer is properly structured
 */
export function validateDisclaimer(disclaimer: any): boolean {
  if (!disclaimer || typeof disclaimer !== 'object') return false;
  
  const required = ['title', 'content', 'severity'];
  return required.every(field => field in disclaimer);
}

export default {
  getDisclaimer,
  checkDisclaimerServiceHealth,
  getAllDisclaimers,
  getEmergencyDisclaimer,
  validateDisclaimer,
  FALLBACK_DISCLAIMERS
};