"""Theme manager — dark/light mode toggle and dynamic accent colors.

Generates a full QSS stylesheet from the current mode and accent color.
Implements a Material-You inspired design language.
"""

import json
import os
from typing import Optional

from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


# ── Default palette ──────────────────────────────────────────

DEFAULT_ACCENT = "#FFD700"

_DARK = {
    "bg_primary": "#0a0a0b",
    "bg_secondary": "#141416",
    "bg_tertiary": "#1c1c1f",
    "bg_surface": "#222226",
    "bg_hover": "#2a2a2f",
    "bg_pressed": "#333338",
    "text_primary": "#f0f0f2",
    "text_secondary": "#a0a0a8",
    "text_dim": "#606068",
    "border": "#2a2a30",
    "border_focus": "#3a3a42",
    "danger": "#ff4d6a",
    "success": "#4ade80",
    "warning": "#fbbf24",
    "info": "#60a5fa",
}

_LIGHT = {
    "bg_primary": "#fafafa",
    "bg_secondary": "#f0f0f2",
    "bg_tertiary": "#e8e8ec",
    "bg_surface": "#ffffff",
    "bg_hover": "#eaeaee",
    "bg_pressed": "#d8d8de",
    "text_primary": "#18181b",
    "text_secondary": "#52525b",
    "text_dim": "#a1a1aa",
    "border": "#e0e0e4",
    "border_focus": "#c8c8ce",
    "danger": "#ef4444",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "info": "#3b82f6",
}

_SETTINGS_FILE = os.path.expanduser("~/.config/sambasense/theme.json")


class ThemeManager:
    """Manages app theming — mode, accent color, QSS generation."""

    def __init__(self):
        self.dark_mode: bool = True
        self.accent: str = DEFAULT_ACCENT
        self._load_settings()

    # ── Persistence ────────────────────────────────────────

    def _load_settings(self):
        try:
            if os.path.exists(_SETTINGS_FILE):
                with open(_SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                    self.dark_mode = data.get("dark_mode", True)
                    self.accent = data.get("accent", DEFAULT_ACCENT)
        except Exception:
            pass

    def save_settings(self):
        os.makedirs(os.path.dirname(_SETTINGS_FILE), exist_ok=True)
        with open(_SETTINGS_FILE, "w") as f:
            json.dump({"dark_mode": self.dark_mode, "accent": self.accent}, f)

    # ── Palette access ─────────────────────────────────────

    @property
    def palette(self) -> dict[str, str]:
        return dict(_DARK) if self.dark_mode else dict(_LIGHT)

    def toggle_mode(self):
        self.dark_mode = not self.dark_mode
        self.save_settings()

    def set_accent(self, color: str):
        self.accent = color
        self.save_settings()

    # ── Derived colors ─────────────────────────────────────

    def get_contrast_text(self, hex_color: str) -> str:
        """Return black or white text depending on background luminance."""
        c = QColor(hex_color)
        # Calculate relative luminance using standard formula
        # L = 0.2126 * R + 0.7152 * G + 0.0722 * B
        lum = 0.2126 * c.red() + 0.7152 * c.green() + 0.0722 * c.blue()
        # Threshold of 128 (approx middle of 0-255) is common
        return "#000000" if lum > 140 else "#ffffff"

    def accent_hover(self) -> str:
        c = QColor(self.accent)
        c.setAlpha(200)
        if self.dark_mode:
            return c.lighter(120).name()
        return c.darker(110).name()

    def accent_pressed(self) -> str:
        c = QColor(self.accent)
        if self.dark_mode:
            return c.darker(130).name()
        return c.darker(140).name()

    def accent_bg(self) -> str:
        """Subtle accent background (10% opacity equivalent)."""
        c = QColor(self.accent)
        if self.dark_mode:
            return f"rgba({c.red()}, {c.green()}, {c.blue()}, 25)"
        return f"rgba({c.red()}, {c.green()}, {c.blue()}, 30)"

    # ── QSS Generation ─────────────────────────────────────

    def generate_stylesheet(self) -> str:
        p = self.palette
        a = self.accent
        ah = self.accent_hover()
        ap = self.accent_pressed()
        ab = self.accent_bg()
        act = self.get_contrast_text(a)

        return f"""
/* ── Global ────────────────────────────────────────── */
* {{
    font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
    font-size: 13px;
    color: {p['text_primary']};
}}

QMainWindow, QWidget#centralWidget {{
    background-color: {p['bg_primary']};
}}

/* ── Sidebar ───────────────────────────────────────── */
QWidget#sidebar {{
    background-color: {p['bg_secondary']};
    border-right: 1px solid {p['border']};
}}

QPushButton#navButton {{
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 12px 18px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
    color: {p['text_secondary']};
}}

QPushButton#navButton:hover {{
    background-color: {p['bg_hover']};
    color: {p['text_primary']};
}}

QPushButton#navButton:checked {{
    background-color: {ab};
    color: {a};
    font-weight: 600;
}}

/* ── Cards ─────────────────────────────────────────── */
QFrame#card {{
    background-color: {p['bg_surface']};
    border: 1px solid {p['border']};
    border-radius: 14px;
    padding: 14px;
}}

QFrame#card:hover {{
    border-color: {p['border_focus']};
}}

/* ── Buttons ───────────────────────────────────────── */
QPushButton#primaryButton {{
    background-color: {a};
    color: {act};
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton#primaryButton:hover {{
    background-color: {ah};
}}

QPushButton#primaryButton:pressed {{
    background-color: {ap};
}}

QPushButton#primaryButton:disabled {{
    background-color: {p['bg_tertiary']};
    color: {p['text_dim']};
}}

QPushButton#secondaryButton {{
    background-color: {p['bg_tertiary']};
    color: {p['text_primary']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    padding: 10px 24px;
    font-weight: 500;
}}

QPushButton#secondaryButton:hover {{
    background-color: {p['bg_hover']};
    border-color: {p['border_focus']};
}}

QPushButton#secondaryButton:disabled {{
    background-color: {p['bg_primary']};
    color: {p['text_dim']};
    border: 1px solid {p['border']};
}}

QPushButton#dangerButton {{
    background-color: {p['danger']};
    color: #ffffff;
    border: none;
    border-radius: 10px;
    padding: 10px 24px;
    font-weight: 600;
}}

QPushButton#dangerButton:hover {{
    background-color: {QColor(p['danger']).lighter(115).name()};
}}

/* ── Inputs ────────────────────────────────────────── */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {p['bg_tertiary']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    color: {p['text_primary']};
    selection-background-color: {a};
    selection-color: #0a0a0b;
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {a};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {p['bg_surface']};
    border: 1px solid {p['border']};
    border-radius: 8px;
    padding: 4px;
    selection-background-color: {ab};
    selection-color: {p['text_primary']};
}}

/* ── Checkboxes ────────────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    color: {p['text_primary']};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {p['border']};
    background-color: {p['bg_tertiary']};
}}

QCheckBox::indicator:checked {{
    background-color: {a};
    border-color: {a};
}}

/* ── ScrollBar ─────────────────────────────────────── */
QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {p['text_dim']};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {p['text_secondary']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: transparent;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background-color: {p['text_dim']};
    border-radius: 4px;
    min-width: 30px;
}}

/* ── Tables ────────────────────────────────────────── */
QTableWidget {{
    background-color: {p['bg_surface']};
    border: 1px solid {p['border']};
    border-radius: 12px;
    gridline-color: {p['border']};
    selection-background-color: {ab};
    selection-color: {p['text_primary']};
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {p['border']};
}}

QHeaderView::section {{
    background-color: {p['bg_tertiary']};
    color: {p['text_secondary']};
    padding: 10px 8px;
    border: none;
    border-bottom: 1px solid {p['border']};
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
}}

/* ── Labels ────────────────────────────────────────── */
QLabel#heading {{
    font-size: 22px;
    font-weight: 700;
    color: {p['text_primary']};
}}

QLabel#subheading {{
    font-size: 14px;
    font-weight: 500;
    color: {p['text_secondary']};
}}

QLabel#accentLabel {{
    color: {a};
    font-weight: 700;
    font-size: 24px;
}}

QLabel#dimLabel {{
    color: {p['text_dim']};
    font-size: 11px;
}}

/* ── Status badges ─────────────────────────────────── */
QLabel#statusRunning {{
    background-color: rgba({QColor(p['success']).red()}, {QColor(p['success']).green()}, {QColor(p['success']).blue()}, 40);
    color: {p['success']};
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 12px;
}}

QLabel#statusStopped {{
    background-color: rgba({QColor(p['danger']).red()}, {QColor(p['danger']).green()}, {QColor(p['danger']).blue()}, 40);
    color: {p['danger']};
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 12px;
}}

QLabel#statusUnknown {{
    background-color: rgba({QColor(p['text_dim']).red()}, {QColor(p['text_dim']).green()}, {QColor(p['text_dim']).blue()}, 40);
    color: {p['text_secondary']};
    border-radius: 6px;
    padding: 4px 12px;
    font-weight: 600;
    font-size: 12px;
}}

/* ── Tooltips ──────────────────────────────────────── */
QToolTip {{
    background-color: {p['bg_surface']};
    color: {p['text_primary']};
    border: 1px solid {p['border']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── Tab bar (for dialogs) ─────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {p['border']};
    border-radius: 8px;
    background-color: {p['bg_surface']};
}}

QTabBar::tab {{
    background-color: {p['bg_tertiary']};
    color: {p['text_secondary']};
    padding: 8px 16px;
    border: none;
    border-bottom: 2px solid transparent;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    color: {a};
    border-bottom: 2px solid {a};
}}

QTabBar::tab:hover {{
    color: {p['text_primary']};
}}

/* ── Group Box ─────────────────────────────────────── */
QGroupBox {{
    background-color: {p['bg_surface']};
    border: 1px solid {p['border']};
    border-radius: 12px;
    padding: 16px;
    padding-top: 36px;
    margin-top: 12px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
    color: {p['text_primary']};
    background-color: {p['bg_surface']}; /* Hide border behind title */
}}

/* ── Message Box ───────────────────────────────────── */
QMessageBox {{
    background-color: {p['bg_surface']};
}}

QMessageBox QLabel {{
    color: {p['text_primary']};
}}

/* ── Progress Bar ──────────────────────────────────── */
QProgressBar {{
    background-color: {p['bg_tertiary']};
    border: none;
    border-radius: 6px;
    height: 10px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {a};
    border-radius: 6px;
}}
"""

    def apply(self, app: QApplication):
        """Apply the generated stylesheet to the application."""
        app.setStyleSheet(self.generate_stylesheet())
