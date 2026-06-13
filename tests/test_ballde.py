"""Test lõi Ball Dế (đá penalty, hướng theo chân)."""
import neoaisport.config as C
from neoaisport.ballde.game import PenaltyController


def _play(c):
    while c.state != c.PLAY:
        c.update(1 / 60)


def test_menu_starts_solo_and_duel():
    c = PenaltyController()
    c.press(0)
    assert c.mode == "solo" and len(c.goals) == 1
    d = PenaltyController()
    d.press(1)
    assert d.mode == "duel" and len(d.goals) == 2


def test_kick_left():
    c = PenaltyController()
    c.press(0)
    _play(c)
    c._prev = [(450, 400)]
    c.update(1 / 60, [(300, 400)])          # dịch trái mạnh
    assert c.phase == "shot" and c.kick_dir == "L"


def test_kick_right():
    c = PenaltyController()
    c.press(0)
    _play(c)
    c._prev = [(450, 400)]
    c.update(1 / 60, [(650, 400)])
    assert c.kick_dir == "R"


def test_kick_center_on_forward_swing():
    c = PenaltyController()
    c.press(0)
    _play(c)
    c._prev = [(450, 400)]
    c.update(1 / 60, [(450, 250)])          # dịch dọc, ngang ~0 → giữa
    assert c.phase == "shot" and c.kick_dir == "C"


def test_small_move_no_kick():
    c = PenaltyController()
    c.press(0)
    _play(c)
    c._prev = [(450, 400)]
    c.update(1 / 60, [(468, 408)])          # dịch nhỏ < ngưỡng
    assert c.phase == "ready"


def test_shot_resolves_and_counts():
    c = PenaltyController(seed=1)
    c.press(0)
    _play(c)
    c._prev = [(450, 400)]
    c.update(1 / 60, [(300, 400)])
    for _ in range(int(C.SHOT_TIME * 60) + 4):
        c.update(1 / 60, [(300, 400)])
        if c.shots_done[0] >= 1:
            break
    assert c.shots_done[0] == 1


def test_solo_ends_after_all_shots():
    c = PenaltyController(seed=2)
    c.press(0)
    _play(c)
    for _ in range(C.PEN_SHOTS):
        c._prev = [(450, 400)]
        c.update(1 / 60, [(300, 400)])
        for _ in range(int(C.SHOT_TIME * 60) + 4):
            c.update(1 / 60, [(300, 400)])
            if c.phase == "ready" or c.state == c.RESULT:
                break
    assert c.state == c.RESULT
