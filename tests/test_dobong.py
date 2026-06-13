"""Test lõi Đỡ Bóng (thuần)."""
import neoaisport.config as C
from neoaisport.dobong.game import VolleyController
from neoaisport.storage.db import Leaderboard


def _play(c):
    while c.state != c.PLAY:
        c.update(1 / 60)


def test_menu_starts_solo_and_duel():
    c = VolleyController()
    c.press(0)
    assert c.mode == "solo" and len(c.balls) == 1
    d = VolleyController()
    d.press(1)
    assert d.mode == "duel" and len(d.balls) == 2


def test_hand_bounces_ball_up():
    c = VolleyController()
    c.press(0)
    _play(c)
    b = c.balls[0]
    b.vy = 200
    b.cooldown = 0
    c.update(1 / 60, [(b.x, b.y)])
    assert c.counts[0] >= 1 and c.balls[0].vy < 0


def test_no_bounce_when_moving_up():
    c = VolleyController()
    c.press(0)
    _play(c)
    b = c.balls[0]
    b.vy = -100
    b.cooldown = 0
    before = c.counts[0]
    c.update(1 / 60, [(b.x, b.y)])
    assert c.counts[0] == before


def test_ball_drop_ends_solo():
    c = VolleyController()
    c.press(0)
    _play(c)
    c.balls[0].y = C.FLOOR_Y
    ev = c.update(1 / 60, [])
    assert c.state == c.RESULT and 0 in ev.dropped


def test_solo_records_best():
    lb = Leaderboard()
    c = VolleyController(leaderboard=lb)
    c.press(0)
    _play(c)
    c.counts[0] = 9
    c.balls[0].y = C.FLOOR_Y
    c.update(1 / 60, [])
    assert lb.best("dobong") >= 9


def test_duel_winner_is_surviving_player():
    c = VolleyController()
    c.press(1)
    _play(c)
    c.balls[0].y = C.FLOOR_Y          # P1 rớt
    c.update(1 / 60, [])
    assert c.state == c.RESULT and c.winner == 1


def test_duel_balls_confined_to_own_half():
    c = VolleyController()
    c.press(1)
    _play(c)
    b0, b1 = c.balls
    # mỗi bóng giới hạn trong nửa của mình (vạch giữa = tường)
    assert b0.xmax <= C.W / 2 and b1.xmin >= C.W / 2
    # bóng P1 lao sang vạch giữa → nảy lại phía mình (vx đổi sang âm), không vượt nửa
    b0.x = b0.xmax - 1
    b0.vx, b0.vy = 500, 0
    b0.update(1 / 60)
    assert b0.x <= C.W / 2 and b0.vx < 0
