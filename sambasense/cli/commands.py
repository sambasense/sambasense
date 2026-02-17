"""SambaSense CLI commands - argparse-based command interface."""

import argparse
import sys

from sambasense import __version__, __app_name__
from sambasense.core.utils import format_bytes, detect_distro, get_package_manager
from sambasense.core.installer import (
    is_samba_installed,
    is_smbclient_installed,
    is_cifs_installed,
    get_service_status,
    install_samba,
    uninstall_samba,
    enable_service,
    disable_service,
)
from sambasense.core.config import (
    list_shares,
    add_share,
    remove_share,
    restart_samba,
    validate_conf,
)
from sambasense.core.mapper import (
    mount_share,
    unmount_share,
    list_mounted_shares,
)
from sambasense.core.storage import (
    get_all_share_stats,
    get_all_mount_stats,
    get_disk_usage,
    record_all_shares,
    record_all_mounts,
)


# ── ANSI colors ──────────────────────────────────────────────
GOLD = "\033[38;2;255;215;0m"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _status_color(status: str) -> str:
    """Color a status string."""
    if status in ("running", "installed", "yes"):
        return f"{GREEN}{status}{RESET}"
    elif status in ("stopped", "not-installed", "no"):
        return f"{RED}{status}{RESET}"
    return f"{DIM}{status}{RESET}"


def _header(title: str):
    """Print a styled header."""
    print(f"\n{GOLD}{'━' * 50}{RESET}")
    print(f"{GOLD}{BOLD}  {title}{RESET}")
    print(f"{GOLD}{'━' * 50}{RESET}")


def _bar(percent: float, width: int = 30) -> str:
    """Create an ASCII bar chart."""
    filled = int(width * percent / 100)
    empty = width - filled
    if percent >= 90:
        color = RED
    elif percent >= 70:
        color = GOLD
    else:
        color = GREEN
    return f"{color}{'█' * filled}{'░' * empty}{RESET} {percent:.1f}%"


# ── Command handlers ────────────────────────────────────────


def cmd_status(_args):
    """Show samba installation and service status."""
    _header("SambaSense Status")
    distro = detect_distro()
    pkg_mgr = get_package_manager()
    samba = is_samba_installed()
    smbclient = is_smbclient_installed()
    cifs = is_cifs_installed()
    svc = get_service_status()

    print(f"  {CYAN}Distribution:{RESET}  {distro}")
    print(f"  {CYAN}Pkg Manager:{RESET}   {pkg_mgr}")
    print(f"  {CYAN}Samba:{RESET}         {_status_color('installed' if samba else 'not-installed')}")
    print(f"  {CYAN}smbclient:{RESET}     {_status_color('installed' if smbclient else 'not-installed')}")
    print(f"  {CYAN}cifs-utils:{RESET}    {_status_color('installed' if cifs else 'not-installed')}")
    print(f"  {CYAN}Service:{RESET}       {_status_color(svc)}")
    print()


def cmd_install(_args):
    """Install samba packages."""
    _header("Installing Samba")
    success, msg = install_samba()
    color = GREEN if success else RED
    print(f"  {color}{msg}{RESET}\n")
    sys.exit(0 if success else 1)


def cmd_uninstall(_args):
    """Uninstall samba packages."""
    _header("Uninstalling Samba")
    confirm = input(f"  {GOLD}Are you sure? [y/N]:{RESET} ").strip().lower()
    if confirm != "y":
        print(f"  {DIM}Cancelled.{RESET}\n")
        return
    success, msg = uninstall_samba()
    color = GREEN if success else RED
    print(f"  {color}{msg}{RESET}\n")
    sys.exit(0 if success else 1)


def cmd_enable(_args):
    """Enable samba service."""
    success, msg = enable_service()
    color = GREEN if success else RED
    print(f"  {color}{msg}{RESET}")


def cmd_disable(_args):
    """Disable samba service."""
    success, msg = disable_service()
    color = GREEN if success else RED
    print(f"  {color}{msg}{RESET}")


def cmd_share(args):
    """Share management subcommand dispatcher."""
    action = args.action

    if action == "list":
        _header("Configured Shares")
        shares = list_shares()
        if not shares:
            print(f"  {DIM}No shares configured.{RESET}\n")
            return
        for name, conf in shares.items():
            path = conf.get("path", "N/A")
            writable = conf.get("writable", "no")
            guest = conf.get("guest ok", "no")
            print(f"  {GOLD}[{name}]{RESET}")
            print(f"    path      = {path}")
            print(f"    writable  = {_status_color(writable)}")
            print(f"    guest ok  = {_status_color(guest)}")
        print()

    elif action == "add":
        name = args.name
        path = args.path
        writable = not args.readonly
        guest_ok = args.guest
        comment = args.comment or ""
        success, msg = add_share(
            name=name, path=path, comment=comment,
            writable=writable, guest_ok=guest_ok,
        )
        color = GREEN if success else RED
        print(f"  {color}{msg}{RESET}")
        if success:
            restart_samba()
            print(f"  {GREEN}Samba restarted.{RESET}")

    elif action == "remove":
        name = args.name
        success, msg = remove_share(name)
        color = GREEN if success else RED
        print(f"  {color}{msg}{RESET}")
        if success:
            restart_samba()
            print(f"  {GREEN}Samba restarted.{RESET}")

    elif action == "validate":
        success, output = validate_conf()
        if success:
            print(f"  {GREEN}Configuration valid.{RESET}")
            if args.verbose:
                print(output)
        else:
            print(f"  {RED}Configuration errors:{RESET}")
            print(output)


def cmd_mount(args):
    """Mount a remote share."""
    success, msg = mount_share(
        remote=args.remote,
        local=args.local,
        username=args.user,
        password=args.password,
    )
    color = GREEN if success else RED
    print(f"  {color}{msg}{RESET}")
    sys.exit(0 if success else 1)


def cmd_umount(args):
    """Unmount a share."""
    success, msg = unmount_share(args.local)
    color = GREEN if success else RED
    print(f"  {color}{msg}{RESET}")
    sys.exit(0 if success else 1)


def cmd_mounts(_args):
    """List mounted CIFS shares."""
    _header("Mounted Shares")
    mounts = list_mounted_shares()
    if not mounts:
        print(f"  {DIM}No CIFS shares currently mounted.{RESET}\n")
        return
    for m in mounts:
        usage = get_disk_usage(m["local"])
        print(f"  {GOLD}{m['remote']}{RESET} → {m['local']}")
        print(f"    {_bar(usage['used'] / max(usage['total'], 1) * 100)}")
        print(f"    {CYAN}Total:{RESET} {format_bytes(usage['total'])}  "
              f"{CYAN}Used:{RESET} {format_bytes(usage['used'])}  "
              f"{CYAN}Free:{RESET} {format_bytes(usage['free'])}")
    print()


def cmd_dash(_args):
    """Display a storage dashboard in the terminal."""
    _header("Local Shares")
    share_stats = get_all_share_stats()
    if not share_stats:
        print(f"  {DIM}No shares configured.{RESET}")
    else:
        for s in share_stats:
            print(f"  {GOLD}[{s['name']}]{RESET} {s['path']}")
            print(f"    {_bar(s['percent'])}")
            print(f"    {CYAN}Used:{RESET} {format_bytes(s['used'])}  "
                  f"{CYAN}Free:{RESET} {format_bytes(s['free'])}  "
                  f"{CYAN}Total:{RESET} {format_bytes(s['total'])}")

    _header("Remote Shares")
    mount_stats = get_all_mount_stats()
    if not mount_stats:
        print(f"  {DIM}No CIFS shares mounted.{RESET}")
    else:
        for m in mount_stats:
            print(f"  {GOLD}{m['remote']}{RESET} → {m['local']}")
            print(f"    {_bar(m['percent'])}")
            print(f"    {CYAN}Used:{RESET} {format_bytes(m['used'])}  "
                  f"{CYAN}Free:{RESET} {format_bytes(m['free'])}  "
                  f"{CYAN}Total:{RESET} {format_bytes(m['total'])}")

    # Record history
    record_all_shares()
    record_all_mounts()
    print()


def cmd_gui(_args):
    """Launch the GUI application."""
    try:
        from sambasense.gui.app import run_app
        run_app()
    except ImportError as e:
        print(f"  {RED}GUI dependencies not available: {e}{RESET}")
        print(f"  {DIM}Install PyQt6: pip install PyQt6{RESET}")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="sambasense",
        description=f"{GOLD}{BOLD}{__app_name__}{RESET} — Samba Configuration & Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"{DIM}Version {__version__}{RESET}",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{__app_name__} {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # status
    sub = subparsers.add_parser("status", help="Show Samba status")
    sub.set_defaults(func=cmd_status)

    # install
    sub = subparsers.add_parser("install", help="Install Samba packages")
    sub.set_defaults(func=cmd_install)

    # uninstall
    sub = subparsers.add_parser("uninstall", help="Uninstall Samba packages")
    sub.set_defaults(func=cmd_uninstall)

    # enable
    sub = subparsers.add_parser("enable", help="Enable Samba service")
    sub.set_defaults(func=cmd_enable)

    # disable
    sub = subparsers.add_parser("disable", help="Disable Samba service")
    sub.set_defaults(func=cmd_disable)

    # share
    share_parser = subparsers.add_parser("share", help="Manage Samba shares")
    share_parser.add_argument(
        "action",
        choices=["list", "add", "remove", "validate"],
        help="Share action",
    )
    share_parser.add_argument("--name", "-n", help="Share name")
    share_parser.add_argument("--path", "-p", help="Share path")
    share_parser.add_argument("--comment", "-c", help="Share comment")
    share_parser.add_argument("--readonly", action="store_true", help="Make read-only")
    share_parser.add_argument("--guest", action="store_true", help="Allow guest access")
    share_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    share_parser.set_defaults(func=cmd_share)

    # mount
    mount_parser = subparsers.add_parser("mount", help="Mount a remote share")
    mount_parser.add_argument("remote", help="Remote share (e.g., //server/share)")
    mount_parser.add_argument("local", help="Local mount point")
    mount_parser.add_argument("--user", "-u", help="SMB username")
    mount_parser.add_argument("--password", "-P", help="SMB password")
    mount_parser.set_defaults(func=cmd_mount)

    # umount
    umount_parser = subparsers.add_parser("umount", help="Unmount a share")
    umount_parser.add_argument("local", help="Local mount point to unmount")
    umount_parser.set_defaults(func=cmd_umount)

    # mounts
    sub = subparsers.add_parser("mounts", help="List mounted CIFS shares")
    sub.set_defaults(func=cmd_mounts)

    # dash
    sub = subparsers.add_parser("dash", help="Storage dashboard")
    sub.set_defaults(func=cmd_dash)

    # gui
    sub = subparsers.add_parser("gui", help="Launch GUI application")
    sub.set_defaults(func=cmd_gui)

    return parser


def cli_main():
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)
