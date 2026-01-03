const fs = require('fs');

console.log('='.repeat(70));
console.log('MULTI-DOCUMENT UPLOAD ERROR CHECK');
console.log('='.repeat(70));

const files = [
  'src/components/Documents/MultiDocumentUpload.tsx',
  'src/app/documents/page.tsx',
  'src/components/Documents/EnhancedDocumentsTab.tsx',
  'src/app/documents/multi-upload/page.tsx'
];

const errors = [];
const warnings = [];
const checks = [];

files.forEach(file => {
  console.log(`\n[Checking] ${file}`);

  if (!fs.existsSync(file)) {
    errors.push(`X File not found: ${file}`);
    return;
  }

  const content = fs.readFileSync(file, 'utf8');
  const lines = content.split('\n').length;
  checks.push(`OK ${file} exists (${lines} lines)`);

  // Check for syntax issues
  const openBraces = (content.match(/{/g) || []).length;
  const closeBraces = (content.match(/}/g) || []).length;
  if (openBraces !== closeBraces) {
    errors.push(`X ${file}: Mismatched braces (${openBraces} open, ${closeBraces} close)`);
  } else {
    checks.push(`OK ${file}: Braces balanced (${openBraces} pairs)`);
  }

  const openParens = (content.match(/\(/g) || []).length;
  const closeParens = (content.match(/\)/g) || []).length;
  if (openParens !== closeParens) {
    errors.push(`X ${file}: Mismatched parentheses (${openParens} open, ${closeParens} close)`);
  } else {
    checks.push(`OK ${file}: Parentheses balanced (${openParens} pairs)`);
  }

  // Check for 'use client' directive in client components
  if (!content.includes("'use client'") && !content.includes('"use client"')) {
    errors.push(`X ${file}: Missing 'use client' directive`);
  } else {
    checks.push(`OK ${file}: Has 'use client' directive`);
  }

  // Check for proper exports
  if (!content.includes('export default') && !content.includes('export {') && !content.includes('export function')) {
    errors.push(`X ${file}: No export found`);
  } else {
    checks.push(`OK ${file}: Has exports`);
  }

  // Check for required imports based on file
  if (file.includes('MultiDocumentUpload.tsx')) {
    const requiredImports = ['useState', 'useCallback', 'Card', 'Upload', 'toast'];
    requiredImports.forEach(imp => {
      if (!content.includes(imp)) {
        errors.push(`X ${file}: Missing required import '${imp}'`);
      }
    });
  }

  if (file.includes('documents/page.tsx')) {
    const requiredImports = ['MultiDocumentUpload', 'useDocuments', 'Card', 'Button'];
    requiredImports.forEach(imp => {
      if (!content.includes(imp)) {
        errors.push(`X ${file}: Missing required import '${imp}'`);
      }
    });
  }

  // Check for common React issues
  const maps = (content.match(/\.map\(/g) || []).length;
  const keys = (content.match(/key=/g) || []).length;
  if (maps > 0 && keys < maps) {
    warnings.push(`WARN ${file}: Possible missing key props (${maps} maps, ${keys} keys)`);
  } else if (maps > 0) {
    checks.push(`OK ${file}: Key props look good (${maps} maps, ${keys} keys)`);
  }

  // Check for useState
  if (content.includes('useState')) {
    checks.push(`OK ${file}: Uses useState hook`);
  }

  // Check for useEffect
  if (content.includes('useEffect')) {
    checks.push(`OK ${file}: Uses useEffect hook`);
  }
});

console.log('\n' + '='.repeat(70));
console.log('RESULTS');
console.log('='.repeat(70));

if (checks.length > 0) {
  console.log(`\nPASSED CHECKS (${checks.length}):`);
  checks.forEach(c => console.log(`  ${c}`));
}

if (warnings.length > 0) {
  console.log(`\nWARNINGS (${warnings.length}):`);
  warnings.forEach(w => console.log(`  ${w}`));
}

if (errors.length > 0) {
  console.log(`\nERRORS (${errors.length}):`);
  errors.forEach(e => console.log(`  ${e}`));
  console.log('\n' + '='.repeat(70));
  console.log('STATUS: ERRORS FOUND');
  console.log('='.repeat(70));
  process.exit(1);
} else {
  console.log('\n' + '='.repeat(70));
  console.log('STATUS: ALL CHECKS PASSED - NO ERRORS');
  console.log('='.repeat(70));
  process.exit(0);
}
