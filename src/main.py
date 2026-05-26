"""Entry point for VPS Manager application."""
import logging
import sys

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from src.app import VPSManagerApp
from src.styles import DARK_STYLESHEET


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName("VPS Manager")
    app.setOrganizationName("OpenClaw")

    # Apply the dark theme globally
    app.setStyleSheet(DARK_STYLESHEET)

    # Use a clean system font for UI elements (monospace fonts handled per-widget)
    ui_font = QFont("Segoe UI", 10)
    app.setFont(ui_font)

    window = VPSManagerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
