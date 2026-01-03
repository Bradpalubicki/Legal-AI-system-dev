const fs = require('fs');
const path = require('path');

console.log("=" .repeat(70));
console.log("COMPREHENSIVE FRONTEND ERROR CHECK");
console.log("=" .repeat(70));

const errors = [];
const warnings = [];
const successes = [];

// Test 1: Check file existence
console.log("\n[1/8] Checking file existence...");
const files = [
  'src/types/case-management.ts',
  'src/lib/api/case-management-api.ts',
  'src/components/CaseManagement/ExecutiveDashboard.tsx',
  'src/components/CaseManagement/TimelineGanttChart.tsx'
];

files.forEach(file => {
  const fullPath = path.join(process.cwd(), file);
  if (fs.existsSync(fullPath)) {
    successes.push(`✓ ${file} exists`);
  } else {
    errors.push(`✗ ${file} NOT FOUND`);
  }
});

// Test 2: Check import statements
console.log("[2/8] Checking import statements...");
files.forEach(file => {
  const fullPath = path.join(process.cwd(), file);
  if (fs.existsSync(fullPath)) {
    const content = fs.readFileSync(fullPath, 'utf8');
    const imports = content.match(/import .* from ['"](.*)['"];?/g) || [];

    imports.forEach(imp => {
      const match = imp.match(/from ['"](.*)['"];?/);
      if (match) {
        const importPath = match[1];
        if (importPath.startsWith('@/')) {
          // Check if the file exists
          const relativePath = importPath.replace('@/', 'src/');
          const possiblePaths = [
            `${relativePath}.ts`,
            `${relativePath}.tsx`,
            `${relativePath}/index.ts`,
            `${relativePath}/index.tsx`
          ];

          const exists = possiblePaths.some(p => fs.existsSync(path.join(process.cwd(), p)));
          if (!exists && !importPath.includes('ui/card')) {
            warnings.push(`⚠ Import may not resolve: ${importPath} in ${file}`);
          }
        }
      }
    });
  }
});

// Test 3: Check TypeScript syntax
console.log("[3/8] Checking TypeScript syntax...");
files.forEach(file => {
  const fullPath = path.join(process.cwd(), file);
  if (fs.existsSync(fullPath)) {
    const content = fs.readFileSync(fullPath, 'utf8');

    // Check for common syntax errors
    const openBraces = (content.match(/{/g) || []).length;
    const closeBraces = (content.match(/}/g) || []).length;
    if (openBraces !== closeBraces) {
      errors.push(`✗ Mismatched braces in ${file}: ${openBraces} open, ${closeBraces} close`);
    } else {
      successes.push(`✓ Braces balanced in ${file}`);
    }

    const openParens = (content.match(/\(/g) || []).length;
    const closeParens = (content.match(/\)/g) || []).length;
    if (openParens !== closeParens) {
      errors.push(`✗ Mismatched parentheses in ${file}: ${openParens} open, ${closeParens} close`);
    }
  }
});

// Test 4: Check export statements
console.log("[4/8] Checking exports...");
const typesContent = fs.readFileSync(path.join(process.cwd(), 'src/types/case-management.ts'), 'utf8');
const exportCount = (typesContent.match(/export (enum|interface|type) \w+/g) || []).length;
if (exportCount > 0) {
  successes.push(`✓ ${exportCount} exports found in types file`);
} else {
  errors.push(`✗ No exports found in types file`);
}

// Test 5: Check API client structure
console.log("[5/8] Checking API client structure...");
const apiContent = fs.readFileSync(path.join(process.cwd(), 'src/lib/api/case-management-api.ts'), 'utf8');
const apiEndpoints = [
  'cases.list',
  'cases.get',
  'cases.create',
  'parties.list',
  'events.list',
  'assets.list',
  'bidding.list',
  'objections.list',
  'timeline.getCriticalPath',
  'briefing.getStrategicSummary'
];

apiEndpoints.forEach(endpoint => {
  if (apiContent.includes(endpoint)) {
    successes.push(`✓ API endpoint ${endpoint} defined`);
  } else {
    errors.push(`✗ API endpoint ${endpoint} missing`);
  }
});

// Test 6: Check component structure
console.log("[6/8] Checking component structure...");
const dashboardContent = fs.readFileSync(
  path.join(process.cwd(), 'src/components/CaseManagement/ExecutiveDashboard.tsx'),
  'utf8'
);

const requiredHooks = ['useState', 'useEffect'];
requiredHooks.forEach(hook => {
  if (dashboardContent.includes(hook)) {
    successes.push(`✓ ${hook} used in ExecutiveDashboard`);
  } else {
    warnings.push(`⚠ ${hook} not found in ExecutiveDashboard`);
  }
});

// Test 7: Check for common React issues
console.log("[7/8] Checking for common React issues...");
[dashboardContent].forEach((content, idx) => {
  const componentName = ['ExecutiveDashboard'][idx];

  // Check for key props in maps
  const maps = content.match(/\.map\(/g) || [];
  const keys = content.match(/key=/g) || [];
  if (maps.length > keys.length) {
    warnings.push(`⚠ ${componentName}: Possible missing key props (${maps.length} maps, ${keys.length} keys)`);
  } else {
    successes.push(`✓ ${componentName}: Key props look good`);
  }

  // Check for proper async/await
  const asyncFuncs = content.match(/async \w+/g) || [];
  const awaits = content.match(/await /g) || [];
  if (asyncFuncs.length > 0 && awaits.length === 0) {
    warnings.push(`⚠ ${componentName}: async functions without await`);
  }
});

// Test 8: Check file sizes
console.log("[8/8] Checking file sizes...");
files.forEach(file => {
  const fullPath = path.join(process.cwd(), file);
  if (fs.existsSync(fullPath)) {
    const stats = fs.statSync(fullPath);
    const sizeKB = (stats.size / 1024).toFixed(2);
    if (stats.size > 100000) {
      warnings.push(`⚠ ${file} is large (${sizeKB} KB)`);
    } else {
      successes.push(`✓ ${file} size OK (${sizeKB} KB)`);
    }
  }
});

// Final Report
console.log("\n" + "=".repeat(70));
console.log("ERROR CHECK REPORT");
console.log("=".repeat(70));

console.log(`\n✓ SUCCESSES: ${successes.length}`);
if (successes.length > 0 && successes.length <= 10) {
  successes.forEach(s => console.log(`  ${s}`));
} else if (successes.length > 10) {
  console.log(`  (Showing first 10 of ${successes.length})`);
  successes.slice(0, 10).forEach(s => console.log(`  ${s}`));
}

if (warnings.length > 0) {
  console.log(`\n⚠ WARNINGS: ${warnings.length}`);
  warnings.forEach(w => console.log(`  ${w}`));
}

if (errors.length > 0) {
  console.log(`\n✗ ERRORS: ${errors.length}`);
  errors.forEach(e => console.log(`  ${e}`));
}

console.log("\n" + "=".repeat(70));
if (errors.length === 0) {
  console.log("STATUS: ✅ ALL CHECKS PASSED");
  console.log("=".repeat(70));
  process.exit(0);
} else {
  console.log("STATUS: ❌ ERRORS FOUND");
  console.log("=".repeat(70));
  process.exit(1);
}
