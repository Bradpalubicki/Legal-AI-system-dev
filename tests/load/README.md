# k6 Load Testing Suite

Comprehensive load testing infrastructure for the Legal AI System using k6.

## Overview

This directory contains load testing scenarios designed to validate system performance, scalability, and reliability under various load conditions.

## Prerequisites

1. **Install k6**:
   ```bash
   # Windows (using Chocolatey)
   choco install k6

   # macOS (using Homebrew)
   brew install k6

   # Linux
   sudo gpg -k
   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6
   ```

2. **Verify installation**:
   ```bash
   k6 version
   ```

## Test Scenarios

### 1. Smoke Test (`scenarios/smoke-test.js`)
**Purpose**: Verify basic functionality under minimal load

- **Duration**: 1 minute
- **Virtual Users**: 1-5 VUs
- **Target RPS**: ~10 requests/second
- **When to Run**: Before every deployment

**Run**:
```bash
k6 run scenarios/smoke-test.js
```

**Expected Results**:
- ✅ All health checks pass
- ✅ P95 latency < 2s
- ✅ Error rate < 1%

---

### 2. Load Test (`scenarios/load-test.js`)
**Purpose**: Test performance under average expected load

- **Duration**: 10 minutes
- **Virtual Users**: 50-100 VUs
- **Target RPS**: ~500-1000 requests/second
- **When to Run**: Before major releases

**Run**:
```bash
k6 run scenarios/load-test.js
```

**Expected Results**:
- ✅ P95 latency < 2s
- ✅ P99 latency < 5s
- ✅ Error rate < 1%
- ✅ RPS > 500

**Workflows Tested**:
- 40% Document operations (list, create, retrieve)
- 30% Case management (CRUD operations)
- 20% Search operations
- 10% Mixed workflows

---

### 3. Stress Test (`scenarios/stress-test.js`)
**Purpose**: Find system breaking points and capacity limits

- **Duration**: 15 minutes
- **Virtual Users**: 100-500 VUs
- **Target RPS**: ~2000-5000 requests/second
- **When to Run**: Capacity planning exercises

**Run**:
```bash
k6 run scenarios/stress-test.js
```

**Expected Results**:
- ✅ P95 latency < 5s
- ✅ P99 latency < 10s
- ✅ Error rate < 5%
- ✅ System degrades gracefully

**What to Monitor**:
- CPU and memory usage on backend pods
- Database connection pool saturation
- Response time degradation patterns
- Auto-scaling trigger points

---

### 4. Spike Test (`scenarios/spike-test.js`)
**Purpose**: Test system response to sudden traffic surges

- **Duration**: 5 minutes
- **Virtual Users**: 10 → 500 → 10 (rapid changes)
- **Target RPS**: ~100 → ~5000 → ~100
- **When to Run**: Before major announcements or launches

**Run**:
```bash
k6 run scenarios/spike-test.js
```

**Expected Results**:
- ✅ P95 latency < 10s (during spike)
- ✅ Error rate < 10%
- ✅ Auto-scaling responds within 2 minutes
- ✅ System recovers after spike subsides

**What to Monitor**:
- Horizontal Pod Autoscaler (HPA) response time
- Rate limiting effectiveness
- Request queuing behavior
- Recovery time after spike

---

### 5. Soak Test (`scenarios/soak-test.js`)
**Purpose**: Detect memory leaks and degradation over extended periods

- **Duration**: 2 hours (default, configurable)
- **Virtual Users**: 50 VUs (sustained)
- **Target RPS**: ~300-500 requests/second
- **When to Run**: Before production deployment, monthly

**Run**:
```bash
# Default 2-hour test
k6 run scenarios/soak-test.js

# Shorter 30-minute test
k6 run -e SOAK_DURATION=30m scenarios/soak-test.js
```

**Expected Results**:
- ✅ P95 latency remains stable over time
- ✅ Error rate < 1%
- ✅ Memory usage doesn't continuously increase
- ✅ No connection leaks

**What to Monitor**:
- Memory usage trends (should be flat or sawtooth from GC)
- Response time trends (should remain constant)
- Database connection count (should be stable)
- File descriptor count
- Redis connection pool

---

## Configuration

### Environment Variables

Configure tests using environment variables:

```bash
# Backend URL
export K6_BASE_URL="http://localhost:8000"

# Frontend URL (for future browser tests)
export K6_FRONTEND_URL="http://localhost:3000"

# Test user credentials
export K6_TEST_USER_EMAIL="loadtest@example.com"
export K6_TEST_USER_PASSWORD="LoadTest123!"
```

Or pass inline:
```bash
k6 run -e K6_BASE_URL=http://api.example.com scenarios/load-test.js
```

### Test Configuration File

Central configuration is in `config.js`:
- Base URLs and endpoints
- Performance thresholds
- Test user credentials
- HTTP request options

## Test Data Generation

Test data is generated automatically using utilities in `utils/dataGenerator.js`:

- `generateCase()` - Random case data
- `generateDocument()` - Random document metadata
- `generateSearchQuery()` - Realistic search queries
- `generateEmail()` - Random email addresses
- `generateUser()` - Random user profiles

All generated data is clearly marked as test data with:
- Prefixes like "Load Test", "LOAD-TEST-"
- Metadata tags: `testRun: true`, `testDocument: true`

## Authentication

Authentication utilities in `utils/auth.js`:

- `login()` - Obtain JWT token
- `verifyToken()` - Validate token
- `logout()` - Invalidate token
- `register()` - Create test user

## Performance Thresholds

### Current Baselines

| Metric | Target | Critical |
|--------|--------|----------|
| P95 Latency | < 2s | < 5s |
| P99 Latency | < 5s | < 10s |
| Error Rate | < 1% | < 5% |
| Availability | > 99.9% | > 99% |
| RPS (Load Test) | > 500 | > 300 |

### Adjusting Thresholds

Edit thresholds in each test scenario's `options` object:

```javascript
export const options = {
  thresholds: {
    'http_req_duration': ['p(95)<2000', 'p(99)<5000'],
    'errors': ['rate<0.01'],
    'http_req_failed': ['rate<0.01'],
  },
};
```

## Running Tests in CI/CD

### GitHub Actions Example

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sundays at 2 AM
  workflow_dispatch:      # Manual trigger

jobs:
  smoke-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6

      - name: Run smoke test
        env:
          K6_BASE_URL: ${{ secrets.STAGING_API_URL }}
          K6_TEST_USER_EMAIL: ${{ secrets.LOAD_TEST_EMAIL }}
          K6_TEST_USER_PASSWORD: ${{ secrets.LOAD_TEST_PASSWORD }}
        run: |
          cd tests/load
          k6 run scenarios/smoke-test.js
```

## Interpreting Results

### k6 Output

k6 provides detailed metrics at the end of each test:

```
✓ list documents successful
✓ create document successful
✓ search documents successful

checks.........................: 99.85% ✓ 2995   ✗ 5
data_received..................: 15 MB  25 kB/s
data_sent......................: 5.2 MB 8.7 kB/s
http_req_duration..............: avg=487ms  min=102ms med=389ms max=2.1s  p(95)=1.2s  p(99)=1.8s
http_req_failed................: 0.16%  ✓ 5      ✗ 2995
http_reqs......................: 3000   5/s
iteration_duration.............: avg=5.2s   min=2.1s  med=4.8s  max=12s   p(95)=8.1s  p(99)=10s
iterations.....................: 600    1/s
vus............................: 100    min=0    max=100
```

### Key Metrics to Watch

1. **http_req_duration** - Response times
   - Focus on P95 and P99 percentiles
   - Average can be misleading

2. **http_req_failed** - Error rate
   - Should be < 1% for production readiness
   - Investigate any failures

3. **checks** - Assertion pass rate
   - Should be > 99%
   - Failed checks indicate functional issues

4. **http_reqs** - Throughput
   - Requests per second handled
   - Compare to target RPS

### Custom Metrics

Each test tracks custom metrics:

- `document_uploads` - Number of documents created
- `case_creations` - Number of cases created
- `search_queries` - Number of searches performed
- `errors` - Custom error tracking
- `api_duration` - API-specific response times

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   WARN[0000] Request Failed error="Get \"http://localhost:8000/health\": dial tcp [::1]:8000: connect: connection refused"
   ```
   **Solution**: Ensure backend is running on the specified URL

2. **Authentication Failures**
   ```
   WARN[0001] login successful................................: 0.00% ✓ 0  ✗ 1
   ```
   **Solution**: Verify test user credentials exist in database:
   ```bash
   # Create test user
   python -m backend.scripts.create_test_user
   ```

3. **High Error Rates**
   - Check backend logs for errors
   - Verify database connectivity
   - Check resource limits (CPU, memory)
   - Review rate limiting configuration

4. **Slow Response Times**
   - Check database query performance
   - Verify Redis cache is working
   - Review application logs for bottlenecks
   - Check network latency

### Debug Mode

Run k6 with verbose logging:
```bash
k6 run --verbose scenarios/smoke-test.js
```

## Test Data Cleanup

Load tests create test data that should be cleaned up periodically:

```bash
# Clean up test documents (PostgreSQL)
psql -d legal_ai_db -c "DELETE FROM documents WHERE metadata->>'testDocument' = 'true';"

# Clean up test cases
psql -d legal_ai_db -c "DELETE FROM cases WHERE metadata->>'testRun' = 'true';"

# Or use automated cleanup script (if available)
python -m backend.scripts.cleanup_test_data
```

## Best Practices

1. **Start Small**: Always run smoke test before larger tests
2. **Monitor Resources**: Watch CPU, memory, and database during tests
3. **Run Regularly**: Schedule weekly load tests to catch regressions
4. **Baseline Metrics**: Establish performance baselines and track trends
5. **Test in Staging**: Run heavy tests (stress, soak) in staging, not production
6. **Clean Up**: Remove test data after tests complete
7. **Document Results**: Keep records of test results for comparison

## Performance Baselines

Document your baseline performance metrics:

| Test Type | VUs | RPS | P95 Latency | P99 Latency | Error Rate |
|-----------|-----|-----|-------------|-------------|------------|
| Smoke | 5 | 10 | TBD | TBD | TBD |
| Load | 100 | 500-1000 | TBD | TBD | TBD |
| Stress | 500 | 2000-5000 | TBD | TBD | TBD |
| Spike | 10-500 | Variable | TBD | TBD | TBD |
| Soak | 50 | 300-500 | TBD | TBD | TBD |

**Note**: Run initial tests to establish your baseline metrics, then update this table.

## Next Steps

1. **Create Test User**: Set up dedicated load test user in database
2. **Run Baseline Tests**: Execute smoke and load tests to establish baselines
3. **Configure CI/CD**: Add load tests to GitHub Actions workflow
4. **Set Up Monitoring**: Configure Grafana dashboards for k6 metrics
5. **Schedule Regular Tests**: Set up weekly automated test runs
6. **Document Baselines**: Update this README with your performance baselines

## Additional Resources

- [k6 Documentation](https://k6.io/docs/)
- [k6 Best Practices](https://k6.io/docs/testing-guides/test-types/)
- [Performance Testing Guide](https://k6.io/docs/testing-guides/)
- [k6 Cloud (Optional)](https://k6.io/cloud/) - For distributed load testing

## Support

For questions or issues with load testing:
1. Check k6 documentation
2. Review backend application logs
3. Verify test environment configuration
4. Consult with DevOps team for infrastructure issues
