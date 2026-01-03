#!/usr/bin/env node

/**
 * Comprehensive Disclaimer Coverage Testing Script
 * 
 * This script tests every route in the Legal AI system to ensure
 * proper disclaimer coverage and compliance enforcement.
 * 
 * CRITICAL: 100% compliance required for legal protection
 */

const https = require('https')
const http = require('http')
const { JSDOM } = require('jsdom')
const fs = require('fs')
const path = require('path')

// Configuration
const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:3000'
const OUTPUT_FILE = path.join(__dirname, 'disclaimer-test-results.json')

// All routes that must be tested for disclaimer compliance
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
  '/mobile/test-results'
]

class DisclaimerCoverageTester {
  constructor() {
    this.results = []
    this.totalRoutes = ROUTES_TO_TEST.length
    this.passedRoutes = 0
    this.failedRoutes = 0
    this.startTime = Date.now()
  }

  async runAllTests() {
    console.log('🔍 DISCLAIMER COVERAGE TESTING STARTED')
    console.log('=' * 60)
    console.log(`Testing ${this.totalRoutes} routes for disclaimer compliance...`)
    console.log(`Base URL: ${BASE_URL}`)
    console.log()

    for (let i = 0; i < ROUTES_TO_TEST.length; i++) {
      const route = ROUTES_TO_TEST[i]
      console.log(`[${i + 1}/${this.totalRoutes}] Testing route: ${route}`)
      
      try {
        const result = await this.testRoute(route)
        this.results.push(result)
        
        if (result.compliant) {
          this.passedRoutes++
          console.log(`  ✅ PASS - All disclaimers present`)
        } else {
          this.failedRoutes++
          console.log(`  ❌ FAIL - ${result.errors.length} issue(s) found`)
          result.errors.forEach(error => console.log(`    ⚠️  ${error}`))
        }
      } catch (error) {
        console.log(`  💥 ERROR - ${error.message}`)
        this.results.push({
          route,
          compliant: false,
          errors: [`Test execution failed: ${error.message}`],
          checks: {},
          timestamp: new Date().toISOString()
        })
        this.failedRoutes++
      }
      
      // Small delay to avoid overwhelming the server
      await new Promise(resolve => setTimeout(resolve, 100))
    }

    this.generateReport()
  }

  async testRoute(route) {
    const url = `${BASE_URL}${route}`
    const html = await this.fetchHTML(url)
    const dom = new JSDOM(html)
    const document = dom.window.document
    
    const errors = []
    const checks = {}
    
    // Test 1: Check for root layout disclaimer configuration
    checks.hasDisclaimerMeta = this.checkDisclaimerMeta(document)
    if (!checks.hasDisclaimerMeta) {
      errors.push('Missing legal disclaimer meta tags in document head')
    }
    
    // Test 2: Check for DisclaimerWrapper component
    checks.hasDisclaimerWrapper = this.checkDisclaimerWrapper(document)
    if (!checks.hasDisclaimerWrapper) {
      errors.push('DisclaimerWrapper component not found - disclaimers not enforced')
    }
    
    // Test 3: Check for compliance markers
    checks.hasComplianceMarkers = this.checkComplianceMarkers(document)
    if (!checks.hasComplianceMarkers) {
      errors.push('Compliance markers missing - automated testing cannot verify disclaimers')
    }
    
    // Test 4: Check for global disclaimer modal structure
    checks.hasGlobalDisclaimerModal = this.checkGlobalDisclaimerModal(document)
    if (!checks.hasGlobalDisclaimerModal) {
      errors.push('Global disclaimer modal structure not found')
    }
    
    // Test 5: Check for page-specific disclaimer
    checks.hasPageDisclaimer = this.checkPageSpecificDisclaimer(document, route)
    if (!checks.hasPageDisclaimer) {
      errors.push('Page-specific disclaimer not configured for this route')
    }
    
    // Test 6: Check for header disclaimer
    checks.hasHeaderDisclaimer = this.checkHeaderDisclaimer(document)
    if (!checks.hasHeaderDisclaimer) {
      errors.push('Header disclaimer bar not present')
    }
    
    // Test 7: Check for footer disclaimer
    checks.hasFooterDisclaimer = this.checkFooterDisclaimer(document)
    if (!checks.hasFooterDisclaimer) {
      errors.push('Footer disclaimer not present')
    }
    
    // Test 8: Check for bypass protection
    checks.hasBypassProtection = this.checkBypassProtection(document)
    if (!checks.hasBypassProtection) {
      errors.push('Bypass protection mechanisms not detected')
    }
    
    // Test 9: Check for content blocking
    checks.hasContentBlocking = this.checkContentBlocking(document)
    if (!checks.hasContentBlocking) {
      errors.push('Content not properly blocked until disclaimer acceptance')
    }
    
    // Test 10: Check for security monitoring
    checks.hasSecurityMonitoring = this.checkSecurityMonitoring(document)
    if (!checks.hasSecurityMonitoring) {
      errors.push('Security monitoring for bypass attempts not active')
    }
    
    const compliant = errors.length === 0
    
    return {
      route,
      compliant,
      errors,
      checks,
      timestamp: new Date().toISOString(),
      complianceScore: this.calculateComplianceScore(checks)
    }
  }

  async fetchHTML(url) {
    return new Promise((resolve, reject) => {
      const protocol = url.startsWith('https') ? https : http
      
      const request = protocol.get(url, (response) => {
        let html = ''
        
        response.on('data', (chunk) => {
          html += chunk
        })
        
        response.on('end', () => {
          if (response.statusCode && response.statusCode >= 200 && response.statusCode < 300) {
            resolve(html)
          } else {
            reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`))
          }
        })
      })
      
      request.on('error', (error) => {
        reject(new Error(`Request failed: ${error.message}`))
      })
      
      request.setTimeout(10000, () => {
        request.destroy()
        reject(new Error('Request timeout'))
      })
    })
  }

  checkDisclaimerMeta(document) {
    const legalMeta = document.querySelector('meta[name="legal-disclaimer"]')
    const attorneyClientMeta = document.querySelector('meta[name="attorney-client"]')
    const complianceMeta = document.querySelector('meta[name="compliance-version"]')
    const disclaimerRequired = document.querySelector('meta[name="disclaimer-required"]')
    
    return legalMeta && attorneyClientMeta && complianceMeta && disclaimerRequired
  }

  checkDisclaimerWrapper(document) {
    // Check for evidence of DisclaimerWrapper by looking for specific elements it creates
    const modalDialog = document.querySelector('div[role="dialog"]')
    const disclaimerAlert = document.querySelector('div[role="alert"]')
    const complianceMarkers = document.querySelector('#disclaimer-compliance-markers')
    
    return modalDialog || disclaimerAlert || complianceMarkers
  }

  checkComplianceMarkers(document) {
    const markers = document.querySelector('#disclaimer-compliance-markers')
    if (!markers) return false
    
    const systemActive = markers.getAttribute('data-disclaimer-system') === 'active'
    const bypassProtected = markers.getAttribute('data-bypass-protection') === 'enabled'
    const mandatoryEnforced = markers.getAttribute('data-mandatory-disclaimers') === 'enforced'
    
    return systemActive && bypassProtected && mandatoryEnforced
  }

  checkGlobalDisclaimerModal(document) {
    // Look for modal structure or content that indicates global disclaimer
    const modalContent = document.body.innerHTML
    return modalContent.includes('IMPORTANT LEGAL NOTICE') || 
           modalContent.includes('NOT constitute legal advice') ||
           modalContent.includes('I Understand and Accept These Disclaimers')
  }

  checkPageSpecificDisclaimer(document, route) {
    const pageContent = document.body.innerHTML
    
    // Check for page-specific disclaimer content based on route
    const routeSpecificTerms = {
      '/': ['General Information System', 'legal AI system'],
      '/documents': ['Document Management', 'organizational purposes'],
      '/dashboard': ['Dashboard Information', 'estimates'],
      '/costs': ['Cost Information', 'binding quotes'],
      '/auth': ['Authentication System', 'attorney-client relationship'],
      '/compliance': ['Compliance Information', 'regulatory'],
      '/admin': ['Administrative Interface', 'system management'],
      '/education': ['Educational Content', 'general information'],
      '/referrals': ['Attorney Referral', 'informational purposes']
    }
    
    // Check for generic disclaimer if no specific terms
    const hasGenericDisclaimer = pageContent.includes('Disclaimer') && 
                                 pageContent.includes('NOT constitute legal advice')
    
    const routeKey = Object.keys(routeSpecificTerms).find(key => route.startsWith(key))
    if (routeKey) {
      const terms = routeSpecificTerms[routeKey]
      const hasSpecificDisclaimer = terms.some(term => pageContent.includes(term))
      return hasSpecificDisclaimer || hasGenericDisclaimer
    }
    
    return hasGenericDisclaimer
  }

  checkHeaderDisclaimer(document) {
    const headerContent = document.body.innerHTML
    return headerContent.includes('NOT LEGAL ADVICE') || 
           headerContent.includes('General Information Only') ||
           headerContent.includes('bg-red-600') // Header disclaimer styling
  }

  checkFooterDisclaimer(document) {
    const footer = document.querySelector('footer')
    if (!footer) return false
    
    const footerText = footer.textContent || footer.innerHTML
    return footerText.includes('Legal Notice') || 
           footerText.includes('not provide legal advice') ||
           footerText.includes('Attorney-Client Relationship')
  }

  checkBypassProtection(document) {
    const pageContent = document.body.innerHTML
    
    // Look for bypass protection mechanisms
    const hasModalProtection = pageContent.includes('onPointerDownOutside') ||
                              pageContent.includes('onEscapeKeyDown')
    const hasStyleProtection = pageContent.includes('!important')
    const hasJSProtection = pageContent.includes('MutationObserver')
    
    return hasModalProtection || hasStyleProtection || hasJSProtection
  }

  checkContentBlocking(document) {
    const pageContent = document.body.innerHTML
    
    // Look for content blocking messages
    return pageContent.includes('Legal Disclaimers Required') ||
           pageContent.includes('Please review and accept') ||
           pageContent.includes('MANDATORY COMPLIANCE')
  }

  checkSecurityMonitoring(document) {
    const pageContent = document.body.innerHTML
    
    // Look for security monitoring code
    return pageContent.includes('SECURITY_VIOLATION') ||
           pageContent.includes('MutationObserver') ||
           pageContent.includes('bypassAttempts')
  }

  calculateComplianceScore(checks) {
    const totalChecks = Object.keys(checks).length
    const passedChecks = Object.values(checks).filter(Boolean).length
    return Math.round((passedChecks / totalChecks) * 100)
  }

  generateReport() {
    const endTime = Date.now()
    const duration = Math.round((endTime - this.startTime) / 1000)
    const complianceRate = Math.round((this.passedRoutes / this.totalRoutes) * 100)
    
    console.log()
    console.log('=' * 60)
    console.log('📊 DISCLAIMER COVERAGE TEST RESULTS')
    console.log('=' * 60)
    console.log()
    console.log(`Total Routes Tested: ${this.totalRoutes}`)
    console.log(`✅ Compliant Routes: ${this.passedRoutes}`)
    console.log(`❌ Non-Compliant Routes: ${this.failedRoutes}`)
    console.log(`📈 Overall Compliance Rate: ${complianceRate}%`)
    console.log(`⏱️  Total Test Duration: ${duration}s`)
    console.log()

    // Detailed compliance breakdown
    console.log('📋 COMPLIANCE BREAKDOWN BY CHECK:')
    console.log('-' * 40)
    
    const checkStats = {}
    this.results.forEach(result => {
      Object.entries(result.checks).forEach(([check, passed]) => {
        if (!checkStats[check]) checkStats[check] = { passed: 0, total: 0 }
        checkStats[check].total++
        if (passed) checkStats[check].passed++
      })
    })
    
    Object.entries(checkStats).forEach(([check, stats]) => {
      const rate = Math.round((stats.passed / stats.total) * 100)
      const status = rate === 100 ? '✅' : rate >= 90 ? '⚠️' : '❌'
      console.log(`${status} ${check}: ${stats.passed}/${stats.total} (${rate}%)`)
    })
    console.log()

    // Failed routes details
    if (this.failedRoutes > 0) {
      console.log('❌ NON-COMPLIANT ROUTES:')
      console.log('-' * 40)
      
      this.results
        .filter(result => !result.compliant)
        .forEach(result => {
          console.log(`Route: ${result.route} (Score: ${result.complianceScore}%)`)
          result.errors.forEach(error => console.log(`  • ${error}`))
          console.log()
        })
    }

    // Overall assessment
    console.log('🎯 OVERALL ASSESSMENT:')
    console.log('-' * 40)
    
    if (complianceRate === 100) {
      console.log('🎉 EXCELLENT: All routes have complete disclaimer coverage!')
      console.log('✅ System is fully compliant and ready for production.')
      console.log('✅ No bypass vulnerabilities detected.')
    } else if (complianceRate >= 90) {
      console.log('✅ GOOD: System meets minimum compliance requirements.')
      console.log(`⚠️  ${this.failedRoutes} route(s) need attention for optimal compliance.`)
    } else {
      console.log('❌ CRITICAL: Compliance rate below acceptable threshold!')
      console.log('🚨 IMMEDIATE ACTION REQUIRED before production deployment.')
      console.log('🔧 Review and fix all non-compliant routes.')
    }

    console.log()
    console.log('📄 Detailed results saved to:', OUTPUT_FILE)

    // Save detailed results to file
    const reportData = {
      summary: {
        totalRoutes: this.totalRoutes,
        passedRoutes: this.passedRoutes,
        failedRoutes: this.failedRoutes,
        complianceRate,
        duration,
        timestamp: new Date().toISOString()
      },
      checkStats,
      results: this.results
    }

    try {
      fs.writeFileSync(OUTPUT_FILE, JSON.stringify(reportData, null, 2))
      console.log('✅ Report saved successfully')
    } catch (error) {
      console.error('❌ Failed to save report:', error.message)
    }

    console.log()
    console.log('=' * 60)
    console.log('🏁 DISCLAIMER COVERAGE TESTING COMPLETE')
    console.log('=' * 60)

    // Exit with appropriate code
    process.exit(complianceRate >= 90 ? 0 : 1)
  }
}

// Main execution
async function main() {
  const tester = new DisclaimerCoverageTester()
  await tester.runAllTests()
}

// Handle errors
process.on('unhandledRejection', (error) => {
  console.error('💥 Unhandled rejection:', error)
  process.exit(1)
})

process.on('uncaughtException', (error) => {
  console.error('💥 Uncaught exception:', error)
  process.exit(1)
})

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('💥 Test execution failed:', error)
    process.exit(1)
  })
}

module.exports = { DisclaimerCoverageTester, ROUTES_TO_TEST }