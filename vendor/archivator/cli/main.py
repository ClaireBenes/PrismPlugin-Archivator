import argparse
import os

from archivator.core.paths import CONFIG_PATH, ensure_app_dirs
from archivator.core.registry import ProjectRegistry
from archivator.services.archive_service import ArchiveService
from archivator.core.exceptions import ArchivatorError


def main():
    """
    Command line interface for Archivator.

    Examples:
        archivator add-project /projects/A
        archivator trash /projects/A/file.ma
        archivator restore /projects/A/.trash/file.ma
        archivator empty proj_001
        archivator list
    """

    # Initialize core services
    ensure_app_dirs()
    registry = ProjectRegistry(str(CONFIG_PATH))
    registry.load()

    service = ArchiveService(registry)

    # Create parser
    parser = argparse.ArgumentParser(
        description="Archivator - Project-based file archiving tool"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -------------------------
    # add-project
    # -------------------------
    add_parser = subparsers.add_parser("add-project", help="Add a new project")
    add_parser.add_argument("root", help="Project root path")
    add_parser.add_argument(
        "--trash",
        help="Trash directory (default: <root>/.trash)",
        default=None
    )

    # -------------------------
    # trash
    # -------------------------
    trash_parser = subparsers.add_parser("trash", help="Move file to trash")
    trash_parser.add_argument("filepath", help="File to move")

    # -------------------------
    # restore
    # -------------------------
    restore_parser = subparsers.add_parser("restore", help="Restore file from trash")
    restore_parser.add_argument("filepath", help="File to restore")

    # -------------------------
    # empty
    # -------------------------
    empty_parser = subparsers.add_parser("empty", help="Empty project trash")
    empty_parser.add_argument("project_id", help="Project ID")

    # -------------------------
    # list
    # -------------------------
    subparsers.add_parser("list", help="List all projects")

    # Parse arguments
    args = parser.parse_args()

    try:
        # -------------------------
        # COMMAND HANDLING
        # -------------------------

        if args.command == "add-project":
            trash_dir = args.trash or os.path.join(args.root, ".trash")

            project = service.add_project(args.root, trash_dir)

            print(f"Project added: {project.name} ({project.id})")

        elif args.command == "trash":
            dest = service.move_to_trash(args.filepath)
            print(f"Moved to trash: {dest}")

        elif args.command == "restore":
            dest = service.restore(args.filepath)
            print(f"Restored to: {dest}")

        elif args.command == "empty":
            service.empty_project_trash(args.project_id)
            print(f"Trash emptied for project: {args.project_id}")

        elif args.command == "list":
            projects = service.list_projects()

            if not projects:
                print("No projects registered.")
            else:
                for p in projects:
                    print(f"{p.id} | {p.name} | {p.root}")

    except ArchivatorError as e:
        print(f"[ERROR] {e}")

    except Exception as e:
        print(f"[UNEXPECTED ERROR] {e}")

# ----------------------------------------
# Entry point
# ----------------------------------------
if __name__ == "__main__":
    main()

#python cli\main.py add-project "C:\Users\claire.benes\Documents\PythonProject\StoragePrismPlugin\OKO" --trash "C:\Users\claire.benes\Documents\PythonProject\StoragePrismPlugin\OKO\01_Trash"
#python cli\main.py list