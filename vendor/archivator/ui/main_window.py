import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import *

from archivator.core.exceptions import ArchivatorError
from archivator.core.registry import ProjectRegistry
from archivator.core.paths import CONFIG_PATH, PLACEHOLDER_PATH, UI_PATH, ensure_app_dirs

from archivator.services.archive_service import ArchiveService

from archivator.ui.dialogs.add_project_dialog import AddProjectDialog
from archivator.ui.dialogs.project_settings_dialog import ProjectSettingsDialog
from archivator.ui.layouts.flow_layout import FlowLayout
from archivator.ui.widgets.add_project_card import AddProjectCard
from archivator.ui.widgets.project_card import ProjectCard
from archivator.ui.controllers.selection_controller import ProjectSelectionController


class MainWindow:
    """
    Main UI controller.

    Responsibilities:
    - Load the .ui file
    - Bind UI widgets
    - Display project cards
    - Forward user actions to ArchiveService
    """

    def __init__(self) -> None:
        self.ui_path = UI_PATH
        self.config_path = CONFIG_PATH
        self.placeholder_path = PLACEHOLDER_PATH

        ensure_app_dirs()
        self.registry = ProjectRegistry(str(CONFIG_PATH))
        self.registry.load()
        self.service = ArchiveService(self.registry)

        self.window = self.load_ui()

        self.selection = ProjectSelectionController()

        self.bind_widgets()
        self.setup_project_area()
        self.connect_signals()
        self.refresh_projects()

    def load_ui(self):
        """
        Load the main window from the Qt Designer .ui file.
        """
        loader = QUiLoader()
        window = loader.load(str(self.ui_path))

        if window is None:
            raise RuntimeError(f"Could not load UI: {self.ui_path}")

        return window

    def bind_widgets(self) -> None:
        """
        Retrieve important widgets from the loaded UI.
        """
        self.project_container = self.window.findChild(QWidget, "projectContainer")
        self.search_bar = self.window.findChild(QLineEdit, "searchLineEdit")
        self.settings_button = self.window.findChild(QPushButton, "settingsButton")
        self.sort_combo = self.window.findChild(QComboBox, "sortComboBox")
        self.stats_label = self.window.findChild(QLabel, "statsLabel")
        self.project_path_label = self.window.findChild(QLabel, "projectPathLabel")
        self.empty_trash_button = self.window.findChild(QPushButton, "emptyTrashButton")

        if self.project_container is None:
            raise RuntimeError("Missing widget 'projectContainer' in interface.ui")

    def setup_project_area(self) -> None:
        """
        Create the scroll area and flow layout used for project cards.
        """
        old_layout = self.project_container.layout()
        if old_layout is not None:
            QWidget().setLayout(old_layout)

        outer_layout = QVBoxLayout(self.project_container)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.cards_widget = QWidget()
        self.flow_layout = FlowLayout(self.cards_widget, margin=0, hspacing=24, vspacing=24)
        self.cards_widget.setLayout(self.flow_layout)
        self.cards_widget.mousePressEvent = self.on_cards_area_clicked

        self.scroll_area.setWidget(self.cards_widget)
        outer_layout.addWidget(self.scroll_area)

    def connect_signals(self) -> None:
        """
        Connect UI events.
        """
        if self.search_bar is not None:
            self.search_bar.textChanged.connect(self.refresh_projects)

        if self.sort_combo is not None:
            self.sort_combo.currentIndexChanged.connect(self.refresh_projects)

        if self.empty_trash_button is not None:
            self.empty_trash_button.clicked.connect(self.empty_selected_trashes)

    def clear_cards(self) -> None:
        """
        Remove all cards from the project area.
        """
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh_projects(self) -> None:
        """
        Reload and display the visible project cards.
        """
        self.clear_cards()
        self.selection.clear_selection()
        self.refresh_selection_ui()

        projects = self.service.list_projects()
        projects = self.filter_projects(projects)
        projects = self.sort_projects(projects)

        if self.stats_label is not None:
            self.stats_label.setText(f"{len(projects)} projects registered")

        self.flow_layout.addWidget(AddProjectCard(self.add_project))

        project_cards = []

        for project in projects:
            card = ProjectCard(project, self, str(self.placeholder_path))
            project_cards.append(card)
            self.flow_layout.addWidget(card)

        self.selection.set_cards(project_cards)

    def filter_projects(self, projects: list) -> list:
        """
        Filter projects according to the search bar.
        """
        if self.search_bar is None:
            return projects

        search_text = self.search_bar.text().strip().lower()
        if not search_text:
            return projects

        return [
            project for project in projects
            if search_text in project.name.lower()
        ]

    def sort_projects(self, projects: list) -> list:
        """
        Sort projects according to the combo box selection.
        """
        if self.sort_combo is None:
            return projects

        current_text = self.sort_combo.currentText()

        if "Name" in current_text:
            return sorted(projects, key=lambda p: p.name.lower())

        if "Path" in current_text:
            return sorted(projects, key=lambda p: p.root.lower())

        return projects

    def add_project(self) -> None:
        dialog = AddProjectDialog(self.window)

        if dialog.exec() != QDialog.Accepted:
            return

        root_path, trash_dir = dialog.get_values()

        try:
            self.service.add_project(root_path, trash_dir)
            self.refresh_projects()

        except ArchivatorError as exc:
            QMessageBox.warning(self.window, "Archivator Error", str(exc))
        except Exception as exc:
            QMessageBox.critical(self.window, "Unexpected Error", str(exc))

    def open_project(self, project) -> None:
        """
        Ask the service to open the selected project's root folder.
        """
        try:
            self.service.open_project_root(project.id)
        except Exception as exc:
            QMessageBox.critical(self.window, "Error", str(exc))

    def open_project_trash(self, project) -> None:
        """
        Ask the service to open the selected project's trash folder.
        """
        try:
            self.service.open_project_trash(project.id)
        except Exception as exc:
            QMessageBox.critical(self.window, "Error", str(exc))

    def empty_project_trash(self, project) -> None:
        """
        Empty the trash directory for the selected project.
        """
        reply = QMessageBox.question(
            self.window,
            "Confirm",
            f"Empty trash for\n{project.name} ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.service.empty_project_trash(project.id)
        except ArchivatorError as exc:
            QMessageBox.warning(self.window, "Archivator Error", str(exc))
        except Exception as exc:
            QMessageBox.critical(self.window, "Unexpected Error", str(exc))

        self.refresh_projects()

    def open_project_settings(self, project) -> None:
        dialog = ProjectSettingsDialog(
            project=project,
            placeholder_path=str(self.placeholder_path),
            parent=self.window,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        values = dialog.get_values()

        try:
            self.service.update_project(
                project_id=project.id,
                name=values["name"],
                root_path=values["root"],
                trash_dir=values["trash_dir"],
                thumbnail_path=values["thumbnail_path"],
            )
            self.refresh_projects()
        except ArchivatorError as exc:
            QMessageBox.warning(self.window, "Archivator Error", str(exc))
        except Exception as exc:
            QMessageBox.critical(self.window, "Unexpected Error", str(exc))

    def remove_project(self, project) -> None:
        """
        Remove a project from the registry after user confirmation.
        """
        reply = QMessageBox.question(
            self.window,
            "Remove Project",
            f"Remove '{project.name}' from Archivator?\n\n"
            f"This will only unregister the project.\n"
            f"No files or folders will be deleted.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            self.service.remove_project(project.id)
            self.refresh_projects()

        except ArchivatorError as exc:
            QMessageBox.warning(self.window, "Archivator Error", str(exc))
        except Exception as exc:
            QMessageBox.critical(self.window, "Unexpected Error", str(exc))

    def select_project(self, project, card, modifiers=None) -> None:
        self.selection.select_project(project, card, modifiers)
        self.refresh_selection_ui()

    def refresh_selection_ui(self) -> None:
        selected_projects = self.selection.get_selected_projects()
        count = len(selected_projects)

        if count == 0:
            self.project_path_label.setText("")
            self.empty_trash_button.setText("Empty ALL Trash")
            return

        if count == 1:
            self.project_path_label.setText(
                f"Selected Project Path : {selected_projects[0].root}"
            )
        else:
            names = [project.name for project in selected_projects]
            self.project_path_label.setText(", ".join(names))

        self.empty_trash_button.setText(f"Empty {count} Trash")

    def on_cards_area_clicked(self, event) -> None:
        """
        Clear selection when clicking empty space in the project area.
        """
        if event.button() == Qt.LeftButton:
            self.selection.clear_selection()
            self.refresh_selection_ui()

    def empty_selected_trashes(self) -> None:
        """
        Empty trash for selected projects.

        If no project is selected, empty trash for all registered projects.
        """
        selected_projects = self.selection.get_selected_projects()

        if selected_projects:
            projects = selected_projects
            message = f"Empty trash for {len(projects)} selected project(s)?"
        else:
            projects = self.service.list_projects()
            message = "Empty trash for ALL projects?"

        if not projects:
            QMessageBox.information(self.window, "Empty Trash", "No projects available.")
            return

        reply = QMessageBox.question(
            self.window,
            "Confirm Empty Trash",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            for project in projects:
                self.service.empty_project_trash(project.id)

        except ArchivatorError as exc:
            QMessageBox.warning(self.window, "Archivator Error", str(exc))

        except Exception as exc:
            QMessageBox.critical(self.window, "Unexpected Error", str(exc))

        self.refresh_projects()

    def show(self) -> None:
        """
        Show the main window.
        """
        self.window.show()