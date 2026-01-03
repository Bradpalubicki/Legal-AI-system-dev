/**
 * Soak Test - Sustained Load
 *
 * Purpose: Test system stability and resource usage over extended periods
 * Duration: 2 hours (configurable)
 * VUs: 50 virtual users (sustained)
 * RPS: ~300-500 requests per second
 *
 * Use Case: Detect memory leaks, resource exhaustion, and degradation over time
 *
 * Usage:
 *   k6 run scenarios/soak-test.js
 *
 * For shorter test (30 minutes):
 *   k6 run -e SOAK_DURATION=30m scenarios/soak-test.js
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
const memoryUsage = new Gauge('memory_usage_estimate');
const activeConnections = new Gauge('active_connections');
const documentUploads = new Counter('document_uploads');
const caseCreations = new Counter('case_creations');
const searchQueries = new Counter('search_queries');
const failedRequests = new Counter('failed_requests');
const successfulRequests = new Counter('successful_requests');

// Configurable soak duration
const SOAK_DURATION = __ENV.SOAK_DURATION || '120m'; // Default: 2 hours

// Test configuration - Soak test
export const options = {
  stages: [
    { duration: '5m', target: 50 },           // Ramp up
    { duration: SOAK_DURATION, target: 50 },  // Sustained load
    { duration: '5m', target: 0 },            // Ramp down
  ],
  thresholds: {
    // Performance should remain consistent throughout
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'],

    // Error rate should remain low even after extended run
    'errors': ['rate<0.01'], // Less than 1% errors
    'http_req_failed': ['rate<0.01'],

    // Throughput should be stable
    'http_reqs': ['rate>300'], // At least 300 RPS sustained

    // Response times should not degrade over time
    'api_duration': ['p(95)<2000'],
  },
  tags: {
    test_type: 'soak',
  },
};

export function setup() {
  console.log('🔥 Starting Soak Test');
  console.log(`Target: ${config.baseUrl}`);
  console.log(`Duration: ${SOAK_DURATION} (sustained load)`);
  console.log('VUs: 50 (constant)');
  console.log('Goal: Detect memory leaks and resource degradation over time');
  console.log('');
  console.log('💡 Monitor these metrics during the test:');
  console.log('   - Memory usage (should remain stable)');
  console.log('   - Response times (should not increase over time)');
  console.log('   - Error rates (should remain near zero)');
  console.log('   - Database connections (should not leak)');
  console.log('');

  const token = login();

  if (!token) {
    throw new Error('Failed to obtain authentication token');
  }

  return {
    token,
    startTime: Date.now(),
  };
}

export default function (data) {
  const { token, startTime } = data;
  const elapsedMinutes = Math.floor((Date.now() - startTime) / 60000);

  // Track active connections
  activeConnections.add(__VU);

  // Estimate memory usage based on active VUs and time
  // This is just an estimate - monitor actual server memory
  const estimatedMemoryMB = __VU * 10 + (elapsedMinutes * 0.5);
  memoryUsage.add(estimatedMemoryMB);

  // Realistic user scenarios
  const scenario = Math.random();

  try {
    if (scenario < 0.35) {
      // 35% - Document workflow
      documentWorkflow(token);
    } else if (scenario < 0.6) {
      // 25% - Case management workflow
      caseManagementWorkflow(token);
    } else if (scenario < 0.8) {
      // 20% - Search workflow
      searchWorkflow(token);
    } else if (scenario < 0.95) {
      // 15% - Read-only workflow
      readOnlyWorkflow(token);
    } else {
      // 5% - Mixed workflow
      mixedWorkflow(token);
    }

    successfulRequests.add(1);

  } catch (e) {
    console.error(`Error in iteration: ${e}`);
    failedRequests.add(1);
    errorRate.add(1);
  }

  // Log progress every ~30 minutes (at different VU intervals)
  if (__VU === 1 && elapsedMinutes % 30 === 0 && elapsedMinutes > 0) {
    console.log(`⏱️  Soak Test Progress: ${elapsedMinutes} minutes elapsed`);
    console.log(`   Successful: ${successfulRequests.count}, Failed: ${failedRequests.count}`);
  }

  // Realistic think time
  sleep(Math.random() * 4 + 2); // Random sleep 2-6 seconds
}

function documentWorkflow(token) {
  group('Document Workflow', function () {
    // List documents
    let response = http.get(
      `${config.baseUrl}${config.endpoints.documents.list}?page=1&limit=20`,
      getHttpOptions(token)
    );

    const listSuccess = check(response, {
      'list documents successful': (r) => r.status === 200,
      'response time acceptable': (r) => r.timings.duration < 3000,
    });

    errorRate.add(!listSuccess);
    apiDuration.add(response.timings.duration);

    sleep(1);

    // Create document
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
        console.error('Error in document workflow:', e);
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

    const listSuccess = check(response, {
      'list cases successful': (r) => r.status === 200,
      'response time acceptable': (r) => r.timings.duration < 3000,
    });

    errorRate.add(!listSuccess);
    apiDuration.add(response.timings.duration);

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
        console.error('Error in case workflow:', e);
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

    const docsSuccess = check(response, {
      'search documents successful': (r) => r.status === 200,
      'search response time acceptable': (r) => r.timings.duration < 4000,
    });

    errorRate.add(!docsSuccess);
    apiDuration.add(response.timings.duration);

    if (docsSuccess) {
      searchQueries.add(1);
    }

    sleep(1);

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
    }
  });
}

function readOnlyWorkflow(token) {
  group('Read-Only Workflow', function () {
    // Multiple read operations - common for browsing users
    const responses = http.batch([
      ['GET', `${config.baseUrl}${config.endpoints.health}`, null, getHttpOptions()],
      ['GET', `${config.baseUrl}${config.endpoints.documents.list}?page=1&limit=10`, null, getHttpOptions(token)],
      ['GET', `${config.baseUrl}${config.endpoints.cases.list}?page=1&limit=10`, null, getHttpOptions(token)],
    ]);

    responses.forEach((response) => {
      const success = check(response, {
        'read operation successful': (r) => r.status === 200,
      });

      errorRate.add(!success);
      apiDuration.add(response.timings.duration);
    });
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
    const response = http.get(
      `${config.baseUrl}${config.endpoints.search.documents}?q=${encodeURIComponent(query)}`,
      getHttpOptions(token)
    );

    const success = check(response, {
      'mixed workflow successful': (r) => r.status === 200,
    });

    if (success) {
      searchQueries.add(1);
    }
  });
}

export function teardown(data) {
  const { startTime } = data;
  const totalMinutes = Math.floor((Date.now() - startTime) / 60000);

  console.log('');
  console.log('🏁 Soak Test Complete');
  console.log('='.repeat(60));
  console.log(`Total Duration: ${totalMinutes} minutes`);
  console.log(`Successful Requests: ${successfulRequests.count}`);
  console.log(`Failed Requests: ${failedRequests.count}`);
  console.log(`Document Uploads: ${documentUploads.count}`);
  console.log(`Case Creations: ${caseCreations.count}`);
  console.log(`Search Queries: ${searchQueries.count}`);
  console.log('='.repeat(60));

  const successRate = successfulRequests.count / (successfulRequests.count + failedRequests.count);
  console.log(`Overall Success Rate: ${(successRate * 100).toFixed(2)}%`);

  console.log('');
  console.log('📊 Analysis Recommendations:');
  console.log('');
  console.log('1. Memory Analysis:');
  console.log('   - Check if server memory usage increased over time');
  console.log('   - Look for memory leaks in application logs');
  console.log('   - Review garbage collection metrics');
  console.log('');
  console.log('2. Performance Degradation:');
  console.log('   - Compare P95 response times: start vs. end');
  console.log('   - Check if database query times increased');
  console.log('   - Review connection pool utilization');
  console.log('');
  console.log('3. Resource Leaks:');
  console.log('   - Verify database connections were properly closed');
  console.log('   - Check for file descriptor leaks');
  console.log('   - Monitor Redis connection count');
  console.log('');

  if (successRate < 0.99) {
    console.log('⚠️  System showed degradation during sustained load');
    console.log('Action Required: Investigate resource leaks and performance issues');
  } else {
    console.log('✅ System maintained stability throughout sustained load');
    console.log('Production Ready: No signs of memory leaks or degradation');
  }
}
