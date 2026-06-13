"""Nguồn 'điểm cơ thể' cho game thị giác — TỐI ƯU cho NEO ARM + cảm giác chơi.

Tối ưu chung cho cả 3 game:
  • Bắt webcam 640×480 + cv2.resize (nhẹ CPU hơn smoothscale).
  • Camera + MediaPipe chạy LUỒNG RIÊNG → vòng lặp vẽ 60fps không khựng khi inference chậm.
  • Làm mượt điểm (EMA) + giữ vị trí ~0.13s khi mất nhận diện → hết giật.

  HandCamera : HandLandmarker → đầu ngón trỏ (mỗi tay 1 điểm).
  PoseCamera : PoseLandmarker → mũi/đầu (mỗi người 1 điểm).
  MouseHands : fallback không camera — con trỏ chuột.

read() → (bg_surface | None, points)  với points = list[(x, y)] trong hệ C.W×C.H.
"""
from __future__ import annotations

import os
import threading

import pygame

from neoaisport import config as C

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
_HAND_MODEL = os.path.join(_ASSETS, "hand_landmarker.task")
_POSE_MODEL = os.path.join(_ASSETS, "pose_landmarker_lite.task")

CAP_W, CAP_H = 640, 480     # độ phân giải bắt (nhẹ cho ARM); toạ độ chuẩn hoá nên không lệch
EMA = 0.5                   # hệ số làm mượt (cao = bám nhanh, thấp = mượt)
HOLD_FRAMES = 8             # giữ vị trí khi mất nhận diện thoáng qua


class MouseHands:
    name = "mouse"
    has_camera = False

    def read(self):
        mx, my = pygame.mouse.get_pos()
        return None, [(float(mx), float(my))]

    def close(self):
        pass


class _CameraBase:
    """Bắt webcam + MediaPipe ở luồng riêng; read() lấy kết quả mới nhất, không chặn."""
    name = "camera"
    has_camera = True

    def __init__(self, cam: int = 0):
        import cv2
        self.cv2 = cv2
        self.cap = cv2.VideoCapture(cam)
        if not self.cap.isOpened():
            raise RuntimeError("Không mở được webcam")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_H)
        self._lock = threading.Lock()
        self._frame_bytes = None
        self._pts_raw: list = []
        self._fid = 0
        self._last_fid = -1
        self._surf = None
        self._pts: list = []
        self._prev: list = []
        self._hold = 0
        self._stop = False
        self._thread = None

    def _start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _build(self):
        raise NotImplementedError

    def _detect(self, landmarker, mp_img, ts):
        raise NotImplementedError

    def _loop(self):
        import mediapipe as mp
        cv2 = self.cv2
        landmarker = self._build()          # tạo trong luồng worker (mediapipe Tasks an toàn 1 luồng)
        ts = 0
        while not self._stop:
            ok, frame = self.cap.read()
            if not ok:
                continue
            frame = cv2.flip(frame, 1)       # soi gương
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts += int(1000 / C.FPS)
            try:
                pts = self._detect(landmarker, mp_img, ts)
            except Exception:
                pts = []
            disp = cv2.resize(rgb, (C.W, C.H))
            b = disp.tobytes()
            with self._lock:
                self._frame_bytes = b
                self._pts_raw = pts
                self._fid += 1
        landmarker.close()

    def read(self):
        with self._lock:
            fid, b, raw = self._fid, self._frame_bytes, list(self._pts_raw)
        if b is None:
            return None, []
        if fid != self._last_fid:
            self._surf = pygame.image.frombuffer(b, (C.W, C.H), "RGB")
            self._last_fid = fid
            self._pts = self._smooth(raw)
        return self._surf, self._pts

    def _smooth(self, raw):
        if not raw:
            if self._prev and self._hold > 0:
                self._hold -= 1
                return self._prev
            self._prev = []
            return []
        self._hold = HOLD_FRAMES
        cur = sorted(raw, key=lambda p: p[0])
        if len(cur) == len(self._prev):
            out = [(EMA * c[0] + (1 - EMA) * p[0], EMA * c[1] + (1 - EMA) * p[1])
                   for c, p in zip(cur, self._prev)]
        else:
            out = cur
        self._prev = out
        return out

    def close(self):
        self._stop = True
        if self._thread:
            self._thread.join(timeout=1.0)
        try:
            self.cap.release()
        except Exception:
            pass


class HandCamera(_CameraBase):
    def __init__(self, max_hands: int = 2, cam: int = 0):
        super().__init__(cam)
        self._n = max_hands
        if not os.path.exists(_HAND_MODEL):
            raise RuntimeError(f"Thiếu model {_HAND_MODEL}")
        self._start()

    def _build(self):
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
        return vision.HandLandmarker.create_from_options(
            vision.HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=_HAND_MODEL),
                running_mode=vision.RunningMode.VIDEO, num_hands=self._n))

    def _detect(self, lm, mp_img, ts):
        res = lm.detect_for_video(mp_img, ts)
        return [(h[8].x * C.W, h[8].y * C.H) for h in res.hand_landmarks]      # đầu ngón trỏ


class PoseCamera(_CameraBase):
    # landmarks Pose: 0 = mũi (đầu); 27/28 = cổ chân trái/phải
    def __init__(self, max_bodies: int = 2, cam: int = 0, landmarks=(0,)):
        super().__init__(cam)
        self._n = max_bodies
        self._lms = landmarks
        if not os.path.exists(_POSE_MODEL):
            raise RuntimeError(f"Thiếu model {_POSE_MODEL}")
        self._start()

    def _build(self):
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
        return vision.PoseLandmarker.create_from_options(
            vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=_POSE_MODEL),
                running_mode=vision.RunningMode.VIDEO, num_poses=self._n))

    def _detect(self, lm, mp_img, ts):
        res = lm.detect_for_video(mp_img, ts)
        return [(pose[i].x * C.W, pose[i].y * C.H)
                for pose in res.pose_landmarks for i in self._lms]


def get_source(kind: str = "hand", prefer: str = "camera", count: int = 2):
    """kind='hand' (tay) | 'pose' (đầu) | 'foot' (2 cổ chân). Fallback chuột nếu không có camera."""
    if prefer == "camera":
        try:
            if kind == "hand":
                return HandCamera(max_hands=count)
            if kind == "foot":
                return PoseCamera(max_bodies=1, landmarks=(27, 28))
            return PoseCamera(max_bodies=count)               # pose (mũi/đầu)
        except Exception as exc:
            print(f"[vision] {exc} → fallback chuột")
    return MouseHands()


def get_hand_source(prefer: str = "camera", max_hands: int = 2):   # tương thích cũ
    return get_source("hand", prefer, max_hands)
