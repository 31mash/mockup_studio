import { Camera, Images, UploadSimple, UserFocus, WarningCircle } from '@phosphor-icons/react';
import { useMemo, useRef, useState, type ReactNode } from 'react';
import { describeCamera, shortCamera } from '../domain/camera';
import { DEFAULT_MONOCHROME, findBackground, PROMPT_EXAMPLES, PROMPT_LIMIT, RATIOS, type SceneKind } from '../domain/catalogs';
import { generateLabel } from '../domain/generation';
import { describeModel, findModel } from '../domain/models';
import { detectConflicts } from '../domain/prompt';
import { OUTPUT_COUNTS, type OutputCount, type StudioTab } from '../domain/studio';
import { engineFor } from '../engine/engines';
import { acknowledgeRights, generate, issuesFor, setSource, uploadSource } from '../state/actions';
import { useAssetUrl } from '../state/assets';
import { isOnline, updateDraft, useApp } from '../state/store';
import { ratioLabel, sceneThumb } from './labels';

export type ComposerDialog = 'ratio' | 'background' | 'angle' | 'model' | 'saved';

type Props = { tab: StudioTab; open: (d: ComposerDialog, anchor: HTMLElement) => void };

export function Composer({ tab, open }: Props) {
  return (
    <section className="composer" aria-label="Create">
      {tab === 'product' ? <ProductSource open={open} /> : <ModelSource open={open} />}
      <PromptField tab={tab} />
      <SettingsRows tab={tab} open={open} />
      <CountField tab={tab} />
      <GenerateBar tab={tab} />
    </section>
  );
}

function FilePicker({ label, onFile, children }: { label: string; onFile: (f: File) => void; children: (pick: () => void) => ReactNode }) {
  const ref = useRef<HTMLInputElement>(null);
  return (
    <>
      <input
        ref={ref}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="visually-hidden"
        aria-label={label}
        tabIndex={-1}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onFile(f);
          e.target.value = '';
        }}
      />
      {children(() => ref.current?.click())}
    </>
  );
}

function DropZone({ tab, title, hint, children }: { tab: StudioTab; title: string; hint: string; children: ReactNode }) {
  const [over, setOver] = useState(false);
  return (
    <div
      className={`drop${over ? ' is-over' : ''}`}
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f) void uploadSource(tab, f);
      }}
    >
      <p className="drop-title">{title}</p>
      <p className="hint">{hint}</p>
      <div className="drop-actions">{children}</div>
    </div>
  );
}

function SourceCard({ assetId, name, detail, actions }: { assetId: string; name: string; detail: string; actions: ReactNode }) {
  const url = useAssetUrl(assetId);
  return (
    <div className="source">
      <div className="source-thumb">{url ? <img src={url} alt={`Source: ${name}`} /> : null}</div>
      <div className="source-info">
        <span className="source-name" title={name}>
          {name}
        </span>
        <span className="hint tabular">{detail}</span>
      </div>
      <div className="source-actions">{actions}</div>
    </div>
  );
}

function ProductSource({ open }: { open: Props['open'] }) {
  const source = useApp((s) => s.drafts.product.source);
  const assets = useApp((s) => s.assets);
  const meta = source?.kind === 'upload' ? assets[source.assetId] : undefined;
  const upload = (f: File) => void uploadSource('product', f);

  return (
    <div className="field">
      <span className="field-label" id="product-source-label">
        Product
      </span>
      <FilePicker label="Upload product photo" onFile={upload}>
        {(pick) =>
          meta ? (
            <SourceCard
              assetId={meta.id}
              name={meta.name}
              detail={`${meta.width} × ${meta.height} px${meta.origin === 'sample' ? ', sample' : ''}`}
              actions={
                <>
                  <button type="button" className="link" onClick={pick}>
                    Replace
                  </button>
                  <button type="button" className="link" onClick={(e) => open('saved', e.currentTarget)}>
                    Choose saved
                  </button>
                  <button type="button" className="link" onClick={() => setSource('product', null)}>
                    Remove
                  </button>
                </>
              }
            />
          ) : (
            <DropZone tab="product" title="Drop a product photo here" hint="JPEG, PNG or WebP, up to 20 MB. A plain or transparent background works best.">
              <button type="button" className="btn" onClick={pick}>
                <UploadSimple size={18} aria-hidden /> Upload photo
              </button>
              <button type="button" className="link" onClick={(e) => open('saved', e.currentTarget)}>
                <Images size={18} aria-hidden /> Choose saved
              </button>
            </DropZone>
          )
        }
      </FilePicker>
    </div>
  );
}

function ModelSource({ open }: { open: Props['open'] }) {
  const source = useApp((s) => s.drafts.model.source);
  const assets = useApp((s) => s.assets);
  const upload = (f: File) => void uploadSource('model', f);
  const model = source?.kind === 'catalog' ? findModel(source.modelId) : undefined;
  const meta = source?.kind === 'upload' ? assets[source.assetId] : undefined;

  return (
    <div className="field">
      <span className="field-label">Model</span>
      <FilePicker label="Upload a photo of a person" onFile={upload}>
        {(pick) => {
          if (model && source)
            return (
              <SourceCard
                assetId={source.assetId}
                name={model.label}
                detail={describeModel(model)}
                actions={
                  <>
                    <button type="button" className="link" onClick={(e) => open('model', e.currentTarget)}>
                      Change model
                    </button>
                    <button type="button" className="link" onClick={pick}>
                      Upload instead
                    </button>
                    <button type="button" className="link" onClick={() => setSource('model', null)}>
                      Remove
                    </button>
                  </>
                }
              />
            );
          if (meta)
            return (
              <>
                <SourceCard
                  assetId={meta.id}
                  name={meta.name}
                  detail={`${meta.width} × ${meta.height} px`}
                  actions={
                    <>
                      <button type="button" className="link" onClick={pick}>
                        Replace
                      </button>
                      <button type="button" className="link" onClick={(e) => open('model', e.currentTarget)}>
                        Select model instead
                      </button>
                      <button type="button" className="link" onClick={() => setSource('model', null)}>
                        Remove
                      </button>
                    </>
                  }
                />
                <label className="check">
                  <input type="checkbox" checked={Boolean(meta.rightsAcknowledged)} onChange={(e) => acknowledgeRights(meta.id, e.target.checked)} />
                  <span>I have the rights and this person's consent to use this photo.</span>
                </label>
              </>
            );
          return (
            <>
              <div className="split-choice">
                <button type="button" className="btn" onClick={pick}>
                  <UploadSimple size={18} aria-hidden /> Upload image
                </button>
                <button type="button" className="btn" onClick={(e) => open('model', e.currentTarget)}>
                  <UserFocus size={18} aria-hidden /> Select model
                </button>
              </div>
              <p className="hint">Upload a photo of a person, or pick someone from the model catalog.</p>
            </>
          );
        }}
      </FilePicker>
    </div>
  );
}

function PromptField({ tab }: { tab: StudioTab }) {
  const draft = useApp((s) => s.drafts[tab]);
  const conflicts = useMemo(() => detectConflicts(draft), [draft]);
  const over = draft.prompt.length > PROMPT_LIMIT;
  const id = `prompt-${tab}`;
  return (
    <div className="field">
      <div className="field-row">
        <label className="field-label" htmlFor={id}>
          Describe your image
        </label>
        <span className="hint tabular" aria-live="polite">
          {draft.prompt.length.toLocaleString()} / {PROMPT_LIMIT.toLocaleString()}
        </span>
      </div>
      <textarea
        id={id}
        className="textarea"
        value={draft.prompt}
        placeholder={`Optional. For example: ${PROMPT_EXAMPLES[tab]}`}
        aria-describedby={`${id}-hint`}
        aria-invalid={over}
        onChange={(e) => updateDraft(tab, { prompt: e.target.value })}
      />
      <p className="hint" id={`${id}-hint`}>
        Optional. Ratio, background and angle come from the settings below.
      </p>
      {over && <p className="note">Shorten the description to 2,000 characters or fewer.</p>}
      {conflicts.map((c) => (
        <p key={c.control} className="note is-quiet">
          {c.message}
        </p>
      ))}
    </div>
  );
}

function RatioGlyph({ id, size = 20 }: { id: string; size?: number }) {
  const r = RATIOS.find((x) => x.id === id);
  if (!r || id === 'auto') return <span className="ratio-glyph is-auto" style={{ width: size * 0.8, height: size * 0.8 }} aria-hidden />;
  const k = size / Math.max(r.w, r.h);
  return <span className="ratio-glyph" style={{ width: Math.max(6, r.w * k), height: Math.max(6, r.h * k) }} aria-hidden />;
}
export { RatioGlyph };

function SettingsRows({ tab, open }: Props) {
  const draft = useApp((s) => s.drafts[tab]);
  const bg = findBackground(tab, draft.backgroundId);
  const color = draft.monochromeColor ?? DEFAULT_MONOCHROME;
  return (
    <div className="field">
      <span className="field-label" id={`settings-${tab}`}>
        Settings
      </span>
      <div className="settings-list" role="group" aria-labelledby={`settings-${tab}`}>
        <button type="button" className="setting" aria-haspopup="dialog" aria-label={`Ratio: ${ratioLabel(draft.ratio)}. Change ratio`} onClick={(e) => open('ratio', e.currentTarget)}>
          <span className="setting-icon">
            <RatioGlyph id={draft.ratio} />
          </span>
          <span className="setting-name">Ratio</span>
          <span className="setting-value">{ratioLabel(draft.ratio)}</span>
          <span className="hint">Change</span>
        </button>
        <button type="button" className="setting" aria-haspopup="dialog" aria-label={`Background: ${bg.label}. Change background`} onClick={(e) => open('background', e.currentTarget)}>
          <span className="setting-icon">
            <img src={sceneThumb(bg.id as SceneKind, color)} alt="" />
          </span>
          <span className="setting-name">Background</span>
          <span className="setting-value">{bg.label}</span>
          <span className="hint">Change</span>
        </button>
        <button type="button" className="setting" aria-haspopup="dialog" aria-label={`Angle: ${describeCamera(draft.camera)}. Change angle`} onClick={(e) => open('angle', e.currentTarget)}>
          <span className="setting-icon">
            <Camera size={22} aria-hidden />
          </span>
          <span className="setting-name">Angle</span>
          <span className="setting-value">{shortCamera(draft.camera)}</span>
          <span className="hint">Change</span>
        </button>
      </div>
    </div>
  );
}

function CountField({ tab }: { tab: StudioTab }) {
  const count = useApp((s) => s.drafts[tab].count);
  return (
    <fieldset className="field" style={{ border: 0, margin: 0, padding: 0 }}>
      <legend className="field-label" style={{ marginBottom: 8 }}>
        Number of images
      </legend>
      <div className="segmented">
        {OUTPUT_COUNTS.map((n) => (
          <label key={n}>
            <input
              type="radio"
              name={`count-${tab}`}
              value={n}
              checked={count === n}
              aria-label={n === 1 ? '1 result' : `${n} results`}
              onChange={() => updateDraft(tab, { count: n as OutputCount })}
            />
            <span aria-hidden>{n}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function GenerateBar({ tab }: { tab: StudioTab }) {
  const draft = useApp((s) => s.drafts[tab]);
  const assets = useApp((s) => s.assets);
  const execution = useApp((s) => s.settings.execution);
  const online = useApp(isOnline);
  const [busy, setBusy] = useState(false);
  // Recompute whenever inputs that affect validation change.
  const issues = useMemo(() => issuesFor(tab), [tab, draft, assets, execution]);
  const engine = engineFor(execution);
  const willQueue = engine.execution === 'cloud' && !online;
  const disabled = issues.length > 0 || busy;
  const label = willQueue ? 'Queue for online' : generateLabel(draft.count);

  async function submit() {
    if (disabled) return;
    setBusy(true);
    try {
      await generate(tab);
    } finally {
      setTimeout(() => setBusy(false), 600);
    }
  }

  return (
    <div className="generate">
      <button type="button" className="btn btn-primary btn-block" disabled={disabled} aria-describedby={`gen-${tab}-status`} onClick={submit}>
        {label}
      </button>
      <div id={`gen-${tab}-status`}>
        {issues.length > 0 ? (
          <p className="note">
            <WarningCircle size={18} aria-hidden style={{ flex: 'none', marginTop: 2 }} />
            <span>{issues[0].message}</span>
          </p>
        ) : (
          <p className="hint">{willQueue ? "You're offline. Queued jobs wait until you review and send them." : engine.runsOn}</p>
        )}
      </div>
    </div>
  );
}
