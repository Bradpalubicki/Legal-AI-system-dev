/**
 * Script to fix hard-coded localhost URLs in frontend code
 * Replaces http://localhost:8000 with API_CONFIG.BASE_URL
 */

const fs = require('fs');
const path = require('path');

const filesToFix = [
  'frontend/src/components/CaseTracking/EnhancedCaseTracker.tsx',
  'frontend/src/app/pacer/page.tsx',
  'frontend/src/components/HelpAgent.tsx',
  'frontend/src/components/PACER/CreditsDashboard.tsx',
  'frontend/src/components/QASection.tsx',
  'frontend/src/app/ai-assistant/page.tsx',
  'frontend/src/components/PACERRateLimitMonitor.tsx',
  'frontend/src/components/Documents/DocumentsTab.tsx',
  'frontend/src/components/Documents/EnhancedDocumentsTab.tsx',
  'frontend/src/components/Documents/MultiDocumentUpload.tsx',
  'frontend/src/components/BankruptcyMultiFileUpload.tsx',
  'frontend/src/app/bankruptcy/upload/page.tsx',
  'frontend/src/components/DefenseFlowEnforcer.tsx',
  'frontend/src/components/UnifiedDefenseBuilder.tsx',
  'frontend/src/components/Cases/EditTransactionModal.tsx',
  'frontend/src/components/Cases/EditTimelineEventModal.tsx',
  'frontend/src/app/cases/[id]/page.tsx',
  'frontend/src/app/dashboard/page.tsx',
  'frontend/src/components/Cases/EditPartyModal.tsx',
  'frontend/src/components/Cases/AddTransactionModal.tsx',
  'frontend/src/lib/api/cases.ts',
  'frontend/src/lib/api/case-management-api.ts',
  'frontend/src/components/Defense/ConversationalDefenseBuilder.tsx',
  'frontend/src/contexts/DocumentContext.tsx',
  'frontend/src/app/api/unified/route.ts',
  'frontend/src/app/api/interview/route.ts',
  'frontend/src/app/api/defense/build/route.ts',
  'frontend/src/components/DefenseBuilder.tsx',
  'frontend/src/hooks/useUnifiedSystem.ts',
  'frontend/src/utils/api.ts',
  'frontend/src/utils/compliance-utils.ts',
];

let totalFixed = 0;
let filesModified = 0;

console.log('🔧 Fixing hard-coded URLs...\n');

filesToFix.forEach(filePath => {
  const fullPath = path.join(__dirname, filePath);

  if (!fs.existsSync(fullPath)) {
    console.log(`⚠️  Skipping ${filePath} (not found)`);
    return;
  }

  let content = fs.readFileSync(fullPath, 'utf8');
  const originalContent = content;

  // Count occurrences
  const matches = content.match(/http:\/\/localhost:8000/g);
  const count = matches ? matches.length : 0;

  if (count === 0) {
    return; // Skip files with no matches
  }

  // Check if file already imports API_CONFIG
  const hasApiConfigImport = content.includes("from '../config/api'") ||
                             content.includes('from "@/config/api"') ||
                             content.includes("from '../../config/api'") ||
                             content.includes("from '../../../config/api'");

  // Add import if needed
  if (!hasApiConfigImport) {
    // Determine correct import path based on file location
    const depth = filePath.split('/').length - 3; // Subtract frontend/src/
    const importPath = '../'.repeat(depth) + 'config/api';

    // Find where to add import (after existing imports)
    const importRegex = /^(import\s+.*?;\s*\n)+/m;
    const importMatch = content.match(importRegex);

    if (importMatch) {
      const lastImport = importMatch[0];
      content = content.replace(
        lastImport,
        lastImport + `import { API_CONFIG } from '${importPath}';\n`
      );
    } else {
      // No imports found, add at top
      content = `import { API_CONFIG } from '${importPath}';\n\n` + content;
    }
  }

  // Replace all occurrences of http://localhost:8000
  content = content.replace(/['"]http:\/\/localhost:8000['"]/g, 'API_CONFIG.BASE_URL');

  // Also replace template literals
  content = content.replace(/`http:\/\/localhost:8000/g, '`${API_CONFIG.BASE_URL}');

  // Write back
  if (content !== originalContent) {
    fs.writeFileSync(fullPath, content, 'utf8');
    console.log(`✅ Fixed ${count} occurrence(s) in ${filePath}`);
    totalFixed += count;
    filesModified++;
  }
});

console.log(`\n✨ Done! Fixed ${totalFixed} hard-coded URLs in ${filesModified} files.`);
console.log('\n⚠️  Manual review recommended for:');
console.log('  - API routes (may need process.env.API_URL for server-side)');
console.log('  - Test files');
console.log('\n💡 Next steps:');
console.log('  1. Review changes: git diff');
console.log('  2. Test the application');
console.log('  3. Commit changes');
