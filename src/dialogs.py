"""Dialog for adding/editing VPS server configurations."""
import os
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QVBoxLayout,
    QLineEdit, QPushButton, QSpinBox, QDialogButtonBox,
    QFileDialog,
)


class AddServerDialog(QDialog):
    """Modal dialog for entering server connection details."""

    def __init__(self, parent=None, edit_data: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Add New Server" if not edit_data else "Edit Server")
        self.setModal(True)
        self.resize(450, 280)
        self.edit_data = edit_data
        self.init_ui()
        if edit_data:
            self._populate(edit_data)

    def init_ui(self):
        layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Production, Dev-VPS")
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("e.g. 18.213.174.229")
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("e.g. ubuntu, root")
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(22)

        self.pem_path_edit = QLineEdit()
        pem_button = QPushButton("Browse...")
        pem_button.clicked.connect(self.browse_pem)

        pem_layout = QHBoxLayout()
        pem_layout.addWidget(self.pem_path_edit)
        pem_layout.addWidget(pem_button)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Optional description")

        layout.addRow("Server Name:", self.name_edit)
        layout.addRow("IP Address:", self.ip_edit)
        layout.addRow("Port:", self.port_spin)
        layout.addRow("Username:", self.username_edit)
        layout.addRow("PEM File:", pem_layout)
        layout.addRow("Description:", self.description_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def browse_pem(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select PEM File", "",
            "PEM Files (*.pem);;All Files (*)"
        )
        if file_path:
            self.pem_path_edit.setText(file_path)

    def _populate(self, data: dict):
        self.name_edit.setText(data.get("name", ""))
        self.ip_edit.setText(data.get("ip", ""))
        self.username_edit.setText(data.get("username", ""))
        self.port_spin.setValue(data.get("port", 22))
        self.pem_path_edit.setText(data.get("pem_path", ""))
        self.description_edit.setText(data.get("description", ""))

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "ip": self.ip_edit.text().strip(),
            "username": self.username_edit.text().strip(),
            "port": self.port_spin.value(),
            "pem_path": self.pem_path_edit.text().strip(),
            "description": self.description_edit.text().strip(),
        }
