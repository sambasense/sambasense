"""Samba configuration management - smb.conf parsing and editing."""

import os
import re
import shutil
from datetime import datetime
from typing import Optional

from sambasense.core.utils import run_cmd

import platform

def _get_smb_conf_path() -> str:
    """Determine the smb.conf path based on OS and common locations."""
    if platform.system() == "Darwin":
        locations = [
            "/etc/samba/smb.conf", # Native
            "/opt/homebrew/etc/samba/smb.conf", # Apple Silicon Brew
            "/usr/local/etc/samba/smb.conf", # Intel Brew
        ]
        for loc in locations:
            if os.path.exists(loc):
                return loc
        return "/etc/samba/smb.conf" # Default fallback
    return "/etc/samba/smb.conf"

SMB_CONF_PATH = _get_smb_conf_path()


def _backup_conf() -> str:
    """Create a timestamped backup of smb.conf. Returns backup path."""
    if not os.path.exists(SMB_CONF_PATH):
        return ""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = f"{SMB_CONF_PATH}.bak.{ts}"
    try:
        shutil.copy2(SMB_CONF_PATH, backup)
    except PermissionError:
        run_cmd(["cp", SMB_CONF_PATH, backup], sudo=True)
    return backup


def parse_smb_conf(path: Optional[str] = None) -> dict[str, dict[str, str]]:
    """Parse smb.conf into a dict of section -> {key: value}.

    Returns:
        Dict where keys are share/section names, values are dicts of params.
        Example: {'global': {'workgroup': 'WORKGROUP'}, 'myshare': {'path': '/srv/share'}}
    """
    conf_path = path or SMB_CONF_PATH
    if not os.path.exists(conf_path):
        return {}

    sections: dict[str, dict[str, str]] = {}
    current_section: Optional[str] = None

    try:
        with open(conf_path, "r") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                # Section header
                match = re.match(r"^\[(.+)\]$", line)
                if match:
                    current_section = match.group(1).strip()
                    if current_section not in sections:
                        sections[current_section] = {}
                    continue
                # Key = value
                if "=" in line and current_section is not None:
                    key, _, value = line.partition("=")
                    sections[current_section][key.strip()] = value.strip()
    except PermissionError:
        # Try reading with elevated privileges
        try:
            result = run_cmd(["cat", conf_path], sudo=True)
            return _parse_conf_string(result.stdout)
        except Exception:
            return {}
    return sections


def _parse_conf_string(content: str) -> dict[str, dict[str, str]]:
    """Parse smb.conf content from a string."""
    sections: dict[str, dict[str, str]] = {}
    current_section: Optional[str] = None
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        match = re.match(r"^\[(.+)\]$", line)
        if match:
            current_section = match.group(1).strip()
            if current_section not in sections:
                sections[current_section] = {}
            continue
        if "=" in line and current_section is not None:
            key, _, value = line.partition("=")
            sections[current_section][key.strip()] = value.strip()
    return sections


def list_shares() -> dict[str, dict[str, str]]:
    """List all user-defined shares (excluding [global], [homes], [printers]).

    Returns:
        Dict of share_name -> share_config.
    """
    excluded = {"global", "homes", "printers", "print$"}
    all_sections = parse_smb_conf()
    return {k: v for k, v in all_sections.items() if k.lower() not in excluded}


def add_share(
    name: str,
    path: str,
    comment: str = "",
    writable: bool = True,
    guest_ok: bool = False,
    browseable: bool = True,
    valid_users: str = "",
    create_mask: str = "0664",
    directory_mask: str = "0775",
) -> tuple[bool, str]:
    """Add a new share section to smb.conf.

    Args:
        name: Share name (e.g., 'documents').
        path: Filesystem path to share.
        comment: Optional description.
        writable: Allow writing.
        guest_ok: Allow guest access.
        browseable: Show in network browse lists.
        valid_users: Comma-separated list of allowed users.
        create_mask: File creation mask.
        directory_mask: Directory creation mask.

    Returns:
        (success, message) tuple.
    """
    existing = parse_smb_conf()
    if name in existing:
        return False, f"Share '{name}' already exists."

    if not os.path.isdir(path):
        try:
            os.makedirs(path, exist_ok=True)
        except PermissionError:
            run_cmd(["mkdir", "-p", path], sudo=True, check=False)

    share_block = f"\n[{name}]\n"
    share_block += f"   path = {path}\n"
    if comment:
        share_block += f"   comment = {comment}\n"
    share_block += f"   writable = {'yes' if writable else 'no'}\n"
    share_block += f"   guest ok = {'yes' if guest_ok else 'no'}\n"
    share_block += f"   browseable = {'yes' if browseable else 'no'}\n"
    if valid_users:
        share_block += f"   valid users = {valid_users}\n"
    share_block += f"   create mask = {create_mask}\n"
    share_block += f"   directory mask = {directory_mask}\n"

    _backup_conf()
    try:
        # Pipe content via stdin to tee — no shell involved, safe from injection
        run_cmd(["tee", "-a", SMB_CONF_PATH], sudo=True, input=share_block)
        return True, f"Share '{name}' added successfully."
    except Exception as e:
        return False, f"Failed to add share: {e}"


def remove_share(name: str) -> tuple[bool, str]:
    """Remove a share section from smb.conf.

    Returns:
        (success, message) tuple.
    """
    if not os.path.exists(SMB_CONF_PATH):
        return False, "smb.conf not found."

    _backup_conf()

    try:
        result = run_cmd(["cat", SMB_CONF_PATH], sudo=True, check=False)
        content = result.stdout
    except Exception:
        return False, "Cannot read smb.conf."

    # Remove the share section
    pattern = rf"\[{re.escape(name)}\].*?(?=\n\[|\Z)"
    new_content, count = re.subn(pattern, "", content, flags=re.DOTALL)
    if count == 0:
        return False, f"Share '{name}' not found in smb.conf."

    # Clean up excessive blank lines
    new_content = re.sub(r"\n{3,}", "\n\n", new_content)

    try:
        # Pipe content via stdin to tee — no shell involved, safe from injection
        run_cmd(["tee", SMB_CONF_PATH], sudo=True, input=new_content)
        return True, f"Share '{name}' removed."
    except Exception as e:
        return False, f"Failed to remove share: {e}"


def edit_share(name: str, options: dict[str, str]) -> tuple[bool, str]:
    """Edit parameters of an existing share.

    Args:
        name: Share name to edit.
        options: Dict of param -> value to update.

    Returns:
        (success, message) tuple.
    """
    existing = parse_smb_conf()
    if name not in existing:
        return False, f"Share '{name}' not found."

    _backup_conf()
    existing[name].update(options)

    # Rebuild conference - read, modify the target section, and write back
    try:
        result = run_cmd(["cat", SMB_CONF_PATH], sudo=True, check=False)
        content = result.stdout
    except Exception:
        return False, "Cannot read smb.conf."

    # Rebuild the share section
    new_section = f"[{name}]\n"
    for key, value in existing[name].items():
        new_section += f"   {key} = {value}\n"

    pattern = rf"\[{re.escape(name)}\].*?(?=\n\[|\Z)"
    new_content = re.sub(pattern, new_section.rstrip(), content, flags=re.DOTALL)

    try:
        # Pipe content via stdin to tee — no shell involved, safe from injection
        run_cmd(["tee", SMB_CONF_PATH], sudo=True, input=new_content)
        return True, f"Share '{name}' updated."
    except Exception as e:
        return False, f"Failed to edit share: {e}"


def restart_samba() -> tuple[bool, str]:
    """Restart the samba service to apply config changes."""
    if platform.system() == "Darwin":
        try:
            # macOS: Stop and start smbd
            run_cmd(["launchctl", "stop", "com.apple.smbd"], sudo=True)
            run_cmd(["launchctl", "start", "com.apple.smbd"], sudo=True)
            return True, "Samba service restarted."
        except Exception as e:
            return False, f"Failed to restart samba service: {e}"

    for svc in ("smbd", "smb"):
        try:
            result = run_cmd(
                ["systemctl", "restart", svc],
                sudo=True,
                check=False,
            )
            if result.returncode == 0:
                return True, f"Service '{svc}' restarted."
        except Exception:
            continue
    return False, "Failed to restart samba service."


def validate_conf() -> tuple[bool, str]:
    """Validate smb.conf using testparm."""
    try:
        result = run_cmd(
            ["testparm", "-s", SMB_CONF_PATH],
            sudo=False,
            check=False,
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr
    except Exception as e:
        return False, f"testparm not available: {e}"
