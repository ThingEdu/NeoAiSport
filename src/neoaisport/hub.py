"""NeoAiSport — màn hình tổng: chọn game thị giác AI (camera). Game chạy tiến trình riêng.

  A/D (hoặc chuột) chọn · ENTER chơi · ESC thoát.
"""
from __future__ import annotations

import math
import subprocess
import sys

import pygame

from neoaisport import config as C
from neoaisport.ui.sprites import draw_cricket, font, load_logo, scale_to
from neoaisport.ui.widgets import center_text, round_rect, wordmark

GAMES = [
    dict(title="Bắt Dế", tech="Bàn tay", move="Vẫy tay bắt đàn Dế",
         module="neoaisport.batde.app", args=["--source", "camera"],
         accent=C.GREEN_CRICKET, icon="hand", ready=True),
    dict(title="Hứng Mưa", tech="Đầu · thân", move="Nghiêng người hứng giọt",
         module="neoaisport.huongmua.app", args=["--source", "camera"],
         accent=C.BLUE_ELECTRIC, icon="head", ready=True),
    dict(title="Đỡ Bóng", tech="Bàn tay", move="Vung tay giữ bóng",
         module="neoaisport.dobong.app", args=["--source", "camera"],
         accent=C.ORANGE_HOT, icon="ball", ready=True),
]

TH, GAP = 320, 22


def _bg(w, h):
    s = pygame.Surface((w, h))
    for y in range(h):
        t = (y / h) ** 0.8
        s.fill(tuple(int(C.BLUE_CYAN[i] + (C.BLUE_SOFT[i] - C.BLUE_CYAN[i]) * t) for i in range(3)),
               (0, y, w, 1))
    return s


class Hub:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((C.W, C.H))
        pygame.display.set_caption("NeoAiSport — Dế Foundation")
        self.clock = pygame.time.Clock()
        self.f_hero = font(64)
        self.f_big = font(32)
        self.f_md = font(24)
        self.f_sm = font(18)
        logo = load_logo()
        self.logo_big = scale_to(logo, w=240) if logo else None
        self.logo_sm = scale_to(logo, h=24) if logo else None
        self.bg = _bg(C.W, C.H)
        self.sel = 0
        self.t = 0.0
        n = len(GAMES)
        self.tw = min(250, (C.W - 40 - (n - 1) * GAP) // n)   # tự co cho vừa nhiều thẻ

    def _x0(self):
        n = len(GAMES)
        return (C.W - (n * self.tw + (n - 1) * GAP)) // 2

    def _rect(self, i):
        return pygame.Rect(self._x0() + i * (self.tw + GAP), 240, self.tw, TH)

    def _at(self, pos):
        for i in range(len(GAMES)):
            if self._rect(i).collidepoint(pos):
                return i
        return None

    def launch(self, game):
        if not game["ready"] or not game["module"]:
            return
        pygame.display.iconify()
        try:
            subprocess.run([sys.executable, "-m", game["module"], *game["args"]])
        except Exception as exc:
            print(f"[hub] không mở được {game['title']}: {exc}")
        self.screen = pygame.display.set_mode((C.W, C.H))
        pygame.event.clear()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(C.FPS) / 1000.0
            self.t += dt
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        running = False
                    elif e.key in (pygame.K_LEFT, pygame.K_a):
                        self.sel = (self.sel - 1) % len(GAMES)
                    elif e.key in (pygame.K_RIGHT, pygame.K_d):
                        self.sel = (self.sel + 1) % len(GAMES)
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                        self.launch(GAMES[self.sel])
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    i = self._at(e.pos)
                    if i is not None:
                        self.sel = i
                        self.launch(GAMES[i])
                elif e.type == pygame.MOUSEMOTION:
                    i = self._at(e.pos)
                    if i is not None:
                        self.sel = i
            self.draw()
            pygame.display.flip()
        pygame.quit()

    def draw(self):
        s = self.screen
        s.blit(self.bg, (0, 0))
        for k in range(3):
            x = (120 + k * 320 + int(self.t * 38)) % (C.W + 120) - 60
            y = 150 + int(16 * math.sin(self.t * 2 + k))
            draw_cricket(s, x, y, [C.BLUE_SOFT, C.GREEN_LIME, C.BLUE_CYAN][k], 1.0, 0.5, 6)
        if self.logo_big:
            s.blit(self.logo_big, self.logo_big.get_rect(center=(C.W // 2, 52)))
        center_text(s, self.f_hero, "NeoAiSport", C.W // 2, 132, C.BLUE_ELECTRIC)
        center_text(s, self.f_sm, "Game thể thao thị giác AI · camera + cơ thể", C.W // 2, 182, C.GREEN_CRICKET)
        for i, g in enumerate(GAMES):
            self._tile(i, g)
        center_text(s, self.f_sm, "A / D (hoặc chuột) chọn   ·   ENTER chơi   ·   ESC thoát",
                    C.W // 2, C.H - 36, C.INK)
        wordmark(s, self.f_sm, self.logo_sm, "NeoAiSport")

    def _tile(self, i, g):
        s = self.screen
        r = self._rect(i)
        active = i == self.sel
        if active:
            r = r.inflate(16, 16)
        round_rect(s, r, C.WHITE, g["accent"], 6 if active else 3, 26)
        pygame.draw.circle(s, C.BLUE_SOFT, (r.left + 24, r.top + 24), 12)
        self._icon(g["icon"], r.centerx, r.top + 92, g["accent"])
        center_text(s, self.f_big, g["title"], r.centerx, r.top + 188, g["accent"])
        center_text(s, self.f_sm, g["tech"], r.centerx, r.top + 222, C.INK)
        center_text(s, self.f_sm, g["move"], r.centerx, r.top + 246, C.GREEN_CRICKET)
        chip = pygame.Rect(0, 0, 156, 36)
        chip.center = (r.centerx, r.bottom - 28)
        if g["ready"]:
            if active:
                round_rect(s, chip, g["accent"], None, 0, 18)
                center_text(s, self.f_sm, "CHƠI  ›", chip.centerx, chip.centery, C.WHITE)
        else:
            round_rect(s, chip, C.GREEN_SOFT, C.GREEN_CRICKET, 2, 18)
            center_text(s, self.f_sm, "Sắp ra mắt", chip.centerx, chip.centery, C.GREEN_CRICKET)

    def _icon(self, kind, cx, cy, accent):
        s = self.screen
        if kind == "hand":
            draw_cricket(s, cx + 18, cy + 6, C.PINK_HOT, 1.0, 0.5, -8)
            r = 30 + int(3 * math.sin(self.t * 5))
            pygame.draw.circle(s, C.GREEN_LIME, (cx - 8, cy), r, 6)
            pygame.draw.circle(s, C.GREEN_LIME, (cx - 8, cy), 6)
        elif kind == "head":
            pygame.draw.circle(s, accent, (cx, cy), 28)
            pygame.draw.circle(s, C.WHITE, (cx - 9, cy - 4), 5)
            pygame.draw.circle(s, C.WHITE, (cx + 9, cy - 4), 5)
            for k in range(4):
                dx = -24 + k * 16
                pygame.draw.line(s, C.BLUE_CYAN, (cx + dx, cy - 40), (cx + dx, cy - 28), 3)
        elif kind == "ball":
            pygame.draw.circle(s, C.WHITE, (cx, cy), 28)
            pygame.draw.circle(s, accent, (cx, cy), 28, 5)
            pygame.draw.arc(s, accent, (cx - 28, cy - 28, 56, 56), 0.4, 2.3, 4)
            pygame.draw.line(s, accent, (cx - 4, cy - 28), (cx - 11, cy - 42), 2)
            pygame.draw.line(s, accent, (cx + 4, cy - 28), (cx + 11, cy - 42), 2)
        elif kind == "foot":
            pygame.draw.circle(s, C.WHITE, (cx + 18, cy + 8), 16)   # bóng
            pygame.draw.circle(s, C.INK, (cx + 18, cy + 8), 16, 2)
            pygame.draw.line(s, accent, (cx - 22, cy - 18), (cx - 18, cy + 8), 9)  # cẳng chân
            pygame.draw.line(s, accent, (cx - 18, cy + 8), (cx + 2, cy + 12), 9)   # bàn chân
            d = 6 + int(4 * math.sin(self.t * 6))
            pygame.draw.arc(s, C.GREEN_LIME, (cx + 30, cy - 12 - d, 24, 40), -1.0, 1.0, 3)  # vệt sút
        else:  # face
            pygame.draw.circle(s, accent, (cx, cy), 30, 5)
            pygame.draw.circle(s, accent, (cx - 10, cy - 6), 4)
            pygame.draw.circle(s, accent, (cx + 10, cy - 6), 4)
            pygame.draw.arc(s, accent, (cx - 14, cy - 6, 28, 22), math.pi, 2 * math.pi, 4)


def main():
    Hub().run()


if __name__ == "__main__":
    main()
