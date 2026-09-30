import { loadEnv } from 'vite';
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';
import { localServer } from './server/plugin.ts';

// One self-contained HTML file: the same build runs from disk, a static host,
// or as a published artifact, with fonts and code inlined so it works offline.
//
// `npm run dev` and `npm run preview` also start the local server
// (server/plugin.ts). It reads HF_TOKEN from .env.local for generative camera
// angles. Only VITE_ variables reach the page, so the token stays on the server.
export default defineConfig(({ mode }) => ({
  plugins: [react(), viteSingleFile(), localServer(loadEnv(mode, process.cwd(), ['HF_', 'MOCKUP_', 'VITE_HF_']))],
  build: { target: 'es2022', assetsInlineLimit: 100_000_000 },
  test: { include: ['tests/unit/**/*.test.ts'], environment: 'node' },
}));
