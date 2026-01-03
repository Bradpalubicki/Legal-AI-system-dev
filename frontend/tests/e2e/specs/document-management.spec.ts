import { test, expect } from '@playwright/test'
import path from 'path'

test.describe('Document Management E2E', () => {
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

  test('complete document upload and review workflow', async ({ page }) => {
    // Navigate to documents page
    await page.click('text=Documents')
    await expect(page).toHaveURL(/.*\/documents/)
    
    // Upload a document
    const fileChooserPromise = page.waitForEvent('filechooser')
    await page.click('text=Upload Document')
    const fileChooser = await fileChooserPromise
    
    // Create a test file (you'd use an actual file in real tests)
    const testFilePath = path.join(__dirname, '..', 'fixtures', 'sample-contract.pdf')
    await fileChooser.setFiles([testFilePath])
    
    // Wait for upload to complete
    await expect(page.locator('.upload-progress')).toBeHidden({ timeout: 30000 })
    
    // Verify document appears in list
    await expect(page.locator('text=sample-contract.pdf')).toBeVisible()
    
    // Open document in viewer
    await page.click('text=sample-contract.pdf')
    
    // Wait for document viewer to load
    await expect(page.locator('[data-testid="document-viewer"]')).toBeVisible()
    await expect(page.locator('text=Page 1 of')).toBeVisible()
    
    // Test zoom functionality
    await page.click('[data-testid="zoom-in"]')
    await page.click('[data-testid="zoom-out"]')
    
    // Test annotation creation
    await page.click('[data-testid="highlight-tool"]')
    
    // Simulate text selection and annotation
    const documentCanvas = page.locator('[data-testid="document-canvas"]')
    await documentCanvas.click({ position: { x: 200, y: 300 } })
    await documentCanvas.drag(documentCanvas, { 
      sourcePosition: { x: 200, y: 300 },
      targetPosition: { x: 400, y: 320 }
    })
    
    // Add annotation text
    await page.fill('[data-testid="annotation-input"]', 'Important contract clause')
    await page.click('[data-testid="save-annotation"]')
    
    // Verify annotation appears
    await expect(page.locator('text=Important contract clause')).toBeVisible()
    
    // Test navigation
    const nextPageButton = page.locator('[data-testid="next-page"]')
    if (await nextPageButton.isEnabled()) {
      await nextPageButton.click()
      await expect(page.locator('text=Page 2 of')).toBeVisible()
      
      await page.click('[data-testid="prev-page"]')
      await expect(page.locator('text=Page 1 of')).toBeVisible()
    }
    
    // Test fullscreen
    await page.click('[data-testid="fullscreen-toggle"]')
    await expect(page.locator('[data-testid="document-viewer"]')).toHaveCSS('position', 'fixed')
    
    // Exit fullscreen
    await page.keyboard.press('Escape')
    await expect(page.locator('[data-testid="document-viewer"]')).not.toHaveCSS('position', 'fixed')
  })

  test('document search and filtering', async ({ page }) => {
    await page.goto('/documents')
    
    // Test search functionality
    await page.fill('[data-testid="document-search"]', 'contract')
    await page.keyboard.press('Enter')
    
    // Wait for search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible()
    
    // Test filters
    await page.click('[data-testid="filter-button"]')
    await expect(page.locator('[data-testid="filter-panel"]')).toBeVisible()
    
    // Apply document type filter
    await page.check('[data-testid="filter-contract"]')
    await page.click('[data-testid="apply-filters"]')
    
    // Verify filtered results
    const documentItems = page.locator('[data-testid^="document-item-"]')
    await expect(documentItems.first()).toBeVisible()
    
    // Clear filters
    await page.click('[data-testid="clear-filters"]')
    await expect(page.locator('[data-testid="filter-contract"]')).not.toBeChecked()
  })

  test('collaborative document annotation', async ({ page, context }) => {
    // Open document
    await page.goto('/documents')
    await page.click('text=sample-contract.pdf')
    
    await expect(page.locator('[data-testid="document-viewer"]')).toBeVisible()
    
    // Create annotation
    await page.click('[data-testid="note-tool"]')
    await page.locator('[data-testid="document-canvas"]').click({ position: { x: 300, y: 400 } })
    
    await page.fill('[data-testid="annotation-input"]', 'Review this section carefully')
    await page.click('[data-testid="save-annotation"]')
    
    // Test collaboration features
    await page.click('[data-testid="collaboration-panel"]')
    await expect(page.locator('[data-testid="active-users"]')).toBeVisible()
    
    // Test annotation comments
    const annotation = page.locator('text=Review this section carefully')
    await annotation.click()
    
    await page.click('[data-testid="add-comment"]')
    await page.fill('[data-testid="comment-input"]', 'Agreed, this needs attention')
    await page.click('[data-testid="save-comment"]')
    
    await expect(page.locator('text=Agreed, this needs attention')).toBeVisible()
    
    // Test real-time updates simulation
    // In a real test, you'd open another browser context/tab
    const newPage = await context.newPage()
    await newPage.goto('/documents')
    await newPage.click('text=sample-contract.pdf')
    
    // Verify annotation is visible in second context
    await expect(newPage.locator('text=Review this section carefully')).toBeVisible()
    
    await newPage.close()
  })

  test('document export and download', async ({ page }) => {
    await page.goto('/documents')
    await page.click('text=sample-contract.pdf')
    
    await expect(page.locator('[data-testid="document-viewer"]')).toBeVisible()
    
    // Test document export
    const downloadPromise = page.waitForEvent('download')
    
    await page.click('[data-testid="export-menu"]')
    await page.click('[data-testid="export-pdf"]')
    
    const download = await downloadPromise
    expect(download.suggestedFilename()).toContain('.pdf')
    
    // Test export with annotations
    await page.click('[data-testid="export-menu"]')
    await page.click('[data-testid="export-with-annotations"]')
    
    const annotatedDownload = await page.waitForEvent('download')
    expect(annotatedDownload.suggestedFilename()).toContain('annotated')
    
    // Test bulk export
    await page.goto('/documents')
    
    // Select multiple documents
    await page.check('[data-testid="select-document-1"]')
    await page.check('[data-testid="select-document-2"]')
    
    const bulkDownloadPromise = page.waitForEvent('download')
    
    await page.click('[data-testid="bulk-actions"]')
    await page.click('[data-testid="bulk-export"]')
    
    const bulkDownload = await bulkDownloadPromise
    expect(bulkDownload.suggestedFilename()).toContain('.zip')
  })

  test('mobile document viewer', async ({ page, isMobile }) => {
    if (!isMobile) {
      test.skip()
    }
    
    await page.goto('/documents')
    
    // Test mobile navigation
    await page.click('[data-testid="mobile-menu-toggle"]')
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible()
    
    await page.click('text=Documents')
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeHidden()
    
    // Open document
    await page.click('text=sample-contract.pdf')
    
    // Test mobile-specific controls
    await expect(page.locator('[data-testid="mobile-document-viewer"]')).toBeVisible()
    
    // Test touch gestures
    const documentArea = page.locator('[data-testid="document-canvas"]')
    
    // Pinch to zoom simulation
    await documentArea.touchStart([
      { x: 200, y: 200 },
      { x: 300, y: 300 }
    ])
    await documentArea.touchMove([
      { x: 150, y: 150 },
      { x: 350, y: 350 }
    ])
    await documentArea.touchEnd()
    
    // Swipe navigation
    await documentArea.swipeLeft()
    
    // Test mobile annotation tools
    await page.click('[data-testid="mobile-annotation-toggle"]')
    await expect(page.locator('[data-testid="mobile-annotation-tools"]')).toBeVisible()
    
    await page.click('[data-testid="mobile-highlight-tool"]')
    
    // Create annotation on mobile
    await documentArea.tap({ position: { x: 200, y: 200 } })
    await page.fill('[data-testid="mobile-annotation-input"]', 'Mobile annotation')
    await page.click('[data-testid="mobile-save-annotation"]')
    
    await expect(page.locator('text=Mobile annotation')).toBeVisible()
  })

  test('offline document access', async ({ page, context }) => {
    // First, load document while online
    await page.goto('/documents')
    await page.click('text=sample-contract.pdf')
    
    await expect(page.locator('[data-testid="document-viewer"]')).toBeVisible()
    
    // Go offline
    await context.setOffline(true)
    
    // Refresh page to simulate offline access
    await page.reload()
    
    // Should show offline indicator
    await expect(page.locator('[data-testid="offline-indicator"]')).toBeVisible()
    
    // Document should still be accessible (cached)
    await expect(page.locator('[data-testid="document-viewer"]')).toBeVisible()
    
    // Test offline annotation creation
    await page.click('[data-testid="highlight-tool"]')
    
    const documentCanvas = page.locator('[data-testid="document-canvas"]')
    await documentCanvas.click({ position: { x: 200, y: 300 } })
    
    await page.fill('[data-testid="annotation-input"]', 'Offline annotation')
    await page.click('[data-testid="save-annotation"]')
    
    // Should show pending sync indicator
    await expect(page.locator('[data-testid="pending-sync"]')).toBeVisible()
    
    // Go back online
    await context.setOffline(false)
    
    // Should sync annotations
    await expect(page.locator('[data-testid="sync-success"]')).toBeVisible({ timeout: 10000 })
    await expect(page.locator('[data-testid="pending-sync"]')).toBeHidden()
  })

  test('accessibility features', async ({ page }) => {
    await page.goto('/documents')
    
    // Test keyboard navigation
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')
    await page.keyboard.press('Enter') // Should open first document
    
    await expect(page.locator('[data-testid="document-viewer"]')).toBeVisible()
    
    // Test focus management
    await page.keyboard.press('Tab')
    const focusedElement = await page.locator(':focus')
    await expect(focusedElement).toBeVisible()
    
    // Test screen reader announcements
    await page.click('[data-testid="next-page"]')
    
    // Check for aria-live regions
    await expect(page.locator('[aria-live="polite"]')).toBeVisible()
    
    // Test high contrast mode
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.emulateMedia({ colorScheme: 'dark' })
    
    // Verify accessibility improvements are applied
    const viewer = page.locator('[data-testid="document-viewer"]')
    await expect(viewer).toHaveCSS('background-color', /(rgb\(0, 0, 0\)|#000000)/)
    
    // Test alt text and labels
    const toolButtons = page.locator('[data-testid^="tool-"]')
    const count = await toolButtons.count()
    
    for (let i = 0; i < count; i++) {
      const button = toolButtons.nth(i)
      await expect(button).toHaveAttribute('aria-label')
    }
  })

  test('performance with large documents', async ({ page }) => {
    // Upload a large document (mock or use large fixture)
    await page.goto('/documents')
    
    const startTime = Date.now()
    
    await page.click('text=large-document.pdf') // Assume this exists
    await expect(page.locator('[data-testid="document-viewer"]')).toBeVisible()
    
    const loadTime = Date.now() - startTime
    
    // Should load within reasonable time
    expect(loadTime).toBeLessThan(5000) // 5 seconds
    
    // Test scroll performance
    const scrollContainer = page.locator('[data-testid="document-scroll-container"]')
    
    // Measure scroll performance
    const scrollStart = Date.now()
    
    for (let i = 0; i < 10; i++) {
      await scrollContainer.evaluate(node => {
        node.scrollTop += 100
      })
      await page.waitForTimeout(50)
    }
    
    const scrollTime = Date.now() - scrollStart
    expect(scrollTime).toBeLessThan(2000) // Should be smooth
    
    // Test memory usage doesn't grow excessively
    const initialMetrics = await page.evaluate(() => (performance as any).memory?.usedJSHeapSize)
    
    // Navigate through pages
    for (let i = 0; i < 5; i++) {
      await page.click('[data-testid="next-page"]')
      await page.waitForTimeout(100)
    }
    
    const finalMetrics = await page.evaluate(() => (performance as any).memory?.usedJSHeapSize)
    
    if (initialMetrics && finalMetrics) {
      const memoryIncrease = finalMetrics - initialMetrics
      // Memory increase should be reasonable
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024) // 50MB
    }
  })
})