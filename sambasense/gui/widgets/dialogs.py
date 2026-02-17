"""Dialog windows for adding/editing shares and mounting remote shares."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QCheckBox, QPushButton, QFileDialog,
    QComboBox, QDialogButtonBox,
)


class AddShareDialog(QDialog):
    """Dialog for adding or editing a Samba share."""

    def __init__(self, parent=None, edit_data: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Share" if edit_data else "Add Share")
        self.setMinimumWidth(450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Edit Share" if edit_data else "Add New Share")
        title.setObjectName("heading")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)

        # Form
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., documents")
        form.addRow("Share Name:", self.name_input)

        # Path with browse button
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("/srv/samba/share")
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_path)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_btn)
        form.addRow("Path:", path_layout)

        self.comment_input = QLineEdit()
        self.comment_input.setPlaceholderText("Optional description")
        form.addRow("Comment:", self.comment_input)

        self.writable_check = QCheckBox("Allow writing")
        self.writable_check.setChecked(True)
        form.addRow("Writable:", self.writable_check)

        self.guest_check = QCheckBox("Allow guest access")
        form.addRow("Guest OK:", self.guest_check)

        self.browseable_check = QCheckBox("Show in network browser")
        self.browseable_check.setChecked(True)
        form.addRow("Browseable:", self.browseable_check)

        self.users_input = QLineEdit()
        self.users_input.setPlaceholderText("user1, user2 (leave empty for all)")
        form.addRow("Valid Users:", self.users_input)

        self.create_mask = QLineEdit("0664")
        form.addRow("Create Mask:", self.create_mask)

        self.dir_mask = QLineEdit("0775")
        form.addRow("Dir Mask:", self.dir_mask)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save Share")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        # Pre-fill if editing
        if edit_data:
            self.name_input.setText(edit_data.get("name", ""))
            self.name_input.setReadOnly(True)
            self.path_input.setText(edit_data.get("path", ""))
            self.comment_input.setText(edit_data.get("comment", ""))
            self.writable_check.setChecked(edit_data.get("writable", "yes").lower() == "yes")
            self.guest_check.setChecked(edit_data.get("guest ok", "no").lower() == "yes")
            self.browseable_check.setChecked(edit_data.get("browseable", "yes").lower() == "yes")
            self.users_input.setText(edit_data.get("valid users", ""))
            self.create_mask.setText(edit_data.get("create mask", "0664"))
            self.dir_mask.setText(edit_data.get("directory mask", "0775"))

    def _browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Share Directory")
        if path:
            self.path_input.setText(path)

    def get_data(self) -> dict:
        return {
            "name": self.name_input.text().strip(),
            "path": self.path_input.text().strip(),
            "comment": self.comment_input.text().strip(),
            "writable": self.writable_check.isChecked(),
            "guest_ok": self.guest_check.isChecked(),
            "browseable": self.browseable_check.isChecked(),
            "valid_users": self.users_input.text().strip(),
            "create_mask": self.create_mask.text().strip(),
            "directory_mask": self.dir_mask.text().strip(),
        }


class MapShareDialog(QDialog):
    """Dialog for mounting a remote CIFS/SMB share."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Map Network Share")
        self.setMinimumWidth(450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Map Network Share")
        title.setObjectName("heading")
        title.setStyleSheet("font-size: 18px;")
        layout.addWidget(title)

        subtitle = QLabel("Mount a remote SMB/CIFS share to your filesystem")
        subtitle.setObjectName("dimLabel")
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.remote_input = QLineEdit()
        self.remote_input.setPlaceholderText("//server/share")
        form.addRow("Remote Path:", self.remote_input)

        # Local mount point with browse
        local_layout = QHBoxLayout()
        self.local_input = QLineEdit()
        self.local_input.setPlaceholderText("/mnt/network/share")
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondaryButton")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_local)
        local_layout.addWidget(self.local_input)
        local_layout.addWidget(browse_btn)
        form.addRow("Mount Point:", local_layout)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username (leave empty for guest)")
        form.addRow("Username:", self.user_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Password:", self.password_input)

        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("WORKGROUP")
        form.addRow("Domain:", self.domain_input)

        self.persistent_check = QCheckBox("Add to /etc/fstab for persistent mount")
        form.addRow("Persistent:", self.persistent_check)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)

        mount_btn = QPushButton("Mount Share")
        mount_btn.setObjectName("primaryButton")
        mount_btn.clicked.connect(self.accept)

        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(mount_btn)
        layout.addLayout(btn_layout)

    def _browse_local(self):
        path = QFileDialog.getExistingDirectory(self, "Select Mount Point")
        if path:
            self.local_input.setText(path)

    def get_data(self) -> dict:
        return {
            "remote": self.remote_input.text().strip(),
            "local": self.local_input.text().strip(),
            "username": self.user_input.text().strip() or None,
            "password": self.password_input.text() or None,
            "domain": self.domain_input.text().strip() or None,
            "persistent": self.persistent_check.isChecked(),
        }
