import { Check } from '@phosphor-icons/react';
import { useMemo, useState, type KeyboardEvent } from 'react';
import {
  AGE_GROUPS,
  BACKGROUNDS,
  DEFAULT_MONOCHROME,
  MONOCHROME_SWATCHES,
  PRESENTATIONS,
  RATIOS,
  TONES,
  type AgeGroup,
  type Presentation,
  type SceneKind,
  type Tone,
} from '../domain/catalogs';
import { resolveTarget } from '../domain/generation';
import { describeModel, filterModels, NO_FILTERS, type ModelFilters, type ModelPreset } from '../domain/models';
import type { StudioTab } from '../domain/studio';
import { setSource } from '../state/actions';
import { useAssetUrl } from '../state/assets';
import { currentEngine, getState, updateDraft, useApp } from '../state/store';
import { RatioGlyph } from './Composer';
import { sceneThumb } from './labels';
import { Sheet } from './Sheet';

type PickerProps = { tab: StudioTab; open: boolean; onClose: () => void; anchor: HTMLElement | null };

/** Arrow keys move through a radio group and select, as native radios do. */
function roving(e: KeyboardEvent<HTMLElement>, index: number, count: number, select: (i: number) => void, columns = 1): void {
  const step: Record<string, number> = { ArrowRight: 1, ArrowLeft: -1, ArrowDown: columns, ArrowUp: -columns };
  const d = step[e.key];
  if (d === undefined) return;
  e.preventDefault();
  const next = Math.min(count - 1, Math.max(0, index + d));
  select(next);
  const group = e.currentTarget.closest('[role="radiogroup"]');
  (group?.querySelectorAll<HTMLElement>('[role="radio"]')[next])?.focus();
}

function sourceDims(tab: StudioTab): { width: number; height: number } {
  const s = getState();
  const src = s.drafts[tab].source;
  if (!src) return { width: 1024, height: 1024 };
  if (src.kind === 'catalog') return { width: 900, height: 1150 };
  const a = s.assets[src.assetId];
  return a ? { width: a.width, height: a.height } : { width: 1024, height: 1024 };
}

export function RatioPicker({ tab, open, onClose, anchor }: PickerProps) {
  const ratio = useApp((s) => s.drafts[tab].ratio);
  const engine = useApp(currentEngine);
  const target = resolveTarget(ratio, sourceDims(tab), engine.caps);
  const select = (i: number) => updateDraft(tab, { ratio: RATIOS[i].id });

  return (
    <Sheet open={open} onClose={onClose} title="Aspect ratio" variant="popover" anchor={anchor} width={360}>
      <div className="ratio-grid" role="radiogroup" aria-label="Aspect ratio">
        {RATIOS.map((r, i) => (
          <button
            key={r.id}
            type="button"
            role="radio"
            aria-checked={ratio === r.id}
            tabIndex={ratio === r.id ? 0 : -1}
            className="ratio-opt"
            onClick={() => {
              select(i);
              onClose();
            }}
            onKeyDown={(e) => roving(e, i, RATIOS.length, select, 2)}
          >
            <span className="ratio-glyph-box">
              <RatioGlyph id={r.id} size={22} />
            </span>
            {r.label}
          </button>
        ))}
      </div>
      <p className="hint tabular">
        Output {target.width} × {target.height} px{ratio === 'auto' ? ', following your photo' : ''}.
        {target.framing === 'fit' ? ' Your photo is wider or taller than 21:9, so it is fitted inside that frame.' : ' Nothing is stretched or cropped.'}
      </p>
    </Sheet>
  );
}

export function BackgroundPicker({ tab, open, onClose, anchor }: PickerProps) {
  const draft = useApp((s) => s.drafts[tab]);
  const options = BACKGROUNDS[tab];
  const color = draft.monochromeColor ?? DEFAULT_MONOCHROME;
  const isMono = draft.backgroundId === 'seamless-monochrome';
  const select = (i: number) => updateDraft(tab, { backgroundId: options[i].id });

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title="Background"
      variant="popover"
      anchor={anchor}
      width={440}
      footer={
        isMono ? (
          <button type="button" className="btn btn-primary" onClick={onClose}>
            Done
          </button>
        ) : undefined
      }
    >
      <div className="bg-list" role="radiogroup" aria-label="Background">
        {options.map((b, i) => {
          const checked = draft.backgroundId === b.id;
          return (
            <button
              key={b.id}
              type="button"
              role="radio"
              aria-checked={checked}
              tabIndex={checked ? 0 : -1}
              className="bg-opt"
              onClick={() => {
                select(i);
                if (b.id !== 'seamless-monochrome') onClose();
              }}
              onKeyDown={(e) => roving(e, i, options.length, select)}
            >
              <img src={sceneThumb(b.id as SceneKind, color)} alt="" />
              <span>
                <span className="bg-opt-label">{b.label}</span>
                <br />
                <span className="bg-opt-desc">{b.description}</span>
              </span>
              {checked ? <Check size={20} aria-hidden /> : <span />}
            </button>
          );
        })}
      </div>
      {isMono && (
        <div className="field">
          <span className="field-label" id={`mono-${tab}`}>
            Color
          </span>
          <div className="swatches" role="radiogroup" aria-labelledby={`mono-${tab}`}>
            {MONOCHROME_SWATCHES.map((s, i) => (
              <button
                key={s.hex}
                type="button"
                role="radio"
                aria-checked={color === s.hex}
                aria-label={s.name}
                title={s.name}
                tabIndex={color === s.hex || (i === 0 && !MONOCHROME_SWATCHES.some((x) => x.hex === color)) ? 0 : -1}
                className="swatch"
                style={{ background: s.hex }}
                onClick={() => updateDraft(tab, { monochromeColor: s.hex })}
                onKeyDown={(e) => roving(e, i, MONOCHROME_SWATCHES.length, (n) => updateDraft(tab, { monochromeColor: MONOCHROME_SWATCHES[n].hex }))}
              />
            ))}
            <label className="visually-hidden" htmlFor={`mono-custom-${tab}`}>
              Custom color
            </label>
            <input id={`mono-custom-${tab}`} className="color-input" type="color" value={color} onChange={(e) => updateDraft(tab, { monochromeColor: e.target.value })} />
          </div>
        </div>
      )}
    </Sheet>
  );
}

function SavedThumb({ id, name }: { id: string; name: string }) {
  const url = useAssetUrl(id);
  return <span className="portrait">{url && <img src={url} alt="" />}<span className="visually-hidden">{name}</span></span>;
}

export function SavedPicker({ open, onClose, anchor }: Omit<PickerProps, 'tab'>) {
  const assets = useApp((s) => s.assets);
  const current = useApp((s) => s.drafts.product.source);
  const saved = useMemo(() => Object.values(assets).filter((a) => a.role === 'product' && a.saved).sort((a, b) => b.createdAt.localeCompare(a.createdAt)), [assets]);
  return (
    <Sheet open={open} onClose={onClose} title="Saved products" variant="popover" anchor={anchor} width={520}>
      {saved.length === 0 ? (
        <p className="hint">No saved products yet. Upload one and it appears here.</p>
      ) : (
        <div className="model-grid">
          {saved.map((a) => (
            <button
              key={a.id}
              type="button"
              className="model-card"
              aria-pressed={current?.kind === 'upload' && current.assetId === a.id}
              aria-label={`Use ${a.name}`}
              onClick={() => {
                setSource('product', { kind: 'upload', assetId: a.id });
                onClose();
              }}
            >
              <SavedThumb id={a.id} name={a.name} />
              <span className="desc" style={{ color: 'var(--ink)', fontWeight: 600 }}>
                {a.name}
              </span>
              <span className="desc tabular">
                {a.width} × {a.height}
              </span>
            </button>
          ))}
        </div>
      )}
      <p className="hint">These images stay on this device. This is not a stock photo search.</p>
    </Sheet>
  );
}

function ModelCard({ m, selected, onPick }: { m: ModelPreset; selected: boolean; onPick: () => void }) {
  const url = useAssetUrl(m.assetId);
  return (
    <button type="button" className="model-card" aria-pressed={selected} aria-label={`Select model ${m.label}`} onClick={onPick}>
      <span className="portrait">{url && <img src={url} alt="" />}</span>
      <span className="name">{m.label}</span>
      <span className="desc">{describeModel(m)}</span>
    </button>
  );
}

export function ModelPicker({ open, onClose }: Omit<PickerProps, 'tab' | 'anchor'>) {
  const [filters, setFilters] = useState<ModelFilters>(NO_FILTERS);
  const source = useApp((s) => s.drafts.model.source);
  const list = filterModels(filters);
  const toneOptions: (Tone | null)[] = [null, ...TONES.map((t) => t.id)];
  const setTone = (i: number) => setFilters((f) => ({ ...f, tone: toneOptions[i] }));
  const active = filters.tone !== null || filters.presentation !== null || filters.ageGroup !== null;

  return (
    <Sheet open={open} onClose={onClose} title="Select model" width={780}>
      <div className="filters">
        <div className="field span">
          <span className="field-label" id="tone-label">
            Skin tone
          </span>
          <div className="tones" role="radiogroup" aria-labelledby="tone-label">
            {toneOptions.map((t, i) => {
              const checked = filters.tone === t;
              const tone = t ? TONES[t - 1] : null;
              return (
                <button
                  key={t ?? 'any'}
                  type="button"
                  role="radio"
                  aria-checked={checked}
                  aria-label={tone ? tone.label : 'Any tone'}
                  title={tone ? tone.label : 'Any tone'}
                  tabIndex={checked ? 0 : -1}
                  className="tone"
                  onClick={() => setTone(i)}
                  onKeyDown={(e) => roving(e, i, toneOptions.length, setTone)}
                >
                  {tone ? <span className="sw" style={{ background: tone.hex }} aria-hidden /> : 'Any'}
                </button>
              );
            })}
          </div>
          <span className="hint">{filters.tone ? `Tone ${filters.tone}` : 'Any tone'}, ordered light to deep.</span>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="filter-presentation">
            Gender presentation
          </label>
          <select
            id="filter-presentation"
            className="select"
            value={filters.presentation ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, presentation: (e.target.value || null) as Presentation | null }))}
          >
            <option value="">Any</option>
            {PRESENTATIONS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label className="field-label" htmlFor="filter-age">
            Age group
          </label>
          <select
            id="filter-age"
            className="select"
            value={filters.ageGroup ?? ''}
            onChange={(e) => setFilters((f) => ({ ...f, ageGroup: (e.target.value || null) as AgeGroup | null }))}
          >
            <option value="">Any</option>
            {AGE_GROUPS.map((a) => (
              <option key={a.id} value={a.id}>
                {a.label}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="field-row">
        <p className="hint" aria-live="polite">
          {list.length === 1 ? '1 model' : `${list.length} models`}
        </p>
        {active && (
          <button type="button" className="link" onClick={() => setFilters(NO_FILTERS)}>
            Clear filters
          </button>
        )}
      </div>
      {list.length === 0 ? (
        <div className="empty" style={{ padding: '1rem 0' }}>
          <p style={{ color: 'var(--ink)' }}>No models match these filters.</p>
          <button type="button" className="btn" onClick={() => setFilters(NO_FILTERS)} style={{ alignSelf: 'flex-start' }}>
            Clear filters
          </button>
        </div>
      ) : (
        <div className="model-grid">
          {list.map((m) => (
            <ModelCard
              key={m.id}
              m={m}
              selected={source?.kind === 'catalog' && source.modelId === m.id}
              onPick={() => {
                setSource('model', { kind: 'catalog', modelId: m.id, assetId: m.assetId });
                onClose();
              }}
            />
          ))}
        </div>
      )}
      <p className="hint">Faceless stand-in figures hold each identity until licensed or synthetic reference photos are added.</p>
    </Sheet>
  );
}
