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
import time

import pygame

from neoaisport import config as C

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
_HAND_MODEL = os.path.join(_ASSETS, "hand_landmarker.task")
_POSE_MODEL = os.path.join(_ASSETS, "pose_landmarker_lite.task")

CAP_W, CAP_H = 640, 480     # độ phân giải bắt (nhẹ cho ARM); toạ độ chuẩn hoá nên không lệch
EMA = 0.5                   # hệ số làm mượt (cao = bám nhanh, thấp = mượt)
HOLD_FRAMES = 8             # giữ vị trí khi mất nhận diện thoáng qua


def _camera_candidates(cam: int | None) -> list[int]:
    """Danh sách index camera cần thử. cam cố định > env NEOAISPORT_CAM > các /dev/video* CÓ THẬT."""
    if cam is not None:
        return [cam]
    env = os.environ.get("NEOAISPORT_CAM", "")
    if env.strip().lstrip("-").isdigit():
        return [int(env)]
    import glob
    nums = sorted({int("".join(filter(str.isdigit, os.path.basename(p))) or -1)
                   for p in glob.glob("/dev/video*")})
    nums = [n for n in nums if n >= 0]
    return nums or [0]          # không có /dev/video* (vd macOS) → thử 0


def _open_camera(cv2, cam: int | None):
    """Mở webcam, trả (cap, index) hoặc (None, None).

    Trên NEO/Linux camera thật có thể KHÔNG ở index 0 (các node /dev/video phụ:
    metadata, obsensor…). Ta **ép backend V4L2** để mở nhanh + tránh backend obsensor dò
    chậm (nguyên nhân camera "lên chậm"), và chỉ thử các /dev/video* có thật.
    """
    backend = getattr(cv2, "CAP_V4L2", 0)
    for idx in _camera_candidates(cam):
        cap = cv2.VideoCapture(idx, backend) if backend else cv2.VideoCapture(idx)
        if cap.isOpened():
            ok, frame = cap.read()
            if ok and frame is not None:
                return cap, idx
        cap.release()
    return None, None


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

    def __init__(self, cam: int | None = None):
        import cv2
        self.cv2 = cv2
        self.cap, self.cam_index = _open_camera(cv2, cam)
        if self.cap is None:
            raise RuntimeError("Không mở được webcam (đã dò các /dev/video*)")
        # MJPG + 640×480 + buffer 1: USB nhẹ hơn, KHÔNG giữ frame cũ → giảm trễ/lác trên ARM.
        try:
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        except Exception:
            pass
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_H)
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception:
            pass
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
        self._latest_rgb = None          # frame mới nhất cho luồng nhận diện
        self._latest_rgb_id = 0
        self._cap_thread = None
        self._det_thread = None

    def _start(self):
        # 2 LUỒNG tách biệt: chụp (nhanh, đẩy hình mượt) + nhận diện (chậm, không khoá hình).
        self._cap_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._det_thread = threading.Thread(target=self._detect_loop, daemon=True)
        self._cap_thread.start()
        self._det_thread.start()

    def _build(self):
        raise NotImplementedError

    def _detect(self, landmarker, mp_img, ts):
        raise NotImplementedError

    def _capture_loop(self):
        """Chụp + đẩy hình webcam NGAY (không chờ MediaPipe) → nền mượt ~tốc độ camera."""
        cv2 = self.cv2
        while not self._stop:
            ok, frame = self.cap.read()
            if not ok:
                continue
            frame = cv2.flip(frame, 1)       # soi gương
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            disp = cv2.resize(rgb, (C.W, C.H))
            with self._lock:
                self._frame_bytes = disp.tobytes()
                self._fid += 1
                self._latest_rgb = rgb        # giao cho luồng nhận diện (frame mới nhất)
                self._latest_rgb_id = self._fid

    def _detect_loop(self):
        """Nhận diện MediaPipe ở luồng riêng trên frame mới nhất; chậm cũng KHÔNG làm khựng hình."""
        import mediapipe as mp
        landmarker = self._build()          # tạo trong chính luồng dùng (Tasks an toàn 1 luồng)
        ts = 0
        last_id = -1
        while not self._stop:
            with self._lock:
                rgb = self._latest_rgb
                rid = self._latest_rgb_id
            if rgb is None or rid == last_id:
                time.sleep(0.005)            # chưa có frame mới → nhường CPU
                continue
            last_id = rid
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts += int(1000 / C.FPS)
            try:
                pts = self._detect(landmarker, mp_img, ts)
            except Exception:
                pts = []
            with self._lock:
                self._pts_raw = pts
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
        for t in (self._cap_thread, self._det_thread):
            if t:
                t.join(timeout=1.0)
        try:
            self.cap.release()
        except Exception:
            pass


class HandCamera(_CameraBase):
    def __init__(self, max_hands: int = 2, cam: int | None = None):
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
    def __init__(self, max_bodies: int = 2, cam: int | None = None, landmarks=(0,)):
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
                # chuỗi 2 chân để VẼ khung + bám bàn chân:
                # [hôngA, gốiA, cổ chânA, bàn chânA, hôngB, gốiB, cổ chânB, bàn chânB]
                return PoseCamera(max_bodies=1, landmarks=(23, 25, 27, 31, 24, 26, 28, 32))
            return PoseCamera(max_bodies=count)               # pose (mũi/đầu)
        except Exception as exc:
            print(f"[vision] {exc} → fallback chuột")
    return MouseHands()


def get_hand_source(prefer: str = "camera", max_hands: int = 2):   # tương thích cũ
    return get_source("hand", prefer, max_hands)
