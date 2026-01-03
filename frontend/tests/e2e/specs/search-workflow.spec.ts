import { test, expect } from '@playwright/test'

test.describe('Search and Legal Research E2E', () => {
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

  test('complete legal research workflow', async ({ page }) => {
    // Navigate to research page
    await page.click('text=Research')
    await expect(page).toHaveURL(/.*\/research/)
    
    // Test basic search
    await page.fill('[data-testid="search-input"]', 'contract breach damages')
    await page.click('[data-testid="search-submit"]')
    
    // Wait for search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible({ timeout: 15000 })
    
    // Verify search results appear
    const resultItems = page.locator('[data-testid^="result-item-"]')
    await expect(resultItems.first()).toBeVisible()
    
    // Test result filtering
    await page.click('[data-testid="filter-panel-toggle"]')
    await expect(page.locator('[data-testid="filter-panel"]')).toBeVisible()
    
    // Apply jurisdiction filter
    await page.check('[data-testid="filter-jurisdiction-federal"]')
    await page.click('[data-testid="apply-filters"]')
    
    // Verify filtered results
    await page.waitForSelector('[data-testid="search-results"]')
    
    // Test advanced search
    await page.click('[data-testid="advanced-search-toggle"]')
    await expect(page.locator('[data-testid="advanced-search-panel"]')).toBeVisible()
    
    // Fill advanced search criteria
    await page.fill('[data-testid="case-name"]', 'Smith v. Jones')
    await page.fill('[data-testid="citation"]', '123 F.3d 456')
    await page.selectOption('[data-testid="date-range"]', 'last-5-years')
    
    await page.click('[data-testid="advanced-search-submit"]')
    
    // Wait for advanced search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    
    // Open a case from results
    await resultItems.first().click()
    
    // Verify case viewer opens
    await expect(page.locator('[data-testid="case-viewer"]')).toBeVisible()
    await expect(page.locator('[data-testid="case-title"]')).toBeVisible()
  })

  test('citation analysis and validation', async ({ page }) => {
    await page.goto('/research')
    
    // Test citation search
    await page.fill('[data-testid="search-input"]', '432 U.S. 197')
    await page.selectOption('[data-testid="search-type"]', 'citation')
    await page.click('[data-testid="search-submit"]')
    
    // Wait for citation results
    await expect(page.locator('[data-testid="citation-result"]')).toBeVisible()
    
    // Verify citation details
    await expect(page.locator('[data-testid="case-name"]')).toContainText('v.')
    await expect(page.locator('[data-testid="court-info"]')).toBeVisible()
    await expect(page.locator('[data-testid="decision-date"]')).toBeVisible()
    
    // Test citation validation
    await page.click('[data-testid="validate-citation"]')
    await expect(page.locator('[data-testid="citation-status"]')).toBeVisible()
    
    // Test citation network
    await page.click('[data-testid="citing-cases-tab"]')
    await expect(page.locator('[data-testid="citing-cases"]')).toBeVisible()
    
    await page.click('[data-testid="cited-cases-tab"]')
    await expect(page.locator('[data-testid="cited-cases"]')).toBeVisible()
    
    // Test citation export
    const downloadPromise = page.waitForEvent('download')
    
    await page.click('[data-testid="export-citation"]')
    await page.click('[data-testid="export-bluebook"]')
    
    const download = await downloadPromise
    expect(download.suggestedFilename()).toContain('citation')
  })

  test('legal database integration', async ({ page }) => {
    await page.goto('/research')
    
    // Test Westlaw integration
    await page.click('[data-testid="database-selector"]')
    await page.click('[data-testid="select-westlaw"]')
    
    await page.fill('[data-testid="search-input"]', 'tort liability')
    await page.click('[data-testid="search-submit"]')
    
    // Wait for Westlaw results
    await expect(page.locator('[data-testid="westlaw-results"]')).toBeVisible({ timeout: 20000 })
    
    // Test result preview
    const firstResult = page.locator('[data-testid^="westlaw-result-"]').first()
    await firstResult.hover()
    
    await expect(page.locator('[data-testid="result-preview"]')).toBeVisible()
    
    // Switch to LexisNexis
    await page.click('[data-testid="database-selector"]')
    await page.click('[data-testid="select-lexis"]')
    
    await page.click('[data-testid="search-submit"]')
    
    // Wait for LexisNexis results
    await expect(page.locator('[data-testid="lexis-results"]')).toBeVisible({ timeout: 20000 })
    
    // Test cross-database comparison
    await page.click('[data-testid="compare-databases"]')
    await expect(page.locator('[data-testid="comparison-view"]')).toBeVisible()
    
    // Verify both result sets are visible
    await expect(page.locator('[data-testid="westlaw-comparison"]')).toBeVisible()
    await expect(page.locator('[data-testid="lexis-comparison"]')).toBeVisible()
  })

  test('AI-powered legal analysis', async ({ page }) => {
    await page.goto('/research')
    
    // Search for a legal concept
    await page.fill('[data-testid="search-input"]', 'piercing corporate veil')
    await page.click('[data-testid="search-submit"]')
    
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    
    // Test AI summary
    await page.click('[data-testid="ai-summary-tab"]')
    await expect(page.locator('[data-testid="ai-summary"]')).toBeVisible({ timeout: 30000 })
    
    // Verify AI summary content
    const summaryText = page.locator('[data-testid="ai-summary-text"]')
    await expect(summaryText).toContainText('corporate veil')
    
    // Test AI-powered insights
    await page.click('[data-testid="ai-insights-tab"]')
    await expect(page.locator('[data-testid="ai-insights"]')).toBeVisible()
    
    // Check for key insights
    await expect(page.locator('[data-testid="key-elements"]')).toBeVisible()
    await expect(page.locator('[data-testid="recent-trends"]')).toBeVisible()
    await expect(page.locator('[data-testid="jurisdiction-analysis"]')).toBeVisible()
    
    // Test AI question answering
    await page.click('[data-testid="ai-qa-tab"]')
    await page.fill('[data-testid="legal-question"]', 'What factors do courts consider when piercing the corporate veil?')
    await page.click('[data-testid="ask-ai"]')
    
    // Wait for AI response
    await expect(page.locator('[data-testid="ai-answer"]')).toBeVisible({ timeout: 30000 })
    
    // Verify answer quality
    const aiAnswer = page.locator('[data-testid="ai-answer-text"]')
    await expect(aiAnswer).toContainText('factors')
    
    // Test AI citation suggestions
    await page.click('[data-testid="suggest-citations"]')
    await expect(page.locator('[data-testid="suggested-citations"]')).toBeVisible()
  })

  test('search history and saved searches', async ({ page }) => {
    await page.goto('/research')
    
    // Perform several searches
    const searches = [
      'contract formation',
      'breach of contract',
      'damages calculation'
    ]
    
    for (const searchTerm of searches) {
      await page.fill('[data-testid="search-input"]', searchTerm)
      await page.click('[data-testid="search-submit"]')
      await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    }
    
    // Check search history
    await page.click('[data-testid="search-history"]')
    await expect(page.locator('[data-testid="history-panel"]')).toBeVisible()
    
    // Verify all searches appear in history
    for (const searchTerm of searches) {
      await expect(page.locator(`text=${searchTerm}`)).toBeVisible()
    }
    
    // Test saving a search
    await page.fill('[data-testid="search-input"]', 'employment discrimination')
    await page.click('[data-testid="search-submit"]')
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    
    await page.click('[data-testid="save-search"]')
    await page.fill('[data-testid="search-name"]', 'Employment Discrimination Research')
    await page.click('[data-testid="confirm-save"]')
    
    // Verify search is saved
    await expect(page.locator('text=Search saved successfully')).toBeVisible()
    
    // Check saved searches
    await page.click('[data-testid="saved-searches"]')
    await expect(page.locator('[data-testid="saved-searches-panel"]')).toBeVisible()
    await expect(page.locator('text=Employment Discrimination Research')).toBeVisible()
    
    // Test loading a saved search
    await page.click('text=Employment Discrimination Research')
    await expect(page.locator('[data-testid="search-input"]')).toHaveValue('employment discrimination')
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
  })

  test('collaborative research features', async ({ page, context }) => {
    await page.goto('/research')
    
    // Start a collaborative session
    await page.fill('[data-testid="search-input"]', 'intellectual property')
    await page.click('[data-testid="search-submit"]')
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    
    // Share research session
    await page.click('[data-testid="collaborate-button"]')
    await expect(page.locator('[data-testid="collaboration-panel"]')).toBeVisible()
    
    await page.click('[data-testid="generate-share-link"]')
    await expect(page.locator('[data-testid="share-link"]')).toBeVisible()
    
    // Get share link
    const shareLink = await page.locator('[data-testid="share-link-input"]').inputValue()
    
    // Test collaborative annotations
    await page.click('[data-testid^="result-item-"]').first()
    await expect(page.locator('[data-testid="case-viewer"]')).toBeVisible()
    
    await page.click('[data-testid="add-research-note"]')
    await page.fill('[data-testid="note-input"]', 'Important precedent for our case')
    await page.click('[data-testid="save-note"]')
    
    await expect(page.locator('text=Important precedent for our case')).toBeVisible()
    
    // Test real-time collaboration (simulate second user)
    const newPage = await context.newPage()
    await newPage.goto(shareLink)
    
    // Verify collaborative session loads
    await expect(newPage.locator('[data-testid="collaborative-session"]')).toBeVisible()
    await expect(newPage.locator('text=Important precedent for our case')).toBeVisible()
    
    // Add note from second user
    await newPage.click('[data-testid="add-research-note"]')
    await newPage.fill('[data-testid="note-input"]', 'Need to verify jurisdiction')
    await newPage.click('[data-testid="save-note"]')
    
    // Verify note appears in original session
    await expect(page.locator('text=Need to verify jurisdiction')).toBeVisible()
    
    await newPage.close()
  })

  test('advanced filtering and sorting', async ({ page }) => {
    await page.goto('/research')
    
    await page.fill('[data-testid="search-input"]', 'personal injury')
    await page.click('[data-testid="search-submit"]')
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    
    // Test date range filtering
    await page.click('[data-testid="filter-panel-toggle"]')
    await page.selectOption('[data-testid="date-range-filter"]', '2020-2024')
    await page.click('[data-testid="apply-filters"]')
    
    // Verify results are filtered by date
    await page.waitForSelector('[data-testid="search-results"]')
    
    // Test court level filtering
    await page.check('[data-testid="filter-supreme-court"]')
    await page.check('[data-testid="filter-appellate-court"]')
    await page.click('[data-testid="apply-filters"]')
    
    // Test relevance sorting
    await page.selectOption('[data-testid="sort-by"]', 'relevance')
    await page.waitForSelector('[data-testid="search-results"]')
    
    // Test date sorting
    await page.selectOption('[data-testid="sort-by"]', 'date-desc')
    await page.waitForSelector('[data-testid="search-results"]')
    
    // Verify sorting applied
    const firstResult = page.locator('[data-testid^="result-item-"]').first()
    const secondResult = page.locator('[data-testid^="result-item-"]').nth(1)
    
    const firstDate = await firstResult.locator('[data-testid="result-date"]').textContent()
    const secondDate = await secondResult.locator('[data-testid="result-date"]').textContent()
    
    // Verify descending date order (newer first)
    expect(new Date(firstDate!)).toBeGreaterThanOrEqual(new Date(secondDate!))
    
    // Test keyword highlighting
    await expect(firstResult.locator('.search-highlight')).toBeVisible()
  })

  test('export and citation management', async ({ page }) => {
    await page.goto('/research')
    
    await page.fill('[data-testid="search-input"]', 'evidence admissibility')
    await page.click('[data-testid="search-submit"]')
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    
    // Select multiple results for export
    await page.check('[data-testid="select-result-1"]')
    await page.check('[data-testid="select-result-2"]')
    await page.check('[data-testid="select-result-3"]')
    
    // Test citation export
    const citationDownload = page.waitForEvent('download')
    
    await page.click('[data-testid="export-selected"]')
    await page.click('[data-testid="export-citations"]')
    await page.selectOption('[data-testid="citation-format"]', 'bluebook')
    await page.click('[data-testid="confirm-export"]')
    
    const download = await citationDownload
    expect(download.suggestedFilename()).toContain('citations')
    
    // Test research report export
    const reportDownload = page.waitForEvent('download')
    
    await page.click('[data-testid="export-selected"]')
    await page.click('[data-testid="export-research-report"]')
    
    await page.fill('[data-testid="report-title"]', 'Evidence Admissibility Research')
    await page.fill('[data-testid="report-description"]', 'Comprehensive research on evidence admissibility standards')
    await page.click('[data-testid="generate-report"]')
    
    const reportFile = await reportDownload
    expect(reportFile.suggestedFilename()).toContain('research-report')
    
    // Test citation manager integration
    await page.click('[data-testid="add-to-citation-manager"]')
    await expect(page.locator('[data-testid="citation-manager-modal"]')).toBeVisible()
    
    await page.selectOption('[data-testid="citation-library"]', 'current-case')
    await page.click('[data-testid="add-citations"]')
    
    await expect(page.locator('text=Citations added to library')).toBeVisible()
  })
})