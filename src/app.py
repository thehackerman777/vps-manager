"""Main window for the VPS Manager application."""
import logging
import os
import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QTextEdit,
    QLineEdit, QLabel, QTabWidget, QMessageBox, QFileDialog,
    QHeaderView, QSplitter, QGroupBox, QStatusBar,
)

from src.database import DatabaseManager
from src.ssh_worker import SSHWorker
from src.dialogs import AddServerDialog

logger = logging.getLogger(__name__)


class VPSManagerApp(QMainWindow):
    """Main application window with server list, console, and script tabs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VPS Manager")
        self.setGeometry(100, 100, 1280, 800)

        self.db_manager = DatabaseManager()
        self.ssh_worker: SSHWorker | None = None
        self.current_server_id: int | None = None

        self._build_ui()
        self.load_servers()

    # ── UI Construction ──────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ─── Left panel: server list ──────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout()
        left.setLayout(left_layout)

        left_layout.addWidget(QLabel("<b>Servers</b>"))

        self.server_table = QTableWidget()
        self.server_table.setColumnCount(5)
        self.server_table.setHorizontalHeaderLabels(
            ["Name", "IP", "Port", "Username", "Description"]
        )
        self.server_table.horizontalHeader().setStretchLastSection(True)
        self.server_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.server_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.server_table.itemSelectionChanged.connect(self._on_server_selected)
        left_layout.addWidget(self.server_table, stretch=1)

        # Server action buttons
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("➕ Add")
        self.add_btn.clicked.connect(self.add_server)
        self.edit_btn = QPushButton("✏️ Edit")
        self.edit_btn.clicked.connect(self.edit_server)
        self.edit_btn.setEnabled(False)
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.clicked.connect(self.delete_server)
        self.delete_btn.setEnabled(False)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.delete_btn)
        left_layout.addLayout(btn_row)

        left.setMinimumWidth(320)
        splitter.addWidget(left)

        # ─── Right panel: tabs ────────────────────────────────────
        self.tabs = QTabWidget()

        # ── Console tab ───────────────────────────────────────────
        console_tab = QWidget()
        console_layout = QVBoxLayout()
        console_tab.setLayout(console_layout)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))
        self.console_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        console_layout.addWidget(QLabel("Console Output:"))
        console_layout.addWidget(self.console_output, stretch=1)

        # Connection bar
        conn_row = QHBoxLayout()
        self.connect_btn = QPushButton("🔌 Connect")
        self.connect_btn.clicked.connect(self.connect_to_server)
        self.connect_btn.setEnabled(False)
        self.disconnect_btn = QPushButton("⛔ Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_from_server)
        self.disconnect_btn.setEnabled(False)
        conn_row.addWidget(self.connect_btn)
        conn_row.addWidget(self.disconnect_btn)
        conn_row.addStretch()
        console_layout.addLayout(conn_row)

        # Command input
        input_row = QHBoxLayout()
        self.console_input = QLineEdit()
        self.console_input.setPlaceholderText("Enter command… (press Enter to send)")
        self.console_input.returnPressed.connect(self._send_console_command)
        self.console_input.setEnabled(False)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._send_console_command)
        self.send_btn.setEnabled(False)
        input_row.addWidget(self.console_input, stretch=1)
        input_row.addWidget(self.send_btn)
        console_layout.addLayout(input_row)

        self.tabs.addTab(console_tab, "Console")

        # ── Scripts tab ────────────────────────────────────────────
        scripts_tab = QWidget()
        scripts_layout = QVBoxLayout()
        scripts_tab.setLayout(scripts_layout)

        scripts_layout.addWidget(QLabel("Associated Scripts:"))
        self.script_list = QTableWidget()
        self.script_list.setColumnCount(2)
        self.script_list.setHorizontalHeaderLabels(["Name", "Description"])
        self.script_list.horizontalHeader().setStretchLastSection(True)
        self.script_list.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.script_list.itemSelectionChanged.connect(self._on_script_selected)
        scripts_layout.addWidget(self.script_list, stretch=1)

        script_btn_row = QHBoxLayout()
        self.add_script_btn = QPushButton("📄 Add Script")
        self.add_script_btn.clicked.connect(self.add_script)
        self.add_script_btn.setEnabled(False)
        self.execute_script_btn = QPushButton("▶️ Execute")
        self.execute_script_btn.clicked.connect(self.execute_script)
        self.execute_script_btn.setEnabled(False)
        script_btn_row.addWidget(self.add_script_btn)
        script_btn_row.addWidget(self.execute_script_btn)
        scripts_layout.addLayout(script_btn_row)

        # Script editor
        scripts_layout.addWidget(QLabel("Script Editor:"))
        self.script_editor = QTextEdit()
        self.script_editor.setFont(QFont("Consolas", 10))
        scripts_layout.addWidget(self.script_editor, stretch=1)

        editor_btn_row = QHBoxLayout()
        self.save_btn = QPushButton("💾 Save")
        self.save_btn.clicked.connect(self.save_script)
        self.load_btn = QPushButton("📂 Load")
        self.load_btn.clicked.connect(self.load_script_from_file)
        editor_btn_row.addWidget(self.save_btn)
        editor_btn_row.addWidget(self.load_btn)
        scripts_layout.addLayout(editor_btn_row)

        self.tabs.addTab(scripts_tab, "Scripts")

        splitter.addWidget(self.tabs)
        splitter.setSizes([350, 930])

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        central.setLayout(main_layout)

        # Status bar
        self.statusBar().showMessage("Ready")

    # ── Server List Operations ────────────────────────────────────

    def load_servers(self):
        servers = self.db_manager.get_servers()
        self.server_table.setRowCount(len(servers))

        for row, srv in enumerate(servers):
            # srv = (id, name, ip, username, pem_path, port, description)
            sid, name, ip, username, pem_path, port, desc = srv

            item_name = QTableWidgetItem(name)
            item_name.setData(Qt.ItemDataRole.UserRole, sid)

            self.server_table.setItem(row, 0, item_name)
            self.server_table.setItem(row, 1, QTableWidgetItem(ip))
            self.server_table.setItem(row, 2, QTableWidgetItem(str(port)))
            self.server_table.setItem(row, 3, QTableWidgetItem(username))
            self.server_table.setItem(row, 4, QTableWidgetItem(desc or ""))

        # Reset selection-dependent buttons
        self._clear_selection_state()

    def _on_server_selected(self):
        row = self.server_table.currentRow()
        if row < 0:
            self._clear_selection_state()
            return

        sid = self.server_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.current_server_id = sid

        self.edit_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.connect_btn.setEnabled(True)
        self.add_script_btn.setEnabled(True)

        self.load_scripts_for_server(sid)

    def _clear_selection_state(self):
        self.current_server_id = None
        self.edit_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.connect_btn.setEnabled(False)
        self.add_script_btn.setEnabled(False)
        self.execute_script_btn.setEnabled(False)
        self.script_list.setRowCount(0)

    def add_server(self):
        dialog = AddServerDialog(self)
        if dialog.exec() == AddServerDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not all([data["name"], data["ip"], data["username"], data["pem_path"]]):
                QMessageBox.warning(
                    self, "Missing fields",
                    "Name, IP, username, and PEM file are required."
                )
                return
            if not os.path.isfile(data["pem_path"]):
                QMessageBox.warning(
                    self, "File not found",
                    f"PEM file does not exist:\n{data['pem_path']}"
                )
                return
            self.db_manager.add_server(**data)
            self.load_servers()
            QMessageBox.information(self, "Success", "Server added.")

    def edit_server(self):
        if not self.current_server_id:
            return
        srv = self.db_manager.get_server(self.current_server_id)
        if not srv:
            return
        # srv = (id, name, ip, username, pem_path, port, description)
        data = {
            "name": srv[1],
            "ip": srv[2],
            "username": srv[3],
            "pem_path": srv[4],
            "port": srv[5],
            "description": srv[6],
        }
        dialog = AddServerDialog(self, edit_data=data)
        if dialog.exec() == AddServerDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            self.db_manager.update_server(self.current_server_id, **new_data)
            self.load_servers()
            QMessageBox.information(self, "Success", "Server updated.")

    def delete_server(self):
        if not self.current_server_id:
            return
        reply = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this server and all its associated scripts?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db_manager.delete_server(self.current_server_id)
            self.current_server_id = None
            self.load_servers()

    # ── Script Operations ─────────────────────────────────────────

    def load_scripts_for_server(self, server_id: int):
        scripts = self.db_manager.get_scripts_for_server(server_id)
        self.script_list.setRowCount(len(scripts))

        for row, scr in enumerate(scripts):
            scr_id, name, script_path, desc = scr
            item = QTableWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, (scr_id, script_path))
            self.script_list.setItem(row, 0, item)
            self.script_list.setItem(row, 1, QTableWidgetItem(desc or ""))

        self.execute_script_btn.setEnabled(False)

    def _on_script_selected(self):
        self.execute_script_btn.setEnabled(
            bool(self.script_list.selectedItems())
        )

    def add_script(self):
        if not self.current_server_id:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Script", "", "Shell Scripts (*.sh);;All Files (*)"
        )
        if file_path:
            name = os.path.basename(file_path)
            self.db_manager.add_script(
                self.current_server_id, name, file_path
            )
            self.load_scripts_for_server(self.current_server_id)
            QMessageBox.information(self, "Success", "Script added.")

    def execute_script(self):
        """Execute selected script on the remote server.
        
        FIX: Uploads the script content via SFTP, then runs it remotely.
        """
        row = self.script_list.currentRow()
        if row < 0 or not self.current_server_id:
            return

        data = self.script_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        script_id, local_script_path = data

        if not os.path.isfile(local_script_path):
            QMessageBox.warning(self, "File Error", f"Script not found:\n{local_script_path}")
            return

        # Read the script content
        try:
            with open(local_script_path) as f:
                script_content = f.read()
        except Exception as e:
            QMessageBox.warning(self, "Read Error", str(e))
            return

        # Build remote path
        script_name = os.path.basename(local_script_path)
        remote_path = f"/tmp/vpsm_{script_name}"

        # Ensure we're connected; if not, connect first
        if not (self.ssh_worker and self.ssh_worker.is_connected()):
            reply = QMessageBox.question(
                self, "Not Connected",
                "Not connected to server. Connect now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self.connect_to_server()

        # Send script via interactive shell
        if self.ssh_worker and self.ssh_worker.is_connected():
            self.ssh_worker.execute_script(script_content, remote_path)
            self.tabs.setCurrentIndex(0)  # Switch to console tab
            self.statusBar().showMessage(f"Executing {script_name} on server…")

    def save_script(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Script", "", "Shell Scripts (*.sh);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(self.script_editor.toPlainText())
                QMessageBox.information(self, "Success", "Script saved.")
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def load_script_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Script", "", "Shell Scripts (*.sh);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path) as f:
                    self.script_editor.setPlainText(f.read())
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ── SSH Connection ────────────────────────────────────────────

    def connect_to_server(self):
        if not self.current_server_id:
            return

        srv = self.db_manager.get_server(self.current_server_id)
        if not srv:
            return

        sid, name, ip, username, pem_path, port, desc = srv

        if not os.path.isfile(pem_path):
            QMessageBox.warning(self, "File Error", f"PEM file not found:\n{pem_path}")
            return

        self.ssh_worker = SSHWorker(ip, port, username, pem_path)
        self.ssh_worker.output_received.connect(self._append_console)
        self.ssh_worker.command_finished.connect(self._on_ssh_finished)
        self.ssh_worker.connection_status.connect(self._on_connection_status)
        self.ssh_worker.error_occurred.connect(self._on_ssh_error)
        self.ssh_worker.start()

        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
        self.console_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.statusBar().showMessage(f"Connecting to {name} ({ip})…")

    def disconnect_from_server(self):
        if self.ssh_worker:
            self.ssh_worker.disconnect()
            if self.ssh_worker.isRunning():
                self.ssh_worker.wait(3000)
            self.ssh_worker = None

        self._reset_connection_ui()

    def _on_connection_status(self, status: str):
        if status == "connected":
            self.statusBar().showMessage("Connected ✅")
        elif status == "disconnected":
            self._reset_connection_ui()
            self.statusBar().showMessage("Disconnected")

    def _on_ssh_finished(self, exit_code: int, output: str):
        self.statusBar().showMessage(f"Command finished (exit: {exit_code})")

    def _on_ssh_error(self, error_msg: str):
        QMessageBox.critical(self, "SSH Error", error_msg)
        self._reset_connection_ui()

    def _reset_connection_ui(self):
        self.connect_btn.setEnabled(bool(self.current_server_id))
        self.disconnect_btn.setEnabled(False)
        self.console_input.setEnabled(False)
        self.send_btn.setEnabled(False)

    # ── Console ──────────────────────────────────────────────────

    def _send_console_command(self):
        """Send the text in the input field to the interactive SSH shell."""
        command = self.console_input.text().strip()
        if not command:
            return
        if not (self.ssh_worker and self.ssh_worker.is_connected()):
            QMessageBox.warning(self, "Not connected", "Connect to a server first.")
            return

        self.ssh_worker.send_command(command)
        self.console_input.clear()

    def _append_console(self, text: str):
        self.console_output.moveCursor(QTextCursor.MoveOperation.End)
        self.console_output.insertPlainText(text)
        # Keep the view scrolled to the bottom
        sb = self.console_output.verticalScrollBar()
        sb.setValue(sb.maximum())

    # ── Convenience ───────────────────────────────────────────────
    # self.tabs is set in _build_ui as the QTabWidget
