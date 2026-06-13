# NeoAiSport — Phân tích & Quy hoạch

> Nền tảng **game thể thao thị giác AI**: người chơi dùng **cơ thể** (bàn tay, cử chỉ,
> khuôn mặt, đầu, tư thế) tương tác qua **camera** — không cần tay cầm. Cùng vũ trụ
> **Dế Foundation** với NeoArcade & DeBlue. Cập nhật: 2026-06-13.

## 1. Vì sao tách khỏi NeoArcade

| | NeoArcade | **NeoAiSport** |
|---|---|---|
| Điều khiển | ThingBot/nút/cần lái (vật lý) | **camera + cơ thể** (AI thị giác) |
| Ngăn xếp | pygame (nhẹ ~50–80MB) | pygame + **opencv + mediapipe + model** (~250–300MB) |
| Phần cứng | NEO + ThingBot | NEO + **webcam** |
| Quyền | không | **Camera** |
| Máy NEO yếu | chạy thoải mái | **cần verify** (xem §5) |

→ Nhồi chung làm NeoArcade nặng + xin quyền camera thừa cho cả bộ. **Tách riêng**: NeoArcade
nhẹ/ổn; NeoAiSport gom thị giác AI với **repo + domain + stack riêng**, cập nhật độc lập.

## 2. Định vị
3 cửa vào thế giới Dế Foundation: **NeoArcade** (vận động + điều khiển vật lý) ·
**NeoAiSport** (vận động + thị giác AI) · **DeBlue** (tư duy Blue Economy). Mascot con Dế xuyên suốt.

## 3. Ngăn xếp công nghệ
- **Render**: pygame-ce.
- **Thị giác (MediaPipe Tasks API)**: `HandLandmarker` (tay ✅) · `PoseLandmarker` (đầu/thân/tư thế) ·
  `FaceLandmarker` (mặt) · `GestureRecognizer` (cử chỉ). `opencv` đọc webcam.
- **Lớp `vision`**: chuẩn hoá khung hình + toạ độ (tay/khớp/mặt) → game chỉ nhận toạ độ,
  **đổi mô hình AI không sửa game** (giống cách `input` ở NeoArcade).
- **storage** SQLite leaderboard · **brand kit** Dế Foundation (mascot/palette/font) dùng chung.

## 4. Danh mục game (roadmap)
| Game | Mô hình AI | Vận động | Trạng thái |
|---|---|---|---|
| **Bắt Dế** | HandLandmarker | vẫy tay bắt đàn Dế | ✅ |
| **Hứng Mưa** | PoseLandmarker (đầu/thân) | nghiêng người hứng giọt mưa | ✅ |
| **Đỡ Bóng** | HandLandmarker | vung tay giữ bóng trên không (thể thao) | ✅ |
| **Ball Dế** | PoseLandmarker (2 cổ chân) | đá penalty trái/phải/giữa theo hướng chân vung | ✅ |
| **Mặt Cười** | FaceLandmarker | há miệng/biểu cảm điều khiển | 🔜 |
| **Oẳn Tù Tì / vẫy tay** | GestureRecognizer | cử chỉ tay | 🔜 |
| **Trò chơi dân gian camera** | Pose/Hand | nhảy dây ảo, rồng rắn, vẫy bắt… | 💡 |

## 5. Triển khai trên NEO One (ARM cấu hình thấp) — phân tích rủi ro

Số đo thật (build tham chiếu):
- **Dung lượng cài**: Bắt Dế ~250–300MB (opencv ~120M, mediapipe 53M, matplotlib 33M, numpy 33M,
  pygame 51M, model 8M). _Lưu ý_: `mediapipe` **ép `opencv-contrib-python`** → dễ **trùng 2 bản opencv**.
  Cài "lean" (`make install-lean`: `--no-deps` + `opencv-contrib-python-headless`) để **bỏ ~120M** & 1 bản opencv.
- **RAM**: nạp pygame+cv2+mediapipe+model đo được **~228MB** → **2GB thừa sức, KHÔNG treo vì RAM**.
- **CPU/fps**: đây là rủi ro chính — ARM yếu chạy mediapipe + giải mã + scale frame 30fps dễ tụt
  **~8–15fps (lag, hiếm khi treo cứng)**. Giảm tải:
  - capture **640×480**, dùng `cv2.resize` thay `pygame.smoothscale`;
  - chạy vision ở **luồng riêng** + **bỏ qua frame** (nhận tay ~15fps, vẽ 60fps);
  - model **lite** + `num_hands` tối thiểu.
- **Rủi ro #1 — wheel `mediapipe` cho aarch64 Linux**: PyPI trước nay hay thiếu. **Phải thử
  `pip install mediapipe` ngay trên NEO**. Nếu không cài được → tìm wheel ARM dựng sẵn, hoặc
  **fallback bắt tay bằng OpenCV thuần** (skin/motion blob, bỏ mediapipe).
- _Cảnh báo macOS_ `Class SDL... implemented in both` (cv2+pygame) **chỉ có trên macOS** (objc),
  **không xảy ra trên Linux ARM** — vô hại.

## 6. Repo · domain · hạ tầng
- **Repo riêng**: `github.com/ThingEdu/NeoAiSport` (private).
- **Domain đề xuất**: `neoaisport.*` (vd `neoaisport.thingedu.vn`) — landing giới thiệu, hướng dẫn
  quyền camera, tải/cập nhật app, video demo.
- **Stack riêng**: package `neoaisport`, venv riêng (deps nặng), CI riêng, đóng gói NEO riêng.
- **Brand kit**: hiện **vendor** (sao chép) mascot/palette/font/widgets từ Dế Foundation để tự chứa;
  sau có thể tách `thing-brand-kit` chung cho cả NeoArcade/NeoAiSport.

## 7. Quan hệ với NeoArcade / NeoPlay
- Trên **NeoPlay**: NeoArcade và NeoAiSport là **2 entry riêng**. Máy yếu / không camera → chỉ cài
  NeoArcade. Máy có webcam + đủ sức → cài thêm NeoAiSport.

## 8. Lộ trình
1. ✅ Tách repo NeoAiSport, chuyển **Bắt Dế** sang, hub game thị giác.
2. ✅ **Hứng Mưa** (Pose) + **Đỡ Bóng** (Hand) — 3 game thị giác, hub đủ 3 thẻ, 19 test.
3. 🔜 Verify `mediapipe` trên NEO ARM + **chế độ ARM** (640×480, luồng riêng, frame-skip) + fallback OpenCV.
4. 🔜 Face/Gesture games + trò chơi dân gian camera.
5. 🔜 Landing domain + đóng gói NeoPlay (entry riêng).
