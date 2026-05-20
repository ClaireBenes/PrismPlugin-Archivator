from archivator.core.project import Project
from archivator.core.registry import ProjectRegistry
from archivator.core.exceptions import ProjectNotFoundError

class ProjectResolver:
    """
    Resolves which project a file belongs to.

    Core idea:
    - Input: file path
    - Output: Project
    """

    def __init__(self, registry: ProjectRegistry):
        """
        Initialize the resolver.

        Args:
            registry (ProjectRegistry): Registry containing all projects.
        """
        self.registry = registry

    def resolve(self, filepath: str) -> Project:
        """
        Find the project that owns the given file path.

        The method checks each registered project and determines
        if the file path is inside the project's root directory.

        Args:
            filepath (str): Path to the file.

        Returns:
            Project: The project that contains the file.

        Raises:
            ProjectNotFoundError: If no project matches the given path.
        """

        # Loop through all registered projects
        for project in self.registry.get_all():

            # Use project's helper method to check ownership
            if project.is_path_inside(filepath):
                return project

        # If no project matches, raise an error
        raise ProjectNotFoundError(filepath)