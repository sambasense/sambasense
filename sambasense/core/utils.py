"""Utility helpers for SambaSense - distro detection, command execution."""

import subprocess
import shutil
import os
import platform


def detect_distro() -> str:
    """Detect the OS or Linux distribution family.

    Returns one of: 'macos', 'arch', 'fedora', 'debian', 'opensuse', 'unknown'.
    """
    if platform.system() == "Darwin":
        return "macos"

    try:
        with open("/etc/os-release", "r") as f:
            content = f.read().lower()
    except FileNotFoundError:
        return "unknown"

    if "arch" in content or "manjaro" in content or "endeavouros" in content:
        return "arch"
    elif "fedora" in content or "rhel" in content or "centos" in content or "rocky" in content:
        return "fedora"
    elif "debian" in content or "ubuntu" in content or "mint" in content or "pop" in content:
        return "debian"
    elif "suse" in content:
        return "opensuse"
    return "unknown"


def get_package_manager() -> str:
    """Return the system package manager command based on distro.

    Returns one of: 'brew', 'pacman', 'dnf', 'apt', 'zypper', or 'unknown'.
    """
    distro = detect_distro()
    mapping = {
        "macos": "brew",
        "arch": "pacman",
        "fedora": "dnf",
        "debian": "apt",
        "opensuse": "zypper",
    }
    return mapping.get(distro, "unknown")


def run_cmd(
    cmd: list[str],
    sudo: bool = False,
    capture: bool = True,
    check: bool = True,
    timeout: int = 120,
) -> subprocess.CompletedProcess:
    """Run a shell command, optionally with sudo.

    Args:
        cmd: Command as a list of strings.
        sudo: If True, prepend 'sudo' (CLI) or 'pkexec' (GUI fallback on Linux).
        capture: Capture stdout/stderr.
        check: Raise CalledProcessError on non-zero exit.
        timeout: Timeout in seconds.

    Returns:
        subprocess.CompletedProcess result.
    """
    if sudo and os.geteuid() != 0:
        if platform.system() == "Darwin":
            # On macOS, just use sudo. GUI apps usually use AuthorizationServices 
            # but for a Python port, sudo is the standard cli/backend fallback.
            cmd = ["sudo"] + cmd
        elif os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            # Use pkexec if available (for Linux GUI), else sudo
            if shutil.which("pkexec"):
                cmd = ["pkexec"] + cmd
            else:
                cmd = ["sudo"] + cmd
        else:
            cmd = ["sudo"] + cmd

    return subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=check,
        timeout=timeout,
    )


def is_command_available(command: str) -> bool:
    """Check if a command is available on PATH."""
    return shutil.which(command) is not None


def format_bytes(size_bytes: int) -> str:
    """Format bytes into human-readable string."""
    if size_bytes < 0:
        return "N/A"
    val = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(val) < 1024.0:
            return f"{val:.1f} {unit}"
        val /= 1024.0
    return f"{val:.1f} PB"


def get_hostname() -> str:
    """Return the system hostname."""
    return platform.node()
