import os

from PySide6.QtWidgets import *


class AddProjectDialog(QDialog):
    """
    Dialog used to register a new project.

    Responsibilities:
    - Ask for a project root path
    - Ask for a trash directory
    - Validate paths
    - Ask to create trash folder if missing
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Add Project")
        self.setMinimumWidth(550)

        self.root_edit = QLineEdit()
        self.root_edit.setPlaceholderText("Project root path")

        self.trash_edit = QLineEdit()
        self.trash_edit.setPlaceholderText("Trash path")

        self.root_button = QPushButton("Browse")
        self.trash_button = QPushButton("Browse")

        self.root_button.setFixedWidth(90)
        self.trash_button.setFixedWidth(90)

        self.root_button.clicked.connect(self.browse_root)
        self.trash_button.clicked.connect(self.browse_trash)

        # Layout
        layout = QVBoxLayout(self)

        # Root row
        layout.addWidget(QLabel("Project Root"))
        root_row = QHBoxLayout()
        root_row.addWidget(self.root_edit)
        root_row.addWidget(self.root_button)
        layout.addLayout(root_row)

        layout.addSpacing(10)

        # Trash row
        layout.addWidget(QLabel("Trash Folder"))
        trash_row = QHBoxLayout()
        trash_row.addWidget(self.trash_edit)
        trash_row.addWidget(self.trash_button)
        layout.addLayout(trash_row)

        layout.addSpacing(12)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def browse_root(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Project Root")
        if not folder:
            return

        folder = folder.replace("\\", "/")
        self.root_edit.setText(folder)

        if not self.trash_edit.text().strip():
            trash = os.path.join(folder, "01_Trash").replace("\\", "/")
            self.trash_edit.setText(trash)

    def browse_trash(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Trash Folder")
        if folder:
            folder = folder.replace("\\", "/")
            self.trash_edit.setText(folder)

    def accept(self) -> None:
        """
        Validate inputs before closing dialog.
        """
        root = self.root_edit.text().strip()
        trash = self.trash_edit.text().strip()

        if not root:
            QMessageBox.warning(self, "Missing Data", "Project root is required.")
            return

        if not os.path.exists(root):
            QMessageBox.warning(self, "Invalid Root", "Project root does not exist.")
            return

        if not trash:
            QMessageBox.warning(self, "Missing Trash", "Trash directory is required.")
            return

        if not os.path.exists(trash):
            reply = QMessageBox.question(
                self,
                "Create Trash Folder",
                f"The trash folder does not exist:\n\n{trash}\n\nCreate it?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )

            if reply != QMessageBox.Yes:
                return

            try:
                os.makedirs(trash, exist_ok=True)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create trash folder:\n{e}")
                return

        super().accept()

    def get_values(self) -> tuple[str, str]:
        root = self.root_edit.text().strip().replace("\\", "/")
        trash = self.trash_edit.text().strip().replace("\\", "/")
        return root, trash