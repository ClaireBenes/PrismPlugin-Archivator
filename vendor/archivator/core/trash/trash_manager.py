import os
import shutil
import uuid
from datetime import datetime, UTC

from archivator.core.exceptions import ArchivatorError
from archivator.core.resolver import ProjectResolver

from .trash_metadata import ( get_metadata_group_entries, get_metadata_path, read_metadata, write_metadata, METADATA_SUFFIX, )
from .trash_paths import ( clean_path, cleanup_empty_dirs, compute_trash_path, make_unique_path, )

class TrashManager:
    """
    Orchestrates trash workflows.

    Responsibilities:
    - Move file groups to trash
    - Restore file groups from trash
    - Empty project trash
    """

    def __init__(self, resolver: ProjectResolver):
        """
        Initialize the TrashManager.

        Args:
            resolver (ProjectResolver): Resolver used to determine project from file paths.
        """
        self.resolver = resolver

    def move_to_trash(self, filepath: str) -> str:
        """
        Move a file and all related files with the same base name
        to the project's trash.

        Args:
            filepath (str): Path to the main file.

        Returns:
            str: Destination path of the selected main file in trash.

        Raises:
            FileNotFoundError: If the file does not exist.
            ArchivatorError: If moving fails.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File does not exist: {filepath}")

        project = self.resolver.resolve(filepath)

        folder = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        base_name, _ = os.path.splitext(filename)

        group_id = str(uuid.uuid4())
        deleted_at = datetime.now(UTC).isoformat(timespec="seconds")

        main_dest_path = None

        for related_filename in self.get_related_filenames(folder, filename):
            src = os.path.join(folder, related_filename)

            desired_dest = compute_trash_path(project, src)
            dest = make_unique_path(desired_dest)

            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(src, dest)

            metadata = {
                "group_id": group_id,
                "group_key": base_name,
                "original_path": clean_path(src),
                "trashed_path": clean_path(dest),
                "original_name": os.path.basename(src),
                "trashed_name": os.path.basename(dest),
                "deleted_at": deleted_at,
                "is_main_file": related_filename == filename,
            }
            write_metadata(dest, metadata)

            if related_filename == filename:
                main_dest_path = dest

        if main_dest_path is None:
            raise ArchivatorError(f"Failed to move main file '{filepath}' to trash.")

        return main_dest_path

    def restore(self, trashed_path: str) -> str:
        """
        Restore a trashed file group to original locations.

        Restore requires Archivator metadata.
        """
        if not os.path.exists(trashed_path):
            raise FileNotFoundError(f"File does not exist: {trashed_path}")

        metadata = read_metadata(trashed_path)

        if metadata is None:
            raise ArchivatorError(
                "Cannot restore this file because no Archivator metadata was found."
            )

        return self.restore_from_metadata_group(trashed_path, metadata)

    def empty_trash(self, project_id: str) -> None:
        """
        Delete all files inside a project's trash directory.

        Args:
            project_id (str): ID of the project.
        """
        project = self.resolver.registry.find_by_id(project_id)

        if not os.path.exists(project.trash_dir):
            return

        shutil.rmtree(project.trash_dir)
        os.makedirs(project.trash_dir, exist_ok=True)

    def restore_from_metadata_group(self, trashed_path: str, selected_metadata: dict) -> str:
        """
        Restore all trashed files belonging to the same metadata group.

        Args:
            trashed_path (str): Selected trashed file path.
            selected_metadata (dict): Metadata of selected file.

        Returns:
            str: Restored path of the selected main file.

        Raises:
            ArchivatorError: If conflicts exist or restore fails.
        """
        project = self.resolver.resolve(trashed_path)
        trash_folder = os.path.dirname(trashed_path)
        group_id = selected_metadata["group_id"]

        entries = get_metadata_group_entries(trash_folder, group_id)

        if not entries:
            raise ArchivatorError("No files found for the selected trash group.")

        conflicts = []
        for entry in entries:
            original_path = entry["original_path"]
            if os.path.exists(original_path):
                conflicts.append(original_path)

        if conflicts:
            conflict_text = "\n".join(conflicts)
            raise ArchivatorError(
                "Cannot restore because the following destination files already exist:\n"
                f"{conflict_text}"
            )

        restored_main_path = None

        for entry in entries:
            src = entry["trashed_path"]
            dest = entry["original_path"]

            if not os.path.exists(src):
                raise ArchivatorError(f"Missing trashed file: {src}")

            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(src, dest)

            metadata_path = get_metadata_path(src)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)

            if clean_path(src) == clean_path(trashed_path):
                restored_main_path = dest

        cleanup_empty_dirs(project.trash_dir)

        if restored_main_path is None:
            raise ArchivatorError(f"Failed to restore main file '{trashed_path}'.")

        return restored_main_path

    def get_related_filenames(self, folder: str, filename: str) -> list[str]:
        """
        Return filenames in the same folder that belong to the same basename group.

        Args:
            folder (str): Source folder.
            filename (str): Selected filename.

        Returns:
            list[str]: Matching filenames.
        """
        base_name, _ = os.path.splitext(filename)

        return [
            entry
            for entry in os.listdir(folder)
            if entry.startswith(base_name)
            and not entry.endswith(METADATA_SUFFIX)
            and os.path.isfile(os.path.join(folder, entry))
        ]