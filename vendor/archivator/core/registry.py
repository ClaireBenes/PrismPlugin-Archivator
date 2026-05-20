import json
import os
from typing import List

from archivator.core.project import Project
from archivator.core.exceptions import InvalidProjectError

class ProjectRegistry:
    """
    Single source of truth for all projects.

    Responsibilities:
    - Load/save JSON config
    - Add/remove/update projects
    - Ensure no duplicate roots or trash dirs
    """

    def __init__(self, config_path: str):
        """
        Initialize the registry.

        Args:
            config_path (str): Path to the projects.json file.
        """
        self.config_path = config_path
        self.projects: List[Project] = []

    def load(self) -> None:
        """
        Load projects from the JSON configuration file.

        If the file does not exist, initializes an empty project list.
        """

        if not os.path.exists(self.config_path):
            self.projects = []
            return

        with open(self.config_path, "r") as f:
            data = json.load(f)

        self.projects = []

        for proj_data in data.get("projects", []):
            project = Project(
                id=proj_data["id"],
                name=proj_data["name"],
                root=proj_data["root"],
                trash_dir=proj_data["trash_dir"],
                collect_config=proj_data.get("collect", {}),
                paths=proj_data.get("paths", []),
                thumbnail_path=proj_data.get("thumbnail_path"),
            )
            self.projects.append(project)

    def save(self) -> None:
        """
        Save all projects to the JSON configuration file.
        """

        data = {"projects": []}

        for project in self.projects:
            data["projects"].append({
                "id": project.id,
                "name": project.name,
                "root": project.root,
                "trash_dir": project.trash_dir,
                "collect": project.collect_config,
                "paths": project.paths,
                "thumbnail_path": project.thumbnail_path,
            })

        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=4)

    def add_project(self, project: Project) -> None:
        """
        Add a new project to the registry.

        Args:
            project (Project): Project instance to add.

        Raises:
            InvalidProjectError: If a project with the same root or trash_dir already exists.
        """

        for existing in self.projects:
            if existing.root == project.root:
                raise InvalidProjectError(
                    f"Project with root '{project.root}' already exists."
                )

            if existing.trash_dir == project.trash_dir:
                raise InvalidProjectError(
                    f"Trash directory '{project.trash_dir}' is already used."
                )

        self.projects.append(project)
        self.save()

    def remove_project(self, project_id: str) -> None:
        """
        Remove a project from the registry by its ID.

        Args:
            project_id (str): ID of the project to remove.

        Raises:
            InvalidProjectError: If no project with the given ID exists.
        """
        project = self.find_by_id(project_id)
        self.projects.remove(project)
        self.save()

    def update_project(self, project_id: str, name: str, root: str, trash_dir: str, thumbnail_path=None) -> None:
        """
        Update an existing project and save the registry.

        Args:
            project_id (str): Project ID.
            name (str): New display name.
            root (str): New project root path.
            trash_dir (str): New trash directory.
            thumbnail_path (str | None): Optional thumbnail path.
        """
        project = self.find_by_id(project_id)
        project.name = name
        project.root = root
        project.trash_dir = trash_dir
        project.thumbnail_path = thumbnail_path
        self.save()

    def get_all(self) -> List[Project]:
        """
        Get all registered projects.

        Returns:
            List[Project]: List of all projects.
        """
        return self.projects


    def find_by_id(self, project_id: str) -> Project:
        """
        Find a project by its ID.

        Args:
            project_id (str): ID of the project to find.

        Returns:
            Project: Matching project instance.

        Raises:
            InvalidProjectError: If no project with the given ID exists.
        """

        for project in self.projects:
            if project.id == project_id:
                return project

        raise InvalidProjectError(f"Project with id '{project_id}' not found.")