class ArchivatorError(Exception):
    """
    Base exception for all Archivator errors.

    All custom exceptions should inherit from this class.
    This allows catching all Archivator-related errors in one place.
    """
    pass


class ProjectNotFoundError(ArchivatorError):
    """
    Raised when no project matches a given file path.
    """

    def __init__(self, filepath: str):
        """
        Initialize the exception.

        Args:
            filepath (str): Path that could not be resolved to a project.
        """
        message = f"No project found for path: {filepath}"
        super().__init__(message)
        self.filepath = filepath


class InvalidProjectError(ArchivatorError):
    """
    Raised when a project configuration is invalid.
    """

    def __init__(self, message: str):
        """
        Initialize the exception.

        Args:
            message (str): Description of the validation error.
        """
        super().__init__(message)