from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QMenu, QVBoxLayout

from archivator.ui.utils.image_helper import build_preview_pixmap
from archivator.ui.utils.folder_size_helper import get_dir_size
from archivator.ui.widgets.add_project_card import CARD_WIDTH, CARD_HEIGHT, PREVIEW_HEIGHT


class ProjectCard(QFrame):
    """
    Visual representation of a project.

    Responsibilities:
    - Display project thumbnail area and name
    - Open project on left click
    - Show a context menu on right click
    - Keep visual feedback for hover / active menu state
    - Delegate actions back to the main window
    """

    def __init__(self, project, controller, placeholder_path: str | None = None, parent=None) -> None:
        super().__init__(parent)

        self.project = project
        self.controller = controller
        self.placeholder_path = placeholder_path

        self.is_hovered = False
        self.is_selected = False
        self.menu_open = False

        self.setObjectName("projectCard")
        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)

        project_size = get_dir_size(self.project.root)
        trash_size = get_dir_size(self.project.trash_dir)
        self.setToolTip(f"Project Size : {project_size}\nTrash Size : {trash_size}\nProject Path : {project.root}\nTrash Path : {project.trash_dir}")

        self.normal_style = """
        QFrame#projectCard {
            border: 1px solid #555;
            border-radius: 10px;
            background-color: #313131;
        }
        QLabel {
            color: white;
            background: transparent;
        }
        """

        self.hover_style = """
        QFrame#projectCard {
            border: 1px solid #c38b59;
            border-radius: 10px;
            background-color: #353535;
        }
        QLabel {
            color: white;
            background: transparent;
        }
        """

        self.active_style = """
        QFrame#projectCard {
            border: 1px solid #c38b59;
            border-radius: 10px;
            background-color: #3a342d;
        }
        QLabel {
            color: white;
            background: transparent;
        }
        """

        self.apply_current_style()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.preview = QLabel("")
        self.preview.setFixedHeight(PREVIEW_HEIGHT)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("""
        background-color: #3a3a3a;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        """)

        self.set_preview_image()

        info = QFrame()
        info.setStyleSheet("""
        background-color: #2b2b2b;
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
        """)

        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(10, 8, 10, 8)

        self.name_label = QLabel(project.name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(self.name_label)

        root_layout.addWidget(self.preview)
        root_layout.addWidget(info)

    def set_preview_image(self) -> None:
        """
        Load the project thumbnail if available, otherwise use the placeholder image.
        """
        image_path = getattr(self.project, "thumbnail_path", None)

        pixmap = build_preview_pixmap(
            image_path=image_path,
            placeholder_path=self.placeholder_path,
            width=CARD_WIDTH,
            height=PREVIEW_HEIGHT,
            radius=10,
            corners="top",
        )

        if pixmap is None:
            self.preview.setText("No Preview")
            return

        self.preview.setText("")
        self.preview.setPixmap(pixmap)
        self.preview.setFixedSize(CARD_WIDTH, PREVIEW_HEIGHT)

    def set_selected(self, selected: bool) -> None:
        self.is_selected = selected
        self.apply_current_style()

    def apply_current_style(self) -> None:
        """
        Apply the correct visual state for the card.
        """
        if self.menu_open or self.is_selected:
            self.setStyleSheet(self.active_style)
        elif self.is_hovered:
            self.setStyleSheet(self.hover_style)
        else:
            self.setStyleSheet(self.normal_style)

    def enterEvent(self, event) -> None:
        self.is_hovered = True
        self.apply_current_style()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.is_hovered = False
        self.apply_current_style()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:
        """
        Select project on single click.
        """
        if event.button() == Qt.LeftButton:
            self.controller.select_project(
                project=self.project,
                card=self,
                modifiers=event.modifiers(),
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        """
        Open project on double click.
        """
        if event.button() == Qt.LeftButton:
            self.controller.open_project(self.project)

        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event) -> None:
        """
        Show the project context menu on right click.
        """
        self.menu_open = True
        self.apply_current_style()

        menu = QMenu(self)

        trash_menu = menu.addMenu("Trash")
        open_trash_action = trash_menu.addAction("Open Trash Folder")
        trash_menu.addSeparator()
        empty_action = trash_menu.addAction("Empty Trash")

        settings_action = menu.addAction("Project Settings")
        menu.addSeparator()
        remove_action = menu.addAction("Remove Project")

        action = menu.exec(event.globalPos())

        self.menu_open = False
        self.apply_current_style()

        if action == open_trash_action:
            self.controller.open_project_trash(self.project)
        elif action == empty_action:
            self.controller.empty_project_trash(self.project)
        elif action == settings_action:
            self.controller.open_project_settings(self.project)
        elif action == remove_action:
            self.controller.remove_project(self.project)