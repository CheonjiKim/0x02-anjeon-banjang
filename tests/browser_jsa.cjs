const { chromium } = require('../tmp/browser-check/node_modules/playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const base = process.env.BANJANG_TEST_URL || 'http://127.0.0.1:8018';
  const task = await (await context.request.post(base + '/api/tasks', { data: { text: '2층 용접 작업', worker_id: 2 } })).json();
  await context.request.post(base + '/api/worker-forms', { data: {
    task_id: task.id, worker_id: 2, report_text: '용접과 주변 정리를 마쳤습니다.', risk_note: '통로 자재를 치워야 합니다.',
  }});
  await page.goto(base);
  await page.getByRole('button', { name: '관리자 · 반장 출근하기' }).click();
  await page.getByRole('link', { name: 'JSA', exact: true }).click();
  await page.getByRole('button', { name: '오늘의 JSA 작성하기' }).click();
  const dialog = page.getByRole('dialog', { name: 'AI JSA 초안' });
  await dialog.getByText('용접과 주변 정리를 마쳤습니다.', { exact: false }).waitFor();
  await dialog.getByLabel('JSA 제목').fill('관리자가 확인한 오늘의 JSA');
  await dialog.getByLabel('안전 조치').fill('통로 자재 제거 후 용접 감시자를 배치한다.');
  await page.screenshot({ path: 'tmp/browser-check/jsa-draft.png' });
  await dialog.getByRole('button', { name: 'JSA 저장' }).click();
  await page.getByText('오늘의 JSA를 저장했습니다.').waitFor();
  await page.getByText('관리자가 확인한 오늘의 JSA', { exact: true }).click();
  const savedDialog = page.getByRole('dialog', { name: 'JSA 보기·수정' });
  assert.equal(await savedDialog.getByLabel('안전 조치').inputValue(), '통로 자재 제거 후 용접 감시자를 배치한다.');
  assert.deepEqual(errors, []);
  console.log('PASS: JSA draft generation, editable popup, save, history reopen; no browser errors');
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
