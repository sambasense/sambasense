"""Unified Storage Dashboard - consolidated view for local shares and remote mounts."""

import time
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout,
)

from sambasense.core.storage import (
    get_all_share_stats, get_all_mount_stats,
    get_usage_history, record_all_shares, record_all_mounts
)
from sambasense.core.utils import format_bytes
from sambasense.gui.widgets.graphs import PieChartWidget, LineGraphWidget, CHART_COLORS
from sambasense.gui.widgets.cards import InfoCard
from sambasense.gui.icons import icon_folder_share, icon_link, icon_chart_pie, icon_refresh


class _DashboardWorker(QThread):
    """Background thread for storage discovery and recording."""
    data_ready = pyqtSignal(list, list)

    def run(self):
        # Data fetching (blocking I/O)
        record_all_shares()
        record_all_mounts()
        local_stats = get_all_share_stats()
        remote_stats = get_all_mount_stats()
        self.data_ready.emit(local_stats, remote_stats)


class DashboardPage(QWidget):
    def __init__(self, accent: str = "#FFD700", is_remote: bool = False, parent=None):
        super().__init__(parent)
        self._accent = accent
        self._is_remote = is_remote
        self._setup_ui()
        
        # Background worker
        self._worker = _DashboardWorker()
        self._worker.data_ready.connect(self._on_data_ready)
        
        # Initial refresh
        self._refresh()

        # Auto-refresh every 30s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(30_000)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_text = "Remote Mounts Dashboard" if self._is_remote else "Local Shares Dashboard"
        title = QLabel(title_text)
        title.setObjectName("heading")
        header_layout.addWidget(title)
        
        self._loading_label = QLabel("  Refreshing...")
        self._loading_label.setObjectName("dimLabel")
        self._loading_label.setStyleSheet("font-style: italic; font-size: 12px;")
        self._loading_label.setVisible(False)
        header_layout.addWidget(self._loading_label)
        
        header_layout.addStretch()

        self._refresh_btn = QPushButton("  Refresh")
        self._refresh_btn.setObjectName("secondaryButton")
        self._refresh_btn.setIcon(icon_refresh(self._accent))
        self._refresh_btn.clicked.connect(self._refresh)
        header_layout.addWidget(self._refresh_btn)
        layout.addLayout(header_layout)

        sub_text = "Consolidated analytics for all remote CIFS mounts" if self._is_remote else "Consolidated analytics for all local Samba shares"
        sub = QLabel(sub_text)
        sub.setObjectName("subheading")
        layout.addWidget(sub)

        # Summary Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        if not self._is_remote:
            self._local_card = InfoCard(
                title="LOCAL SHARES", value="—", subtitle="Loading statistics...",
                icon_fn=icon_folder_share, accent=self._accent,
            )
            cards_layout.addWidget(self._local_card)
        else:
            self._remote_card = InfoCard(
                title="REMOTE MOUNTS", value="—", subtitle="Loading statistics...",
                icon_fn=icon_link, accent=self._accent,
            )
            cards_layout.addWidget(self._remote_card)
        
        layout.addLayout(cards_layout)

        # Scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(8, 10, 8, 16)
        container_layout.setSpacing(24)

        # Main Column
        self._main_col = QVBoxLayout()
        self._main_col.setSpacing(16)
        container_layout.addLayout(self._main_col, 1)

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _refresh(self):
        if self._worker.isRunning():
            return
        self._loading_label.setVisible(True)
        self._refresh_btn.setEnabled(False)
        self._worker.start()

    def _on_data_ready(self, local_stats, remote_stats):
        self._loading_label.setVisible(False)
        self._refresh_btn.setEnabled(True)
        
        # Update Summary Cards
        if not self._is_remote:
            local_used = sum(s["used"] for s in local_stats)
            local_free = sum(s["free"] for s in local_stats)
            self._local_card.set_value(str(len(local_stats)))
            self._local_card.set_subtitle(f"{format_bytes(local_used)} Used / {format_bytes(local_free)} Available")
        else:
            remote_used = sum(s["used"] for s in remote_stats)
            remote_free = sum(s["free"] for s in remote_stats)
            self._remote_card.set_value(str(len(remote_stats)))
            self._remote_card.set_subtitle(f"{format_bytes(remote_used)} Used / {format_bytes(remote_free)} Available")

        # Clear columns
        self._clear_layout(self._main_col)

        # Section Headers
        header_text = "REMOTE MOUNTS" if self._is_remote else "LOCAL SHARES"
        header = QLabel(header_text)
        header.setObjectName("dimLabel")
        header.setStyleSheet("font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        self._main_col.addWidget(header)

        # Items
        stats = remote_stats if self._is_remote else local_stats
        if not stats:
            empty_msg = "No remote mounts active" if self._is_remote else "No local shares configured"
            self._main_col.addWidget(self._create_empty_label(empty_msg))
        else:
            for i, stat in enumerate(stats):
                self._main_col.addWidget(self._create_stat_card(stat, i, is_remote=self._is_remote))

        self._main_col.addStretch()

    def _create_empty_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("dimLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("padding: 40px; font-size: 13px; background: rgba(0,0,0,0.1); border-radius: 8px;")
        return label

    def _create_stat_card(self, stat: dict, index: int, is_remote: bool) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        # Title/Path Row
        header = QHBoxLayout()
        name = stat['name'] if not is_remote else f"{stat['remote']}"
        name_label = QLabel(name)
        name_label.setObjectName("accentLabel")
        name_label.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {self._accent};")
        header.addWidget(name_label)
        header.addStretch()

        sub_info = stat.get('path', '') if not is_remote else f"→ {stat['local']}"
        sub_label = QLabel(sub_info)
        sub_label.setObjectName("dimLabel")
        sub_label.setStyleSheet("font-size: 11px;")
        header.addWidget(sub_label)
        card_layout.addLayout(header)

        # Storage Metrics
        metrics = QLabel(
            f"Used: {format_bytes(stat['used'])} / {format_bytes(stat['free'])} Available  •  {stat['percent']}%"
        )
        metrics.setObjectName("dimLabel")
        metrics.setStyleSheet("font-size: 12px;")
        card_layout.addWidget(metrics)

        # Miniature Charts Row
        charts = QHBoxLayout()
        charts.setSpacing(12)

        pie = PieChartWidget(accent=self._accent)
        pie.setFixedSize(120, 120)
        color = CHART_COLORS[index % len(CHART_COLORS)]
        # Theme-aware "Free" color (dim text/border color)
        # We can't easily get the palette here without passing it or looking up parent.
        # But we can use a safe default or ask the widget to handle "transparent/dim" if we pass None?
        # Better: use a hardcoded safe color that works in both or just use the widget's palette in paintEvent if color is None.
        # Let's use a semi-transparent gray that works on both dark/light
        free_col = "#2a2a30" if "0a0a0b" in self._accent else "#e0e0e4"  # Primitive check, unreliable
        # Actually, let's just pass a specific key that the widget understands, or use a color we know works.
        # In light mode, #2a2a30 is too dark. In dark mode, it's fine.
        # Let's rely on the fact that we can pass a QColor or let the widget handle it?
        # The widget currently expects a hex string or uses a default from CHART_COLORS.
        # Let's change the widget to use a default if we pass "theme_dim".
        
        # Actually, best approach: check self.palette().windowText().color() logic in the widget or just pass a color.
        # Since we are in the page, we can access the theme manager if we really wanted, but we don't have it easily.
        # However, we know if we are in dark mode based on the passed accent? No.
        # But wait, dashboard_page receives accent but not the mode.
        # Let's update `PieChartWidget` to handle a special "dim" color type or just default the 'Free' flavor to a dim color from palette.
        
        pie.set_data([
            {"label": "Used", "value": stat["used"], "color": color},
            {"label": "Free", "value": stat["free"], "color": "palette_dim"},
        ])
        charts.addWidget(pie)

        history_key = stat['path'] if not is_remote else stat['local']
        history = get_usage_history(history_key)
        line = LineGraphWidget(accent=self._accent)
        line.setFixedHeight(120)
        if history:
            line_data = []
            for dp in history:
                ts = dp.get("timestamp", 0)
                t_str = time.strftime("%H:%M", time.localtime(ts)) if ts else ""
                line_data.append({"label": t_str, "value": dp.get("used", 0)})
            line.set_data(line_data)
        charts.addWidget(line, 1)
        
        card_layout.addLayout(charts)
        return card

    def update_accent(self, accent: str):
        self._accent = accent
        if hasattr(self, "_local_card"):
            self._local_card.update_accent(accent)
        if hasattr(self, "_remote_card"):
            self._remote_card.update_accent(accent)
        self._refresh_btn.setIcon(icon_refresh(accent))
        self._refresh()
