"""Lõi Bắt Dế — THUẦN Python (không pygame/camera), test được.

Sân chung (C.W × C.H) có một đàn Dế nhảy. Mỗi khung nhận danh sách `hands`
(toạ độ px của bàn tay, đã soi gương). Tay chạm Dế (trong CATCH_R) thì bắt được;
Dế thấy tay tới gần (FLEE_R) thì bỏ chạy. Hết giờ → kết quả.

  solo : mọi bàn tay tính cho người 0 (đua điểm theo thời gian).
  duel : 2 bàn tay (trái = P1, phải = P2) cùng tranh 1 đàn — ai bắt nhiều hơn thắng.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from neoaisport import config as C

MARGIN = 70


@dataclass
class CatchEvents:
    caught: list = field(default_factory=list)   # [(player, x, y)]
    countdown_tick: int | None = None
    started: bool = False
    ended: bool = False


class Cricket:
    def __init__(self, x, y, rng: random.Random, color_idx=0):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.rng = rng
        self.color_idx = color_idx
        self.caught = False
        self._pick_target()

    def _pick_target(self):
        self.tx = self.rng.uniform(MARGIN, C.W - MARGIN)
        self.ty = self.rng.uniform(MARGIN, C.H - MARGIN)

    def update(self, dt, hands):
        near, nd = None, C.FLEE_R
        for hx, hy in hands:
            d = math.hypot(self.x - hx, self.y - hy)
            if d < nd:
                nd, near = d, (hx, hy)
        if near:                                   # bỏ chạy khỏi tay
            ax, ay = self.x - near[0], self.y - near[1]
            n = math.hypot(ax, ay) or 1.0
            self.vx, self.vy = ax / n * C.CRICKET_FLEE, ay / n * C.CRICKET_FLEE
        else:                                      # lang thang tới đích
            dx, dy = self.tx - self.x, self.ty - self.y
            n = math.hypot(dx, dy)
            if n < 8:
                self._pick_target()
            else:
                self.vx, self.vy = dx / n * C.CRICKET_SPEED, dy / n * C.CRICKET_SPEED
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < MARGIN or self.x > C.W - MARGIN:
            self.x = max(MARGIN, min(C.W - MARGIN, self.x))
            self._pick_target()
        if self.y < MARGIN or self.y > C.H - MARGIN:
            self.y = max(MARGIN, min(C.H - MARGIN, self.y))
            self._pick_target()


class CatchController:
    MENU, COUNTDOWN, PLAY, RESULT = "menu", "countdown", "play", "result"

    def __init__(self, leaderboard=None, seed=1, time_limit=C.CATCH_TIME):
        self.lb = leaderboard
        self.rng = random.Random(seed)
        self.time_limit = time_limit
        self.state = self.MENU
        self.mode = None
        self.crickets: list[Cricket] = []
        self.counts = [0]
        self.timer = 0.0
        self.count = 0.0
        self.result = ""
        self.winner = None
        self.best = leaderboard.best("batde") if leaderboard else 0
        self.game_id = 0

    def _spawn(self):
        return Cricket(self.rng.uniform(MARGIN, C.W - MARGIN),
                       self.rng.uniform(MARGIN, C.H - MARGIN),
                       self.rng, self.rng.randint(0, 2))

    def start(self, mode):
        self.mode = mode
        self.game_id += 1
        self.counts = [0] if mode == "solo" else [0, 0]
        self.crickets = [self._spawn() for _ in range(C.CATCH_FLOCK)]
        self.timer = self.time_limit
        self.count = C.COUNTDOWN
        self.result = ""
        self.winner = None
        self.state = self.COUNTDOWN

    def press(self, btn):
        if btn not in (0, 1):
            return
        if self.state == self.MENU:
            self.start("solo" if btn == 0 else "duel")
        elif self.state == self.RESULT:
            self.start(self.mode) if btn == 0 else setattr(self, "state", self.MENU)

    def _assign(self, hands):
        """Gán mỗi bàn tay cho 1 người chơi → [(player, (x,y))]."""
        if not hands:
            return []
        if self.mode == "solo":
            return [(0, h) for h in hands]
        order = sorted(hands, key=lambda h: h[0])
        if len(order) == 1:
            return [(0 if order[0][0] < C.W / 2 else 1, order[0])]
        return [(0, order[0]), (1, order[-1])]

    def update(self, dt, hands=None) -> CatchEvents:
        hands = hands or []
        ev = CatchEvents()
        if self.state == self.COUNTDOWN:
            self.count -= dt
            ev.countdown_tick = max(1, int(self.count) + 1)
            if self.count <= 0:
                self.state = self.PLAY
                ev.started = True
        elif self.state == self.PLAY:
            self.timer -= dt
            for c in self.crickets:
                c.update(dt, hands)
            for player, (hx, hy) in self._assign(hands):
                best, bd = None, C.CATCH_R
                for c in self.crickets:
                    if c.caught:
                        continue
                    d = math.hypot(c.x - hx, c.y - hy)
                    if d < bd:
                        bd, best = d, c
                if best:
                    best.caught = True
                    self.counts[player] += 1
                    ev.caught.append((player, best.x, best.y))
            if any(c.caught for c in self.crickets):
                self.crickets = [c for c in self.crickets if not c.caught]
                while len(self.crickets) < C.CATCH_FLOCK:
                    self.crickets.append(self._spawn())
            if self.timer <= 0:
                self._end(ev)
        return ev

    def _end(self, ev):
        ev.ended = True
        if self.mode == "solo":
            self.best = max(self.best, self.counts[0])
            if self.lb:
                self.lb.add("batde", "DE", self.counts[0], int(self.time_limit * 1000))
            self.result = f"{self.counts[0]} con Dế"
        else:
            self.winner = 0 if self.counts[0] >= self.counts[1] else 1
            if self.lb:
                self.lb.add("batde_duel", f"P{self.winner + 1}",
                            self.counts[self.winner], int(self.time_limit * 1000), won=1)
            self.result = f"P{self.winner + 1} THẮNG  ({self.counts[0]}–{self.counts[1]})"
        self.state = self.RESULT
