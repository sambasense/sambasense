"""SambaSense main application — sidebar navigation, theme toggle, accent picker."""

import sys
import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QFont, QFontDatabase, QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QColorDialog, QSizePolicy,
    QPushButton, QStackedWidget, QLabel, QColorDialog, QSizePolicy,
    QSpacerItem,
)
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from sambasense.gui.widgets.toggle import ToggleSwitch

from sambasense import __app_name__, __version__
from sambasense.gui.theme import ThemeManager
from sambasense.gui.icons import (
    icon_download, icon_folder_share, icon_link,
    icon_download, icon_folder_share, icon_link,
    icon_chart_pie, icon_chart_line, icon_sun, icon_moon, icon_palette,
    icon_coffee,
)
from sambasense.gui.pages.install_page import InstallPage
from sambasense.gui.pages.shares_page import SharesPage
from sambasense.gui.pages.map_page import MapPage
from sambasense.gui.pages.dashboard_page import DashboardPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._theme = ThemeManager()
        self.setWindowTitle(f"{__app_name__} — Samba Management")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        accent = self._theme.accent
        self.setWindowIcon(icon_folder_share(accent))

        # Main widget & layout
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ─────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(12)

        # App branding
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(8, 0, 0, 16)
        brand_row.setSpacing(8)

        self._brand_icon = QLabel()
        brand_row.addWidget(self._brand_icon)

        self._brand_label = QLabel(__app_name__)
        brand_row.addWidget(self._brand_label)
        brand_row.addStretch()
        sidebar_layout.addLayout(brand_row)

        self._nav_buttons: list[QPushButton] = []
        nav_items = [
            ("Local Shares", icon_chart_pie),
            ("Remote Mounts", icon_link),
            ("Install && Manage", icon_download),
            ("Configure Shares", icon_folder_share),
            ("Map Shares", icon_link),
        ]

        for i, (label, icon_fn) in enumerate(nav_items):
            btn = QPushButton(f"  {label}")
            btn.setObjectName("navButton")
            btn.setIcon(icon_fn(accent))
            btn.setIconSize(QSize(20, 20))
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setChecked(i == 0)
            btn.clicked.connect(lambda _, idx=i: self._nav_to(idx))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            sidebar_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sidebar_layout.addStretch()

        # Theme controls
        theme_container = QWidget()
        theme_container.setObjectName("themeCard")
        theme_layout = QVBoxLayout(theme_container)
        
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Dark Mode"))
        mode_row.addStretch()
        self._mode_toggle = ToggleSwitch(checked=self._theme.dark_mode, accent=accent)
        self._mode_toggle.toggled.connect(self._toggle_mode)
        mode_row.addWidget(self._mode_toggle)
        theme_layout.addLayout(mode_row)

        picker_row = QHBoxLayout()
        picker_row.addWidget(QLabel("Accent"))
        picker_row.addStretch()
        self._accent_btn = QPushButton()
        self._accent_btn.setObjectName("accentButton")
        self._accent_btn.setFixedSize(32, 32)
        self._accent_btn.setIcon(icon_palette(accent))
        self._accent_btn.clicked.connect(self._pick_accent)
        picker_row.addWidget(self._accent_btn)
        theme_layout.addLayout(picker_row)
        
        # Ko-fi Button
        self._kofi_btn = QPushButton("  Buy me a coffee")
        self._kofi_btn.setObjectName("navButton")
        self._kofi_btn.setIcon(icon_coffee(accent))
        self._kofi_btn.setIconSize(QSize(20, 20))
        self._kofi_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._kofi_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://ko-fi.com/sabylasolutions")))
        theme_layout.addWidget(self._kofi_btn)

        sidebar_layout.addWidget(theme_container)

        root.addWidget(sidebar)

        # ── Main content ────────────────────────────────────
        central.setObjectName("centralWidget")
        self._stack = QStackedWidget()
        
        self._pages = [
            DashboardPage(accent=accent, is_remote=False),
            DashboardPage(accent=accent, is_remote=True),
            InstallPage(accent=accent),
            SharesPage(accent=accent),
            MapPage(accent=accent),
        ]

        for page in self._pages:
            self._stack.addWidget(page)

        root.addWidget(self._stack, 1)

        # Initialize UI state
        self._apply_theme()
        self._update_all_accents(accent)

    def _nav_to(self, index: int):
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

    def _toggle_mode(self, is_dark: bool):
        self._theme.dark_mode = is_dark
        self._theme.save_settings()
        self._apply_theme()
        self._update_toggle_style()

    def _pick_accent(self):
        color = QColorDialog.getColor(QColor(self._theme.accent), self, "Choose Accent Color")
        if color.isValid():
            new_accent = color.name().upper()
            self._theme.accent = new_accent
            self._theme.save_settings()
            self._apply_theme()
            self._update_all_accents(new_accent)

    def _update_all_accents(self, accent: str):
        self.setWindowIcon(icon_folder_share(accent))
        
        # Update branding
        self._brand_icon.setPixmap(icon_folder_share(accent).pixmap(24, 24))
        self._brand_label.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {accent};")
        
        # Update nav icons
        icon_fns = [icon_chart_pie, icon_link, icon_download, icon_folder_share, icon_link]
        for btn, fn in zip(self._nav_buttons, icon_fns):
            btn.setIcon(fn(accent))

        self._accent_btn.setIcon(icon_palette(accent))
        self._kofi_btn.setIcon(icon_coffee(accent))
        self._update_toggle_style()

        # Update pages
        for page in self._pages:
            if hasattr(page, "update_accent"):
                page.update_accent(accent)

    def _update_toggle_style(self):
        accent = self._theme.accent
        self._mode_toggle.set_accent(accent)
        if self._theme.dark_mode:
            self._mode_toggle.set_track_off("#3a3a42")
        else:
            self._mode_toggle.set_track_off("#d0d0d8")

    def _apply_theme(self):
        app = QApplication.instance()
        if app:
            self._theme.apply(app)


def run_app():
    """Launch the SambaSense GUI application."""
    import traceback
    
    try:
        app = QApplication(sys.argv)
        app.setApplicationName(__app_name__)
        app.setApplicationVersion(__version__)

        window = MainWindow()
        window.show()
        window.raise_()
        window.activateWindow()
        
        sys.exit(app.exec())
        
    except Exception:
        crash_dir = os.path.expanduser("~/.local/share/sambasense")
        os.makedirs(crash_dir, exist_ok=True)
        crash_log = os.path.join(crash_dir, "crash.log")
        with open(crash_log, "w") as f:
            f.write(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    run_app()
