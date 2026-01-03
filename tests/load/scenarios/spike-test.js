/**
 * Spike Test - Sudden Traffic Surge
 *
 * Purpose: Test system behavior under sudden, extreme traffic spikes
 * Duration: 5 minutes
 * VUs: 10 → 500 → 10 (rapid changes)
 * RPS: ~100 → ~5000 → ~100
 *
 * Use Case: Verify auto-scaling response and system stability during traffic surges
 *
 * Usage:
 *   k6 run scenarios/spike-test.js
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
const spikeResponseTime = new Trend('spike_response_time');
const activeVUs = new Gauge('active_vus');
const failedRequests = new Counter('failed_requests');
const successfulRequests = new Counter('successful_requests');

// Test configuration - Spike test
export const options = {
  stages: [
    { duration: '30s', target: 10 },    // Low baseline
    { duration: '30s', target: 500 },   // SPIKE! Sudden surge
    { duration: '1m', target: 500 },    // Maintain spike
    { duration: '30s', target: 10 },    // Drop back down
    { duration: '30s', target: 10 },    // Recover
    { duration: '30s', target: 300 },   // Second spike
    { duration: '30s', target: 10 },    // Drop again
    { duration: '30s', target: 10 },    // Final recovery
  ],
  thresholds: {
    // Response times may be higher during spike
    'http_req_duration': ['p(95)<10000'], // 10s for P95 during spike

    // Error rate threshold
    'errors': ['rate<0.1'], // Less than 10% errors (higher tolerance for spike)
    'http_req_failed': ['rate<0.1'],

    // Spike-specific metrics
    'spike_response_time': ['p(50)<3000'], // Median should still be reasonable
  },
  tags: {
    test_type: 'spike',
  },
};

export function setup() {
  console.log('⚡ Starting Spike Test');
  console.log(`Target: ${config.baseUrl}`);
  console.log('Duration: 5 minutes');
  console.log('Pattern: 10 → 500 → 10 VUs (sudden spikes)');
  console.log('Goal: Test auto-scaling and stability under sudden load changes');

  const token = login();

  if (!token) {
    throw new Error('Failed to obtain authentication token');
  }

  return { token };
}

export default function (data) {
  const { token } = data;
  const startTime = Date.now();

  // Track active VUs
  activeVUs.add(__VU);

  // Quick, simple operations during spike
  const scenario = Math.random();

  try {
    if (scenario < 0.5) {
      // 50% - Quick reads
      quickReadsWorkflow(token);
    } else if (scenario < 0.8) {
      // 30% - Search operations
      searchWorkflow(token);
    } else {
      // 20% - Create operations
      createWorkflow(token);
    }

    // Track successful completion
    successfulRequests.add(1);

  } catch (e) {
    failedRequests.add(1);
    errorRate.add(1);
  }

  // Record response time for this iteration
  const duration = Date.now() - startTime;
  spikeResponseTime.add(duration);

  // Minimal sleep during spike test
  sleep(Math.random() * 1 + 0.5); // Random sleep 0.5-1.5 seconds
}

function quickReadsWorkflow(token) {
  group('Quick Reads', function () {
    // Fast read-only operations
    const responses = http.batch([
      ['GET', `${config.baseUrl}${config.endpoints.health}`, null, getHttpOptions()],
      ['GET', `${config.baseUrl}${config.endpoints.documents.list}?page=1&limit=10`, null, getHttpOptions(token)],
      ['GET', `${config.baseUrl}${config.endpoints.cases.list}?page=1&limit=10`, null, getHttpOptions(token)],
    ]);

    responses.forEach((response, index) => {
      const success = check(response, {
        'quick read successful': (r) => r.status === 200,
        'response under 5s': (r) => r.timings.duration < 5000,
      });

      errorRate.add(!success);
      apiDuration.add(response.timings.duration);
    });
  });
}

function searchWorkflow(token) {
  group('Search Workflow', function () {
    const query = generateSearchQuery();

    const response = http.get(
      `${config.baseUrl}${config.endpoints.search.documents}?q=${encodeURIComponent(query)}&limit=20`,
      getHttpOptions(token)
    );

    const success = check(response, {
      'search successful': (r) => r.status === 200,
      'search under 8s': (r) => r.timings.duration < 8000,
    });

    errorRate.add(!success);
    apiDuration.add(response.timings.duration);
  });
}

function createWorkflow(token) {
  group('Create Workflow', function () {
    // Simple create operation
    const docData = generateDocument();
    const response = http.post(
      `${config.baseUrl}${config.endpoints.documents.list}`,
      JSON.stringify(docData),
      getHttpOptions(token)
    );

    const success = check(response, {
      'create successful': (r) => r.status === 201 || r.status === 200 || r.status === 503,
      // Allow 503 during extreme spike - service should gracefully degrade
    });

    errorRate.add(!success);
    apiDuration.add(response.timings.duration);

    // If we got rate limited or service unavailable, that's expected during spike
    if (response.status === 429 || response.status === 503) {
      console.log(`Expected degradation: ${response.status} during spike`);
    }
  });
}

export function teardown(data) {
  console.log('🏁 Spike Test Complete');
  console.log('='.repeat(50));
  console.log(`Successful Requests: ${successfulRequests.count}`);
  console.log(`Failed Requests: ${failedRequests.count}`);
  console.log('='.repeat(50));

  const successRate = successfulRequests.count / (successfulRequests.count + failedRequests.count);
  console.log(`Success Rate: ${(successRate * 100).toFixed(2)}%`);

  if (successRate < 0.9) {
    console.log('⚠️  System struggled with traffic spikes');
    console.log('Recommendations:');
    console.log('  - Review auto-scaling configuration');
    console.log('  - Check if HPA triggers are set correctly');
    console.log('  - Consider implementing request queuing');
    console.log('  - Add rate limiting to protect backend');
  } else {
    console.log('✅ System handled traffic spikes well');
    console.log('Auto-scaling appears to be working correctly');
  }
}
