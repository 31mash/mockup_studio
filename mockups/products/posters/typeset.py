"""Setting Comfortaa as IndiGo's poster lettering.

Comfortaa is the closest open font to IndiGo's rounded display face, but three
of its letters give it away next to the original posters, so they are redrawn
here as vector shapes that sit exactly where Comfortaa would put them:

- y: IndiGo's y is a u whose right stem runs on into the descender (Comfortaa
  draws a v-shaped y). Drawn as Comfortaa's own u, centred on the y's ink,
  plus a stem of the same weight down to the descender depth of p.
- e: IndiGo's e is an almost closed ring whose bar rises from inside the
  bowl, lower left, to the ring's upper right, leaving a small aperture under
  it (Comfortaa has a flat bar and a wide open mouth).
- l: a plain straight stem (Comfortaa's l has a hooked foot).

Glyph positions come from measure.mjs, which lays the text out in the same
Chromium and fonts that tools/raster.mjs rasterizes with, so the shapes and
the remaining Comfortaa letters line up exactly. Units are SVG user units.
"""

from __future__ import annotations

import json
import math
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
FAMILY = 'Comfortaa'
REF = 1000.0  # size the metrics are measured at
CUSTOM = set('yel')
# Extra pair spacing (em): Comfortaa's wide T overhangs a tightly set h; an
# en dash after a (u-shaped) y needs a little more room to read as spaced.
KERN = {('T', 'h'): 0.075, (' ', '–'): 0.2}


class Typesetter:
    """Collect every text run first (plan), measure them all in one browser
    session (measure), then set lines (line)."""

    def __init__(self, fill: str):
        self.fill = fill
        self.runs: dict[tuple, int] = {}
        self.glyph_keys: dict[tuple, int] = {}
        self.data = None

    # ------------------------------------------------------------ measuring
    def plan(self, segs):
        for text, weight in segs:
            self.runs.setdefault((text, weight), len(self.runs))
            for ch in set(text) | set('uplo'):
                self.glyph_keys.setdefault((ch, weight), len(self.glyph_keys))

    def measure(self):
        req = {
            'runs': [{'text': t, 'family': FAMILY, 'weight': w, 'size': REF, 'ls': 0} for (t, w) in self.runs],
            'glyphs': [{'ch': c, 'family': FAMILY, 'weight': w} for (c, w) in self.glyph_keys],
        }
        out = subprocess.run(
            ['node', os.path.join(HERE, 'measure.mjs')], input=json.dumps(req), capture_output=True, text=True, cwd=ROOT
        )
        if out.returncode:
            raise RuntimeError(out.stderr)
        self.data = json.loads(out.stdout)

    def run(self, text, weight):
        return self.data['runs'][self.runs[(text, weight)]]

    def glyph(self, ch, weight):
        return self.data['glyphs'][self.glyph_keys[(ch, weight)]]

    def stem(self, weight):
        """Stem width of the straight l at this weight (font units)."""
        a, b = self.glyph('l', weight)['rows']['mid'][0]
        return b - a

    # ------------------------------------------------------------ layout
    def layout(self, segs, size, ls, custom=CUSTOM):
        """Origins (x from the line's origin) of every character, as
        [(ch, weight, x)], plus the ink extent (left, right). A straight l
        gives back the room of Comfortaa's hooked foot: its advance becomes
        stem plus equal side bearings."""
        k = size / REF
        chars, x, shift = [], 0.0, 0.0
        for text, weight in segs:
            r = self.run(text, weight)
            for i, ch in enumerate(text):
                chars.append((ch, weight, x + r['starts'][i] * k + i * ls + shift))
                shift += KERN.get((ch, text[i + 1 : i + 2]), 0.0) * size
                if ch == 'l' and 'l' in custom:
                    g = self.glyph('l', weight)
                    a, b = g['rows']['mid'][0]
                    shift -= (g['adv'] - a - b) * k
            x += r['end'] * k + len(text) * ls
        vis = [(c, w, cx) for c, w, cx in chars if c != ' ']
        left = vis[0][2] + self.glyph(vis[0][0], vis[0][1])['l'] * k
        c, w, cx = vis[-1]
        g = self.glyph(c, w)
        right = cx + (g['rows']['mid'][0][1] if c == 'l' and 'l' in custom else g['r']) * k
        return chars, left, right

    def fit_ls(self, segs, size, width, custom=CUSTOM):
        """Letter-spacing (user units) that makes the ink exactly `width`."""
        _, l0, r0 = self.layout(segs, size, 0.0, custom)
        n = sum(len(t) for t, _ in segs) - 1
        return (width - (r0 - l0)) / n

    # ------------------------------------------------------------ drawing
    def line(self, segs, x, y, size, ls=0.0, sx=1.0, ink_left=True, custom=CUSTOM):
        """One line of text; x is the ink's left edge (or the origin when
        ink_left is False), y the baseline. sx condenses the line."""
        chars, left, _ = self.layout(segs, size, ls, custom)
        k = size / REF
        ox = x - (left * sx if ink_left else 0.0)
        out = [f'<g transform="translate({ox:.2f} {y:.2f}) scale({sx:.4f} 1)" fill="{self.fill}">']
        # Consecutive ordinary letters of one weight share a <text> element,
        # placed at the measured origin of its first letter.
        run, run_w, run_x = '', None, 0.0

        def flush():
            if run.strip():
                out.append(
                    f'<text x="{run_x:.2f}" y="0" font-family="{FAMILY}" font-weight="{run_w}" '
                    f'font-size="{size:.2f}" letter-spacing="{ls:.3f}" style="white-space:pre">{esc(run)}</text>'
                )

        for i, (ch, w, cx) in enumerate(chars):
            if ch in custom:
                flush()
                run = ''
                out.append(self.custom_glyph(ch, w, cx, k))
                continue
            if run and w == run_w:
                run += ch
            else:
                flush()
                run, run_w, run_x = ch, w, cx
            # A kerned pair moves everything after it: start a new run there.
            if i + 1 < len(chars) and (ch, chars[i + 1][0]) in KERN:
                flush()
                run = ''
        flush()
        out.append('</g>')
        return ''.join(out)

    def custom_glyph(self, ch, w, x, k):
        s = self.stem(w)
        if ch == 'l':
            g = self.glyph('l', w)
            a, b = g['rows']['mid'][0]
            return rrect(x + a * k, -g['asc'] * k, (b - a) * k, g['asc'] * k, (b - a) * k / 2)
        if ch == 'y':
            gy, gu, gp = self.glyph('y', w), self.glyph('u', w), self.glyph('p', w)
            ux = x + ((gy['l'] + gy['r']) / 2 - (gu['l'] + gu['r']) / 2) * k
            a, b = gu['rows']['mid'][-1]  # the u's right stem
            top = -gu['asc'] * 0.5 * k
            desc = rrect(ux + a * k, top, (b - a) * k, gp['desc'] * k - top, (b - a) * k / 2)
            u = f'<text x="{ux:.2f}" y="0" font-family="{FAMILY}" font-weight="{w}" font-size="{REF * k:.2f}">u</text>'
            return u + desc
        if ch == 'e':
            g = self.glyph('e', w)
            cx = x + (g['l'] + g['r']) / 2 * k
            cy = -(g['asc'] - g['desc']) / 2 * k
            rx = ((g['r'] - g['l']) / 2 - s / 2) * k
            ry = ((g['asc'] + g['desc']) / 2 - s / 2) * k

            def p(deg, f=1.0):
                a = math.radians(deg)
                return cx + f * rx * math.cos(a), cy - f * ry * math.sin(a)

            # Ring from the lower-right terminal round the bottom, left and
            # top to the upper right, then the bar down into the bowl.
            t0, t1 = -10.0, 30.0
            x0, y0 = p(t0)
            x1, y1 = p(t1)
            qx, qy = cx - 0.38 * rx, cy + 0.26 * ry
            return (
                f'<path d="M{x0:.2f} {y0:.2f} A{rx:.2f} {ry:.2f} 0 1 1 {x1:.2f} {y1:.2f} L{qx:.2f} {qy:.2f}" '
                f'fill="none" stroke="{self.fill}" stroke-width="{s * k:.2f}" stroke-linecap="round" stroke-linejoin="round"/>'
            )
        raise ValueError(ch)


def rrect(x, y, w, h, r):
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{r:.2f}"/>'


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
