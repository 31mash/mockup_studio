import { CaretDown, FolderSimple, Gear, WarningCircle } from '@phosphor-icons/react';
import { isOnline, useApp } from '../state/store';

type Props = {
  onSettings: (anchor: HTMLElement) => void;
  onProject: (anchor: HTMLElement) => void;
};

export function TopBar({ onSettings, onProject }: Props) {
  const name = useApp((s) => s.project.name);
  const execution = useApp((s) => s.settings.execution);
  const online = useApp(isOnline);
  const storage = useApp((s) => s.storage);

  const cloud = execution === 'cloud';
  const label = cloud ? (online ? 'Cloud' : 'Offline') : 'On this device';
  const full = cloud ? (online ? 'Cloud (simulated), connected' : 'Offline. Cloud jobs will queue') : `On this device${online ? '' : ', offline'}`;

  return (
    <header className="topbar">
      <h1 className="wordmark">
        <span className="visually-hidden">Future Mockup Studio</span>
        <span className="long" aria-hidden>
          Future Mockup Studio
        </span>
        <span className="short" aria-hidden>
          Mockup Studio
        </span>
      </h1>
      <span className="topbar-spacer" />
      {storage !== 'ok' && (
        <span className="chip warn-chip" role="status">
          <WarningCircle size={18} aria-hidden />
          <span className="chip-label">Not saved on this device</span>
          <span className="visually-hidden">Changes are not being saved on this device.</span>
        </span>
      )}
      <button type="button" className="chip project-btn" aria-label={`Project: ${name}`} onClick={(e) => onProject(e.currentTarget)}>
        <FolderSimple size={18} aria-hidden />
        <span>{name}</span>
        <CaretDown size={14} aria-hidden />
      </button>
      <button type="button" className="chip" aria-label={`Where images are made: ${full}. Open settings`} onClick={(e) => onSettings(e.currentTarget)}>
        <span className={`status-dot${cloud && !online ? ' is-off' : ''}`} aria-hidden />
        <span className="chip-label">{label}</span>
      </button>
      <button type="button" className="icon-btn" aria-label="Settings" onClick={(e) => onSettings(e.currentTarget)}>
        <Gear size={22} aria-hidden />
      </button>
    </header>
  );
}
