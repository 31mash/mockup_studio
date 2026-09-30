import { expect, test, type Page } from '@playwright/test';
import { fileURLToPath } from 'node:url';

const fixture = (name: string) => fileURLToPath(new URL(`../fixtures/${name}`, import.meta.url));
const newestJob = (page: Page) => page.locator('.jobs > section').first();
const jobCount = (page: Page) => page.locator('.jobs > section').count();

async function openStudio(page: Page) {
  await page.goto('/');
  // First open seeds a sample product, a turned example and a two-image batch.
  await expect(page.getByRole('button', { name: 'Download image', exact: true })).toHaveCount(3, { timeout: 20_000 });
}

async function openSettings(page: Page) {
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  return page.getByRole('dialog', { name: 'Settings' });
}

test('first open shows a sample product and example batches', async ({ page }) => {
  await openStudio(page);
  await expect(page.getByText('Sample dropper bottle')).toBeVisible();
  await expect(page.getByRole('heading', { name: /Minimalist Podiums, 3:4/ })).toBeVisible();
  await expect(page.getByRole('heading', { name: /Studio white, 1:1/ })).toBeVisible();
  await expect(page.getByText(/three-quarter right view/)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Generate 1 image' })).toBeEnabled();
});

test('upload a product, keep defaults, generate 1, download it', async ({ page }) => {
  await openStudio(page);
  await page.getByLabel('Upload product photo').setInputFiles(fixture('mug-white.jpg'));
  await expect(page.getByText('mug-white.jpg')).toBeVisible();
  await page.getByRole('button', { name: 'Generate 1 image' }).click();
  const job = newestJob(page);
  await expect(job.getByRole('button', { name: 'Download image', exact: true })).toHaveCount(1, { timeout: 20_000 });
  await expect(job.getByRole('heading')).toHaveText('Studio white, Auto');

  const [download] = await Promise.all([page.waitForEvent('download'), job.getByRole('button', { name: 'Download image', exact: true }).click()]);
  expect(download.suggestedFilename()).toMatch(/^product-studio-white-auto-1\.jpg$/);

  // Auto follows the 1:1 source; the subject was keyed off its white backdrop.
  await job.getByRole('button', { name: /^Details for/ }).click();
  const details = page.getByRole('dialog', { name: 'Job details' });
  await expect(details.getByText('1536 × 1536 px, native framing')).toBeVisible();
  await expect(details.getByText('Separated from a plain backdrop on this device')).toBeVisible();
  await expect(details.locator('.brief')).toContainText('Keep this exact product.');
});

test('tab drafts survive switching and reload (plan task 3)', async ({ page }) => {
  await openStudio(page);
  await page.getByRole('tab', { name: 'Product', exact: true }).click();
  await page.getByLabel('Describe your image').fill('Soft morning light');
  await page.getByRole('tab', { name: 'Model', exact: true }).click();
  await page.getByLabel('Describe your image').fill('Warm cafe portrait');
  await page.waitForTimeout(400);
  await page.reload();
  await expect(page.getByLabel('Describe your image')).toHaveValue('Warm cafe portrait');
  await page.getByRole('tab', { name: 'Product', exact: true }).click();
  await expect(page.getByLabel('Describe your image')).toHaveValue('Soft morning light');
});

test('filter and select a model, Cafe at 9:16, generate 4 (plan task 4)', async ({ page }) => {
  await openStudio(page);
  await page.getByRole('tab', { name: 'Model', exact: true }).click();
  await page.getByRole('button', { name: 'Select model', exact: true }).click();
  const picker = page.getByRole('dialog', { name: 'Select model' });
  await expect(picker).toBeVisible();
  await page.getByLabel('Age group').selectOption('teen');
  await page.getByLabel('Gender presentation').selectOption('female');
  await expect(picker.getByText('1 model', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Select model Maya' }).click();
  await expect(page.getByText('Teen, female, Tone 4')).toBeVisible();

  await page.getByRole('button', { name: /^Background:/ }).click();
  await page.getByRole('radio', { name: /^Cafe/ }).click();
  await page.getByRole('button', { name: /^Ratio:/ }).click();
  await page.getByRole('radio', { name: '9:16', exact: true }).click();
  await page.getByRole('radio', { name: '4 results', exact: true }).check();
  await expect(page.getByRole('button', { name: 'Generate 4 images' })).toBeEnabled();
  await page.getByRole('button', { name: 'Generate 4 images' }).click();

  const job = newestJob(page);
  await expect(job.getByRole('button', { name: 'Download image', exact: true })).toHaveCount(4, { timeout: 30_000 });
  const sizes = await job.locator('.frame-btn img').evaluateAll((imgs) => imgs.map((i) => [(i as HTMLImageElement).naturalWidth, (i as HTMLImageElement).naturalHeight]));
  expect(sizes).toEqual([
    [864, 1536],
    [864, 1536],
    [864, 1536],
    [864, 1536],
  ]);
  await job.getByRole('button', { name: /^Details for/ }).click();
  await expect(page.getByRole('dialog', { name: 'Job details' }).locator('.brief')).toContainText('fully clothed');
});

test('a failed image keeps the others and retries alone (plan task 7)', async ({ page }) => {
  await openStudio(page);
  const settings = await openSettings(page);
  await settings.getByLabel(/Fail one image in each batch/).check();
  await settings.getByRole('button', { name: 'Close' }).click();

  await page.getByRole('radio', { name: '4 results', exact: true }).check();
  await page.getByRole('button', { name: 'Generate 4 images' }).click();
  const job = newestJob(page);
  await expect(job.getByRole('button', { name: 'Download image', exact: true })).toHaveCount(3, { timeout: 20_000 });
  await expect(job.getByText('Partial, 3 of 4 ready')).toBeVisible();
  await expect(job.getByRole('button', { name: 'Retry failed image', exact: true })).toHaveCount(1);
  const before = await jobCount(page);
  await job.getByRole('button', { name: 'Retry failed image', exact: true }).click();
  await expect(job.getByRole('button', { name: 'Download image', exact: true })).toHaveCount(4, { timeout: 20_000 });
  expect(await jobCount(page)).toBe(before); // a retry is not a second batch
  await job.getByRole('button', { name: /^Details for/ }).click();
  await expect(page.getByRole('dialog', { name: 'Job details' }).getByText(/Image 3: Ready, attempt 2/)).toBeVisible();
});

test('cloud jobs queue while offline and wait for review (plan task 8)', async ({ page, context }) => {
  await openStudio(page);
  const settings = await openSettings(page);
  await settings.getByLabel('Cloud (simulated)').check();
  await settings.getByRole('button', { name: 'Close' }).click();

  // A real browser offline event switches Generate to Queue for online.
  await context.setOffline(true);
  await expect(page.getByRole('button', { name: 'Queue for online' })).toBeVisible();
  const jobsBefore = await jobCount(page);
  await page.getByRole('button', { name: 'Queue for online' }).click();
  await expect(page.getByText('1 job waiting for connection')).toBeVisible();
  await context.setOffline(false);

  // Restart while still offline. Without a service worker the page itself
  // needs the network, so this uses the persisted "Simulate offline" switch.
  const s2 = await openSettings(page);
  await s2.getByLabel(/Simulate offline/).check();
  await s2.getByRole('button', { name: 'Close' }).click();
  await page.waitForTimeout(400);
  await page.reload();
  await expect(page.getByText('1 job waiting for connection')).toBeVisible();
  expect(await jobCount(page)).toBe(jobsBefore);

  const s3 = await openSettings(page);
  await s3.getByLabel(/Simulate offline/).uncheck();
  await s3.getByRole('button', { name: 'Close' }).click();
  await expect(page.getByRole('button', { name: 'Review and send' })).toBeVisible();
  expect(await jobCount(page)).toBe(jobsBefore); // reconnecting sends nothing by itself

  await page.getByRole('button', { name: 'Review and send' }).click();
  await page.getByRole('dialog', { name: 'Review and send' }).getByRole('button', { name: 'Send all' }).click();
  const job = newestJob(page);
  await expect(job.getByText('simulated cloud')).toBeVisible();
  await expect(job.getByRole('button', { name: 'Download image', exact: true })).toHaveCount(1, { timeout: 20_000 });
  await expect(page.getByText(/waiting for connection|ready to review/)).toHaveCount(0);
});

test('camera: keyboard and numbers agree, Cancel restores, nothing generates (plan task 5)', async ({ page }) => {
  await openStudio(page);
  const jobsBefore = await jobCount(page);
  await page.getByRole('button', { name: /^Angle:/ }).click();
  const sheet = page.getByRole('dialog', { name: 'Camera angle' });
  const guide = sheet.getByRole('group', { name: /Camera position guide/ });
  await guide.focus();
  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('ArrowRight');
  await page.keyboard.press('Shift+ArrowUp');
  await expect(sheet.getByLabel('Rotation in degrees')).toHaveValue('10');
  await expect(sheet.getByLabel('Tilt in degrees')).toHaveValue('15');
  await sheet.getByRole('button', { name: 'Cancel' }).click();
  await expect(page.getByRole('button', { name: 'Angle: Original. Change angle' })).toBeVisible();

  await page.getByRole('button', { name: /^Angle:/ }).click();
  await expect(sheet.getByLabel('Rotation in degrees')).toHaveValue('0');
  const box = (await guide.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 60, box.y + box.height / 2, { steps: 6 });
  await page.mouse.up();
  await expect(sheet.getByLabel('Rotation in degrees')).not.toHaveValue('0');
  await expect(sheet.getByRole('radio', { name: 'Left profile' })).toBeDisabled();
  await expect(sheet.getByText(/Profile and top-down views need a generative engine/)).toBeVisible();
  await sheet.getByRole('radio', { name: 'Three-quarter left' }).click();
  await expect(sheet.getByText(/turns in real perspective/)).toBeVisible();
  await sheet.getByRole('button', { name: 'Apply angle' }).click();
  await expect(page.getByRole('button', { name: 'Angle: Three-quarter left. Change angle' })).toBeVisible();
  expect(await jobCount(page)).toBe(jobsBefore);
});

test('all nine ratios appear on both tabs', async ({ page }) => {
  await openStudio(page);
  for (const tab of ['Product', 'Model']) {
    await page.getByRole('tab', { name: tab, exact: true }).click();
    await page.getByRole('button', { name: /^Ratio:/ }).click();
    const dialog = page.getByRole('dialog', { name: 'Aspect ratio' });
    await expect(dialog.getByRole('radio')).toHaveText(['Auto', '1:1', '3:2', '2:3', '4:3', '3:4', '9:16', '16:9', '21:9']);
    await dialog.getByRole('button', { name: 'Close' }).click();
  }
});

test('bad files explain what to do; busy backdrops are placed whole', async ({ page }) => {
  await openStudio(page);
  await page.getByLabel('Upload product photo').setInputFiles(fixture('not-an-image.txt'));
  await expect(page.getByText('Use a JPEG, PNG or WebP image.')).toBeVisible();

  await page.getByLabel('Upload product photo').setInputFiles(fixture('tiny.png'));
  await expect(page.getByText(/under 512 px/)).toBeVisible();

  await page.getByLabel('Upload product photo').setInputFiles(fixture('busy-scene.jpg'));
  await expect(page.getByText('busy-scene.jpg')).toBeVisible();
  await page.getByRole('button', { name: 'Generate 1 image' }).click();
  const job = newestJob(page);
  await expect(job.getByRole('button', { name: 'Download image', exact: true })).toHaveCount(1, { timeout: 20_000 });
  await job.getByRole('button', { name: /^Details for/ }).click();
  await expect(page.getByText('Not separated. The photo is placed whole')).toBeVisible();
});

test('an uploaded person needs a rights acknowledgment', async ({ page }) => {
  await openStudio(page);
  await page.getByRole('tab', { name: 'Model', exact: true }).click();
  await page.getByLabel('Upload a photo of a person').setInputFiles(fixture('person-plain.jpg'));
  const generate = page.getByRole('button', { name: 'Generate 1 image' });
  await expect(generate).toBeDisabled();
  await expect(page.getByText('Confirm you have the rights and consent to use this photo.')).toBeVisible();
  await page.getByLabel(/I have the rights/).check();
  await expect(generate).toBeEnabled();
  await generate.click();
  await expect(newestJob(page).getByRole('button', { name: 'Download image', exact: true })).toHaveCount(1, { timeout: 20_000 });
});

test('cancel stops pending cloud work', async ({ page }) => {
  await openStudio(page);
  const settings = await openSettings(page);
  await settings.getByLabel('Cloud (simulated)').check();
  await settings.getByRole('button', { name: 'Close' }).click();
  await page.getByRole('radio', { name: '4 results', exact: true }).check();
  await page.getByRole('button', { name: 'Generate 4 images' }).click();
  const job = newestJob(page);
  await job.getByRole('button', { name: 'Cancel' }).click();
  await expect(job.getByText('Canceled', { exact: true }).first()).toBeVisible();
  await expect(job.getByRole('button', { name: 'Download image', exact: true })).toHaveCount(0);
});

test('a turned product renders, and people keep their photographed angle', async ({ page }) => {
  await openStudio(page);
  await page.getByRole('button', { name: /^Angle:/ }).click();
  const sheet = page.getByRole('dialog', { name: 'Camera angle' });
  await sheet.getByLabel('Rotation in degrees').fill('90');
  await sheet.getByLabel('Rotation in degrees').press('Enter');
  await expect(sheet.getByLabel('Rotation in degrees')).toHaveValue('35'); // clamped to what the engine can do
  await sheet.getByRole('button', { name: 'Apply angle' }).click();
  await page.getByRole('button', { name: 'Generate 1 image' }).click();
  const job = newestJob(page);
  await expect(job.getByRole('button', { name: 'Download image', exact: true })).toHaveCount(1, { timeout: 20_000 });
  await job.getByRole('button', { name: /^Details for/ }).click();
  await expect(page.getByRole('dialog', { name: 'Job details' }).getByText(/turned in perspective/)).toBeVisible();
  await page.getByRole('dialog', { name: 'Job details' }).getByRole('button', { name: 'Close' }).click();

  await page.getByRole('tab', { name: 'Model', exact: true }).click();
  await page.getByRole('button', { name: /^Angle:/ }).click();
  await expect(sheet.getByLabel('Rotation', { exact: true })).toBeDisabled();
  await expect(sheet.getByRole('radio', { name: 'Three-quarter left' })).toBeDisabled();
  await expect(sheet.getByText('Turning a person needs a generative engine. Zoom still works here.')).toBeVisible();
});
