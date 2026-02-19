#!/bin/bash
# Build SambaSense Flatpak
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building SambaSense Flatpak"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BUILD_DIR="$SCRIPT_DIR/build"
REPO_DIR="$SCRIPT_DIR/repo"

# Ensure runtime is installed
flatpak install -y --noninteractive flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08 2>/dev/null || true

# Create desktop file for flatpak
cat > "$SCRIPT_DIR/com.sambasense.SambaSense.desktop" << EOF
[Desktop Entry]
Name=SambaSense
Comment=Samba Configuration & Management
Exec=sambasense gui
Icon=com.sambasense.SambaSense
Terminal=false
Type=Application
Categories=System;Network;Settings;
Keywords=samba;smb;cifs;share;network;
EOF

# Build
cd "$SCRIPT_DIR"
flatpak-builder --force-clean "$BUILD_DIR" com.sambasense.SambaSense.yml

# Create repo
flatpak-builder --repo="$REPO_DIR" --force-clean "$BUILD_DIR" com.sambasense.SambaSense.yml

# Create bundle
flatpak build-bundle "$REPO_DIR" "$SCRIPT_DIR/SambaSense.flatpak" com.sambasense.SambaSense

echo ""
echo "✓ Flatpak built: $SCRIPT_DIR/SambaSense.flatpak"
echo "  Install with: flatpak install SambaSense.flatpak"
