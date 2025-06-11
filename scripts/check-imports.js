#!/usr/bin/env node
// check-imports.js

const fs = require('fs');
const path = require('path');
const babelParser = require('@babel/parser');
const traverse = require('@babel/traverse').default;

const ROOT_DIR = path.resolve(__dirname, 'frontend/src'); // change if needed
const EXTENSIONS = ['.js', '.jsx'];

function findFiles(dir) {
  let results = [];
  const list = fs.readdirSync(dir);
  list.forEach((file) => {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);
    if (stat && stat.isDirectory()) {
      results = results.concat(findFiles(fullPath));
    } else if (EXTENSIONS.includes(path.extname(file))) {
      results.push(fullPath);
    }
  });
  return results;
}

function parseFile(filePath) {
  const code = fs.readFileSync(filePath, 'utf8');
  return babelParser.parse(code, {
    sourceType: 'module',
    plugins: ['jsx', 'importMeta'],
  });
}

function resolveImportPath(importPath, baseDir) {
  if (importPath.startsWith('@')) {
    // assume alias maps to src/
    importPath = importPath.replace(/^@/, path.join(ROOT_DIR));
  } else if (importPath.startsWith('/')) {
    importPath = path.join(ROOT_DIR, importPath);
  } else if (!importPath.startsWith('.')) {
    return null; // skip package imports
  } else {
    importPath = path.resolve(baseDir, importPath);
  }

  for (let ext of [...EXTENSIONS, '/index.js', '/index.jsx']) {
    const fullPath = importPath + ext;
    if (fs.existsSync(fullPath)) return fullPath;
  }

  return null;
}

function getExports(filePath) {
  try {
    const ast = parseFile(filePath);
    const exports = { default: false, named: [] };

    traverse(ast, {
      ExportNamedDeclaration(path) {
        const decl = path.node.declaration;
        if (decl && decl.declarations) {
          decl.declarations.forEach((d) => {
            if (d.id?.name) exports.named.push(d.id.name);
          });
        } else if (path.node.specifiers) {
          path.node.specifiers.forEach((s) => {
            if (s.exported?.name) exports.named.push(s.exported.name);
          });
        }
      },
      ExportDefaultDeclaration() {
        exports.default = true;
      },
    });

    return exports;
  } catch (e) {
    return { error: e.message };
  }
}

function checkImports() {
  const files = findFiles(ROOT_DIR);
  let problems = [];

  for (let file of files) {
    const dir = path.dirname(file);
    const ast = parseFile(file);

    traverse(ast, {
      ImportDeclaration({ node }) {
        const source = node.source.value;
        const resolvedPath = resolveImportPath(source, dir);

        if (!resolvedPath) return; // skip node_modules or unresolved

        if (!fs.existsSync(resolvedPath)) {
          problems.push(`[❌ NOT FOUND] ${source} in ${file}`);
          return;
        }

        const exports = getExports(resolvedPath);
        if (exports.error) {
          problems.push(`[❌ PARSE ERROR] ${resolvedPath}: ${exports.error}`);
          return;
        }

        node.specifiers.forEach((spec) => {
          if (spec.type === 'ImportDefaultSpecifier' && !exports.default) {
            problems.push(`[❌ MISSING DEFAULT] '${source}' in ${file}`);
          }
          if (spec.type === 'ImportSpecifier') {
            const name = spec.imported.name;
            if (!exports.named.includes(name)) {
              problems.push(`[❌ MISSING NAMED] '${name}' from '${source}' in ${file}`);
            }
          }
        });
      },
    });
  }

  if (problems.length) {
    console.log(`\n🚨 Found ${problems.length} import issue(s):\n`);
    problems.forEach((p) => console.log(p));
  } else {
    console.log('✅ All imports look clean.');
  }
}

checkImports();
