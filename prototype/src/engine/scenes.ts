import type { SceneKind } from '../domain/catalogs';
import { blurredLayer, composite, vGradient, type Ctx } from './canvas';
import { mix, rgba, shade } from './color';

/**
 * Procedural scene painters for the sketch engine. Each one reads the camera:
 * tilt moves the horizon, rotation shifts the scenery sideways (parallax) and
 * swings the light. None of them redraws the subject.
 */
export type SceneParams = {
  W: number;
  H: number;
  horizon: number;
  parallax: number;
  light: number; // radians; 0 = light from the right, negative = from the upper left
  color: string;
  rand: () => number;
  /** Where the subject stands, for scenes that build around it. */
  subject: { x: number; y: number; w: number; h: number };
  tilt: number;
};

export const SCENE_AMBIENT: Record<SceneKind, string | null> = {
  'studio-white': null,
  'seamless-monochrome': null,
  'minimalist-podium': '#F4EFE6',
  'natural-outdoor': '#FFE7C4',
  'aesthetic-indoor': '#F4D9B6',
  'natural-outdoor-environment': '#E4EEF6',
  'corporate-office': '#DDE6EE',
  cafe: '#F2B77A',
};

/** Horizon as a fraction of height at zero tilt. */
export const SCENE_HORIZON: Record<SceneKind, number> = {
  'studio-white': 0.64,
  'seamless-monochrome': 0.64,
  'minimalist-podium': 0.72,
  'natural-outdoor': 0.6,
  'aesthetic-indoor': 0.62,
  'natural-outdoor-environment': 0.58,
  'corporate-office': 0.74,
  cafe: 0.76,
};

/** The surface the subject stands on, so shadows stay on it. */
export type Ground = { kind: 'plane'; y: number } | { kind: 'ellipse'; cx: number; cy: number; rx: number; ry: number };

export function paintScene(x: Ctx, kind: SceneKind, p: SceneParams): Ground {
  const plane: Ground = { kind: 'plane', y: p.horizon };
  switch (kind) {
    case 'studio-white':
      sweep(x, p, '#F3F3EF', '#E2E1DB', 0.4);
      return plane;
    case 'seamless-monochrome':
      sweep(x, p, shade(p.color, 0.1), shade(p.color, -0.12), 0.25);
      return plane;
    case 'minimalist-podium':
      return podium(x, p);
    case 'natural-outdoor':
      outdoorClose(x, p);
      return plane;
    case 'aesthetic-indoor':
      indoor(x, p);
      return plane;
    case 'natural-outdoor-environment':
      outdoorWide(x, p);
      return plane;
    case 'corporate-office':
      office(x, p);
      return plane;
    case 'cafe':
      cafe(x, p);
      return plane;
  }
}

function lightPool(x: Ctx, p: SceneParams, strength: number, cx: number, cy: number): void {
  const r = Math.max(p.W, p.H) * 0.75;
  const g = x.createRadialGradient(cx, cy, 0, cx, cy, r);
  g.addColorStop(0, `rgba(255,253,248,${strength})`);
  g.addColorStop(1, 'rgba(255,253,248,0)');
  x.fillStyle = g;
  x.fillRect(0, 0, p.W, p.H);
}

function vignette(x: Ctx, p: SceneParams, strength: number): void {
  const r = Math.hypot(p.W, p.H) * 0.62;
  const g = x.createRadialGradient(p.W / 2, p.H * 0.45, r * 0.45, p.W / 2, p.H * 0.45, r);
  g.addColorStop(0, 'rgba(20,18,16,0)');
  g.addColorStop(1, `rgba(20,18,16,${strength})`);
  x.fillStyle = g;
  x.fillRect(0, 0, p.W, p.H);
}

/** Seamless paper sweep: wall curves into floor around the horizon. */
function sweep(x: Ctx, p: SceneParams, wall: string, floor: string, pool: number): void {
  const { W, H, horizon } = p;
  const h = horizon / H;
  x.fillStyle = vGradient(x, 0, H, [
    [0, shade(wall, 0.05)],
    [h - 0.16, wall],
    [h + 0.06, mix(wall, floor, 0.65)],
    [1, floor],
  ]);
  x.fillRect(0, 0, W, H);
  lightPool(x, p, pool, W * 0.5 - Math.cos(p.light) * W * 0.25 + p.parallax * 0.3, Math.min(horizon, H) * 0.45);
  vignette(x, p, 0.12);
}

function podium(x: Ctx, p: SceneParams): Ground {
  const { W, H, subject, rand } = p;
  sweep(x, p, '#DADBD3', '#C9C8BF', 0.3);

  // A second, lower plinth sits further back and moves with the camera.
  const back = blurredLayer(W, H, W * 0.006, (b) => {
    const bw = Math.max(W * 0.16, subject.w * 0.9);
    const bx = subject.x + subject.w * 0.55 + W * 0.12 + p.parallax * 0.5;
    const top = Math.min(H * 0.98, p.horizon + (subject.y - p.horizon) * 0.35);
    cylinder(b, bx, top, bw, H * 1.2, '#E6E3DC', p);
  });
  composite(x, back, W, H);

  const pw = Math.min(W * 0.84, Math.max(W * 0.3, subject.w * 1.55));
  const cx = subject.x + subject.w / 2 + (rand() - 0.5) * W * 0.01;
  const ry = cylinder(x, cx, subject.y, pw, H * 1.2, '#EEECE7', p);
  return { kind: 'ellipse', cx, cy: subject.y, rx: pw / 2, ry };
}

function cylinder(x: Ctx, cx: number, topY: number, w: number, height: number, color: string, p: SceneParams): number {
  const ry = w * (0.07 + 0.3 * Math.max(0, p.tilt) / 90);
  const left = cx - w / 2;
  const side = x.createLinearGradient(left, 0, left + w, 0);
  const lightFromLeft = Math.cos(p.light) < 0;
  side.addColorStop(0, shade(color, lightFromLeft ? 0.06 : -0.16));
  side.addColorStop(0.45, color);
  side.addColorStop(1, shade(color, lightFromLeft ? -0.18 : 0.04));
  x.fillStyle = side;
  x.beginPath();
  x.moveTo(left, topY);
  x.lineTo(left, topY + height);
  x.lineTo(left + w, topY + height);
  x.lineTo(left + w, topY);
  x.ellipse(cx, topY, w / 2, ry, 0, 0, Math.PI, false);
  x.fill();
  x.fillStyle = shade(color, 0.05);
  x.beginPath();
  x.ellipse(cx, topY, w / 2, ry, 0, 0, Math.PI * 2);
  x.fill();
  x.strokeStyle = rgba(shade(color, -0.2), 0.25);
  x.lineWidth = Math.max(1, w * 0.003);
  x.stroke();
  return ry;
}

function foliage(b: Ctx, p: SceneParams, count: number, y0: number, y1: number, sizes: [number, number], palette: string[]): void {
  const { W, rand } = p;
  for (let i = 0; i < count; i++) {
    const r = W * (sizes[0] + rand() * (sizes[1] - sizes[0]));
    const cx = -W * 0.2 + rand() * W * 1.4 + p.parallax;
    const cy = y0 + rand() * (y1 - y0);
    b.fillStyle = palette[Math.floor(rand() * palette.length)];
    b.beginPath();
    b.ellipse(cx, cy, r, r * (0.7 + rand() * 0.5), rand() * Math.PI, 0, Math.PI * 2);
    b.fill();
  }
}

function sky(x: Ctx, p: SceneParams, top: string, low: string): void {
  const { W, H } = p;
  x.fillStyle = vGradient(x, 0, Math.max(1, p.horizon), [
    [0, top],
    [1, low],
  ]);
  x.fillRect(0, 0, W, H);
}

function outdoorClose(x: Ctx, p: SceneParams): void {
  const { W, H, horizon, rand } = p;
  sky(x, p, '#9DB6C6', '#EAE3D2');
  lightPool(x, p, 0.35, W * 0.18 + p.parallax * 0.4, horizon * 0.25);
  const trees = blurredLayer(W, H, W * 0.035, (b) =>
    foliage(b, p, 70, horizon - H * 0.42, horizon + H * 0.02, [0.05, 0.16], ['#5E7454', '#7C8F63', '#44573F', '#95A274', '#B4B98A']),
  );
  composite(x, trees, W, H);
  // Weathered stone surface the product rests on.
  x.fillStyle = vGradient(x, horizon, H, [
    [0, '#CFC6B5'],
    [0.35, '#BDB3A1'],
    [1, '#8C8373'],
  ]);
  x.fillRect(0, horizon, W, H - horizon);
  const dapple = blurredLayer(W, H, W * 0.02, (b) => {
    for (let i = 0; i < 26; i++) {
      b.fillStyle = rand() > 0.5 ? 'rgba(255,246,222,0.35)' : 'rgba(40,44,30,0.22)';
      const cx = rand() * W + p.parallax * 0.2;
      const cy = horizon + rand() * (H - horizon);
      b.beginPath();
      b.ellipse(cx, cy, W * (0.03 + rand() * 0.07), W * (0.01 + rand() * 0.02), 0, 0, Math.PI * 2);
      b.fill();
    }
  });
  composite(x, dapple, W, H, 0.8);
  x.fillStyle = 'rgba(60,54,44,0.18)';
  x.fillRect(0, horizon - 1, W, Math.max(2, H * 0.003));
  vignette(x, p, 0.16);
}

function indoor(x: Ctx, p: SceneParams): void {
  const { W, H, horizon, rand } = p;
  x.fillStyle = vGradient(x, 0, H, [
    [0, '#E9E1D5'],
    [1, '#D8CDBD'],
  ]);
  x.fillRect(0, 0, W, H);
  const room = blurredLayer(W, H, W * 0.018, (b) => {
    // Window light falling across the wall.
    b.fillStyle = 'rgba(255,244,222,0.55)';
    const wx = W * 0.06 + p.parallax * 0.6;
    b.beginPath();
    b.moveTo(wx, horizon * 0.08);
    b.lineTo(wx + W * 0.26, horizon * 0.02);
    b.lineTo(wx + W * 0.36, horizon * 0.9);
    b.lineTo(wx + W * 0.1, horizon * 0.98);
    b.fill();
    // A framed print.
    const fx = W * 0.64 + p.parallax * 0.6;
    b.fillStyle = '#B5A58F';
    b.fillRect(fx, horizon * 0.2, W * 0.2, horizon * 0.34);
    b.fillStyle = '#EDE6DA';
    b.fillRect(fx + W * 0.015, horizon * 0.2 + W * 0.015, W * 0.17, horizon * 0.34 - W * 0.03);
    b.fillStyle = '#9FA89A';
    b.fillRect(fx + W * 0.04, horizon * 0.3, W * 0.12, horizon * 0.12);
    // A plant in a pot on the table.
    const px = W * 0.86 + p.parallax * 0.8;
    b.fillStyle = '#C9B8A0';
    b.fillRect(px - W * 0.05, horizon - H * 0.12, W * 0.1, H * 0.12);
    for (let i = 0; i < 26; i++) {
      b.fillStyle = ['#4F6448', '#6D8060', '#3E5038'][i % 3];
      const a = rand() * Math.PI;
      const len = H * (0.08 + rand() * 0.16);
      b.beginPath();
      b.ellipse(px + Math.cos(a) * len * 0.6, horizon - H * 0.12 - Math.sin(a) * len * 0.7, W * 0.018, len * 0.35, a - Math.PI / 2, 0, Math.PI * 2);
      b.fill();
    }
  });
  composite(x, room, W, H);
  // Oak table surface.
  x.fillStyle = vGradient(x, horizon, H, [
    [0, '#B98F66'],
    [0.5, '#9E7550'],
    [1, '#7A5638'],
  ]);
  x.fillRect(0, horizon, W, H - horizon);
  x.strokeStyle = 'rgba(70,45,25,0.08)';
  x.lineWidth = Math.max(1, H * 0.0015);
  for (let i = 0; i < 40; i++) {
    const y = horizon + rand() * (H - horizon);
    x.beginPath();
    x.moveTo(0, y);
    x.bezierCurveTo(W * 0.3, y + (rand() - 0.5) * 8, W * 0.7, y + (rand() - 0.5) * 8, W, y);
    x.stroke();
  }
  x.fillStyle = 'rgba(255,240,215,0.22)';
  x.fillRect(0, horizon, W, Math.max(2, H * 0.004));
  vignette(x, p, 0.18);
}

function hills(b: Ctx, p: SceneParams, base: number, amp: number, color: string, freq: number, phase: number): void {
  const { W, H } = p;
  b.fillStyle = color;
  b.beginPath();
  b.moveTo(0, H);
  for (let i = 0; i <= 48; i++) {
    const t = i / 48;
    const xx = t * W;
    const y = base - amp * (Math.sin(t * freq + phase + p.parallax / W) * 0.6 + Math.sin(t * freq * 2.3 + phase * 1.7) * 0.4);
    b.lineTo(xx, y);
  }
  b.lineTo(W, H);
  b.closePath();
  b.fill();
}

function outdoorWide(x: Ctx, p: SceneParams): void {
  const { W, H, horizon, rand } = p;
  sky(x, p, '#9FBBD0', '#EDE8DC');
  const clouds = blurredLayer(W, H, W * 0.03, (b) => {
    b.fillStyle = 'rgba(255,255,255,0.7)';
    for (let i = 0; i < 9; i++) {
      b.beginPath();
      b.ellipse(rand() * W + p.parallax * 0.2, rand() * horizon * 0.55, W * (0.08 + rand() * 0.14), H * 0.025, 0, 0, Math.PI * 2);
      b.fill();
    }
  });
  composite(x, clouds, W, H);
  const far = blurredLayer(W, H, W * 0.008, (b) => {
    hills(b, { ...p, parallax: p.parallax * 0.3 }, horizon - H * 0.02, H * 0.05, '#A7B6B4', 5, rand() * 6);
    hills(b, { ...p, parallax: p.parallax * 0.6 }, horizon + H * 0.01, H * 0.035, '#7F9776', 7, rand() * 6);
    foliage(b, p, 14, horizon - H * 0.04, horizon, [0.015, 0.035], ['#4E6545', '#5C7250']);
  });
  composite(x, far, W, H);
  x.fillStyle = vGradient(x, horizon, H, [
    [0, '#8FA36A'],
    [1, '#5E7845'],
  ]);
  x.fillRect(0, horizon + H * 0.01, W, H);
  x.strokeStyle = 'rgba(40,60,25,0.12)';
  x.lineWidth = Math.max(1, W * 0.0012);
  for (let i = 0; i < 260; i++) {
    const gx = rand() * W;
    const gy = horizon + H * 0.02 + rand() * (H - horizon);
    const len = H * 0.006 * (1 + ((gy - horizon) / H) * 4);
    x.beginPath();
    x.moveTo(gx, gy);
    x.lineTo(gx + (rand() - 0.5) * len, gy - len);
    x.stroke();
  }
  vignette(x, p, 0.14);
}

function office(x: Ctx, p: SceneParams): void {
  const { W, H, horizon, rand } = p;
  x.fillStyle = vGradient(x, 0, H, [
    [0, '#DCDFE1'],
    [1, '#C9CDD0'],
  ]);
  x.fillRect(0, 0, W, H);
  const room = blurredLayer(W, H, W * 0.022, (b) => {
    const wx = -W * 0.05 + p.parallax * 0.6;
    const ww = W * 0.62;
    const wy = horizon * 0.06;
    const wh = horizon * 0.8;
    b.fillStyle = '#EEF3F6';
    b.fillRect(wx, wy, ww, wh);
    // City blocks through the glass.
    for (let i = 0; i < 12; i++) {
      b.fillStyle = ['#C9D3DA', '#B7C3CC', '#D6DDE2'][i % 3];
      const bw = ww * (0.06 + rand() * 0.1);
      const bh = wh * (0.2 + rand() * 0.5);
      b.fillRect(wx + rand() * ww, wy + wh - bh, bw, bh);
    }
    b.fillStyle = '#7F878D';
    for (let i = 0; i <= 4; i++) b.fillRect(wx + (ww / 4) * i - W * 0.004, wy, W * 0.008, wh);
    b.fillRect(wx, wy + wh * 0.5, ww, W * 0.006);
    // Desk partition and a plant.
    b.fillStyle = '#B4B9BD';
    b.fillRect(0, horizon - H * 0.12, W, H * 0.12);
    foliage(b, { ...p, parallax: p.parallax * 0.8 }, 14, horizon - H * 0.3, horizon - H * 0.12, [0.02, 0.05], ['#56704F', '#6F8766']);
  });
  composite(x, room, W, H);
  x.fillStyle = '#7C8084';
  x.fillRect(0, horizon, W, H - horizon);
  lightPool(x, p, 0.25, W * 0.2 + p.parallax * 0.4, horizon * 0.4);
  vignette(x, p, 0.16);
}

function cafe(x: Ctx, p: SceneParams): void {
  const { W, H, horizon, rand } = p;
  x.fillStyle = vGradient(x, 0, H, [
    [0, '#5E4838'],
    [1, '#35281F'],
  ]);
  x.fillRect(0, 0, W, H);
  const room = blurredLayer(W, H, W * 0.014, (b) => {
    // Shelves of jars and cups behind the counter.
    for (let s = 0; s < 3; s++) {
      const sy = horizon * (0.35 + s * 0.2);
      b.fillStyle = '#2B201A';
      b.fillRect(0, sy, W, H * 0.008);
      for (let i = 0; i < 14; i++) {
        b.fillStyle = ['#8E6A4B', '#C9A27A', '#6B5040', '#D8C3A5'][Math.floor(rand() * 4)];
        const jw = W * (0.02 + rand() * 0.025);
        const jh = H * (0.03 + rand() * 0.05);
        b.fillRect(rand() * W + p.parallax * 0.7, sy - jh, jw, jh);
      }
    }
    b.fillStyle = '#2A1F18';
    b.fillRect(0, horizon - H * 0.06, W, H);
    b.fillStyle = 'rgba(214,170,120,0.35)';
    b.fillRect(0, horizon - H * 0.06, W, H * 0.006);
  });
  composite(x, room, W, H);
  const bokeh = blurredLayer(W, H, W * 0.008, (b) => {
    for (let i = 0; i < 46; i++) {
      const r = W * (0.012 + rand() * 0.04);
      b.fillStyle = rgba(['#F2C57C', '#F7DDA8', '#E8A45C'][i % 3], 0.18 + rand() * 0.4);
      b.beginPath();
      b.arc(rand() * W + p.parallax * 0.9, rand() * horizon * 0.95, r, 0, Math.PI * 2);
      b.fill();
    }
  });
  x.save();
  x.globalCompositeOperation = 'screen';
  composite(x, bokeh, W, H);
  x.restore();
  vignette(x, p, 0.3);
}
