import os

def clean_path(path: str) -> str:
    """
    Normalize a path for stable storage.
    """
    return os.path.abspath(path).replace("\\", "/")


def compute_trash_path(project, filepath: str) -> str:
    """
    Compute the mirrored destination path inside the project trash.
    """
    relative_path = os.path.relpath(filepath, project.root)
    return os.path.join(project.trash_dir, relative_path)


def make_unique_path(path: str) -> str:
    """
    Return a unique file path by appending _1, _2, etc. if needed.
    """
    if not os.path.exists(path):
        return path

    counter = 1
    original_path = path

    while os.path.exists(path):
        name, ext = os.path.splitext(os.path.basename(original_path))
        parent = os.path.dirname(original_path)
        path = os.path.join(parent, f"{name}_{counter}{ext}")
        counter += 1

    return path


def cleanup_empty_dirs(root_dir: str) -> None:
    """
    Remove empty directories under a root folder.
    """
    for root, dirs, files in os.walk(root_dir, topdown=False):
        if root == root_dir:
            continue

        if not os.listdir(root):
            os.rmdir(root)