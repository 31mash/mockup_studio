import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';

// One self-contained HTML file: the same build runs from disk, a static host,
// or as a published artifact, with fonts and code inlined so it works offline.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  build: { target: 'es2022', assetsInlineLimit: 100_000_000 },
  test: { include: ['tests/unit/**/*.test.ts'], environment: 'node' },
});
