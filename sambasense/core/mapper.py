"""CIFS share mounting and management."""

import os
import re
import platform
import tempfile
from typing import Optional

from sambasense.core.utils import run_cmd


def list_mounted_shares() -> list[dict[str, str]]:
    """List all currently mounted CIFS/SMB shares.

    Returns:
        List of dicts with keys: 'remote', 'local', 'type', 'options'.
    """
    mounts = []
    
    if platform.system() == "Darwin":
        try:
            # macOS: Use mount command
            result = run_cmd(["mount"], check=False)
            for line in result.stdout.splitlines():
                # Format: //user@server/share on /local/path (smbfs, ...)
                match = re.match(r'(//.*?) on (.*?) \((smbfs|smb3|cifs).*?\)', line)
                if match:
                    mounts.append({
                        "remote": match.group(1),
                        "local": match.group(2),
                        "type": match.group(3),
                        "options": "", # Detailed options parsing can be added if needed
                    })
        except Exception:
            pass
        return mounts

    # Linux: Use /proc/mounts
    try:
        if os.path.exists("/proc/mounts"):
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4 and parts[2] in ("cifs", "smb3"):
                        mounts.append({
                            "remote": parts[0],
                            "local": parts[1],
                            "type": parts[2],
                            "options": parts[3] if len(parts) > 3 else "",
                        })
    except Exception:
        pass
    return mounts


def mount_share(
    remote: str,
    local: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    domain: Optional[str] = None,
    options: Optional[str] = None,
) -> tuple[bool, str]:
    """Mount a remote CIFS share to a local directory.

    Args:
        remote: Remote share path (e.g., //server/share).
        local: Local mount point.
        username: SMB username (optional for guest).
        password: SMB password.
        domain: SMB domain/workgroup.
        options: Additional mount options string.

    Returns:
        (success, message) tuple.
    """
    # Normalize remote path
    if not remote.startswith("//"):
        remote = "//" + remote.lstrip("/")

    # Create mount point
    if not os.path.exists(local):
        try:
            os.makedirs(local, exist_ok=True)
        except PermissionError:
            run_cmd(["mkdir", "-p", local], sudo=True, check=False)

    # Build mount command
    if platform.system() == "Darwin":
        # macOS uses mount_smbfs.  mount_smbfs has no credentials-file interface,
        # so we embed only the username in the URL and let the OS prompt for the
        # password via its native authentication dialog.  Embedding the password
        # in the URL exposes it in `ps aux`; omitting it avoids that risk.
        if username:
            remote_with_user = remote.replace("//", f"//{username}@")
        else:
            remote_with_user = remote
        cmd = ["mount_smbfs", remote_with_user, local]
        try:
            run_cmd(cmd, sudo=True)
            return True, f"Mounted {remote} at {local}"
        except Exception as e:
            return False, f"Mount failed: {e}"

    # Linux uses mount -t cifs with a credentials file so the password is
    # never visible in the process table or shell history.
    cmd = ["mount", "-t", "cifs", remote, local]
    mount_opts: list[str] = []
    creds_path: Optional[str] = None

    try:
        if username or password or domain:
            creds_lines: list[str] = []
            if username:
                creds_lines.append(f"username={username}")
            if password:
                creds_lines.append(f"password={password}")
            if domain:
                creds_lines.append(f"domain={domain}")
            creds_content = "\n".join(creds_lines) + "\n"

            # Write to a temp file readable only by the current user
            creds_fd, creds_path = tempfile.mkstemp(suffix=".cred", prefix="sambasense_")
            os.chmod(creds_path, 0o600)
            with os.fdopen(creds_fd, "w") as f:
                f.write(creds_content)
            mount_opts.append(f"credentials={creds_path}")
        else:
            mount_opts.append("guest")

        mount_opts.append(f"uid={os.getuid()}")
        mount_opts.append(f"gid={os.getgid()}")
        if options:
            mount_opts.append(options)
        cmd += ["-o", ",".join(mount_opts)]

        run_cmd(cmd, sudo=True)
        return True, f"Mounted {remote} at {local}"
    except Exception as e:
        return False, f"Mount failed: {e}"
    finally:
        if creds_path and os.path.exists(creds_path):
            try:
                os.unlink(creds_path)
            except OSError:
                pass


def unmount_share(local: str) -> tuple[bool, str]:
    """Unmount a CIFS share.

    Args:
        local: Local mount point to unmount.

    Returns:
        (success, message) tuple.
    """
    try:
        run_cmd(["umount", local], sudo=True)
        return True, f"Unmounted {local}"
    except Exception as e:
        return False, f"Unmount failed: {e}"


def add_fstab_entry(
    remote: str,
    local: str,
    credentials_file: Optional[str] = None,
    options: str = "defaults,noauto,user",
) -> tuple[bool, str]:
    """Add a persistent mount entry to /etc/fstab.

    Args:
        remote: Remote share path.
        local: Local mount point.
        credentials_file: Path to credentials file for authentication.
        options: Mount options.

    Returns:
        (success, message) tuple.
    """
    if not remote.startswith("//"):
        remote = "//" + remote.lstrip("/")

    mount_opts = options
    if credentials_file:
        mount_opts += f",credentials={credentials_file}"

    fstab_line = f"{remote}  {local}  cifs  {mount_opts}  0  0\n"

    # Check for existing entry — match the first field exactly to avoid
    # substring false-positives (e.g. //server/share matching //server/share2)
    def _fstab_has_entry(content: str) -> bool:
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.split()[0] == remote:
                return True
        return False

    try:
        with open("/etc/fstab", "r") as f:
            if _fstab_has_entry(f.read()):
                return False, f"Entry for {remote} already exists in fstab."
    except PermissionError:
        result = run_cmd(["cat", "/etc/fstab"], sudo=True, check=False)
        if _fstab_has_entry(result.stdout):
            return False, f"Entry for {remote} already exists in fstab."

    try:
        # Pipe content via stdin to tee — no shell involved, safe from injection
        run_cmd(["tee", "-a", "/etc/fstab"], sudo=True, input=fstab_line)
        return True, f"Added fstab entry for {remote}."
    except Exception as e:
        return False, f"Failed to add fstab entry: {e}"


def remove_fstab_entry(remote: str) -> tuple[bool, str]:
    """Remove a CIFS entry from /etc/fstab.

    Returns:
        (success, message) tuple.
    """
    try:
        result = run_cmd(["cat", "/etc/fstab"], sudo=True, check=False)
        lines = result.stdout.splitlines(keepends=True)
        new_lines = [l for l in lines if remote not in l]
        if len(new_lines) == len(lines):
            return False, f"No fstab entry found for {remote}."
        new_content = "".join(new_lines)
        # Pipe content via stdin to tee — no shell involved, safe from injection
        run_cmd(["tee", "/etc/fstab"], sudo=True, input=new_content)
        return True, f"Removed fstab entry for {remote}."
    except Exception as e:
        return False, f"Failed to remove fstab entry: {e}"
