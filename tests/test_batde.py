"""Test lõi Bắt Dế (thuần)."""
import random

import neoaisport.config as C
from neoaisport.batde.game import CatchController, Cricket
from neoaisport.storage.db import Leaderboard


def _play(c):
    while c.state != c.PLAY:
        c.update(1 / 60)


def test_menu_starts_solo_and_duel():
    c = CatchController()
    c.press(0)
    assert c.mode == "solo" and len(c.counts) == 1
    c2 = CatchController()
    c2.press(1)
    assert c2.mode == "duel" and len(c2.counts) == 2


def test_flock_size_on_start():
    c = CatchController()
    c.press(0)
    assert len(c.crickets) == C.CATCH_FLOCK


def test_hand_catches_and_flock_refills():
    c = CatchController()
    c.press(0)
    _play(c)
    cr = c.crickets[0]
    ev = c.update(1 / 60, [(cr.x, cr.y)])
    assert c.counts[0] >= 1
    assert any(e[0] == 0 for e in ev.caught)
    assert len(c.crickets) == C.CATCH_FLOCK


def test_cricket_flees_from_hand():
    cr = Cricket(C.W / 2, C.H / 2, random.Random(1))
    cr.update(1 / 60, [(C.W / 2 + 10, C.H / 2)])   # tay bên phải
    assert cr.x < C.W / 2                            # chạy sang trái


def test_timer_ends_to_result():
    c = CatchController(time_limit=0.05)
    c.press(0)
    _play(c)
    c.update(0.1, [])
    assert c.state == c.RESULT


def test_solo_records_best():
    lb = Leaderboard()
    c = CatchController(leaderboard=lb, time_limit=0.05)
    c.press(0)
    _play(c)
    c.counts[0] = 7
    c.update(0.1, [])
    assert c.state == c.RESULT and lb.best("batde") >= 7


def test_duel_two_hands_score_separately():
    c = CatchController()
    c.press(1)
    _play(c)
    c.crickets[0].x, c.crickets[0].y = 100, 300
    c.crickets[1].x, c.crickets[1].y = C.W - 100, 300
    for cc in c.crickets[2:]:
        cc.x, cc.y = C.W / 2, 40
    c.update(1 / 60, [(C.W - 100, 300), (100, 300)])   # đảo thứ tự → controller tự sort theo x
    assert c.counts[0] >= 1 and c.counts[1] >= 1
