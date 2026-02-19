"""Custom-painted chart widgets — pie charts and line graphs.

Uses QPainter for zero-dependency, theme-aware visualizations.
"""

import math
from typing import Optional

from PyQt6.QtCore import Qt, QRectF, QPointF, QSize
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QLinearGradient, QPainterPath
from PyQt6.QtWidgets import QWidget, QSizePolicy, QToolTip
from PyQt6.QtCore import pyqtSignal


# ── Color palettes for charts ────────────────────────────────

CHART_COLORS = [
    "#FFD700", "#4ade80", "#60a5fa", "#f472b6", "#a78bfa",
    "#fb923c", "#34d399", "#f87171", "#38bdf8", "#e879f9",
    "#facc15", "#22d3ee", "#c084fc", "#fb7185", "#84cc16",
]


def _color_at(index: int) -> QColor:
    return QColor(CHART_COLORS[index % len(CHART_COLORS)])


class PieChartWidget(QWidget):
    """Donut-style pie chart with animated segments and hover tooltips."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        data: Optional[list[dict]] = None,
        donut: bool = True,
        accent: str = "#FFD700",
    ):
        """
        Args:
            data: List of dicts with 'label', 'value', and optional 'color'.
                  Example: [{'label': 'Used', 'value': 45}, {'label': 'Free', 'value': 55}]
            donut: If True, render as donut chart (hole in center).
            accent: Accent color for center text.
        """
        super().__init__(parent)
        self._data = data or []
        self._donut = donut
        self._accent = accent
        self._hovered_index = -1
        self.setMinimumSize(180, 180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)

    def set_data(self, data: list[dict]):
        self._data = data
        self.update()

    def set_accent(self, color: str):
        self._accent = color
        self.update()

    def paintEvent(self, event):
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        side = min(w, h) - 20
        cx, cy = w / 2, h / 2
        rect = QRectF(cx - side / 2, cy - side / 2, side, side)

        total = sum(d["value"] for d in self._data)
        if total == 0:
            painter.end()
            return

        start_angle = 90 * 16  # Start at top
        for i, item in enumerate(self._data):
            span = int((item["value"] / total) * 360 * 16)
            col_val = item.get("color", CHART_COLORS[i % len(CHART_COLORS)])
            if col_val == "palette_dim":
                # Use a dim color derived from palette
                c = self.palette().text().color()
                c.setAlpha(30)
                color = c
            else:
                color = QColor(col_val)

            if i == self._hovered_index:
                color = color.lighter(130)
                hover_rect = rect.adjusted(-4, -4, 4, 4)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawPie(hover_rect, start_angle, span)
            else:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(color))
                painter.drawPie(rect, start_angle, span)

            start_angle += span

        # Donut hole
        if self._donut:
            hole_size = side * 0.55
            hole_rect = QRectF(cx - hole_size / 2, cy - hole_size / 2, hole_size, hole_size)
            bg = self.palette().window().color()
            painter.setBrush(QBrush(bg))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(hole_rect)

            # Center text
            if self._data:
                font = QFont("Inter", int(side * 0.09), QFont.Weight.Bold)
                painter.setFont(font)
                painter.setPen(QColor(self._accent))
                top_item = max(self._data, key=lambda d: d["value"])
                percent = (top_item["value"] / total) * 100
                painter.drawText(hole_rect, Qt.AlignmentFlag.AlignCenter, f"{percent:.0f}%")

        painter.end()

    def mouseMoveEvent(self, event):
        pos = event.position()
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        dx = pos.x() - cx
        dy = -(pos.y() - cy)
        dist = math.sqrt(dx * dx + dy * dy)
        side = min(w, h) - 20

        if dist > side / 2 or (self._donut and dist < side * 0.275):
            self._hovered_index = -1
            self.update()
            return

        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
        chart_angle = (90 - angle) % 360

        total = sum(d["value"] for d in self._data)
        if total == 0:
            return

        cumulative = 0
        for i, item in enumerate(self._data):
            cumulative += (item["value"] / total) * 360
            if chart_angle <= cumulative:
                if self._hovered_index != i:
                    self._hovered_index = i
                    self.update()
                    label = item.get("label", f"Segment {i}")
                    val = item["value"]
                    pct = (val / total) * 100
                    QToolTip.showText(
                        event.globalPosition().toPoint(),
                        f"{label}: {pct:.1f}%",
                    )
                return
        self._hovered_index = -1
        self.update()

    def leaveEvent(self, event):
        self._hovered_index = -1
        self.update()


class LineGraphWidget(QWidget):
    """Line graph with gradient fill, grid lines, and axis labels."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        data: Optional[list[dict]] = None,
        accent: str = "#FFD700",
        y_label: str = "",
    ):
        """
        Args:
            data: List of dicts with 'label' (x-axis), 'value' (y-axis).
                  Example: [{'label': 'Mon', 'value': 42}, ...]
            accent: Line color.
            y_label: Y-axis label text.
        """
        super().__init__(parent)
        self._data = data or []
        self._accent = accent
        self._y_label = y_label
        self.setMinimumSize(280, 160)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self._hovered_idx = -1

    def set_data(self, data: list[dict]):
        self._data = data
        self.update()

    def set_accent(self, color: str):
        self._accent = color
        self.update()

    def paintEvent(self, event):
        if not self._data or len(self._data) < 2:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Use palette text dim color
            dim_col = self.palette().placeholderText().color()
            if not dim_col.isValid():
                 # Fallback if placeholderText not set (it usually isn't in default palette)
                 # We can use text() with alpha
                 dim_col = self.palette().text().color()
                 dim_col.setAlpha(100)
                 
            painter.setPen(dim_col)
            font = QFont("Inter", 11)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Not enough data")
            painter.end()
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin_l, margin_r, margin_t, margin_b = 55, 20, 20, 35
        plot_w = w - margin_l - margin_r
        plot_h = h - margin_t - margin_b

        values = [d["value"] for d in self._data]
        v_min = min(values) * 0.9
        v_max = max(values) * 1.1
        if v_max == v_min:
            v_max = v_min + 1

        def to_x(i):
            return margin_l + (i / (len(self._data) - 1)) * plot_w

        def to_y(v):
            return margin_t + plot_h - ((v - v_min) / (v_max - v_min)) * plot_h


        # Grid lines - use weak text color
        grid_col = self.palette().text().color()
        grid_col.setAlpha(30)
        grid_pen = QPen(grid_col, 1)
        painter.setPen(grid_pen)
        for i in range(5):
            y = margin_t + (i / 4) * plot_h
            painter.drawLine(QPointF(margin_l, y), QPointF(w - margin_r, y))

        # Y-axis labels
        label_font = QFont("Inter", 9)
        painter.setFont(label_font)
        
        # Use secondary text color
        text_col = self.palette().text().color()
        text_col.setAlpha(150)
        painter.setPen(text_col)
        
        for i in range(5):
            y = margin_t + (i / 4) * plot_h
            val = v_max - (i / 4) * (v_max - v_min)
            if val >= 1_000_000_000:
                text = f"{val / 1_000_000_000:.1f}G"
            elif val >= 1_000_000:
                text = f"{val / 1_000_000:.1f}M"
            elif val >= 1_000:
                text = f"{val / 1_000:.1f}K"
            else:
                text = f"{val:.0f}"
            painter.drawText(QRectF(0, y - 10, margin_l - 8, 20),
                             Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, text)

        # X-axis labels (show a subset)
        max_labels = max(1, plot_w // 60)
        step = max(1, len(self._data) // max_labels)
        for i in range(0, len(self._data), step):
            x = to_x(i)
            label = str(self._data[i].get("label", ""))[:6]
            painter.drawText(QRectF(x - 30, h - margin_b + 5, 60, 25),
                             Qt.AlignmentFlag.AlignCenter, label)

        # Gradient fill
        path = QPainterPath()
        path.moveTo(to_x(0), to_y(values[0]))
        for i in range(1, len(values)):
            path.lineTo(to_x(i), to_y(values[i]))
        path.lineTo(to_x(len(values) - 1), margin_t + plot_h)
        path.lineTo(to_x(0), margin_t + plot_h)
        path.closeSubpath()

        accent_color = QColor(self._accent)
        grad = QLinearGradient(0, margin_t, 0, margin_t + plot_h)
        accent_color.setAlpha(60)
        grad.setColorAt(0, accent_color)
        accent_color.setAlpha(5)
        grad.setColorAt(1, accent_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

        # Line
        line_pen = QPen(QColor(self._accent), 2.5)
        line_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        line_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(line_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for i in range(1, len(values)):
            painter.drawLine(
                QPointF(to_x(i - 1), to_y(values[i - 1])),
                QPointF(to_x(i), to_y(values[i])),
            )

        # Dots
        painter.setPen(Qt.PenStyle.NoPen)
        for i in range(len(values)):
            x, y = to_x(i), to_y(values[i])
            if i == self._hovered_idx:
                painter.setBrush(QBrush(QColor(self._accent)))
                painter.drawEllipse(QPointF(x, y), 5, 5)
            else:
                painter.setBrush(QBrush(QColor(self._accent)))
                painter.drawEllipse(QPointF(x, y), 3, 3)

        painter.end()

    def mouseMoveEvent(self, event):
        pos = event.position()
        w = self.width()
        margin_l, margin_r = 55, 20
        plot_w = w - margin_l - margin_r

        if len(self._data) < 2:
            return

        x = pos.x() - margin_l
        if x < 0 or x > plot_w:
            self._hovered_idx = -1
            self.update()
            return

        idx = round(x / plot_w * (len(self._data) - 1))
        idx = max(0, min(idx, len(self._data) - 1))
        if self._hovered_idx != idx:
            self._hovered_idx = idx
            self.update()
            item = self._data[idx]
            label = item.get("label", "")
            val = item["value"]
            if val >= 1_000_000_000:
                val_str = f"{val / 1_000_000_000:.2f} GB"
            elif val >= 1_000_000:
                val_str = f"{val / 1_000_000:.2f} MB"
            else:
                val_str = f"{val:,.0f}"
            QToolTip.showText(
                event.globalPosition().toPoint(),
                f"{label}: {val_str}",
            )

    def leaveEvent(self, event):
        self._hovered_idx = -1
        self.update()
