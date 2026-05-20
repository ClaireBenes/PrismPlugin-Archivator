import os
import uuid
from typing import List

from archivator.core.project import Project
from archivator.core.registry import ProjectRegistry
from archivator.core.resolver import ProjectResolver
from archivator.core.trash.trash_manager import TrashManager
from archivator.core.exceptions import InvalidProjectError

from archivator.services.desktop_service import DesktopService
from archivator.services.path_validator import validate_project_paths, normalize_path


class ArchiveService:
    """
    High-level API used by:
    - CLI
    - UI
    - External tools (Prism plugin)

    This is the main application entry point.
    """

    def __init__(self, registry: ProjectRegistry):
        """
        Initialize the archive service.

        Args:
            registry (ProjectRegistry): Project registry instance.
        """
        self.registry = registry
        self.resolver = ProjectResolver(registry)
        self.trash_manager = TrashManager(self.resolver)
        self.desktop_service = DesktopService()

    def move_to_trash(self, filepath: str) -> str:
        """
        Move a file to its project's trash.

        Args:
            filepath (str): Path to the file.

        Returns:
            str: Destination path in trash.
        """
        return self.trash_manager.move_to_trash(filepath)

    def restore(self, filepath: str) -> str:
        """
        Restore a file from trash.

        Args:
            filepath (str): Path to the file in trash.

        Returns:
            str: Restored file path.
        """
        return self.trash_manager.restore(filepath)

    def empty_project_trash(self, project_id: str) -> None:
        """
        Empty the trash for a given project.

        Args:
            project_id (str): ID of the project.
        """
        self.trash_manager.empty_trash(project_id)

    def add_project(self, root_path: str, trash_dir: str) -> Project:
        """
        Create and register a new project.
        """

        root_path = normalize_path(root_path)
        trash_dir = normalize_path(trash_dir)

        validate_project_paths(root_path, trash_dir, self.registry.get_all())

        if not os.path.exists(trash_dir):
            os.makedirs(trash_dir, exist_ok=True)

        project = Project(
            id=str(uuid.uuid4()),
            name = os.path.basename(os.path.normpath(root_path)),
            root=root_path,
            trash_dir=trash_dir,
            collect_config={},
            paths=[],
        )

        self.registry.add_project(project)
        return project

    def update_project(self, project_id: str, name: str, root_path: str, trash_dir: str, thumbnail_path: str | None = None) -> None:
        """
        Update an existing project.

        Args:
            project_id (str): Project ID.
            name (str): New display name.
            root_path (str): New project root path.
            trash_dir (str): New trash directory.
            thumbnail_path (str | None): Optional thumbnail path.

        Raises:
            InvalidProjectError: If input data is invalid or conflicts with another project.
        """
        name = name.strip()
        root_path = normalize_path(root_path)
        trash_dir = normalize_path(trash_dir)
        thumbnail_path = normalize_path(thumbnail_path) if thumbnail_path else None

        if not name:
            raise InvalidProjectError("Project name cannot be empty.")

        if not os.path.exists(root_path):
            raise InvalidProjectError(f"Project root does not exist: {root_path}")

        if not os.path.exists(trash_dir):
            raise InvalidProjectError(f"Trash directory does not exist: {trash_dir}")

        validate_project_paths(
            root_path=root_path,
            trash_dir=trash_dir,
            existing_projects=[
                project for project in self.registry.get_all()
                if project.id != project_id
            ],
        )

        self.registry.update_project(
            project_id=project_id,
            name=name,
            root=root_path,
            trash_dir=trash_dir,
            thumbnail_path=thumbnail_path,
        )

    def remove_project(self, project_id: str) -> None:
        """
        Remove a registered project.

        Args:
            project_id (str): ID of the project to remove.
        """
        self.registry.remove_project(project_id)

    def list_projects(self) -> List[Project]:
        """
        Get all registered projects.

        Returns:
            List[Project]: List of registered projects.
        """
        return self.registry.get_all()

    def get_project(self, project_id: str) -> Project:
        """
        Get a project by its ID.

        Args:
            project_id (str): Project ID.

        Returns:
            Project: Matching project.
        """
        return self.registry.find_by_id(project_id)

    def get_project_from_path(self, filepath: str) -> Project:
        """
        Resolve and return the project owning a given path.

        Args:
            filepath (str): A path inside the project.

        Returns:
            Project: Matching project.
        """
        return self.resolver.resolve(filepath)

    def open_project_root(self, project_id: str) -> None:
        """
        Open a project's root folder in the system file browser.

        Args:
            project_id (str): Project ID.
        """
        project = self.registry.find_by_id(project_id)
        self.desktop_service.open_folder(project.root)

    def open_project_root_from_path(self, filepath: str) -> None:
        """
        Resolve the project from a path and open its root folder.

        Args:
            filepath (str): A path inside the project.
        """
        project = self.resolver.resolve(filepath)
        self.desktop_service.open_folder(project.root)

    def open_project_trash(self, project_id: str) -> None:
        """
        Open the trash folder for a registered project.

        Args:
            project_id (str): Project ID.

        Raises:
            InvalidProjectError: If the trash folder does not exist.
        """
        project = self.registry.find_by_id(project_id)

        if not os.path.exists(project.trash_dir):
            raise InvalidProjectError(
                f"Trash directory does not exist for project '{project.name}': {project.trash_dir}"
            )

        self.desktop_service.open_folder(project.trash_dir)

    def open_trash_from_path(self, filepath: str) -> None:
        """
        Resolve a project from a path and open its trash folder.

        Args:
            filepath (str): Path inside the project.

        Raises:
            InvalidProjectError: If the trash folder does not exist.
        """
        project = self.resolver.resolve(filepath)

        if not os.path.exists(project.trash_dir):
            raise InvalidProjectError(
                f"Trash directory does not exist for project '{project.name}': {project.trash_dir}"
            )

        self.desktop_service.open_folder(project.trash_dir)