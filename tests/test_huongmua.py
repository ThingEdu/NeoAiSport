"""Test lõi Hứng Mưa (thuần)."""
import neoaisport.config as C
from neoaisport.huongmua.game import Drop, RainController
from neoaisport.storage.db import Leaderboard


def _play(c):
    while c.state != c.PLAY:
        c.update(1 / 60)


def test_menu_starts_solo_and_duel():
    c = RainController()
    c.press(0)
    assert c.mode == "solo" and len(c.counts) == 1 and len(c.basket_x) == 1
    d = RainController()
    d.press(1)
    assert d.mode == "duel" and len(d.counts) == 2 and len(d.basket_x) == 2


def test_basket_follows_body():
    c = RainController()
    c.press(0)
    _play(c)
    c.update(1 / 60, [(200, 300)])
    assert abs(c.basket_x[0] - 200) < 1


def test_catch_drop_increments():
    c = RainController()
    c.press(0)
    _play(c)
    d = Drop(c.basket_x[0])
    d.y = C.BASKET_Y
    c.drops = [d]
    c.update(1 / 60, [(c.basket_x[0], 300)])
    assert c.counts[0] >= 1


def test_miss_counts_when_basket_far():
    c = RainController()
    c.press(0)
    _play(c)
    c.basket_x[0] = 100
    d = Drop(800)
    d.y = C.H + 25
    c.drops = [d]
    ev = c.update(1 / 60, [(100, 300)])
    assert ev.missed >= 1 and c.counts[0] == 0


def test_timer_ends_to_result():
    c = RainController(time_limit=0.05)
    c.press(0)
    _play(c)
    c.update(0.1, [])
    assert c.state == c.RESULT


def test_solo_records_best():
    lb = Leaderboard()
    c = RainController(leaderboard=lb, time_limit=0.05)
    c.press(0)
    _play(c)
    c.counts[0] = 8
    c.update(0.1, [])
    assert lb.best("huongmua") >= 8
