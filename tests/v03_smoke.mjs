import { chromium, webkit } from 'playwright';
import fs from 'node:fs';

const baseURL = process.env.BASE_URL || 'http://127.0.0.1:8000/kajitori_minimal_pictogram_compact.html';
const browserName = process.env.BROWSER || 'chromium';
const browserType = browserName === 'webkit' ? webkit : chromium;
const browser = await browserType.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });

const seed = {
  tasksByDate: { legacy_day: { sentinel: true } },
  missedLog: [{ sentinel: 'legacy-missed' }],
  retryQueue: [{ sentinel: 'legacy-retry' }],
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
    questionHistory: [{ date: '2026-09-01', key: 'night_set', answer: 'know' }],
    questionCooldownUntil: {},
    questionKnowStreak: { night_set: 1 },
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
  if (!condition) throw new Error(`[${browserName}] ${message}`);
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

await page.getByRole('button', { name: '0件' }).click();
assert(await page.locator('.task-card').count() === 0, '0件 mode still renders active task cards');
assert((await page.locator('.empty-card').textContent()).includes('今日は0件で大丈夫'), '0件 empty state missing');

await page.getByRole('button', { name: '3件' }).click();
assert(await page.locator('.task-card').count() > 0, 'task cards did not return after leaving 0件 mode');
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
const nextSizeCard = page.locator('.forecast-card').filter({ hasText: '次のオムツサイズ' });
if (await nextSizeCard.count()) {
  await nextSizeCard.getByRole('button', { name: '今日の一覧に追加' }).click();
  assert(await page.locator('#todayView.active').count() === 1, 'forecast add did not return to today');
  assert(await page.locator('[data-task="next_size"]').count() === 1, 'explicitly added non-recurring forecast item is not visible today');
}

await page.locator('.bottom-nav [data-tab="record"]').click();
assert(await page.locator('#recordView.active').count() === 1, 'record tab did not activate');

stored = await page.evaluate(() => JSON.parse(localStorage.getItem('kajitori_stable_mvp_v2')));
assert(stored.tasksByDate?.legacy_day?.sentinel === true, 'legacy tasksByDate was lost');
assert(stored.missedLog?.[0]?.sentinel === 'legacy-missed', 'legacy missedLog was lost');
assert(stored.retryQueue?.[0]?.sentinel === 'legacy-retry', 'legacy retryQueue was lost');
assert(stored.v02.questionHistory?.[0]?.key === 'night_set', 'existing v02 question history was lost');

await page.locator('.bottom-nav [data-tab="today"]').click();
await page.locator('[data-task="diaper_stock"] .chev').click();
fs.mkdirSync('artifacts', { recursive: true });
await page.screenshot({ path: `artifacts/v03-iphone-${browserName}.png`, fullPage: false });

assert(errors.length === 0, `browser errors detected:\n${errors.join('\n')}`);
await browser.close();
console.log(`v0.3 ${browserName} smoke test: PASS`);
