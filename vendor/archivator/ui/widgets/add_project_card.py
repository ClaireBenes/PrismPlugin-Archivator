from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


CARD_WIDTH = 260
CARD_HEIGHT = 180
PREVIEW_HEIGHT = 120


class AddProjectCard(QFrame):
    """
    Card shown as the first item in the project grid.

    Responsibilities:
    - Display a clear 'Add Project' entry point
    - Trigger the provided callback when clicked
    """

    def __init__(self, on_click, parent=None) -> None:
        super().__init__(parent)

        self._on_click = on_click

        self.setObjectName("addProjectCard")
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
        QFrame#addProjectCard {
            border: 1px solid #555;
            border-radius: 10px;
            background-color: #2b2b2b;
        }
        QFrame#addProjectCard:hover {
            border: 1px solid #c38b59;
            background-color: #333333;
        }
        QLabel {
            color: white;
            background: transparent;
        }
        """)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        preview = QFrame()
        preview.setFixedHeight(PREVIEW_HEIGHT)
        preview.setStyleSheet("""
        background-color: #3a3a3a;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        """)

        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setAlignment(Qt.AlignCenter)

        plus_label = QLabel("+")
        plus_label.setAlignment(Qt.AlignCenter)
        plus_label.setStyleSheet("font-size: 30px; font-weight: bold;")
        preview_layout.addWidget(plus_label)

        info = QFrame()
        info.setStyleSheet("""
        background-color: #2b2b2b;
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
        """)

        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(10, 8, 10, 8)

        title = QLabel("Add Project")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(title)

        root_layout.addWidget(preview)
        root_layout.addWidget(info)

    def mousePressEvent(self, event) -> None:
        """
        Trigger the callback when the card is clicked.
        """
        if callable(self._on_click):
            self._on_click()
        super().mousePressEvent(event)