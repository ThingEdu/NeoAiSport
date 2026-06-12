"""Âm thanh chip-tune tổng hợp trong bộ nhớ (không cần file). Tự tắt nếu mixer lỗi."""
from __future__ import annotations

import math
import struct

import pygame

_RATE = 22050


class SoundManager:
    def __init__(self, enabled: bool = True):
        self.ok = False
        self.snd: dict = {}
        if not enabled:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=_RATE, size=-16, channels=1)
            self.snd = {
                "flap": self._tone([(660, 0.06)], vol=0.35),
                "score": self._tone([(880, 0.05), (1180, 0.06)], vol=0.4),
                "hit": self._tone([(200, 0.12)], vol=0.5, square=True),
                "win": self._tone([(700, 0.09), (900, 0.09), (1320, 0.16)], vol=0.5),
                "count": self._tone([(520, 0.07)], vol=0.3),
            }
            self.ok = True
        except Exception:
            self.ok = False

    def _tone(self, segments, vol=0.4, square=False):
        buf = bytearray()
        amp = int(32767 * vol)
        for freq, dur in segments:
            n = int(_RATE * dur)
            for i in range(n):
                env = min(1.0, i / 80) * min(1.0, (n - i) / 400)   # fade in/out nhẹ
                if square:
                    s = amp if math.sin(2 * math.pi * freq * i / _RATE) >= 0 else -amp
                else:
                    s = amp * math.sin(2 * math.pi * freq * i / _RATE)
                buf += struct.pack("<h", int(s * env))
        return pygame.mixer.Sound(buffer=bytes(buf))

    def play(self, name: str):
        if self.ok and name in self.snd:
            self.snd[name].play()
