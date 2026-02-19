# SambaSense

<p align="center">
  <img src="assets/sambasense.svg" alt="SambaSense" width="96"/>
</p>

<p align="center">
  <strong>A modern Samba configuration &amp; management application</strong><br/>
  <em>Built with Python 3 &amp; PyQt6 — CLI &amp; GUI</em>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white"/>
  <img alt="PyQt6" src="https://img.shields.io/badge/PyQt6-6.5+-41CD52?style=flat-square&logo=qt&logoColor=white"/>
  <img alt="License" src="https://img.shields.io/badge/License-MIT-FFD700?style=flat-square"/>
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Linux-FCC624?style=flat-square&logo=linux&logoColor=black"/>
  <a href="https://ko-fi.com/sabylasolutions"><img alt="Ko-fi" src="https://img.shields.io/badge/Donate-Ko--fi-F16061?style=flat-square&logo=ko-fi&logoColor=white"/></a>
</p>

---

## Features

- **Install / Uninstall** — Install or remove Samba and smbclient with one click or command
- **Configure Shares** — Add, edit, and remove Samba shares with a visual editor or CLI
- **Map Network Shares** — Mount and unmount remote CIFS/SMB shares with persistent fstab support
- **Storage Dashboards** — View mapped shares and shared folders with colorful pie charts and line graphs
- **Multi-Distro & macOS Support** — Arch, Fedora, Debian, and **macOS 14+ (including Tahoe)**

## Versions & OS Support

| OS / Distro | Version Support | Status |
|-------------|-----------------|--------|
| **Arch**    | Rolling (Latest) | ✅ Supported |
| **Fedora**  | 40 / 41 / RHEL 9 | ✅ Supported |
| **Debian**  | 11 (Bullseye) / 12 (Bookworm) | ✅ Supported |
| **Ubuntu**  | 20.04 / 22.04 / 24.04 | ✅ Supported |
| **macOS**   | 14 (Sonoma) — **26 (Tahoe)** | ✅ Supported |
| **AppImage**| Portable (Any Glibc Linux) | ✅ Supported |
| **Flatpak** | Sandboxed (Flathub compatible) | ✅ Supported |

## Languages & Technologies

| Component | Technology |
|-----------|-----------|
| Core Logic | **Python 3.10+** (Darwin & Linux Aware) |
| GUI Framework | **PyQt6** |
| Charts | Custom **QPainter** (zero external chart deps) |
| Icons | Programmatic **SVG** (Inline & Dynamic) |
| CLI | **argparse** with POSIX/Launchd handling |

## Dark Mode & macOS Aesthetics

SambaSense features a **Material You**-inspired design that adapts to its host:

- **True Dark Mode** — deep black background with gold `#FFD700` accents
- **Native Fonts** — Uses **Inter** (Linux) or native macOS system typography
- **Accent picker** — choice of color accents that persist across restarts
- **macOS Native Features** — Uses `launchctl` for service management and `mount_smbfs` for native integration.

## Capabilities

### GUI Application
- Sidebar navigation with consolidated **Storage Dashboard**
- Install & Manage — package status badges, service start/stop/enable/disable
- Configure Shares — table view with inline edit/delete, add share dialog
- Map Shares — mount remote CIFS/SMB shares with credential input
- Storage Dashboard — two-column layout with donuts and line graphs for local/remote storage

### CLI Mode
Every feature is accessible via the `sambasense` command:

```
sambasense [command] [options]
```

| Command | Description |
|---------|-------------|
| `sambasense status` | Show samba installation & service status |
| `sambasense dash` | Display unified storage dashboard in terminal |
| `sambasense gui` | Launch the GUI application |
| `sambasense --version` | Print version (v1.0.0) |

## Installation

### From Source (Development)
```bash
git clone https://github.com/sambasense/sambasense.git
cd sambasense
pip install -e .
sambasense --help
```

### Quick Run (No Install)
```bash
python3 -m sambasense --help     # CLI
python3 -m sambasense gui        # GUI
```

## Packages

| Format | Platform | Build | Download |
|--------|----------|-------|----------|
| `.deb` | Debian / Ubuntu / Pop!_OS | `packaging/deb/build.sh` | [Download .deb](https://github.com/sambasense/sambasense/releases/v1.0.0/download/sambasense_1.0.0.deb) |
| `.rpm` | Fedora / RHEL / CentOS | `packaging/rpm/build.sh` | [Download .rpm](https://github.com/sambasense/sambasense/releases/v1.0.0/download/sambasense-1.0.0-1.fc40.noarch.rpm) |
| `.pkg.tar.zst` | Arch / Endeavour / Manjaro | `packaging/arch/build.sh` | [Download .pkg.tar.zst](https://github.com/sambasense/sambasense/releases/v1.0.0/download/sambasense-1.0.0-1-any.pkg.tar.zst) |
| AppImage | Portable Linux | `packaging/appimage/build.sh` | [Download AppImage](https://github.com/sambasense/sambasense/releases/v1.0.0/download/SambaSense-x86_64.AppImage) |
| Flatpak | Sandboxed Linux | `packaging/flatpak/build.sh` | [Download Flatpak](https://github.com/sambasense/sambasense/releases/v1.0.0/download/SambaSense.flatpak) |
| Homebrew | macOS (Darwin) | `brew install sambasense` | [GitHub Release](https://github.com/sambasense/sambasense/releases/v1.0.0) |

## Requirements

- Python 3.10+
- PyQt6 ≥ 6.5
- Linux with `systemd` OR macOS 14+ with `launchd`
- `samba`, `smbclient`, `cifs-utils`

---

## ⚠️ Disclaimer

**USE AT YOUR OWN RISK.** This software is provided "as is", without warranty of any kind, express or implied. The author(s) and contributors are **not liable** for any damage to systems, servers, data loss, network disruptions, or any other issues that may arise from the use, misuse, or inability to use this software. This application manages system services and modifies system configuration files — always review changes and maintain proper backups. By using SambaSense, you accept full responsibility for any outcomes.

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Made with ☕ by <a href="https://ko-fi.com/sabylasolutions">Sabyla Solutions</a></sub>
</p>
