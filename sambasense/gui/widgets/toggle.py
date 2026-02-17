"""Animated toggle switch widget for dark/light mode switching."""

from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import QWidget, QSizePolicy


class ToggleSwitch(QWidget):
    """A Material-style animated toggle switch.

    Emits `toggled(bool)` when the user clicks to change state.
    """

    toggled = pyqtSignal(bool)

    def __init__(
        self,
        parent=None,
        checked: bool = False,
        accent: str = "#FFD700",
        track_off: str = "#3a3a42",
        knob_off: str = "#a0a0a8",
        width: int = 52,
        height: int = 28,
    ):
        super().__init__(parent)
        self._checked = checked
        self._accent = accent
        self._track_off = track_off
        self._knob_off = knob_off
        self._w = width
        self._h = height

        self.setFixedSize(width, height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Knob position (0.0 = left/off, 1.0 = right/on)
        self._knob_pos = 1.0 if checked else 0.0

        # Animation
        self._animation = QPropertyAnimation(self, b"knobPosition", self)
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

    # ── Qt property for animation ────────────────────────

    def _get_knob_pos(self) -> float:
        return self._knob_pos

    def _set_knob_pos(self, pos: float):
        self._knob_pos = pos
        self.update()

    knobPosition = pyqtProperty(float, _get_knob_pos, _set_knob_pos)

    # ── Public API ───────────────────────────────────────

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool):
        if self._checked == checked:
            return
        self._checked = checked
        self._animate()
        self.toggled.emit(self._checked)

    def set_accent(self, color: str):
        self._accent = color
        self.update()

    def set_track_off(self, color: str):
        self._track_off = color
        self.update()

    # ── Events ───────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._checked = not self._checked
            self._animate()
            self.toggled.emit(self._checked)

    def _animate(self):
        self._animation.stop()
        self._animation.setStartValue(self._knob_pos)
        self._animation.setEndValue(1.0 if self._checked else 0.0)
        self._animation.start()

    # ── Painting ─────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        radius = h / 2

        # Interpolate track color based on knob position
        off_color = QColor(self._track_off)
        on_color = QColor(self._accent)
        t = self._knob_pos
        track_r = int(off_color.red() + (on_color.red() - off_color.red()) * t)
        track_g = int(off_color.green() + (on_color.green() - off_color.green()) * t)
        track_b = int(off_color.blue() + (on_color.blue() - off_color.blue()) * t)
        track_color = QColor(track_r, track_g, track_b)

        # Draw track
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)

        # Draw knob
        knob_r = (h - 8) / 2
        knob_x = 4 + self._knob_pos * (w - h)
        knob_y = h / 2

        # Knob shadow
        shadow = QColor(0, 0, 0, 40)
        painter.setBrush(QBrush(shadow))
        painter.drawEllipse(QRectF(knob_x + 0.5, knob_y - knob_r + 1, knob_r * 2, knob_r * 2))

        # Knob
        knob_color = QColor("#ffffff") if self._checked else QColor(self._knob_off)
        painter.setBrush(QBrush(knob_color))
        painter.drawEllipse(QRectF(knob_x, knob_y - knob_r, knob_r * 2, knob_r * 2))

        painter.end()
