#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SambaSense — Comprehensive Sandbox Test Runner
#  Tests install, all CLI features, and unit tests
#  inside clean Podman containers (Arch, Debian, Fedora).
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CTR="${CTR:-podman}"
PKG_VERSION="1.1.1"
DIST_DIR="$PROJECT_ROOT/dist"

RED='\033[0;31m'; GREEN='\033[0;32m'; GOLD='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'

echo ""
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GOLD}  SambaSense Sandbox Test Suite v${PKG_VERSION}${NC}"
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Runtime: $CTR ($($CTR --version 2>/dev/null | head -1))${NC}"
echo -e "${CYAN}  Source:  $PROJECT_ROOT${NC}"

TOTAL_PASS=0
TOTAL_FAIL=0

# ── 1. Arch Linux: source install + full suite ──────────────────
echo ""
echo -e "${GOLD}[1/3] Arch Linux — source install${NC}"

if $CTR run --rm \
    -v "$PROJECT_ROOT:/src:ro" \
    archlinux:latest bash << 'ARCHEOF'
set -e
pacman -Syu --noconfirm >/dev/null 2>&1
pacman -S --noconfirm python python-pip python-pytest samba cifs-utils >/dev/null 2>&1
mkdir -p /tmp/ss && cp -r /src/* /tmp/ss/ && cd /tmp/ss
pip install --break-system-packages -e . >/dev/null 2>&1

G="\033[0;32m"; R="\033[0;31m"; O="\033[0;33m"; N="\033[0m"
P=0; F=0
ok()   { echo -e "  ${G}✓${N} $1"; P=$((P+1)); }
fail() { echo -e "  ${R}✗${N} $1"; F=$((F+1)); }
hdr()  { echo -e "\n${O}─── $1 ───${N}"; }

hdr "Install"
sambasense --version 2>&1 | grep -q "1.1.1" && ok "version 1.1.1" || fail "version"

hdr "Module imports"
python3 -c "import sambasense; assert sambasense.__version__ == '1.1.1'" && ok "sambasense" || fail "sambasense"
python3 -c "from sambasense.core.utils import detect_distro,run_cmd,format_bytes,get_hostname,is_command_available" && ok "core.utils" || fail "core.utils"
python3 -c "from sambasense.core.config import parse_smb_conf,list_shares,add_share,remove_share,edit_share,restart_samba,validate_conf" && ok "core.config" || fail "core.config"
python3 -c "from sambasense.core.installer import is_samba_installed,get_service_status,install_samba,uninstall_samba,enable_service,disable_service,start_service,stop_service" && ok "core.installer" || fail "core.installer"
python3 -c "from sambasense.core.mapper import list_mounted_shares,mount_share,unmount_share,add_fstab_entry,remove_fstab_entry" && ok "core.mapper" || fail "core.mapper"
python3 -c "from sambasense.core.storage import get_disk_usage,get_usage_percent,record_usage,get_usage_history" && ok "core.storage" || fail "core.storage"
python3 -c "from sambasense.cli.commands import build_parser,cli_main" && ok "cli.commands" || fail "cli.commands"

hdr "Unit tests (pytest)"
python3 -m pytest /src/tests/ -q --tb=short && ok "All unit tests passed" || fail "Unit tests"

hdr "CLI subcommands"
sambasense --version  2>&1 | grep -q "1.1.1"    && ok "--version"   || fail "--version"
sambasense --help     2>&1 | grep -q "sambasense" && ok "--help"      || fail "--help"
sambasense status     2>&1 | grep -qi "distrib"  && ok "status"      || fail "status"
sambasense dash       2>&1                        && ok "dash"        || fail "dash"
sambasense mounts     2>&1                        && ok "mounts"      || fail "mounts"
sambasense share list 2>&1                        && ok "share list"  || fail "share list"

hdr "Parser: all subcommands"
python3 -c "
from sambasense.cli.commands import build_parser
p = build_parser()
cases = [
  (['status'],'status'),(['install'],'install'),(['uninstall'],'uninstall'),
  (['enable'],'enable'),(['disable'],'disable'),
  (['share','list'],'share'),(['share','validate'],'share'),
  (['share','add','--name','x','--path','/x'],'share'),
  (['share','remove','--name','x'],'share'),
  (['mount','//s/x','/m','-u','u','-P','p'],'mount'),
  (['umount','/m'],'umount'),(['mounts'],'mounts'),(['dash'],'dash'),(['gui'],'gui'),
]
for argv,cmd in cases:
    a=p.parse_args(argv); assert a.command==cmd,f'got {a.command} want {cmd}'
print(f'  {len(cases)}/{len(cases)} OK')
" && ok "14 parser subcommands" || fail "Parser"

hdr "smb.conf parse / _parse_conf_string"
python3 -c "
import tempfile,os
from sambasense.core.config import parse_smb_conf,_parse_conf_string
raw='[global]\n   workgroup = WORKGROUP\n[docs]\n   path=/srv/docs\n   writable=yes\n   guest ok=no\n'
with tempfile.NamedTemporaryFile(mode='w',suffix='.conf',delete=False) as f:
    f.write(raw); tmp=f.name
try:
    s=parse_smb_conf(tmp)
    assert s['global']['workgroup']=='WORKGROUP'
    assert s['docs']['path']=='/srv/docs'
    assert s['docs']['writable']=='yes'
    s2=_parse_conf_string(raw)
    assert s2['docs']['guest ok']=='no'
    print('  OK')
finally: os.unlink(tmp)
" && ok "smb.conf parsing" || fail "smb.conf parsing"

hdr "Storage: disk usage + history"
python3 -c "
import tempfile,unittest.mock as mock
from sambasense.core.storage import get_disk_usage,get_usage_percent,record_usage,get_usage_history
u=get_disk_usage('/tmp')
assert u['total']>0 and u['used']+u['free']==u['total']
assert get_disk_usage('/nonexistent/xyz')=={'total':0,'used':0,'free':0}
pct=get_usage_percent('/tmp'); assert 0.0<=pct<=100.0
with tempfile.TemporaryDirectory() as d:
    with mock.patch('sambasense.core.storage._HISTORY_DIR',d):
        record_usage('/tmp',label='t'); record_usage('/tmp',label='t')
        h=get_usage_history('/tmp')
        assert len(h)==2 and h[0]['label']=='t' and 'timestamp' in h[0] and h[0]['total']>0
print('  OK')
" && ok "Storage functions" || fail "Storage functions"

hdr "format_bytes edge cases"
python3 -c "
from sambasense.core.utils import format_bytes
assert format_bytes(0)=='0.0 B'; assert format_bytes(1024)=='1.0 KB'
assert format_bytes(1024**2)=='1.0 MB'; assert format_bytes(1024**3)=='1.0 GB'
assert 'TB' in format_bytes(2*1024**4); assert format_bytes(-1)=='N/A'
print('  OK')
" && ok "format_bytes" || fail "format_bytes"

hdr "mapper: list_mounted_shares (mocked)"
python3 -c "
import unittest.mock as mock
MOCKS=('sysfs /sys sysfs rw 0 0\n'
       '//192.168.1.1/share /mnt/nas cifs rw,username=user 0 0\n'
       '//fileserver/docs /mnt/docs smb3 rw,guest 0 0\n')
with mock.patch('builtins.open',mock.mock_open(read_data=MOCKS)):
    from sambasense.core.mapper import list_mounted_shares
    m=list_mounted_shares()
    assert len(m)==2,f'expected 2 got {len(m)}'
    assert m[0]['remote']=='//192.168.1.1/share' and m[0]['type']=='cifs'
    assert m[1]['type']=='smb3'
print('  OK')
" && ok "list_mounted_shares" || fail "list_mounted_shares"

hdr "mapper: fstab exact-field duplicate check"
python3 -c "
import unittest.mock as mock
FSTAB=('# fstab\n//server/share  /mnt/share  cifs  defaults  0  0\n//server/share2 /mnt/share2 cifs  defaults  0  0\n')
with mock.patch('builtins.open',mock.mock_open(read_data=FSTAB)):
    from sambasense.core.mapper import add_fstab_entry
    ok1,msg1=add_fstab_entry('//server/share','/mnt/share')
    assert not ok1 and 'already exists' in msg1, f'should reject: got ok={ok1} msg={msg1}'
    ok2,msg2=add_fstab_entry('//server/sha','/mnt/sha')
    if not ok2 and 'already exists' in msg2:
        raise AssertionError('//server/sha falsely rejected as duplicate of //server/share')
print('  OK')
" && ok "fstab duplicate check (exact field)" || fail "fstab duplicate check"

hdr "installer: distro + pkg-manager detection"
python3 -c "
from sambasense.core.utils import detect_distro,get_package_manager
d=detect_distro(); pm=get_package_manager()
assert isinstance(d,str) and len(d)>0
assert isinstance(pm,str)
print(f'  distro={d} pm={pm}')
" && ok "distro/pkg-mgr detection" || fail "distro/pkg-mgr detection"

hdr "Security: no bash -c in source"
grep -r "bash.*-c" /src/sambasense/ 2>/dev/null | grep -v __pycache__ \
    && fail "bash -c found" || ok "No bash -c shell invocations"

echo ""
echo -e "${O}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"
echo -e "  Results: ${G}${P} passed${N}  ${R}${F} failed${N}"
echo -e "${O}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${N}"
[ "$F" -eq 0 ] && exit 0 || exit 1
ARCHEOF
then
    echo -e "  ${GREEN}✓ Arch: PASSED${NC}"; TOTAL_PASS=$((TOTAL_PASS+1))
else
    echo -e "  ${RED}✗ Arch: FAILED${NC}"; TOTAL_FAIL=$((TOTAL_FAIL+1))
fi

# ── 2. Debian Bookworm: .deb install + abbreviated suite ─────────
echo ""
echo -e "${GOLD}[2/3] Debian Bookworm — .deb install${NC}"
DEB_PKG="$DIST_DIR/sambasense_${PKG_VERSION}.deb"
if [ ! -f "$DEB_PKG" ]; then
    echo -e "  ${GOLD}⚠  No .deb in dist/ — skipping (run build_all.sh first)${NC}"
else
if $CTR run --rm \
    -v "$PROJECT_ROOT:/src:ro" \
    -v "$DIST_DIR:/dist:ro" \
    debian:bookworm bash -c "
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null 2>&1
apt-get install -y -qq python3 python3-pip python3-pytest samba cifs-utils libgl1-mesa-glx libglib2.0-0 >/dev/null 2>&1
dpkg -i /dist/sambasense_${PKG_VERSION}.deb 2>/dev/null; apt-get install -f -y -qq >/dev/null 2>&1
pip3 install --break-system-packages /opt/sambasense/ >/dev/null 2>&1 || true

G='\033[0;32m'; R='\033[0;31m'; O='\033[0;33m'; N='\033[0m'
P=0; F=0
ok()   { echo -e \"  \${G}✓\${N} \$1\"; P=\$((P+1)); }
fail() { echo -e \"  \${R}✗\${N} \$1\"; F=\$((F+1)); }
hdr()  { echo -e \"\n\${O}─── \$1 ───\${N}\"; }

hdr 'Install'; sambasense --version 2>&1 | grep -q '1.1.1' && ok 'deb + version 1.1.1' || fail 'deb install/version'
hdr 'Imports'
python3 -c 'import sambasense; assert sambasense.__version__==\"1.1.1\"' && ok 'sambasense' || fail 'sambasense'
python3 -c 'from sambasense.core.utils import detect_distro,format_bytes' && ok 'core.utils' || fail 'core.utils'
python3 -c 'from sambasense.core.config import parse_smb_conf,add_share' && ok 'core.config' || fail 'core.config'
python3 -c 'from sambasense.core.mapper import list_mounted_shares' && ok 'core.mapper' || fail 'core.mapper'
python3 -c 'from sambasense.core.storage import get_disk_usage,record_usage' && ok 'core.storage' || fail 'core.storage'
hdr 'Unit tests'; python3 -m pytest /src/tests/ -q --tb=short && ok 'unit tests' || fail 'unit tests'
hdr 'CLI'
sambasense status 2>&1 | grep -qi 'distrib' && ok 'status' || fail 'status'
sambasense dash   2>&1 && ok 'dash' || fail 'dash'
sambasense mounts 2>&1 && ok 'mounts' || fail 'mounts'
sambasense share list 2>&1 && ok 'share list' || fail 'share list'
hdr 'Security'
grep -r 'bash.*-c' /src/sambasense/ 2>/dev/null | grep -v __pycache__ && fail 'bash -c found' || ok 'no bash -c'

echo -e \"\n\${O}Results: \${G}\${P} passed\${N}  \${R}\${F} failed\${N}\"
[ \"\$F\" -eq 0 ] && exit 0 || exit 1
"
then
    echo -e "  ${GREEN}✓ Debian: PASSED${NC}"; TOTAL_PASS=$((TOTAL_PASS+1))
else
    echo -e "  ${RED}✗ Debian: FAILED${NC}"; TOTAL_FAIL=$((TOTAL_FAIL+1))
fi
fi

# ── 3. Fedora 40: .rpm install + abbreviated suite ───────────────
echo ""
echo -e "${GOLD}[3/3] Fedora 40 — .rpm install${NC}"
RPM_PKG=$(ls "$DIST_DIR"/sambasense-*.rpm 2>/dev/null | head -1 || true)
if [ -z "$RPM_PKG" ] || [ ! -f "$RPM_PKG" ]; then
    echo -e "  ${GOLD}⚠  No .rpm in dist/ — skipping (run build_all.sh first)${NC}"
else
if $CTR run --rm \
    -v "$PROJECT_ROOT:/src:ro" \
    -v "$DIST_DIR:/dist:ro" \
    fedora:40 bash -c "
dnf install -y -q python3 python3-pip python3-pytest samba samba-client cifs-utils mesa-libGL qt6-qtsvg >/dev/null 2>&1
rpm -i \$(ls /dist/sambasense-*.rpm | head -1) 2>&1 || rpm -i --nodeps \$(ls /dist/sambasense-*.rpm | head -1)
pip3 install /opt/sambasense/ >/dev/null 2>&1 || pip3 install --break-system-packages /opt/sambasense/ >/dev/null 2>&1 || true
export PYTHONPATH=/opt/sambasense:\$PYTHONPATH

G='\033[0;32m'; R='\033[0;31m'; O='\033[0;33m'; N='\033[0m'
P=0; F=0
ok()   { echo -e \"  \${G}✓\${N} \$1\"; P=\$((P+1)); }
fail() { echo -e \"  \${R}✗\${N} \$1\"; F=\$((F+1)); }
hdr()  { echo -e \"\n\${O}─── \$1 ───\${N}\"; }

hdr 'Install'; sambasense --version 2>&1 | grep -q '1.1.1' && ok 'rpm + version 1.1.1' || fail 'rpm install/version'
hdr 'Imports'
python3 -c 'import sambasense; assert sambasense.__version__==\"1.1.1\"' && ok 'sambasense' || fail 'sambasense'
python3 -c 'from sambasense.core.utils import detect_distro,format_bytes' && ok 'core.utils' || fail 'core.utils'
python3 -c 'from sambasense.core.config import parse_smb_conf,add_share' && ok 'core.config' || fail 'core.config'
python3 -c 'from sambasense.core.mapper import list_mounted_shares' && ok 'core.mapper' || fail 'core.mapper'
python3 -c 'from sambasense.core.storage import get_disk_usage,record_usage' && ok 'core.storage' || fail 'core.storage'
hdr 'Unit tests'; python3 -m pytest /src/tests/ -q --tb=short && ok 'unit tests' || fail 'unit tests'
hdr 'CLI'
sambasense status 2>&1 | grep -qi 'distrib' && ok 'status' || fail 'status'
sambasense dash   2>&1 && ok 'dash' || fail 'dash'
sambasense mounts 2>&1 && ok 'mounts' || fail 'mounts'
sambasense share list 2>&1 && ok 'share list' || fail 'share list'
hdr 'Security'
grep -r 'bash.*-c' /src/sambasense/ 2>/dev/null | grep -v __pycache__ && fail 'bash -c found' || ok 'no bash -c'

echo -e \"\n\${O}Results: \${G}\${P} passed\${N}  \${R}\${F} failed\${N}\"
[ \"\$F\" -eq 0 ] && exit 0 || exit 1
"
then
    echo -e "  ${GREEN}✓ Fedora: PASSED${NC}"; TOTAL_PASS=$((TOTAL_PASS+1))
else
    echo -e "  ${RED}✗ Fedora: FAILED${NC}"; TOTAL_FAIL=$((TOTAL_FAIL+1))
fi
fi

# ── Final summary ─────────────────────────────────────────────────
echo ""
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GOLD}  FINAL: ${GREEN}${TOTAL_PASS} distro(s) PASSED${NC}  ${RED}${TOTAL_FAIL} FAILED${NC}"
echo -e "${GOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
[ "$TOTAL_FAIL" -eq 0 ]
