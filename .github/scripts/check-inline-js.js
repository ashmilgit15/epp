// CI helper: syntax-check inline <script> blocks in epp-ide/index.html
const fs = require('fs');
const path = require('path');

const htmlPath = path.join(__dirname, '..', '..', 'epp-ide', 'index.html');
const html = fs.readFileSync(htmlPath, 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);

if (scripts.length === 0) {
    console.error('No inline scripts found in index.html!');
    process.exit(1);
}

let failed = false;
scripts.forEach((code, i) => {
    try {
        new Function(code);
        console.log(`inline script ${i}: OK`);
    } catch (e) {
        console.error(`inline script ${i}: SYNTAX ERROR — ${e.message}`);
        failed = true;
    }
});

process.exit(failed ? 1 : 0);
