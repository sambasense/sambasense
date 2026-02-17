#!/bin/bash
# Build SambaSense AppImage
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PKG_VERSION="1.1.0"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building SambaSense AppImage"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BUILD_DIR="$SCRIPT_DIR/build"
APPDIR="$BUILD_DIR/SambaSense.AppDir"

# Clean
rm -rf "$BUILD_DIR"
mkdir -p "$APPDIR"

# Download tools if needed
LINUXDEPLOY="$BUILD_DIR/linuxdeploy-x86_64.AppImage"
APPIMAGETOOL="$BUILD_DIR/appimagetool-x86_64.AppImage"

if [ ! -f "$LINUXDEPLOY" ]; then
    echo "Downloading linuxdeploy..."
    wget -q "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage" \
         -O "$LINUXDEPLOY"
    chmod +x "$LINUXDEPLOY"
fi

# Create AppDir structure
mkdir -p "$APPDIR/usr/bin"
mkdir -p "$APPDIR/usr/lib/python3/dist-packages"
mkdir -p "$APPDIR/usr/share/applications"
mkdir -p "$APPDIR/usr/share/icons/hicolor/scalable/apps"

# Copy application
cp -r "$PROJECT_ROOT/sambasense" "$APPDIR/usr/lib/python3/dist-packages/"

# Create launcher
cat > "$APPDIR/usr/bin/sambasense" << 'LAUNCHER'
#!/bin/bash
SELF_DIR="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="$SELF_DIR/../lib/python3/dist-packages:$PYTHONPATH"
exec python3 -m sambasense "$@"
LAUNCHER
chmod +x "$APPDIR/usr/bin/sambasense"

# AppRun
cat > "$APPDIR/AppRun" << 'APPRUN'
#!/bin/bash
SELF="$(readlink -f "$0")"
HERE="$(dirname "$SELF")"
export PATH="$HERE/usr/bin:$PATH"
export PYTHONPATH="$HERE/usr/lib/python3/dist-packages:$PYTHONPATH"
exec python3 -m sambasense "$@"
APPRUN
chmod +x "$APPDIR/AppRun"

# Desktop and icon
cp "$SCRIPT_DIR/SambaSense.desktop" "$APPDIR/"
cp "$SCRIPT_DIR/SambaSense.desktop" "$APPDIR/usr/share/applications/"
cp "$PROJECT_ROOT/assets/sambasense.svg" "$APPDIR/sambasense.svg"
cp "$PROJECT_ROOT/assets/sambasense.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/sambasense.svg"

# Build AppImage with linuxdeploy
"$LINUXDEPLOY" \
    --appdir "$APPDIR" \
    --desktop-file "$APPDIR/SambaSense.desktop" \
    --icon-file "$APPDIR/sambasense.svg" \
    --output appimage

# Move output
mv SambaSense-*.AppImage "$SCRIPT_DIR/" 2>/dev/null || true

echo ""
echo "✓ AppImage built in $SCRIPT_DIR/"
echo "  Run with: ./SambaSense-x86_64.AppImage"
