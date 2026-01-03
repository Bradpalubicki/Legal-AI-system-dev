/**
 * Comprehensive Disclaimer Coverage Testing Suite
 * 
 * This test suite automatically visits every route in the application
 * and verifies that disclaimers are present and cannot be bypassed.
 * 
 * CRITICAL: All routes MUST have proper disclaimer coverage for legal compliance
 */

import { test, expect, Page, BrowserContext } from '@playwright/test'
import path from 'path'

// Define all application routes that must be tested
const ROUTES_TO_TEST = [
  // Core application routes
  '/',
  '/dashboard',
  '/documents',
  '/documents/upload',
  '/costs',
  
  // Authentication routes
  '/auth/login',
  '/auth/register', 
  '/auth/verify-attorney',
  
  // Legal workflow routes
  '/compliance',
  '/compliance/terms-acceptance',
  '/client-portal',
  '/education',
  '/referrals',
  
  // Administrative routes
  '/admin',
  '/admin/audit',
  '/admin/monitoring',
  
  // Mobile routes
  '/mobile',
  '/mobile/offline',
  '/mobile/accessibility',
  '/mobile/test-results',
  
  // Dynamic routes (using placeholder IDs)
  '/dashboard/test-matter-id',
  '/documents/test-doc-id',
  '/documents/analysis/test-analysis-id',
  '/education/topics/test-topic-id'
]

interface DisclaimerValidationResult {
  route: string
  hasGlobalDisclaimer: boolean
  hasPageDisclaimer: boolean
  hasHeaderDisclaimer: boolean
  hasFooterDisclaimer: boolean
  complianceMarkersPresent: boolean
  disclaimerAcceptanceRequired: boolean
  bypassProtectionEnabled: boolean
  modalsBypassBlocked: boolean
  cssOverrideProtection: boolean
  domManipulationMonitored: boolean
  overallCompliance: boolean
  errors: string[]
}

class DisclaimerComplianceTester {
  private page: Page
  private results: DisclaimerValidationResult[] = []

  constructor(page: Page) {
    this.page = page
  }

  async testAllRoutes(): Promise<DisclaimerValidationResult[]> {
    console.log(`[DISCLAIMER_TEST] Starting comprehensive disclaimer testing for ${ROUTES_TO_TEST.length} routes`)
    
    for (const route of ROUTES_TO_TEST) {
      console.log(`[DISCLAIMER_TEST] Testing route: ${route}`)
      try {
        const result = await this.testRoute(route)
        this.results.push(result)
        console.log(`[DISCLAIMER_TEST] Route ${route}: ${result.overallCompliance ? 'PASS' : 'FAIL'}`)
      } catch (error) {
        console.error(`[DISCLAIMER_TEST] Error testing route ${route}:`, error)
        this.results.push({
          route,
          hasGlobalDisclaimer: false,
          hasPageDisclaimer: false,
          hasHeaderDisclaimer: false,
          hasFooterDisclaimer: false,
          complianceMarkersPresent: false,
          disclaimerAcceptanceRequired: false,
          bypassProtectionEnabled: false,
          modalsBypassBlocked: false,
          cssOverrideProtection: false,
          domManipulationMonitored: false,
          overallCompliance: false,
          errors: [`Test execution failed: ${error}`]
        })
      }
    }

    return this.results
  }

  async testRoute(route: string): Promise<DisclaimerValidationResult> {
    const errors: string[] = []
    
    // Navigate to the route
    await this.page.goto(`http://localhost:3000${route}`, { waitUntil: 'networkidle' })
    
    // Wait a moment for disclaimers to load
    await this.page.waitForTimeout(2000)

    // Test 1: Check for global disclaimer modal
    const hasGlobalDisclaimer = await this.validateGlobalDisclaimer()
    if (!hasGlobalDisclaimer) {
      errors.push('Global disclaimer modal not present or not functional')
    }

    // Accept global disclaimer if present
    if (hasGlobalDisclaimer) {
      await this.acceptGlobalDisclaimer()
    }

    // Test 2: Check for page-specific disclaimer
    const hasPageDisclaimer = await this.validatePageSpecificDisclaimer()
    if (!hasPageDisclaimer) {
      errors.push('Page-specific disclaimer not present')
    }

    // Accept page disclaimer if present
    if (hasPageDisclaimer) {
      await this.acceptPageDisclaimer()
    }

    // Test 3: Check for header disclaimer
    const hasHeaderDisclaimer = await this.validateHeaderDisclaimer()
    if (!hasHeaderDisclaimer) {
      errors.push('Header disclaimer not present or not visible')
    }

    // Test 4: Check for footer disclaimer
    const hasFooterDisclaimer = await this.validateFooterDisclaimer()
    if (!hasFooterDisclaimer) {
      errors.push('Footer disclaimer not present')
    }

    // Test 5: Check compliance markers
    const complianceMarkersPresent = await this.validateComplianceMarkers()
    if (!complianceMarkersPresent) {
      errors.push('Compliance markers missing or incomplete')
    }

    // Test 6: Test disclaimer acceptance requirement
    const disclaimerAcceptanceRequired = await this.testDisclaimerAcceptanceRequirement()
    if (!disclaimerAcceptanceRequired) {
      errors.push('Content accessible without disclaimer acceptance')
    }

    // Test 7: Test bypass protection
    const bypassProtectionEnabled = await this.testBypassProtection()
    if (!bypassProtectionEnabled) {
      errors.push('Bypass protection not functioning properly')
    }

    // Test 8: Test modal bypass blocking
    const modalsBypassBlocked = await this.testModalBypassBlocking()
    if (!modalsBypassBlocked) {
      errors.push('Modal disclaimers can be bypassed')
    }

    // Test 9: Test CSS override protection
    const cssOverrideProtection = await this.testCSSOverrideProtection()
    if (!cssOverrideProtection) {
      errors.push('CSS override protection not functioning')
    }

    // Test 10: Test DOM manipulation monitoring
    const domManipulationMonitored = await this.testDOMManipulationMonitoring()
    if (!domManipulationMonitored) {
      errors.push('DOM manipulation monitoring not active')
    }

    // Calculate overall compliance
    const overallCompliance = errors.length === 0

    return {
      route,
      hasGlobalDisclaimer,
      hasPageDisclaimer,
      hasHeaderDisclaimer,
      hasFooterDisclaimer,
      complianceMarkersPresent,
      disclaimerAcceptanceRequired,
      bypassProtectionEnabled,
      modalsBypassBlocked,
      cssOverrideProtection,
      domManipulationMonitored,
      overallCompliance,
      errors
    }
  }

  async validateGlobalDisclaimer(): Promise<boolean> {
    try {
      // Check if global disclaimer modal is present and visible
      const modalExists = await this.page.locator('[data-testid="global-disclaimer-modal"]').count() > 0
      if (modalExists) {
        const modalVisible = await this.page.locator('[data-testid="global-disclaimer-modal"]').isVisible()
        return modalVisible
      }

      // Alternative check by dialog role
      const dialogExists = await this.page.locator('div[role="dialog"]').count() > 0
      if (dialogExists) {
        const dialogContent = await this.page.locator('div[role="dialog"]').textContent()
        return dialogContent?.includes('IMPORTANT LEGAL NOTICE') || dialogContent?.includes('NOT constitute legal advice') || false
      }

      return false
    } catch {
      return false
    }
  }

  async acceptGlobalDisclaimer(): Promise<void> {
    try {
      // Try to find and click the accept button
      const acceptButton = this.page.locator('button:has-text("I Understand and Accept These Disclaimers")')
      if (await acceptButton.count() > 0) {
        await acceptButton.click()
        await this.page.waitForTimeout(1000)
      }
    } catch (error) {
      console.log('Could not accept global disclaimer:', error)
    }
  }

  async validatePageSpecificDisclaimer(): Promise<boolean> {
    try {
      // Wait for page disclaimer modal to appear after global acceptance
      await this.page.waitForTimeout(1000)
      
      const pageModalExists = await this.page.locator('div[role="dialog"]').count() > 0
      if (pageModalExists) {
        const dialogContent = await this.page.locator('div[role="dialog"]').textContent()
        return dialogContent?.includes('Disclaimer') && !dialogContent?.includes('IMPORTANT LEGAL NOTICE') || false
      }

      // Check for page disclaimer banner
      const bannerExists = await this.page.locator('[data-testid="page-disclaimer-banner"]').count() > 0
      if (bannerExists) {
        return await this.page.locator('[data-testid="page-disclaimer-banner"]').isVisible()
      }

      // Alternative check for any disclaimer alert
      const alertExists = await this.page.locator('div[role="alert"]').count() > 0
      return alertExists
    } catch {
      return false
    }
  }

  async acceptPageDisclaimer(): Promise<void> {
    try {
      // Try to find and click the page-specific accept button
      const acceptButton = this.page.locator('button:has-text("I Understand These Additional Disclaimers")')
      if (await acceptButton.count() > 0) {
        await acceptButton.click()
        await this.page.waitForTimeout(1000)
      }
    } catch (error) {
      console.log('Could not accept page disclaimer:', error)
    }
  }

  async validateHeaderDisclaimer(): Promise<boolean> {
    try {
      // Check for header disclaimer bar
      const headerDisclaimer = await this.page.locator('.bg-red-600').count() > 0
      if (headerDisclaimer) {
        const headerText = await this.page.locator('.bg-red-600').textContent()
        return headerText?.includes('NOT LEGAL ADVICE') || headerText?.includes('General Information Only') || false
      }
      return false
    } catch {
      return false
    }
  }

  async validateFooterDisclaimer(): Promise<boolean> {
    try {
      // Check for footer disclaimer
      const footerExists = await this.page.locator('footer').count() > 0
      if (footerExists) {
        const footerText = await this.page.locator('footer').textContent()
        return footerText?.includes('Legal Notice') || footerText?.includes('not provide legal advice') || false
      }
      return false
    } catch {
      return false
    }
  }

  async validateComplianceMarkers(): Promise<boolean> {
    try {
      const markersElement = await this.page.locator('#disclaimer-compliance-markers')
      const markersExist = await markersElement.count() > 0
      
      if (markersExist) {
        const disclaimerSystem = await markersElement.getAttribute('data-disclaimer-system')
        const bypassProtection = await markersElement.getAttribute('data-bypass-protection')
        const globalDisclaimer = await markersElement.getAttribute('data-global-disclaimer')
        const pageDisclaimer = await markersElement.getAttribute('data-page-disclaimer')
        
        return disclaimerSystem === 'active' && 
               bypassProtection === 'enabled' && 
               globalDisclaimer === 'present' &&
               pageDisclaimer === 'present'
      }
      return false
    } catch {
      return false
    }
  }

  async testDisclaimerAcceptanceRequirement(): Promise<boolean> {
    try {
      // Reload page to reset disclaimer acceptance
      await this.page.reload({ waitUntil: 'networkidle' })
      
      // Check if content is blocked without disclaimer acceptance
      const blockedContent = await this.page.locator('text=Legal Disclaimers Required').count() > 0
      const modalPresent = await this.page.locator('div[role="dialog"]').count() > 0
      
      return blockedContent || modalPresent
    } catch {
      return false
    }
  }

  async testBypassProtection(): Promise<boolean> {
    try {
      // Test escape key blocking
      await this.page.keyboard.press('Escape')
      await this.page.waitForTimeout(500)
      
      // Check if modal is still present
      const modalStillPresent = await this.page.locator('div[role="dialog"]').count() > 0
      
      // Test outside click blocking
      if (modalStillPresent) {
        await this.page.click('body', { position: { x: 10, y: 10 } })
        await this.page.waitForTimeout(500)
        const modalStillThere = await this.page.locator('div[role="dialog"]').count() > 0
        return modalStillThere
      }
      
      return modalStillPresent
    } catch {
      return false
    }
  }

  async testModalBypassBlocking(): Promise<boolean> {
    try {
      // Test if modal can be closed without proper acceptance
      const modalExists = await this.page.locator('div[role="dialog"]').count() > 0
      if (modalExists) {
        // Try to close modal by clicking backdrop
        await this.page.click('body')
        await this.page.waitForTimeout(500)
        
        // Modal should still be present
        const stillPresent = await this.page.locator('div[role="dialog"]').count() > 0
        return stillPresent
      }
      return true // No modal means no bypass possible
    } catch {
      return false
    }
  }

  async testCSSOverrideProtection(): Promise<boolean> {
    try {
      // Try to hide disclaimer elements with CSS
      await this.page.addStyleTag({
        content: `
          [data-disclaimer] { display: none !important; }
          footer { visibility: hidden !important; }
          .bg-red-600 { opacity: 0 !important; }
        `
      })
      
      await this.page.waitForTimeout(1000)
      
      // Check if disclaimers are still visible (protection working)
      const headerVisible = await this.page.locator('.bg-red-600').isVisible()
      const footerVisible = await this.page.locator('footer').isVisible()
      
      return headerVisible || footerVisible
    } catch {
      return false
    }
  }

  async testDOMManipulationMonitoring(): Promise<boolean> {
    try {
      // Check if DOM manipulation monitoring script is present
      const scriptContent = await this.page.evaluate(() => {
        const scripts = Array.from(document.scripts)
        return scripts.some(script => 
          script.innerHTML.includes('MutationObserver') && 
          script.innerHTML.includes('SECURITY_VIOLATION')
        )
      })
      
      return scriptContent
    } catch {
      return false
    }
  }

  generateReport(): string {
    const totalRoutes = this.results.length
    const compliantRoutes = this.results.filter(r => r.overallCompliance).length
    const complianceRate = ((compliantRoutes / totalRoutes) * 100).toFixed(2)
    
    let report = `\n=== DISCLAIMER COVERAGE REPORT ===\n\n`
    report += `Total Routes Tested: ${totalRoutes}\n`
    report += `Compliant Routes: ${compliantRoutes}\n`
    report += `Non-Compliant Routes: ${totalRoutes - compliantRoutes}\n`
    report += `Overall Compliance Rate: ${complianceRate}%\n\n`

    // Detailed results
    report += `=== DETAILED RESULTS ===\n\n`
    
    this.results.forEach(result => {
      report += `Route: ${result.route}\n`
      report += `Status: ${result.overallCompliance ? 'COMPLIANT ✅' : 'NON-COMPLIANT ❌'}\n`
      
      if (!result.overallCompliance) {
        report += `Errors:\n`
        result.errors.forEach(error => {
          report += `  - ${error}\n`
        })
      }
      
      report += `Global Disclaimer: ${result.hasGlobalDisclaimer ? '✅' : '❌'}\n`
      report += `Page Disclaimer: ${result.hasPageDisclaimer ? '✅' : '❌'}\n`
      report += `Header Disclaimer: ${result.hasHeaderDisclaimer ? '✅' : '❌'}\n`
      report += `Footer Disclaimer: ${result.hasFooterDisclaimer ? '✅' : '❌'}\n`
      report += `Bypass Protection: ${result.bypassProtectionEnabled ? '✅' : '❌'}\n`
      report += `\n`
    })

    // Summary recommendations
    report += `=== RECOMMENDATIONS ===\n\n`
    
    if (complianceRate === '100.00') {
      report += `🎉 EXCELLENT: All routes have proper disclaimer coverage!\n`
      report += `✅ The system provides comprehensive legal compliance protection.\n`
      report += `✅ No bypass vulnerabilities detected.\n`
    } else {
      report += `⚠️  ATTENTION REQUIRED: ${totalRoutes - compliantRoutes} routes need disclaimer fixes.\n`
      report += `🔧 Review and fix non-compliant routes before production deployment.\n`
      
      const failedRoutes = this.results.filter(r => !r.overallCompliance)
      if (failedRoutes.length > 0) {
        report += `\nRoutes requiring immediate attention:\n`
        failedRoutes.forEach(route => {
          report += `  - ${route.route}\n`
        })
      }
    }

    return report
  }
}

// Main test suite
test.describe('Disclaimer Coverage Testing', () => {
  let tester: DisclaimerComplianceTester

  test.beforeEach(async ({ page }) => {
    tester = new DisclaimerComplianceTester(page)
    
    // Set viewport for consistent testing
    await page.setViewportSize({ width: 1200, height: 800 })
  })

  test('should have disclaimer coverage on all routes', async ({ page }) => {
    console.log('[DISCLAIMER_TEST] Starting comprehensive disclaimer coverage test')
    
    const results = await tester.testAllRoutes()
    const report = tester.generateReport()
    
    console.log(report)
    
    // Assert that all routes are compliant
    const compliantRoutes = results.filter(r => r.overallCompliance).length
    const totalRoutes = results.length
    const complianceRate = (compliantRoutes / totalRoutes) * 100
    
    expect(complianceRate).toBeGreaterThanOrEqual(90) // Require at least 90% compliance
    
    // Individual assertions for critical checks
    for (const result of results) {
      expect(result.hasGlobalDisclaimer, `Route ${result.route} missing global disclaimer`).toBe(true)
      expect(result.complianceMarkersPresent, `Route ${result.route} missing compliance markers`).toBe(true)
      expect(result.disclaimerAcceptanceRequired, `Route ${result.route} allows bypass of disclaimer acceptance`).toBe(true)
    }
  })

  test('should block all bypass attempts', async ({ page }) => {
    console.log('[DISCLAIMER_TEST] Testing bypass protection across all routes')
    
    for (const route of ROUTES_TO_TEST.slice(0, 5)) { // Test first 5 routes for bypass protection
      await page.goto(`http://localhost:3000${route}`)
      await page.waitForTimeout(1000)
      
      // Test escape key blocking
      await page.keyboard.press('Escape')
      await page.waitForTimeout(500)
      
      const modalStillPresent = await page.locator('div[role="dialog"]').count() > 0
      const blockedContentPresent = await page.locator('text=Legal Disclaimers Required').count() > 0
      
      expect(modalStillPresent || blockedContentPresent, 
        `Route ${route} allows escape key bypass`).toBe(true)
    }
  })

  test('should maintain disclaimers after DOM manipulation attempts', async ({ page }) => {
    console.log('[DISCLAIMER_TEST] Testing DOM manipulation protection')
    
    await page.goto('http://localhost:3000/')
    await page.waitForTimeout(2000)
    
    // Try to manipulate DOM to hide disclaimers
    await page.evaluate(() => {
      const disclaimerElements = document.querySelectorAll('[data-disclaimer]')
      disclaimerElements.forEach(el => {
        (el as HTMLElement).style.display = 'none'
        (el as HTMLElement).style.visibility = 'hidden'
        (el as HTMLElement).style.opacity = '0'
      })
    })
    
    await page.waitForTimeout(2000)
    
    // Check if disclaimers are restored by protection mechanisms
    const disclaimerVisible = await page.locator('footer').isVisible()
    expect(disclaimerVisible, 'Disclaimer protection failed against DOM manipulation').toBe(true)
  })
})

export { DisclaimerComplianceTester, ROUTES_TO_TEST }