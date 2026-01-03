const fs = require('fs');
const path = require('path');

const apiFile = path.join(process.cwd(), 'src/lib/api/case-management-api.ts');
const content = fs.readFileSync(apiFile, 'utf8');

console.log("Verifying API Client Structure:");
console.log("=".repeat(50));

// Check for main API object
const hasMainObject = content.includes('export const caseManagementAPI');
console.log(hasMainObject ? '✓ Main API object exported' : '✗ Main API object missing');

// Check for nested namespaces
const namespaces = ['cases', 'parties', 'events', 'transactions', 'assets', 'bidding', 'objections', 'timeline', 'briefing'];
let allPresent = true;

namespaces.forEach(ns => {
  const pattern = new RegExp(`${ns}:\s*{`, 'g');
  if (pattern.test(content)) {
    console.log(`✓ Namespace '${ns}' defined`);
  } else {
    console.log(`✗ Namespace '${ns}' missing`);
    allPresent = false;
  }
});

// Check for async functions
const asyncFunctions = (content.match(/async \(/g) || []).length;
console.log(`\n✓ ${asyncFunctions} async functions defined`);

// Check for fetchAPI calls
const fetchCalls = (content.match(/fetchAPI</g) || []).length;
console.log(`✓ ${fetchCalls} API fetch calls`);

console.log("\n" + "=".repeat(50));
console.log(allPresent && asyncFunctions > 20 && fetchCalls > 20 ? '✅ API CLIENT OK' : '❌ API CLIENT HAS ISSUES');
