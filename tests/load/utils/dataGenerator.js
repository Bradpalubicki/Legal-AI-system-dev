/**
 * Test Data Generation Utilities
 */

import { randomIntBetween, randomItem, randomString } from 'k6';

/**
 * Generate random email address
 */
export function generateEmail() {
  return `loadtest-${randomString(8)}@example.com`;
}

/**
 * Generate random password
 */
export function generatePassword() {
  return `Pass${randomString(12)}!123`;
}

/**
 * Generate random case data
 */
export function generateCase() {
  const caseTypes = ['civil', 'criminal', 'family', 'corporate'];
  const statuses = ['open', 'in_progress', 'pending_review', 'closed'];

  return {
    title: `Load Test Case ${randomString(6)}`,
    description: `This is a test case created during load testing. ID: ${randomString(10)}`,
    caseNumber: `LOAD-${Date.now()}-${randomIntBetween(1000, 9999)}`,
    caseType: randomItem(caseTypes),
    status: randomItem(statuses),
    priority: randomIntBetween(1, 5),
    metadata: {
      testRun: true,
      createdBy: 'load-test',
      timestamp: new Date().toISOString(),
    },
  };
}

/**
 * Generate random document metadata
 */
export function generateDocument() {
  const documentTypes = ['contract', 'brief', 'motion', 'evidence', 'correspondence'];

  return {
    title: `Load Test Document ${randomString(8)}`,
    description: `Test document for load testing. ID: ${randomString(10)}`,
    documentType: randomItem(documentTypes),
    tags: [
      `loadtest`,
      `tag-${randomString(4)}`,
      `category-${randomIntBetween(1, 10)}`,
    ],
    metadata: {
      testDocument: true,
      size: randomIntBetween(1024, 1048576), // 1KB to 1MB
      createdAt: new Date().toISOString(),
    },
  };
}

/**
 * Generate random search query
 */
export function generateSearchQuery() {
  const queries = [
    'contract agreement',
    'motion to dismiss',
    'evidence submitted',
    'plaintiff defendant',
    'legal precedent',
    'case law',
    'statute violation',
    'appeal decision',
    'settlement negotiation',
    'discovery request',
  ];

  return randomItem(queries);
}

/**
 * Generate sample document content
 */
export function generateDocumentContent() {
  const templates = [
    `LEGAL DOCUMENT - TEST DATA

This is a sample legal document created for load testing purposes.

Case Number: LOAD-TEST-${randomIntBetween(10000, 99999)}
Date: ${new Date().toISOString()}

PARTIES:
Plaintiff: Load Test Party A
Defendant: Load Test Party B

SUMMARY:
${randomString(200)}

DETAILS:
${randomString(500)}

This document is created for testing purposes only and contains no real legal information.

END OF DOCUMENT`,

    `CONTRACT AGREEMENT - TEST DATA

This Agreement ("Agreement") is entered into as of ${new Date().toISOString()}.

PARTIES:
Party A (Test Entity ${randomString(6)})
Party B (Test Entity ${randomString(6)})

TERMS AND CONDITIONS:
1. ${randomString(100)}
2. ${randomString(100)}
3. ${randomString(100)}

SIGNATURES:
[Test Signature]

Test Document ID: ${randomString(10)}`,

    `LEGAL BRIEF - TEST DATA

IN THE MATTER OF: Load Test Case ${randomString(8)}

Case No: LOAD-${randomIntBetween(1000, 9999)}

INTRODUCTION:
${randomString(150)}

ARGUMENT:
${randomString(300)}

CONCLUSION:
${randomString(100)}

Test Brief ID: ${randomString(10)}`,
  ];

  return randomItem(templates);
}

/**
 * Generate random file data for upload
 */
export function generateFileData(sizeKB = 10) {
  const content = generateDocumentContent();
  // Pad to reach desired size
  const padding = randomString(sizeKB * 1024 - content.length);
  return content + padding;
}

/**
 * Generate random user data
 */
export function generateUser() {
  return {
    email: generateEmail(),
    password: generatePassword(),
    fullName: `Load Test User ${randomString(8)}`,
    role: randomItem(['user', 'attorney', 'admin']),
    organization: `Test Org ${randomString(6)}`,
  };
}

export default {
  generateEmail,
  generatePassword,
  generateCase,
  generateDocument,
  generateSearchQuery,
  generateDocumentContent,
  generateFileData,
  generateUser,
};
