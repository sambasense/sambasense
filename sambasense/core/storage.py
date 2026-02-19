"""Storage information and disk usage statistics."""

import hashlib
import json
import os
import shutil
import time
from pathlib import Path
from typing import Optional

from sambasense.core.config import list_shares
from sambasense.core.mapper import list_mounted_shares


import platform

# Simple file-based history storage
if platform.system() == "Darwin":
    _HISTORY_DIR = os.path.expanduser("~/Library/Application Support/sambasense/history")
else:
    _HISTORY_DIR = os.path.expanduser("~/.local/share/sambasense/history")


def get_disk_usage(path: str) -> dict[str, int]:
    """Get disk usage statistics for a path.

    Returns:
        Dict with keys: 'total', 'used', 'free' (in bytes).
    """
    try:
        usage = shutil.disk_usage(path)
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
        }
    except (OSError, FileNotFoundError):
        return {"total": 0, "used": 0, "free": 0}


def get_usage_percent(path: str) -> float:
    """Get usage percentage for a path (0-100)."""
    usage = get_disk_usage(path)
    if usage["total"] == 0:
        return 0.0
    return (usage["used"] / usage["total"]) * 100.0


def get_all_share_stats() -> list[dict]:
    """Get storage stats for all configured Samba shares.

    Returns:
        List of dicts with: 'name', 'path', 'total', 'used', 'free', 'percent'.
    """
    shares = list_shares()
    stats = []
    for name, config in shares.items():
        path = config.get("path", "")
        if not path:
            continue
        usage = get_disk_usage(path)
        total = usage["total"]
        percent = (usage["used"] / total * 100.0) if total > 0 else 0.0
        stats.append({
            "name": name,
            "path": path,
            "comment": config.get("comment", ""),
            "writable": config.get("writable", "no"),
            "guest_ok": config.get("guest ok", "no"),
            "total": usage["total"],
            "used": usage["used"],
            "free": usage["free"],
            "percent": round(percent, 1),
        })
    return stats


def get_all_mount_stats() -> list[dict]:
    """Get storage stats for all mounted CIFS/SMB shares.

    Returns:
        List of dicts with: 'remote', 'local', 'total', 'used', 'free', 'percent'.
    """
    mounts = list_mounted_shares()
    stats = []
    for mount in mounts:
        local = mount["local"]
        usage = get_disk_usage(local)
        total = usage["total"]
        percent = (usage["used"] / total * 100.0) if total > 0 else 0.0
        stats.append({
            "remote": mount["remote"],
            "local": local,
            "type": mount["type"],
            "total": usage["total"],
            "used": usage["used"],
            "free": usage["free"],
            "percent": round(percent, 1),
        })
    return stats


def _ensure_history_dir():
    """Ensure the history directory exists."""
    os.makedirs(_HISTORY_DIR, exist_ok=True)


def record_usage(path: str, label: str = ""):
    """Record a usage data point for a path (for line graph history).

    Args:
        path: Filesystem path to record.
        label: Friendly label (share name or mount point).
    """
    _ensure_history_dir()
    safe_name = hashlib.sha256(path.encode()).hexdigest()
    history_file = os.path.join(_HISTORY_DIR, f"{safe_name}.json")

    data_points = _load_history_file(history_file)

    usage = get_disk_usage(path)
    data_points.append({
        "timestamp": int(time.time()),
        "total": usage["total"],
        "used": usage["used"],
        "free": usage["free"],
        "label": label or path,
    })

    # Keep last 100 data points
    data_points = data_points[-100:]

    with open(history_file, "w") as f:
        json.dump(data_points, f, indent=2)


def get_usage_history(path: str, max_points: int = 50) -> list[dict]:
    """Retrieve usage history for a path.

    Returns:
        List of dicts with: 'timestamp', 'total', 'used', 'free', 'label'.
    """
    safe_name = hashlib.sha256(path.encode()).hexdigest()
    history_file = os.path.join(_HISTORY_DIR, f"{safe_name}.json")
    data = _load_history_file(history_file)
    return data[-max_points:]


def _load_history_file(filepath: str) -> list[dict]:
    """Load a JSON history file, returning empty list if missing/corrupt."""
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def record_all_shares():
    """Record usage data for all configured shares (for periodic snapshots)."""
    for stat in get_all_share_stats():
        record_usage(stat["path"], label=stat["name"])


def record_all_mounts():
    """Record usage data for all mounted shares (for periodic snapshots)."""
    for stat in get_all_mount_stats():
        record_usage(stat["local"], label=stat["remote"])
