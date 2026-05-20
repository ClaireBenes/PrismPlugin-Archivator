import sys

from PySide6.QtWidgets import QApplication
from archivator.ui.main_window import MainWindow


def main() -> None:
    """
    Application entry point.
    """
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()