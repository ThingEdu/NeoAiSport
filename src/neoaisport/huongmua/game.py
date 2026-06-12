"""Lõi Hứng Mưa — THUẦN Python, test được.

Giọt mưa rơi từ trên; rổ ở đáy đi theo VỊ TRÍ CƠ THỂ người chơi (mũi/đầu từ Pose).
Hứng giọt = +1. Đếm giờ. solo (1 rổ) / duel (2 rổ theo trái–phải).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from neoaisport import config as C


@dataclass
class RainEvents:
    caught: list = field(default_factory=list)   # (player, x, y)
    missed: int = 0
    countdown_tick: int | None = None
    started: bool = False
    ended: bool = False


class Drop:
    __slots__ = ("x", "y", "kind")

    def __init__(self, x, kind="water"):
        self.x = float(x)
        self.y = -20.0
        self.kind = kind

    def update(self, dt):
        self.y += C.DROP_FALL * dt


class RainController:
    MENU, COUNTDOWN, PLAY, RESULT = "menu", "countdown", "play", "result"

    def __init__(self, leaderboard=None, seed=1, time_limit=C.RAIN_TIME):
        self.lb = leaderboard
        self.rng = random.Random(seed)
        self.time_limit = time_limit
        self.state = self.MENU
        self.mode = None
        self.drops: list[Drop] = []
        self.counts = [0]
        self.basket_x = [C.W / 2]
        self.timer = 0.0
        self.count = 0.0
        self._spawn_t = 0.0
        self.result = ""
        self.winner = None
        self.best = leaderboard.best("huongmua") if leaderboard else 0
        self.game_id = 0

    def start(self, mode):
        self.mode = mode
        self.game_id += 1
        self.counts = [0] if mode == "solo" else [0, 0]
        self.basket_x = [C.W / 2] if mode == "solo" else [C.W * 0.3, C.W * 0.7]
        self.drops = []
        self.timer = self.time_limit
        self.count = C.COUNTDOWN
        self._spawn_t = 0.0
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

    def _assign(self, points):
        if not points:
            return []
        if self.mode == "solo":
            return [(0, points[0])]
        order = sorted(points, key=lambda p: p[0])
        if len(order) == 1:
            return [(0 if order[0][0] < C.W / 2 else 1, order[0])]
        return [(0, order[0]), (1, order[-1])]

    def _clamp(self, x):
        return max(C.BASKET_W / 2, min(C.W - C.BASKET_W / 2, x))

    def update(self, dt, points=None) -> RainEvents:
        points = points or []
        ev = RainEvents()
        if self.state == self.COUNTDOWN:
            self.count -= dt
            ev.countdown_tick = max(1, int(self.count) + 1)
            if self.count <= 0:
                self.state = self.PLAY
                ev.started = True
            return ev
        if self.state != self.PLAY:
            return ev

        for player, (px, _py) in self._assign(points):
            self.basket_x[player] = self._clamp(px)

        self.timer -= dt
        self._spawn_t -= dt
        if self._spawn_t <= 0:
            self.drops.append(Drop(self.rng.uniform(40, C.W - 40),
                                   "energy" if self.rng.random() < 0.2 else "water"))
            self._spawn_t = C.DROP_SPAWN

        kept = []
        for d in self.drops:
            d.update(dt)
            caught = False
            if C.BASKET_Y - 18 <= d.y <= C.BASKET_Y + C.BASKET_H:
                for p in range(len(self.counts)):
                    if abs(d.x - self.basket_x[p]) < C.BASKET_W / 2 + C.DROP_R:
                        self.counts[p] += 1
                        ev.caught.append((p, d.x, d.y))
                        caught = True
                        break
            if caught:
                continue
            if d.y > C.H + 20:
                ev.missed += 1
            else:
                kept.append(d)
        self.drops = kept

        if self.timer <= 0:
            self._end(ev)
        return ev

    def _end(self, ev):
        ev.ended = True
        if self.mode == "solo":
            self.best = max(self.best, self.counts[0])
            if self.lb:
                self.lb.add("huongmua", "DE", self.counts[0], int(self.time_limit * 1000))
            self.result = f"{self.counts[0]} giọt"
        else:
            self.winner = 0 if self.counts[0] >= self.counts[1] else 1
            if self.lb:
                self.lb.add("huongmua_duel", f"P{self.winner + 1}",
                            self.counts[self.winner], int(self.time_limit * 1000), won=1)
            self.result = f"P{self.winner + 1} THẮNG  ({self.counts[0]}–{self.counts[1]})"
        self.state = self.RESULT
