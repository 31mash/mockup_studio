import type { SceneKind } from '../domain/catalogs';
import { toneHex } from '../domain/catalogs';
import type { ModelPreset } from '../domain/models';
import { ctx2d, makeCanvas } from './canvas';
import { rng, shade } from './color';
import { paintScene, SCENE_HORIZON } from './scenes';

const DISPLAY_FONT = "'Anton', 'Oswald', Impact, sans-serif";
const BODY_FONT = "'Archivo', 'Helvetica Neue', Arial, sans-serif";

/**
 * A sample product so the studio opens in a working state. Drawn on a
 * transparent canvas, like a clean product cutout would be.
 */
export function drawSampleProduct(): HTMLCanvasElement {
  const W = 900;
  const H = 1400;
  const c = makeCanvas(W, H);
  const x = ctx2d(c);
  const cx = W / 2;

  // Amber glass body with shoulders.
  const body = new Path2D();
  const left = 250;
  const right = 650;
  const top = 560;
  const bottom = 1350;
  body.moveTo(cx - 88, 440);
  body.bezierCurveTo(cx - 90, 520, left, 500, left, top + 40);
  body.lineTo(left, bottom - 44);
  body.quadraticCurveTo(left, bottom, left + 44, bottom);
  body.lineTo(right - 44, bottom);
  body.quadraticCurveTo(right, bottom, right, bottom - 44);
  body.lineTo(right, top + 40);
  body.bezierCurveTo(right, 500, cx + 90, 520, cx + 88, 440);
  body.closePath();
  const glass = x.createLinearGradient(left, 0, right, 0);
  glass.addColorStop(0, '#4A220A');
  glass.addColorStop(0.18, '#8E4715');
  glass.addColorStop(0.42, '#B5621F');
  glass.addColorStop(0.7, '#8A4214');
  glass.addColorStop(1, '#3F1C08');
  x.fillStyle = glass;
  x.fill(body);

  // Glass highlights.
  x.save();
  x.clip(body);
  const hi = x.createLinearGradient(left + 60, 0, left + 130, 0);
  hi.addColorStop(0, 'rgba(255,236,210,0)');
  hi.addColorStop(0.5, 'rgba(255,236,210,0.42)');
  hi.addColorStop(1, 'rgba(255,236,210,0)');
  x.fillStyle = hi;
  x.fillRect(left + 60, 480, 70, 840);
  x.fillStyle = 'rgba(255,236,210,0.18)';
  x.fillRect(right - 34, 560, 10, 740);
  x.fillStyle = 'rgba(30,12,2,0.35)';
  x.fillRect(left, bottom - 40, right - left, 40);
  x.restore();

  // Label wrapped around the body.
  const lt = 790;
  const lb = 1150;
  x.fillStyle = '#F1EDE4';
  x.fillRect(left + 18, lt, right - left - 36, lb - lt);
  const wrap = x.createLinearGradient(left + 18, 0, right - 18, 0);
  wrap.addColorStop(0, 'rgba(60,40,20,0.28)');
  wrap.addColorStop(0.3, 'rgba(60,40,20,0)');
  wrap.addColorStop(0.75, 'rgba(60,40,20,0.04)');
  wrap.addColorStop(1, 'rgba(60,40,20,0.34)');
  x.fillStyle = wrap;
  x.fillRect(left + 18, lt, right - left - 36, lb - lt);
  x.fillStyle = '#25242A';
  x.textAlign = 'center';
  x.textBaseline = 'alphabetic';
  x.font = `96px ${DISPLAY_FONT}`;
  x.fillText('SAMPLE', cx, lt + 150);
  x.fillRect(cx - 90, lt + 186, 180, 3);
  x.font = `500 34px ${BODY_FONT}`;
  x.fillText('Facial oil', cx, lt + 250);
  x.font = `400 28px ${BODY_FONT}`;
  x.fillText('30 ml', cx, lt + 300);

  // Dropper collar with ribs.
  const collar = x.createLinearGradient(cx - 110, 0, cx + 110, 0);
  collar.addColorStop(0, '#111013');
  collar.addColorStop(0.35, '#3A383D');
  collar.addColorStop(1, '#0C0B0E');
  x.fillStyle = collar;
  x.beginPath();
  x.roundRect(cx - 110, 250, 220, 200, 14);
  x.fill();
  x.strokeStyle = 'rgba(255,255,255,0.07)';
  x.lineWidth = 3;
  for (let i = 0; i < 12; i++) {
    const rx = cx - 96 + i * 17.5;
    x.beginPath();
    x.moveTo(rx, 262);
    x.lineTo(rx, 438);
    x.stroke();
  }

  // Rubber bulb.
  const bulb = x.createLinearGradient(cx - 62, 0, cx + 62, 0);
  bulb.addColorStop(0, '#16151A');
  bulb.addColorStop(0.3, '#4A484F');
  bulb.addColorStop(1, '#0E0D11');
  x.fillStyle = bulb;
  x.beginPath();
  x.moveTo(cx - 60, 255);
  x.bezierCurveTo(cx - 70, 150, cx - 58, 60, cx, 56);
  x.bezierCurveTo(cx + 58, 60, cx + 70, 150, cx + 60, 255);
  x.closePath();
  x.fill();
  x.fillStyle = 'rgba(255,255,255,0.16)';
  x.beginPath();
  x.ellipse(cx - 26, 140, 10, 50, -0.08, 0, Math.PI * 2);
  x.fill();
  return c;
}

const HAIR: Record<ModelPreset['ageGroup'], string> = {
  kid: '#3A2A20',
  teen: '#2B211B',
  'young-adult': '#221B17',
  'middle-aged': '#3B3029',
  'older-adult': '#B7B2AA',
};

/**
 * Faceless stand-in figure for a catalog identity until licensed or
 * synthetic reference photos exist. Tone, age and wardrobe stay stable.
 */
export function drawStandIn(m: ModelPreset): HTMLCanvasElement {
  const W = 900;
  const H = 1150;
  const c = makeCanvas(W, H);
  const x = ctx2d(c);
  const cx = W / 2;
  const kid = m.ageGroup === 'kid';
  const teen = m.ageGroup === 'teen';
  const s = kid ? 0.78 : teen ? 0.9 : 1;
  const skin = toneHex(m.tone);
  const headRx = (kid ? 116 : 110) * (kid ? 1 : s);
  const headRy = headRx * 1.3;
  const headY = H - 700 * s - 120;
  const shoulderY = headY + headRy + 70 * s;
  const shoulderW = (m.presentation === 'male' ? 560 : 500) * s;

  // Hair behind the head for longer styles.
  if (m.presentation === 'female') {
    x.fillStyle = HAIR[m.ageGroup];
    x.beginPath();
    x.ellipse(cx, headY + headRy * 0.35, headRx * 1.22, headRy * 1.25, 0, 0, Math.PI * 2);
    x.fill();
  }

  // Torso and shoulders.
  const torso = new Path2D();
  torso.moveTo(cx - shoulderW / 2 - 30, H);
  torso.bezierCurveTo(cx - shoulderW / 2 - 20, shoulderY + 80, cx - shoulderW / 2 + 10, shoulderY, cx - 90 * s, shoulderY - 16);
  torso.lineTo(cx + 90 * s, shoulderY - 16);
  torso.bezierCurveTo(cx + shoulderW / 2 - 10, shoulderY, cx + shoulderW / 2 + 20, shoulderY + 80, cx + shoulderW / 2 + 30, H);
  torso.closePath();
  const cloth = x.createLinearGradient(cx - shoulderW / 2, 0, cx + shoulderW / 2, 0);
  cloth.addColorStop(0, shade(m.wardrobe, 0.08));
  cloth.addColorStop(0.55, m.wardrobe);
  cloth.addColorStop(1, shade(m.wardrobe, -0.28));
  x.fillStyle = cloth;
  x.fill(torso);

  // Neck.
  const neck = x.createLinearGradient(cx - 60 * s, 0, cx + 60 * s, 0);
  neck.addColorStop(0, shade(skin, -0.08));
  neck.addColorStop(1, shade(skin, -0.22));
  x.fillStyle = neck;
  x.beginPath();
  x.roundRect(cx - 46 * s, headY + headRy * 0.7, 92 * s, shoulderY - (headY + headRy * 0.7) + 10, 26);
  x.fill();
  x.fillStyle = shade(m.wardrobe, -0.12);
  x.beginPath();
  x.ellipse(cx, shoulderY - 10, 82 * s, 22 * s, 0, 0, Math.PI);
  x.fill();

  // Head.
  const head = x.createRadialGradient(cx - headRx * 0.35, headY - headRy * 0.3, headRx * 0.2, cx, headY, headRy * 1.1);
  head.addColorStop(0, shade(skin, 0.1));
  head.addColorStop(0.7, skin);
  head.addColorStop(1, shade(skin, -0.2));
  x.fillStyle = head;
  x.beginPath();
  x.ellipse(cx, headY, headRx, headRy, 0, 0, Math.PI * 2);
  x.fill();

  // Hair on top.
  x.fillStyle = HAIR[m.ageGroup];
  x.beginPath();
  x.ellipse(cx, headY - headRy * 0.42, headRx * 1.04, headRy * 0.62, 0, Math.PI, Math.PI * 2);
  x.fill();
  x.beginPath();
  x.ellipse(cx, headY - headRy * 0.42, headRx * 1.04, headRy * (m.presentation === 'female' ? 0.3 : 0.16), 0, 0, Math.PI);
  x.fill();
  return c;
}

/** Scene-only preview for the background picker. */
export function drawSceneThumb(kind: SceneKind, color: string, size = 176): HTMLCanvasElement {
  const c = makeCanvas(size, size);
  const x = ctx2d(c);
  const horizon = size * SCENE_HORIZON[kind];
  paintScene(x, kind, {
    W: size,
    H: size,
    horizon,
    parallax: 0,
    light: -2.5,
    color,
    rand: rng(7),
    subject: { x: size * 0.36, y: horizon + (size - horizon) * 0.4, w: size * 0.28, h: size * 0.4 },
    tilt: 0,
  });
  return c;
}
