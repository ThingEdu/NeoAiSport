"""Vẽ mascot con Dế (bám sát logo Dế Foundation) + nạp logo. Cần pygame."""
from __future__ import annotations

import math
import os

import pygame

from neoaisport import config as C

ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

FONT_STACK = "arialroundedmtbold,avenirnextrounded,avenirnext,nunito,inter,helveticaneue,arial"


def font(size: int, bold: bool = True):
    return pygame.font.SysFont(FONT_STACK, size, bold=bold)


def load_logo():
    try:
        return pygame.image.load(os.path.join(ASSET_DIR, "logo_de.png")).convert_alpha()
    except Exception:
        return None


def scale_to(img, w=None, h=None):
    iw, ih = img.get_size()
    if w is None:
        w = int(iw * h / ih)
    if h is None:
        h = int(ih * w / iw)
    return pygame.transform.smoothscale(img, (w, h))


def _smooth(surf, color, pts, width):
    """Đường cong mượt (Catmull-Rom) cho râu con Dế."""
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = pts[max(i - 1, 0)], pts[i], pts[i + 1], pts[min(i + 2, len(pts) - 1)]
        for j in range(9):
            t = j / 8
            t2, t3 = t * t, t * t * t
            x = 0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if len(out) > 1:
        pygame.draw.lines(surf, color, False, out, width)


def draw_cricket(target, cx, cy, color=C.BLUE_ELECTRIC, squash=1.0, wing=0.0, rot=0.0, band=None):
    """Con Dế phẳng một-màu, quay phải — thân lá, mắt trắng, 2 râu, chân nhảy."""
    surf = pygame.Surface((150, 150), pygame.SRCALPHA)
    cxl, cyl = 70, 80

    def P(x, y):
        return (cxl + x, cyl + y)

    sq = 0.82 + 0.18 * squash
    bw, bh = int(58 * sq), int(32 / sq)
    pygame.draw.line(surf, color, P(-8, 7), P(-26, 18), 8)
    pygame.draw.line(surf, color, P(-26, 18), P(-12, 25), 8)
    pygame.draw.line(surf, color, P(10, 11), P(8, 24), 4)
    pygame.draw.polygon(surf, color, [P(-40, 1), P(-8, -bh // 2 + 3), P(-8, bh // 2 - 3)])
    pygame.draw.ellipse(surf, color, (P(-14, -bh // 2)[0], P(-14, -bh // 2)[1], bw, bh))
    lift = int(wing * 7)
    pygame.draw.ellipse(surf, C.BLUE_WING, (P(-10, -bh // 2 - 3 - lift)[0], P(-10, -bh // 2 - 3 - lift)[1], int(38 * sq), 18))
    if band:
        pygame.draw.line(surf, band, P(20, -bh // 2 + 7), P(34, -bh // 2 + 5), 5)
    pygame.draw.circle(surf, C.WHITE, P(26, -3), 7)
    pygame.draw.circle(surf, C.INK, P(28, -3), 3)
    pygame.draw.circle(surf, C.WHITE, P(29, -4), 1)
    _smooth(surf, color, [P(28, -9), P(40, -22), P(52, -38), P(60, -52)], 3)
    _smooth(surf, color, [P(26, -7), P(34, -16), P(44, -28), P(50, -42)], 3)
    pygame.draw.circle(surf, color, P(60, -52), 3)
    pygame.draw.circle(surf, color, P(50, -42), 3)
    if rot:
        surf = pygame.transform.rotate(surf, -rot)
    target.blit(surf, surf.get_rect(center=(cx, cy)))
