#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SambaSense — Master Package Builder
#  Builds all 5 package formats using Podman sandboxes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/dist"
PKG_VERSION="1.1.1"

RED='\033[0;31m'
GREEN='\033[0;32m'
GOLD='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

mkdir -p "$OUTPUT_DIR"

info()  { echo -e "${CYAN}▸${NC} $1"; }
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${GOLD}⚠${NC} $1"; }
fail()  { echo -e "${RED}✗${NC} $1"; }

echo ""
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GOLD}  SambaSense Package Builder v${PKG_VERSION}${NC}"
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

CTR="podman"
if ! command -v podman &>/dev/null; then
    if command -v docker &>/dev/null; then
        CTR="docker"
    else
        fail "Neither podman nor docker found. Install podman: sudo pacman -S podman"
        exit 1
    fi
fi
ok "Using $CTR ($($CTR --version))"
echo ""

# ═══════════════════════════════════════════════════════
# 1. Arch Linux (.pkg.tar.zst) — Podman sandbox
# ═══════════════════════════════════════════════════════
echo -e "${GOLD}[1/5] Building Arch package (.pkg.tar.zst) in Podman sandbox${NC}"
info "Using archlinux:latest container..."

$CTR run --rm \
    -v "$PROJECT_ROOT:/src:ro" \
    -v "$OUTPUT_DIR:/out" \
    archlinux:latest bash -c '
set -e
pacman -Syu --noconfirm > /dev/null 2>&1
pacman -S --noconfirm python python-build python-installer python-setuptools python-wheel fakeroot binutils debugedit > /dev/null 2>&1

useradd -m builder
mkdir -p /tmp/build && cd /tmp/build

cp -r /src/sambasense /src/setup.py /src/pyproject.toml /src/requirements.txt .
mkdir -p assets && cp /src/assets/sambasense.svg assets/
tar czf sambasense-1.1.1.tar.gz --transform="s,^,sambasense-1.1.1/," sambasense/ setup.py pyproject.toml requirements.txt assets/

cp /src/packaging/arch/PKGBUILD .

chown -R builder:builder /tmp/build
su builder -c "cd /tmp/build && makepkg -sfd --noconfirm --skipchecksums 2>&1 | tail -10"
cp /tmp/build/*.pkg.tar.zst /out/ 2>/dev/null && echo "ARCH_OK" || echo "ARCH_FAIL"
' | grep -q "ARCH_OK"

if ls "$OUTPUT_DIR"/sambasense-*.pkg.tar.zst 1>/dev/null 2>&1; then
    ok "Arch package → dist/$(ls "$OUTPUT_DIR"/sambasense-*.pkg.tar.zst | xargs -n1 basename | head -1)"
else
    fail "Arch package build failed"
    exit 1
fi
echo ""

# ═══════════════════════════════════════════════════════
# 2. Debian (.deb) — Podman sandbox
# ═══════════════════════════════════════════════════════
echo -e "${GOLD}[2/5] Building Debian package (.deb) in Podman sandbox${NC}"
info "Using debian:bookworm container..."

$CTR run --rm \
    -v "$PROJECT_ROOT:/src:ro" \
    -v "$OUTPUT_DIR:/out" \
    debian:bookworm bash -c '
set -e
apt-get update -qq > /dev/null 2>&1
apt-get install -y -qq dpkg-dev > /dev/null 2>&1

PKG="sambasense_1.1.1"
B="/tmp/$PKG"

mkdir -p "$B/opt/sambasense" "$B/usr/bin" "$B/usr/share/applications" \
         "$B/usr/share/icons/hicolor/scalable/apps" "$B/DEBIAN"

cp -r /src/sambasense "$B/opt/sambasense/"
cp /src/setup.py /src/pyproject.toml /src/requirements.txt "$B/opt/sambasense/"

cat > "$B/DEBIAN/control" << EOF
Package: sambasense
Version: 1.1.1
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-pyqt6, samba, cifs-utils, libqt6svg6
Maintainer: Sabyla Solutions <contact@sabylasolutions.com>
Description: SambaSense - Samba Configuration & Management
 A desktop application for installing, configuring, and
 managing Samba shares with rich storage visualizations.
EOF

cat > "$B/DEBIAN/postinst" << "POSTINST"
#!/bin/bash
set -e
pip3 install --break-system-packages /opt/sambasense/ 2>/dev/null || pip3 install /opt/sambasense/ || true
echo "SambaSense installed. Run sambasense to get started."
POSTINST
chmod 755 "$B/DEBIAN/postinst"

printf "#!/bin/bash\nexport PYTHONPATH=/opt/sambasense:\$PYTHONPATH\nexec python3 -m sambasense \"\$@\"\n" > "$B/usr/bin/sambasense"
chmod 755 "$B/usr/bin/sambasense"

cat > "$B/usr/share/applications/sambasense.desktop" << EOF
[Desktop Entry]
Name=SambaSense
Comment=Samba Configuration & Management
Exec=sambasense gui
Icon=sambasense
Terminal=false
Type=Application
Categories=System;Network;Settings;
EOF

cp /src/assets/sambasense.svg "$B/usr/share/icons/hicolor/scalable/apps/sambasense.svg"
dpkg-deb --build "$B" /out/sambasense_1.1.1.deb > /dev/null 2>&1
echo "DEB_OK"
'

if [ -f "$OUTPUT_DIR/sambasense_1.1.1.deb" ]; then
    ok "Debian package → dist/sambasense_1.1.1.deb"
else
    fail "Debian package build failed"
fi
echo ""

# ═══════════════════════════════════════════════════════
# 3. Fedora RPM (.rpm) — Podman sandbox
# ═══════════════════════════════════════════════════════
echo -e "${GOLD}[3/5] Building RPM package (.rpm) in Podman sandbox${NC}"
info "Using fedora:40 container..."

$CTR run --rm \
    -v "$PROJECT_ROOT:/src:ro" \
    -v "$OUTPUT_DIR:/out" \
    fedora:40 bash -c '
set -e
dnf install -y -q rpm-build > /dev/null 2>&1

R="/root/rpmbuild"
mkdir -p "$R"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

cd /src
tar czf "$R/SOURCES/sambasense-1.1.1.tar.gz" \
    --transform="s,^,sambasense-1.1.1/," \
    sambasense/ setup.py pyproject.toml requirements.txt assets/

cat > "$R/SPECS/sambasense.spec" << "SPEC"
Name:           sambasense
Version:        1.1.1
Release:        1%{?dist}
Summary:        Samba Configuration & Management Application
License:        MIT
URL:            https://github.com/sabylasolutions/sambasense
Source0:        sambasense-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3 >= 3.10
Requires:       samba samba-client cifs-utils qt6-qtsvg

%description
SambaSense — Samba Configuration & Management Application

%prep
%autosetup -n sambasense-%{version}

%install
mkdir -p %{buildroot}/opt/sambasense
cp -r sambasense %{buildroot}/opt/sambasense/
cp setup.py pyproject.toml requirements.txt %{buildroot}/opt/sambasense/

mkdir -p %{buildroot}%{_bindir}
printf "#!/bin/bash\nexport PYTHONPATH=/opt/sambasense:\$PYTHONPATH\nexec python3 -m sambasense \"\$@\"\n" > %{buildroot}%{_bindir}/sambasense
chmod 755 %{buildroot}%{_bindir}/sambasense

mkdir -p %{buildroot}%{_datadir}/applications
cat > %{buildroot}%{_datadir}/applications/sambasense.desktop << EOF
[Desktop Entry]
Name=SambaSense
Comment=Samba Configuration & Management
Exec=sambasense gui
Icon=sambasense
Terminal=false
Type=Application
Categories=System;Network;Settings;
EOF

install -Dm644 assets/sambasense.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/sambasense.svg

%files
/opt/sambasense/
%{_bindir}/sambasense
%{_datadir}/applications/sambasense.desktop
%{_datadir}/icons/hicolor/scalable/apps/sambasense.svg
SPEC

rpmbuild -ba "$R/SPECS/sambasense.spec" 2>&1 | tail -3
cp "$R"/RPMS/noarch/*.rpm /out/ 2>/dev/null
echo "RPM_OK"
'

if ls "$OUTPUT_DIR"/*.rpm 1>/dev/null 2>&1; then
    ok "RPM package → dist/$(ls "$OUTPUT_DIR"/*.rpm | xargs -n1 basename | head -1)"
else
    fail "RPM package build failed"
fi
echo ""

# ═══════════════════════════════════════════════════════
# 4. AppImage — Podman sandbox
# ═══════════════════════════════════════════════════════
echo -e "${GOLD}[4/5] Building AppImage in Podman sandbox${NC}"
info "Using ubuntu:22.04 container with appimagetool..."

$CTR run --rm \
    -v "$PROJECT_ROOT:/src:ro" \
    -v "$OUTPUT_DIR:/out" \
    ubuntu:22.04 bash -c '
set -e
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq > /dev/null 2>&1
apt-get install -y -qq python3 file wget libqt6svg6 > /dev/null 2>&1

A="/tmp/SambaSense.AppDir"
mkdir -p "$A/usr/bin" "$A/usr/lib/python3/dist-packages" \
         "$A/usr/share/applications" "$A/usr/share/icons/hicolor/scalable/apps"

cp -r /src/sambasense "$A/usr/lib/python3/dist-packages/"

cat > "$A/AppRun" << "APPRUN"
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
export PYTHONPATH="$HERE/usr/lib/python3/dist-packages:$PYTHONPATH"
exec python3 -m sambasense "$@"
APPRUN
chmod +x "$A/AppRun"

printf "#!/bin/bash\nSELF_DIR=\"\$(dirname \"\$(readlink -f \"\$0\")\")\"\nexport PYTHONPATH=\"\$SELF_DIR/../lib/python3/dist-packages:\$PYTHONPATH\"\nexec python3 -m sambasense \"\$@\"\n" > "$A/usr/bin/sambasense"
chmod +x "$A/usr/bin/sambasense"

cat > "$A/sambasense.desktop" << EOF
[Desktop Entry]
Name=SambaSense
Comment=Samba Configuration & Management
Exec=sambasense gui
Icon=sambasense
Terminal=false
Type=Application
Categories=System;Network;Settings;
EOF

cp /src/assets/sambasense.svg "$A/sambasense.svg"
cp /src/assets/sambasense.svg "$A/.DirIcon" 2>/dev/null || true
cp "$A/sambasense.desktop" "$A/usr/share/applications/"
cp /src/assets/sambasense.svg "$A/usr/share/icons/hicolor/scalable/apps/sambasense.svg"

cd /tmp
wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool
chmod +x appimagetool
./appimagetool --appimage-extract > /dev/null 2>&1
ARCH=x86_64 ./squashfs-root/AppRun "$A" /out/SambaSense-x86_64.AppImage 2>&1 | tail -3
echo "APPIMAGE_OK"
'

if [ -f "$OUTPUT_DIR/SambaSense-x86_64.AppImage" ]; then
    ok "AppImage → dist/SambaSense-x86_64.AppImage"
else
    fail "AppImage build failed"
fi
echo ""

# ═══════════════════════════════════════════════════════
# 5. Flatpak — Podman sandbox
# ═══════════════════════════════════════════════════════
echo -e "${GOLD}[5/5] Building Flatpak bundle in Podman sandbox${NC}"
info "Using fedora:40 container with flatpak-builder..."

$CTR run --rm --privileged \
    -v "$PROJECT_ROOT:/src:ro" \
    -v "$OUTPUT_DIR:/out" \
    fedora:40 bash -c '
set -e
dnf install -y -q flatpak flatpak-builder > /dev/null 2>&1
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true

echo "  Installing Freedesktop runtime (this may take a moment)..."
flatpak install -y --noninteractive flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08 2>/dev/null || {
    echo "FLATPAK_RUNTIME_FAIL"
    exit 1
}

cd /tmp
mkdir -p build repo

cat > manifest.yml << "MANIFEST"
app-id: com.sabyla.SambaSense
runtime: org.freedesktop.Platform
runtime-version: "23.08"
sdk: org.freedesktop.Sdk
command: sambasense
finish-args:
  - --share=network
  - --share=ipc
  - --socket=x11
  - --socket=wayland
  - --filesystem=host
modules:
  - name: sambasense
    buildsystem: simple
    build-commands:
      - mkdir -p /app/lib/python3/dist-packages
      - cp -r sambasense /app/lib/python3/dist-packages/
      - mkdir -p /app/bin
      - printf "#!/bin/bash\nexport PYTHONPATH=/app/lib/python3/dist-packages:\$PYTHONPATH\nexec python3 -m sambasense \"\$@\"\n" > /app/bin/sambasense
      - chmod 755 /app/bin/sambasense
      - install -Dm644 assets/sambasense.svg /app/share/icons/hicolor/scalable/apps/com.sabyla.SambaSense.svg
      - mkdir -p /app/share/applications
      - printf "[Desktop Entry]\nName=SambaSense\nComment=Samba Configuration & Management\nExec=sambasense gui\nIcon=com.sabyla.SambaSense\nTerminal=false\nType=Application\nCategories=System;Network;Settings;\n" > /app/share/applications/com.sabyla.SambaSense.desktop
    sources:
      - type: dir
        path: /src
MANIFEST

flatpak-builder --force-clean build manifest.yml 2>&1 | tail -5
flatpak-builder --repo=repo --force-clean build manifest.yml 2>&1 | tail -3
flatpak build-bundle repo /out/SambaSense.flatpak com.sabyla.SambaSense 2>&1 | tail -3
echo "FLATPAK_OK"
'

if [ -f "$OUTPUT_DIR/SambaSense.flatpak" ]; then
    ok "Flatpak → dist/SambaSense.flatpak"
else
    fail "Flatpak build failed (runtime download may require more time/bandwidth)"
fi
echo ""

# ── Summary ───────────────────────────────────────────
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GOLD}  Build Summary${NC}"
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
ls -lh "$OUTPUT_DIR"/ 2>/dev/null
echo ""
echo -e "  All packages in: ${CYAN}$OUTPUT_DIR/${NC}"
echo ""
