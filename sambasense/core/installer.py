"""Samba and smbclient installation management."""

import platform

from sambasense.core.utils import detect_distro, run_cmd, is_command_available


# Package names per distro
_SAMBA_PACKAGES = {
    "arch": ["samba"],
    "fedora": ["samba", "samba-client", "samba-common"],
    "debian": ["samba", "smbclient"],
    "opensuse": ["samba", "samba-client"],
}

_CIFS_PACKAGES = {
    "arch": ["cifs-utils"],
    "fedora": ["cifs-utils"],
    "debian": ["cifs-utils"],
    "opensuse": ["cifs-utils"],
}

# Install commands per distro
_INSTALL_CMD = {
    "arch": ["pacman", "-S", "--noconfirm"],
    "fedora": ["dnf", "install", "-y"],
    "debian": ["apt", "install", "-y"],
    "opensuse": ["zypper", "install", "-y"],
}

_UNINSTALL_CMD = {
    "arch": ["pacman", "-Rns", "--noconfirm"],
    "fedora": ["dnf", "remove", "-y"],
    "debian": ["apt", "remove", "-y"],
    "opensuse": ["zypper", "remove", "-y"],
}


def is_samba_installed() -> bool:
    """Check if the samba server is installed."""
    return is_command_available("smbd")


def is_smbclient_installed() -> bool:
    """Check if smbclient is installed."""
    return is_command_available("smbclient")


def is_cifs_installed() -> bool:
    """Check if cifs-utils (mount.cifs) is installed. (Always True on macOS)"""
    if platform.system() == "Darwin":
        return True
    return is_command_available("mount.cifs")


def get_service_status() -> str:
    """Get the smbd service status.

    Returns one of: 'running', 'stopped', 'not-installed', 'unknown'.
    """
    if not is_samba_installed():
        return "not-installed"
    try:
        result = run_cmd(
            ["systemctl", "is-active", "smbd"],
            sudo=False,
            check=False,
        )
        status = result.stdout.strip()
        if status == "active":
            return "running"
        # Try smb.service (Arch / Fedora)
        result2 = run_cmd(
            ["systemctl", "is-active", "smb"],
            sudo=False,
            check=False,
        )
        if result2.stdout.strip() == "active":
            return "running"
        return "stopped"
    except Exception:
        return "unknown"


def _get_service_name() -> str:
    """Determine the correct systemd service name for smbd."""
    for name in ("smbd", "smb"):
        try:
            result = run_cmd(
                ["systemctl", "list-unit-files", f"{name}.service"],
                sudo=False,
                check=False,
            )
            if name in result.stdout:
                return name
        except Exception:
            continue
    return "smbd"


def install_samba() -> tuple[bool, str]:
    """Install samba and smbclient packages.

    Returns:
        (success, message) tuple.
    """
    distro = detect_distro()
    if distro == "unknown":
        return False, "Unsupported distribution. Please install samba manually."

    packages = _SAMBA_PACKAGES.get(distro, []) + _CIFS_PACKAGES.get(distro, [])
    cmd = _INSTALL_CMD[distro] + packages

    try:
        run_cmd(cmd, sudo=True, timeout=300)
        # Enable and start service
        svc = _get_service_name()
        run_cmd(["systemctl", "enable", "--now", svc], sudo=True, check=False)
        return True, f"Successfully installed: {', '.join(packages)}"
    except Exception as e:
        return False, f"Installation failed: {e}"


def uninstall_samba() -> tuple[bool, str]:
    """Uninstall samba packages.

    Returns:
        (success, message) tuple.
    """
    distro = detect_distro()
    if distro == "unknown":
        return False, "Unsupported distribution. Please uninstall samba manually."

    # Stop service first (for Linux)
    if platform.system() != "Darwin":
        run_cmd(["systemctl", "disable", "--now", _get_service_name()], sudo=True, check=False)

    packages = _SAMBA_PACKAGES.get(distro, [])
    cmd = _UNINSTALL_CMD[distro] + packages

    try:
        run_cmd(cmd, sudo=True, timeout=300)
        return True, f"Successfully uninstalled: {', '.join(packages)}"
    except Exception as e:
        return False, f"Uninstall failed: {e}"


def enable_service() -> tuple[bool, str]:
    """Enable and start the Samba service."""
    if platform.system() == "Darwin":
        try:
            run_cmd(["launchctl", "load", "-w", "/System/Library/LaunchDaemons/com.apple.smbd.plist"], sudo=True)
            return True, "Samba service enabled and loaded."
        except Exception as e:
            return False, f"Failed to enable service: {e}"

    try:
        run_cmd(["systemctl", "enable", "--now", _get_service_name()], sudo=True)
        return True, "Samba service enabled and started."
    except Exception as e:
        return False, f"Failed to enable service: {e}"


def disable_service() -> tuple[bool, str]:
    """Disable and stop the Samba service."""
    if platform.system() == "Darwin":
        try:
            run_cmd(["launchctl", "unload", "-w", "/System/Library/LaunchDaemons/com.apple.smbd.plist"], sudo=True)
            return True, "Samba service disabled and unloaded."
        except Exception as e:
            return False, f"Failed to disable service: {e}"

    try:
        run_cmd(["systemctl", "disable", "--now", _get_service_name()], sudo=True)
        return True, "Samba service disabled and stopped."
    except Exception as e:
        return False, f"Failed to disable service: {e}"


def start_service() -> tuple[bool, str]:
    """Start the Samba service temporarily."""
    if platform.system() == "Darwin":
        try:
            run_cmd(["launchctl", "start", "com.apple.smbd"], sudo=True)
            return True, "Samba service started."
        except Exception as e:
            return False, f"Failed to start service: {e}"

    try:
        run_cmd(["systemctl", "start", _get_service_name()], sudo=True)
        return True, "Samba service started."
    except Exception as e:
        return False, f"Failed to start service: {e}"


def stop_service() -> tuple[bool, str]:
    """Stop the Samba service temporarily."""
    if platform.system() == "Darwin":
        try:
            run_cmd(["launchctl", "stop", "com.apple.smbd"], sudo=True)
            return True, "Samba service stopped."
        except Exception as e:
            return False, f"Failed to stop service: {e}"

    try:
        run_cmd(["systemctl", "stop", _get_service_name()], sudo=True)
        return True, "Samba service stopped."
    except Exception as e:
        return False, f"Failed to stop service: {e}"
