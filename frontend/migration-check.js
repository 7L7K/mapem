const fs = require('fs');
const path = require('path');

console.log("👑 King's CRA → Vite Migration Checker 👑");
console.log("=========================================\n");

const pkgPath = path.join(process.cwd(), 'package.json');
const srcDir = path.join(process.cwd(), 'src');
const publicDir = path.join(process.cwd(), 'public');

// Check package.json dependencies
const pkg = JSON.parse(fs.readFileSync(pkgPath));
const dependencies = pkg.dependencies || {};
const devDependencies = pkg.devDependencies || {};

console.log('🔍 Checking Dependencies...\n');

const importantDeps = ['react-router', 'react-router-dom', 'redux', 'react-redux', 'axios', 'leaflet', 'react-leaflet'];
importantDeps.forEach(dep => {
  if (dependencies[dep] || devDependencies[dep]) {
    console.log(`✅ Detected ${dep}: ${(dependencies[dep] || devDependencies[dep])}`);
  }
});

// Check for environment variables (.env)
console.log('\n🔍 Checking Environment Variables...');
const envExists = fs.existsSync(path.join(process.cwd(), '.env'));
console.log(envExists ? '✅ .env file found.' : '❌ No .env file detected.');

// Check public directory (index.html, favicon)
console.log('\n🔍 Checking Public Directory...');
const indexHtmlExists = fs.existsSync(path.join(publicDir, 'index.html'));
console.log(indexHtmlExists ? '✅ public/index.html found.' : '❌ public/index.html NOT found.');

const faviconExists = fs.existsSync(path.join(publicDir, 'favicon.ico'));
console.log(faviconExists ? '✅ public/favicon.ico found.' : '⚠️ public/favicon.ico NOT found.');

// Check global CSS files
console.log('\n🔍 Checking Global CSS Files...');
const globalCss = ['index.css', 'App.css', 'styles.css'];
globalCss.forEach(file => {
  const exists = fs.existsSync(path.join(srcDir, file));
  console.log(exists ? `✅ ${file} found.` : `⚠️ ${file} NOT found.`);
});

// Check JSX or TSX components
console.log('\n🔍 Checking React Components...');
const srcFiles = fs.readdirSync(srcDir).filter(f => f.endsWith('.jsx') || f.endsWith('.tsx') || f.endsWith('.js'));
console.log(`✅ Found ${srcFiles.length} component files (.jsx/.tsx/.js):`);
srcFiles.forEach(f => console.log(`   - ${f}`));

// Check CRA-specific features (serviceWorker, reportWebVitals)
console.log('\n🔍 Checking CRA-specific Features...');
const craFiles = ['serviceWorker.js', 'reportWebVitals.js', 'setupTests.js'];
craFiles.forEach(file => {
  const exists = fs.existsSync(path.join(srcDir, file));
  console.log(exists ? `✅ CRA-specific file found: ${file}` : `⚠️ ${file} not detected.`);
});

// Final output instructions
console.log('\n🚩 Migration Instructions:');
console.log('1. ✅ Move all component files listed above to your Vite src folder.');
if (envExists) console.log('2. ✅ Copy your .env file into your new Vite project (Vite auto-loads .env files).');
if (indexHtmlExists) console.log('3. ⚠️ Manually merge your public/index.html with Vite’s index.html.');
if (faviconExists) console.log('4. ✅ Move public/favicon.ico to your Vite public directory.');
console.log('5. ⚠️ Install any dependencies listed above using npm/yarn/pnpm in your new Vite project.');
console.log('   Example: npm install react-router-dom axios leaflet react-leaflet');
console.log('6. ⚠️ Review any CRA-specific files (serviceWorker.js, reportWebVitals.js) to determine if needed (often these can be skipped).');

console.log('\n🎯 Run these steps to smoothly migrate your CRA project to Vite!');
