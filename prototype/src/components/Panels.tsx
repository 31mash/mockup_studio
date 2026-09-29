import { ArrowLeft, ArrowRight, DownloadSimple, PaperPlaneTilt, Trash, X } from '@phosphor-icons/react';
import { useEffect, useState } from 'react';
import { describeCamera } from '../domain/camera';
import { findBackground } from '../domain/catalogs';
import { findModel } from '../domain/models';
import { engineById } from '../engine/engines';
import type { Cutout } from '../engine/subject';
import { deleteQueued, downloadResult, exportProject, removeJob, resetProject, sendQueued } from '../state/actions';
import { subjectFor, useAssetUrl } from '../state/assets';
import { dismissToast, isOnline, setState, updateSettings, useApp } from '../state/store';
import { storageEstimate } from '../storage/db';
import { angleSummary, ERROR_TEXT, formatBytes, formatTime, jobTitle, ratioLabel, slotStateLabel } from './labels';
import { Sheet } from './Sheet';

// ---------------------------------------------------------------- viewer

export function Viewer({ jobId, index, onClose, onIndex }: { jobId: string | null; index: number; onClose: () => void; onIndex: (i: number) => void }) {
  const job = useApp((s) => s.jobs.find((j) => j.snapshot.id === jobId));
  const canSave = useApp((s) => s.saveMode !== 'none');
  const ready = job?.slots.filter((s) => s.state === 'succeeded') ?? [];
  const pos = Math.max(0, ready.findIndex((s) => s.index === index));
  const slot = ready[pos];
  const url = useAssetUrl(slot?.assetId);

  useEffect(() => {
    if (!job) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' && pos < ready.length - 1) onIndex(ready[pos + 1].index);
      if (e.key === 'ArrowLeft' && pos > 0) onIndex(ready[pos - 1].index);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  return (
    <Sheet
      open={Boolean(job && slot)}
      onClose={onClose}
      title={job ? jobTitle(job) : 'Image'}
      width={1100}
      footer={
        job && slot ? (
          <>
            <span className="hint tabular grow">
              Image {slot.index + 1} of {job.slots.length}, {job.snapshot.target.width} × {job.snapshot.target.height} px
            </span>
            <button type="button" className="icon-btn" aria-label="Previous image" disabled={pos === 0} onClick={() => onIndex(ready[pos - 1].index)}>
              <ArrowLeft size={20} aria-hidden />
            </button>
            <button type="button" className="icon-btn" aria-label="Next image" disabled={pos >= ready.length - 1} onClick={() => onIndex(ready[pos + 1].index)}>
              <ArrowRight size={20} aria-hidden />
            </button>
            {canSave && (
              <>
                <button type="button" className="btn" onClick={() => void downloadResult(job, slot.index, 'png')}>
                  PNG
                </button>
                <button type="button" className="btn btn-primary" onClick={() => void downloadResult(job, slot.index, 'jpg')}>
                  <DownloadSimple size={18} aria-hidden /> Download JPEG
                </button>
              </>
            )}
          </>
        ) : undefined
      }
    >
      {url && job && <img className="viewer-img" src={url} alt={`Generated image ${slot.index + 1}: ${jobTitle(job)}`} />}
    </Sheet>
  );
}

// ---------------------------------------------------------------- details

const CUTOUT_TEXT: Record<Cutout, string> = {
  alpha: 'Transparent image, used as it is',
  keyed: 'Separated from a plain backdrop on this device',
  none: 'Not separated. The photo is placed whole',
};

export function JobDetails({ jobId, onClose }: { jobId: string | null; onClose: () => void }) {
  const job = useApp((s) => s.jobs.find((j) => j.snapshot.id === jobId));
  const source = useApp((s) => (job ? s.assets[job.snapshot.draft.source.assetId] : undefined));
  const [cutout, setCutout] = useState<Cutout | null>(null);
  const [confirm, setConfirm] = useState(false);

  useEffect(() => {
    setCutout(null);
    setConfirm(false);
    if (job) subjectFor(job.snapshot.draft.source.assetId).then((p) => setCutout(p.cutout), () => setCutout(null));
  }, [jobId]);

  if (!job) return <Sheet open={false} onClose={onClose} title="Details">{null}</Sheet>;
  const { snapshot } = job;
  const d = snapshot.draft;
  const engine = engineById(snapshot.engine.provider);
  const model = d.source.kind === 'catalog' ? findModel(d.source.modelId) : undefined;
  const rows: [string, string][] = [
    ['Runs on', engine.execution === 'cloud' ? 'Cloud (simulated)' : 'This device'],
    ['Engine', `${snapshot.engine.provider} / ${snapshot.engine.model} ${snapshot.engine.version}`],
    ['Prompt template', snapshot.promptVersion],
    ['Source', model ? `${model.label} (catalog stand-in)` : source?.name ?? 'Missing'],
    ['Subject', cutout ? CUTOUT_TEXT[cutout] : 'Checking'],
    ['Background', `${findBackground(d.tab, d.backgroundId).label}${d.backgroundId === 'seamless-monochrome' && d.monochromeColor ? `, ${d.monochromeColor}` : ''}`],
    ['Ratio', ratioLabel(d.ratio)],
    ['Output size', `${snapshot.target.width} × ${snapshot.target.height} px, ${snapshot.target.framing} framing`],
    ['Angle', describeCamera(d.camera)],
    ['Results', String(d.count)],
    ['Created', formatTime(snapshot.createdAt)],
  ];
  if (snapshot.queuedIntentId) rows.push(['Queued as', snapshot.queuedIntentId]);

  return (
    <Sheet
      open
      onClose={onClose}
      title="Job details"
      variant="side"
      width={520}
      footer={
        confirm ? (
          <>
            <span className="grow hint">Remove this job and its images from this device?</span>
            <button type="button" className="btn" onClick={() => setConfirm(false)}>
              Keep
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                removeJob(snapshot.id);
                onClose();
              }}
            >
              Remove
            </button>
          </>
        ) : (
          <button type="button" className="link grow" onClick={() => setConfirm(true)}>
            <Trash size={16} aria-hidden /> Remove from history
          </button>
        )
      }
    >
      <p className="hint">{jobTitle(job)}</p>
      <dl className="details">
        {rows.map(([k, v]) => (
          <div key={k} style={{ display: 'contents' }}>
            <dt>{k}</dt>
            <dd className="tabular">{v}</dd>
          </div>
        ))}
      </dl>
      <div className="field">
        <span className="field-label">Generation brief</span>
        <pre className="brief">{snapshot.brief}</pre>
        <p className="hint">Built from your settings and text. A real image model receives this with the source image.</p>
      </div>
      <div className="field">
        <span className="field-label">Images</span>
        <ul style={{ margin: 0, paddingLeft: '1.1rem' }}>
          {job.slots.map((s) => (
            <li key={s.index} className="tabular">
              Image {s.index + 1}: {slotStateLabel(s, snapshot.execution === 'cloud')}, attempt {s.attempt}, seed {s.seed}
              {s.errorCode ? `. ${ERROR_TEXT[s.errorCode] ?? s.errorCode}` : ''}
            </li>
          ))}
        </ul>
      </div>
    </Sheet>
  );
}

// ---------------------------------------------------------------- settings

export function SettingsSheet({ open, onClose }: { open: boolean; onClose: () => void }) {
  const settings = useApp((s) => s.settings);
  const online = useApp(isOnline);
  const browserOnline = useApp((s) => s.browserOnline);
  const storage = useApp((s) => s.storage);
  const assets = useApp((s) => s.assets);
  const [usage, setUsage] = useState<string | null>(null);

  useEffect(() => {
    if (open) storageEstimate().then((e) => setUsage(e ? `${formatBytes(e.usage)} used of ${formatBytes(e.quota)} available` : null));
  }, [open, assets]);

  return (
    <Sheet open={open} onClose={onClose} title="Settings" variant="side" width={460}>
      <div className="group" style={{ borderTop: 0, paddingTop: 0 }}>
        <span className="group-title" id="where-label">
          Where images are made
        </span>
        <div role="radiogroup" aria-labelledby="where-label" className="field">
          <label className="radio-card">
            <input type="radio" name="execution" checked={settings.execution === 'local'} onChange={() => updateSettings({ execution: 'local' })} />
            <span>
              <b>On this device</b>
              <span>Prototype sketch engine in your browser. Works offline and never uploads your photos.</span>
            </span>
          </label>
          <label className="radio-card">
            <input type="radio" name="execution" checked={settings.execution === 'cloud'} onChange={() => updateSettings({ execution: 'cloud' })} />
            <span>
              <b>Cloud (simulated)</b>
              <span>Acts like a cloud provider: upload, queue and network delays. While offline, jobs queue until you review and send them.</span>
            </span>
          </label>
        </div>
        <p className="hint">
          {online ? 'Connected.' : browserOnline ? 'Offline mode is simulated.' : 'This browser is offline.'} Changing this affects new jobs only. A local job never moves to the cloud on its own.
        </p>
      </div>

      <div className="group">
        <span className="group-title" id="theme-label">
          Appearance
        </span>
        <div className="inline-radios" role="radiogroup" aria-labelledby="theme-label">
          {(['system', 'light', 'dark'] as const).map((t) => (
            <label key={t}>
              <input type="radio" name="theme" checked={settings.theme === t} onChange={() => updateSettings({ theme: t })} />
              {t === 'system' ? 'Match system' : t === 'light' ? 'Light' : 'Dark'}
            </label>
          ))}
        </div>
      </div>

      <div className="group">
        <span className="group-title">Testing</span>
        <label className="check">
          <input type="checkbox" checked={settings.simulateOffline} onChange={(e) => updateSettings({ simulateOffline: e.target.checked })} />
          <span>Simulate offline. Cloud jobs queue instead of sending.</span>
        </label>
        <label className="check">
          <input type="checkbox" checked={settings.failOneSlot} onChange={(e) => updateSettings({ failOneSlot: e.target.checked })} />
          <span>Fail one image in each batch, to try partial results and Retry.</span>
        </label>
      </div>

      <div className="group">
        <span className="group-title">Storage</span>
        <p className="hint">
          {storage === 'ok'
            ? `Drafts, uploads and results are saved in this browser${usage ? `: ${usage}` : ''}. Browsers can clear this data, so export projects you want to keep.`
            : 'This browser is not letting the studio save. Everything works for this session only. Export the project to keep your images.'}
        </p>
        <button type="button" className="btn" style={{ alignSelf: 'flex-start' }} onClick={() => void exportProject()}>
          <DownloadSimple size={18} aria-hidden /> Export project
        </button>
      </div>
    </Sheet>
  );
}

// ---------------------------------------------------------------- project

export function ProjectMenu({ open, onClose, anchor }: { open: boolean; onClose: () => void; anchor: HTMLElement | null }) {
  const project = useApp((s) => s.project);
  const [confirm, setConfirm] = useState(false);
  useEffect(() => setConfirm(false), [open]);
  return (
    <Sheet open={open} onClose={onClose} title="Project" variant="popover" anchor={anchor} width={380}>
      <div className="field">
        <label className="field-label" htmlFor="project-name">
          Project name
        </label>
        <input
          id="project-name"
          className="text-input"
          value={project.name}
          maxLength={80}
          onChange={(e) => setState((s) => ({ project: { ...s.project, name: e.target.value, updatedAt: new Date().toISOString() } }))}
        />
        <p className="hint">Started {formatTime(project.createdAt)}. Autosaved on this device.</p>
      </div>
      <button type="button" className="btn" style={{ alignSelf: 'flex-start' }} onClick={() => void exportProject()}>
        <DownloadSimple size={18} aria-hidden /> Export project
      </button>
      {confirm ? (
        <div className="confirm" role="alert">
          <p>Delete everything in this project? Drafts, uploads, results and queued jobs are removed from this device.</p>
          <div className="drop-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                onClose();
                void resetProject();
              }}
            >
              Delete project data
            </button>
            <button type="button" className="btn" onClick={() => setConfirm(false)}>
              Keep project
            </button>
          </div>
        </div>
      ) : (
        <button type="button" className="link" style={{ alignSelf: 'flex-start' }} onClick={() => setConfirm(true)}>
          <Trash size={16} aria-hidden /> Delete project data
        </button>
      )}
    </Sheet>
  );
}

// ---------------------------------------------------------------- queue

function QueueThumb({ id }: { id: string }) {
  const url = useAssetUrl(id);
  return <div className="source-thumb" style={{ width: 64 }}>{url && <img src={url} alt="" />}</div>;
}

export function QueueReview({ open, onClose }: { open: boolean; onClose: () => void }) {
  const queue = useApp((s) => s.queue);
  const online = useApp(isOnline);
  useEffect(() => {
    if (open && queue.length === 0) onClose();
  }, [open, queue.length, onClose]);

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title="Review and send"
      width={620}
      footer={
        <>
          <span className="hint grow">{online ? 'Each job runs in the simulated cloud. No cost in this prototype.' : 'Connect to send. Nothing leaves this device until you do.'}</span>
          <button type="button" className="btn btn-primary" disabled={!online || !queue.length} onClick={() => queue.forEach((q) => sendQueued(q.id))}>
            <PaperPlaneTilt size={18} aria-hidden /> Send all
          </button>
        </>
      }
    >
      <p className="hint">These jobs were queued while offline. They keep the settings you chose; the output size is set when you send them.</p>
      <div className="field" style={{ gap: 'var(--s4)' }}>
        {queue.map((q) => (
          <div key={q.id} className="source" style={{ gridTemplateColumns: '64px minmax(0,1fr)' }}>
            <QueueThumb id={q.draft.source.assetId} />
            <div className="source-info">
              <span className="source-name">
                {q.draft.tab === 'product' ? 'Product' : 'Model'}: {findBackground(q.draft.tab, q.draft.backgroundId).label}, {ratioLabel(q.draft.ratio)}
              </span>
              <span className="hint">
                {q.draft.count === 1 ? '1 image' : `${q.draft.count} images`}, {angleSummary(q.draft.camera)}. Queued {formatTime(q.createdAt)}
              </span>
              <div className="source-actions">
                <button type="button" className="link" disabled={!online} onClick={() => sendQueued(q.id)}>
                  Send
                </button>
                <button type="button" className="link" onClick={() => deleteQueued(q.id)}>
                  Delete
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Sheet>
  );
}

// ---------------------------------------------------------------- toasts

export function Toasts() {
  const toasts = useApp((s) => s.toasts);
  return (
    <div className="toasts" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`toast${t.tone === 'error' ? ' is-error' : ''}`} role={t.tone === 'error' ? 'alert' : 'status'}>
          <p>{t.text}</p>
          <button type="button" className="icon-btn" aria-label="Dismiss" onClick={() => dismissToast(t.id)}>
            <X size={16} aria-hidden />
          </button>
        </div>
      ))}
    </div>
  );
}

