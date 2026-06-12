"""Helper vẽ dùng chung cho các game NeoArcade (cùng style Dế Foundation)."""
from __future__ import annotations

import math
import random

import pygame

from neoaisport import config as C


def round_rect(screen, rect, fill, border=None, bw=0, rad=16):
    if len(fill) == 4:
        srf = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(srf, fill, (0, 0, *rect.size), border_radius=rad)
        screen.blit(srf, rect.topleft)
    else:
        pygame.draw.rect(screen, fill, rect, border_radius=rad)
    if border and bw:
        pygame.draw.rect(screen, border, rect, width=bw, border_radius=rad)


def draw_text(screen, font, txt, x, y, col, center=False, shadow=True):
    img = font.render(txt, True, col)
    r = img.get_rect()
    if center:
        r.center = (x, y)
    else:
        r.topleft = (x, y)
    if shadow:
        screen.blit(font.render(txt, True, (0, 0, 0)), (r.x + 2, r.y + 2))
    screen.blit(img, r)


def center_text(screen, font, txt, x, y, col, panel=False):
    if panel:
        pad = font.render(txt, True, col).get_rect(center=(x, y)).inflate(54, 30)
        round_rect(screen, pad, C.WHITE, col, 5, 22)
    draw_text(screen, font, txt, x, y, col, center=True)


def pill(screen, font, cx, cy, txt, color):
    img = font.render(txt, True, C.WHITE)
    r = img.get_rect(center=(cx, cy))
    pad = pygame.Rect(0, 0, max(r.width + 40, 78), 58)
    pad.center = (cx, cy)
    round_rect(screen, pad, color, C.WHITE, 4, 22)
    screen.blit(img, r)


def wordmark(screen, font_sm, logo_sm, label="NeoArcade"):
    if logo_sm:
        lw, lh = logo_sm.get_size()
        txt = font_sm.render(label, True, C.INK)
        p = pygame.Rect(14, C.H - 38, 12 + lw + 10 + txt.get_width() + 12, lh + 8)
        round_rect(screen, p, C.WHITE, C.BLUE_ELECTRIC, 2, 13)
        screen.blit(logo_sm, (p.left + 12, p.centery - lh // 2))
        screen.blit(txt, (p.left + 12 + lw + 10, p.centery - txt.get_height() // 2))
    else:
        p = pygame.Rect(14, C.H - 36, 220, 26)
        round_rect(screen, p, C.WHITE, C.BLUE_ELECTRIC, 2, 13)
        draw_text(screen, font_sm, label, p.left + 14, p.centery - 9, C.INK)


def mode_card(screen, f_big, f_md, cx, cy, title, sub, key, accent):
    card = pygame.Rect(0, 0, 300, 170)
    card.center = (cx, cy)
    round_rect(screen, card, C.WHITE, accent, 5, 26)
    pygame.draw.circle(screen, C.BLUE_SOFT, (card.left + 26, card.top + 26), 13)
    pygame.draw.circle(screen, C.GREEN_LIME, (card.right - 24, card.bottom - 24), 11)
    center_text(screen, f_big, title, cx, cy - 36, accent)
    center_text(screen, f_md, sub, cx, cy + 6, C.INK)
    center_text(screen, f_md, key, cx, cy + 46, C.GREEN_CRICKET)


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "col", "r")

    def __init__(self, x, y, col):
        a = random.uniform(0, math.tau)
        sp = random.uniform(70, 260)
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(a) * sp, math.sin(a) * sp
        self.life, self.col, self.r = random.uniform(0.3, 0.7), col, random.randint(3, 6)

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, s):
        if self.life > 0:
            pygame.draw.circle(s, self.col, (int(self.x), int(self.y)), self.r)
