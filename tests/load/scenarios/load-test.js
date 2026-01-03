/**
 * Load Test - Average Load
 *
 * Purpose: Test system performance under average expected load
 * Duration: 10 minutes
 * VUs: 50-100 virtual users
 * RPS: ~500-1000 requests per second
 *
 * Use Case: Performance testing before major releases
 *
 * Usage:
 *   k6 run scenarios/load-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { config, getHttpOptions, getMultipartOptions } from '../config.js';
import { login } from '../utils/auth.js';
import { generateCase, generateDocument, generateSearchQuery } from '../utils/dataGenerator.js';

// Custom metrics
const errorRate = new Rate('errors');
const apiDuration = new Trend('api_duration');
const documentUploads = new Counter('document_uploads');
const caseCreations = new Counter('case_creations');
const searchQueries = new Counter('search_queries');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 100 },  // Ramp up to 100 users
    { duration: '2m', target: 100 },  // Stay at 100 users
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    // Performance requirements
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'],

    // Error rate requirements
    'errors': ['rate<0.01'], // Less than 1% errors
    'http_req_failed': ['rate<0.01'],

    // Throughput requirements
    'http_reqs': ['rate>500'], // At least 500 RPS
  },
  tags: {
    test_type: 'load',
  },
};

export function setup() {
  console.log('⚡ Starting Load Test');
  console.log(`Target: ${config.baseUrl}`);
  console.log('Duration: 10 minutes');
  console.log('Peak VUs: 100');

  const token = login();

  if (!token) {
    throw new Error('Failed to obtain authentication token');
  }

  return { token };
}

export default function (data) {
  const { token } = data;

  // Simulate realistic user behavior
  const scenario = Math.random();

  if (scenario < 0.4) {
    // 40% - Document workflow
    documentWorkflow(token);
  } else if (scenario < 0.7) {
    // 30% - Case management workflow
    caseManagementWorkflow(token);
  } else if (scenario < 0.9) {
    // 20% - Search workflow
    searchWorkflow(token);
  } else {
    // 10% - Mixed workflow
    mixedWorkflow(token);
  }

  sleep(Math.random() * 3 + 2); // Random sleep 2-5 seconds
}

function documentWorkflow(token) {
  group('Document Workflow', function () {
    // List documents
    let response = http.get(
      `${config.baseUrl}${config.endpoints.documents.list}?page=1&limit=20`,
      getHttpOptions(token)
    );

    check(response, {
      'list documents successful': (r) => r.status === 200,
    });

    sleep(1);

    // Create document metadata
    const docData = generateDocument();
    response = http.post(
      `${config.baseUrl}${config.endpoints.documents.list}`,
      JSON.stringify(docData),
      getHttpOptions(token)
    );

    const created = check(response, {
      'create document successful': (r) => r.status === 201 || r.status === 200,
    });

    if (created) {
      documentUploads.add(1);

      try {
        const doc = JSON.parse(response.body);
        const docId = doc.id || doc.document_id;

        if (docId) {
          sleep(1);

          // Get document details
          response = http.get(
            `${config.baseUrl}${config.endpoints.documents.get(docId)}`,
            getHttpOptions(token)
          );

          check(response, {
            'get document successful': (r) => r.status === 200,
          });
        }
      } catch (e) {
        console.error('Error parsing document response:', e);
      }
    }
  });
}

function caseManagementWorkflow(token) {
  group('Case Management Workflow', function () {
    // List cases
    let response = http.get(
      `${config.baseUrl}${config.endpoints.cases.list}?page=1&limit=20`,
      getHttpOptions(token)
    );

    check(response, {
      'list cases successful': (r) => r.status === 200,
    });

    sleep(1);

    // Create case
    const caseData = generateCase();
    response = http.post(
      `${config.baseUrl}${config.endpoints.cases.create}`,
      JSON.stringify(caseData),
      getHttpOptions(token)
    );

    const created = check(response, {
      'create case successful': (r) => r.status === 201 || r.status === 200,
    });

    if (created) {
      caseCreations.add(1);

      try {
        const caseObj = JSON.parse(response.body);
        const caseId = caseObj.id || caseObj.case_id;

        if (caseId) {
          sleep(1);

          // Get case details
          response = http.get(
            `${config.baseUrl}${config.endpoints.cases.get(caseId)}`,
            getHttpOptions(token)
          );

          check(response, {
            'get case successful': (r) => r.status === 200,
          });

          sleep(1);

          // Update case
          const updateData = { ...caseData, status: 'in_progress' };
          response = http.put(
            `${config.baseUrl}${config.endpoints.cases.update(caseId)}`,
            JSON.stringify(updateData),
            getHttpOptions(token)
          );

          check(response, {
            'update case successful': (r) => r.status === 200,
          });
        }
      } catch (e) {
        console.error('Error parsing case response:', e);
      }
    }
  });
}

function searchWorkflow(token) {
  group('Search Workflow', function () {
    const query = generateSearchQuery();

    // Search documents
    let response = http.get(
      `${config.baseUrl}${config.endpoints.search.documents}?q=${encodeURIComponent(query)}`,
      getHttpOptions(token)
    );

    check(response, {
      'search documents successful': (r) => r.status === 200,
    });

    searchQueries.add(1);

    sleep(1);

    // Search cases
    response = http.get(
      `${config.baseUrl}${config.endpoints.search.cases}?q=${encodeURIComponent(query)}`,
      getHttpOptions(token)
    );

    check(response, {
      'search cases successful': (r) => r.status === 200,
    });

    searchQueries.add(1);
  });
}

function mixedWorkflow(token) {
  group('Mixed Workflow', function () {
    // Health check
    http.get(`${config.baseUrl}${config.endpoints.health}`, getHttpOptions());

    sleep(0.5);

    // List documents
    http.get(`${config.baseUrl}${config.endpoints.documents.list}`, getHttpOptions(token));

    sleep(0.5);

    // List cases
    http.get(`${config.baseUrl}${config.endpoints.cases.list}`, getHttpOptions(token));

    sleep(0.5);

    // Search
    const query = generateSearchQuery();
    http.get(
      `${config.baseUrl}${config.endpoints.search.documents}?q=${encodeURIComponent(query)}`,
      getHttpOptions(token)
    );
  });
}

export function teardown(data) {
  console.log('🏁 Load Test Complete');
  console.log(`Document Uploads: ${documentUploads.count}`);
  console.log(`Case Creations: ${caseCreations.count}`);
  console.log(`Search Queries: ${searchQueries.count}`);
}
