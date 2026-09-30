import { VideoCamera } from '@phosphor-icons/react';
import { useEffect, useRef, useState, type KeyboardEvent, type PointerEvent } from 'react';
import { cameraPosition, describeCamera, isOriginal, normalizeCamera, ORIGINAL } from '../domain/camera';
import { CAMERA_PRESETS, CAMERA_RANGE } from '../domain/catalogs';
import type { CameraIntent, StudioTab } from '../domain/studio';
import { MODEL_AZIMUTHS } from '../domain/angles';
import { useAssetUrl } from '../state/assets';
import { currentEngine, updateDraft, useApp } from '../state/store';
import { Sheet } from './Sheet';

type Props = { tab: StudioTab; open: boolean; onClose: () => void };

const SIZE = 300;
const C = SIZE / 2;
const R = 112;
const rad = (d: number) => (d * Math.PI) / 180;
const VIEW = rad(32);

type Range = { min: number; max: number };

export function AngleSheet({ tab, open, onClose }: Props) {
  const saved = useApp((s) => s.drafts[tab].camera);
  const sourceId = useApp((s) => s.drafts[tab].source?.assetId);
  const engine = useApp(currentEngine);
  const [intent, setIntent] = useState<CameraIntent>(saved);

  // Each time the sheet opens, start from the draft's current camera.
  useEffect(() => {
    if (open) setIntent(saved);
  }, [open]);

  // What the current engine can do. The controls never offer more.
  const caps = engine.caps;
  const limits = caps.cameraLimits;
  // A generative engine draws new views; the sketch engine turns the photo.
  const generative = caps.camera === 'validated-view-control';
  const person = tab === 'model' && caps.turnsPeople === false;
  const rotRange: Range = person ? { min: 0, max: 0 } : limits ? { min: -limits.rotation, max: limits.rotation } : CAMERA_RANGE.rotation;
  const tiltRange: Range = person ? { min: 0, max: 0 } : limits ? { min: limits.tiltMin, max: limits.tiltMax } : CAMERA_RANGE.tilt;
  const clamp = (v: number, r: Range) => Math.min(r.max, Math.max(r.min, v));
  const presetOk = (id: string) => {
    if (!caps.supportedCameraIntents.includes(id)) return false;
    const p = CAMERA_PRESETS.find((c) => c.id === id);
    return !person || !p || (p.rotation === 0 && p.tilt === 0);
  };

  const pos = cameraPosition(intent);
  const setRelative = (patch: Partial<{ rotation: number; tilt: number; zoom: number }>) => {
    const next = { ...pos, ...patch };
    setIntent(normalizeCamera({ kind: 'relative', rotation: clamp(next.rotation, rotRange), tilt: clamp(next.tilt, tiltRange), zoom: next.zoom }));
  };

  function apply() {
    updateDraft(tab, { camera: normalizeCamera(intent) });
    onClose();
  }

  const presetIndex = intent.kind === 'preset' ? CAMERA_PRESETS.findIndex((p) => p.id === intent.name) : -1;
  const selectPreset = (i: number) => {
    if (presetOk(CAMERA_PRESETS[i].id)) setIntent({ kind: 'preset', name: CAMERA_PRESETS[i].id });
  };
  const turned = pos.rotation !== 0 || pos.tilt !== 0;

  return (
    <Sheet
      open={open}
      onClose={onClose}
      title="Camera angle"
      width={780}
      footer={
        <>
          <button type="button" className="link grow" onClick={() => setIntent(ORIGINAL)} disabled={isOriginal(intent) && intent.kind === 'preset'}>
            Reset to original
          </button>
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="button" className="btn btn-primary" onClick={apply}>
            Apply angle
          </button>
        </>
      }
    >
      <div className="angle-body">
        <Orbit intent={intent} sourceId={sourceId} onMove={setRelative} rotRange={rotRange} locked={person} steps={generative ? [...MODEL_AZIMUTHS] : undefined} />
        <div className="field" style={{ gap: 'var(--s4)' }}>
          <div className="field">
            <span className="field-label" id={`presets-${tab}`}>
              Presets
            </span>
            <div className="presets" role="radiogroup" aria-labelledby={`presets-${tab}`}>
              {CAMERA_PRESETS.map((p, i) => (
                <button
                  key={p.id}
                  type="button"
                  role="radio"
                  aria-checked={presetIndex === i}
                  disabled={!presetOk(p.id)}
                  tabIndex={presetIndex === i || (presetIndex < 0 && i === 0) ? 0 : -1}
                  className="preset"
                  onClick={() => selectPreset(i)}
                  onKeyDown={(e) => {
                    const d = { ArrowDown: 2, ArrowUp: -2, ArrowRight: 1, ArrowLeft: -1 }[e.key];
                    if (d === undefined) return;
                    e.preventDefault();
                    let n = i;
                    do n = Math.min(CAMERA_PRESETS.length - 1, Math.max(0, n + d));
                    while (!presetOk(CAMERA_PRESETS[n].id) && n > 0 && n < CAMERA_PRESETS.length - 1);
                    if (!presetOk(CAMERA_PRESETS[n].id)) return;
                    selectPreset(n);
                    e.currentTarget.parentElement?.querySelectorAll<HTMLElement>('[role="radio"]')[n]?.focus();
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>
            <p className="hint">
              {generative
                ? tab === 'model'
                  ? 'The model draws the person from the new side, in 45° steps. Angles in between snap to the nearest step.'
                  : 'The model draws views your photo does not show, in 45° steps (dots on the ring) and four heights. The studio turns the product the rest of the way in perspective.'
                : person
                  ? 'Turning a person needs a generative engine. Zoom still works here.'
                  : 'Profile and top-down views need a generative engine: a photo has no pixels for those sides.'}
            </p>
          </div>
          <div className="field">
            <span className="field-label">Custom</span>
            <Slider id={`rot-${tab}`} label="Rotation" unit="°" value={pos.rotation} range={rotRange} disabled={person} onChange={(v) => setRelative({ rotation: v })} />
            <Slider id={`tilt-${tab}`} label="Tilt" unit="°" value={pos.tilt} range={tiltRange} disabled={person} onChange={(v) => setRelative({ tilt: v })} />
            <Slider id={`zoom-${tab}`} label="Zoom" unit="" value={pos.zoom} range={CAMERA_RANGE.zoom} onChange={(v) => setRelative({ zoom: v })} />
            <p className="hint">
              {intent.kind === 'preset'
                ? `${describeCamera(intent)} asks for a view relative to the subject.`
                : person
                  ? 'Zoom moves the camera closer or further away.'
                  : `Custom values move the camera relative to your photo: up to ${rotRange.max}° either way, and tilt from ${tiltRange.min}° to ${tiltRange.max}°.`}
            </p>
          </div>
        </div>
      </div>
      {!isOriginal(intent) && (
        <p className="note is-quiet">
          {turned && generative
            ? tab === 'model'
              ? 'The model draws this view from your photo. What it cannot see, such as the back of the head or clothing, is its best guess: check the face, hands and details before you use the image. Scene, light and shadow are made on this device.'
              : 'The model draws this view from your photo. Sides it cannot see, such as the back or the base, are its best guess: check labels, text and logos before you use the image. Scene, light and shadow are made on this device.'
            : turned
            ? 'The product turns in real perspective, using your photo. Its sides take the color of its edges, and the scene, light and shadow follow the camera.'
            : 'Zoom changes the framing. Nothing is cropped.'}
        </p>
      )}
    </Sheet>
  );
}

function Slider({
  id,
  label,
  unit,
  value,
  range,
  disabled,
  onChange,
}: {
  id: string;
  label: string;
  unit: string;
  value: number;
  range: { min: number; max: number };
  disabled?: boolean;
  onChange: (v: number) => void;
}) {
  const [text, setText] = useState(String(value));
  useEffect(() => setText(String(value)), [value]);
  return (
    <div className="slider">
      <label htmlFor={id} className="field-label" style={{ fontWeight: 500 }}>
        {label}
      </label>
      <input id={id} type="range" min={range.min} max={range.max} step={1} value={value} disabled={disabled} onChange={(e) => onChange(Number(e.target.value))} />
      <input
        className="num"
        type="text"
        disabled={disabled}
        inputMode="numeric"
        aria-label={`${label} ${unit ? 'in degrees' : 'value'}`}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={() => {
          const n = parseInt(text, 10);
          if (Number.isFinite(n)) onChange(n);
          else setText(String(value));
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter') (e.target as HTMLInputElement).blur();
        }}
      />
    </div>
  );
}

function Orbit({
  intent,
  sourceId,
  onMove,
  rotRange,
  locked,
  steps,
}: {
  intent: CameraIntent;
  sourceId?: string;
  onMove: (p: { rotation: number; tilt: number }) => void;
  rotRange: Range;
  locked: boolean;
  /** Azimuths a generative engine is trained on, marked on the ring. */
  steps?: number[];
}) {
  const url = useAssetUrl(sourceId);
  const drag = useRef<{ x: number; y: number; rotation: number; tilt: number } | null>(null);
  const pos = cameraPosition(intent);
  // The guide views the orbit from slightly above, so the front camera sits
  // below the subject and a camera behind it reads as behind.
  const dist = R * (1 - pos.zoom / 160);
  const X = Math.sin(rad(pos.rotation)) * Math.cos(rad(pos.tilt));
  const Y = Math.sin(rad(pos.tilt));
  const Z = Math.cos(rad(pos.rotation)) * Math.cos(rad(pos.tilt));
  const x = C + dist * X;
  const y = C - dist * (Y * Math.cos(VIEW) - Z * Math.sin(VIEW));
  const behind = Z * Math.cos(VIEW) + Y * Math.sin(VIEW) < -0.05;

  // The stretch of orbit this engine can reach, drawn along the ring.
  const reach: string[] = [];
  for (let a = rotRange.min; rotRange.max - rotRange.min < 360 && a <= rotRange.max; a += 2.5) {
    const rx = C + R * Math.sin(rad(a));
    const ry = C + R * Math.cos(rad(a)) * Math.sin(VIEW);
    reach.push(`${rx.toFixed(1)},${ry.toFixed(1)}`);
  }

  function down(e: PointerEvent<HTMLDivElement>) {
    if (locked) return;
    drag.current = { x: e.clientX, y: e.clientY, rotation: pos.rotation, tilt: pos.tilt };
    e.currentTarget.setPointerCapture(e.pointerId);
  }
  function move(e: PointerEvent<HTMLDivElement>) {
    const d = drag.current;
    if (!d) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const k = SIZE / rect.width;
    onMove({ rotation: Math.round(d.rotation + (e.clientX - d.x) * k * 0.9), tilt: Math.round(d.tilt - (e.clientY - d.y) * k * 0.6) });
  }
  function up() {
    drag.current = null;
  }
  function key(e: KeyboardEvent<HTMLDivElement>) {
    const step = e.shiftKey ? 15 : 5;
    const map: Record<string, [number, number]> = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] };
    const m = map[e.key];
    if (!m || locked) return;
    e.preventDefault();
    onMove({ rotation: pos.rotation + m[0], tilt: pos.tilt + m[1] });
  }

  const meridians = [0, 30, 55, 75].map((a) => R * Math.cos(rad(a)));
  const parallels = [-50, -25, 25, 50];

  return (
    <div
      className="orbit"
      role="group"
      tabIndex={0}
      aria-label={`Camera position guide. Rotation ${pos.rotation} degrees, tilt ${pos.tilt} degrees. Drag, or use the arrow keys; hold Shift for bigger steps.`}
      onPointerDown={down}
      onPointerMove={move}
      onPointerUp={up}
      onPointerCancel={up}
      onKeyDown={key}
    >
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} aria-hidden>
        <circle className="orbit-rim" cx={C} cy={C} r={R} />
        {meridians.map((rx, i) => (
          <ellipse key={`m${i}`} className="orbit-line" cx={C} cy={C} rx={Math.max(0.5, rx)} ry={R} />
        ))}
        {parallels.map((lat) => {
          const cy = C - R * Math.sin(rad(lat));
          const rx = R * Math.cos(rad(lat));
          return <ellipse key={`p${lat}`} className="orbit-line" cx={C} cy={cy} rx={rx} ry={rx * 0.16} />;
        })}
        <ellipse className="orbit-ring" cx={C} cy={C} rx={R} ry={R * Math.sin(VIEW)} />
        {reach.length > 1 && <polyline className="orbit-reach" points={reach.join(' ')} />}
        {steps?.map((a) => (
          <circle key={a} className="orbit-step" cx={C + R * Math.sin(rad(a))} cy={C + R * Math.cos(rad(a)) * Math.sin(VIEW)} r={3} />
        ))}
        <line className="orbit-path" x1={C} y1={C} x2={x} y2={y} />
      </svg>
      <p className="orbit-hint">{locked ? 'People keep their photographed angle' : 'Drag to move the camera'}</p>
      <div className="orbit-subject">{url && <img src={url} alt="" />}</div>
      <div className={`orbit-cam${behind ? ' is-behind' : ''}`} style={{ left: `${(x / SIZE) * 100}%`, top: `${(y / SIZE) * 100}%` }}>
        <span className="cam-box">
          <VideoCamera size={18} aria-hidden />
        </span>
        <span>{behind ? 'Camera, behind' : 'Camera'}</span>
      </div>
    </div>
  );
}
