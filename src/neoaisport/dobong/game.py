"""Lõi Đỡ Bóng — THUẦN Python, test được.

Bóng rơi theo trọng lực; tay chạm khi bóng đi xuống → bật bóng lên + tính 1 lần đỡ.
Bóng chạm sàn = rớt. solo: giữ càng lâu càng nhiều điểm (đỡ). duel: 2 bóng, ai rớt trước thua.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from neoaisport import config as C


@dataclass
class VolleyEvents:
    hits: list = field(default_factory=list)      # (player, x, y)
    dropped: list = field(default_factory=list)   # [player]
    countdown_tick: int | None = None
    started: bool = False
    ended: bool = False


class Ball:
    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.vx = self.vy = 0.0
        self.alive = True
        self.cooldown = 0.0

    def update(self, dt):
        if self.cooldown > 0:
            self.cooldown -= dt
        self.vy += C.BALL_GRAV * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < C.BALL_R:
            self.x, self.vx = C.BALL_R, abs(self.vx)
        elif self.x > C.W - C.BALL_R:
            self.x, self.vx = C.W - C.BALL_R, -abs(self.vx)
        if self.y < C.BALL_R:
            self.y, self.vy = C.BALL_R, abs(self.vy) * 0.5


class VolleyController:
    MENU, COUNTDOWN, PLAY, RESULT = "menu", "countdown", "play", "result"

    def __init__(self, leaderboard=None, seed=1):
        self.lb = leaderboard
        self.state = self.MENU
        self.mode = None
        self.balls: list[Ball] = []
        self.counts = [0]
        self.timer = 0.0
        self.count = 0.0
        self.result = ""
        self.winner = None
        self.best = leaderboard.best("dobong") if leaderboard else 0
        self.game_id = 0

    def start(self, mode):
        self.mode = mode
        self.game_id += 1
        if mode == "solo":
            self.counts = [0]
            self.balls = [Ball(C.W / 2, 120)]
        else:
            self.counts = [0, 0]
            self.balls = [Ball(C.W * 0.28, 120), Ball(C.W * 0.72, 120)]
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

    def _hands_for(self, i, hands):
        if self.mode == "solo":
            return hands
        return [h for h in hands if (h[0] < C.W / 2) == (i == 0)]

    def update(self, dt, points=None) -> VolleyEvents:
        hands = points or []
        ev = VolleyEvents()
        if self.state == self.COUNTDOWN:
            self.count -= dt
            ev.countdown_tick = max(1, int(self.count) + 1)
            if self.count <= 0:
                self.state = self.PLAY
                ev.started = True
            return ev
        if self.state != self.PLAY:
            return ev

        for i, ball in enumerate(self.balls):
            if not ball.alive:
                continue
            ball.update(dt)
            if ball.cooldown <= 0 and ball.vy > 0:
                for hx, hy in self._hands_for(i, hands):
                    if math.hypot(ball.x - hx, ball.y - hy) < C.HIT_R:
                        ball.vy = -C.BOUNCE_V
                        ball.vx = max(-420, min(420, ball.vx + (ball.x - hx) * 2.4))
                        ball.cooldown = C.HIT_COOLDOWN
                        self.counts[i] += 1
                        ev.hits.append((i, ball.x, ball.y))
                        break
            if ball.y > C.FLOOR_Y - C.BALL_R:
                ball.y = C.FLOOR_Y - C.BALL_R
                ball.alive = False
                ev.dropped.append(i)
        if ev.dropped:
            self._end(ev)
        return ev

    def _end(self, ev):
        ev.ended = True
        if self.mode == "solo":
            self.best = max(self.best, self.counts[0])
            if self.lb:
                self.lb.add("dobong", "DE", self.counts[0], 0)
            self.result = f"{self.counts[0]} lần đỡ"
        else:
            alive = [i for i, b in enumerate(self.balls) if b.alive]
            self.winner = alive[0] if alive else (0 if self.counts[0] >= self.counts[1] else 1)
            if self.lb:
                self.lb.add("dobong_duel", f"P{self.winner + 1}",
                            self.counts[self.winner], 0, won=1)
            self.result = f"P{self.winner + 1} THẮNG  ({self.counts[0]}–{self.counts[1]})"
        self.state = self.RESULT
