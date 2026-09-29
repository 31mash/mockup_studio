// Draws the e2e fixture images with the browser's canvas.
// Run from prototype/: node tests/fixtures/make-fixtures.mjs
import { chromium } from '@playwright/test';
import { writeFileSync } from 'node:fs';

const browser = await chromium.launch();
const page = await browser.newPage();
const files = await page.evaluate(async () => {
  const make = (w, h, draw, type = 'image/png', q) => {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    draw(c.getContext('2d'));
    return c.toDataURL(type, q);
  };
  return {
    // Product on a plain white backdrop: a ceramic mug.
    'mug-white.jpg': make(1200, 1200, (x) => {
      x.fillStyle = '#f6f6f3'; x.fillRect(0, 0, 1200, 1200);
      x.fillStyle = '#385c78'; x.beginPath(); x.roundRect(380, 360, 400, 540, 40); x.fill();
      x.strokeStyle = '#385c78'; x.lineWidth = 46; x.beginPath(); x.ellipse(830, 610, 70, 110, 0, 0, Math.PI * 2); x.stroke();
      x.fillStyle = '#466c8a'; x.beginPath(); x.ellipse(580, 360, 200, 40, 0, 0, Math.PI * 2); x.fill();
      x.fillStyle = '#1e3040'; x.beginPath(); x.ellipse(580, 360, 160, 28, 0, 0, Math.PI * 2); x.fill();
      x.fillStyle = '#ece6d6'; x.fillRect(470, 560, 220, 140);
    }, 'image/jpeg', 0.92),
    // Transparent product cutout.
    'bottle-alpha.png': make(800, 1000, (x) => {
      x.fillStyle = '#c4483a'; x.beginPath(); x.roundRect(220, 180, 360, 720, 60); x.fill();
      x.fillStyle = '#28282c'; x.fillRect(330, 90, 140, 100);
    }),
    // A person-like portrait on a plain grey backdrop.
    'person-plain.jpg': make(900, 1200, (x) => {
      x.fillStyle = '#c8c9cb'; x.fillRect(0, 0, 900, 1200);
      x.fillStyle = '#34463c'; x.beginPath(); x.roundRect(170, 560, 560, 700, 120); x.fill();
      x.fillStyle = '#966c50'; x.fillRect(400, 440, 100, 140);
      x.fillStyle = '#a07658'; x.beginPath(); x.ellipse(450, 330, 120, 150, 0, 0, Math.PI * 2); x.fill();
    }, 'image/jpeg', 0.92),
    // A busy backdrop the keyer should refuse to separate.
    'busy-scene.jpg': make(1000, 800, (x) => {
      for (let i = 0; i < 400; i++) {
        x.fillStyle = `hsl(${(i * 37) % 360} 60% ${30 + (i % 40)}%)`;
        x.fillRect((i * 97) % 1000, (i * 53) % 800, 80, 60);
      }
    }, 'image/jpeg', 0.9),
    // Tiny image for the low-resolution warning.
    'tiny.png': make(300, 240, (x) => {
      x.fillStyle = '#ffffff'; x.fillRect(0, 0, 300, 240);
      x.fillStyle = '#6a4'; x.fillRect(100, 60, 100, 120);
    }),
  };
});
for (const [name, url] of Object.entries(files)) {
  writeFileSync(new URL(name, import.meta.url), Buffer.from(url.split(',')[1], 'base64'));
}
writeFileSync(new URL('not-an-image.txt', import.meta.url), 'This is text, not an image.\n');
await browser.close();
console.log('fixtures written:', Object.keys(files).join(', '));
