import http, { type IncomingMessage, type ServerResponse } from 'node:http';
import type { AddressInfo } from 'node:net';
import { readFileSync } from 'node:fs';
import { afterEach, describe, expect, test } from 'vitest';
import { cameraPrompt, parseParams, sniffImage } from '../../server/angles';
import { localServer, type LocalServerEnv } from '../../server/plugin';

const png = new Uint8Array(readFileSync(new URL('../fixtures/bottle-alpha.png', import.meta.url)));
const TOKEN = 'hf_testsecret0123456789';

type Middleware = (req: IncomingMessage, res: ServerResponse, next: () => void) => void;
const servers: http.Server[] = [];

/** Runs the plugin's middleware on a real HTTP server, as Vite would. */
async function start(env: LocalServerEnv): Promise<string> {
  const stack: Middleware[] = [];
  const plugin = localServer(env);
  (plugin.configureServer as (s: unknown) => void)({ middlewares: { use: (fn: Middleware) => stack.push(fn) } });
  const server = http.createServer((req, res) =>
    stack[0](req, res, () => {
      res.statusCode = 200;
      res.end('page');
    }),
  );
  servers.push(server);
  await new Promise<void>((r) => server.listen(0, '127.0.0.1', r));
  return `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
}

afterEach(async () => {
  await Promise.all(servers.splice(0).map((s) => new Promise((r) => s.close(r))));
});

const post = (base: string, query: string, headers: Record<string, string> = { 'x-mockup-studio': '1' }, body: Uint8Array<ArrayBuffer> = new Uint8Array(png)) =>
  fetch(`${base}/api/local/angles?${query}`, { method: 'POST', headers, body });

describe('request parsing', () => {
  test('fills defaults and keeps sizes on a 16 px grid', () => {
    expect(parseParams(new URLSearchParams('azimuth=90&elevation=30'))).toEqual({ azimuth: 90, elevation: 30, distance: 1, seed: 0, width: 1024, height: 1024 });
    expect(parseParams(new URLSearchParams('azimuth=0&elevation=0&width=1000&height=777')).width).toBe(992);
  });

  test('refuses out-of-range and missing values', () => {
    for (const q of ['elevation=0', 'azimuth=360&elevation=0', 'azimuth=0&elevation=90', 'azimuth=x&elevation=0', 'azimuth=0&elevation=0&width=100']) {
      expect(() => parseParams(new URLSearchParams(q)), q).toThrow();
    }
  });

  test('knows images by their bytes, not their names', () => {
    expect(sniffImage(png)).toBe('image/png');
    expect(sniffImage(new Uint8Array([0xff, 0xd8, 0xff, 0xe0]))).toBe('image/jpeg');
    expect(sniffImage(new TextEncoder().encode('RIFF....WEBPVP8 '))).toBe('image/webp');
    expect(sniffImage(new TextEncoder().encode('not an image'))).toBeNull();
  });

  test('builds the same prompt as the Space', () => {
    expect(cameraPrompt(90, 30, 1)).toBe('<sks> right side view elevated shot medium shot');
    expect(cameraPrompt(100, 50, 1.5)).toBe('<sks> right side view high-angle shot wide shot');
  });
});

describe('local server', () => {
  test('status says what is missing, and never includes the token', async () => {
    const off = await start({});
    const a = await (await fetch(`${off}/api/local/status`)).json();
    expect(a).toMatchObject({ service: 'mockup-studio-local', angles: { ready: false, provider: 'huggingface-space' } });
    expect(a.angles.reason).toMatch(/HF_TOKEN/);

    const on = await start({ HF_TOKEN: TOKEN, HF_ANGLE_SPACE: 'http://127.0.0.1:9/' });
    const text = await (await fetch(`${on}/api/local/status`)).text();
    expect(JSON.parse(text).angles.ready).toBe(true);
    expect(text).not.toContain(TOKEN);
  });

  test('generates through the provider and returns the image', async () => {
    const base = await start({ MOCKUP_ANGLES: 'mock' });
    const res = await post(base, 'azimuth=270&elevation=30&seed=7');
    expect(res.status).toBe(200);
    expect(res.headers.get('content-type')).toBe('image/png');
    expect(res.headers.get('x-angle-seed')).toBe('7');
    expect(res.headers.get('x-angle-prompt')).toBe('<sks> left side view elevated shot medium shot');
    expect(new Uint8Array(await res.arrayBuffer())).toEqual(new Uint8Array(png));
  });

  test('only the studio page on this computer may call it', async () => {
    const base = await start({ MOCKUP_ANGLES: 'mock' });
    expect((await post(base, 'azimuth=0&elevation=30', {})).status).toBe(403);
    expect((await post(base, 'azimuth=0&elevation=30', { 'x-mockup-studio': '1', origin: 'https://example.com' })).status).toBe(403);
    expect((await post(base, 'azimuth=0&elevation=30', { 'x-mockup-studio': '1', 'sec-fetch-site': 'cross-site' })).status).toBe(403);
    const rebound = await new Promise<number>((resolve) =>
      http.get(`${base}/api/local/status`, { headers: { host: 'attacker.example' } }, (r) => resolve(r.statusCode ?? 0)),
    );
    expect(rebound).toBe(403);
    expect((await post(base, 'azimuth=0&elevation=30', { 'x-mockup-studio': '1', origin: base })).status).toBe(200);
  });

  test('explains bad requests', async () => {
    const base = await start({ MOCKUP_ANGLES: 'mock' });
    expect((await post(base, 'azimuth=400&elevation=0')).status).toBe(400);
    const bad = await post(base, 'azimuth=0&elevation=30', undefined, new TextEncoder().encode('hello'));
    expect(bad.status).toBe(415);
    expect(await bad.json()).toMatchObject({ error: 'bad-request' });
    expect((await fetch(`${base}/api/local/nope`)).status).toBe(404);
    expect(await (await fetch(`${base}/other`)).text()).toBe('page');
  });

  test('reports an unreachable model as a clear error', async () => {
    const base = await start({ HF_ANGLE_SPACE: 'http://127.0.0.1:9/' });
    const res = await post(base, 'azimuth=90&elevation=0');
    expect([502, 503]).toContain(res.status);
    expect((await res.json()).error).toMatch(/unreachable|space-unavailable/);
  });

  test('without a token, the Hub Space is refused before any network call', async () => {
    const base = await start({});
    const res = await post(base, 'azimuth=90&elevation=0');
    expect(res.status).toBe(503);
    expect((await res.json()).error).toBe('no-token');
  });
});
