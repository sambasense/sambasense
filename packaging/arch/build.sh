#!/bin/bash
# Build SambaSense Arch package (.pkg.tar.zst)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PKG_VERSION="1.1.1"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building SambaSense Arch package"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

BUILD_DIR="$SCRIPT_DIR/build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create source tarball
cd "$PROJECT_ROOT"
tar czf "$BUILD_DIR/sambasense-${PKG_VERSION}.tar.gz" \
    --transform="s,^,sambasense-${PKG_VERSION}/," \
    sambasense/ setup.py pyproject.toml requirements.txt assets/

# Copy PKGBUILD
cp "$SCRIPT_DIR/PKGBUILD" "$BUILD_DIR/"

# Build
cd "$BUILD_DIR"
makepkg -sf --noconfirm

# Move output
mv *.pkg.tar.zst "$SCRIPT_DIR/" 2>/dev/null || true

echo ""
echo "✓ Package built: $SCRIPT_DIR/sambasense-${PKG_VERSION}-1-any.pkg.tar.zst"
echo "  Install with: sudo pacman -U sambasense-${PKG_VERSION}-1-any.pkg.tar.zst"
