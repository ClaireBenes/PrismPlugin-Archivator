import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from archivator.ui.utils.image_helper import build_preview_pixmap
from archivator.ui.utils.folder_size_helper import get_dir_size


class ProjectSettingsDialog(QDialog):
    """
    Dialog used to edit an existing project.

    Responsibilities:
    - Edit project name
    - Edit project root path
    - Edit trash path
    - Preview thumbnail
    - Select or clear thumbnail
    - Validate fields live
    - Disable Save while invalid
    """

    PREVIEW_WIDTH = 300
    PREVIEW_HEIGHT = 170
    PREVIEW_RADIUS = 10

    FIELD_ERROR_STYLE = """
    QLineEdit {
        border: 1px solid #d96c6c;
    }
    """

    def __init__(self, project, placeholder_path: str | None = None, parent=None) -> None:
        super().__init__(parent)

        self.project = project
        self.placeholder_path = placeholder_path
        self.selected_thumbnail_path = getattr(project, "thumbnail_path", None)

        self.setWindowTitle(f"Project Settings - {project.name}")
        self.setMinimumWidth(760)

        self.name_edit = QLineEdit(project.name)
        self.root_edit = QLineEdit(project.root)
        self.trash_edit = QLineEdit(project.trash_dir)

        self.root_browse_button = QPushButton("Browse")
        self.trash_browse_button = QPushButton("Browse")
        self.thumb_browse_button = QPushButton("Set Thumbnail")
        self.thumb_clear_button = QPushButton("Clear")

        self.root_browse_button.setFixedWidth(90)
        self.trash_browse_button.setFixedWidth(90)
        self.thumb_clear_button.setFixedWidth(80)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.save_button = self.buttons.button(QDialogButtonBox.Save)

        self.root_browse_button.clicked.connect(self.browse_root)
        self.trash_browse_button.clicked.connect(self.browse_trash)
        self.thumb_browse_button.clicked.connect(self.browse_thumbnail)
        self.thumb_clear_button.clicked.connect(self.clear_thumbnail)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        self.name_edit.textChanged.connect(self.validate)
        self.root_edit.textChanged.connect(self.validate)
        self.trash_edit.textChanged.connect(self.validate)

        form_layout = QGridLayout()
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(14)

        form_layout.addWidget(QLabel("Project Name"), 0, 0)
        form_layout.addWidget(self.name_edit, 0, 1)

        root_row = QHBoxLayout()
        root_row.setSpacing(8)
        root_row.addWidget(self.root_edit)
        root_row.addWidget(self.root_browse_button)

        form_layout.addWidget(QLabel("Project Root"), 1, 0)
        form_layout.addLayout(root_row, 1, 1)

        trash_row = QHBoxLayout()
        trash_row.setSpacing(8)
        trash_row.addWidget(self.trash_edit)
        trash_row.addWidget(self.trash_browse_button)

        form_layout.addWidget(QLabel("Trash Folder"), 2, 0)
        form_layout.addLayout(trash_row, 2, 1)

        left_panel = QVBoxLayout()
        left_panel.setSpacing(0)
        left_panel.addLayout(form_layout)
        left_panel.addStretch()

        form_layout.addWidget(QLabel(f"Project Size "), 4, 0)
        project_size = QLabel(f"{get_dir_size(project.root)}")
        project_size.setStyleSheet("font-size: 15px;")
        form_layout.addWidget(project_size, 4, 1)

        form_layout.addWidget(QLabel(f"Trash Size "), 5, 0)
        trash_size = QLabel(f"{get_dir_size(project.trash_dir)}")
        trash_size.setStyleSheet("font-size: 15px;")
        form_layout.addWidget(trash_size, 5, 1)

        thumb_buttons_row = QHBoxLayout()
        thumb_buttons_row.setSpacing(8)
        thumb_buttons_row.addWidget(self.thumb_browse_button)
        thumb_buttons_row.addWidget(self.thumb_clear_button)
        thumb_buttons_row.addStretch()

        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        right_panel.addWidget(QLabel("Thumbnail Preview"))
        right_panel.addWidget(self.preview_label)
        right_panel.addLayout(thumb_buttons_row)
        right_panel.addStretch()

        content_row = QHBoxLayout()
        content_row.setSpacing(24)
        content_row.addLayout(left_panel, 3)
        content_row.addLayout(right_panel, 2)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)
        main_layout.addLayout(content_row)
        main_layout.addWidget(self.buttons)

        self.update_preview()
        self.validate()

    def browse_root(self) -> None:
        """
        Let the user choose a new project root folder.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Project Root")
        if folder:
            self.root_edit.setText(folder.replace("\\", "/"))

    def browse_trash(self) -> None:
        """
        Let the user choose a new trash folder.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Trash Folder")
        if folder:
            self.trash_edit.setText(folder.replace("\\", "/"))

    def browse_thumbnail(self) -> None:
        """
        Let the user choose a thumbnail image.
        """
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Thumbnail",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)"
        )
        if filepath:
            self.selected_thumbnail_path = filepath.replace("\\", "/")
            self.update_preview()

    def clear_thumbnail(self) -> None:
        """
        Remove the custom thumbnail and fall back to the placeholder.
        """
        self.selected_thumbnail_path = None
        self.update_preview()

    def clear_validation_styles(self) -> None:
        """
        Remove validation styles from all editable fields.
        """
        self.name_edit.setStyleSheet("")
        self.root_edit.setStyleSheet("")
        self.trash_edit.setStyleSheet("")

    def set_field_error(self, field: QLineEdit) -> None:
        """
        Highlight one invalid field.
        """
        self.clear_validation_styles()
        field.setStyleSheet(self.FIELD_ERROR_STYLE)

    def validate(self) -> None:
        """
        Live validation of all editable fields.

        The dialog shows no text error message.
        It only highlights the invalid field and disables Save.
        """
        name = self.name_edit.text().strip()
        root = self.root_edit.text().strip().replace("\\", "/")
        trash = self.trash_edit.text().strip().replace("\\", "/")

        self.clear_validation_styles()

        if not name:
            self.set_field_error(self.name_edit)
            self.save_button.setEnabled(False)
            return

        if not root:
            self.set_field_error(self.root_edit)
            self.save_button.setEnabled(False)
            return

        if not os.path.exists(root):
            self.set_field_error(self.root_edit)
            self.save_button.setEnabled(False)
            return

        if not trash:
            self.set_field_error(self.trash_edit)
            self.save_button.setEnabled(False)
            return

        if not os.path.exists(trash):
            self.set_field_error(self.trash_edit)
            self.save_button.setEnabled(False)
            return

        self.save_button.setEnabled(True)

    def update_preview(self) -> None:
        """
        Update the thumbnail preview using the shared UI helper.
        """
        pixmap = build_preview_pixmap(
            image_path=self.selected_thumbnail_path,
            placeholder_path=self.placeholder_path,
            width=self.PREVIEW_WIDTH,
            height=self.PREVIEW_HEIGHT,
            radius=self.PREVIEW_RADIUS,
            corners="all",
        )

        if pixmap is None:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("No Preview")
            return

        self.preview_label.setText("")
        self.preview_label.setPixmap(pixmap)

    def accept(self) -> None:
        """
        Only close if the form is currently valid.
        """
        self.validate()

        if not self.save_button.isEnabled():
            return

        super().accept()

    def get_values(self) -> dict:
        """
        Return current dialog values.
        """
        return {
            "name": self.name_edit.text().strip(),
            "root": self.root_edit.text().strip().replace("\\", "/"),
            "trash_dir": self.trash_edit.text().strip().replace("\\", "/"),
            "thumbnail_path": self.selected_thumbnail_path,
        }