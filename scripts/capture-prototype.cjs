// npm ci && npm run check:prototype; uses Edge on Windows, Chromium on Linux.
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright-core');
const { mkdirSync, readFileSync } = require('node:fs');
const assert = require('node:assert/strict');
const http = require('node:http');
const path = require('node:path');

const root = path.resolve(__dirname, '../frontend/prototype');
const server = http.createServer((request, response) => {
  const name = new URL(request.url, 'http://localhost').pathname;
  const file = path.resolve(root, `.${name === '/' ? '/index.html' : name}`);
  if (!file.startsWith(root + path.sep)) { response.writeHead(403).end(); return; }
  try {
    const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript' };
    response.setHeader('Content-Type', types[path.extname(file)] || 'application/octet-stream');
    response.end(readFileSync(file));
  } catch { response.writeHead(404).end(); }
});

(async () => {
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const channel = process.env.PLAYWRIGHT_CHANNEL || (process.platform === 'win32' ? 'msedge' : undefined);
  let browser;
  try {
    browser = await chromium.launch({ channel, headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1100 } });
    const errors = [];
    page.on('pageerror', (error) => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/`, { waitUntil: 'networkidle' });
    const dir = path.join(root, 'screenshots');
    mkdirSync(dir, { recursive: true });
    await page.screenshot({ path: `${dir}/upload.png`, fullPage: true });
    const originalText = await page.locator('#lecture').inputValue();
    await page.locator('#lecture').fill('Changed material');
    await page.locator('#upload-form button').click();
    assert.equal(await page.locator('#upload').isVisible(), true);
    assert.match(await page.locator('#feedback').innerText(), /Прототип/);
    await page.locator('#lecture').fill(originalText);
    const originalQuestions = await page.locator('#questions').inputValue();
    await page.locator('#questions').fill('Changed question');
    await page.locator('#upload-form button').click();
    assert.equal(await page.locator('#upload').isVisible(), true);
    await page.locator('#questions').fill(originalQuestions);
    await page.locator('#upload-form button').click();
    await page.locator('#approve').waitFor({ state: 'visible' });
    await page.screenshot({ path: `${dir}/approval.png`, fullPage: true });
    await page.locator('#delete').click();
    await page.locator('nav a[href="#review"]').click();
    assert.equal(await page.locator('#review-card').isVisible(), false);
    await page.locator('nav a[href="#approve"]').click();
    await page.locator('#card-question').fill('');
    await page.locator('#accept').click();
    assert.equal(await page.locator('#card-status').innerText(), 'Удалена');
    await page.locator('#card-question').fill('Как работает активное воспроизведение?');
    await page.locator('#accept').click();
    await page.locator('nav a[href="#review"]').click();
    assert.equal(await page.locator('#review-question').innerText(), 'Как работает активное воспроизведение?');
    await page.locator('#reveal').click();
    assert.equal(await page.locator('#reference').isVisible(), false);
    await page.locator('#student-answer').fill('Вспомнить материал самостоятельно, без подсказок.');
    await page.locator('#reveal').click();
    assert.equal(await page.locator('#reference').isVisible(), true);
    await page.screenshot({ path: `${dir}/review.png`, fullPage: true });
    await page.locator('[data-grade="correct"]').click();
    assert.equal(await page.locator('#review-card').isVisible(), false);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator('nav a[href="#upload"]').click();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    await page.screenshot({ path: `${dir}/mobile.png`, fullPage: true });
    await page.locator('#title').focus();
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('#lecture').evaluate((node) => node === document.activeElement), true);
    assert.deepEqual(errors, []);
    console.log('PASS: demo guards, editing, deletion, approval, answer, self-assessment, keyboard, 390px; 4 screenshots.');
  } finally {
    if (browser) await browser.close();
    await new Promise((resolve) => server.close(resolve));
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
