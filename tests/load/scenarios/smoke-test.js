/**
 * Smoke Test - Minimal Load
 *
 * Purpose: Verify the system works under minimal load
 * Duration: 1 minute
 * VUs: 1-5 virtual users
 * RPS: ~10 requests per second
 *
 * Use Case: Run before every deployment to verify basic functionality
 *
 * Usage:
 *   k6 run scenarios/smoke-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';
import { config, getHttpOptions } from '../config.js';
import { login } from '../utils/auth.js';

// Custom metrics
const errorRate = new Rate('errors');
const apiDuration = new Trend('api_duration');
const successfulRequests = new Counter('successful_requests');
const failedRequests = new Counter('failed_requests');

// Test configuration
export const options = {
  stages: [
    { duration: '30s', target: 5 },  // Ramp up to 5 users
    { duration: '30s', target: 5 },  // Stay at 5 users
  ],
  thresholds: {
    // 95% of requests should complete within 2s
    'http_req_duration': ['p(95)<2000'],

    // 99% of requests should complete within 5s
    'http_req_duration': ['p(99)<5000'],

    // Error rate should be less than 1%
    'errors': ['rate<0.01'],

    // At least 99% of requests should succeed
    'http_req_failed': ['rate<0.01'],
  },
  tags: {
    test_type: 'smoke',
  },
};

// Setup function - runs once before the test
export function setup() {
  console.log('🔥 Starting Smoke Test');
  console.log(`Target: ${config.baseUrl}`);

  // Verify the system is reachable
  const healthCheck = http.get(`${config.baseUrl}${config.endpoints.health}`);

  if (healthCheck.status !== 200) {
    throw new Error(`Health check failed: ${healthCheck.status}`);
  }

  console.log('✅ Health check passed');

  // Try to login and get token for authenticated requests
  const token = login();

  return { token };
}

// Main test function - runs for each virtual user
export default function (data) {
  const { token } = data;

  // Group 1: Health Checks
  group('Health Checks', function () {
    const responses = http.batch([
      ['GET', `${config.baseUrl}${config.endpoints.health}`, null, getHttpOptions()],
      ['GET', `${config.baseUrl}${config.endpoints.healthDatabase}`, null, getHttpOptions()],
      ['GET', `${config.baseUrl}${config.endpoints.healthSystem}`, null, getHttpOptions()],
    ]);

    responses.forEach((response) => {
      const passed = check(response, {
        'status is 200': (r) => r.status === 200,
        'response time < 1s': (r) => r.timings.duration < 1000,
      });

      errorRate.add(!passed);
      apiDuration.add(response.timings.duration);

      if (passed) {
        successfulRequests.add(1);
      } else {
        failedRequests.add(1);
      }
    });
  });

  sleep(1);

  // Group 2: Authentication (if we have a token)
  if (token) {
    group('Authentication', function () {
      const response = http.get(
        `${config.baseUrl}${config.endpoints.auth.me}`,
        getHttpOptions(token)
      );

      const passed = check(response, {
        'authenticated request successful': (r) => r.status === 200,
        'response time < 500ms': (r) => r.timings.duration < 500,
      });

      errorRate.add(!passed);
      apiDuration.add(response.timings.duration);

      if (passed) {
        successfulRequests.add(1);
      } else {
        failedRequests.add(1);
      }
    });

    sleep(1);

    // Group 3: API Endpoints
    group('API Endpoints', function () {
      // Test document listing
      const docsResponse = http.get(
        `${config.baseUrl}${config.endpoints.documents.list}`,
        getHttpOptions(token)
      );

      const docsPassed = check(docsResponse, {
        'documents list successful': (r) => r.status === 200,
        'documents response time < 1s': (r) => r.timings.duration < 1000,
      });

      errorRate.add(!docsPassed);
      apiDuration.add(docsResponse.timings.duration);

      if (docsPassed) {
        successfulRequests.add(1);
      } else {
        failedRequests.add(1);
      }

      sleep(1);

      // Test case listing
      const casesResponse = http.get(
        `${config.baseUrl}${config.endpoints.cases.list}`,
        getHttpOptions(token)
      );

      const casesPassed = check(casesResponse, {
        'cases list successful': (r) => r.status === 200,
        'cases response time < 1s': (r) => r.timings.duration < 1000,
      });

      errorRate.add(!casesPassed);
      apiDuration.add(casesResponse.timings.duration);

      if (casesPassed) {
        successfulRequests.add(1);
      } else {
        failedRequests.add(1);
      }
    });
  }

  sleep(2);
}

// Teardown function - runs once after the test
export function teardown(data) {
  console.log('🏁 Smoke Test Complete');
  console.log(`Successful Requests: ${successfulRequests.count}`);
  console.log(`Failed Requests: ${failedRequests.count}`);

  if (failedRequests.count > 0) {
    console.error('❌ Some requests failed - investigate before proceeding');
  } else {
    console.log('✅ All smoke tests passed - system is healthy');
  }
}
