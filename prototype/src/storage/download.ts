/**
 * Saving files. Inside the claude.ai artifact viewer, plain download links are
 * inert, so saves go through the viewer's `downloads` capability (the viewer
 * confirms each file). Anywhere else, a normal browser download.
 */
type DownloadsNs = { save(req: { filename: string; data: Blob }): Promise<{ status: string }> };
type ClaudeWindow = Window & { claude?: { use(name: string): Promise<unknown> } };

export type SaveMode = 'browser' | 'viewer' | 'none';

let modePromise: Promise<SaveMode> | null = null;
let viewerNs: DownloadsNs | null = null;

export function saveMode(): Promise<SaveMode> {
  if (!modePromise) {
    const w = window as ClaudeWindow;
    if (!w.claude?.use) modePromise = Promise.resolve('browser');
    else
      modePromise = w.claude
        .use('downloads')
        .then((ns) => {
          viewerNs = (ns as DownloadsNs | null) ?? null;
          return viewerNs ? ('viewer' as const) : ('none' as const);
        })
        .catch(() => 'none' as const);
  }
  return modePromise;
}

export type SaveResult = 'saved' | 'declined' | 'unavailable' | 'failed';

export async function saveFile(filename: string, blob: Blob): Promise<SaveResult> {
  const mode = await saveMode();
  if (mode === 'none') return 'unavailable';
  if (mode === 'viewer' && viewerNs) {
    try {
      await viewerNs.save({ filename, data: blob });
      return 'saved';
    } catch (e) {
      const code = (e as { code?: string })?.code;
      if (code === 'declined') return 'declined';
      if (code === 'unavailable' || code === 'not_granted') return 'unavailable';
      return 'failed';
    }
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30_000);
  return 'saved';
}

export function safeName(s: string): string {
  return (
    s
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 60) || 'image'
  );
}
