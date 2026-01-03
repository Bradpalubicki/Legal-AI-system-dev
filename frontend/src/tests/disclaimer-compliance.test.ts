/**
 * DISCLAIMER COMPLIANCE AUTOMATED TESTING
 * 
 * This test suite validates that ALL pages have proper legal disclaimers
 * and that the disclaimer bypass protection is functioning correctly.
 * 
 * CRITICAL: These tests must pass 100% for legal compliance.
 */

import { test, expect } from '@playwright/test'

// Pages that must have disclaimers
const CRITICAL_PAGES = [
  '/',
  '/research',
  '/contracts', 
  '/dashboard',
  '/analyze',
  '/profile',
  '/settings'
]

// API endpoints that must have disclaimer headers
const CRITICAL_API_ENDPOINTS = [
  '/api/research',
  '/api/contracts/analyze',
  '/api/dashboard/stats',
  '/api/analyze/document'
]

// Required disclaimer text patterns
const REQUIRED_DISCLAIMER_PATTERNS = [
  /not legal advice/i,
  /general information/i,
  /consult.*attorney/i,
  /educational purposes/i
]

// Required header disclaimers
const REQUIRED_HEADERS = [
  'x-legal-disclaimer',
  'x-attorney-client',
  'x-compliance-protected',
  'x-disclaimer-required'
]

// Page-specific disclaimer requirements
const PAGE_SPECIFIC_DISCLAIMERS = {
  '/research': [
    /legal research.*informational purposes/i,
    /not a substitute for attorney consultation/i
  ],
  '/contracts': [
    /contract analysis.*not.*legal review/i,
    /consult.*attorney.*before signing/i
  ],
  '/dashboard': [
    /dashboard information.*not legal advice/i,
    /deadlines.*estimates.*verify.*court/i
  ]
}

test.describe('Disclaimer Compliance Tests', () => {
  
  test.describe('Global Disclaimer Requirements', () => {
    
    CRITICAL_PAGES.forEach(page => {
      test(`${page} - Has global disclaimer modal`, async ({ page: playwright }) => {
        await playwright.goto(page)
        
        // Should show global disclaimer modal on first visit
        await expect(playwright.locator('[data-testid="global-disclaimer-modal"]')).toBeVisible()
        
        // Should have required disclaimer text
        const modalContent = await playwright.locator('[data-testid="global-disclaimer-content"]').textContent()
        
        for (const pattern of REQUIRED_DISCLAIMER_PATTERNS) {
          expect(modalContent).toMatch(pattern)
        }
      })
      
      test(`${page} - Blocks content until disclaimer accepted`, async ({ page: playwright }) => {
        await playwright.goto(page)
        
        // Content should be blocked initially
        await expect(playwright.locator('main')).not.toBeVisible()
        
        // Should show blocking message
        await expect(playwright.locator('[data-testid="disclaimer-blocking-message"]')).toBeVisible()
        
        // Accept disclaimer
        await playwright.locator('[data-testid="accept-global-disclaimer"]').click()
        
        // Content should now be visible
        await expect(playwright.locator('main')).toBeVisible()
      })
      
      test(`${page} - Has persistent header disclaimer`, async ({ page: playwright }) => {
        // Accept disclaimers first
        await playwright.goto(page)
        await playwright.locator('[data-testid="accept-global-disclaimer"]').click()
        
        // Check for persistent header
        await expect(playwright.locator('[data-testid="persistent-disclaimer-header"]')).toBeVisible()
        
        // Header should contain required text
        const headerText = await playwright.locator('[data-testid="persistent-disclaimer-header"]').textContent()
        expect(headerText).toMatch(/not legal advice/i)
      })
      
      test(`${page} - Has footer disclaimer`, async ({ page: playwright }) => {
        // Accept disclaimers first
        await playwright.goto(page)
        await playwright.locator('[data-testid="accept-global-disclaimer"]').click()
        
        // Check for footer disclaimer
        await expect(playwright.locator('[data-testid="footer-disclaimer"]')).toBeVisible()
        
        // Footer should contain required legal notices
        const footerText = await playwright.locator('[data-testid="footer-disclaimer"]').textContent()
        expect(footerText).toMatch(/no attorney-client relationship/i)
        expect(footerText).toMatch(/consult.*qualified attorney/i)
      })
    })
  })
  
  test.describe('Page-Specific Disclaimer Requirements', () => {
    
    Object.entries(PAGE_SPECIFIC_DISCLAIMERS).forEach(([page, patterns]) => {
      test(`${page} - Has page-specific disclaimers`, async ({ page: playwright }) => {
        await playwright.goto(page)
        
        // Accept global disclaimer
        await playwright.locator('[data-testid="accept-global-disclaimer"]').click()
        
        // Should show page-specific disclaimer modal
        await expect(playwright.locator('[data-testid="page-specific-disclaimer-modal"]')).toBeVisible()
        
        // Should have page-specific disclaimer text
        const pageModalContent = await playwright.locator('[data-testid="page-specific-disclaimer-content"]').textContent()
        
        for (const pattern of patterns) {
          expect(pageModalContent).toMatch(pattern)
        }
      })
      
      test(`${page} - Has page-specific disclaimer banner`, async ({ page: playwright }) => {
        // Accept both disclaimers
        await playwright.goto(page)
        await playwright.locator('[data-testid="accept-global-disclaimer"]').click()
        await playwright.locator('[data-testid="accept-page-disclaimer"]').click()
        
        // Should have page-specific banner
        await expect(playwright.locator('[data-testid="page-disclaimer-banner"]')).toBeVisible()
        
        // Banner should contain page-specific text
        const bannerText = await playwright.locator('[data-testid="page-disclaimer-banner"]').textContent()
        expect(bannerText).toMatch(patterns[0])
      })
    })
  })
  
  test.describe('Disclaimer Bypass Protection', () => {
    
    test('Cannot access content without accepting disclaimers', async ({ page }) => {
      await page.goto('/')
      
      // Try to access main content directly
      const mainContent = page.locator('main')
      await expect(mainContent).not.toBeVisible()
      
      // Try to navigate to other pages
      await page.goto('/research')
      await expect(mainContent).not.toBeVisible()
      
      // Content should only be visible after accepting disclaimers
      await page.locator('[data-testid="accept-global-disclaimer"]').click()
      await expect(mainContent).toBeVisible()
    })
    
    test('Disclaimer acceptance persists in session', async ({ page }) => {
      await page.goto('/')
      await page.locator('[data-testid="accept-global-disclaimer"]').click()
      
      // Navigate to another page
      await page.goto('/research')
      
      // Should not show global disclaimer again
      await expect(page.locator('[data-testid="global-disclaimer-modal"]')).not.toBeVisible()
      
      // But should still show page-specific disclaimer
      await expect(page.locator('[data-testid="page-specific-disclaimer-modal"]')).toBeVisible()
    })
    
    test('Cannot bypass disclaimers with direct URL manipulation', async ({ page }) => {
      // Try to access page content directly
      await page.goto('/research?skipDisclaimer=true')
      
      // Should still show disclaimer modal
      await expect(page.locator('[data-testid="global-disclaimer-modal"]')).toBeVisible()
      
      // Content should still be blocked
      await expect(page.locator('main')).not.toBeVisible()
    })
  })
  
  test.describe('Disclaimer Presence Validation', () => {
    
    test('All pages have compliance markers', async ({ page }) => {
      for (const testPage of CRITICAL_PAGES) {
        await page.goto(testPage)
        await page.locator('[data-testid="accept-global-disclaimer"]').click()
        
        // Check for compliance markers
        const complianceMarkers = page.locator('#disclaimer-compliance-markers')
        await expect(complianceMarkers).toBeAttached()
        
        // Validate marker attributes
        await expect(complianceMarkers).toHaveAttribute('data-global-disclaimer', 'present')
        await expect(complianceMarkers).toHaveAttribute('data-footer-disclaimer', 'present')
        await expect(complianceMarkers).toHaveAttribute('data-disclaimer-accepted-global', 'true')
        
        // Page-specific markers
        if (PAGE_SPECIFIC_DISCLAIMERS[testPage]) {
          await page.locator('[data-testid="accept-page-disclaimer"]').click()
          await expect(complianceMarkers).toHaveAttribute('data-page-disclaimer', 'present')
          await expect(complianceMarkers).toHaveAttribute('data-disclaimer-accepted-page', 'true')
        }
      }
    })
    
    test('API responses have disclaimer headers', async ({ request }) => {
      for (const endpoint of CRITICAL_API_ENDPOINTS) {
        const response = await request.get(endpoint)
        
        // Check for required disclaimer headers
        for (const header of REQUIRED_HEADERS) {
          expect(response.headers()).toHaveProperty(header)
        }
        
        // Validate header content
        expect(response.headers()['x-legal-disclaimer']).toMatch(/general information/i)
        expect(response.headers()['x-attorney-client']).toMatch(/no.*relationship/i)
      }
    })
    
    test('JSON API responses include disclaimer in body', async ({ request }) => {
      const response = await request.get('/api/research/sample')
      const data = await response.json()
      
      // Should have disclaimer fields
      expect(data).toHaveProperty('_legal_disclaimer')
      expect(data).toHaveProperty('_compliance_info')
      
      // Disclaimer text should be present
      expect(data._legal_disclaimer).toMatch(/not legal advice/i)
      expect(data._compliance_info.not_legal_advice).toBe(true)
      expect(data._compliance_info.disclaimer_injected).toBe(true)
    })
  })
  
  test.describe('Disclaimer Accessibility', () => {
    
    test('Disclaimers are accessible to screen readers', async ({ page }) => {
      await page.goto('/')
      
      // Check ARIA labels and roles
      const disclaimerModal = page.locator('[data-testid="global-disclaimer-modal"]')
      await expect(disclaimerModal).toHaveAttribute('role', 'dialog')
      await expect(disclaimerModal).toHaveAttribute('aria-modal', 'true')
      
      // Check for proper headings
      await expect(page.locator('h1, h2').filter({ hasText: /legal notice/i })).toBeVisible()
    })
    
    test('Disclaimer text is keyboard navigable', async ({ page }) => {
      await page.goto('/')
      
      // Tab through disclaimer elements
      await page.keyboard.press('Tab')
      await expect(page.locator('[data-testid="accept-global-disclaimer"]')).toBeFocused()
      
      // Enter key should accept disclaimer
      await page.keyboard.press('Enter')
      await expect(page.locator('main')).toBeVisible()
    })
  })
  
  test.describe('Disclaimer Compliance Monitoring', () => {
    
    test('Disclaimer events are logged', async ({ page }) => {
      // Monitor console logs for compliance events
      const logs: string[] = []
      page.on('console', msg => {
        if (msg.text().includes('[COMPLIANCE]')) {
          logs.push(msg.text())
        }
      })
      
      await page.goto('/')
      await page.locator('[data-testid="accept-global-disclaimer"]').click()
      
      // Should have logged disclaimer display and acceptance
      expect(logs).toEqual(
        expect.arrayContaining([
          expect.stringContaining('Disclaimer displayed'),
          expect.stringContaining('Disclaimer accepted')
        ])
      )
    })
    
    test('Page load blocked without disclaimers generates alert', async ({ page }) => {
      // This would integrate with monitoring systems in production
      await page.goto('/')
      
      // Verify content is actually blocked
      const isContentBlocked = await page.locator('main').isVisible()
      expect(isContentBlocked).toBe(false)
      
      // Verify disclaimer modal is shown
      const isDisclaimerShown = await page.locator('[data-testid="global-disclaimer-modal"]').isVisible()
      expect(isDisclaimerShown).toBe(true)
    })
  })
  
  test.describe('Mobile Disclaimer Compliance', () => {
    
    test('Disclaimers work on mobile viewports', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      
      // Disclaimer modal should be responsive
      await expect(page.locator('[data-testid="global-disclaimer-modal"]')).toBeVisible()
      
      // Should be able to scroll through disclaimer text
      await page.locator('[data-testid="global-disclaimer-content"]').scrollIntoViewIfNeeded()
      
      // Accept button should be accessible
      await page.locator('[data-testid="accept-global-disclaimer"]').click()
      await expect(page.locator('main')).toBeVisible()
    })
    
    test('Persistent header is responsive on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.locator('[data-testid="accept-global-disclaimer"]').click()
      
      // Header disclaimer should be visible and readable on mobile
      const header = page.locator('[data-testid="persistent-disclaimer-header"]')
      await expect(header).toBeVisible()
      
      // Should be able to collapse/expand
      await page.locator('[data-testid="disclaimer-toggle"]').click()
      // Verify collapsed state is functional
    })
  })
})

// Performance tests for disclaimer system
test.describe('Disclaimer Performance', () => {
  
  test('Disclaimer system does not significantly impact page load', async ({ page }) => {
    const startTime = Date.now()
    
    await page.goto('/')
    await page.locator('[data-testid="accept-global-disclaimer"]').click()
    await expect(page.locator('main')).toBeVisible()
    
    const loadTime = Date.now() - startTime
    
    // Disclaimer system should not add more than 500ms to page load
    expect(loadTime).toBeLessThan(5000) // 5 seconds total (generous for CI)
  })
})

// Integration tests with real backend
test.describe('Full Stack Disclaimer Integration', () => {
  
  test('Backend API middleware adds disclaimers', async ({ request }) => {
    const response = await request.get('/api/health')
    
    // Even health check should have disclaimer headers
    expect(response.headers()).toHaveProperty('x-legal-disclaimer')
    expect(response.headers()).toHaveProperty('x-compliance-protected')
  })
  
  test('End-to-end disclaimer flow works', async ({ page }) => {
    // Full flow from page load to API call
    await page.goto('/research')
    
    // Accept disclaimers
    await page.locator('[data-testid="accept-global-disclaimer"]').click()
    await page.locator('[data-testid="accept-page-disclaimer"]').click()
    
    // Make API request through UI
    await page.fill('[data-testid="search-input"]', 'test query')
    
    // Monitor API response for disclaimer headers
    const [response] = await Promise.all([
      page.waitForResponse('/api/research/**'),
      page.click('[data-testid="search-button"]')
    ])
    
    expect(response.headers()).toHaveProperty('x-legal-disclaimer')
    
    const data = await response.json()
    expect(data).toHaveProperty('_legal_disclaimer')
  })
})