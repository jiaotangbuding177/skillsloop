// Process-local adapter: keep the upstream screenshot script byte-for-byte.
// The pinned image provides system Chromium rather than a Playwright download.
const path = require('path');
const bases = [...(process.env.NODE_PATH || '').split(path.delimiter), '/opt/node-tools/lib/node_modules'].filter(Boolean);
let playwright;
for (const base of bases) {
  for (const name of ['playwright', 'playwright-core']) {
    try { playwright = require(path.join(base, name)); break; } catch (_) {}
  }
  if (playwright) break;
}
if (!playwright) throw new Error('Pinned Darwin runtime lacks Playwright');
const originalLaunch = playwright.chromium.launch.bind(playwright.chromium);
playwright.chromium.launch = (options = {}) => originalLaunch({
  ...options,
  executablePath: options.executablePath || '/usr/bin/chromium',
});
