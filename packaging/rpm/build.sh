#!/bin/bash
# Build SambaSense .rpm package
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PKG_VERSION="1.0.0"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Building SambaSense .rpm package"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Setup rpmbuild directories
RPMBUILD_DIR="$HOME/rpmbuild"
mkdir -p "$RPMBUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create tarball
TARBALL_DIR="$RPMBUILD_DIR/SOURCES"
cd "$PROJECT_ROOT"
tar czf "$TARBALL_DIR/sambasense-${PKG_VERSION}.tar.gz" \
    --transform="s,^,sambasense-${PKG_VERSION}/," \
    sambasense/ setup.py pyproject.toml requirements.txt assets/ packaging/

# Copy spec
cp "$SCRIPT_DIR/sambasense.spec" "$RPMBUILD_DIR/SPECS/"

# Create desktop file
cat > "$SCRIPT_DIR/sambasense.desktop" << EOF
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

# Build
rpmbuild -ba "$RPMBUILD_DIR/SPECS/sambasense.spec"

echo ""
echo "✓ RPM built in $RPMBUILD_DIR/RPMS/"
echo "  Install with: sudo dnf install <path-to-rpm>"
