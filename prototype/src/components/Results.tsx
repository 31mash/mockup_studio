import { ArrowsClockwise, DownloadSimple, Info, PaperPlaneTilt, Stop, Tray } from '@phosphor-icons/react';
import { useMemo, type CSSProperties } from 'react';
import { isActive, retryableSlots } from '../domain/generation';
import type { JobRecord, Slot, StudioTab } from '../domain/studio';
import { cancelJob, checkStatus, downloadAll, downloadResult, retryFailed } from '../state/actions';
import { useAssetUrl } from '../state/assets';
import { isOnline, useApp } from '../state/store';
import { ERROR_TEXT, jobMeta, jobStateLabel, jobTitle, slotStateLabel } from './labels';

type Props = {
  tab: StudioTab;
  onView: (jobId: string, index: number) => void;
  onDetails: (jobId: string) => void;
  onQueue: () => void;
};

export function Results({ tab, onView, onDetails, onQueue }: Props) {
  const jobs = useApp((s) => s.jobs);
  const list = useMemo(() => jobs.filter((j) => j.snapshot.draft.tab === tab), [jobs, tab]);
  return (
    <section className="results" aria-labelledby="results-title">
      <div className="results-head">
        <h2 className="results-title" id="results-title">
          Results
        </h2>
        {list.length > 0 && <p className="hint">Newest first. Everything is saved on this device.</p>}
      </div>
      <QueueBar onQueue={onQueue} />
      {list.length === 0 ? (
        <Empty tab={tab} />
      ) : (
        <div className="jobs">
          {list.map((j) => (
            <JobGroup key={j.snapshot.id} job={j} onView={onView} onDetails={onDetails} />
          ))}
        </div>
      )}
    </section>
  );
}

function QueueBar({ onQueue }: { onQueue: () => void }) {
  const count = useApp((s) => s.queue.length);
  const online = useApp(isOnline);
  if (!count) return null;
  const jobs = count === 1 ? '1 job' : `${count} jobs`;
  return (
    <div className="queue-bar" role="status">
      <p>
        <Tray size={20} aria-hidden />
        {online ? `${jobs} queued for the cloud, ready to review` : `${jobs} waiting for connection`}
      </p>
      <button type="button" className={online ? 'btn btn-primary' : 'btn'} onClick={onQueue}>
        {online ? (
          <>
            <PaperPlaneTilt size={18} aria-hidden /> Review and send
          </>
        ) : (
          'View queue'
        )}
      </button>
    </div>
  );
}

function Empty({ tab }: { tab: StudioTab }) {
  return (
    <div className="empty">
      <h3>Your images will appear here.</h3>
      <p>
        {tab === 'product'
          ? 'Start with a product: upload a photo or choose a saved one, keep the defaults, and press Generate.'
          : 'Start with a subject: upload a photo of a person or select a model, then press Generate.'}
      </p>
    </div>
  );
}

function paletteStyle(palette: string[] | undefined): CSSProperties | undefined {
  if (!palette || palette.length < 3) return undefined;
  return { '--dust': palette[2], '--sand': palette[0], '--spice': palette[1], '--shadow': palette[3] ?? palette[0] } as CSSProperties;
}

function JobGroup({ job, onView, onDetails }: { job: JobRecord; onView: Props['onView']; onDetails: Props['onDetails'] }) {
  const uploading = useApp((s) => Boolean(s.uploading[job.snapshot.id]));
  const source = useApp((s) => s.assets[job.snapshot.draft.source.assetId]);
  const canSave = useApp((s) => s.saveMode !== 'none');
  const state = jobStateLabel(job, uploading);
  const retryable = retryableSlots(job.slots);
  const done = job.slots.filter((s) => s.state === 'succeeded').length;
  const n = job.slots.length;
  const cloud = job.snapshot.execution === 'cloud';
  const titleId = `job-${job.snapshot.id}`;

  return (
    <section aria-labelledby={titleId} style={paletteStyle(source?.palette)}>
      <header className="job-head">
        <div>
          <h3 className="job-title" id={titleId}>
            {jobTitle(job)}
            {job.example && <span className="tag">Example</span>}
          </h3>
          <p className="job-meta">{jobMeta(job)}</p>
        </div>
        <div className="job-actions">
          <span className={`job-state${state.alert ? ' is-alert' : ''}`} role="status">
            {state.text}
          </span>
          {isActive(job.state) && (
            <button type="button" className="link" onClick={() => cancelJob(job.snapshot.id)}>
              <Stop size={16} aria-hidden /> Cancel
            </button>
          )}
          {job.state === 'unknown' && (
            <button type="button" className="link" onClick={() => void checkStatus(job.snapshot.id)}>
              Check status
            </button>
          )}
          {retryable.length > 1 && !isActive(job.state) && (
            <button type="button" className="link" onClick={() => retryFailed(job.snapshot.id)}>
              <ArrowsClockwise size={16} aria-hidden /> Retry all failed
            </button>
          )}
          {canSave && done > 1 && !isActive(job.state) && (
            <button type="button" className="link" onClick={() => void downloadAll(job)}>
              <DownloadSimple size={16} aria-hidden /> Download all
            </button>
          )}
          <button type="button" className="link" onClick={() => onDetails(job.snapshot.id)} aria-label={`Details for ${jobTitle(job)}`}>
            <Info size={16} aria-hidden /> Details
          </button>
        </div>
      </header>
      <div className={`grid n${n}`}>
        {job.slots.map((slot) => (
          <SlotCard key={slot.index} job={job} slot={slot} cloud={cloud} canSave={canSave} onView={onView} />
        ))}
      </div>
    </section>
  );
}

function SlotCard({ job, slot, cloud, canSave, onView }: { job: JobRecord; slot: Slot; cloud: boolean; canSave: boolean; onView: Props['onView'] }) {
  const url = useAssetUrl(slot.state === 'succeeded' ? slot.assetId : undefined);
  const { width, height } = job.snapshot.target;
  const ratio = { aspectRatio: `${width} / ${height}` };
  const n = slot.index + 1;
  const working = slot.state === 'queued' || slot.state === 'running' || slot.state === 'saving';
  const label = slotStateLabel(slot, cloud);

  if (slot.state === 'succeeded') {
    return (
      <figure className="card">
        <div className="frame" style={ratio}>
          <button type="button" className="frame-btn" aria-label={`Open image ${n}`} onClick={() => onView(job.snapshot.id, slot.index)}>
            {url && <img className="reveal" src={url} alt={`Generated image ${n}: ${jobTitle(job)}`} />}
          </button>
        </div>
        <figcaption className="caption-row">
          <span className="tabular">
            {width} × {height}
          </span>
          {canSave && (
            <span className="actions">
              <button type="button" className="link" aria-label="Download image" onClick={() => void downloadResult(job, slot.index)}>
                <DownloadSimple size={16} aria-hidden /> Download
              </button>
            </span>
          )}
        </figcaption>
      </figure>
    );
  }

  return (
    <figure className="card">
      <div className={`frame${working ? ' is-working' : ''}${slot.state === 'failed' || slot.state === 'unknown' ? ' is-failed' : ''}${slot.state === 'canceled' ? ' is-canceled' : ''}`} style={ratio}>
        {working && <span className="matte" aria-hidden />}
        <p className="frame-state">
          <span>{label}</span>
          {(slot.state === 'failed' || slot.state === 'unknown') && slot.errorCode && (
            <span className="hint" style={{ fontWeight: 400 }}>
              {ERROR_TEXT[slot.errorCode] ?? 'Something went wrong.'}
            </span>
          )}
          {slot.state === 'unknown' && (
            <span className="hint" style={{ fontWeight: 400 }}>
              Use Check status before retrying, so nothing is paid for twice.
            </span>
          )}
        </p>
      </div>
      <figcaption className="caption-row">
        <span>Image {n}</span>
        {slot.state === 'failed' && (
          <span className="actions">
            <button type="button" className="link" aria-label="Retry failed image" onClick={() => retryFailed(job.snapshot.id, slot.index)}>
              <ArrowsClockwise size={16} aria-hidden /> Retry
            </button>
          </span>
        )}
      </figcaption>
    </figure>
  );
}
