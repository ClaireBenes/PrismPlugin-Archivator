import os
from archivator.core.exceptions import InvalidProjectError


def normalize_path(path: str) -> str:
    """
    Normalize a filesystem path for safe comparisons.
    Does NOT change case for display purposes.
    """
    return os.path.normpath(os.path.abspath(path))

def normalize_path_for_compare(path: str) -> str:
    """
    Normalize a path for comparisons (case-insensitive on Windows).
    """
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))

def is_same_or_subpath(child: str, parent: str) -> bool:
    """
    Return True if 'child' is the same path as 'parent'
    or located inside it.
    """
    child = normalize_path_for_compare(child)
    parent = normalize_path_for_compare(parent)

    try:
        common = os.path.commonpath([child, parent])
    except ValueError:
        return False

    return common == parent


def validate_project_paths(root_path: str, trash_dir: str, existing_projects: list) -> None:
    """
    Validate project root and trash directory against application rules.
    """

    root_path = normalize_path(root_path)
    trash_dir = normalize_path(trash_dir)

    if not os.path.exists(root_path):
        raise InvalidProjectError(f"Root path does not exist: {root_path}")

    if not trash_dir:
        raise InvalidProjectError("Trash directory must be specified.")

    if root_path == trash_dir:
        raise InvalidProjectError("Project root and trash directory cannot be the same.")

    # Root cannot be inside its own trash
    if is_same_or_subpath(root_path, trash_dir):
        raise InvalidProjectError("Project root cannot be inside the trash directory.")

    for project in existing_projects:
        existing_root = normalize_path(project.root)
        existing_trash = normalize_path(project.trash_dir)

        if root_path == existing_root:
            raise InvalidProjectError(
                f"Project with root '{root_path}' already exists."
            )

        if trash_dir == existing_trash:
            raise InvalidProjectError(
                f"Trash directory '{trash_dir}' is already used."
            )

        if is_same_or_subpath(root_path, existing_trash):
            raise InvalidProjectError(
                f"Project root cannot be inside another project's trash:\n{existing_trash}"
            )

        if is_same_or_subpath(trash_dir, existing_trash):
            raise InvalidProjectError(
                f"Trash directory cannot be inside another project's trash:\n{existing_trash}"
            )

        if is_same_or_subpath(root_path, existing_root):
            raise InvalidProjectError(
                f"Project root cannot be inside another project's root:\n{existing_root}"
            )

        if is_same_or_subpath(existing_root, root_path):
            raise InvalidProjectError(
                f"Another project root already exists inside this root:\n{existing_root}"
            )