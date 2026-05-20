import json
import os


METADATA_SUFFIX = ".archivator.json"


def get_metadata_path(trashed_file_path: str) -> str:
    """
    Return the sidecar metadata path for a trashed file.
    """
    return f"{trashed_file_path}{METADATA_SUFFIX}"


def write_metadata(trashed_file_path: str, metadata: dict) -> None:
    """
    Write sidecar metadata next to a trashed file.
    """
    metadata_path = get_metadata_path(trashed_file_path)

    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=4)


def read_metadata(trashed_file_path: str) -> dict | None:
    """
    Read sidecar metadata for a trashed file.
    """
    metadata_path = get_metadata_path(trashed_file_path)

    if not os.path.exists(metadata_path):
        return None

    try:
        with open(metadata_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def get_metadata_group_entries(trash_folder: str, group_id: str) -> list[dict]:
    """
    Collect all metadata entries in a trash folder belonging to one group.
    """
    entries = []

    for f in os.listdir(trash_folder):
        if not f.endswith(METADATA_SUFFIX):
            continue

        metadata_path = os.path.join(trash_folder, f)

        try:
            with open(metadata_path, "r", encoding="utf-8") as handle:
                metadata = json.load(handle)
        except Exception:
            continue

        if metadata.get("group_id") == group_id:
            entries.append(metadata)

    return entries