"""Lớp vẽ Bắt Dế (pygame) — nền camera (hoặc cỏ brand) + đàn Dế + con trỏ tay."""
from __future__ import annotations

import random

import pygame

from neoaisport import config as C
from neoaisport.ui.sprites import draw_cricket, font, load_logo, scale_to
from neoaisport.ui.widgets import (
    Particle,
    center_text,
    draw_text,
    energy_glow,
    mode_card,
    pill,
    round_rect,
    wordmark,
)

CRICKET_COLORS = [C.BLUE_ELECTRIC, C.GREEN_CRICKET, C.PINK_HOT]


class CatchRenderer:
    def __init__(self, screen, source_name="camera"):
        self.screen = screen
        self.source_name = source_name
        self.t = 0.0
        self.f_hero = font(76)
        self.f_big = font(46)
        self.f_md = font(26)
        self.f_sm = font(18)
        logo = load_logo()
        self.logo_big = scale_to(logo, w=250) if logo else None
        self.logo_sm = scale_to(logo, h=24) if logo else None
        self._brand_bg = self._make_brand_bg()
        self.fx: list = []
        self.dim = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
        self.dim.fill((10, 16, 40, 85))            # nền trận: mờ nhẹ để Dế nổi
        self.menu_dim = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
        self.menu_dim.fill((10, 16, 40, 120))      # menu: mờ hơn cho chữ dễ đọc

    def _make_brand_bg(self):
        s = pygame.Surface((C.W, C.H))
        s.fill(C.GREEN_CRICKET)
        rng = random.Random(7)
        for _ in range(120):
            x, y = rng.randint(0, C.W), rng.randint(0, C.H)
            pygame.draw.circle(s, C.GREEN_DEEP, (x, y), rng.randint(2, 5))
        for _ in range(40):
            x, y = rng.randint(0, C.W), rng.randint(0, C.H)
            pygame.draw.polygon(s, C.GREEN_LIME, [(x, y), (x + 5, y - 12), (x + 10, y)])
        return s

    def _accents(self, hands, mode):
        """Màu con trỏ từng tay (theo thứ tự x): solo=lime, đấu=blue/orange."""
        if not hands:
            return {}
        if mode == "solo":
            return {id(h): C.GREEN_LIME for h in hands}
        order = sorted(hands, key=lambda h: h[0])
        cols = {}
        for i, h in enumerate(order):
            cols[id(h)] = C.BLUE_ELECTRIC if i == 0 else C.ORANGE_HOT
        return cols

    def draw(self, ctrl, ev, lb, dt, bg=None, hands=None):
        hands = hands or []
        self.t += dt
        for pl, x, y in ev.caught:
            for _ in range(14):
                self.fx.append(Particle(x, y, C.GREEN_LIME))
        for p in self.fx:
            p.update(dt)
        self.fx = [p for p in self.fx if p.life > 0]

        if ctrl.state == ctrl.MENU:
            self._menu(ctrl, lb, bg)
            for h in hands:                         # hiện con trỏ tay ngay ở menu
                self._cursor(h[0], h[1], C.GREEN_LIME)
            wordmark(self.screen, self.f_sm, self.logo_sm, "Bắt Dế · NeoAiSport")
            return

        if bg is not None:
            self.screen.blit(bg, (0, 0))
            self.screen.blit(self.dim, (0, 0))
        else:
            self.screen.blit(self._brand_bg, (0, 0))

        for c in ctrl.crickets:
            draw_cricket(self.screen, c.x, c.y, CRICKET_COLORS[c.color_idx % 3], 1.0, 0.4, 0)
        for p in self.fx:
            p.draw(self.screen)
        cols = self._accents(hands, ctrl.mode)
        for h in hands:
            self._cursor(h[0], h[1], cols.get(id(h), C.GREEN_LIME))

        if ctrl.state == ctrl.PLAY:
            self._hud(ctrl)
        if ctrl.state == ctrl.COUNTDOWN:
            center_text(self.screen, self.f_hero, str(ev.countdown_tick or 1),
                        C.W // 2, C.H // 2, C.BLUE_ELECTRIC, panel=True)
            center_text(self.screen, self.f_md, "Vẫy tay sẵn sàng!", C.W // 2, C.H // 2 + 70, C.WHITE)
        if ctrl.state == ctrl.RESULT:
            self._result(ctrl, lb)
        wordmark(self.screen, self.f_sm, self.logo_sm, "Bắt Dế · NeoAiSport")

    def _cursor(self, x, y, accent):
        energy_glow(self.screen, x, y, int(C.CATCH_R * 1.5), accent, self.t)

    def _hud(self, ctrl):
        secs = max(0, int(ctrl.timer + 0.99))
        pill(self.screen, self.f_big, C.W // 2, 50, f"{secs}s", C.BLUE_ELECTRIC)
        bar = pygame.Rect(C.W // 2 - 130, 84, 260, 10)
        round_rect(self.screen, bar, (255, 255, 255, 90), None, 0, 5)
        fw = int(260 * max(0, ctrl.timer) / ctrl.time_limit)
        if fw > 4:
            fb = bar.copy()
            fb.width = fw
            round_rect(self.screen, fb, C.GREEN_LIME, None, 0, 5)
        if ctrl.mode == "solo":
            self._chip(20, 16, "Bắt", ctrl.counts[0], C.GREEN_CRICKET)
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

    def _menu(self, ctrl, lb, bg=None):
        s = self.screen
        if bg is not None:                          # thấy webcam ngay ở menu
            s.blit(bg, (0, 0))
            s.blit(self.menu_dim, (0, 0))
        else:
            s.blit(self._brand_bg, (0, 0))
        if self.logo_big:
            s.blit(self.logo_big, self.logo_big.get_rect(center=(C.W // 2, 60)))
        draw_cricket(s, C.W // 2 - 250, 160, C.BLUE_ELECTRIC, 1.0, 0.6, 6)
        draw_cricket(s, C.W // 2 - 150, 150, C.PINK_HOT, 1.0, 0.3, -10)
        draw_cricket(s, C.W // 2 + 250, 160, C.ORANGE_HOT, 1.0, 0.8, -6)
        draw_cricket(s, C.W // 2 + 150, 150, C.GREEN_CRICKET, 1.0, 0.5, 10)
        center_text(s, self.f_hero, "Bắt Dế", C.W // 2, 150, C.BLUE_ELECTRIC)
        center_text(s, self.f_sm, "NeoAiSport · vẫy tay bắt đàn Dế", C.W // 2, 200, C.GREEN_LIME)
        mode_card(s, self.f_big, self.f_md, C.W // 2 - 180, 330, "SOLO", "Đếm giờ 45s", "Nút 1 · SPACE", C.BLUE_ELECTRIC)
        mode_card(s, self.f_big, self.f_md, C.W // 2 + 180, 330, "ĐẤU 2 NGƯỜI", "Hai tay tranh đàn", "Nút 2 · ENTER", C.ORANGE_HOT)
        top = lb.top("batde", limit=3) if lb else []
        if top:
            center_text(s, self.f_sm, "TOP: " + "   ".join(f"{n} {sc}" for n, sc in top),
                        C.W // 2, C.H - 92, C.WHITE)
        center_text(s, self.f_sm, f"Camera: {self.source_name}   ·   ESC thoát", C.W // 2, C.H - 56, C.WHITE)

    def _result(self, ctrl, lb):
        ov = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
        ov.fill((18, 26, 70, 130))
        self.screen.blit(ov, (0, 0))
        card = pygame.Rect(0, 0, 600, 250)
        card.center = (C.W // 2, C.H // 2)
        acc = C.ORANGE_HOT if "THẮNG" in ctrl.result else C.BLUE_ELECTRIC
        round_rect(self.screen, card, C.WHITE, acc, 5, 30)
        center_text(self.screen, self.f_hero, ctrl.result, C.W // 2, C.H // 2 - 50, acc)
        center_text(self.screen, self.f_md, "Nút 1 chơi lại  ·  Nút 2 menu  ·  ESC thoát",
                    C.W // 2, C.H // 2 + 54, C.INK)
