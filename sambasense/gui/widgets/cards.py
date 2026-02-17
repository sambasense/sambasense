"""Material-style info cards for displaying storage and status data."""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy, QGraphicsDropShadowEffect,
)


class InfoCard(QFrame):
    """Rounded material card with icon, title, value, and subtitle."""

    def __init__(
        self,
        title: str = "",
        value: str = "",
        subtitle: str = "",
        icon_fn: Optional[callable] = None,
        accent: str = "#FFD700",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(120)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        # Icon area
        self._icon_fn = icon_fn
        self._icon_label = None
        if icon_fn:
            self._icon_label = QLabel()
            self._icon_label.setPixmap(icon_fn(accent).pixmap(32, 32))
            self._icon_label.setFixedSize(48, 48)
            self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._icon_label.setStyleSheet(
                f"background-color: rgba({QColor(accent).red()}, "
                f"{QColor(accent).green()}, {QColor(accent).blue()}, 25);"
                f"border-radius: 12px;"
            )
            layout.addWidget(self._icon_label)

        # Text area
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("dimLabel")
        self._title_label.setStyleSheet("font-size: 11px; text-transform: uppercase; letter-spacing: 1px;")

        self._value_label = QLabel(value)
        self._value_label.setObjectName("accentLabel")

        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setObjectName("dimLabel")
        self._subtitle_label.setStyleSheet("font-size: 12px;")

        text_layout.addWidget(self._title_label)
        text_layout.addWidget(self._value_label)
        text_layout.addWidget(self._subtitle_label)
        text_layout.addStretch()

        layout.addLayout(text_layout)
        layout.addStretch()

    def set_value(self, value: str):
        self._value_label.setText(value)

    def set_subtitle(self, subtitle: str):
        self._subtitle_label.setText(subtitle)

    def set_title(self, title: str):
        self._title_label.setText(title)

    def update_accent(self, accent: str):
        self._accent = accent
        if self._icon_label and self._icon_fn:
            # Update icon pixmap (regenerate with new accent)
            try:
                self._icon_label.setPixmap(self._icon_fn(accent).pixmap(32, 32))
            except Exception:
                pass
            
            qc = QColor(accent)
            self._icon_label.setStyleSheet(
                f"background-color: rgba({qc.red()}, {qc.green()}, {qc.blue()}, 25);"
                f"border-radius: 12px;"
            )


class StatusBadge(QLabel):
    """Small status indicator badge that preserves its category label."""

    def __init__(self, label: str, status: str = "unknown", parent=None):
        super().__init__(parent)
        self._label = label
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(32)
        self.set_status(status)

    def set_status(self, status: str):
        status_lower = status.lower()
        if status_lower in ("running", "active", "installed", "mounted"):
            self.setObjectName("statusRunning")
        elif status_lower in ("stopped", "inactive", "not-installed", "unmounted"):
            self.setObjectName("statusStopped")
        else:
            self.setObjectName("statusUnknown")
        
        display_status = status.replace("-", " ").title()
        self.setText(f"{self._label}: {display_status}")
        
        # Force style recalculation
        self.style().unpolish(self)
        self.style().polish(self)
