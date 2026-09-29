import { useEffect, useState } from 'react';
import { findModel } from '../domain/models';
import { blobToCanvas, canvasToBlob } from '../engine/canvas';
import { drawStandIn } from '../engine/standins';
import { prepareSubject, type PreparedSubject } from '../engine/subject';
import { getBlob, putBlob } from '../storage/db';
import type { AssetMeta } from '../domain/studio';
import { setState } from './store';

const urls = new Map<string, string>();
const pending = new Map<string, Promise<string | undefined>>();
const subjects = new Map<string, PreparedSubject>();
const catalogBlobs = new Map<string, Blob>();

export async function addAsset(meta: AssetMeta, blob: Blob): Promise<void> {
  await putBlob(meta.id, blob);
  urls.set(meta.id, URL.createObjectURL(blob));
  setState((s) => ({ assets: { ...s.assets, [meta.id]: meta } }));
}

/** Catalog stand-ins are drawn on demand, never stored. */
async function catalogBlob(id: string): Promise<Blob | undefined> {
  const cached = catalogBlobs.get(id);
  if (cached) return cached;
  const model = findModel(id.replace(/^catalog:/, ''));
  if (!model) return undefined;
  const blob = await canvasToBlob(drawStandIn(model), 'image/png');
  catalogBlobs.set(id, blob);
  return blob;
}

export async function assetBlob(id: string): Promise<Blob | undefined> {
  if (id.startsWith('catalog:')) return catalogBlob(id);
  return getBlob(id);
}

export function assetUrl(id: string): Promise<string | undefined> {
  const hit = urls.get(id);
  if (hit) return Promise.resolve(hit);
  let p = pending.get(id);
  if (!p) {
    p = assetBlob(id).then((b) => {
      pending.delete(id);
      if (!b) return undefined;
      const u = URL.createObjectURL(b);
      urls.set(id, u);
      return u;
    });
    pending.set(id, p);
  }
  return p;
}

export function useAssetUrl(id: string | undefined): string | undefined {
  const [url, setUrl] = useState<string | undefined>(() => (id ? urls.get(id) : undefined));
  useEffect(() => {
    let live = true;
    if (!id) {
      setUrl(undefined);
      return;
    }
    const hit = urls.get(id);
    if (hit) setUrl(hit);
    else assetUrl(id).then((u) => live && setUrl(u));
    return () => {
      live = false;
    };
  }, [id]);
  return url;
}

export async function subjectFor(id: string): Promise<PreparedSubject> {
  const hit = subjects.get(id);
  if (hit) return hit;
  const blob = await assetBlob(id);
  if (!blob) throw new Error('source-missing');
  const c = await blobToCanvas(blob, 2000);
  const prepared = prepareSubject(c);
  subjects.set(id, prepared);
  return prepared;
}

export function forgetAll(): void {
  urls.forEach((u) => URL.revokeObjectURL(u));
  urls.clear();
  subjects.clear();
}
