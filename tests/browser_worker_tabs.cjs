const { chromium } = require('../tmp/browser-check/node_modules/playwright');
const assert = require('node:assert/strict');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, serviceWorkers: 'block' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const base = process.env.BANJANG_TEST_URL || 'http://127.0.0.1:8018';
  const task = await (await context.request.post(base + '/api/tasks', { data: { text: '2층 용접 작업, 주변에 합판', worker_id: 2 } })).json();

  await page.goto(base);
  await page.getByLabel('아이디').fill('admin');
  await page.getByLabel('비밀번호').fill('1234');
  await page.getByRole('button', { name: '로그인' }).click();
  await page.getByRole('link', { name: 'JSA', exact: true }).click();
  await page.getByRole('heading', { name: '오늘의 JSA' }).waitFor();
  await page.evaluate(() => localStorage.removeItem('banjang.user'));
  await page.goto(base + '/#/login');
  await page.reload();

  await page.getByLabel('아이디').fill('worker');
  await page.getByLabel('비밀번호').fill('1234');
  await page.getByRole('button', { name: '로그인' }).click();
  await page.getByText('2층 용접 작업, 주변에 합판', { exact: true }).waitFor();
  await page.getByRole('heading', { name: '안전 체크리스트' }).waitFor();
  assert(await page.getByText('화재감시자 배치', { exact: true }).isVisible());
  assert(await page.getByText('불티 비산 방지포 설치', { exact: true }).isVisible());

  await page.getByRole('link', { name: '사진', exact: true }).click();
  const submit = page.getByRole('button', { name: '제출하기' });
  assert(await submit.isDisabled());
  await page.getByLabel('위험 요소와 바라는 조치').fill('통로에 자재가 쌓여 있습니다. 이동 조치가 필요합니다.');
  assert(await submit.isEnabled());
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=', 'base64');
  await page.getByLabel('사진 첨부하기').setInputFiles({ name: 'risk.png', mimeType: 'image/png', buffer: png });
  await submit.click();
  await page.getByText('위험 요소를 신고했습니다.', { exact: false }).waitFor();
  await page.getByText('조치중', { exact: true }).waitFor();
  const reports = await (await context.request.get(base + '/api/incidents?worker_id=2')).json();
  await context.request.post(`${base}/api/incidents/${reports[0].id}/follow-up`, { data: {} });
  await page.reload();
  await page.getByText('조치 완료', { exact: true }).first().waitFor();
  await page.screenshot({ path: 'tmp/browser-check/worker-risk-reports.png', fullPage: true });

  await page.getByRole('link', { name: '캘린더', exact: true }).click();
  await page.waitForTimeout(500);
  if (!(await page.getByText('2026년 10월', { exact: true }).count())) {
    throw new Error(`calendar missing at ${page.url()}\n${await page.locator('body').innerText()}\npage errors: ${errors.join(' | ')}`);
  }
  await page.getByText('2026년 10월', { exact: true }).waitFor();
  await page.getByRole('link', { name: '내 기록', exact: true }).click();
  await page.getByText(/점$/, { exact: false }).first().waitFor();
  assert.deepEqual(errors, []);
  assert.equal(task.worker_id, 2);
  console.log('PASS: JSA route, worker checklist, risk report validation/status, calendar and personal score; no browser errors');
  await browser.close();
})().catch(error => { console.error(error); process.exit(1); });
