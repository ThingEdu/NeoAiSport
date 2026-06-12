"""Nguồn 'điểm cơ thể' cho game thị giác.

  HandCamera : webcam + MediaPipe HandLandmarker → đầu ngón trỏ (mỗi tay 1 điểm).
  PoseCamera : webcam + MediaPipe PoseLandmarker → mũi/đầu (mỗi người 1 điểm).
  MouseHands : fallback dev/không camera — con trỏ chuột làm 1 điểm.

read() → (bg_surface | None, points)  với points = list[(x, y)] trong hệ C.W×C.H.
get_source(kind="hand"|"pose") tự fallback chuột nếu không có camera.
"""
from __future__ import annotations

import os

import pygame

from neoaisport import config as C

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
_HAND_MODEL = os.path.join(_ASSETS, "hand_landmarker.task")
_POSE_MODEL = os.path.join(_ASSETS, "pose_landmarker_lite.task")


class MouseHands:
    name = "mouse"
    has_camera = False

    def read(self):
        mx, my = pygame.mouse.get_pos()
        return None, [(float(mx), float(my))]

    def close(self):
        pass


class _CameraBase:
    """Mở webcam + đọc khung (soi gương) + dựng surface pygame. Lớp con cài _detect()."""
    name = "camera"
    has_camera = True

    def __init__(self, cam: int = 0):
        # Import cv2/mediapipe Ở ĐÂY (sau pygame.init()) → SDL pygame nạp trước (cảnh báo macOS vô hại).
        import cv2
        import mediapipe as mp
        self.cv2 = cv2
        self.mp = mp
        self.cap = cv2.VideoCapture(cam)
        if not self.cap.isOpened():
            raise RuntimeError("Không mở được webcam")
        self._ts = 0

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            return None, []
        frame = self.cv2.flip(frame, 1)                      # soi gương (selfie)
        rgb = self.cv2.cvtColor(frame, self.cv2.COLOR_BGR2RGB)
        mp_img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
        self._ts += int(1000 / C.FPS)
        points = self._detect(mp_img)
        surf = pygame.image.frombuffer(rgb.tobytes(), (rgb.shape[1], rgb.shape[0]), "RGB")
        if surf.get_size() != (C.W, C.H):
            surf = pygame.transform.smoothscale(surf, (C.W, C.H))
        return surf, points

    def _detect(self, mp_img):
        raise NotImplementedError

    def close(self):
        try:
            self.cap.release()
            self.landmarker.close()
        except Exception:
            pass


class HandCamera(_CameraBase):
    def __init__(self, max_hands: int = 2, cam: int = 0):
        super().__init__(cam)
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
        if not os.path.exists(_HAND_MODEL):
            raise RuntimeError(f"Thiếu model {_HAND_MODEL}")
        self.landmarker = vision.HandLandmarker.create_from_options(
            vision.HandLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=_HAND_MODEL),
                running_mode=vision.RunningMode.VIDEO, num_hands=max_hands))

    def _detect(self, mp_img):
        res = self.landmarker.detect_for_video(mp_img, self._ts)
        return [(lm[8].x * C.W, lm[8].y * C.H) for lm in res.hand_landmarks]   # đầu ngón trỏ


class PoseCamera(_CameraBase):
    def __init__(self, max_bodies: int = 2, cam: int = 0):
        super().__init__(cam)
        from mediapipe.tasks import python as mp_python
        from mediapipe.tasks.python import vision
        if not os.path.exists(_POSE_MODEL):
            raise RuntimeError(f"Thiếu model {_POSE_MODEL}")
        self.landmarker = vision.PoseLandmarker.create_from_options(
            vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=_POSE_MODEL),
                running_mode=vision.RunningMode.VIDEO, num_poses=max_bodies))

    def _detect(self, mp_img):
        res = self.landmarker.detect_for_video(mp_img, self._ts)
        return [(p[0].x * C.W, p[0].y * C.H) for p in res.pose_landmarks]      # mũi (đầu)


def get_source(kind: str = "hand", prefer: str = "camera", count: int = 2):
    """kind='hand' (tay) | 'pose' (tư thế/đầu). Fallback chuột nếu không có camera."""
    if prefer == "camera":
        try:
            return HandCamera(max_hands=count) if kind == "hand" else PoseCamera(max_bodies=count)
        except Exception as exc:
            print(f"[vision] {exc} → fallback chuột")
    return MouseHands()


def get_hand_source(prefer: str = "camera", max_hands: int = 2):   # tương thích cũ (Bắt Dế)
    return get_source("hand", prefer, max_hands)
