#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SambaSense — Sandbox Test Runner
#  Verifies all functions in a clean Arch container
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CTR="podman"

echo "🚀 Starting Sandbox Test in Arch Linux container..."

$CTR run --rm \
    -v "$PROJECT_ROOT:/src:ro" \
    archlinux:latest bash -c '
set -e
pacman -Syu --noconfirm > /dev/null 2>&1
pacman -S --noconfirm python python-pip samba cifs-utils > /dev/null 2>&1

echo "📦 Installing SambaSense from source..."
mkdir -p /tmp/src
cp -r /src/* /tmp/src/
cd /tmp/src
pip install --break-system-packages . > /dev/null 2>&1

echo "🔍 Verifying CLI Command: sambasense --version"
sambasense --version

echo "🔍 Verifying CLI Command: sambasense status"
sambasense status

echo "🔍 Verifying CLI Command: sambasense dash"
sambasense dash

echo "🔍 Verifying CLI Command: sambasense share list"
sambasense share list

echo "✅ Sandbox CLI Tests Passed!"
'
