import { chromium } from 'playwright';
import fs from 'node:fs';

const baseURL = process.env.BASE_URL || 'http://127.0.0.1:8000/kajitori_minimal_pictogram_compact.html';
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });

const seed = {
  tasksByDate: {},
  missedLog: [],
  retryQueue: [],
  v02: {
    version: 2,
    profile: {
      initialized: true,
      babyBirthdate: '2026-04-22',
      olderChild: true,
      daycare: true,
      feeding: 'mixed',
      leaveEnd: '',
      rhythm: 'all_day'
    },
    days: {},
    stateFacts: {},
    questionHistory: [],
    questionCooldownUntil: {},
    questionKnowStreak: {},
    evidenceEvents: [],
    spontaneous: []
  }
};

await context.addInitScript((data) => {
  localStorage.setItem('kajitori_stable_mvp_v2', JSON.stringify(data));
}, seed);

const page = await context.newPage();
const errors = [];
page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
page.on('console', (msg) => {
  if (msg.type() === 'error') errors.push(`console: ${msg.text()}`);
});

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

await page.goto(baseURL, { waitUntil: 'networkidle' });

assert(await page.locator('.brand h1').textContent() === '家事取りゲーム', 'brand title mismatch');
assert((await page.locator('#headerSubtitle').textContent()).includes('v0.3'), 'v0.3 subtitle missing');
assert(await page.locator('#onboarding.show').count() === 0, 'seeded profile unexpectedly opened onboarding');
assert(await page.locator('.bottom-nav .tab').count() === 3, 'bottom nav must contain exactly three tabs');
assert(await page.locator('.task-card').count() > 0, 'today task cards are missing');

const mainBox = await page.locator('#mainScroll').boundingBox();
const navBox = await page.locator('.bottom-nav').boundingBox();
assert(mainBox && navBox, 'main/nav boxes missing');
assert(mainBox.y + mainBox.height <= navBox.y + 1, 'bottom nav overlaps the scrollable main region');

const minTarget = await page.evaluate(() => {
  const selectors = ['button', '.task-card', '.tab'];
  const nodes = [...document.querySelectorAll(selectors.join(','))];
  return nodes.filter((el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
  }).reduce((min, el) => Math.min(min, el.getBoundingClientRect().height), Infinity);
});
assert(minTarget >= 38, `visible interactive target below smoke threshold: ${minTarget}px`);

await page.getByRole('button', { name: '3件' }).click();
let stored = await page.evaluate(() => JSON.parse(localStorage.getItem('kajitori_stable_mvp_v2')));
const dayKey = Object.keys(stored.v02.days)[0];
assert(stored.v02.days[dayKey].capacity === 'ahead', '3件 setting did not persist as ahead');

await page.locator('[data-task="diaper_stock"] .chev').click();
assert(await page.locator('#detailOverlay.show').count() === 1, 'detail bottom sheet did not open');
await page.getByRole('button', { name: '少なめ' }).click();
await page.getByRole('button', { name: 'これで完了' }).click();
assert(await page.locator('#detailOverlay.show').count() === 0, 'detail bottom sheet did not close after completion');

stored = await page.evaluate(() => JSON.parse(localStorage.getItem('kajitori_stable_mvp_v2')));
assert(stored.v02.days[dayKey].status.diaper_stock === 'done', 'diaper task was not persisted as done');
assert(stored.v02.stateFacts.diaper_stock?.value === 'soon', 'diaper state was not persisted as soon');
assert(stored.v02.stateFacts.diaper_stock?.checkedDate === dayKey, 'diaper state freshness date missing');
assert(stored.v02.evidenceEvents.some((e) => e.templateId === 'diaper_stock'), 'inventory evidence event was not created');

const simpleCandidates = ['meal_plan', 'laundry_next', 'tomorrow_plan', 'rest_window'];
let simpleId = null;
for (const id of simpleCandidates) {
  if (await page.locator(`[data-task="${id}"] .task-check`).count()) {
    simpleId = id;
    break;
  }
}
assert(simpleId, 'no visible simple task available for one-tap completion test');
await page.locator(`[data-task="${simpleId}"] .task-check`).click();
stored = await page.evaluate(() => JSON.parse(localStorage.getItem('kajitori_stable_mvp_v2')));
assert(stored.v02.days[dayKey].status[simpleId] === 'done', 'simple task did not complete in one tap');

await page.locator(`[data-task="${simpleId}"] .task-check`).click();
stored = await page.evaluate(() => JSON.parse(localStorage.getItem('kajitori_stable_mvp_v2')));
assert(stored.v02.days[dayKey].status[simpleId] === 'active', 'completed simple task did not reopen');

await page.locator('.bottom-nav [data-tab="forecast"]').click();
assert(await page.locator('#forecastView.active').count() === 1, 'forecast tab did not activate');
assert(await page.locator('.forecast-card').count() > 0, 'forecast cards missing');
await page.locator('.bottom-nav [data-tab="record"]').click();
assert(await page.locator('#recordView.active').count() === 1, 'record tab did not activate');

await page.locator('.bottom-nav [data-tab="today"]').click();
await page.locator('[data-task="diaper_stock"] .chev').click();
fs.mkdirSync('artifacts', { recursive: true });
await page.screenshot({ path: 'artifacts/v03-iphone-smoke.png', fullPage: false });

assert(errors.length === 0, `browser errors detected:\n${errors.join('\n')}`);

await browser.close();
console.log('v0.3 smoke test: PASS');
