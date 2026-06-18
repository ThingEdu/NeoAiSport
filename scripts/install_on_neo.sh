#!/usr/bin/env bash
# ==============================================================================
# NeoAiSport installer — NEO App Script Convention v0 (for NEOPlay).
# Game thể thao thị giác AI (camera + tay/tư thế) trên NEO (Dế Foundation).
#
# NEOPlay chạy: bash install_on_neo.sh --version=X.Y.Z   (không TTY, user thường)
# Thủ công:     bash install_on_neo.sh --version 0.1.0
# Gỡ:           bash install_on_neo.sh --uninstall
#
# Lưu ý ARM: mediapipe 0.10.18 có wheel aarch64 cp311 nhưng cần pin numpy<2 +
# protobuf<5 + matplotlib (xem docs/NEO-ONE-INSTALL.md). Script này cài đúng "lean".
# ==============================================================================
set -euo pipefail

APP_ID="neoaisport"
DISPLAY_NAME="NeoAiSport"
MODULE="neoaisport"
GIT_REPO="https://github.com/ThingEdu/NeoAiSport.git"
BUNDLED_SRC="$HOME/Ai-Code/NeoAiSport"

APP_HOME="$HOME/Applications/$APP_ID"
VENV="$APP_HOME/venv"
BIN="$HOME/.local/bin/$APP_ID"
DESKTOP="$HOME/.local/share/applications/$APP_ID.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor/128x128/apps"
ICON_FILE="$ICON_DIR/$APP_ID.png"

VERSION=""
UNINSTALL=false
while [ $# -gt 0 ]; do
    case "$1" in
        --version=*)  VERSION="${1#*=}"; shift ;;
        --version)    VERSION="${2:-}"; shift 2 ;;
        --uninstall)  UNINSTALL=true; shift ;;
        --no-desktop) shift ;;
        *)            shift ;;
    esac
done

uninstall() {
    rm -rf "$APP_HOME" "$BIN" "$DESKTOP" "$ICON_FILE"
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    echo "$DISPLAY_NAME đã gỡ."
    exit 0
}
[ "$UNINSTALL" = true ] && uninstall

if [ -z "$VERSION" ]; then
    echo "NEOPLAY_ERROR=missing_version" >&2
    exit 1
fi

# Bắt buộc Python 3.11 (wheel mediapipe-0.10.18-cp311-...aarch64)
if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2]==(3,11) else 1)'; then
    echo "NEOPLAY_ERROR=missing_system_deps" >&2   # cần Python 3.11 để có wheel mediapipe
    exit 1
fi

# Nguồn cài: ưu tiên bundled; nếu không có thì clone GitHub (repo public, gồm model .task)
WORK=""
if [ -d "$BUNDLED_SRC/src/$MODULE" ]; then
    SRC="$BUNDLED_SRC"
    echo "Cài từ source bundled: $SRC"
else
    command -v git >/dev/null || { echo "NEOPLAY_ERROR=missing_system_deps" >&2; exit 1; }
    WORK="$(mktemp -d)"
    git clone --depth 1 "$GIT_REPO" "$WORK/NeoAiSport" >/dev/null 2>&1 \
        || { echo "NEOPLAY_ERROR=clone_failed" >&2; exit 1; }
    SRC="$WORK/NeoAiSport"
    echo "Cài từ GitHub: $GIT_REPO"
fi

# venv riêng + công thức "lean" cho ARM/NEO ---------------------------------
rm -rf "$APP_HOME"
mkdir -p "$APP_HOME"
python3 -m venv "$VENV"
PIP="$VENV/bin/pip"
"$PIP" install --quiet --upgrade pip

# (1) package + pygame, KHÔNG kéo deps của mediapipe
"$PIP" install --quiet --no-deps "$SRC"
"$PIP" install --quiet "pygame-ce>=2.5"
# (2) mediapipe (no-deps) + deps runtime, PIN numpy<2 / protobuf<5, thêm matplotlib
"$PIP" install --quiet --no-deps mediapipe
"$PIP" install --quiet \
    "numpy<2" "protobuf>=4.25.3,<5" matplotlib \
    opencv-contrib-python-headless absl-py flatbuffers sounddevice attrs

# kiểm tra import (cv2 + mediapipe.tasks + package)
if ! "$VENV/bin/python" -c "import pygame, cv2, mediapipe; from mediapipe.tasks.python import vision; import $MODULE" 2>/dev/null; then
    echo "NEOPLAY_ERROR=install_failed" >&2
    exit 1
fi

# launcher: bin venv không có console-script cho hub → wrapper gọi -m hub
mkdir -p "$(dirname "$BIN")"
cat > "$BIN" <<EOF
#!/usr/bin/env bash
exec "$VENV/bin/python" -m $MODULE.hub "\$@"
EOF
chmod +x "$BIN"

# icon
if [ -f "$SRC/src/$MODULE/assets/logo_de.png" ]; then
    mkdir -p "$ICON_DIR"
    cp "$SRC/src/$MODULE/assets/logo_de.png" "$ICON_FILE"
    ICON_REF="$ICON_FILE"
else
    ICON_REF="applications-games"
fi

# .desktop — menu desktop mục Education
mkdir -p "$(dirname "$DESKTOP")"
cat > "$DESKTOP" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$DISPLAY_NAME
GenericName=AI Vision Games
Comment=Game thể thao thị giác AI bằng camera trên NEO (Dế Foundation)
Exec=$BIN
Icon=$ICON_REF
Terminal=false
Categories=Education;
Keywords=neo;game;ai;camera;vision;maker;education;de;
StartupNotify=true
EOF
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) grep -q 'local/bin' "$HOME/.bashrc" 2>/dev/null || \
       echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc" ;;
esac

[ -n "$WORK" ] && rm -rf "$WORK"

echo "NEOPLAY_INSTALLED version=$VERSION"
