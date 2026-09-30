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
    // Studio-style photo: a two-face carton on a graded grey backdrop, with a
    // soft cast shadow, a contact shadow and sensor noise. Tests shadow removal.
    'shadow-box.jpg': make(1200, 1400, (x) => {
      const g = x.createRadialGradient(560, 520, 100, 600, 700, 1000);
      g.addColorStop(0, '#f1f1ee'); g.addColorStop(1, '#d9d9d5');
      x.fillStyle = g; x.fillRect(0, 0, 1200, 1400);
      const box = new Path2D();
      box.moveTo(360, 380); box.lineTo(700, 330); box.lineTo(860, 400); box.lineTo(860, 1100); box.lineTo(700, 1180); box.lineTo(360, 1110); box.closePath();
      x.save(); x.filter = 'blur(38px)'; x.globalAlpha = 0.35; x.fillStyle = '#3a3a36';
      x.beginPath(); x.moveTo(700, 1180); x.lineTo(1080, 1060); x.lineTo(1120, 1000); x.lineTo(860, 1060); x.closePath(); x.fill();
      x.translate(60, 30); x.fill(box); x.restore();
      x.save(); x.filter = 'blur(6px)'; x.globalAlpha = 0.5; x.fillStyle = '#20201c';
      x.beginPath(); x.ellipse(610, 1150, 280, 24, 0.02, 0, Math.PI * 2); x.fill(); x.restore();
      x.fillStyle = '#6f8a4e'; x.beginPath(); x.moveTo(360, 380); x.lineTo(700, 330); x.lineTo(700, 1180); x.lineTo(360, 1110); x.closePath(); x.fill();
      x.fillStyle = '#56703b'; x.beginPath(); x.moveTo(700, 330); x.lineTo(860, 400); x.lineTo(860, 1100); x.lineTo(700, 1180); x.closePath(); x.fill();
      x.fillStyle = '#f3efe2'; x.font = 'bold 84px sans-serif'; x.fillText('OAT', 420, 560); x.font = '40px sans-serif'; x.fillText('crisp & toasted', 420, 620);
      x.fillStyle = '#e8c35a'; x.beginPath(); x.ellipse(530, 860, 110, 110, 0, 0, Math.PI * 2); x.fill();
      const d = x.getImageData(0, 0, 1200, 1400);
      let s = 7;
      for (let i = 0; i < d.data.length; i += 4) { s = (s * 1103515245 + 12345) >>> 0; const n = ((s >>> 24) - 128) / 40; d.data[i] += n; d.data[i + 1] += n; d.data[i + 2] += n; }
      x.putImageData(d, 0, 0);
    }, 'image/jpeg', 0.9),
    // White-capped bottle on an off-white backdrop with a soft shadow to the
    // left. The white cap must survive the cutout.
    'shadow-bottle.jpg': make(1000, 1300, (x) => {
      x.fillStyle = '#f4f3f0'; x.fillRect(0, 0, 1000, 1300);
      x.save(); x.filter = 'blur(30px)'; x.globalAlpha = 0.3; x.fillStyle = '#35332e';
      x.beginPath(); x.moveTo(420, 1130); x.lineTo(90, 1020); x.lineTo(120, 960); x.lineTo(560, 1080); x.closePath(); x.fill(); x.restore();
      x.save(); x.filter = 'blur(5px)'; x.globalAlpha = 0.45; x.fillStyle = '#1f1d1a';
      x.beginPath(); x.ellipse(500, 1135, 170, 18, 0, 0, Math.PI * 2); x.fill(); x.restore();
      const body = x.createLinearGradient(330, 0, 670, 0);
      body.addColorStop(0, '#2d4b63'); body.addColorStop(0.4, '#4f7695'); body.addColorStop(1, '#23394b');
      x.fillStyle = body; x.beginPath(); x.roundRect(330, 420, 340, 720, 48); x.fill();
      x.fillStyle = body; x.beginPath(); x.roundRect(420, 330, 160, 110, 12); x.fill();
      const cap = x.createLinearGradient(410, 0, 590, 0);
      cap.addColorStop(0, '#e9e8e4'); cap.addColorStop(0.45, '#ffffff'); cap.addColorStop(1, '#d6d4cf');
      x.fillStyle = cap; x.beginPath(); x.roundRect(410, 190, 180, 150, 14); x.fill();
      x.fillStyle = '#f7f4ea'; x.fillRect(360, 640, 280, 260);
      x.fillStyle = '#2d4b63'; x.font = 'bold 54px sans-serif'; x.fillText('TONIC', 420, 760);
      const d = x.getImageData(0, 0, 1000, 1300);
      let s = 11;
      for (let i = 0; i < d.data.length; i += 4) { s = (s * 1103515245 + 12345) >>> 0; const n = ((s >>> 24) - 128) / 48; d.data[i] += n; d.data[i + 1] += n; d.data[i + 2] += n; }
      x.putImageData(d, 0, 0);
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
