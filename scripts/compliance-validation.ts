#!/usr/bin/env ts-node

/**
 * Legal AI System - Compliance Validation Script
 * 
 * This script performs comprehensive compliance validation across the entire system
 * to ensure adherence to professional responsibility rules and UPL prevention standards.
 * 
 * Usage: npm run compliance:validate
 */

import { promises as fs } from 'fs';
import path from 'path';
import chalk from 'chalk';

interface ComplianceCheck {
  id: string;
  name: string;
  description: string;
  status: 'pass' | 'fail' | 'warning' | 'pending';
  details: string[];
  recommendations?: string[];
}

interface ValidationResult {
  timestamp: string;
  overallStatus: 'pass' | 'fail' | 'warning';
  totalChecks: number;
  passedChecks: number;
  failedChecks: number;
  warningChecks: number;
  complianceScore: number;
  checks: ComplianceCheck[];
}

class ComplianceValidator {
  private frontendPath: string;
  private backendPath: string;
  private results: ComplianceCheck[] = [];

  constructor() {
    this.frontendPath = path.join(process.cwd(), 'frontend');
    this.backendPath = path.join(process.cwd(), 'backend');
  }

  async runFullValidation(): Promise<ValidationResult> {
    console.log(chalk.blue('🔍 Starting Legal AI System Compliance Validation\n'));
    
    // Run all compliance checks
    await this.check1_AIOutputDisclaimers();
    await this.check2_NoAdviceLanguage();
    await this.check3_AttorneyReviewFlags();
    await this.check4_StateRulesApplication();
    await this.check5_AuditLoggingFunction();
    await this.check6_UserAcknowledgmentTracking();
    await this.check7_EducationalContentAccess();
    await this.check8_ReferralSystemDisclaimers();

    // Calculate results
    const totalChecks = this.results.length;
    const passedChecks = this.results.filter(r => r.status === 'pass').length;
    const failedChecks = this.results.filter(r => r.status === 'fail').length;
    const warningChecks = this.results.filter(r => r.status === 'warning').length;
    
    const complianceScore = Math.round((passedChecks / totalChecks) * 100);
    const overallStatus = failedChecks > 0 ? 'fail' : warningChecks > 0 ? 'warning' : 'pass';

    return {
      timestamp: new Date().toISOString(),
      overallStatus,
      totalChecks,
      passedChecks,
      failedChecks,
      warningChecks,
      complianceScore,
      checks: this.results
    };
  }

  private async check1_AIOutputDisclaimers(): Promise<void> {
    console.log(chalk.yellow('📋 Check 1: AI Output Disclaimers'));
    
    const check: ComplianceCheck = {
      id: 'ai-output-disclaimers',
      name: 'AI Output Disclaimer Coverage',
      description: 'Verify all AI outputs include appropriate legal disclaimers',
      status: 'pending',
      details: []
    };

    try {
      // Check AI response components
      const aiComponents = await this.findFiles(this.frontendPath, /AI|Response|Analysis/i);
      const disclaimerComponents = await this.findFiles(this.frontendPath, /Disclaimer|Warning|Notice/i);
      
      check.details.push(`Found ${aiComponents.length} AI-related components`);
      check.details.push(`Found ${disclaimerComponents.length} disclaimer components`);

      // Check for disclaimer imports in AI components
      let componentsWithDisclaimers = 0;
      for (const component of aiComponents) {
        const content = await fs.readFile(component, 'utf-8');
        if (content.includes('disclaimer') || content.includes('Disclaimer') || 
            content.includes('warning') || content.includes('Warning') ||
            content.includes('notice') || content.includes('Notice')) {
          componentsWithDisclaimers++;
        }
      }

      const disclaimerCoverage = (componentsWithDisclaimers / Math.max(aiComponents.length, 1)) * 100;
      check.details.push(`Disclaimer coverage: ${disclaimerCoverage.toFixed(1)}% of AI components`);

      if (disclaimerCoverage >= 90) {
        check.status = 'pass';
        check.details.push('✅ Excellent disclaimer coverage across AI components');
      } else if (disclaimerCoverage >= 75) {
        check.status = 'warning';
        check.details.push('⚠️  Good disclaimer coverage, some components may need review');
        check.recommendations = ['Review AI components without disclaimer references'];
      } else {
        check.status = 'fail';
        check.details.push('❌ Insufficient disclaimer coverage');
        check.recommendations = ['Add disclaimers to all AI output components'];
      }

      // Check for specific disclaimer types
      const requiredDisclaimers = [
        'upl_prevention',
        'attorney_client',
        'information_only',
        'professional_review'
      ];

      for (const disclaimerType of requiredDisclaimers) {
        const found = await this.searchInFiles(this.frontendPath, disclaimerType);
        if (found.length > 0) {
          check.details.push(`✅ Found ${disclaimerType} disclaimers in ${found.length} files`);
        } else {
          check.details.push(`⚠️  ${disclaimerType} disclaimers not found`);
          if (check.status === 'pass') check.status = 'warning';
        }
      }

    } catch (error) {
      check.status = 'fail';
      check.details.push(`❌ Error during validation: ${error}`);
    }

    this.results.push(check);
    this.printCheckResult(check);
  }

  private async check2_NoAdviceLanguage(): Promise<void> {
    console.log(chalk.yellow('⚖️  Check 2: No Legal Advice Language'));
    
    const check: ComplianceCheck = {
      id: 'no-advice-language',
      name: 'Legal Advice Language Detection',
      description: 'Ensure no unauthorized legal advice language in system responses',
      status: 'pending',
      details: []
    };

    try {
      // Define prohibited advice language patterns
      const prohibitedPatterns = [
        'you should hire',
        'I recommend that you',
        'you must',
        'you should file',
        'you need to',
        'the best course of action',
        'I advise you to',
        'you should sue',
        'you have a strong case',
        'you should settle',
        'this will win in court',
        'you should plead'
      ];

      const allowedInformationalPatterns = [
        'generally speaking',
        'typically',
        'in most cases',
        'commonly',
        'for educational purposes',
        'this information suggests',
        'research indicates',
        'studies show'
      ];

      // Check all response templates and AI-related files
      const responseFiles = await this.findFiles(this.frontendPath, /(response|template|ai|prompt)/i);
      let violationCount = 0;
      let checkedFiles = 0;

      for (const file of responseFiles) {
        try {
          const content = await fs.readFile(file, 'utf-8');
          checkedFiles++;

          for (const pattern of prohibitedPatterns) {
            if (content.toLowerCase().includes(pattern.toLowerCase())) {
              violationCount++;
              check.details.push(`⚠️  Found prohibited pattern "${pattern}" in ${path.basename(file)}`);
            }
          }

          // Check for proper informational language
          const hasInformationalLanguage = allowedInformationalPatterns.some(pattern => 
            content.toLowerCase().includes(pattern.toLowerCase())
          );
          
          if (hasInformationalLanguage) {
            check.details.push(`✅ Found proper informational language in ${path.basename(file)}`);
          }
        } catch (err) {
          // Skip files that can't be read
        }
      }

      check.details.push(`Checked ${checkedFiles} response-related files`);
      check.details.push(`Found ${violationCount} potential advice language violations`);

      if (violationCount === 0) {
        check.status = 'pass';
        check.details.push('✅ No prohibited legal advice language detected');
      } else if (violationCount <= 3) {
        check.status = 'warning';
        check.details.push('⚠️  Minor advice language issues detected');
        check.recommendations = ['Review flagged files and replace advice language with informational language'];
      } else {
        check.status = 'fail';
        check.details.push('❌ Multiple advice language violations found');
        check.recommendations = ['Comprehensive review and replacement of advice language required'];
      }

    } catch (error) {
      check.status = 'fail';
      check.details.push(`❌ Error during validation: ${error}`);
    }

    this.results.push(check);
    this.printCheckResult(check);
  }

  private async check3_AttorneyReviewFlags(): Promise<void> {
    console.log(chalk.yellow('👨‍⚖️ Check 3: Attorney Review Flags'));
    
    const check: ComplianceCheck = {
      id: 'attorney-review-flags',
      name: 'Attorney Review Flag System',
      description: 'Verify attorney review flagging mechanisms are properly implemented',
      status: 'pending',
      details: []
    };

    try {
      // Check for attorney review components and logic
      const reviewComponents = await this.searchInFiles(this.frontendPath, 'attorney.*review|review.*attorney');
      const flagComponents = await this.searchInFiles(this.frontendPath, 'flag|Flag');
      const supervisionComponents = await this.searchInFiles(this.frontendPath, 'supervis|Supervis');

      check.details.push(`Found ${reviewComponents.length} attorney review references`);
      check.details.push(`Found ${flagComponents.length} flagging mechanism references`);
      check.details.push(`Found ${supervisionComponents.length} supervision references`);

      // Check for specific review triggers
      const reviewTriggers = [
        'risk.*level.*high',
        'upl.*warning',
        'advice.*detected',
        'attorney.*required',
        'professional.*review'
      ];

      let triggersFound = 0;
      for (const trigger of reviewTriggers) {
        const found = await this.searchInFiles(this.frontendPath, trigger);
        if (found.length > 0) {
          triggersFound++;
          check.details.push(`✅ Found review trigger pattern: ${trigger}`);
        }
      }

      const triggerCoverage = (triggersFound / reviewTriggers.length) * 100;
      check.details.push(`Review trigger coverage: ${triggerCoverage.toFixed(1)}%`);

      // Check for attorney role verification
      const roleVerification = await this.searchInFiles(this.frontendPath, 'attorney.*role|role.*attorney|bar.*number|attorney.*verify');
      check.details.push(`Found ${roleVerification.length} attorney role verification references`);

      if (reviewComponents.length >= 3 && triggerCoverage >= 80 && roleVerification.length >= 2) {
        check.status = 'pass';
        check.details.push('✅ Attorney review system appears comprehensive');
      } else if (reviewComponents.length >= 2 && triggerCoverage >= 60) {
        check.status = 'warning';
        check.details.push('⚠️  Attorney review system present but may need enhancement');
        check.recommendations = ['Enhance review trigger coverage', 'Add more attorney verification checks'];
      } else {
        check.status = 'fail';
        check.details.push('❌ Attorney review system insufficient');
        check.recommendations = ['Implement comprehensive attorney review system'];
      }

    } catch (error) {
      check.status = 'fail';
      check.details.push(`❌ Error during validation: ${error}`);
    }

    this.results.push(check);
    this.printCheckResult(check);
  }

  private async check4_StateRulesApplication(): Promise<void> {
    console.log(chalk.yellow('🏛️  Check 4: State Rules Application'));
    
    const check: ComplianceCheck = {
      id: 'state-rules-application',
      name: 'State-Specific Rule Application',
      description: 'Verify state-specific legal rules are properly applied',
      status: 'pending',
      details: []
    };

    try {
      // Check for state-specific components and logic
      const stateComponents = await this.searchInFiles(this.frontendPath, 'state|State|jurisdiction|Jurisdiction');
      const ruleComponents = await this.searchInFiles(this.frontendPath, 'rule|Rule|regulation|Regulation');

      check.details.push(`Found ${stateComponents.length} state/jurisdiction references`);
      check.details.push(`Found ${ruleComponents.length} rule/regulation references`);

      // Check for specific state implementations
      const commonStates = ['CA', 'NY', 'TX', 'FL'];
      let stateImplementations = 0;

      for (const state of commonStates) {
        const found = await this.searchInFiles(this.frontendPath, `['"]${state}['"]|${state}.*rule|${state}.*law`);
        if (found.length > 0) {
          stateImplementations++;
          check.details.push(`✅ Found ${state} state-specific implementations`);
        }
      }

      const statesCoverage = (stateImplementations / commonStates.length) * 100;
      check.details.push(`State coverage: ${statesCoverage.toFixed(1)}% of major jurisdictions`);

      // Check for state rule management
      const stateRuleManager = await this.searchInFiles(this.frontendPath, 'StateRulesManager|state.*rules.*manager');
      if (stateRuleManager.length > 0) {
        check.details.push('✅ Found state rules management system');
      }

      // Check for jurisdiction detection
      const jurisdictionDetection = await this.searchInFiles(this.frontendPath, 'jurisdiction.*detect|detect.*jurisdiction|location.*based');
      if (jurisdictionDetection.length > 0) {
        check.details.push('✅ Found jurisdiction detection capabilities');
      }

      if (statesCoverage >= 75 && stateRuleManager.length > 0 && jurisdictionDetection.length > 0) {
        check.status = 'pass';
        check.details.push('✅ Comprehensive state rules application system');
      } else if (statesCoverage >= 50 && (stateRuleManager.length > 0 || jurisdictionDetection.length > 0)) {
        check.status = 'warning';
        check.details.push('⚠️  State rules system present but could be enhanced');
        check.recommendations = ['Expand state coverage', 'Enhance jurisdiction detection'];
      } else {
        check.status = 'fail';
        check.details.push('❌ Insufficient state rules application');
        check.recommendations = ['Implement comprehensive state rules management system'];
      }

    } catch (error) {
      check.status = 'fail';
      check.details.push(`❌ Error during validation: ${error}`);
    }

    this.results.push(check);
    this.printCheckResult(check);
  }

  private async check5_AuditLoggingFunction(): Promise<void> {
    console.log(chalk.yellow('📊 Check 5: Audit Logging Function'));
    
    const check: ComplianceCheck = {
      id: 'audit-logging',
      name: 'Audit Logging System',
      description: 'Verify comprehensive audit logging is functioning correctly',
      status: 'pending',
      details: []
    };

    try {
      // Check for audit logging components
      const auditComponents = await this.searchInFiles(this.frontendPath, 'audit|Audit|log|Log');
      const loggingComponents = await this.searchInFiles(this.frontendPath, 'logging|Logger|audit.*trail');

      check.details.push(`Found ${auditComponents.length} audit-related references`);
      check.details.push(`Found ${loggingComponents.length} logging system references`);

      // Check for specific audit features
      const auditFeatures = [
        'user.*session.*log',
        'compliance.*log',
        'access.*log',
        'audit.*trail',
        'pii.*mask',
        'data.*redact'
      ];

      let featuresFound = 0;
      for (const feature of auditFeatures) {
        const found = await this.searchInFiles(this.frontendPath, feature);
        if (found.length > 0) {
          featuresFound++;
          check.details.push(`✅ Found audit feature: ${feature}`);
        }
      }

      const auditCoverage = (featuresFound / auditFeatures.length) * 100;
      check.details.push(`Audit feature coverage: ${auditCoverage.toFixed(1)}%`);

      // Check for audit interface
      const auditInterface = await this.searchInFiles(this.frontendPath, 'admin.*audit|audit.*page|audit.*interface');
      if (auditInterface.length > 0) {
        check.details.push('✅ Found audit interface implementation');
      }

      // Check for PII protection in audit logs
      const piiProtection = await this.searchInFiles(this.frontendPath, 'mask|redact|anonymize|privacy');
      if (piiProtection.length >= 3) {
        check.details.push('✅ Found PII protection mechanisms');
      }

      if (auditCoverage >= 80 && auditInterface.length > 0 && piiProtection.length >= 3) {
        check.status = 'pass';
        check.details.push('✅ Comprehensive audit logging system detected');
      } else if (auditCoverage >= 60 && auditInterface.length > 0) {
        check.status = 'warning';
        check.details.push('⚠️  Audit logging present but may need enhancement');
        check.recommendations = ['Enhance audit feature coverage', 'Strengthen PII protection'];
      } else {
        check.status = 'fail';
        check.details.push('❌ Insufficient audit logging capabilities');
        check.recommendations = ['Implement comprehensive audit logging system'];
      }

    } catch (error) {
      check.status = 'fail';
      check.details.push(`❌ Error during validation: ${error}`);
    }

    this.results.push(check);
    this.printCheckResult(check);
  }

  private async check6_UserAcknowledgmentTracking(): Promise<void> {
    console.log(chalk.yellow('✅ Check 6: User Acknowledgment Tracking'));
    
    const check: ComplianceCheck = {
      id: 'user-acknowledgment-tracking',
      name: 'User Acknowledgment Tracking System',
      description: 'Verify user acknowledgment tracking is comprehensive and functional',
      status: 'pending',
      details: []
    };

    try {
      // Check for acknowledgment components
      const acknowledgmentComponents = await this.searchInFiles(this.frontendPath, 'acknowledgment|Acknowledgment|acknowledge|Acknowledge');
      const trackingComponents = await this.searchInFiles(this.frontendPath, 'track|Track|analytics|Analytics');

      check.details.push(`Found ${acknowledgmentComponents.length} acknowledgment references`);
      check.details.push(`Found ${trackingComponents.length} tracking references`);

      // Check for specific acknowledgment features
      const acknowledgmentFeatures = [
        'acknowledgment.*rate',
        'disclaimer.*track',
        'user.*acknowledge',
        'acknowledgment.*log',
        'consent.*track',
        'agreement.*track'
      ];

      let featuresFound = 0;
      for (const feature of acknowledgmentFeatures) {
        const found = await this.searchInFiles(this.frontendPath, feature);
        if (found.length > 0) {
          featuresFound++;
          check.details.push(`✅ Found acknowledgment feature: ${feature}`);
        }
      }

      const acknowledgmentCoverage = (featuresFound / acknowledgmentFeatures.length) * 100;
      check.details.push(`Acknowledgment tracking coverage: ${acknowledgmentCoverage.toFixed(1)}%`);

      // Check for UserAcknowledgments component
      const userAckComponent = await this.searchInFiles(this.frontendPath, 'UserAcknowledgments');
      if (userAckComponent.length > 0) {
        check.details.push('✅ Found UserAcknowledgments component');
      }

      // Check for acknowledgment analytics
      const analytics = await this.searchInFiles(this.frontendPath, 'acknowledgment.*analytics|analytics.*acknowledgment|drop.*off.*rate');
      if (analytics.length > 0) {
        check.details.push('✅ Found acknowledgment analytics capabilities');
      }

      if (acknowledgmentCoverage >= 70 && userAckComponent.length > 0 && analytics.length > 0) {
        check.status = 'pass';
        check.details.push('✅ Comprehensive acknowledgment tracking system');
      } else if (acknowledgmentCoverage >= 50 && acknowledgmentComponents.length >= 5) {
        check.status = 'warning';
        check.details.push('⚠️  Acknowledgment tracking present but could be enhanced');
        check.recommendations = ['Enhance acknowledgment analytics', 'Add more tracking features'];
      } else {
        check.status = 'fail';
        check.details.push('❌ Insufficient acknowledgment tracking');
        check.recommendations = ['Implement comprehensive acknowledgment tracking system'];
      }

    } catch (error) {
      check.status = 'fail';
      check.details.push(`❌ Error during validation: ${error}`);
    }

    this.results.push(check);
    this.printCheckResult(check);
  }

  private async check7_EducationalContentAccess(): Promise<void> {
    console.log(chalk.yellow('📚 Check 7: Educational Content Accessibility'));
    
    const check: ComplianceCheck = {
      id: 'educational-content-access',
      name: 'Educational Content Accessibility',
      description: 'Verify educational content is properly accessible and marked as such',
      status: 'pending',
      details: []
    };

    try {
      // Check for educational content markers
      const educationalComponents = await this.searchInFiles(this.frontendPath, 'educational|Educational|education|Education');
      const informationalComponents = await this.searchInFiles(this.frontendPath, 'informational|Information|info|Info');
      const resourceComponents = await this.searchInFiles(this.frontendPath, 'resource|Resource|guide|Guide');

      check.details.push(`Found ${educationalComponents.length} educational content references`);
      check.details.push(`Found ${informationalComponents.length} informational content references`);
      check.details.push(`Found ${resourceComponents.length} resource/guide references`);

      // Check for accessibility features
      const accessibilityFeatures = [
        'aria-',
        'alt=',
        'role=',
        'tabindex',
        'accessibility',
        'a11y'
      ];

      let accessibilityScore = 0;
      for (const feature of accessibilityFeatures) {
        const found = await this.searchInFiles(this.frontendPath, feature);
        if (found.length > 0) {
          accessibilityScore++;
          check.details.push(`✅ Found accessibility feature: ${feature}`);
        }
      }

      const accessibilityCoverage = (accessibilityScore / accessibilityFeatures.length) * 100;
      check.details.push(`Accessibility coverage: ${accessibilityCoverage.toFixed(1)}%`);

      // Check for educational disclaimers
      const educationalDisclaimers = await this.searchInFiles(this.frontendPath, 'educational.*purpose|for.*educational|informational.*only');
      if (educationalDisclaimers.length > 0) {
        check.details.push('✅ Found educational purpose disclaimers');
      }

      // Check for content organization
      const contentOrg = await this.searchInFiles(this.frontendPath, 'faq|FAQ|help|Help|tutorial|Tutorial');
      if (contentOrg.length > 0) {
        check.details.push('✅ Found organized educational content');
      }

      const totalEducationalContent = educationalComponents.length + informationalComponents.length + resourceComponents.length;

      if (totalEducationalContent >= 10 && accessibilityCoverage >= 70 && educationalDisclaimers.length > 0) {
        check.status = 'pass';
        check.details.push('✅ Educational content is well-organized and accessible');
      } else if (totalEducationalContent >= 5 && accessibilityCoverage >= 50) {
        check.status = 'warning';
        check.details.push('⚠️  Educational content present but accessibility could be improved');
        check.recommendations = ['Enhance accessibility features', 'Add more educational disclaimers'];
      } else {
        check.status = 'fail';
        check.details.push('❌ Insufficient educational content accessibility');
        check.recommendations = ['Implement comprehensive educational content system'];
      }

    } catch (error) {
      check.status = 'fail';
      check.details.push(`❌ Error during validation: ${error}`);
    }

    this.results.push(check);
    this.printCheckResult(check);
  }

  private async check8_ReferralSystemDisclaimers(): Promise<void> {
    console.log(chalk.yellow('🔄 Check 8: Referral System Disclaimers'));
    
    const check: ComplianceCheck = {
      id: 'referral-system-disclaimers',
      name: 'Referral System Disclaimer Coverage',
      description: 'Verify referral system includes appropriate disclaimers and professional notices',
      status: 'pending',
      details: []
    };

    try {
      // Check for referral system components
      const referralComponents = await this.searchInFiles(this.frontendPath, 'referral|Referral|refer|Refer');
      const attorneyReferral = await this.searchInFiles(this.frontendPath, 'attorney.*referral|referral.*attorney|find.*attorney');
      const professionalReferral = await this.searchInFiles(this.frontendPath, 'professional.*referral|legal.*professional');

      check.details.push(`Found ${referralComponents.length} referral system references`);
      check.details.push(`Found ${attorneyReferral.length} attorney referral references`);
      check.details.push(`Found ${professionalReferral.length} professional referral references`);

      // Check for referral disclaimers
      const referralDisclaimers = [
        'referral.*disclaimer',
        'no.*endorsement',
        'independent.*attorney',
        'not.*recommendation',
        'professional.*responsibility',
        'attorney.*relationship'
      ];

      let disclaimersFound = 0;
      for (const disclaimer of referralDisclaimers) {
        const found = await this.searchInFiles(this.frontendPath, disclaimer);
        if (found.length > 0) {
          disclaimersFound++;
          check.details.push(`✅ Found referral disclaimer: ${disclaimer}`);
        }
      }

      const disclaimerCoverage = (disclaimersFound / referralDisclaimers.length) * 100;
      check.details.push(`Referral disclaimer coverage: ${disclaimerCoverage.toFixed(1)}%`);

      // Check for professional verification in referrals
      const verification = await this.searchInFiles(this.frontendPath, 'verify.*attorney|attorney.*verify|bar.*check|license.*verify');
      if (verification.length > 0) {
        check.details.push('✅ Found attorney verification in referral system');
      }

      // Check for referral tracking
      const tracking = await this.searchInFiles(this.frontendPath, 'referral.*track|track.*referral|referral.*log');
      if (tracking.length > 0) {
        check.details.push('✅ Found referral tracking capabilities');
      }

      const totalReferralReferences = referralComponents.length + attorneyReferral.length;

      if (totalReferralReferences >= 5 && disclaimerCoverage >= 60 && verification.length > 0) {
        check.status = 'pass';
        check.details.push('✅ Referral system has appropriate disclaimers and safeguards');
      } else if (totalReferralReferences >= 3 && disclaimerCoverage >= 40) {
        check.status = 'warning';
        check.details.push('⚠️  Referral system present but disclaimers could be enhanced');
        check.recommendations = ['Add more referral disclaimers', 'Enhance attorney verification'];
      } else if (totalReferralReferences > 0) {
        check.status = 'fail';
        check.details.push('❌ Referral system lacks sufficient disclaimers');
        check.recommendations = ['Add comprehensive referral disclaimers', 'Implement attorney verification'];
      } else {
        check.status = 'warning';
        check.details.push('⚠️  No referral system detected - may need implementation');
        check.recommendations = ['Consider implementing attorney referral system with proper disclaimers'];
      }

    } catch (error) {
      check.status = 'fail';
      check.details.push(`❌ Error during validation: ${error}`);
    }

    this.results.push(check);
    this.printCheckResult(check);
  }

  private async findFiles(dir: string, pattern: RegExp): Promise<string[]> {
    const files: string[] = [];
    
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
          const subFiles = await this.findFiles(fullPath, pattern);
          files.push(...subFiles);
        } else if (entry.isFile() && (entry.name.endsWith('.ts') || entry.name.endsWith('.tsx')) && pattern.test(entry.name)) {
          files.push(fullPath);
        }
      }
    } catch (error) {
      // Directory doesn't exist or can't be read
    }
    
    return files;
  }

  private async searchInFiles(dir: string, pattern: string): Promise<string[]> {
    const matches: string[] = [];
    const regex = new RegExp(pattern, 'gi');
    
    try {
      const allFiles = await this.findFiles(dir, /\.(ts|tsx|js|jsx)$/);
      
      for (const file of allFiles) {
        try {
          const content = await fs.readFile(file, 'utf-8');
          if (regex.test(content)) {
            matches.push(file);
          }
        } catch (error) {
          // Skip files that can't be read
        }
      }
    } catch (error) {
      // Directory doesn't exist
    }
    
    return matches;
  }

  private printCheckResult(check: ComplianceCheck): void {
    const statusIcon = {
      pass: '✅',
      warning: '⚠️ ',
      fail: '❌',
      pending: '⏳'
    }[check.status];

    const statusColor = {
      pass: chalk.green,
      warning: chalk.yellow,
      fail: chalk.red,
      pending: chalk.gray
    }[check.status];

    console.log(statusColor(`${statusIcon} ${check.name}: ${check.status.toUpperCase()}`));
    
    if (check.details.length > 0) {
      check.details.forEach(detail => console.log(`   ${detail}`));
    }
    
    if (check.recommendations && check.recommendations.length > 0) {
      console.log(chalk.cyan('   Recommendations:'));
      check.recommendations.forEach(rec => console.log(chalk.cyan(`   • ${rec}`)));
    }
    
    console.log(); // Empty line for readability
  }

  async generateReport(results: ValidationResult): Promise<void> {
    const reportPath = path.join(process.cwd(), 'COMPLIANCE_VALIDATION_REPORT.md');
    
    const report = `# Legal AI System - Compliance Validation Report

**Generated:** ${results.timestamp}  
**Overall Status:** ${results.overallStatus.toUpperCase()}  
**Compliance Score:** ${results.complianceScore}/100

## Summary

- **Total Checks:** ${results.totalChecks}
- **Passed:** ${results.passedChecks}
- **Failed:** ${results.failedChecks}
- **Warnings:** ${results.warningChecks}

## Detailed Results

${results.checks.map(check => `
### ${check.name}
**Status:** ${check.status.toUpperCase()}  
**Description:** ${check.description}

**Details:**
${check.details.map(detail => `- ${detail}`).join('\n')}

${check.recommendations ? `**Recommendations:**
${check.recommendations.map(rec => `- ${rec}`).join('\n')}` : ''}
`).join('\n')}

## Compliance Assessment

${results.overallStatus === 'pass' 
  ? '✅ **SYSTEM COMPLIANT** - All critical compliance checks passed.' 
  : results.overallStatus === 'warning'
  ? '⚠️  **SYSTEM MOSTLY COMPLIANT** - Minor issues detected that should be addressed.'
  : '❌ **SYSTEM NON-COMPLIANT** - Critical issues detected that must be resolved before production.'}

---
*Report generated by Legal AI System Compliance Validator*
`;

    await fs.writeFile(reportPath, report, 'utf-8');
    console.log(chalk.blue(`📄 Detailed report saved to: ${reportPath}`));
  }
}

// Main execution
async function main() {
  const validator = new ComplianceValidator();
  
  try {
    const results = await validator.runFullValidation();
    
    // Print summary
    console.log(chalk.blue('\n📊 COMPLIANCE VALIDATION SUMMARY'));
    console.log(chalk.blue('====================================='));
    
    const statusColor = results.overallStatus === 'pass' ? chalk.green : 
                       results.overallStatus === 'warning' ? chalk.yellow : chalk.red;
    
    console.log(`Overall Status: ${statusColor(results.overallStatus.toUpperCase())}`);
    console.log(`Compliance Score: ${statusColor(`${results.complianceScore}/100`)}`);
    console.log(`Total Checks: ${results.totalChecks}`);
    console.log(`Passed: ${chalk.green(results.passedChecks)}`);
    console.log(`Warnings: ${chalk.yellow(results.warningChecks)}`);
    console.log(`Failed: ${chalk.red(results.failedChecks)}`);
    
    // Generate detailed report
    await validator.generateReport(results);
    
    // Exit with appropriate code
    process.exit(results.overallStatus === 'fail' ? 1 : 0);
    
  } catch (error) {
    console.error(chalk.red('❌ Validation failed with error:'), error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

export default ComplianceValidator;