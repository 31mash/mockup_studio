import { useCallback, useEffect, useState } from 'react';
import { AngleSheet } from './components/AngleSheet';
import { Composer, type ComposerDialog } from './components/Composer';
import { JobDetails, ProjectMenu, QueueReview, SettingsSheet, Toasts, Viewer } from './components/Panels';
import { BackgroundPicker, ModelPicker, RatioPicker, SavedPicker } from './components/Pickers';
import { Results } from './components/Results';
import { Tabs } from './components/Tabs';
import { TopBar } from './components/TopBar';
import { useApp } from './state/store';

type Open =
  | { kind: ComposerDialog | 'settings' | 'project' | 'queue'; anchor: HTMLElement | null }
  | { kind: 'viewer'; jobId: string; index: number }
  | { kind: 'details'; jobId: string }
  | null;

export function App() {
  const ready = useApp((s) => s.ready);
  const tab = useApp((s) => s.tab);
  const theme = useApp((s) => s.settings.theme);
  const [open, setOpen] = useState<Open>(null);
  const close = useCallback(() => setOpen(null), []);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'system') root.removeAttribute('data-theme');
    else root.setAttribute('data-theme', theme);
  }, [theme]);

  const is = (k: string) => open?.kind === k;
  const anchor = open && 'anchor' in open ? open.anchor : null;

  return (
    <>
      <TopBar onSettings={(a) => setOpen({ kind: 'settings', anchor: a })} onProject={(a) => setOpen({ kind: 'project', anchor: a })} />
      <Tabs />
      {ready ? (
        <main className="workspace" id="studio-panel" role="tabpanel" aria-labelledby={`tab-${tab}`}>
          <Composer key={tab} tab={tab} open={(kind, a) => setOpen({ kind, anchor: a })} />
          <Results
            tab={tab}
            onView={(jobId, index) => setOpen({ kind: 'viewer', jobId, index })}
            onDetails={(jobId) => setOpen({ kind: 'details', jobId })}
            onQueue={() => setOpen({ kind: 'queue', anchor: null })}
          />
        </main>
      ) : (
        <div className="loading" role="status">
          Setting up the studio
        </div>
      )}

      <RatioPicker tab={tab} open={is('ratio')} onClose={close} anchor={anchor} />
      <BackgroundPicker tab={tab} open={is('background')} onClose={close} anchor={anchor} />
      <AngleSheet tab={tab} open={is('angle')} onClose={close} />
      <ModelPicker open={is('model')} onClose={close} />
      <SavedPicker open={is('saved')} onClose={close} anchor={anchor} />
      <SettingsSheet open={is('settings')} onClose={close} />
      <ProjectMenu open={is('project')} onClose={close} anchor={anchor} />
      <QueueReview open={is('queue')} onClose={close} />
      <Viewer
        jobId={open?.kind === 'viewer' ? open.jobId : null}
        index={open?.kind === 'viewer' ? open.index : 0}
        onClose={close}
        onIndex={(i) => setOpen((o) => (o?.kind === 'viewer' ? { ...o, index: i } : o))}
      />
      <JobDetails jobId={open?.kind === 'details' ? open.jobId : null} onClose={close} />
      <Toasts />
    </>
  );
}
