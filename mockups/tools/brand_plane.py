"""The dotted IndiGo plane as SVG circles in its own grid units, for the gallery mark."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brand.indigo import INDIGO_BLUE, PLANE  # noqa: E402


def plane_dots_svg(color: str = INDIGO_BLUE, r: float = 0.3) -> str:
    return ''.join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>' for x, y in PLANE)
