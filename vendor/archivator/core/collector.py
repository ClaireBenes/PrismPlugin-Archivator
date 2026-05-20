from archivator.core.project import Project

class Collector:
    """
    Automated cleanup logic.

    Responsibilities:
    - Scan project directories
    - Apply rules (age, size, etc.)
    - Move eligible files to trash
    """

    def run(self, project: Project):
        pass

    def should_collect(self, filepath: str, project: Project) -> bool:
        pass