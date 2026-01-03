#!/usr/bin/env node

/**
 * Simple Disclaimer Coverage Test
 * 
 * Tests disclaimer coverage by analyzing the source code structure
 * and verifying that all necessary disclaimer components are in place.
 * 
 * This test runs without external dependencies and provides immediate feedback.
 */

const fs = require('fs')
const path = require('path')

class SimpleDisclaimerTest {
  constructor() {
    this.results = []
    this.frontendPath = path.resolve(__dirname, '../../')
    this.errors = []
    this.warnings = []
  }

  async runTests() {
    console.log('🔍 SIMPLE DISCLAIMER COVERAGE TEST')
    console.log('=' * 50)
    console.log('Testing disclaimer system configuration...\n')

    // Test 1: Check if DisclaimerWrapper exists and is properly configured
    await this.testDisclaimerWrapperExists()
    
    // Test 2: Check root layout integration
    await this.testRootLayoutIntegration()
    
    // Test 3: Check for all route-specific disclaimers
    await this.testRouteSpecificDisclaimers()
    
    // Test 4: Check bypass protection measures
    await this.testBypassProtectionMeasures()
    
    // Test 5: Check compliance markers
    await this.testComplianceMarkers()
    
    // Test 6: Check for security monitoring
    await this.testSecurityMonitoring()
    
    // Test 7: Analyze route coverage
    await this.analyzeRouteCoverage()

    this.generateReport()
  }

  async testDisclaimerWrapperExists() {
    console.log('1️⃣  Testing DisclaimerWrapper component...')
    
    const wrapperPath = path.join(this.frontendPath, 'src/components/layout/DisclaimerWrapper.tsx')
    
    if (!fs.existsSync(wrapperPath)) {
      this.errors.push('DisclaimerWrapper component not found')
      console.log('   ❌ DisclaimerWrapper.tsx not found')
      return
    }
    
    const wrapperContent = fs.readFileSync(wrapperPath, 'utf8')
    
    // Check for essential features
    const checks = {
      'Global disclaimer modal': wrapperContent.includes('GLOBAL_DISCLAIMER') && wrapperContent.includes('showGlobalModal'),
      'Page-specific disclaimers': wrapperContent.includes('PAGE_SPECIFIC_DISCLAIMERS'),
      'Bypass protection': wrapperContent.includes('bypassAttempts') && wrapperContent.includes('onPointerDownOutside'),
      'Security monitoring': wrapperContent.includes('MutationObserver') && wrapperContent.includes('SECURITY_VIOLATION'),
      'Content blocking': wrapperContent.includes('hasAcceptedGlobal') && wrapperContent.includes('hasAcceptedPageSpecific'),
      'Compliance markers': wrapperContent.includes('disclaimer-compliance-markers'),
      'CSS protection': wrapperContent.includes('!important') && wrapperContent.includes('style jsx'),
      'Session management': wrapperContent.includes('sessionStorage') && wrapperContent.includes('timestamp')
    }
    
    const passedChecks = Object.entries(checks).filter(([_, passed]) => passed)
    const failedChecks = Object.entries(checks).filter(([_, passed]) => !passed)
    
    console.log(`   ✅ DisclaimerWrapper found with ${passedChecks.length}/8 features`)
    
    if (failedChecks.length > 0) {
      console.log('   ⚠️  Missing features:')
      failedChecks.forEach(([feature]) => {
        console.log(`      • ${feature}`)
        this.warnings.push(`DisclaimerWrapper missing: ${feature}`)
      })
    }
    
    this.results.push({
      test: 'DisclaimerWrapper Component',
      passed: failedChecks.length === 0,
      score: Math.round((passedChecks.length / 8) * 100)
    })
  }

  async testRootLayoutIntegration() {
    console.log('2️⃣  Testing root layout integration...')
    
    const layoutPath = path.join(this.frontendPath, 'src/app/layout.tsx')
    
    if (!fs.existsSync(layoutPath)) {
      this.errors.push('Root layout.tsx not found')
      console.log('   ❌ Root layout.tsx not found')
      return
    }
    
    const layoutContent = fs.readFileSync(layoutPath, 'utf8')
    
    const checks = {
      'DisclaimerWrapper import': layoutContent.includes('DisclaimerWrapper'),
      'DisclaimerWrapper usage': layoutContent.includes('<DisclaimerWrapper>'),
      'Legal meta tags': layoutContent.includes('legal-disclaimer') && layoutContent.includes('attorney-client'),
      'Security headers': layoutContent.includes('X-Content-Type-Options') && layoutContent.includes('X-Frame-Options'),
      'Compliance metadata': layoutContent.includes('compliance-version') && layoutContent.includes('disclaimer-required')
    }
    
    const passedChecks = Object.entries(checks).filter(([_, passed]) => passed)
    const failedChecks = Object.entries(checks).filter(([_, passed]) => !passed)
    
    console.log(`   ✅ Root layout integration: ${passedChecks.length}/5 checks passed`)
    
    if (failedChecks.length > 0) {
      failedChecks.forEach(([feature]) => {
        console.log(`   ❌ Missing: ${feature}`)
        this.errors.push(`Root layout missing: ${feature}`)
      })
    }
    
    this.results.push({
      test: 'Root Layout Integration',
      passed: failedChecks.length === 0,
      score: Math.round((passedChecks.length / 5) * 100)
    })
  }

  async testRouteSpecificDisclaimers() {
    console.log('3️⃣  Testing route-specific disclaimer coverage...')
    
    const wrapperPath = path.join(this.frontendPath, 'src/components/layout/DisclaimerWrapper.tsx')
    const wrapperContent = fs.readFileSync(wrapperPath, 'utf8')
    
    // Extract page-specific disclaimers from the file
    const disclaimerMatches = wrapperContent.match(/PAGE_SPECIFIC_DISCLAIMERS[\s\S]*?(?=\n\s*})/g)
    
    if (!disclaimerMatches) {
      this.errors.push('PAGE_SPECIFIC_DISCLAIMERS not found')
      console.log('   ❌ PAGE_SPECIFIC_DISCLAIMERS not found')
      return
    }
    
    const disclaimerSection = disclaimerMatches[0]
    
    // Count routes with disclaimers
    const routeMatches = disclaimerSection.match(/'\//g)
    const routeCount = routeMatches ? routeMatches.length : 0
    
    // Check for key routes
    const keyRoutes = [
      "'/':", "'/dashboard':", "'/documents':", "'/costs':", 
      "'/auth':", "'/compliance':", "'/admin':", "'/education':",
      "'/referrals':", "'/client-portal':", "'/mobile':"
    ]
    
    const coveredRoutes = keyRoutes.filter(route => disclaimerSection.includes(route))
    
    console.log(`   ✅ Route-specific disclaimers: ${routeCount} total routes covered`)
    console.log(`   ✅ Key routes covered: ${coveredRoutes.length}/${keyRoutes.length}`)
    
    if (coveredRoutes.length < keyRoutes.length) {
      const missingRoutes = keyRoutes.filter(route => !disclaimerSection.includes(route))
      console.log('   ⚠️  Missing disclaimers for:')
      missingRoutes.forEach(route => {
        console.log(`      • ${route.replace(':', '')}`)
        this.warnings.push(`Missing disclaimer for route: ${route}`)
      })
    }
    
    this.results.push({
      test: 'Route-Specific Disclaimers',
      passed: coveredRoutes.length >= keyRoutes.length * 0.9, // 90% threshold
      score: Math.round((coveredRoutes.length / keyRoutes.length) * 100)
    })
  }

  async testBypassProtectionMeasures() {
    console.log('4️⃣  Testing bypass protection measures...')
    
    const wrapperPath = path.join(this.frontendPath, 'src/components/layout/DisclaimerWrapper.tsx')
    const wrapperContent = fs.readFileSync(wrapperPath, 'utf8')
    
    const protectionMeasures = {
      'Modal escape blocking': wrapperContent.includes('onEscapeKeyDown') && wrapperContent.includes('preventDefault'),
      'Outside click blocking': wrapperContent.includes('onPointerDownOutside') && wrapperContent.includes('preventDefault'),
      'Bypass attempt tracking': wrapperContent.includes('bypassAttempts') && wrapperContent.includes('setBypassAttempts'),
      'System lockout': wrapperContent.includes('isLocked') && wrapperContent.includes('ACCESS RESTRICTED'),
      'CSS override protection': wrapperContent.includes('!important') && wrapperContent.includes('display: block'),
      'DOM manipulation monitoring': wrapperContent.includes('MutationObserver') && wrapperContent.includes('style'),
      'Security violation logging': wrapperContent.includes('logSecurityViolation') && wrapperContent.includes('SECURITY_VIOLATION')
    }
    
    const enabledProtections = Object.entries(protectionMeasures).filter(([_, enabled]) => enabled)
    const missingProtections = Object.entries(protectionMeasures).filter(([_, enabled]) => !enabled)
    
    console.log(`   ✅ Bypass protection: ${enabledProtections.length}/7 measures active`)
    
    if (missingProtections.length > 0) {
      console.log('   ⚠️  Missing protections:')
      missingProtections.forEach(([protection]) => {
        console.log(`      • ${protection}`)
        this.warnings.push(`Missing bypass protection: ${protection}`)
      })
    }
    
    this.results.push({
      test: 'Bypass Protection Measures',
      passed: missingProtections.length === 0,
      score: Math.round((enabledProtections.length / 7) * 100)
    })
  }

  async testComplianceMarkers() {
    console.log('5️⃣  Testing compliance markers...')
    
    const wrapperPath = path.join(this.frontendPath, 'src/components/layout/DisclaimerWrapper.tsx')
    const wrapperContent = fs.readFileSync(wrapperPath, 'utf8')
    
    const markerChecks = {
      'Compliance markers element': wrapperContent.includes('disclaimer-compliance-markers'),
      'System status markers': wrapperContent.includes('data-disclaimer-system') && wrapperContent.includes('data-bypass-protection'),
      'Acceptance tracking': wrapperContent.includes('data-disclaimer-accepted-global') && wrapperContent.includes('data-disclaimer-accepted-page'),
      'Timestamp tracking': wrapperContent.includes('data-disclaimer-timestamp'),
      'Security status': wrapperContent.includes('data-bypass-attempts') && wrapperContent.includes('data-system-locked'),
      'Version tracking': wrapperContent.includes('data-compliance-version')
    }
    
    const presentMarkers = Object.entries(markerChecks).filter(([_, present]) => present)
    const missingMarkers = Object.entries(markerChecks).filter(([_, present]) => !present)
    
    console.log(`   ✅ Compliance markers: ${presentMarkers.length}/6 markers present`)
    
    if (missingMarkers.length > 0) {
      missingMarkers.forEach(([marker]) => {
        console.log(`   ❌ Missing: ${marker}`)
        this.errors.push(`Missing compliance marker: ${marker}`)
      })
    }
    
    this.results.push({
      test: 'Compliance Markers',
      passed: missingMarkers.length === 0,
      score: Math.round((presentMarkers.length / 6) * 100)
    })
  }

  async testSecurityMonitoring() {
    console.log('6️⃣  Testing security monitoring...')
    
    const wrapperPath = path.join(this.frontendPath, 'src/components/layout/DisclaimerWrapper.tsx')
    const wrapperContent = fs.readFileSync(wrapperPath, 'utf8')
    
    const monitoringFeatures = {
      'DOM mutation monitoring': wrapperContent.includes('MutationObserver'),
      'Style manipulation detection': wrapperContent.includes('attributeName === \'style\''),
      'Security violation logging': wrapperContent.includes('[SECURITY_VIOLATION]'),
      'Bypass attempt counting': wrapperContent.includes('bypassAttempts') && wrapperContent.includes('prev => prev + 1'),
      'Periodic monitoring': wrapperContent.includes('setInterval') && wrapperContent.includes('detectBypass')
    }
    
    const activeFeatures = Object.entries(monitoringFeatures).filter(([_, active]) => active)
    const inactiveFeatures = Object.entries(monitoringFeatures).filter(([_, active]) => !active)
    
    console.log(`   ✅ Security monitoring: ${activeFeatures.length}/5 features active`)
    
    if (inactiveFeatures.length > 0) {
      inactiveFeatures.forEach(([feature]) => {
        console.log(`   ⚠️  Inactive: ${feature}`)
        this.warnings.push(`Inactive security monitoring: ${feature}`)
      })
    }
    
    this.results.push({
      test: 'Security Monitoring',
      passed: inactiveFeatures.length <= 1, // Allow one missing feature
      score: Math.round((activeFeatures.length / 5) * 100)
    })
  }

  async analyzeRouteCoverage() {
    console.log('7️⃣  Analyzing route coverage...')
    
    // Check for app routes
    const appPath = path.join(this.frontendPath, 'src/app')
    const routes = this.findAppRoutes(appPath)
    
    console.log(`   ✅ Found ${routes.length} app routes`)
    
    // Log some example routes
    const exampleRoutes = routes.slice(0, 10)
    if (exampleRoutes.length > 0) {
      console.log('   📋 Example routes found:')
      exampleRoutes.forEach(route => console.log(`      • ${route}`))
      if (routes.length > 10) {
        console.log(`      • ... and ${routes.length - 10} more`)
      }
    }
    
    this.results.push({
      test: 'Route Coverage Analysis',
      passed: routes.length > 0,
      score: routes.length > 15 ? 100 : Math.round((routes.length / 15) * 100)
    })
  }

  findAppRoutes(dir, basePath = '', routes = []) {
    try {
      const items = fs.readdirSync(dir, { withFileTypes: true })
      
      for (const item of items) {
        const fullPath = path.join(dir, item.name)
        const routePath = path.join(basePath, item.name)
        
        if (item.isDirectory()) {
          // Skip node_modules and other non-route directories
          if (!item.name.startsWith('.') && item.name !== 'node_modules') {
            this.findAppRoutes(fullPath, routePath, routes)
          }
        } else if (item.name === 'page.tsx' || item.name === 'layout.tsx') {
          // Convert filesystem path to route
          let route = basePath.replace(/\\/g, '/') // Convert Windows paths
          route = route.replace(/\[([^\]]+)\]/g, ':$1') // Convert [param] to :param
          if (route === '' || route === '/') route = '/'
          else if (!route.startsWith('/')) route = '/' + route
          
          routes.push(route)
        }
      }
    } catch (error) {
      // Ignore errors for inaccessible directories
    }
    
    return routes
  }

  generateReport() {
    console.log('\n' + '=' * 50)
    console.log('📊 DISCLAIMER TEST RESULTS')
    console.log('=' * 50)
    
    const totalTests = this.results.length
    const passedTests = this.results.filter(r => r.passed).length
    const failedTests = totalTests - passedTests
    const overallScore = Math.round(this.results.reduce((sum, r) => sum + r.score, 0) / totalTests)
    
    console.log(`\nOverall Results:`)
    console.log(`✅ Passed Tests: ${passedTests}/${totalTests}`)
    console.log(`❌ Failed Tests: ${failedTests}/${totalTests}`)
    console.log(`📈 Overall Score: ${overallScore}%`)
    console.log(`⚠️  Warnings: ${this.warnings.length}`)
    console.log(`🚨 Errors: ${this.errors.length}`)
    
    console.log(`\nDetailed Results:`)
    console.log('-' * 30)
    this.results.forEach(result => {
      const status = result.passed ? '✅' : '❌'
      console.log(`${status} ${result.test}: ${result.score}%`)
    })
    
    if (this.warnings.length > 0) {
      console.log(`\n⚠️  Warnings:`)
      this.warnings.forEach(warning => console.log(`   • ${warning}`))
    }
    
    if (this.errors.length > 0) {
      console.log(`\n🚨 Errors:`)
      this.errors.forEach(error => console.log(`   • ${error}`))
    }
    
    console.log(`\n🎯 Assessment:`)
    if (overallScore >= 95 && this.errors.length === 0) {
      console.log('🎉 EXCELLENT: Disclaimer system is fully configured and production-ready!')
    } else if (overallScore >= 85 && this.errors.length <= 2) {
      console.log('✅ GOOD: Disclaimer system meets requirements with minor issues.')
    } else if (overallScore >= 70) {
      console.log('⚠️  ACCEPTABLE: Disclaimer system functional but needs improvements.')
    } else {
      console.log('❌ CRITICAL: Disclaimer system requires immediate attention!')
    }
    
    console.log('\n' + '=' * 50)
    console.log('🏁 DISCLAIMER TEST COMPLETE')
    console.log('=' * 50)
  }
}

// Main execution
async function main() {
  const tester = new SimpleDisclaimerTest()
  await tester.runTests()
}

// Run if called directly
if (require.main === module) {
  main().catch(error => {
    console.error('💥 Test failed:', error)
    process.exit(1)
  })
}

module.exports = { SimpleDisclaimerTest }