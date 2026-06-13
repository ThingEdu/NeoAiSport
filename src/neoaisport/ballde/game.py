"""Lõi Ball Dế (đá penalty) — THUẦN Python, test được.

AI bám 2 cổ chân (Pose). Phát hiện cú sút = chân dịch nhanh (> KICK_DIST mỗi bước);
HƯỚNG sút theo hướng chân vung: trái / phải / giữa. Thủ môn bay ngẫu nhiên 1 hướng;
sút khác hướng thủ môn = BÀN. Mỗi người PEN_SHOTS lượt.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from neoaisport import config as C

DIRS = ("L", "C", "R")
# Chỉ số bàn chân trong chuỗi 8 điểm chân [hôngA,gốiA,cổchânA,bànchânA, hôngB,...]
FOOT_IDX = (3, 7)


def feet_of(pts):
    """Lấy 2 bàn chân từ chuỗi chân (8 điểm). Fallback chuột: trả nguyên (1 điểm)."""
    if len(pts) >= 8:
        return [pts[FOOT_IDX[0]], pts[FOOT_IDX[1]]]
    return list(pts)


@dataclass
class PenaltyEvents:
    shot: dict | None = None      # {"player","kick","keeper","goal"} khi 1 cú sút kết thúc
    countdown_tick: int | None = None
    started: bool = False
    ended: bool = False


class PenaltyController:
    MENU, COUNTDOWN, PLAY, RESULT = "menu", "countdown", "play", "result"

    def __init__(self, leaderboard=None, seed=1):
        self.lb = leaderboard
        self.rng = random.Random(seed)
        self.state = self.MENU
        self.mode = None
        self.goals = [0]
        self.shots_done = [0]
        self.cur = 0
        self.phase = "ready"          # ready | shot
        self.shot_timer = 0.0
        self.ball_t = 0.0
        self.kick_dir = "C"
        self.keeper_dir = "C"
        self.scored = False
        self.count = 0.0
        self.result = ""
        self.winner = None
        self.best = leaderboard.best("ballde") if leaderboard else 0
        self.game_id = 0
        self._prev: list = []

    def _total(self):
        return C.PEN_SHOTS if self.mode == "solo" else C.PEN_SHOTS * 2

    def start(self, mode):
        self.mode = mode
        self.game_id += 1
        self.goals = [0] if mode == "solo" else [0, 0]
        self.shots_done = [0] if mode == "solo" else [0, 0]
        self.cur = 0
        self.phase = "ready"
        self.shot_timer = 0.0
        self.ball_t = 0.0
        self.result = ""
        self.winner = None
        self._prev = []
        self.count = C.COUNTDOWN
        self.state = self.COUNTDOWN

    def press(self, btn):
        if btn not in (0, 1):
            return
        if self.state == self.MENU:
            self.start("solo" if btn == 0 else "duel")
        elif self.state == self.RESULT:
            self.start(self.mode) if btn == 0 else setattr(self, "state", self.MENU)

    def _kick(self, dx):
        self.kick_dir = "L" if dx < -C.KICK_DIR_DX else ("R" if dx > C.KICK_DIR_DX else "C")
        self.keeper_dir = self.rng.choice(DIRS)
        self.scored = self.kick_dir != self.keeper_dir
        self.phase = "shot"
        self.shot_timer = C.SHOT_TIME
        self.ball_t = 0.0

    def update(self, dt, points=None) -> PenaltyEvents:
        pts = points or []
        ev = PenaltyEvents()
        if self.state == self.COUNTDOWN:
            self.count -= dt
            ev.countdown_tick = max(1, int(self.count) + 1)
            if self.count <= 0:
                self.state = self.PLAY
                ev.started = True
            return ev
        if self.state != self.PLAY:
            return ev

        cur = sorted(feet_of(pts), key=lambda p: p[0])
        if self.phase == "ready":
            best_move, best_dx = 0.0, 0.0
            for i, p in enumerate(cur):
                if i < len(self._prev):
                    dx = p[0] - self._prev[i][0]
                    dy = p[1] - self._prev[i][1]
                    move = math.hypot(dx, dy)
                    if move > best_move:
                        best_move, best_dx = move, dx
            if best_move > C.KICK_DIST:
                self._kick(best_dx)
        else:
            self.shot_timer -= dt
            self.ball_t = min(1.0, 1 - self.shot_timer / C.SHOT_TIME)
            if self.shot_timer <= 0:
                if self.scored:
                    self.goals[self.cur] += 1
                self.shots_done[self.cur] += 1
                ev.shot = {"player": self.cur, "kick": self.kick_dir,
                           "keeper": self.keeper_dir, "goal": self.scored}
                self.phase = "ready"
                if sum(self.shots_done) >= self._total():
                    self._end(ev)
                elif self.mode == "duel":
                    self.cur = 1 - self.cur
        self._prev = cur
        return ev

    def _end(self, ev):
        ev.ended = True
        if self.mode == "solo":
            self.best = max(self.best, self.goals[0])
            if self.lb:
                self.lb.add("ballde", "DE", self.goals[0], 0)
            self.result = f"{self.goals[0]}/{C.PEN_SHOTS} bàn"
        else:
            self.winner = 0 if self.goals[0] >= self.goals[1] else 1
            if self.lb:
                self.lb.add("ballde_duel", f"P{self.winner + 1}", self.goals[self.winner], 0, won=1)
            self.result = f"P{self.winner + 1} THẮNG  ({self.goals[0]}–{self.goals[1]})"
        self.state = self.RESULT
