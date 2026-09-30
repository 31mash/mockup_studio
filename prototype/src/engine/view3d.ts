import { ctx2d, makeCanvas } from './canvas';

/**
 * Turns a cut-out product in real perspective. The photo stays a crisp front
 * face, and a side is extruded along its traced outline, colored from just
 * inside the edge and lit by the scene's key light. A long-lens camera orbits
 * it. This is a genuine re-projection of the photo, which is why the turn is
 * limited: past about 35 degrees the photo has no pixels for the sides a real
 * turn would reveal, and only a generative model can invent them.
 */
export const TURN_LIMITS = { rotation: 35, tiltMin: -15, tiltMax: 40 } as const;

const CARD_VERT = `
attribute vec3 aPos;
attribute vec2 aUv;
uniform mat4 uMvp;
varying vec2 vUv;
void main() {
  vUv = aUv;
  gl_Position = uMvp * vec4(aPos, 1.0);
}`;

const CARD_FRAG = `
precision mediump float;
uniform sampler2D uTex;
varying vec2 vUv;
void main() {
  vec4 c = texture2D(uTex, vUv);
  if (c.a < 0.01) discard;
  gl_FragColor = vec4(c.rgb * c.a, c.a);
}`;

const SIDE_VERT = `
attribute vec3 aPos;
attribute vec3 aColor;
attribute vec3 aNormal;
uniform mat4 uMvp;
varying vec3 vColor;
varying vec3 vNormal;
varying float vDepth;
void main() {
  vColor = aColor;
  vNormal = aNormal;
  vDepth = aPos.z;
  gl_Position = uMvp * vec4(aPos, 1.0);
}`;

const SIDE_FRAG = `
precision mediump float;
uniform vec3 uLight;
uniform float uFront;
uniform float uBack;
varying vec3 vColor;
varying vec3 vNormal;
varying float vDepth;
void main() {
  vec3 n = normalize(vNormal);
  float key = max(dot(n, uLight), 0.0);
  float depthFade = mix(0.88, 1.0, clamp((vDepth - uBack) / (uFront - uBack), 0.0, 1.0));
  float shade = (0.68 + 0.34 * key) * depthFade;
  gl_FragColor = vec4(vColor * shade, 1.0);
}`;

type GL = WebGLRenderingContext;
type Env = { canvas: HTMLCanvasElement; gl: GL; card: WebGLProgram; side: WebGLProgram };
let cached: Env | null | undefined;

function setup(): Env | null {
  if (cached !== undefined) return cached;
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl', { premultipliedAlpha: true, preserveDrawingBuffer: true, antialias: true, alpha: true }) as GL | null;
    if (!gl) return (cached = null);
    const compile = (type: number, src: string) => {
      const sh = gl.createShader(type)!;
      gl.shaderSource(sh, src);
      gl.compileShader(sh);
      if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(sh) ?? 'shader');
      return sh;
    };
    const link = (vs: string, fs: string) => {
      const prog = gl.createProgram()!;
      gl.attachShader(prog, compile(gl.VERTEX_SHADER, vs));
      gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fs));
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error('link');
      return prog;
    };
    return (cached = { canvas, gl, card: link(CARD_VERT, CARD_FRAG), side: link(SIDE_VERT, SIDE_FRAG) });
  } catch {
    return (cached = null);
  }
}

/** Whether this browser can turn products (WebGL available). */
export function canReproject(): boolean {
  return typeof document !== 'undefined' && Boolean(setup());
}

type Seg = [number, number, number, number];

/** Marching squares on a 0..1 field at the 0.5 level; returns line segments. */
function contour(f: Float32Array, w: number, h: number): Seg[] {
  const segs: Seg[] = [];
  const at = (x: number, y: number) => (x < 0 || y < 0 || x >= w || y >= h ? 0 : f[y * w + x]);
  const lerp = (a: number, b: number) => (0.5 - a) / (b - a || 1e-6);
  for (let y = -1; y < h; y++) {
    for (let x = -1; x < w; x++) {
      const tl = at(x, y);
      const tr = at(x + 1, y);
      const br = at(x + 1, y + 1);
      const bl = at(x, y + 1);
      const c = (tl >= 0.5 ? 8 : 0) | (tr >= 0.5 ? 4 : 0) | (br >= 0.5 ? 2 : 0) | (bl >= 0.5 ? 1 : 0);
      if (c === 0 || c === 15) continue;
      const top: [number, number] = [x + lerp(tl, tr), y];
      const right: [number, number] = [x + 1, y + lerp(tr, br)];
      const bottom: [number, number] = [x + lerp(bl, br), y + 1];
      const left: [number, number] = [x, y + lerp(tl, bl)];
      const add = (p: [number, number], q: [number, number]) => segs.push([p[0], p[1], q[0], q[1]]);
      switch (c) {
        case 1:
        case 14:
          add(left, bottom);
          break;
        case 2:
        case 13:
          add(bottom, right);
          break;
        case 3:
        case 12:
          add(left, right);
          break;
        case 4:
        case 11:
          add(top, right);
          break;
        case 5:
          add(left, top);
          add(bottom, right);
          break;
        case 6:
        case 9:
          add(top, bottom);
          break;
        case 7:
        case 8:
          add(left, top);
          break;
        case 10:
          add(top, right);
          add(left, bottom);
          break;
      }
    }
  }
  return segs;
}

type Mat = Float32Array;
function mul(a: Mat, b: Mat): Mat {
  const o = new Float32Array(16);
  for (let c = 0; c < 4; c++) {
    for (let r = 0; r < 4; r++) {
      let s = 0;
      for (let k = 0; k < 4; k++) s += a[k * 4 + r] * b[c * 4 + k];
      o[c * 4 + r] = s;
    }
  }
  return o;
}
function perspective(fovY: number, aspect: number, near: number, far: number): Mat {
  const f = 1 / Math.tan(fovY / 2);
  const o = new Float32Array(16);
  o[0] = f / aspect;
  o[5] = f;
  o[10] = (far + near) / (near - far);
  o[11] = -1;
  o[14] = (2 * far * near) / (near - far);
  return o;
}
function lookAt(eye: number[], at: number[], up: number[]): Mat {
  const sub = (p: number[], q: number[]) => [p[0] - q[0], p[1] - q[1], p[2] - q[2]];
  const norm = (v: number[]) => {
    const l = Math.hypot(v[0], v[1], v[2]) || 1;
    return [v[0] / l, v[1] / l, v[2] / l];
  };
  const cross = (p: number[], q: number[]) => [p[1] * q[2] - p[2] * q[1], p[2] * q[0] - p[0] * q[2], p[0] * q[1] - p[1] * q[0]];
  const z = norm(sub(eye, at));
  const x = norm(cross(up, z));
  const y = cross(z, x);
  const dot = (p: number[], q: number[]) => p[0] * q[0] + p[1] * q[1] + p[2] * q[2];
  return new Float32Array([x[0], y[0], z[0], 0, x[1], y[1], z[1], 0, x[2], y[2], z[2], 0, -dot(x, eye), -dot(y, eye), -dot(z, eye), 1]);
}

/**
 * Renders the cutout from a camera turned by `rotation` degrees around the
 * vertical axis and raised by `tilt` degrees. Returns a transparent canvas
 * trimmed to the product, or null when WebGL is unavailable.
 */
export function reproject(subject: HTMLCanvasElement, rotation: number, tilt: number, lightAngle: number): HTMLCanvasElement | null {
  const env = setup();
  if (!env) return null;
  const { gl, canvas } = env;
  const rot = Math.max(-TURN_LIMITS.rotation, Math.min(TURN_LIMITS.rotation, rotation));
  const til = Math.max(TURN_LIMITS.tiltMin, Math.min(TURN_LIMITS.tiltMax, tilt));

  const sw = subject.width;
  const sh = subject.height;
  const aspect = sw / sh;

  // Outline and edge colors from a mid-resolution copy.
  const M = 420;
  const mw = Math.max(16, Math.round(aspect >= 1 ? M : M * aspect));
  const mh = Math.max(16, Math.round(aspect >= 1 ? M / aspect : M));
  const probe = makeCanvas(mw, mh);
  const pc = ctx2d(probe, { willReadFrequently: true });
  pc.drawImage(subject, 0, 0, mw, mh);
  const pd = pc.getImageData(0, 0, mw, mh).data;
  let field = new Float32Array(mw * mh) as Float32Array;
  for (let i = 0; i < field.length; i++) field[i] = pd[i * 4 + 3] / 255;
  // A softened field traces a clean outline and gives smooth normals.
  field = boxBlur(boxBlur(field, mw, mh, 2), mw, mh, 1);
  const segs = contour(field, mw, mh);
  // Bilinear sample of the field, for sub-pixel gradients.
  const at = (x: number, y: number) => {
    const cx = Math.min(mw - 1.001, Math.max(0, x));
    const cy = Math.min(mh - 1.001, Math.max(0, y));
    const x0 = Math.floor(cx);
    const y0 = Math.floor(cy);
    const fx = cx - x0;
    const fy = cy - y0;
    const i = y0 * mw + x0;
    return (field[i] * (1 - fx) + field[i + 1] * fx) * (1 - fy) + (field[i + mw] * (1 - fx) + field[i + mw + 1] * fx) * fy;
  };
  // Inward unit direction at a point, from the field gradient over 3 pixels.
  const inward = (x: number, y: number, fallback: [number, number]): [number, number] => {
    const gx = at(x + 1.5, y) - at(x - 1.5, y);
    const gy = at(x, y + 1.5) - at(x, y - 1.5);
    const n = Math.hypot(gx, gy);
    return n < 1e-4 ? fallback : [gx / n, gy / n];
  };
  // Side colors come from a heavily blurred, alpha-weighted copy, so they
  // grade smoothly along the outline instead of striping with print detail.
  const cr = new Float32Array(mw * mh);
  const cg = new Float32Array(mw * mh);
  const cb = new Float32Array(mw * mh);
  const cw = new Float32Array(mw * mh);
  for (let i = 0; i < mw * mh; i++) {
    const a = pd[i * 4 + 3] > 200 ? 1 : 0;
    cr[i] = pd[i * 4] * a;
    cg[i] = pd[i * 4 + 1] * a;
    cb[i] = pd[i * 4 + 2] * a;
    cw[i] = a;
  }
  const rad = Math.max(2, Math.round(Math.min(mw, mh) * 0.012));
  for (const ch of [cr, cg, cb, cw]) {
    ch.set(boxBlur(ch, mw, mh, rad));
    ch.set(boxBlur(ch, mw, mh, rad));
  }
  const colorAt = (x: number, y: number): [number, number, number] => {
    const i = Math.min(mh - 1, Math.max(0, Math.round(y))) * mw + Math.min(mw - 1, Math.max(0, Math.round(x)));
    const w = cw[i];
    return w > 1e-3 ? [cr[i] / w / 255, cg[i] / w / 255, cb[i] / w / 255] : [0.5, 0.5, 0.5];
  };

  // World: height 1, width = aspect, base at y = 0, depth centered on z = 0.
  const depth = 0.34 * Math.min(aspect, 1);
  const zF = depth / 2;
  const zB = -depth / 2;
  const toX = (u: number) => (u / mw - 0.5) * aspect;
  const toY = (v: number) => 1 - v / mh;

  const sidePos: number[] = [];
  const sideCol: number[] = [];
  const sideNor: number[] = [];
  const inset = 0.6; // tuck the side just inside the photo's soft edge
  for (const [x1, y1, x2, y2] of segs) {
    const segLen = Math.hypot(x2 - x1, y2 - y1) || 1;
    const perp: [number, number] = [-(y2 - y1) / segLen, (x2 - x1) / segLen];
    const na = inward(x1, y1, perp);
    const nb = inward(x2, y2, perp);
    const ca = colorAt(x1 + na[0] * 2.5, y1 + na[1] * 2.5);
    const cbv = colorAt(x2 + nb[0] * 2.5, y2 + nb[1] * 2.5);
    const ax = toX(x1 + na[0] * inset);
    const ay = toY(y1 + na[1] * inset);
    const bx = toX(x2 + nb[0] * inset);
    const by = toY(y2 + nb[1] * inset);
    sidePos.push(ax, ay, zF, bx, by, zF, ax, ay, zB, bx, by, zF, bx, by, zB, ax, ay, zB);
    for (const c of [ca, cbv, ca, cbv, cbv, ca]) sideCol.push(c[0], c[1], c[2]);
    // Outward normals per vertex; image y points down, world y up.
    for (const n of [na, nb, na, nb, nb, na]) sideNor.push(-n[0], n[1], 0);
  }

  const outW = Math.round(sw * 1.5);
  const outH = Math.round(sh * 1.4);
  canvas.width = outW;
  canvas.height = outH;
  gl.viewport(0, 0, outW, outH);
  gl.clearColor(0, 0, 0, 0);
  gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
  gl.enable(gl.DEPTH_TEST);

  const D = 5; // long lens: gentle perspective, like product photography
  const pivot = [0, 0.5, 0];
  const r = (rot * Math.PI) / 180;
  const t = (til * Math.PI) / 180;
  const eye = [D * Math.sin(r) * Math.cos(t), 0.5 + D * Math.sin(t), D * Math.cos(r) * Math.cos(t)];
  const fov = 2 * Math.atan(1.4 / 2 / D);
  const mvp = mul(perspective(fov, outW / outH, 0.1, 50), lookAt(eye, pivot, [0, 1, 0]));

  const buffers: WebGLBuffer[] = [];
  const locs: number[] = [];
  const attr = (prog: WebGLProgram, data: Float32Array, name: string, size: number) => {
    const b = gl.createBuffer()!;
    buffers.push(b);
    gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, name);
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, size, gl.FLOAT, false, 0, 0);
    locs.push(loc);
  };
  const release = () => {
    locs.forEach((l) => gl.disableVertexAttribArray(l));
    locs.length = 0;
  };

  // Side first.
  const L = [Math.cos(lightAngle) * 0.75, 0.55, 0.6];
  const ll = Math.hypot(L[0], L[1], L[2]);
  gl.useProgram(env.side);
  attr(env.side, new Float32Array(sidePos), 'aPos', 3);
  attr(env.side, new Float32Array(sideCol), 'aColor', 3);
  attr(env.side, new Float32Array(sideNor), 'aNormal', 3);
  gl.uniformMatrix4fv(gl.getUniformLocation(env.side, 'uMvp'), false, mvp);
  gl.uniform3f(gl.getUniformLocation(env.side, 'uLight'), L[0] / ll, L[1] / ll, L[2] / ll);
  gl.uniform1f(gl.getUniformLocation(env.side, 'uFront'), zF);
  gl.uniform1f(gl.getUniformLocation(env.side, 'uBack'), zB);
  gl.drawArrays(gl.TRIANGLES, 0, sidePos.length / 3);
  release();

  // Then the photo face, nudged forward so it always wins at the shared edge.
  gl.useProgram(env.card);
  const hx = aspect / 2;
  attr(env.card, new Float32Array([-hx, 1, zF, hx, 1, zF, -hx, 0, zF, hx, 1, zF, hx, 0, zF, -hx, 0, zF]), 'aPos', 3);
  attr(env.card, new Float32Array([0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1]), 'aUv', 2);
  const tex = gl.createTexture();
  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, subject);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  gl.uniformMatrix4fv(gl.getUniformLocation(env.card, 'uMvp'), false, mvp);
  gl.uniform1i(gl.getUniformLocation(env.card, 'uTex'), 0);
  // Premultiplied "over", so the photo's soft edge blends onto the side
  // rather than punching a see-through seam.
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  gl.enable(gl.POLYGON_OFFSET_FILL);
  gl.polygonOffset(-1, -1);
  gl.drawArrays(gl.TRIANGLES, 0, 6);
  gl.disable(gl.POLYGON_OFFSET_FILL);
  gl.disable(gl.BLEND);
  release();

  const out = makeCanvas(outW, outH);
  ctx2d(out).drawImage(canvas, 0, 0);
  buffers.forEach((b) => gl.deleteBuffer(b));
  gl.deleteTexture(tex);
  return trimAlpha(out);
}

function boxBlur(src: Float32Array, W: number, H: number, r: number): Float32Array {
  const tmp = new Float32Array(W * H);
  const out = new Float32Array(W * H);
  const n = 2 * r + 1;
  for (let y = 0; y < H; y++) {
    let s = 0;
    for (let k = -r; k <= r; k++) s += src[y * W + Math.min(W - 1, Math.max(0, k))];
    for (let x = 0; x < W; x++) {
      tmp[y * W + x] = s / n;
      s += src[y * W + Math.min(W - 1, x + r + 1)] - src[y * W + Math.max(0, x - r)];
    }
  }
  for (let x = 0; x < W; x++) {
    let s = 0;
    for (let k = -r; k <= r; k++) s += tmp[Math.min(H - 1, Math.max(0, k)) * W + x];
    for (let y = 0; y < H; y++) {
      out[y * W + x] = s / n;
      s += tmp[Math.min(H - 1, y + r + 1) * W + x] - tmp[Math.max(0, y - r) * W + x];
    }
  }
  return out;
}

function trimAlpha(c: HTMLCanvasElement): HTMLCanvasElement {
  const x = ctx2d(c, { willReadFrequently: true });
  const { width: W, height: H } = c;
  const d = x.getImageData(0, 0, W, H).data;
  let minX = W;
  let minY = H;
  let maxX = -1;
  let maxY = -1;
  for (let y = 0; y < H; y++) {
    for (let px = 0; px < W; px++) {
      if (d[(y * W + px) * 4 + 3] > 8) {
        if (px < minX) minX = px;
        if (px > maxX) maxX = px;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }
    }
  }
  if (maxX < 0) return c;
  const out = makeCanvas(maxX - minX + 1, maxY - minY + 1);
  ctx2d(out).drawImage(c, minX, minY, out.width, out.height, 0, 0, out.width, out.height);
  return out;
}
