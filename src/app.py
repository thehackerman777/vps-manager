"""Main window for the VPS Manager application."""
import logging
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ansi_parser import AnsiConsoleParser
from src.database import DatabaseManager
from src.dialogs import AddServerDialog
from src.ssh_worker import SSHWorker

logger = logging.getLogger(__name__)


class VPSManagerApp(QMainWindow):
    """Main application window with server list, console, and script tabs."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VPS Manager")
        self.setGeometry(100, 100, 1300, 820)

        self.db_manager = DatabaseManager()
        self.ssh_worker: SSHWorker | None = None
        self.current_server_id: int | None = None
        self._ansi_parser: AnsiConsoleParser | None = None

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
        left_layout.setContentsMargins(12, 12, 6, 12)
        left_layout.setSpacing(8)
        left.setLayout(left_layout)

        servers_label = QLabel("Servers")
        left_layout.addWidget(servers_label)

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
        self.server_table.setAlternatingRowColors(True)
        self.server_table.verticalHeader().setVisible(False)
        self.server_table.itemSelectionChanged.connect(self._on_server_selected)
        left_layout.addWidget(self.server_table, stretch=1)

        # Server action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.add_btn = QPushButton("➕  Add")
        self.add_btn.clicked.connect(self.add_server)
        self.edit_btn = QPushButton("✏️  Edit")
        self.edit_btn.clicked.connect(self.edit_server)
        self.edit_btn.setEnabled(False)
        self.delete_btn = QPushButton("🗑️  Delete")
        self.delete_btn.clicked.connect(self.delete_server)
        self.delete_btn.setEnabled(False)
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.delete_btn)
        left_layout.addLayout(btn_row)

        left.setMinimumWidth(340)
        splitter.addWidget(left)

        # ─── Right panel: tabs ────────────────────────────────────
        self.tabs = QTabWidget()

        # ── Console tab ───────────────────────────────────────────
        console_tab = QWidget()
        console_layout = QVBoxLayout()
        console_layout.setContentsMargins(12, 12, 12, 12)
        console_layout.setSpacing(8)
        console_tab.setLayout(console_layout)

        console_label = QLabel("Terminal Output")
        console_layout.addWidget(console_label)

        self.console_output = QTextEdit()
        self.console_output.setObjectName("console_output")
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Cascadia Code", 12))
        self.console_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        # Dark terminal background color
        palette = self.console_output.palette()
        palette.setColor(palette.ColorRole.Base, QColor("#010409"))
        self.console_output.setPalette(palette)
        console_layout.addWidget(self.console_output, stretch=1)

        # Connection bar
        conn_row = QHBoxLayout()
        conn_row.setSpacing(8)
        self.connect_btn = QPushButton("🔌  Connect")
        self.connect_btn.setObjectName("connect_btn")
        self.connect_btn.clicked.connect(self.connect_to_server)
        self.connect_btn.setEnabled(False)
        self.disconnect_btn = QPushButton("⛔  Disconnect")
        self.disconnect_btn.setObjectName("disconnect_btn")
        self.disconnect_btn.clicked.connect(self.disconnect_from_server)
        self.disconnect_btn.setEnabled(False)
        self.clear_btn = QPushButton("🧹  Clear")
        self.clear_btn.clicked.connect(self.console_output.clear)
        conn_row.addWidget(self.connect_btn)
        conn_row.addWidget(self.disconnect_btn)
        conn_row.addWidget(self.clear_btn)
        conn_row.addStretch()
        console_layout.addLayout(conn_row)

        # Command input
        input_row = QHBoxLayout()
        input_row.setSpacing(6)
        self.console_input = QLineEdit()
        self.console_input.setObjectName("console_input")
        self.console_input.setPlaceholderText("Enter command… (press Enter to send)")
        self.console_input.returnPressed.connect(self._send_console_command)
        self.console_input.setEnabled(False)
        self.send_btn = QPushButton("Send ↵")
        self.send_btn.clicked.connect(self._send_console_command)
        self.send_btn.setEnabled(False)
        input_row.addWidget(self.console_input, stretch=1)
        input_row.addWidget(self.send_btn)
        console_layout.addLayout(input_row)

        self.tabs.addTab(console_tab, "  🖥  Console  ")

        # ── Scripts tab ────────────────────────────────────────────
        scripts_tab = QWidget()
        scripts_layout = QVBoxLayout()
        scripts_layout.setContentsMargins(12, 12, 12, 12)
        scripts_layout.setSpacing(8)
        scripts_tab.setLayout(scripts_layout)

        scripts_layout.addWidget(QLabel("Associated Scripts"))
        self.script_list = QTableWidget()
        self.script_list.setColumnCount(2)
        self.script_list.setHorizontalHeaderLabels(["Name", "Description"])
        self.script_list.horizontalHeader().setStretchLastSection(True)
        self.script_list.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.script_list.setAlternatingRowColors(True)
        self.script_list.verticalHeader().setVisible(False)
        self.script_list.itemSelectionChanged.connect(self._on_script_selected)
        scripts_layout.addWidget(self.script_list, stretch=1)

        script_btn_row = QHBoxLayout()
        script_btn_row.setSpacing(6)
        self.add_script_btn = QPushButton("📄  Add Script")
        self.add_script_btn.clicked.connect(self.add_script)
        self.add_script_btn.setEnabled(False)
        self.execute_script_btn = QPushButton("▶  Execute")
        self.execute_script_btn.setObjectName("execute_btn")
        self.execute_script_btn.clicked.connect(self.execute_script)
        self.execute_script_btn.setEnabled(False)
        script_btn_row.addWidget(self.add_script_btn)
        script_btn_row.addWidget(self.execute_script_btn)
        script_btn_row.addStretch()
        scripts_layout.addLayout(script_btn_row)

        # Script editor
        scripts_layout.addWidget(QLabel("Script Editor"))
        self.script_editor = QTextEdit()
        self.script_editor.setFont(QFont("Cascadia Code", 12))
        scripts_layout.addWidget(self.script_editor, stretch=1)

        editor_btn_row = QHBoxLayout()
        editor_btn_row.setSpacing(6)
        self.save_btn = QPushButton("💾  Save")
        self.save_btn.clicked.connect(self.save_script)
        self.load_btn = QPushButton("📂  Load File")
        self.load_btn.clicked.connect(self.load_script_from_file)
        editor_btn_row.addWidget(self.save_btn)
        editor_btn_row.addWidget(self.load_btn)
        editor_btn_row.addStretch()
        scripts_layout.addLayout(editor_btn_row)

        self.tabs.addTab(scripts_tab, "  📜  Scripts  ")

        splitter.addWidget(self.tabs)
        splitter.setSizes([360, 940])

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
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

        self.server_table.resizeColumnsToContents()
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

        self.script_list.resizeColumnsToContents()
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
        """Upload and execute selected script on the remote server via SFTP."""
        row = self.script_list.currentRow()
        if row < 0 or not self.current_server_id:
            return

        data = self.script_list.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        script_id, local_script_path = data

        if not os.path.isfile(local_script_path):
            QMessageBox.warning(
                self, "File Error", f"Script not found:\n{local_script_path}"
            )
            return

        # Read the script with explicit UTF-8 encoding to avoid charmap errors
        try:
            with open(local_script_path, encoding="utf-8") as f:
                script_content = f.read()
        except UnicodeDecodeError:
            # Fallback: try latin-1 (reads any byte sequence)
            try:
                with open(local_script_path, encoding="latin-1") as f:
                    script_content = f.read()
            except Exception as e:
                QMessageBox.warning(self, "Read Error", str(e))
                return
        except Exception as e:
            QMessageBox.warning(self, "Read Error", str(e))
            return

        script_name = os.path.basename(local_script_path)
        remote_path = f"/tmp/vpsm_{script_name}"

        # Ensure we're connected; if not, offer to connect
        if not (self.ssh_worker and self.ssh_worker.is_connected()):
            reply = QMessageBox.question(
                self, "Not Connected",
                "Not connected to server. Connect now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self.connect_to_server()
            # Give worker a moment to connect before queuing the script
            self.msleep_after_connect = True

        if self.ssh_worker and self.ssh_worker.is_connected():
            self.ssh_worker.execute_script(script_content, remote_path)
            self.tabs.setCurrentIndex(0)  # Switch to console tab
            self.statusBar().showMessage(f"Uploading & executing {script_name}…")

    def save_script(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Script", "", "Shell Scripts (*.sh);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
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
                with open(file_path, encoding="utf-8") as f:
                    self.script_editor.setPlainText(f.read())
            except UnicodeDecodeError:
                try:
                    with open(file_path, encoding="latin-1") as f:
                        self.script_editor.setPlainText(f.read())
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))
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

        # Re-initialise the ANSI parser bound to the (cleared) console
        self.console_output.clear()
        self._ansi_parser = AnsiConsoleParser(self.console_output)

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
        """Route raw terminal data through the ANSI parser."""
        if self._ansi_parser:
            self._ansi_parser.feed(text)
        else:
            # Fallback: plain insert (e.g. before first connection)
            cursor = self.console_output.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(text)
            self.console_output.setTextCursor(cursor)
            sb = self.console_output.verticalScrollBar()
            sb.setValue(sb.maximum())
