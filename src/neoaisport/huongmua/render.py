"""Lớp vẽ Hứng Mưa — nền camera/trời + giọt mưa + rổ đi theo người."""
from __future__ import annotations

import pygame

from neoaisport import config as C
from neoaisport.ui.sprites import draw_cricket, font, load_logo, scale_to
from neoaisport.ui.widgets import (
    Particle, center_text, draw_text, mode_card, pill, round_rect, wordmark,
)


def _sky(w, h):
    s = pygame.Surface((w, h))
    for y in range(h):
        t = (y / h) ** 0.9
        s.fill(tuple(int(C.BLUE_CYAN[i] + (C.BLUE_SOFT[i] - C.BLUE_CYAN[i]) * t) for i in range(3)),
               (0, y, w, 1))
    return s


class RainRenderer:
    def __init__(self, screen, source_name="camera"):
        self.screen = screen
        self.source_name = source_name
        self.f_hero = font(72)
        self.f_big = font(46)
        self.f_md = font(26)
        self.f_sm = font(18)
        logo = load_logo()
        self.logo_big = scale_to(logo, w=250) if logo else None
        self.logo_sm = scale_to(logo, h=24) if logo else None
        self.sky = _sky(C.W, C.H)
        self.dim = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
        self.dim.fill((10, 16, 40, 90))
        self.fx = []

    def draw(self, ctrl, ev, lb, dt, bg=None, points=None):
        for _p, x, y in ev.caught:
            for _ in range(10):
                self.fx.append(Particle(x, y, C.BLUE_CYAN))
        for p in self.fx:
            p.update(dt)
        self.fx = [p for p in self.fx if p.life > 0]

        if ctrl.state == ctrl.MENU:
            self._menu(ctrl, lb)
            wordmark(self.screen, self.f_sm, self.logo_sm, "Hứng Mưa · NeoAiSport")
            return
        if bg is not None:
            self.screen.blit(bg, (0, 0))
            self.screen.blit(self.dim, (0, 0))
        else:
            self.screen.blit(self.sky, (0, 0))
        # đất
        pygame.draw.rect(self.screen, C.GREEN_CRICKET, (0, C.BASKET_Y + C.BASKET_H, C.W, C.H))
        pygame.draw.rect(self.screen, C.GREEN_LIME, (0, C.BASKET_Y + C.BASKET_H, C.W, 6))
        for d in ctrl.drops:
            self._drop(d)
        for p in self.fx:
            p.draw(self.screen)
        accents = [C.GREEN_CRICKET] if ctrl.mode == "solo" else [C.BLUE_ELECTRIC, C.ORANGE_HOT]
        for i, bx in enumerate(ctrl.basket_x):
            self._basket(bx, accents[i % len(accents)])
        if ctrl.state == ctrl.PLAY:
            self._hud(ctrl)
        if ctrl.state == ctrl.COUNTDOWN:
            center_text(self.screen, self.f_hero, str(ev.countdown_tick or 1),
                        C.W // 2, C.H // 2, C.BLUE_ELECTRIC, panel=True)
            center_text(self.screen, self.f_md, "Nghiêng người sẵn sàng!", C.W // 2, C.H // 2 + 70, C.WHITE)
        if ctrl.state == ctrl.RESULT:
            self._result(ctrl)
        wordmark(self.screen, self.f_sm, self.logo_sm, "Hứng Mưa · NeoAiSport")

    def _drop(self, d):
        x, y = int(d.x), int(d.y)
        col = C.GREEN_LIME if d.kind == "energy" else C.BLUE_CYAN
        pygame.draw.circle(self.screen, col, (x, y), C.DROP_R)
        pygame.draw.polygon(self.screen, col, [(x - 7, y - 6), (x + 7, y - 6), (x, y - 20)])
        pygame.draw.circle(self.screen, C.WHITE, (x - 4, y - 3), 3)

    def _basket(self, x, accent):
        x = int(x)
        w, h = C.BASKET_W, C.BASKET_H
        top = C.BASKET_Y
        pts = [(x - w // 2, top), (x + w // 2, top), (x + w // 2 - 14, top + h), (x - w // 2 + 14, top + h)]
        pygame.draw.polygon(self.screen, accent, pts)
        pygame.draw.line(self.screen, C.GREEN_LIME, (x - w // 2, top), (x + w // 2, top), 6)
        for k in range(-2, 3):
            pygame.draw.line(self.screen, C.GREEN_DEEP, (x + k * 26, top + 4), (x + k * 22, top + h - 2), 2)

    def _hud(self, ctrl):
        secs = max(0, int(ctrl.timer + 0.99))
        pill(self.screen, self.f_big, C.W // 2, 50, f"{secs}s", C.BLUE_ELECTRIC)
        if ctrl.mode == "solo":
            self._chip(20, 16, "Hứng", ctrl.counts[0], C.GREEN_CRICKET)
            draw_text(self.screen, self.f_sm, f"Kỷ lục {ctrl.best}", 24, 70, C.WHITE)
        else:
            self._chip(20, 16, "P1", ctrl.counts[0], C.BLUE_ELECTRIC)
            self._chip(C.W - 150, 16, "P2", ctrl.counts[1], C.ORANGE_HOT)

    def _chip(self, x, y, label, n, accent):
        r = pygame.Rect(x, y, 130, 46)
        round_rect(self.screen, r, (247, 247, 247, 235), accent, 4, 14)
        draw_text(self.screen, self.f_md, label, r.left + 12, r.top + 8, accent)
        num = self.f_md.render(str(n), True, C.INK)
        self.screen.blit(num, (r.right - 14 - num.get_width(), r.top + 8))

    def _menu(self, ctrl, lb):
        s = self.screen
        s.blit(self.sky, (0, 0))
        if self.logo_big:
            s.blit(self.logo_big, self.logo_big.get_rect(center=(C.W // 2, 60)))
        for k in range(6):
            self._drop(type("D", (), {"x": 80 + k * 140, "y": 250 + (k % 2) * 40, "kind": "water"}))
        center_text(s, self.f_hero, "Hứng Mưa", C.W // 2, 150, C.BLUE_ELECTRIC)
        center_text(s, self.f_sm, "NeoAiSport · nghiêng người hứng giọt", C.W // 2, 200, C.GREEN_CRICKET)
        mode_card(s, self.f_big, self.f_md, C.W // 2 - 180, 330, "SOLO", "Đếm giờ 45s", "Nút 1 · SPACE", C.BLUE_ELECTRIC)
        mode_card(s, self.f_big, self.f_md, C.W // 2 + 180, 330, "ĐẤU 2 NGƯỜI", "2 người 2 rổ", "Nút 2 · ENTER", C.ORANGE_HOT)
        center_text(s, self.f_sm, f"Camera: {self.source_name}   ·   ESC thoát", C.W // 2, C.H - 56, C.INK)

    def _result(self, ctrl):
        ov = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
        ov.fill((18, 26, 70, 130))
        self.screen.blit(ov, (0, 0))
        card = pygame.Rect(0, 0, 600, 240)
        card.center = (C.W // 2, C.H // 2)
        acc = C.ORANGE_HOT if "THẮNG" in ctrl.result else C.BLUE_ELECTRIC
        round_rect(self.screen, card, C.WHITE, acc, 5, 30)
        center_text(self.screen, self.f_hero, ctrl.result, C.W // 2, C.H // 2 - 46, acc)
        center_text(self.screen, self.f_md, "Nút 1 chơi lại  ·  Nút 2 menu  ·  ESC thoát",
                    C.W // 2, C.H // 2 + 52, C.INK)
