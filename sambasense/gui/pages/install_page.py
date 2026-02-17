"""Install / Uninstall page — manage samba packages and service."""

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QMessageBox, QGroupBox, QGridLayout, QScrollArea, QFrame,
)

from sambasense.core.installer import (
    is_samba_installed, is_smbclient_installed, is_cifs_installed,
    get_service_status, install_samba, uninstall_samba,
    enable_service, disable_service, start_service, stop_service,
)
from sambasense.core.utils import detect_distro, get_package_manager
from sambasense.gui.widgets.cards import InfoCard, StatusBadge
from sambasense.gui.icons import icon_server, icon_download, icon_refresh, icon_trash


class _StatusWorker(QThread):
    """Background thread for status checks."""
    data_ready = pyqtSignal(bool, bool, bool, str)

    def run(self):
        samba = is_samba_installed()
        smbclient = is_smbclient_installed()
        cifs = is_cifs_installed()
        svc = get_service_status()
        self.data_ready.emit(samba, smbclient, cifs, svc)


class _WorkerThread(QThread):
    """Background thread for install/uninstall operations."""
    finished = pyqtSignal(bool, str)

    def __init__(self, func):
        super().__init__()
        self._func = func

    def run(self):
        success, msg = self._func()
        self.finished.emit(success, msg)


class InstallPage(QWidget):
    def __init__(self, accent: str = "#FFD700", parent=None):
        super().__init__(parent)
        self._accent = accent
        self._setup_ui()
        
        # Status worker
        self._status_worker = _StatusWorker()
        self._status_worker.data_ready.connect(self._on_status_ready)
        
        # Initial refresh
        self._refresh_status()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        # Header
        header_row = QHBoxLayout()
        header = QLabel("Install && Manage")
        header.setObjectName("heading")
        header_row.addWidget(header)
        
        self._loading_label = QLabel("  Refreshing...")
        self._loading_label.setObjectName("dimLabel")
        self._loading_label.setStyleSheet("font-style: italic; font-size: 12px;")
        self._loading_label.setVisible(False)
        header_row.addWidget(self._loading_label)
        header_row.addStretch()
        
        self._refresh_btn = QPushButton()
        self._refresh_btn.setObjectName("secondaryButton")
        self._refresh_btn.setIcon(icon_refresh(self._accent))
        self._refresh_btn.setFixedSize(36, 36)
        self._refresh_btn.setToolTip("Refresh status")
        self._refresh_btn.clicked.connect(self._refresh_status)
        header_row.addWidget(self._refresh_btn)
        
        layout.addLayout(header_row)

        sub = QLabel("Manage Samba packages and service on your system")
        sub.setObjectName("subheading")
        layout.addWidget(sub)

        # Content scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 10, 0, 20)
        container_layout.setSpacing(24)

        # System info cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        self._distro_card = InfoCard(
            title="DISTRIBUTION",
            value=detect_distro().title(),
            subtitle=f"Package manager: {get_package_manager()}",
            icon_fn=icon_server,
            accent=self._accent,
        )
        cards_layout.addWidget(self._distro_card)

        self._service_card = InfoCard(
            title="SERVICE STATUS",
            value="—",
            subtitle="smbd / smb service",
            icon_fn=icon_download,
            accent=self._accent,
        )
        cards_layout.addWidget(self._service_card)
        container_layout.addLayout(cards_layout)

        # Package status group
        pkg_group = QGroupBox("Core Packages")
        pkg_layout = QHBoxLayout(pkg_group)
        pkg_layout.setContentsMargins(20, 24, 20, 20)
        pkg_layout.setSpacing(40)
        pkg_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._samba_badge = StatusBadge("Samba Server")
        self._smbclient_badge = StatusBadge("SMB Client")
        self._cifs_badge = StatusBadge("CIFS Utils")
        
        pkg_layout.addWidget(self._samba_badge)
        pkg_layout.addWidget(self._smbclient_badge)
        pkg_layout.addWidget(self._cifs_badge)
        container_layout.addWidget(pkg_group)

        # Service management
        service_group = QGroupBox("Service Control")
        service_layout = QVBoxLayout(service_group)
        service_layout.setSpacing(16)

        # Actions row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        
        self._start_btn = QPushButton("Start")
        self._stop_btn = QPushButton("Stop")
        self._enable_btn = QPushButton("Enable")
        self._disable_btn = QPushButton("Disable")
        
        for btn in [self._start_btn, self._stop_btn, self._enable_btn, self._disable_btn]:
            btn.setObjectName("secondaryButton")
            btn_row.addWidget(btn)
            
        self._start_btn.clicked.connect(self._do_start)
        self._stop_btn.clicked.connect(self._do_stop)
        self._enable_btn.clicked.connect(self._do_enable)
        self._disable_btn.clicked.connect(self._do_disable)
        
        service_layout.addLayout(btn_row)
        container_layout.addWidget(service_group)

        # Installation actions
        install_group = QGroupBox("Installation Tasks")
        install_layout = QHBoxLayout(install_group)
        install_layout.setSpacing(12)
        
        self._install_btn = QPushButton(" Install Samba")
        self._install_btn.setObjectName("primaryButton")
        self._install_btn.setIcon(icon_download(self._accent))
        self._install_btn.clicked.connect(self._do_install)
        
        self._uninstall_btn = QPushButton(" Uninstall Samba")
        self._uninstall_btn.setObjectName("dangerButton")
        self._uninstall_btn.setIcon(icon_trash(self._accent))
        self._uninstall_btn.clicked.connect(self._do_uninstall)
        
        install_layout.addWidget(self._install_btn)
        install_layout.addWidget(self._uninstall_btn)
        container_layout.addWidget(install_group)

        # Progress & Status message
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        self._progress.setFixedHeight(6)
        container_layout.addWidget(self._progress)

        self._status_label = QLabel("")
        self._status_label.setObjectName("dimLabel")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self._status_label)
        
        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _refresh_status(self):
        if self._status_worker.isRunning():
            return
        self._loading_label.setVisible(True)
        self._refresh_btn.setEnabled(False)
        self._status_worker.start()

    def _on_status_ready(self, samba, smbclient, cifs, svc):
        self._loading_label.setVisible(False)
        self._refresh_btn.setEnabled(True)
        
        self._samba_badge.set_status("installed" if samba else "not-installed")
        self._smbclient_badge.set_status("installed" if smbclient else "not-installed")
        self._cifs_badge.set_status("installed" if cifs else "not-installed")
        self._service_card.set_value(svc.replace("-", " ").title())

        self._install_btn.setEnabled(not samba)
        self._uninstall_btn.setEnabled(samba)
        self._start_btn.setEnabled(samba and svc != "running")
        self._stop_btn.setEnabled(samba and svc == "running")
        self._enable_btn.setEnabled(samba)
        self._disable_btn.setEnabled(samba)

    def _set_busy(self, busy: bool, msg: str = ""):
        self._progress.setVisible(busy)
        self._progress.setRange(0, 0 if busy else 100)
        self._status_label.setText(msg)
        self._install_btn.setEnabled(not busy)
        self._uninstall_btn.setEnabled(not busy)
        self._start_btn.setEnabled(not busy)
        self._stop_btn.setEnabled(not busy)
        self._enable_btn.setEnabled(not busy)
        self._disable_btn.setEnabled(not busy)

    def _do_install(self):
        self._set_busy(True, "Installing Samba packages...")
        self._worker = _WorkerThread(install_samba)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _do_uninstall(self):
        reply = QMessageBox.question(
            self, "Confirm Uninstall",
            "Are you sure you want to uninstall Samba?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._set_busy(True, "Uninstalling Samba...")
        self._worker = _WorkerThread(uninstall_samba)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _do_enable(self):
        self._set_busy(True, "Enabling service...")
        self._worker = _WorkerThread(enable_service)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _do_disable(self):
        self._set_busy(True, "Disabling service...")
        self._worker = _WorkerThread(disable_service)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _do_start(self):
        self._set_busy(True, "Starting service...")
        self._worker = _WorkerThread(start_service)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _do_stop(self):
        self._set_busy(True, "Stopping service...")
        self._worker = _WorkerThread(stop_service)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, success: bool, msg: str):
        self._set_busy(False, msg)
        self._refresh_status()
        if not success:
            QMessageBox.warning(self, "Error", msg)

    def update_accent(self, accent: str):
        self._accent = accent
        self._distro_card.update_accent(accent)
        self._service_card.update_accent(accent)
        self._refresh_btn.setIcon(icon_refresh(accent))
        self._refresh_status()
