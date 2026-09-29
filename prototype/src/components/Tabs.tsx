import { useRef } from 'react';
import { isActive } from '../domain/generation';
import type { StudioTab } from '../domain/studio';
import { setState, useApp } from '../state/store';

const TABS: { id: StudioTab; label: string }[] = [
  { id: 'product', label: 'Product' },
  { id: 'model', label: 'Model' },
];

export function Tabs() {
  const tab = useApp((s) => s.tab);
  const jobs = useApp((s) => s.jobs);
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});

  function select(id: StudioTab, focus = false) {
    setState({ tab: id });
    if (focus) refs.current[id]?.focus();
  }

  return (
    <nav className="tabs" role="tablist" aria-label="Studio">
      {TABS.map((t, i) => {
        const busy = jobs.some((j) => j.snapshot.draft.tab === t.id && isActive(j.state));
        return (
          <button
            key={t.id}
            ref={(el) => {
              refs.current[t.id] = el;
            }}
            type="button"
            role="tab"
            id={`tab-${t.id}`}
            aria-selected={tab === t.id}
            aria-controls="studio-panel"
            aria-describedby={busy ? `busy-${t.id}` : undefined}
            tabIndex={tab === t.id ? 0 : -1}
            className="tab"
            onClick={() => select(t.id)}
            onKeyDown={(e) => {
              if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                e.preventDefault();
                select(TABS[(i + (e.key === 'ArrowRight' ? 1 : TABS.length - 1)) % TABS.length].id, true);
              }
            }}
          >
            {t.label}
            {busy && (
              <span className="tab-busy" id={`busy-${t.id}`} aria-hidden>
                Generating
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
}
