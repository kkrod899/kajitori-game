import { chromium, webkit } from 'playwright';
import fs from 'node:fs';

const browserName = process.env.BROWSER || 'chromium';
const browserType = browserName === 'webkit' ? webkit : chromium;
const url = process.env.SHADOW_URL || 'http://127.0.0.1:8123/artifacts/shadow_console_v2.html';
const browser = await browserType.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
const page = await context.newPage();
const errors = [];
const externalRequests = [];
page.on('pageerror', error => errors.push(`pageerror: ${error.message}`));
page.on('console', msg => { if (msg.type() === 'error') errors.push(`console: ${msg.text()}`); });
page.on('request', request => {
  const target = new URL(request.url());
  if (target.origin !== new URL(url).origin) externalRequests.push(request.url());
});

function assert(condition, message) { if (!condition) throw new Error(`[${browserName}] ${message}`); }
async function tri(id, value) { await page.locator(`[data-field-id="${id}"] button[data-tri="${value}"]`).click(); }

await page.goto(url, { waitUntil: 'networkidle' });
assert(await page.getByRole('heading', { name: '家事取り Shadow v2' }).count() === 1, 'title missing');
assert(await page.locator('.bottom-nav button').count() === 3, 'three navigation buttons required');

await page.getByRole('button', { name: '家庭設定を始める' }).click();
for (const id of ['infant','older_child','daycare','two_adult_household','uses_car','bottle_used','local_area_set']) {
  const box = page.locator(`[data-profile="${id}"]`);
  if (!(await box.isChecked())) await box.check();
}
await page.getByRole('button', { name: '保存' }).click();

await tri('daycare_today','yes');
await tri('daycare_tomorrow','yes');
await tri('daycare_unread','yes');
await tri('daycare_prep','no');
await page.locator('[data-field-id="daycare_deadline"]').fill('6');
await tri('daycare_deadline_closed','no');
await page.locator('[data-field-id="milk_stock"]').selectOption('critical');
await page.locator('[data-field-id="diaper_stock"]').selectOption('low');
await tri('dinner_decided','no');
await tri('sink_blocked','yes');
await tri('laundry_urgent','yes');
await tri('handoff_due','yes');

await page.getByRole('button', { name: '候補を生成して封印' }).click();
await page.getByText('候補は封印済み').waitFor();
assert(await page.locator('.candidate-card').count() === 0, 'candidate cards leaked before reveal');
const sealedText = await page.locator('main').innerText();
assert(!sealedText.includes('園の提出書類'), 'candidate content leaked before reveal');
assert(!sealedText.match(/\d+カード/), 'candidate count leaked before reveal');

let stored = await page.evaluate(() => JSON.parse(localStorage.getItem('kajitori_shadow_v2')));
const dayKey = Object.keys(stored.days)[0];
const snapshot = stored.days[dayKey].engineSnapshot;
assert(stored.days[dayKey].phase === 'sealed', 'sealed phase not persisted');
assert(snapshot.hash.length === 64, 'snapshot hash missing');
assert(snapshot.payload.atomic.some(x => x.id === 'DAYCARE-008'), 'known daycare deadline did not activate');
assert(snapshot.payload.atomic.some(x => x.id === 'INF-FEED-005'), 'critical milk stock did not activate');
assert(snapshot.payload.cards.length < snapshot.payload.atomic.length, 'atomic responsibilities were not bundled into cards');

await page.locator('.bottom-nav [data-view="actual"]').click();
await page.getByRole('button', { name: '＋ 必要事項を記録' }).click();
await page.locator('#actualSearch').fill('オムツ在庫が次の購入まで持つか判断する [INF-DIAP-002]');
await page.locator('#actualSource').selectOption('self');
await page.locator('#completed').check();
await page.locator('#loopClosed').check();
await page.getByRole('button', { name: '保存' }).click();
assert(await page.locator('[data-actual-id]').count() === 1, 'actual responsibility log missing');

await page.getByRole('button', { name: '記録を確定して候補を開く' }).click();
await page.locator('.candidate-card').first().waitFor();
stored = await page.evaluate(() => JSON.parse(localStorage.getItem('kajitori_shadow_v2')));
assert(stored.days[dayKey].phase === 'revealed', 'revealed phase not persisted');
assert(stored.days[dayKey].actualLogConfirmedAt, 'pre-reveal confirmation timestamp missing');
assert(stored.days[dayKey].revealedAt, 'reveal timestamp missing');

let firstCard = page.locator('.candidate-card').first();
await firstCard.locator('[data-review="needed"] button[data-value="yes"]').click();
firstCard = page.locator('.candidate-card').first();
await firstCard.locator('[data-review="timing"] button[data-value="right"]').click();

await page.locator('.bottom-nav [data-view="export"]').click();
assert(await page.getByText('atomic見落とし').count() === 1, 'atomic metric missing');
assert(await page.getByText('不要カード').count() === 1, 'card noise metric missing');
assert(await page.getByRole('button', { name: '実証一式をJSONで保存' }).count() === 1, 'bundle export missing');
assert(await page.getByRole('button', { name: '観測行をJSONLで保存' }).count() === 1, 'JSONL export missing');

await page.reload({ waitUntil: 'networkidle' });
assert(await page.locator('.candidate-card').count() > 0, 'revealed state was not restored after reload');
await page.locator('.bottom-nav [data-view="export"]').click();
assert(await page.getByText('今日の集計').count() === 1, 'metrics view not restored from persisted data');
assert(externalRequests.length === 0, `unexpected external requests: ${externalRequests.join(', ')}`);
assert(errors.length === 0, `browser errors:\n${errors.join('\n')}`);

fs.mkdirSync('artifacts/screenshots', { recursive: true });
await page.screenshot({ path: `artifacts/screenshots/shadow-console-${browserName}.png`, fullPage: false });
await browser.close();
console.log(`shadow console v2 ${browserName}: PASS`);
