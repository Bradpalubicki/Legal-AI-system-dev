/**
 * k6 Load Testing Configuration
 *
 * Central configuration for all load testing scenarios
 */

export const config = {
  // Base URL for testing (override with K6_BASE_URL env var)
  baseUrl: __ENV.K6_BASE_URL || 'http://localhost:8000',

  // Frontend URL
  frontendUrl: __ENV.K6_FRONTEND_URL || 'http://localhost:3000',

  // Test user credentials
  testUser: {
    email: __ENV.K6_TEST_USER_EMAIL || 'loadtest@example.com',
    password: __ENV.K6_TEST_USER_PASSWORD || 'LoadTest123!',
  },

  // API endpoints
  endpoints: {
    health: '/health',
    healthDatabase: '/health/database',
    healthSystem: '/health/system',
    auth: {
      login: '/api/auth/login',
      register: '/api/auth/register',
      logout: '/api/auth/logout',
      me: '/api/auth/me',
    },
    documents: {
      list: '/api/documents',
      upload: '/api/documents/upload',
      get: (id) => `/api/documents/${id}`,
      analyze: (id) => `/api/documents/${id}/analyze`,
      delete: (id) => `/api/documents/${id}`,
    },
    cases: {
      list: '/api/cases',
      create: '/api/cases',
      get: (id) => `/api/cases/${id}`,
      update: (id) => `/api/cases/${id}`,
    },
    search: {
      documents: '/api/search/documents',
      cases: '/api/search/cases',
    },
  },

  // Thresholds for test pass/fail
  thresholds: {
    // 95% of requests should complete within 2s
    http_req_duration_p95: 2000,

    // 99% of requests should complete within 5s
    http_req_duration_p99: 5000,

    // Error rate should be less than 1%
    http_req_failed_rate: 0.01,

    // Successful requests should be > 99%
    http_req_success_rate: 0.99,
  },

  // Test data
  testData: {
    // Sample document for upload testing
    sampleDocument: open('./test-files/sample-document.txt', 'b'),

    // Sample PDF for testing
    samplePdf: open('./test-files/sample-document.pdf', 'b'),

    // Test cases
    sampleCase: {
      title: 'Load Test Case',
      description: 'Case created during load testing',
      caseNumber: `LOAD-TEST-${Date.now()}`,
      status: 'open',
    },
  },
};

/**
 * Get common HTTP options
 */
export function getHttpOptions(token = null) {
  const options = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-load-test/1.0',
    },
    tags: {
      name: 'api-request',
    },
  };

  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }

  return options;
}

/**
 * Get multipart form options for file uploads
 */
export function getMultipartOptions(token = null) {
  const options = {
    headers: {
      'User-Agent': 'k6-load-test/1.0',
    },
    tags: {
      name: 'file-upload',
    },
  };

  if (token) {
    options.headers['Authorization'] = `Bearer ${token}`;
  }

  return options;
}

export default config;
