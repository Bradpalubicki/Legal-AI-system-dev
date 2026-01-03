/**
 * Stress Test - Peak Load
 *
 * Purpose: Test system performance under extreme load and find breaking points
 * Duration: 15 minutes
 * VUs: 100-500 virtual users
 * RPS: ~2000-5000 requests per second
 *
 * Use Case: Capacity planning and system limits testing
 *
 * Usage:
 *   k6 run scenarios/stress-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { config, getHttpOptions } from '../config.js';
import { login } from '../utils/auth.js';
import { generateCase, generateDocument, generateSearchQuery } from '../utils/dataGenerator.js';

// Custom metrics
const errorRate = new Rate('errors');
const apiDuration = new Trend('api_duration');
const activeVUs = new Gauge('active_vus');
const requestRate = new Rate('request_rate');
const documentUploads = new Counter('document_uploads');
const caseCreations = new Counter('case_creations');
const searchQueries = new Counter('search_queries');
const failedRequests = new Counter('failed_requests');

// Test configuration - Stress test
export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up to baseline
    { duration: '3m', target: 200 },   // Increase to 2x load
    { duration: '2m', target: 300 },   // Push to 3x load
    { duration: '3m', target: 500 },   // Maximum stress
    { duration: '2m', target: 500 },   // Sustain peak
    { duration: '2m', target: 300 },   // Step down
    { duration: '1m', target: 0 },     // Recovery
  ],
  thresholds: {
    // More relaxed thresholds for stress test
    'http_req_duration': ['p(95)<5000', 'p(99)<10000'],

    // Allow higher error rate under stress
    'errors': ['rate<0.05'], // Less than 5% errors
    'http_req_failed': ['rate<0.05'],

    // Throughput requirements
    'http_reqs': ['rate>1000'], // At least 1000 RPS at peak
  },
  tags: {
    test_type: 'stress',
  },
};

export function setup() {
  console.log('💥 Starting Stress Test');
  console.log(`Target: ${config.baseUrl}`);
  console.log('Duration: 15 minutes');
  console.log('Peak VUs: 500');
  console.log('Goal: Find system breaking points');

  const token = login();

  if (!token) {
    throw new Error('Failed to obtain authentication token');
  }

  return { token };
}

export default function (data) {
  const { token } = data;

  // Track active VUs
  activeVUs.add(__VU);

  // More aggressive scenarios - less sleep time
  const scenario = Math.random();

  if (scenario < 0.4) {
    // 40% - Document workflow
    documentWorkflow(token);
  } else if (scenario < 0.7) {
    // 30% - Case management workflow
    caseManagementWorkflow(token);
  } else if (scenario < 0.85) {
    // 15% - Search workflow
    searchWorkflow(token);
  } else if (scenario < 0.95) {
    // 10% - Mixed workflow
    mixedWorkflow(token);
  } else {
    // 5% - Heavy workflow (multiple operations)
    heavyWorkflow(token);
  }

  // Shorter sleep for stress test
  sleep(Math.random() * 2 + 1); // Random sleep 1-3 seconds
}

function documentWorkflow(token) {
  group('Document Workflow', function () {
    // List documents
    let response = http.get(
      `${config.baseUrl}${config.endpoints.documents.list}?page=1&limit=50`,
      getHttpOptions(token)
    );

    const listSuccess = check(response, {
      'list documents successful': (r) => r.status === 200,
    });

    errorRate.add(!listSuccess);
    apiDuration.add(response.timings.duration);

    if (!listSuccess) {
      failedRequests.add(1);
      return;
    }

    sleep(0.5);

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

    errorRate.add(!created);

    if (created) {
      documentUploads.add(1);

      try {
        const doc = JSON.parse(response.body);
        const docId = doc.id || doc.document_id;

        if (docId) {
          sleep(0.5);

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
        failedRequests.add(1);
      }
    } else {
      failedRequests.add(1);
    }
  });
}

function caseManagementWorkflow(token) {
  group('Case Management Workflow', function () {
    // List cases
    let response = http.get(
      `${config.baseUrl}${config.endpoints.cases.list}?page=1&limit=50`,
      getHttpOptions(token)
    );

    const listSuccess = check(response, {
      'list cases successful': (r) => r.status === 200,
    });

    errorRate.add(!listSuccess);
    apiDuration.add(response.timings.duration);

    if (!listSuccess) {
      failedRequests.add(1);
      return;
    }

    sleep(0.5);

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

    errorRate.add(!created);

    if (created) {
      caseCreations.add(1);

      try {
        const caseObj = JSON.parse(response.body);
        const caseId = caseObj.id || caseObj.case_id;

        if (caseId) {
          sleep(0.5);

          // Get case details
          response = http.get(
            `${config.baseUrl}${config.endpoints.cases.get(caseId)}`,
            getHttpOptions(token)
          );

          check(response, {
            'get case successful': (r) => r.status === 200,
          });
        }
      } catch (e) {
        failedRequests.add(1);
      }
    } else {
      failedRequests.add(1);
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

    const docsSuccess = check(response, {
      'search documents successful': (r) => r.status === 200,
    });

    errorRate.add(!docsSuccess);

    if (docsSuccess) {
      searchQueries.add(1);
    } else {
      failedRequests.add(1);
    }

    sleep(0.3);

    // Search cases
    response = http.get(
      `${config.baseUrl}${config.endpoints.search.cases}?q=${encodeURIComponent(query)}`,
      getHttpOptions(token)
    );

    const casesSuccess = check(response, {
      'search cases successful': (r) => r.status === 200,
    });

    errorRate.add(!casesSuccess);

    if (casesSuccess) {
      searchQueries.add(1);
    } else {
      failedRequests.add(1);
    }
  });
}

function mixedWorkflow(token) {
  group('Mixed Workflow', function () {
    // Batch requests
    const responses = http.batch([
      ['GET', `${config.baseUrl}${config.endpoints.health}`, null, getHttpOptions()],
      ['GET', `${config.baseUrl}${config.endpoints.documents.list}`, null, getHttpOptions(token)],
      ['GET', `${config.baseUrl}${config.endpoints.cases.list}`, null, getHttpOptions(token)],
    ]);

    responses.forEach((response, index) => {
      const success = check(response, {
        'batch request successful': (r) => r.status === 200,
      });

      errorRate.add(!success);

      if (!success) {
        failedRequests.add(1);
      }
    });
  });
}

function heavyWorkflow(token) {
  group('Heavy Workflow', function () {
    // Simulate a power user doing many operations

    // 1. List both documents and cases
    const responses = http.batch([
      ['GET', `${config.baseUrl}${config.endpoints.documents.list}?page=1&limit=100`, null, getHttpOptions(token)],
      ['GET', `${config.baseUrl}${config.endpoints.cases.list}?page=1&limit=100`, null, getHttpOptions(token)],
    ]);

    responses.forEach((response) => {
      errorRate.add(response.status !== 200);
    });

    sleep(0.5);

    // 2. Create multiple documents
    for (let i = 0; i < 3; i++) {
      const docData = generateDocument();
      const response = http.post(
        `${config.baseUrl}${config.endpoints.documents.list}`,
        JSON.stringify(docData),
        getHttpOptions(token)
      );

      const created = check(response, {
        'bulk create successful': (r) => r.status === 201 || r.status === 200,
      });

      if (created) {
        documentUploads.add(1);
      } else {
        failedRequests.add(1);
      }

      sleep(0.2);
    }

    sleep(0.5);

    // 3. Perform multiple searches
    for (let i = 0; i < 3; i++) {
      const query = generateSearchQuery();
      const response = http.get(
        `${config.baseUrl}${config.endpoints.search.documents}?q=${encodeURIComponent(query)}`,
        getHttpOptions(token)
      );

      const success = check(response, {
        'search successful': (r) => r.status === 200,
      });

      if (success) {
        searchQueries.add(1);
      } else {
        failedRequests.add(1);
      }

      sleep(0.2);
    }
  });
}

export function teardown(data) {
  console.log('🏁 Stress Test Complete');
  console.log('='.repeat(50));
  console.log(`Document Uploads: ${documentUploads.count}`);
  console.log(`Case Creations: ${caseCreations.count}`);
  console.log(`Search Queries: ${searchQueries.count}`);
  console.log(`Failed Requests: ${failedRequests.count}`);
  console.log('='.repeat(50));

  if (failedRequests.count > 0) {
    console.log('⚠️  System experienced failures under stress');
    console.log('Review logs to identify bottlenecks');
  } else {
    console.log('✅ System handled stress load successfully');
  }
}
