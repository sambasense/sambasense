#!/bin/bash
# Build SambaSense .deb package
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PKG_NAME="sambasense"
PKG_VERSION="1.0.0"
BUILD_DIR="$SCRIPT_DIR/build"
PKG_DIR="$BUILD_DIR/${PKG_NAME}_${PKG_VERSION}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building SambaSense .deb package"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$PKG_DIR"

# Create directory structure
mkdir -p "$PKG_DIR/opt/sambasense"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/applications"
mkdir -p "$PKG_DIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$PKG_DIR/DEBIAN"

# Copy application files
cp -r "$PROJECT_ROOT/sambasense" "$PKG_DIR/opt/sambasense/"
cp "$PROJECT_ROOT/setup.py" "$PKG_DIR/opt/sambasense/"
cp "$PROJECT_ROOT/pyproject.toml" "$PKG_DIR/opt/sambasense/"
cp "$PROJECT_ROOT/requirements.txt" "$PKG_DIR/opt/sambasense/"

# Copy control files
cp "$SCRIPT_DIR/DEBIAN/control" "$PKG_DIR/DEBIAN/"
cp "$SCRIPT_DIR/DEBIAN/postinst" "$PKG_DIR/DEBIAN/"
chmod 755 "$PKG_DIR/DEBIAN/postinst"

# Create launcher script
cat > "$PKG_DIR/usr/bin/sambasense" << 'EOF'
#!/bin/bash
exec python3 -m sambasense "$@"
EOF
chmod 755 "$PKG_DIR/usr/bin/sambasense"

# Create .desktop file
cat > "$PKG_DIR/usr/share/applications/sambasense.desktop" << EOF
[Desktop Entry]
Name=SambaSense
Comment=Samba Configuration & Management
Exec=sambasense gui
Icon=sambasense
Terminal=false
Type=Application
Categories=System;Network;Settings;
Keywords=samba;smb;cifs;share;network;
EOF

# Copy icon
cp "$PROJECT_ROOT/assets/sambasense.svg" "$PKG_DIR/usr/share/icons/hicolor/128x128/apps/sambasense.svg"

# Build package
dpkg-deb --build "$PKG_DIR"
mv "$PKG_DIR.deb" "$SCRIPT_DIR/"

echo ""
echo "✓ Package built: $SCRIPT_DIR/${PKG_NAME}_${PKG_VERSION}.deb"
echo "  Install with: sudo dpkg -i ${PKG_NAME}_${PKG_VERSION}.deb"
