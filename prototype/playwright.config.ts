import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 60_000,
  fullyParallel: false,
  reporter: 'list',
  use: { baseURL: 'http://localhost:4173', trace: 'retain-on-failure' },
  // The preview server includes the local server; the mock provider stands in
  // for Hugging Face so generative jobs run without a network or a token.
  webServer: { command: 'npx vite preview --port 4173 --strictPort', port: 4173, reuseExistingServer: true, env: { MOCKUP_ANGLES: 'mock' } },
  projects: [
    {
      name: 'desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1440, height: 900 },
        // Software WebGL, so the camera re-projection runs in headless Chromium.
        launchOptions: { args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] },
      },
    },
  ],
});
