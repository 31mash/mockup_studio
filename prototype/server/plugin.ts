// The studio's local server: two routes added to Vite's dev and preview
// servers, so `npm run dev` on your computer is all it takes.
//
//   GET  /api/local/status   Is the generative engine ready? No secrets.
//   POST /api/local/angles   Image body, view in the query. Returns the image.
//
// Only pages served by this same server may call it. The token is read from
// the environment (HF_TOKEN in prototype/.env.local) and stays in this process.

import type { IncomingMessage, ServerResponse } from 'node:http';
import type { Plugin } from 'vite';
import { AngleError, createProvider, parseParams, sniffImage, type AngleProvider, type ProviderEnv } from './angles.ts';

const MAX_BODY = 20 * 1024 * 1024;
const LOOPBACK = /^(localhost|127(?:\.\d{1,3}){3}|\[::1\])$/i;
const IPV4 = /^\d{1,3}(?:\.\d{1,3}){3}$/;

type Next = (err?: unknown) => void;

export type LocalServerEnv = ProviderEnv & {
  /** Extra host names allowed to call the API, comma separated (LAN use). */
  MOCKUP_ALLOWED_HOSTS?: string;
  VITE_HF_TOKEN?: string;
};

export function localServer(env: LocalServerEnv): Plugin {
  let provider: AngleProvider | null = null;
  const get = () => (provider ??= createProvider(env));
  const allowed = new Set((env.MOCKUP_ALLOWED_HOSTS ?? '').split(',').map((h) => h.trim().toLowerCase()).filter(Boolean));
  let chain: Promise<unknown> = Promise.resolve();

  function hostAllowed(host: string | undefined): boolean {
    if (!host) return false;
    const name = host.replace(/:\d+$/, '').toLowerCase();
    // IP literals can't be DNS-rebound; names must be local or listed.
    return LOOPBACK.test(name) || IPV4.test(name) || allowed.has(name);
  }

  function sameOrigin(req: IncomingMessage): boolean {
    const site = req.headers['sec-fetch-site'];
    if (site && site !== 'same-origin' && site !== 'none') return false;
    const origin = req.headers.origin;
    if (!origin) return true;
    try {
      return new URL(origin).host === req.headers.host;
    } catch {
      return false;
    }
  }

  function send(res: ServerResponse, status: number, body: unknown): void {
    res.statusCode = status;
    res.setHeader('content-type', 'application/json; charset=utf-8');
    res.setHeader('cache-control', 'no-store');
    res.end(JSON.stringify(body));
  }

  function fail(res: ServerResponse, e: unknown): void {
    const err = e instanceof AngleError ? e : new AngleError('failed', 'The local server failed.', 500);
    if (!(e instanceof AngleError)) console.error('[mockup-studio] angles:', e);
    if (!res.writableEnded && !res.destroyed) send(res, err.status, { error: err.code, message: err.message });
  }

  async function readBody(req: IncomingMessage): Promise<Buffer> {
    const chunks: Buffer[] = [];
    let size = 0;
    for await (const chunk of req) {
      size += chunk.length;
      if (size > MAX_BODY) throw new AngleError('bad-request', 'The image is larger than 20 MB.', 413);
      chunks.push(chunk as Buffer);
    }
    return Buffer.concat(chunks);
  }

  async function handle(req: IncomingMessage, res: ServerResponse, next: Next): Promise<void> {
    const url = new URL(req.url ?? '/', 'http://local');
    if (!url.pathname.startsWith('/api/local/')) return next();
    if (!hostAllowed(req.headers.host) || !sameOrigin(req)) return send(res, 403, { error: 'forbidden', message: 'Only the studio page on this computer may call the local server.' });

    if (url.pathname === '/api/local/status' && req.method === 'GET') {
      const status = await get().status();
      return send(res, 200, { service: 'mockup-studio-local', version: 1, angles: status });
    }

    if (url.pathname === '/api/local/angles' && req.method === 'POST') {
      // A custom header forces a CORS preflight, which this server never grants.
      if (req.headers['x-mockup-studio'] !== '1') return send(res, 403, { error: 'forbidden', message: 'Missing studio header.' });
      const params = parseParams(url.searchParams);
      const bytes = await readBody(req);
      const mime = sniffImage(bytes);
      if (!mime) throw new AngleError('bad-request', 'Send a PNG, JPEG or WebP image.', 415);

      const abort = new AbortController();
      res.on('close', () => {
        if (!res.writableEnded) abort.abort();
      });
      // One generation at a time; the Space queues per account anyway.
      const run = chain.then(() => (abort.signal.aborted ? Promise.reject(new AngleError('canceled', 'Canceled.', 499)) : get().generate(new Blob([new Uint8Array(bytes)], { type: mime }), params, abort.signal)));
      chain = run.catch(() => undefined);
      const out = await run;
      res.statusCode = 200;
      res.setHeader('content-type', out.mime);
      res.setHeader('cache-control', 'no-store');
      res.setHeader('x-angle-seed', String(out.seed));
      res.setHeader('x-angle-prompt', out.prompt.replace(/[^\x20-\x7e]/g, ''));
      res.end(Buffer.from(out.bytes));
      return;
    }

    send(res, 404, { error: 'not-found', message: 'Unknown local route.' });
  }

  const middleware = (req: IncomingMessage, res: ServerResponse, next: Next) => {
    handle(req, res, next).catch((e) => fail(res, e));
  };

  return {
    name: 'mockup-studio-local-server',
    configureServer(server) {
      server.middlewares.use(middleware);
      announce(env, () => get().status());
    },
    configurePreviewServer(server) {
      server.middlewares.use(middleware);
      announce(env, () => get().status());
    },
  };
}

/** One startup line about the generative engine. Never prints the token. */
function announce(env: LocalServerEnv, status: () => Promise<{ ready: boolean; account?: string; reason?: string; provider: string; space: string }>): void {
  if (process.env.VITEST) return;
  if (env.VITE_HF_TOKEN) {
    console.warn('[mockup-studio] VITE_HF_TOKEN could be built into the page. Rename it to HF_TOKEN in .env.local.');
  }
  void status().then(
    (s) =>
      console.log(
        s.ready
          ? `[mockup-studio] Generative angles ready: ${s.provider === 'mock' ? 'mock provider' : `${s.space}${s.account ? `, as ${s.account}` : ''}`}.`
          : `[mockup-studio] Generative angles off. ${s.reason ?? ''}`,
      ),
    () => undefined,
  );
}
