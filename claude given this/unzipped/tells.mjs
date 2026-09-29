// Fails the build if src contains patterns that make a UI look generated.
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, extname } from 'node:path';

const RULES = [
  [/backdrop-blur|backdrop-filter/, 'glass blur'],
  [/\bshadow-|drop-shadow|box-shadow/, 'drop shadow'],
  [/gradient/i, 'gradient'],
  [/rounded-(lg|xl|2xl|3xl)/, 'soft corner radius'],
  [/lucide/i, 'lucide icons'],
  [/\u2014/, 'em dash'],
  [/#(fff|ffffff|000|000000)\b/i, 'pure white or black'],
  [/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u, 'emoji or checkmark glyph'],
  [/animate-(pulse|bounce|ping)/, 'pulse or bounce animation'],
  [/purple|violet|fuchsia/i, 'purple'],
];

const files = [];
const walk = (d) => {
  for (const f of readdirSync(d)) {
    const p = join(d, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (['.ts', '.tsx', '.css', '.html'].includes(extname(p))) files.push(p);
  }
};
walk('src');
files.push('index.html');

let bad = 0;
for (const file of files) {
  readFileSync(file, 'utf8').split('\n').forEach((line, i) => {
    for (const [re, name] of RULES) {
      if (re.test(line)) { console.error(`${file}:${i + 1}  ${name}`); bad++; }
    }
  });
}
if (bad) { console.error(`\n${bad} tell(s) found.`); process.exit(1); }
console.log('tells: clean');
