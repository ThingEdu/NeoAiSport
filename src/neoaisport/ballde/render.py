"""Lớp vẽ Ball Dế — sân + khung thành + thủ môn Dế + bóng + khung chân + hướng sút."""
from __future__ import annotations

import math

import pygame

from neoaisport import config as C
from neoaisport.ballde.game import DIRS
from neoaisport.ui.sprites import draw_cricket, font, load_logo, scale_to
from neoaisport.ui.widgets import (
    center_text, draw_text, energy_glow, mode_card, pill, round_rect, wordmark,
)

GOAL_L, GOAL_R = int(C.W * 0.27), int(C.W * 0.73)
GOAL_H = 150
KEEPER_Y = C.PEN_GOAL_Y + GOAL_H - 26
PITCH = (32, 132, 86)


def _zone_x(d):
    span = GOAL_R - GOAL_L
    return {"L": GOAL_L + span * 0.2, "C": C.W / 2, "R": GOAL_R - span * 0.2}[d]


class PenaltyRenderer:
    def __init__(self, screen, source_name="camera"):
        self.screen = screen
        self.source_name = source_name
        self.t = 0.0
        self.f_hero = font(72)
        self.f_big = font(46)
        self.f_md = font(26)
        self.f_sm = font(18)
        logo = load_logo()
        self.logo_big = scale_to(logo, w=250) if logo else None
        self.logo_sm = scale_to(logo, h=24) if logo else None
        self.dim = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
        self.dim.fill((10, 16, 40, 90))

    def draw(self, ctrl, ev, lb, dt, bg=None, points=None):
        self.t += dt
        feet = points or []
        if ctrl.state == ctrl.MENU:
            self._menu(ctrl, lb)
            wordmark(self.screen, self.f_sm, self.logo_sm, "Ball Dế · NeoAiSport")
            return
        if bg is not None:
            self.screen.blit(bg, (0, 0))
            self.screen.blit(self.dim, (0, 0))
        else:
            self._pitch()
        self._goal()

        # thủ môn (Dế) — bay theo keeper_dir khi sút
        kx = C.W / 2
        if ctrl.phase == "shot":
            kx = C.W / 2 + (_zone_x(ctrl.keeper_dir) - C.W / 2) * min(1, ctrl.ball_t * 1.2)
        draw_cricket(self.screen, kx, KEEPER_Y, C.PINK_HOT, 1.0, 0.6, 0)

        # bóng
        if ctrl.phase == "shot":
            tx, ty = _zone_x(ctrl.kick_dir), C.PEN_GOAL_Y + 46
            bx = C.W / 2 + (tx - C.W / 2) * ctrl.ball_t
            by = C.PEN_SPOT_Y + (ty - C.PEN_SPOT_Y) * ctrl.ball_t
            self._ball(bx, by, 14 + int(6 * (1 - ctrl.ball_t)))
        else:
            self._ball(C.W / 2, C.PEN_SPOT_Y, 18)

        self._legs(feet)                        # khung chân + bàn chân + quầng sáng

        # thể hiện HƯỚNG SÚT
        if ctrl.phase == "shot":
            self._kick_dir(ctrl)
            if ctrl.ball_t > 0.7:
                txt, col = ("BÀN!", C.ORANGE_HOT) if ctrl.scored else ("CẢN!", C.BLUE_ELECTRIC)
                center_text(self.screen, self.f_hero, txt, C.W // 2, 150, col, panel=True)

        # nhắc nếu camera chưa thấy chân
        if ctrl.state in (ctrl.PLAY, ctrl.COUNTDOWN) and self.source_name != "mouse" \
                and not self._feet_visible(feet):
            center_text(self.screen, self.f_md, "Lùi xa để camera thấy CẢ CHÂN",
                        C.W // 2, C.H - 100, C.PINK_HOT, panel=True)

        if ctrl.state == ctrl.PLAY:
            self._hud(ctrl)
        if ctrl.state == ctrl.COUNTDOWN:
            center_text(self.screen, self.f_hero, str(ev.countdown_tick or 1),
                        C.W // 2, C.H // 2, C.BLUE_ELECTRIC, panel=True)
            center_text(self.screen, self.f_md, "Vung chân để sút trái / phải / giữa!",
                        C.W // 2, C.H // 2 + 70, C.WHITE)
        if ctrl.state == ctrl.RESULT:
            self._result(ctrl)
        wordmark(self.screen, self.f_sm, self.logo_sm, "Ball Dế · NeoAiSport")

    def _legs(self, pts):
        """Vẽ khung chân (hông–gối–cổ chân–bàn chân) + bàn chân + quầng sáng."""
        s = self.screen
        if len(pts) >= 8:
            for chain in (pts[0:4], pts[4:8]):
                ip = [(int(p[0]), int(p[1])) for p in chain]
                pygame.draw.lines(s, C.WHITE, False, ip, 6)
                for p in ip[:3]:
                    pygame.draw.circle(s, C.BLUE_ELECTRIC, p, 7)
                    pygame.draw.circle(s, C.WHITE, p, 3)
                foot = ip[3]
                energy_glow(s, foot[0], foot[1], 46, C.GREEN_LIME, self.t)
                pygame.draw.circle(s, C.GREEN_LIME, foot, 12)
                pygame.draw.circle(s, C.INK, foot, 12, 2)
        else:
            for f in pts:                                   # fallback chuột
                energy_glow(s, f[0], f[1], 46, C.GREEN_LIME, self.t)

    def _feet_visible(self, pts):
        return len(pts) >= 8 and pts[3][1] < C.H and pts[7][1] < C.H

    def _kick_dir(self, ctrl):
        s = self.screen
        span = (GOAL_R - GOAL_L) // 3
        zx = {"L": GOAL_L, "C": GOAL_L + span, "R": GOAL_L + 2 * span}[ctrl.kick_dir]
        hl = pygame.Surface((span, GOAL_H), pygame.SRCALPHA)
        hl.fill((*C.GREEN_LIME, 90))
        s.blit(hl, (zx, C.PEN_GOAL_Y))
        sx, sy = C.W // 2, int(C.PEN_SPOT_Y)
        tx, ty = int(_zone_x(ctrl.kick_dir)), C.PEN_GOAL_Y + GOAL_H + 24
        pygame.draw.line(s, C.GREEN_LIME, (sx, sy), (tx, ty), 6)
        ang = math.atan2(ty - sy, tx - sx)
        for da in (2.5, -2.5):
            ex, ey = tx - 18 * math.cos(ang + da), ty - 18 * math.sin(ang + da)
            pygame.draw.line(s, C.GREEN_LIME, (tx, ty), (int(ex), int(ey)), 6)
        labels = {"L": "SÚT TRÁI", "C": "SÚT GIỮA", "R": "SÚT PHẢI"}
        center_text(s, self.f_md, labels[ctrl.kick_dir], C.W // 2, C.H - 92, C.GREEN_CRICKET, panel=True)

    def _pitch(self):
        self.screen.fill(PITCH)
        for y in range(0, C.H, 80):             # sọc cỏ
            if (y // 80) % 2:
                pygame.draw.rect(self.screen, (28, 120, 78), (0, y, C.W, 80))
        pygame.draw.rect(self.screen, C.WHITE, (GOAL_L - 50, C.PEN_GOAL_Y, GOAL_R - GOAL_L + 100, GOAL_H + 120), 3)
        pygame.draw.circle(self.screen, C.WHITE, (C.W // 2, int(C.PEN_SPOT_Y)), 4)

    def _goal(self):
        s = self.screen
        net = pygame.Rect(GOAL_L, C.PEN_GOAL_Y, GOAL_R - GOAL_L, GOAL_H)
        mesh = pygame.Surface(net.size, pygame.SRCALPHA)
        for x in range(0, net.width, 16):
            pygame.draw.line(mesh, (255, 255, 255, 70), (x, 0), (x, net.height))
        for y in range(0, net.height, 16):
            pygame.draw.line(mesh, (255, 255, 255, 70), (0, y), (net.width, y))
        s.blit(mesh, net.topleft)
        pygame.draw.rect(s, C.WHITE, (GOAL_L - 8, C.PEN_GOAL_Y - 8, 8, GOAL_H + 8))
        pygame.draw.rect(s, C.WHITE, (GOAL_R, C.PEN_GOAL_Y - 8, 8, GOAL_H + 8))
        pygame.draw.rect(s, C.WHITE, (GOAL_L - 8, C.PEN_GOAL_Y - 8, GOAL_R - GOAL_L + 16, 8))

    def _ball(self, x, y, r):
        x, y = int(x), int(y)
        pygame.draw.circle(self.screen, C.WHITE, (x, y), r)
        pygame.draw.circle(self.screen, C.INK, (x, y), r, 2)
        pygame.draw.circle(self.screen, C.INK, (x, y), max(2, r // 3))

    def _hud(self, ctrl):
        if ctrl.mode == "solo":
            pill(self.screen, self.f_big, C.W // 2, C.H - 40, f"{ctrl.goals[0]}/{C.PEN_SHOTS}", C.GREEN_CRICKET)
            draw_text(self.screen, self.f_sm, f"Kỷ lục {ctrl.best}", 24, 24, C.WHITE)
            draw_text(self.screen, self.f_sm, f"Lượt {ctrl.shots_done[0] + 1}/{C.PEN_SHOTS}", C.W - 130, 24, C.WHITE)
        else:
            self._chip(20, 16, "P1", ctrl.goals[0], C.BLUE_ELECTRIC, ctrl.cur == 0)
            self._chip(C.W - 150, 16, "P2", ctrl.goals[1], C.ORANGE_HOT, ctrl.cur == 1)

    def _chip(self, x, y, label, n, accent, active):
        r = pygame.Rect(x, y, 130, 46)
        round_rect(self.screen, r, (247, 247, 247, 235), accent, 6 if active else 3, 14)
        draw_text(self.screen, self.f_md, label, r.left + 12, r.top + 8, accent)
        num = self.f_md.render(str(n), True, C.INK)
        self.screen.blit(num, (r.right - 14 - num.get_width(), r.top + 8))

    def _menu(self, ctrl, lb):
        s = self.screen
        self._pitch()
        if self.logo_big:
            s.blit(self.logo_big, self.logo_big.get_rect(center=(C.W // 2, 56)))
        self._ball(C.W // 2 - 250, 160, 22)
        draw_cricket(s, C.W // 2 + 250, 158, C.PINK_HOT, 1.0, 0.6, -6)
        center_text(s, self.f_hero, "Ball Dế", C.W // 2, 150, C.BLUE_ELECTRIC)
        center_text(s, self.f_sm, "NeoAiSport · đá penalty bằng chân", C.W // 2, 200, C.GREEN_LIME)
        mode_card(s, self.f_big, self.f_md, C.W // 2 - 180, 330, "SOLO", f"{C.PEN_SHOTS} lượt sút", "Nút 1 · SPACE", C.BLUE_ELECTRIC)
        mode_card(s, self.f_big, self.f_md, C.W // 2 + 180, 330, "ĐẤU 2 NGƯỜI", "Thay phiên sút", "Nút 2 · ENTER", C.ORANGE_HOT)
        center_text(s, self.f_sm, f"Camera: {self.source_name}   ·   ESC thoát", C.W // 2, C.H - 56, C.WHITE)

    def _result(self, ctrl):
        ov = pygame.Surface((C.W, C.H), pygame.SRCALPHA)
        ov.fill((18, 26, 70, 140))
        self.screen.blit(ov, (0, 0))
        card = pygame.Rect(0, 0, 600, 240)
        card.center = (C.W // 2, C.H // 2)
        acc = C.ORANGE_HOT if ("THẮNG" in ctrl.result or ctrl.goals[0] >= C.PEN_SHOTS - 1) else C.BLUE_ELECTRIC
        round_rect(self.screen, card, C.WHITE, acc, 5, 30)
        center_text(self.screen, self.f_hero, ctrl.result, C.W // 2, C.H // 2 - 46, acc)
        center_text(self.screen, self.f_md, "Nút 1 chơi lại  ·  Nút 2 menu  ·  ESC thoát",
                    C.W // 2, C.H // 2 + 52, C.INK)
