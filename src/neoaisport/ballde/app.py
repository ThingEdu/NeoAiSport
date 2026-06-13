"""Ball Dế — vòng lặp chính: webcam + MediaPipe Pose (bám 2 cổ chân) đá penalty.

  python -m neoaisport.ballde.app            # camera
  python -m neoaisport.ballde.app --source mouse
"""
from __future__ import annotations

import argparse
import os

import pygame

from neoaisport import config as C
from neoaisport.ballde.game import PenaltyController
from neoaisport.ballde.render import PenaltyRenderer
from neoaisport.input.vision import get_source
from neoaisport.storage.db import Leaderboard
from neoaisport.ui.sound import SoundManager


def run(source="camera", db_path="neoaisport.db", sound=True):
    pygame.init()
    screen = pygame.display.set_mode((C.W, C.H))
    pygame.display.set_caption("Ball Dế — NeoAiSport · Dế Foundation")
    clock = pygame.time.Clock()
    lb = Leaderboard(db_path)
    ctrl = PenaltyController(leaderboard=lb)
    src = get_source("foot", source)
    renderer = PenaltyRenderer(screen, source_name=src.name)
    snd = SoundManager(enabled=sound)

    prev_tick, running = None, True
    while running:
        dt = min(clock.tick(C.FPS) / 1000.0, 0.05)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key in (pygame.K_SPACE, pygame.K_w):
                    ctrl.press(0)
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    ctrl.press(1)
        bg, points = src.read()
        ev = ctrl.update(dt, points)
        if ev.shot:
            snd.play("score" if ev.shot["goal"] else "hit")
        if ev.ended:
            snd.play("win")
        if ev.countdown_tick is not None and ev.countdown_tick != prev_tick:
            snd.play("count")
        prev_tick = ev.countdown_tick
        renderer.draw(ctrl, ev, lb, dt, bg=bg, points=points)
        pygame.display.flip()
    src.close()
    lb.close()
    pygame.quit()


def main():
    ap = argparse.ArgumentParser(description="Ball Dế — NeoAiSport")
    ap.add_argument("--source", default="camera", choices=["camera", "mouse"])
    ap.add_argument("--db", default=os.environ.get("NEOAISPORT_DB", "neoaisport.db"))
    ap.add_argument("--no-sound", action="store_true")
    args = ap.parse_args()
    run(source=args.source, db_path=args.db, sound=not args.no_sound)


if __name__ == "__main__":
    main()
