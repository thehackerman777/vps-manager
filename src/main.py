"""Entry point for VPS Manager application."""
import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.app import VPSManagerApp


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
    window = VPSManagerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
