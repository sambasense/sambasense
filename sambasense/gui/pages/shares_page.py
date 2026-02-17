"""Shares configuration page — add, edit, remove Samba shares."""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView,
)

from sambasense.core.config import list_shares, add_share, remove_share, edit_share, restart_samba
from sambasense.core.storage import get_disk_usage
from sambasense.core.utils import format_bytes
from sambasense.gui.widgets.dialogs import AddShareDialog
from sambasense.gui.widgets.graphs import PieChartWidget
from sambasense.gui.icons import icon_plus, icon_trash, icon_refresh


class _SharesWorker(QThread):
    """Background thread for fetching shares and their storage usage."""
    data_ready = pyqtSignal(list)

    def run(self):
        shares = list_shares()
        data = []
        for name, conf in shares.items():
            path = conf.get("path", "")
            usage = get_disk_usage(path)
            data.append({
                "name": name,
                "conf": conf,
                "usage": usage
            })
        self.data_ready.emit(data)


class SharesPage(QWidget):
    def __init__(self, accent: str = "#FFD700", parent=None):
        super().__init__(parent)
        self._accent = accent
        self._setup_ui()
        
        # Background worker
        self._worker = _SharesWorker()
        self._worker.data_ready.connect(self._on_data_ready)
        
        # Initial refresh
        self._refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Configure Shares")
        title.setObjectName("heading")
        header_layout.addWidget(title)
        
        self._loading_label = QLabel("  Refreshing...")
        self._loading_label.setObjectName("dimLabel")
        self._loading_label.setStyleSheet("font-style: italic; font-size: 12px;")
        self._loading_label.setVisible(False)
        header_layout.addWidget(self._loading_label)
        
        header_layout.addStretch()

        self._add_btn = QPushButton("  Add Share")
        self._add_btn.setObjectName("primaryButton")
        self._add_btn.setIcon(icon_plus(self._accent))
        self._add_btn.clicked.connect(self._add_share)
        header_layout.addWidget(self._add_btn)

        self._refresh_btn = QPushButton("  Refresh")
        self._refresh_btn.setObjectName("secondaryButton")
        self._refresh_btn.setIcon(icon_refresh(self._accent))
        self._refresh_btn.clicked.connect(self._refresh)
        header_layout.addWidget(self._refresh_btn)

        layout.addLayout(header_layout)

        sub = QLabel("Manage shared folders in your Samba configuration")
        sub.setObjectName("subheading")
        layout.addWidget(sub)

        # Content: table + pie chart
        content = QHBoxLayout()
        content.setSpacing(20)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Name", "Path", "Writable", "Guest OK", "Storage", "Actions"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(5, 120)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(False)
        content.addWidget(self._table, 3)

        # Pie chart panel
        chart_panel = QVBoxLayout()
        chart_label = QLabel("Storage Overview")
        chart_label.setObjectName("subheading")
        chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_panel.addWidget(chart_label)

        self._pie = PieChartWidget(accent=self._accent)
        self._pie.setFixedSize(220, 220)
        chart_panel.addWidget(self._pie, alignment=Qt.AlignmentFlag.AlignCenter)

        self._pie_legend = QLabel("")
        self._pie_legend.setObjectName("dimLabel")
        self._pie_legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pie_legend.setWordWrap(True)
        chart_panel.addWidget(self._pie_legend)
        chart_panel.addStretch()

        content.addLayout(chart_panel, 1)
        layout.addLayout(content)

    def _refresh(self):
        if self._worker.isRunning():
            return
        self._loading_label.setVisible(True)
        self._refresh_btn.setEnabled(False)
        self._worker.start()

    def _on_data_ready(self, shares_data):
        self._loading_label.setVisible(False)
        self._refresh_btn.setEnabled(True)
        
        self._table.setRowCount(len(shares_data))

        pie_data = []
        legend_lines = []

        for row, item in enumerate(shares_data):
            name = item["name"]
            conf = item["conf"]
            usage = item["usage"]
            
            path = conf.get("path", "")
            writable = conf.get("writable", "no")
            guest = conf.get("guest ok", "no")

            self._table.setItem(row, 0, QTableWidgetItem(name))
            self._table.setItem(row, 1, QTableWidgetItem(path))
            self._table.setItem(row, 2, QTableWidgetItem(writable))
            self._table.setItem(row, 3, QTableWidgetItem(guest))

            total = usage["total"]
            used_pct = (usage["used"] / total * 100) if total > 0 else 0
            storage_text = f"{format_bytes(usage['used'])} / {format_bytes(total)} ({used_pct:.0f}%)"
            self._table.setItem(row, 4, QTableWidgetItem(storage_text))

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 4, 4, 4)
            action_layout.setSpacing(4)

            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("secondaryButton")
            edit_btn.setFixedWidth(50)
            edit_btn.clicked.connect(lambda _, n=name, c=conf: self._edit_share(n, c))

            del_btn = QPushButton("Del")
            del_btn.setObjectName("dangerButton")
            del_btn.setFixedWidth(50)
            del_btn.clicked.connect(lambda _, n=name: self._remove_share(n))

            action_layout.addWidget(edit_btn)
            action_layout.addWidget(del_btn)
            self._table.setCellWidget(row, 5, action_widget)

            if total > 0:
                pie_data.append({"label": name, "value": usage["used"]})
                legend_lines.append(f"● {name}: {format_bytes(usage['used'])}")

        self._pie.set_data(pie_data)
        self._pie_legend.setText("\n".join(legend_lines) if legend_lines else "No shares")

    def _add_share(self):
        dialog = AddShareDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data["name"] or not data["path"]:
                QMessageBox.warning(self, "Validation", "Name and path are required.")
                return
            success, msg = add_share(
                name=data["name"],
                path=data["path"],
                comment=data["comment"],
                writable=data["writable"],
                guest_ok=data["guest_ok"],
                browseable=data["browseable"],
                valid_users=data["valid_users"],
                create_mask=data["create_mask"],
                directory_mask=data["directory_mask"],
            )
            if success:
                restart_samba()
            QMessageBox.information(self, "Result", msg)
            self._refresh()

    def _edit_share(self, name: str, conf: dict):
        edit_data = {"name": name, **conf}
        dialog = AddShareDialog(self, edit_data=edit_data)
        if dialog.exec():
            data = dialog.get_data()
            options = {}
            if data["path"]:
                options["path"] = data["path"]
            if data["comment"]:
                options["comment"] = data["comment"]
            options["writable"] = "yes" if data["writable"] else "no"
            options["guest ok"] = "yes" if data["guest_ok"] else "no"
            options["browseable"] = "yes" if data["browseable"] else "no"
            if data["valid_users"]:
                options["valid users"] = data["valid_users"]
            options["create mask"] = data["create_mask"]
            options["directory mask"] = data["directory_mask"]

            success, msg = edit_share(name, options)
            if success:
                restart_samba()
            QMessageBox.information(self, "Result", msg)
            self._refresh()

    def _remove_share(self, name: str):
        reply = QMessageBox.question(
            self, "Confirm Remove",
            f"Remove share '{name}' from configuration?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = remove_share(name)
            if success:
                restart_samba()
            QMessageBox.information(self, "Result", msg)
            self._refresh()

    def update_accent(self, accent: str):
        self._accent = accent
        self._pie.set_accent(accent)
        self._add_btn.setIcon(icon_plus(accent))
        self._refresh_btn.setIcon(icon_refresh(accent))
        self._refresh()
