"""Map shares page — mount/unmount remote CIFS shares."""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView,
)

from sambasense.core.mapper import mount_share, unmount_share, list_mounted_shares, add_fstab_entry
from sambasense.core.storage import get_disk_usage
from sambasense.core.utils import format_bytes
from sambasense.gui.widgets.dialogs import MapShareDialog
from sambasense.gui.icons import icon_plus, icon_refresh, icon_link


class _RefreshWorker(QThread):
    """Background thread for listing mounts and fetching usage stats."""
    data_ready = pyqtSignal(list)

    def run(self):
        mounts = list_mounted_shares()
        data = []
        for m in mounts:
            # this can block if the mount is stale
            try:
                usage = get_disk_usage(m["local"])
            except Exception:
                usage = {"total": 0, "used": 0, "free": 0, "percent": 0}
            
            data.append({
                "remote": m["remote"],
                "local": m["local"],
                "type": m["type"],
                "usage": usage
            })
        self.data_ready.emit(data)


class _MountWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs

    def run(self):
        success, msg = self._func(*self._args, **self._kwargs)
        self.finished.emit(success, msg)


class MapPage(QWidget):
    def __init__(self, accent: str = "#FFD700", parent=None):
        super().__init__(parent)
        self._accent = accent
        self._setup_ui()
        
        # Workers
        self._refresh_worker = _RefreshWorker()
        self._refresh_worker.data_ready.connect(self._on_data_ready)
        
        # Initial refresh
        self._refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Map Network Shares")
        title.setObjectName("heading")
        header_layout.addWidget(title)
        
        self._loading_label = QLabel("  Refreshing...")
        self._loading_label.setObjectName("dimLabel")
        self._loading_label.setStyleSheet("font-style: italic; font-size: 12px;")
        self._loading_label.setVisible(False)
        header_layout.addWidget(self._loading_label)
        
        header_layout.addStretch()

        self._map_btn = QPushButton("  Map Share")
        self._map_btn.setObjectName("primaryButton")
        self._map_btn.setIcon(icon_plus(self._accent))
        self._map_btn.clicked.connect(self._map_share)
        header_layout.addWidget(self._map_btn)

        self._refresh_btn = QPushButton("  Refresh")
        self._refresh_btn.setObjectName("secondaryButton")
        self._refresh_btn.setIcon(icon_refresh(self._accent))
        self._refresh_btn.clicked.connect(self._refresh)
        header_layout.addWidget(self._refresh_btn)

        layout.addLayout(header_layout)

        sub = QLabel("Mount and manage remote SMB/CIFS network shares")
        sub.setObjectName("subheading")
        layout.addWidget(sub)

        # Mounts table
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "Remote Path", "Local Mount", "Type", "Storage", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(4, 100)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        # Empty state
        self._empty_label = QLabel(
            "No CIFS/SMB shares currently mounted.\n\n"
            "Click 'Map Share' to mount a remote network share."
        )
        self._empty_label.setObjectName("dimLabel")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet("font-size: 14px; padding: 40px;")
        layout.addWidget(self._empty_label)

    def _refresh(self):
        if self._refresh_worker.isRunning():
            return
        self._loading_label.setVisible(True)
        self._refresh_btn.setEnabled(False)
        self._refresh_worker.start()

    def _on_data_ready(self, mounts_data):
        self._loading_label.setVisible(False)
        self._refresh_btn.setEnabled(True)
        
        self._table.setRowCount(len(mounts_data))
        self._table.setVisible(len(mounts_data) > 0)
        self._empty_label.setVisible(len(mounts_data) == 0)

        for row, m in enumerate(mounts_data):
            self._table.setItem(row, 0, QTableWidgetItem(m["remote"]))
            self._table.setItem(row, 1, QTableWidgetItem(m["local"]))
            self._table.setItem(row, 2, QTableWidgetItem(m["type"]))

            usage = m["usage"]
            total = usage["total"]
            pct = (usage["used"] / total * 100) if total > 0 else 0
            storage_text = f"{format_bytes(usage['used'])} / {format_bytes(total)} ({pct:.0f}%)"
            self._table.setItem(row, 3, QTableWidgetItem(storage_text))

            unmount_btn = QPushButton("Unmount")
            unmount_btn.setObjectName("dangerButton")
            unmount_btn.setFixedWidth(90)
            unmount_btn.clicked.connect(lambda _, loc=m["local"]: self._unmount(loc))
            action_w = QWidget()
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(4, 4, 4, 4)
            action_l.addWidget(unmount_btn)
            self._table.setCellWidget(row, 4, action_w)

    def _map_share(self):
        dialog = MapShareDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data["remote"] or not data["local"]:
                QMessageBox.warning(self, "Validation", "Remote path and mount point are required.")
                return
            
            # Use the existing MountWorker for the operation
            self._worker = _MountWorker(
                mount_share,
                remote=data["remote"],
                local=data["local"],
                username=data["username"],
                password=data["password"],
                domain=data["domain"],
            )
            
            # Closure to handle persistent mount after success
            def on_mount_finished(success, msg):
                if success and data.get("persistent"):
                    add_fstab_entry(data["remote"], data["local"])
                QMessageBox.information(self, "Mount Result", msg)
                self._refresh()

            self._worker.finished.connect(on_mount_finished)
            self._worker.start()

    def _unmount(self, local: str):
        reply = QMessageBox.question(
            self, "Confirm Unmount",
            f"Unmount '{local}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._worker = _MountWorker(unmount_share, local)
            self._worker.finished.connect(lambda s, m: (
                QMessageBox.information(self, "Unmount Result", m),
                self._refresh()
            ))
            self._worker.start()

    def update_accent(self, accent: str):
        self._accent = accent
        self._map_btn.setIcon(icon_plus(accent))
        self._refresh_btn.setIcon(icon_refresh(accent))
        self._refresh()
