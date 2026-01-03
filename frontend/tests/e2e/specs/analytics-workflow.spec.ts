import { test, expect } from '@playwright/test'

test.describe('Analytics and Reporting E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Use authentication state if available
    try {
      await page.context().addCookies([])
    } catch (error) {
      // Handle case where no auth state exists
    }
    
    await page.goto('/')
    
    // Wait for the application to load
    await page.waitForSelector('[data-testid="app-ready"], [data-testid="dashboard"]', { 
      timeout: 10000 
    })
  })

  test('dashboard overview and widgets', async ({ page }) => {
    // Navigate to analytics dashboard
    await page.click('text=Analytics')
    await expect(page).toHaveURL(/.*\/analytics/)
    
    // Wait for dashboard to load
    await expect(page.locator('[data-testid="analytics-dashboard"]')).toBeVisible()
    
    // Verify key metrics widgets are present
    await expect(page.locator('[data-testid="total-documents-widget"]')).toBeVisible()
    await expect(page.locator('[data-testid="active-cases-widget"]')).toBeVisible()
    await expect(page.locator('[data-testid="research-queries-widget"]')).toBeVisible()
    await expect(page.locator('[data-testid="ai-usage-widget"]')).toBeVisible()
    
    // Test widget interactivity
    await page.click('[data-testid="total-documents-widget"]')
    await expect(page.locator('[data-testid="documents-detail-modal"]')).toBeVisible()
    
    // Test modal content
    await expect(page.locator('[data-testid="document-breakdown-chart"]')).toBeVisible()
    await expect(page.locator('[data-testid="document-trend-chart"]')).toBeVisible()
    
    await page.click('[data-testid="modal-close"]')
    await expect(page.locator('[data-testid="documents-detail-modal"]')).toBeHidden()
    
    // Test time range selector
    await page.selectOption('[data-testid="time-range-selector"]', '30-days')
    
    // Wait for widgets to update
    await page.waitForTimeout(1000)
    
    // Verify data refresh
    await expect(page.locator('[data-testid="last-updated"]')).toBeVisible()
  })

  test('usage analytics and trends', async ({ page }) => {
    await page.goto('/analytics/usage')
    
    // Wait for usage analytics to load
    await expect(page.locator('[data-testid="usage-analytics"]')).toBeVisible()
    
    // Test user activity chart
    await expect(page.locator('[data-testid="user-activity-chart"]')).toBeVisible()
    
    // Test chart interactions
    const chartContainer = page.locator('[data-testid="user-activity-chart"]')
    await chartContainer.hover()
    
    // Verify tooltip appears on hover
    await expect(page.locator('[data-testid="chart-tooltip"]')).toBeVisible()
    
    // Test feature usage breakdown
    await page.click('[data-testid="feature-usage-tab"]')
    await expect(page.locator('[data-testid="feature-usage-chart"]')).toBeVisible()
    
    // Verify feature breakdown data
    await expect(page.locator('[data-testid="document-analysis-usage"]')).toBeVisible()
    await expect(page.locator('[data-testid="legal-research-usage"]')).toBeVisible()
    await expect(page.locator('[data-testid="citation-analysis-usage"]')).toBeVisible()
    
    // Test time-based filtering
    await page.selectOption('[data-testid="usage-timeframe"]', 'weekly')
    await page.waitForSelector('[data-testid="usage-chart-updated"]')
    
    // Test user segmentation
    await page.click('[data-testid="user-segments-tab"]')
    await expect(page.locator('[data-testid="user-segments-chart"]')).toBeVisible()
    
    // Verify segment data
    await expect(page.locator('[data-testid="attorneys-segment"]')).toBeVisible()
    await expect(page.locator('[data-testid="paralegals-segment"]')).toBeVisible()
    await expect(page.locator('[data-testid="clients-segment"]')).toBeVisible()
  })

  test('performance metrics and monitoring', async ({ page }) => {
    await page.goto('/analytics/performance')
    
    // Wait for performance metrics to load
    await expect(page.locator('[data-testid="performance-dashboard"]')).toBeVisible()
    
    // Test system performance metrics
    await expect(page.locator('[data-testid="response-time-chart"]')).toBeVisible()
    await expect(page.locator('[data-testid="error-rate-chart"]')).toBeVisible()
    await expect(page.locator('[data-testid="throughput-chart"]')).toBeVisible()
    
    // Test real-time monitoring
    await expect(page.locator('[data-testid="realtime-status"]')).toBeVisible()
    await expect(page.locator('[data-testid="active-sessions"]')).toBeVisible()
    
    // Test AI model performance
    await page.click('[data-testid="ai-performance-tab"]')
    await expect(page.locator('[data-testid="ai-response-times"]')).toBeVisible()
    await expect(page.locator('[data-testid="model-accuracy-metrics"]')).toBeVisible()
    
    // Test performance alerts
    await page.click('[data-testid="alerts-tab"]')
    await expect(page.locator('[data-testid="performance-alerts"]')).toBeVisible()
    
    // Test alert configuration
    await page.click('[data-testid="configure-alerts"]')
    await expect(page.locator('[data-testid="alert-config-modal"]')).toBeVisible()
    
    await page.fill('[data-testid="response-time-threshold"]', '5000')
    await page.fill('[data-testid="error-rate-threshold"]', '5')
    await page.click('[data-testid="save-alert-config"]')
    
    await expect(page.locator('text=Alert configuration saved')).toBeVisible()
  })

  test('document analytics and insights', async ({ page }) => {
    await page.goto('/analytics/documents')
    
    // Wait for document analytics to load
    await expect(page.locator('[data-testid="document-analytics"]')).toBeVisible()
    
    // Test document type distribution
    await expect(page.locator('[data-testid="document-type-chart"]')).toBeVisible()
    
    // Verify chart shows different document types
    await expect(page.locator('text=Contracts')).toBeVisible()
    await expect(page.locator('text=Legal Briefs')).toBeVisible()
    await expect(page.locator('text=Court Filings')).toBeVisible()
    
    // Test processing time analytics
    await page.click('[data-testid="processing-metrics-tab"]')
    await expect(page.locator('[data-testid="processing-time-chart"]')).toBeVisible()
    
    // Test AI analysis insights
    await page.click('[data-testid="ai-insights-tab"]')
    await expect(page.locator('[data-testid="sentiment-analysis-chart"]')).toBeVisible()
    await expect(page.locator('[data-testid="risk-assessment-chart"]')).toBeVisible()
    
    // Test document search analytics
    await page.click('[data-testid="search-analytics-tab"]')
    await expect(page.locator('[data-testid="search-frequency-chart"]')).toBeVisible()
    await expect(page.locator('[data-testid="popular-terms"]')).toBeVisible()
    
    // Test drill-down functionality
    const contractsSegment = page.locator('[data-testid="contracts-chart-segment"]')
    await contractsSegment.click()
    
    // Verify drill-down modal opens
    await expect(page.locator('[data-testid="contracts-detail-modal"]')).toBeVisible()
    await expect(page.locator('[data-testid="contract-subcategories"]')).toBeVisible()
    
    // Test export functionality
    const exportDownload = page.waitForEvent('download')
    
    await page.click('[data-testid="export-document-analytics"]')
    await page.selectOption('[data-testid="export-format"]', 'pdf')
    await page.click('[data-testid="confirm-export"]')
    
    const download = await exportDownload
    expect(download.suggestedFilename()).toContain('document-analytics')
  })

  test('case analytics and outcomes', async ({ page }) => {
    await page.goto('/analytics/cases')
    
    // Wait for case analytics to load
    await expect(page.locator('[data-testid="case-analytics"]')).toBeVisible()
    
    // Test case status overview
    await expect(page.locator('[data-testid="case-status-chart"]')).toBeVisible()
    
    // Verify different case statuses
    await expect(page.locator('text=Active')).toBeVisible()
    await expect(page.locator('text=Closed')).toBeVisible()
    await expect(page.locator('text=Pending')).toBeVisible()
    
    // Test case duration analytics
    await page.click('[data-testid="duration-analytics-tab"]')
    await expect(page.locator('[data-testid="case-duration-chart"]')).toBeVisible()
    
    // Test outcome analysis
    await page.click('[data-testid="outcomes-tab"]')
    await expect(page.locator('[data-testid="case-outcomes-chart"]')).toBeVisible()
    
    // Test practice area breakdown
    await page.click('[data-testid="practice-areas-tab"]')
    await expect(page.locator('[data-testid="practice-areas-chart"]')).toBeVisible()
    
    // Verify different practice areas
    await expect(page.locator('text=Corporate Law')).toBeVisible()
    await expect(page.locator('text=Litigation')).toBeVisible()
    await expect(page.locator('text=Contract Law')).toBeVisible()
    
    // Test case complexity analysis
    await page.click('[data-testid="complexity-tab"]')
    await expect(page.locator('[data-testid="complexity-metrics"]')).toBeVisible()
    
    // Test predictive analytics
    await page.click('[data-testid="predictions-tab"]')
    await expect(page.locator('[data-testid="outcome-predictions"]')).toBeVisible()
    await expect(page.locator('[data-testid="duration-predictions"]')).toBeVisible()
  })

  test('billing and financial analytics', async ({ page }) => {
    await page.goto('/analytics/billing')
    
    // Wait for billing analytics to load
    await expect(page.locator('[data-testid="billing-analytics"]')).toBeVisible()
    
    // Test revenue overview
    await expect(page.locator('[data-testid="revenue-chart"]')).toBeVisible()
    await expect(page.locator('[data-testid="total-revenue"]')).toBeVisible()
    
    // Test billable hours analysis
    await page.click('[data-testid="billable-hours-tab"]')
    await expect(page.locator('[data-testid="billable-hours-chart"]')).toBeVisible()
    
    // Test client billing breakdown
    await page.click('[data-testid="client-billing-tab"]')
    await expect(page.locator('[data-testid="client-billing-chart"]')).toBeVisible()
    
    // Test time tracking analytics
    await page.click('[data-testid="time-tracking-tab"]')
    await expect(page.locator('[data-testid="time-tracking-chart"]')).toBeVisible()
    
    // Test AI usage cost analysis
    await page.click('[data-testid="ai-costs-tab"]')
    await expect(page.locator('[data-testid="ai-cost-chart"]')).toBeVisible()
    await expect(page.locator('[data-testid="cost-breakdown"]')).toBeVisible()
    
    // Test profitability analysis
    await page.click('[data-testid="profitability-tab"]')
    await expect(page.locator('[data-testid="profitability-chart"]')).toBeVisible()
    
    // Test invoice analytics
    await page.click('[data-testid="invoices-tab"]')
    await expect(page.locator('[data-testid="invoice-status-chart"]')).toBeVisible()
    
    // Test financial forecasting
    await page.click('[data-testid="forecasting-tab"]')
    await expect(page.locator('[data-testid="revenue-forecast"]')).toBeVisible()
    await expect(page.locator('[data-testid="expense-forecast"]')).toBeVisible()
  })

  test('custom report generation', async ({ page }) => {
    await page.goto('/analytics/reports')
    
    // Wait for reports page to load
    await expect(page.locator('[data-testid="reports-dashboard"]')).toBeVisible()
    
    // Test custom report builder
    await page.click('[data-testid="create-custom-report"]')
    await expect(page.locator('[data-testid="report-builder"]')).toBeVisible()
    
    // Configure report parameters
    await page.fill('[data-testid="report-name"]', 'Monthly Case Summary')
    await page.selectOption('[data-testid="report-type"]', 'case-analytics')
    await page.selectOption('[data-testid="date-range"]', 'last-month')
    
    // Add data sources
    await page.check('[data-testid="include-case-status"]')
    await page.check('[data-testid="include-billing-data"]')
    await page.check('[data-testid="include-document-counts"]')
    
    // Configure visualization options
    await page.click('[data-testid="visualization-tab"]')
    await page.selectOption('[data-testid="chart-type"]', 'bar-chart')
    await page.selectOption('[data-testid="color-scheme"]', 'blue')
    
    // Preview report
    await page.click('[data-testid="preview-report"]')
    await expect(page.locator('[data-testid="report-preview"]')).toBeVisible()
    
    // Generate report
    const reportDownload = page.waitForEvent('download')
    
    await page.click('[data-testid="generate-report"]')
    await page.selectOption('[data-testid="output-format"]', 'pdf')
    await page.click('[data-testid="confirm-generate"]')
    
    const download = await reportDownload
    expect(download.suggestedFilename()).toContain('Monthly-Case-Summary')
    
    // Test scheduled reports
    await page.click('[data-testid="schedule-report"]')
    await expect(page.locator('[data-testid="schedule-modal"]')).toBeVisible()
    
    await page.selectOption('[data-testid="schedule-frequency"]', 'monthly')
    await page.selectOption('[data-testid="schedule-day"]', '1')
    await page.fill('[data-testid="recipient-emails"]', 'admin@example.com')
    
    await page.click('[data-testid="save-schedule"]')
    await expect(page.locator('text=Report scheduled successfully')).toBeVisible()
    
    // Verify scheduled report appears in list
    await page.click('[data-testid="scheduled-reports-tab"]')
    await expect(page.locator('text=Monthly Case Summary')).toBeVisible()
  })

  test('data export and integration', async ({ page }) => {
    await page.goto('/analytics')
    
    // Test bulk data export
    await page.click('[data-testid="export-data"]')
    await expect(page.locator('[data-testid="export-modal"]')).toBeVisible()
    
    // Configure export options
    await page.check('[data-testid="export-cases"]')
    await page.check('[data-testid="export-documents"]')
    await page.check('[data-testid="export-analytics"]')
    
    await page.selectOption('[data-testid="export-format"]', 'csv')
    await page.selectOption('[data-testid="date-range"]', 'last-quarter')
    
    const exportDownload = page.waitForEvent('download')
    
    await page.click('[data-testid="start-export"]')
    
    // Wait for export to complete
    await expect(page.locator('[data-testid="export-progress"]')).toBeVisible()
    await expect(page.locator('[data-testid="export-complete"]')).toBeVisible({ timeout: 30000 })
    
    const download = await exportDownload
    expect(download.suggestedFilename()).toContain('.zip')
    
    // Test API integration
    await page.click('[data-testid="api-integration"]')
    await expect(page.locator('[data-testid="api-modal"]')).toBeVisible()
    
    // Generate API key
    await page.click('[data-testid="generate-api-key"]')
    await expect(page.locator('[data-testid="api-key"]')).toBeVisible()
    
    // Test webhook configuration
    await page.click('[data-testid="webhooks-tab"]')
    await page.fill('[data-testid="webhook-url"]', 'https://api.example.com/webhooks')
    await page.check('[data-testid="case-update-events"]')
    await page.check('[data-testid="document-events"]')
    
    await page.click('[data-testid="save-webhook"]')
    await expect(page.locator('text=Webhook configured successfully')).toBeVisible()
  })

  test('mobile analytics dashboard', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip()
    }
    
    await page.goto('/analytics')
    
    // Test mobile dashboard layout
    await expect(page.locator('[data-testid="mobile-analytics-dashboard"]')).toBeVisible()
    
    // Test swipeable widget cards
    const widgetContainer = page.locator('[data-testid="widget-container"]')
    
    // Swipe to navigate between widgets
    await widgetContainer.swipeLeft()
    await widgetContainer.swipeLeft()
    
    // Test mobile-specific controls
    await page.click('[data-testid="mobile-menu-toggle"]')
    await expect(page.locator('[data-testid="mobile-analytics-menu"]')).toBeVisible()
    
    // Navigate to different analytics sections
    await page.click('[data-testid="mobile-nav-usage"]')
    await expect(page.locator('[data-testid="mobile-usage-analytics"]')).toBeVisible()
    
    // Test touch interactions with charts
    const chart = page.locator('[data-testid="mobile-chart"]')
    await chart.tap()
    
    // Test mobile report generation
    await page.click('[data-testid="mobile-generate-report"]')
    await expect(page.locator('[data-testid="mobile-report-modal"]')).toBeVisible()
    
    // Simple mobile report configuration
    await page.selectOption('[data-testid="mobile-report-type"]', 'summary')
    await page.click('[data-testid="mobile-generate"]')
    
    await expect(page.locator('text=Report generated')).toBeVisible()
  })
})