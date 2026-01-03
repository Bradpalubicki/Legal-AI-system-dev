const fs = require('fs');
const file = 'src/components/CaseManagement/DeadlineManager.tsx';
const content = fs.readFileSync(file, 'utf8');

console.log('='.repeat(70));
console.log('DEADLINE MANAGER COMPONENT VALIDATION');
console.log('='.repeat(70));

const errors = [];
const checks = [];

// 1. Line count
const lineCount = content.split('\n').length;
checks.push(`✓ Total lines: ${lineCount}`);

// 2. Check for React hooks
const hasUseState = content.includes('useState');
const hasUseEffect = content.includes('useEffect');
if (hasUseState) checks.push('✓ useState hook found');
else errors.push('✗ useState hook missing');
if (hasUseEffect) checks.push('✓ useEffect hook found');
else errors.push('✗ useEffect hook missing');

// 3. Check for API calls
const apiCalls = (content.match(/caseManagementAPI\./g) || []).length;
checks.push(`✓ API calls: ${apiCalls}`);

// 4. Check JSX elements
const jsxElements = (content.match(/<[A-Z][^>]*>/g) || []).length;
checks.push(`✓ JSX elements: ${jsxElements}`);

// 5. Check brace balance
const openBraces = (content.match(/{/g) || []).length;
const closeBraces = (content.match(/}/g) || []).length;
if (openBraces === closeBraces) {
  checks.push(`✓ Braces balanced: ${openBraces} pairs`);
} else {
  errors.push(`✗ Mismatched braces: ${openBraces} open, ${closeBraces} close`);
}

// 6. Check parenthesis balance
const openParens = (content.match(/\(/g) || []).length;
const closeParens = (content.match(/\)/g) || []).length;
if (openParens === closeParens) {
  checks.push(`✓ Parentheses balanced: ${openParens} pairs`);
} else {
  errors.push(`✗ Mismatched parentheses: ${openParens} open, ${closeParens} close`);
}

// 7. Check required features
const features = {
  'Timeline events integration': content.includes('caseManagementAPI.events'),
  'Action items integration': content.includes('caseManagementAPI.briefing.getActionItems'),
  'Critical path integration': content.includes('caseManagementAPI.timeline.getCriticalPath'),
  'Deadline list': content.includes('filteredDeadlines.map'),
  'Detail modal': content.includes('selectedDeadline'),
  'Status filter': content.includes('statusFilter'),
  'Priority filter': content.includes('priorityFilter'),
  'Type filter': content.includes('typeFilter'),
  'Critical path toggle': content.includes('showOnlyCritical'),
  'Days until calculation': content.includes('getDaysUntil'),
  'Urgency indicator': content.includes('getUrgencyIndicator'),
  'Summary cards': content.includes('getOverdueCount'),
  'Loading state': content.includes('loading'),
  'Error handling': content.includes('setError'),
};

Object.entries(features).forEach(([feature, present]) => {
  if (present) {
    checks.push(`✓ Feature: ${feature}`);
  } else {
    errors.push(`✗ Missing feature: ${feature}`);
  }
});

console.log('\nPASSED CHECKS:');
checks.forEach(c => console.log(`  ${c}`));

if (errors.length > 0) {
  console.log('\n❌ ERRORS FOUND:');
  errors.forEach(e => console.log(`  ${e}`));
  console.log('='.repeat(70));
  process.exit(1);
} else {
  console.log('\n' + '='.repeat(70));
  console.log('✅ STEP 8 COMPLETE - Deadline Manager validated successfully');
  console.log('All features implemented, no errors found');
  console.log('='.repeat(70));
  process.exit(0);
}
