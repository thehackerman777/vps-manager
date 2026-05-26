"""Dark-mode Qt stylesheet for VPS Manager.

Provides a modern, premium-looking dark theme for the entire application.
"""


DARK_STYLESHEET = """
/* ── Global ──────────────────────────────────────────────────────────────── */
QWidget {
    background-color: #0d1117;
    color: #e0e0e0;
    font-family: "Segoe UI", "Inter", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #0d1117;
}

/* ── Splitter ─────────────────────────────────────────────────────────────── */
QSplitter::handle {
    background-color: #21262d;
    width: 2px;
    height: 2px;
}

/* ── Labels ───────────────────────────────────────────────────────────────── */
QLabel {
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    padding: 2px 0px;
}

/* ── Buttons ──────────────────────────────────────────────────────────────── */
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #30363d;
    border-color: #58a6ff;
    color: #f0f6fc;
}

QPushButton:pressed {
    background-color: #1f6feb;
    border-color: #1f6feb;
    color: #ffffff;
}

QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}

/* ── Connect/Disconnect special buttons ───────────────────────────────────── */
QPushButton#connect_btn {
    background-color: #1a3a1a;
    border-color: #238636;
    color: #3fb950;
    font-weight: 600;
}

QPushButton#connect_btn:hover {
    background-color: #238636;
    color: #ffffff;
}

QPushButton#disconnect_btn {
    background-color: #3a1a1a;
    border-color: #da3633;
    color: #f85149;
    font-weight: 600;
}

QPushButton#disconnect_btn:hover {
    background-color: #da3633;
    color: #ffffff;
}

QPushButton#execute_btn {
    background-color: #1e2a3a;
    border-color: #1f6feb;
    color: #58a6ff;
    font-weight: 600;
}

QPushButton#execute_btn:hover {
    background-color: #1f6feb;
    color: #ffffff;
}

/* ── Tables ───────────────────────────────────────────────────────────────── */
QTableWidget {
    background-color: #0d1117;
    alternate-background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #21262d;
    border-radius: 6px;
    gridline-color: #21262d;
    selection-background-color: #1f3a5a;
    selection-color: #e0e0e0;
}

QTableWidget::item {
    padding: 6px 10px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #1f3a5a;
    color: #e0e0e0;
}

QTableWidget::item:hover {
    background-color: #161b22;
}

QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 10px;
    border: none;
    border-bottom: 2px solid #21262d;
    border-right: 1px solid #21262d;
    letter-spacing: 0.3px;
}

QHeaderView::section:hover {
    background-color: #21262d;
    color: #c9d1d9;
}

/* ── Tabs ─────────────────────────────────────────────────────────────────── */
QTabWidget::pane {
    background-color: #0d1117;
    border: 1px solid #21262d;
    border-radius: 0px 6px 6px 6px;
}

QTabBar::tab {
    background-color: #161b22;
    color: #8b949e;
    border: 1px solid #21262d;
    border-bottom: none;
    border-radius: 6px 6px 0px 0px;
    padding: 8px 20px;
    font-size: 12px;
    font-weight: 500;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #0d1117;
    color: #58a6ff;
    border-color: #30363d;
    border-bottom: 2px solid #58a6ff;
}

QTabBar::tab:hover:!selected {
    background-color: #21262d;
    color: #c9d1d9;
}

/* ── Console / Text Editors ───────────────────────────────────────────────── */
QTextEdit {
    background-color: #0d1117;
    color: #e0e0e0;
    border: 1px solid #21262d;
    border-radius: 6px;
    selection-background-color: #1f6feb;
    selection-color: #ffffff;
    padding: 4px;
}

QTextEdit#console_output {
    background-color: #010409;
    color: #e0e0e0;
    border: 1px solid #1f6feb;
    border-radius: 6px;
    font-family: "Cascadia Code", "Fira Code", "JetBrains Mono", "Consolas", monospace;
    font-size: 13px;
    line-height: 1.4;
}

/* ── Line Inputs ──────────────────────────────────────────────────────────── */
QLineEdit {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}

QLineEdit:focus {
    border-color: #58a6ff;
    background-color: #0d1117;
    color: #f0f6fc;
}

QLineEdit:disabled {
    background-color: #0d1117;
    color: #484f58;
    border-color: #21262d;
}

QLineEdit#console_input {
    font-family: "Cascadia Code", "Fira Code", "JetBrains Mono", "Consolas", monospace;
    font-size: 13px;
    background-color: #010409;
    border: 1px solid #30363d;
}

QLineEdit#console_input:focus {
    border-color: #58a6ff;
}

/* ── Scrollbars ───────────────────────────────────────────────────────────── */
QScrollBar:vertical {
    background-color: #0d1117;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #30363d;
    min-height: 30px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #484f58;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #0d1117;
    height: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #30363d;
    min-width: 30px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #484f58;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ── Status Bar ───────────────────────────────────────────────────────────── */
QStatusBar {
    background-color: #161b22;
    color: #8b949e;
    border-top: 1px solid #21262d;
    font-size: 11px;
    padding: 2px 8px;
}

/* ── Group Boxes ──────────────────────────────────────────────────────────── */
QGroupBox {
    background-color: #161b22;
    border: 1px solid #21262d;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 600;
    color: #8b949e;
    font-size: 11px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #58a6ff;
}

/* ── Message Boxes & Dialogs ──────────────────────────────────────────────── */
QMessageBox {
    background-color: #161b22;
    color: #c9d1d9;
}

QMessageBox QLabel {
    color: #c9d1d9;
    font-size: 13px;
    text-transform: none;
    font-weight: normal;
    letter-spacing: 0;
}

QDialog {
    background-color: #161b22;
    color: #c9d1d9;
}

/* ── Combo Boxes ──────────────────────────────────────────────────────────── */
QComboBox {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 10px;
}

QComboBox:hover {
    border-color: #58a6ff;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #21262d;
    color: #c9d1d9;
    selection-background-color: #1f3a5a;
    border: 1px solid #30363d;
}

/* ── Spin Boxes ───────────────────────────────────────────────────────────── */
QSpinBox {
    background-color: #161b22;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 5px 8px;
}

QSpinBox:focus {
    border-color: #58a6ff;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #21262d;
    border: none;
    border-radius: 3px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #30363d;
}
"""
