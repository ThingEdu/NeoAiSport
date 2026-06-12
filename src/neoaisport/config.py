"""Hằng số game + bảng màu Dế Foundation. THUẦN — không import pygame."""

# ---- Khung hình ----
W, H = 900, 600
FPS = 60

# ---- Vật lý / luật chơi ----
GRAVITY = 1500.0
FLAP_V = -420.0
BIRD_R = 16
PIPE_W = 84
PIPE_SPACING = 270
GROUND_H = 80
BASE_SPEED = 220.0
SPEED_PER_POINT = 6.0

# ---- Hứng Mưa (camera + tư thế/đầu) ----
DROP_R = 16
DROP_FALL = 250.0         # tốc độ rơi (px/s)
DROP_SPAWN = 0.55         # giây giữa các giọt
BASKET_W, BASKET_H = 130, 40
BASKET_Y = H - 96
RAIN_TIME = 45.0

# ---- Đỡ Bóng (camera + bàn tay) ----
BALL_R = 28
BALL_GRAV = 900.0
BOUNCE_V = 640.0          # vận tốc bật lên khi đỡ
HIT_R = 60                # bán kính tay chạm bóng
HIT_COOLDOWN = 0.22
FLOOR_Y = H - 40

# ---- Bắt Dế (camera + bàn tay) ----
CATCH_FLOCK = 8           # số Dế giữ trên màn (đàn = cluster)
CATCH_R = 48              # bán kính bắt (tay chạm Dế)
FLEE_R = 125              # Dế bỏ chạy khi tay tới gần
CRICKET_SPEED = 140.0     # tốc độ lang thang
CRICKET_FLEE = 330.0      # tốc độ bỏ chạy
CATCH_TIME = 45.0         # giây mỗi lượt

# ---- Đua Xe Dế (top-down lane runner) ----
CAR_W, CAR_H = 50, 78
ROAD_MARGIN = 64          # lề cỏ/nhà 2 bên trong mỗi view
STEER_SPEED = 360.0       # px/s khi cần lái = ±1
RACE_SPEED = 300.0        # tốc độ tiến (px/s)
RACE_SPEED_PER = 0.06     # solo: nhanh dần theo quãng đường
RACE_TARGET = 7200        # quãng đường về đích khi đấu (px)
RACE_STUN = 1.0           # xoay vòng khi đụng (đấu)
RACE_INVULN_EXTRA = 0.6
OBSTACLE_W, OBSTACLE_H = 48, 48
ENERGY_R = 15
SPAWN_GAP = 210           # khoảng cách dọc giữa các hàng vật thể (px)

DUEL_TARGET = 18          # số cột để về đích (đấu 2 người)
DUEL_GAP = 195            # khe cố định khi đấu (công bằng)
SOLO_GAP0 = 205           # khe ban đầu solo (hẹp dần)
SOLO_GAP_MIN = 140
STUN_TIME = 1.2          # choáng khi va chạm (đấu)
INVULN_EXTRA = 0.5       # bất tử thêm sau khi tỉnh
HIT_PUSHBACK = 70        # lùi cột khi va chạm (đấu)
COUNTDOWN = 3.0

# ---- Bảng màu Dế Foundation (DE STEM) ----
BLUE_ELECTRIC = (35, 71, 251)    # #2347FB
BLUE_WING = (104, 134, 252)
BLUE_CYAN = (148, 246, 255)      # #94F6FF
BLUE_SOFT = (216, 239, 255)      # #D8EFFF
PINK_HOT = (215, 29, 144)        # #D71D90
ORANGE_HOT = (231, 77, 30)       # #E74D1E
ORANGE_WARM = (240, 112, 32)     # #F07020
GREEN_CRICKET = (12, 112, 105)   # #0C7069
GREEN_DEEP = (9, 84, 78)
GREEN_LIME = (213, 242, 68)      # #D5F244
GREEN_SOFT = (241, 255, 211)     # #F1FFD3
INK = (18, 18, 18)
WHITE = (247, 247, 247)
