import { X } from '@phosphor-icons/react';
import { useEffect, useId, useLayoutEffect, useRef, type ReactNode } from 'react';

type Props = {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  /** popover: anchored beside its trigger on wide screens; side: right-hand panel. */
  variant?: 'center' | 'popover' | 'side';
  anchor?: HTMLElement | null;
  width?: number;
};

/**
 * Modal sheet on the native <dialog>: focus is contained, Escape closes, and
 * the browser returns focus to the trigger. Below 640px every variant becomes
 * a bottom sheet.
 */
export function Sheet({ open, onClose, title, children, footer, variant = 'center', anchor, width = 560 }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useLayoutEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) {
      d.showModal();
      place();
    } else if (!open && d.open) d.close();
  });

  // Re-place when the window or the sheet's own content changes size, so a
  // popover that grows (like the monochrome swatches) stays on screen.
  useEffect(() => {
    if (!open) return;
    const onResize = () => place();
    window.addEventListener('resize', onResize);
    const ro = typeof ResizeObserver !== 'undefined' && ref.current?.firstElementChild ? new ResizeObserver(onResize) : null;
    if (ro && ref.current?.firstElementChild) ro.observe(ref.current.firstElementChild);
    return () => {
      window.removeEventListener('resize', onResize);
      ro?.disconnect();
    };
  });

  function place() {
    const d = ref.current;
    if (!d) return;
    d.style.left = '';
    d.style.top = '';
    d.style.position = '';
    d.style.margin = '';
    if (window.innerWidth <= 640) return;
    if (variant === 'side') {
      d.style.margin = '0 0 0 auto';
      return;
    }
    if (variant !== 'popover' || !anchor) return;
    const r = anchor.getBoundingClientRect();
    const h = d.offsetHeight;
    const w = d.offsetWidth;
    const roomRight = window.innerWidth - r.right - 16;
    d.style.position = 'fixed';
    d.style.margin = '0';
    d.style.left = `${roomRight >= w ? r.right + 12 : Math.max(16, window.innerWidth - w - 16)}px`;
    d.style.top = `${Math.min(Math.max(16, r.top - 24), window.innerHeight - h - 16)}px`;
  }

  return (
    <dialog
      ref={ref}
      className={`sheet${variant === 'popover' ? ' is-popover' : ''}${variant === 'side' ? ' is-side' : ''}`}
      aria-labelledby={titleId}
      style={{ width }}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === ref.current) onClose();
      }}
    >
      {open && (
        <div className="sheet-inner">
          <header className="sheet-head">
            <h2 className="sheet-title" id={titleId}>
              {title}
            </h2>
            <button type="button" className="icon-btn" aria-label="Close" onClick={onClose}>
              <X size={20} aria-hidden />
            </button>
          </header>
          {children}
          {footer && <footer className="sheet-foot">{footer}</footer>}
        </div>
      )}
    </dialog>
  );
}
