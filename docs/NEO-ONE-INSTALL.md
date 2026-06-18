# Cài đặt NeoAiSport trên NEO One

Hướng dẫn cài & chạy **NeoAiSport** (game thị giác AI bằng camera) trên **NEO One** (ARM64 / Armbian).
Đã kiểm chứng thực tế: NEO One, Armbian bookworm, aarch64, Python 3.11.2, camera `/dev/video0` — **20/20 test pass**.

> ⚠️ NeoAiSport phụ thuộc **MediaPipe + OpenCV** nên cài nặng hơn NeoArcade.
> **Phần quan trọng nhất là §4 (công thức cài "lean" cho ARM)** — phải pin đúng phiên bản
> `numpy` / `protobuf` và thêm `matplotlib`, nếu không `import mediapipe` sẽ lỗi.

---

## 1. Yêu cầu

| Mục | Giá trị |
|-----|---------|
| Thiết bị | NEO One (SoC Allwinner, ARM64 / `aarch64`) |
| Hệ điều hành | Armbian bookworm (Debian 12) |
| Python | **3.11** (mediapipe 0.10.18 có wheel `cp311` aarch64) |
| RAM | ≥ 1.5GB trống (mediapipe + opencv ~250–300MB cài) |
| Camera | webcam USB → `/dev/video0` (`ls -l /dev/video*`) |
| Màn hình | màn hình gắn trực tiếp máy NEO (X11, display `:0`) |
| Đã có sẵn trên Armbian | `git`, `pip3`, `venv`, `libsdl2-2.0-0`, `libgl1`, `gcc` |

```bash
# (nếu thiếu) thư viện hệ thống cho SDL + OpenGL
sudo apt update && sudo apt install -y python3-venv libsdl2-2.0-0 libgl1
```

---

## 2. Truy cập NEO One qua SSH (từ máy dev)

```bash
ssh neo@<IP-NEO-One>          # ví dụ: ssh neo@192.168.1.92
ssh-copy-id neo@<IP-NEO-One>  # cài key một lần (tùy chọn)
```

---

## 3. Lấy mã nguồn

**Clone từ GitHub** (repo public, MIT):

```bash
mkdir -p ~/Ai-Code && cd ~/Ai-Code
git clone https://github.com/ThingEdu/NeoAiSport.git
cd NeoAiSport
```

Hoặc **rsync bản local** từ máy dev:

```bash
# chạy trên MÁY DEV
rsync -az --delete \
  --exclude '.venv/' --exclude '.pytest_cache/' --exclude '__pycache__/' \
  ~/Ai-Code/NeoAiSport/ neo@<IP-NEO-One>:~/Ai-Code/NeoAiSport/
```

> Model AI offline (`src/neoaisport/assets/hand_landmarker.task` ~7.5MB,
> `pose_landmarker_lite.task` ~5.5MB) đi kèm repo — **không cần tải mạng** khi chạy.

---

## 4. Cài đặt — công thức "lean" cho ARM ⭐

MediaPipe trên ARM cần xử lý vài xung đột phụ thuộc. Cài theo đúng các bước sau
(đây là cách `make install-lean` mở rộng, đã thêm các bản vá đã kiểm chứng trên NEO One):

```bash
cd ~/Ai-Code/NeoAiSport
python3 -m venv .venv
.venv/bin/pip install --upgrade pip

# (1) package + pygame (KHÔNG kéo deps của mediapipe)
.venv/bin/pip install --no-deps -e .
.venv/bin/pip install "pygame-ce>=2.5"

# (2) mediapipe (không deps) + các dep runtime cần thiết, PIN đúng phiên bản
.venv/bin/pip install --no-deps mediapipe
.venv/bin/pip install \
  "numpy<2" \
  "protobuf>=4.25.3,<5" \
  matplotlib \
  opencv-contrib-python-headless \
  absl-py flatbuffers sounddevice attrs

# (3) công cụ test (tùy chọn)
.venv/bin/pip install pytest ruff
```

### Vì sao phải pin như vậy (đã gặp & xử lý trên NEO One)

| Vấn đề | Nguyên nhân | Cách xử lý |
|--------|-------------|------------|
| `ModuleNotFoundError: matplotlib` khi `import mediapipe` | `import mediapipe` kéo `mediapipe.solutions.drawing_utils` → cần matplotlib | cài `matplotlib` |
| `numpy 2.x incompatible` | mediapipe 0.10.18 yêu cầu **numpy < 2** | pin `numpy<2` (→ 1.26.x) |
| `protobuf 7.x incompatible` | mediapipe yêu cầu **protobuf 4.25.3–<5** | pin `protobuf>=4.25.3,<5` |
| numpy bị nâng lên 2.x | `jax` / `sentencepiece` kéo theo numpy mới | **KHÔNG cài** jax/sentencepiece (không cần cho Hand/Pose) |
| opencv báo "cần numpy>=2" | metadata của `opencv-contrib-python-headless` 4.13 | **bỏ qua** — `import cv2` vẫn chạy tốt với numpy 1.26 (chỉ là cảnh báo pip) |

> Dùng `opencv-contrib-python-headless` (không phải bản thường) để tránh trùng OpenCV
> mà mediapipe kéo theo, và nhẹ hơn (không kéo GUI Qt) — hợp NEO cấu hình thấp.

---

## 5. Kiểm tra cài đặt

```bash
cd ~/Ai-Code/NeoAiSport
# import OK?
.venv/bin/python -c "import pygame, cv2, mediapipe as mp; \
from mediapipe.tasks.python import vision; \
import neoaisport; print('ALL IMPORTS OK', mp.__version__)"

# test engine (headless)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m pytest -q
# Kỳ vọng: 20 passed
```

---

## 6. Chạy game

Game hiển thị trên **màn hình gắn trực tiếp máy NEO** (`:0`) và dùng **camera** `/dev/video0`.

```bash
cd ~/Ai-Code/NeoAiSport
DISPLAY=:0 .venv/bin/python -m neoaisport.hub          # màn tổng — chọn game
```

Hoặc qua Makefile (chạy ngay trên máy NEO):

```bash
make run             # màn tổng (Bắt Dế / Hứng Mưa / Đỡ Bóng)
make run-batde       # Bắt Dế bằng camera
make run-mouse       # Bắt Dế bằng chuột (khi không có webcam)
```

Thêm `--source mouse` cho game lẻ nếu chưa có camera:
`.venv/bin/python -m neoaisport.batde.app --source mouse`

---

## 7. Launcher tiện lợi (tùy chọn)

```bash
mkdir -p ~/bin
cat > ~/bin/neoaisport <<'SH'
#!/bin/bash
cd ~/Ai-Code/NeoAiSport
export DISPLAY="${DISPLAY:-:0}"
exec .venv/bin/python -m neoaisport.hub "$@"
SH
chmod +x ~/bin/neoaisport
grep -q 'HOME/bin' ~/.bashrc || echo 'export PATH="$HOME/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

Từ giờ chỉ cần gõ: `neoaisport`

---

## 8. Xử lý sự cố

| Triệu chứng | Xử lý |
|-------------|-------|
| `ModuleNotFoundError: matplotlib` (lúc import mediapipe) | Cài `matplotlib` (xem §4). |
| `numpy ... is incompatible` / mediapipe crash | Pin lại: `.venv/bin/pip install "numpy<2" "protobuf>=4.25.3,<5"`. |
| Không có wheel mediapipe | Bắt buộc **Python 3.11** (wheel `mediapipe-0.10.18-cp311-...aarch64`). Kiểm tra `python3 --version`. |
| Camera không mở | `ls -l /dev/video0`; thêm user vào nhóm video: `sudo usermod -aG video $USER` rồi đăng nhập lại; thử `--source mouse`. |
| Cửa sổ không hiện qua SSH | Đặt `DISPLAY=:0`; cần phiên X chạy trên màn hình máy (`ls /tmp/.X11-unix/` → `X0`). |
| FPS thấp / giật | Bình thường trên ARM; engine đã chạy vision ở luồng riêng + capture 640×480. Xem [`docs/NeoAiSport-Plan.md`](NeoAiSport-Plan.md) §5. |
| **Chữ tiếng Việt hiện ô trống / mất dấu** (ạ ế ổ ọ ấ ố ứ…) | Máy thiếu font phủ **Latin Extended Additional (U+1EA0+)**. Code đã tự fallback sang DejaVu/Noto; nếu vẫn lỗi: `sudo apt install -y fonts-dejavu-core fonts-noto-core`. Xem §9. |

---

## 9. Font tiếng Việt

Văn bản trong game được vẽ bằng `pygame` (`src/neoaisport/ui/sprites.py` → `font()`).
Trước đây `font()` chỉ dò các font macOS (Arial Rounded, Avenir, Nunito…); trên NEO/Linux
không có font nào khớp nên `pygame` rơi về **font mặc định `freesansbold`**, vốn **không có
khối Unicode Latin Extended Additional (U+1EA0–U+1EF9)** — đúng các chữ Việt có dấu nặng/hỏi
chồng dấu (ạ ả ấ ầ ế ệ ổ ộ ọ ố ứ…) → hiện thành ô trống (tofu).

**Cách fix trong code** (đã áp dụng): `font()` dò **file font** qua `pygame.font.match_font`
theo thứ tự — ưu tiên font bo tròn trên macOS, rồi **Noto Sans / DejaVu Sans trên Linux/NEO**
(cả hai phủ đủ chữ Việt) — và nạp bằng `pygame.font.Font(path)`. Nhờ vậy:
- **macOS**: vẫn dùng Arial Rounded / Avenir (đúng brand).
- **NEO/Linux**: tự dùng **DejaVu Sans Bold** (`fonts-dejavu-core`, có sẵn trên Armbian).

**Giữ brand bo tròn trên NEO (tùy chọn):** thả file `Nunito-Bold.ttf` (OFL, có hỗ trợ
tiếng Việt) vào `src/neoaisport/assets/`. `font()` sẽ tự ưu tiên dùng font bundled này trên
mọi máy, không cần đổi code.

Kiểm tra nhanh font có đủ chữ Việt không:

```bash
.venv/bin/python -c "import pygame; pygame.init(); \
from neoaisport.ui.sprites import font,_font_file; print('font:',_font_file()); \
m=font(24).metrics('ạếổọấốứảầ'); print('thiếu glyph?', any(x is None for x in m))"
# 'thiếu glyph? False' = OK
```

---

_Tài liệu liên quan: [`README.md`](../README.md) · [`docs/NeoAiSport-Plan.md`](NeoAiSport-Plan.md)_
